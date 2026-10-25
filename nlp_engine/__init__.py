"""
NLP Retrieval & QA Pipeline Package for VIT Vellore Chatbot
===========================================================
Integrates Text Preprocessing, TF-IDF Baseline, Semantic Embeddings,
RapidFuzz Matching, Hybrid Ranking, and Intent Guard into a cohesive engine.
"""

import os
import json
from typing import List, Dict, Optional, Any

from nlp_engine.preprocessor import TextPreprocessor
from nlp_engine.tfidf_retriever import TfidfRetriever
from nlp_engine.semantic_retriever import SemanticRetriever
from nlp_engine.fuzzy_matcher import FuzzyMatcher
from nlp_engine.hybrid_ranker import HybridRanker
from nlp_engine.reranker import CandidateReranker
from nlp_engine.intent_guard import IntentGuard

class FAQEngine:
    def __init__(self, data_json_path: Optional[str] = None, cache_embeddings_path: Optional[str] = None):
        self.data_json_path = data_json_path
        self.cache_embeddings_path = cache_embeddings_path
        
        self.preprocessor = TextPreprocessor()
        self.ranker = HybridRanker(cache_file=cache_embeddings_path)
        self.reranker = CandidateReranker(enabled=False)
        self.intent_guard = IntentGuard()
        self.faq_records: List[Dict] = []
        self.is_loaded = False

    def load_data(self, faq_records: Optional[List[Dict]] = None):
        if faq_records is not None:
            self.faq_records = faq_records
        elif self.data_json_path and os.path.exists(self.data_json_path):
            with open(self.data_json_path, "r", encoding="utf-8") as f:
                self.faq_records = json.load(f)
        else:
            raise FileNotFoundError(f"Cannot load FAQ dataset from {self.data_json_path}")

        print(f"[FAQEngine] Initializing hybrid retrieval on {len(self.faq_records)} records...")
        self.ranker.fit(self.faq_records)
        self.is_loaded = True
        print(f"[FAQEngine] Ready.")
        return self

    def query(
        self,
        user_message: str,
        category_filter: Optional[str] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Processes user query through preprocessing, hybrid retrieval,
        intent guard validation, and generates a structured response.
        """
        if not self.is_loaded:
            raise RuntimeError("FAQEngine not loaded. Call load_data() first.")

        query_clean = user_message.strip()
        if not query_clean:
            return {
                "status": "empty_query",
                "decision": "empty_query",
                "answer": "Please ask a question about VIT Vellore admissions, courses, fees, hostels, academics, examinations, or placements."
            }

        # 1. Hybrid Ranking
        ranked_candidates = self.ranker.rank(
            query=query_clean,
            category_filter=category_filter,
            top_k=top_k
        )

        # 2. Evaluate with Intent Guard
        result = self.intent_guard.evaluate(query=query_clean, ranked_candidates=ranked_candidates)
        result["user_query"] = user_message
        return result

    def get_faq_by_id(self, faq_id: str) -> Optional[Dict]:
        for f in self.faq_records:
            if f["faq_id"] == faq_id:
                return f
        return None

    def get_categories(self) -> List[str]:
        cats = sorted(list({r.get("category", "General") for r in self.faq_records if r.get("category")}))
        return cats

__all__ = [
    "FAQEngine",
    "TextPreprocessor",
    "TfidfRetriever",
    "SemanticRetriever",
    "FuzzyMatcher",
    "HybridRanker",
    "CandidateReranker",
    "IntentGuard"
]
