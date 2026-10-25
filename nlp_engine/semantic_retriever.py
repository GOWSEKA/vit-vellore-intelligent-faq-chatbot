"""
Semantic Retrieval Engine using Sentence Transformers
====================================================
Uses sentence-transformers/all-MiniLM-L6-v2 to represent questions as dense embeddings.
Features on-disk precomputed embedding caching for sub-millisecond cold starts on CPU.
"""

import os
import hashlib
from typing import List, Dict, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from nlp_engine.preprocessor import TextPreprocessor

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

class SemanticRetriever:
    def __init__(self, cache_file: Optional[str] = None):
        self.preprocessor = TextPreprocessor(expand_acronyms=False)
        self.model: Optional[SentenceTransformer] = None
        self.cache_file = cache_file
        self.faq_records: List[Dict] = []
        self.embeddings: Optional[np.ndarray] = None
        self.faq_hash: str = ""

    def _get_corpus_hash(self, texts: List[str]) -> str:
        """Computes SHA-256 hash of the question corpus to detect updates."""
        hasher = hashlib.sha256()
        for t in texts:
            hasher.update(t.encode("utf-8"))
        return hasher.hexdigest()

    def _ensure_model_loaded(self):
        """Lazy load SentenceTransformer model on CPU with memory optimizations."""
        if self.model is None:
            import torch
            torch.set_num_threads(1)
            try:
                torch.set_num_interop_threads(1)
            except Exception:
                pass
            # Explicitly load on CPU in eval mode
            self.model = SentenceTransformer(MODEL_NAME, device="cpu")
            self.model.eval()

    def build_index(self, faq_records: List[Dict], force_rebuild: bool = False):
        """Encodes or loads precomputed embeddings for the FAQ records."""
        self.faq_records = faq_records
        
        # Prepare text representation for each FAQ (focus primarily on question, with brief category context)
        texts_to_embed = [
            f"VIT Vellore {r.get('category', '')}: {self.preprocessor.preprocess_for_retrieval(r['question'], for_semantic=True)}"
            for r in faq_records
        ]
        
        current_hash = self._get_corpus_hash(texts_to_embed)
        self.faq_hash = current_hash

        # Attempt to load from cache
        if not force_rebuild and self.cache_file and os.path.exists(self.cache_file):
            try:
                cached_data = np.load(self.cache_file, allow_pickle=True)
                cached_hash = str(cached_data.get("hash", ""))
                if cached_hash == current_hash and "embeddings" in cached_data:
                    self.embeddings = cached_data["embeddings"]
                    # Normalize embeddings for cosine similarity
                    norm = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
                    self.embeddings = self.embeddings / np.maximum(norm, 1e-12)
                    return self
            except Exception as e:
                print(f"[Warning] Failed to load embedding cache: {e}. Recomputing...")

        # Recompute embeddings
        self._ensure_model_loaded()
        raw_embeddings = self.model.encode(
            texts_to_embed,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
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
            
        self._ensure_model_loaded()
        import torch
        with torch.inference_mode():
            q_emb = self.model.encode(
                [f"VIT Vellore: {cleaned_query}"],
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True
            )[0]
        
        # Dot product of normalized vectors equals cosine similarity
        sims = np.dot(self.embeddings, q_emb)
        # Clip to [0.0, 1.0] range
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
