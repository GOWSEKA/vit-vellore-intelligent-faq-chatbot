"""
Typo & Lexical Variation Matcher using RapidFuzz
================================================
Calculates typo-tolerant fuzzy similarities between the user query and stored FAQ questions.
Acts as a complementary signal for spelling errors and variations without destructive word replacement.
"""

from typing import List, Dict
import numpy as np
from rapidfuzz import fuzz
from nlp_engine.preprocessor import TextPreprocessor

class FuzzyMatcher:
    def __init__(self):
        self.preprocessor = TextPreprocessor(expand_acronyms=True)
        self.faq_records: List[Dict] = []
        self.normalized_questions: List[str] = []

    def fit(self, faq_records: List[Dict]):
        """Caches preprocessed questions for fast fuzzy scoring."""
        self.faq_records = faq_records
        self.normalized_questions = [
            self.preprocessor.preprocess_for_retrieval(r["question"], for_semantic=False)
            for r in faq_records
        ]
        return self

    def score(self, query: str) -> np.ndarray:
        """
        Computes normalized fuzzy similarity [0.0, 1.0] for each FAQ question.
        Uses a blend of token_sort_ratio and WRatio for word-order invariance.
        """
        if not self.normalized_questions:
            return np.zeros(len(self.faq_records))
            
        cleaned_query = self.preprocessor.preprocess_for_retrieval(query, for_semantic=False)
        if not cleaned_query.strip():
            return np.zeros(len(self.faq_records))

        scores = np.zeros(len(self.normalized_questions), dtype=np.float32)
        for idx, target_q in enumerate(self.normalized_questions):
            # Token sort ratio handles reordered words
            tsr = fuzz.token_sort_ratio(cleaned_query, target_q)
            # WRatio handles length differences and capitalization
            wr = fuzz.WRatio(cleaned_query, target_q)
            # Scale from 0..100 to 0.0..1.0
            combined = (0.6 * tsr + 0.4 * wr) / 100.0
            scores[idx] = combined
            
        return scores

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """Retrieves top_k FAQ candidates using fuzzy matching."""
        sims = self.score(query)
        top_indices = np.argsort(sims)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            results.append({
                "faq": self.faq_records[idx],
                "score": float(sims[idx])
            })
        return results
