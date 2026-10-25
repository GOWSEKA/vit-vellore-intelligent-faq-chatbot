"""
TF-IDF Lexical Retrieval Baseline
================================
Implements dual TF-IDF index (Word N-grams + Character N-grams) with cosine similarity
for high-speed lexical and sub-word pattern matching.
"""

from typing import List, Dict, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nlp_engine.preprocessor import TextPreprocessor

class TfidfRetriever:
    def __init__(self):
        self.preprocessor = TextPreprocessor(expand_acronyms=True)
        # Word-level TF-IDF (unigrams + bigrams)
        self.word_vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=1,
            token_pattern=r"(?u)\b\w+\b"
        )
        # Character n-gram TF-IDF (3 to 5 chars) for typo resilience
        self.char_vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            sublinear_tf=True,
            min_df=1
        )
        self.word_matrix = None
        self.char_matrix = None
        self.faq_records: List[Dict] = []
        self.is_fitted = False

    def fit(self, faq_records: List[Dict]):
        """Fits both word and character vectorizers on FAQ knowledge base."""
        self.faq_records = faq_records
        corpus = []
        for r in faq_records:
            # Combine question and key answer tokens for richer index
            combined = f"{r['question']} {r.get('category', '')} {r['answer']}"
            cleaned = self.preprocessor.preprocess_for_retrieval(combined, for_semantic=False)
            corpus.append(cleaned)
            
        self.word_matrix = self.word_vectorizer.fit_transform(corpus)
        self.char_matrix = self.char_vectorizer.fit_transform(corpus)
        self.is_fitted = True
        return self

    def score(self, query: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns (word_scores, char_scores) arrays for all FAQs against the query.
        """
        if not self.is_fitted:
            raise ValueError("TfidfRetriever has not been fitted on any corpus.")
            
        cleaned_query = self.preprocessor.preprocess_for_retrieval(query, for_semantic=False)
        if not cleaned_query.strip():
            zeros = np.zeros(len(self.faq_records))
            return zeros, zeros
            
        q_word_vec = self.word_vectorizer.transform([cleaned_query])
        q_char_vec = self.char_vectorizer.transform([cleaned_query])
        
        word_sims = cosine_similarity(q_word_vec, self.word_matrix).flatten()
        char_sims = cosine_similarity(q_char_vec, self.char_matrix).flatten()
        
        return word_sims, char_sims

    def retrieve(self, query: str, top_k: int = 5, char_weight: float = 0.3) -> List[Dict]:
        """Retrieves top_k FAQ candidates using combined word and character TF-IDF."""
        word_sims, char_sims = self.score(query)
        combined_scores = (1.0 - char_weight) * word_sims + char_weight * char_sims
        
        top_indices = np.argsort(combined_scores)[::-1][:top_k]
        results = []
        for idx in top_indices:
            results.append({
                "faq": self.faq_records[idx],
                "score": float(combined_scores[idx]),
                "word_score": float(word_sims[idx]),
                "char_score": float(char_sims[idx])
            })
        return results
