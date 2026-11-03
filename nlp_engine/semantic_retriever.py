"""
Semantic Retrieval Engine using Sentence Transformers / ONNX Runtime
====================================================================
Uses all-MiniLM-L6-v2 to represent questions as 384-dimensional dense embeddings.
Features:
- Primary Engine: Pure ONNX Runtime + tokenizers (Rust) for ultra-low memory (~150 MB).
- Fallback Engine: SentenceTransformers / PyTorch CPU.
- Precomputed embedding caching for sub-millisecond cold starts on CPU.
"""

import os
import hashlib
from typing import List, Dict, Optional, Any
import numpy as np
from nlp_engine.preprocessor import TextPreprocessor

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ONNX_DIR = os.path.join(PROJECT_ROOT, "data", "model_onnx")
ONNX_MODEL_PATH = os.path.join(ONNX_DIR, "model.onnx")
ONNX_TOKENIZER_PATH = os.path.join(ONNX_DIR, "tokenizer.json")

class SemanticRetriever:
    def __init__(self, cache_file: Optional[str] = None):
        self.preprocessor = TextPreprocessor(expand_acronyms=False)
        self.cache_file = cache_file
        self.faq_records: List[Dict] = []
        self.embeddings: Optional[np.ndarray] = None
        self.faq_hash: str = ""
        
        # Model handles (lazily initialized)
        self.backend_mode: Optional[str] = None  # "onnx" or "torch"
        self.onnx_session = None
        self.onnx_tokenizer = None
        self.torch_model = None

    def _get_corpus_hash(self, texts: List[str]) -> str:
        """Computes SHA-256 hash of the question corpus to detect updates."""
        hasher = hashlib.sha256()
        for t in texts:
            hasher.update(t.encode("utf-8"))
        return hasher.hexdigest()

    def _ensure_model_loaded(self):
        """
        Lazily loads inference engine on CPU with memory optimizations.
        Prioritizes ONNX Runtime (low memory ~150 MB). Falls back to PyTorch if ONNX is missing.
        """
        if self.backend_mode is not None:
            return

        # 1. Attempt to load ONNX Runtime first (ultra-low memory)
        if os.path.exists(ONNX_MODEL_PATH) and os.path.exists(ONNX_TOKENIZER_PATH):
            try:
                from tokenizers import Tokenizer
                import onnxruntime as ort

                self.onnx_tokenizer = Tokenizer.from_file(ONNX_TOKENIZER_PATH)
                self.onnx_tokenizer.enable_padding(pad_token="[PAD]")
                self.onnx_tokenizer.enable_truncation(max_length=128)

                sess_options = ort.SessionOptions()
                sess_options.intra_op_num_threads = 1
                sess_options.inter_op_num_threads = 1
                sess_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
                sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

                self.onnx_session = ort.InferenceSession(
                    ONNX_MODEL_PATH,
                    sess_options,
                    providers=["CPUExecutionProvider"]
                )
                self.backend_mode = "onnx"
                return
            except Exception as e:
                print(f"[Warning] Failed to initialize ONNX Runtime: {e}. Falling back to PyTorch...")

        # 2. Fallback to PyTorch SentenceTransformer
        try:
            import torch
            torch.set_num_threads(1)
            try:
                torch.set_num_interop_threads(1)
            except Exception:
                pass
            from sentence_transformers import SentenceTransformer
            self.torch_model = SentenceTransformer(MODEL_NAME, device="cpu")
            self.torch_model.eval()
            self.backend_mode = "torch"
        except Exception as e:
            raise RuntimeError(f"Unable to load any semantic embedding engine: {e}")

    def _encode_texts(self, texts: List[str]) -> np.ndarray:
        """Encodes a list of texts into L2-normalized 384-dimensional dense vectors."""
        self._ensure_model_loaded()

        if self.backend_mode == "onnx":
            encodings = [self.onnx_tokenizer.encode(t) for t in texts]
            input_ids = np.array([e.ids for e in encodings], dtype=np.int64)
            attention_mask = np.array([e.attention_mask for e in encodings], dtype=np.int64)
            token_type_ids = np.array([e.type_ids for e in encodings], dtype=np.int64)

            inputs = {
                "input_ids": input_ids,
                "attention_mask": attention_mask,
                "token_type_ids": token_type_ids
            }
            outputs = self.onnx_session.run(None, inputs)
            token_embeddings = outputs[0]

            # Mean pooling over non-padded tokens
            input_mask_expanded = np.expand_dims(attention_mask, -1).astype(np.float32)
            sum_embeddings = np.sum(token_embeddings * input_mask_expanded, axis=1)
            sum_mask = np.clip(np.sum(input_mask_expanded, axis=1), 1e-9, None)
            mean_pooled = sum_embeddings / sum_mask

            # L2 normalize
            norm = np.linalg.norm(mean_pooled, axis=1, keepdims=True)
            return mean_pooled / np.maximum(norm, 1e-12)

        elif self.backend_mode == "torch":
            import torch
            with torch.inference_mode():
                raw = self.torch_model.encode(
                    texts,
                    show_progress_bar=False,
                    convert_to_numpy=True,
                    normalize_embeddings=True
                )
            return raw

        raise RuntimeError("No active backend mode available for encoding.")

    def build_index(self, faq_records: List[Dict], force_rebuild: bool = False):
        """Encodes or loads precomputed embeddings for the FAQ records."""
        self.faq_records = faq_records
        
        texts_to_embed = [
            f"VIT Vellore {r.get('category', '')}: {self.preprocessor.preprocess_for_retrieval(r['question'], for_semantic=True)}"
            for r in faq_records
        ]
        
        current_hash = self._get_corpus_hash(texts_to_embed)
        self.faq_hash = current_hash

        # Attempt to load from precomputed cache (Zero model memory required!)
        if not force_rebuild and self.cache_file and os.path.exists(self.cache_file):
            try:
                cached_data = np.load(self.cache_file, allow_pickle=True)
                cached_hash = str(cached_data.get("hash", ""))
                if cached_hash == current_hash and "embeddings" in cached_data:
                    self.embeddings = cached_data["embeddings"]
                    norm = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
                    self.embeddings = self.embeddings / np.maximum(norm, 1e-12)
                    return self
            except Exception as e:
                print(f"[Warning] Failed to load embedding cache: {e}. Recomputing...")

        # Recompute embeddings
        raw_embeddings = self._encode_texts(texts_to_embed)
        self.embeddings = raw_embeddings

        # Save to cache
        if self.cache_file:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            np.savez_compressed(self.cache_file, embeddings=self.embeddings, hash=current_hash)
            
        return self

    def score(self, query: str) -> np.ndarray:
        """Computes cosine similarity of query against all stored FAQ embeddings."""
        if self.embeddings is None:
            raise ValueError("Semantic index has not been built.")
            
        cleaned_query = self.preprocessor.preprocess_for_retrieval(query, for_semantic=True)
        if not cleaned_query.strip():
            return np.zeros(len(self.faq_records))
            
        q_emb = self._encode_texts([f"VIT Vellore: {cleaned_query}"])[0]
        
        # Dot product of normalized vectors equals cosine similarity
        sims = np.dot(self.embeddings, q_emb)
        sims = np.clip(sims, 0.0, 1.0)
        return sims

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """Retrieves top_k FAQ candidates using dense semantic similarity."""
        sims = self.score(query)
        top_indices = np.argsort(sims)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            results.append({
                "faq": self.faq_records[idx],
                "score": float(sims[idx])
            })
        return results
