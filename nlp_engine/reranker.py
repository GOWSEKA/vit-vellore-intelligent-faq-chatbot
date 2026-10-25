"""
Optional Cross-Encoder / DistilBERT Candidate Reranker
=====================================================
Evaluates whether a cross-encoder / transformer reranker improves ranking
over the bi-encoder hybrid baseline, with strict latency profiling.
"""

from typing import List, Dict, Optional
import time

class CandidateReranker:
    """
    Reranks the top-N candidate FAQs retrieved by the hybrid engine.
    Supports cross-encoder models with safe fallback if not installed.
    """
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2", enabled: bool = False):
        self.model_name = model_name
        self.enabled = enabled
        self._model = None

    def _load_model(self):
        if self._model is None and self.enabled:
            try:
                from sentence_transformers import CrossEncoder
                self._model = CrossEncoder(self.model_name, max_length=256)
            except Exception as e:
                print(f"[Warning] Cross-encoder could not be loaded: {e}. Fallback to hybrid ranking.")
                self.enabled = False

    def rerank(self, query: str, candidates: List[Dict], top_k: int = 3) -> List[Dict]:
        """
        Takes candidate FAQs from the hybrid retriever and reranks them.
        Returns reranked candidates and measured rerank latency in ms.
        """
        if not self.enabled or not candidates:
            for c in candidates:
                c["rerank_score"] = c["score"]
                c["rerank_latency_ms"] = 0.0
            return candidates[:top_k]

        self._load_model()
        if self._model is None:
            for c in candidates:
                c["rerank_score"] = c["score"]
                c["rerank_latency_ms"] = 0.0
            return candidates[:top_k]

        t0 = time.perf_counter()
        pairs = [[query, f"{c['faq']['question']} {c['faq']['answer']}"] for c in candidates]
        
        try:
            scores = self._model.predict(pairs)
            for idx, c in enumerate(candidates):
                c["rerank_score"] = float(scores[idx])
                
            reranked = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)
            latency_ms = (time.perf_counter() - t0) * 1000.0
            
            for r in reranked:
                r["rerank_latency_ms"] = round(latency_ms, 2)
                
            return reranked[:top_k]
        except Exception as e:
            print(f"[Reranker Error] {e}")
            for c in candidates:
                c["rerank_score"] = c["score"]
                c["rerank_latency_ms"] = 0.0
            return candidates[:top_k]
