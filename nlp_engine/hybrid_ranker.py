"""
Hybrid Retrieval and Ranking Engine
===================================
Combines Semantic Embeddings, Word TF-IDF, Character N-grams, RapidFuzz,
and Entity Boosts into a calibrated multi-stage retrieval system.
"""

import re
from typing import List, Dict, Optional, Tuple
import numpy as np
from nlp_engine.preprocessor import TextPreprocessor
from nlp_engine.tfidf_retriever import TfidfRetriever
from nlp_engine.semantic_retriever import SemanticRetriever
from nlp_engine.fuzzy_matcher import FuzzyMatcher

class HybridRanker:
    def __init__(
        self,
        weight_semantic: float = 0.50,
        weight_tfidf: float = 0.20,
        weight_char: float = 0.15,
        weight_fuzzy: float = 0.15,
        cache_file: Optional[str] = None
    ):
        self.w_sem = weight_semantic
        self.w_tfidf = weight_tfidf
        self.w_char = weight_char
        self.w_fuzzy = weight_fuzzy
        
        self.preprocessor = TextPreprocessor()
        self.tfidf = TfidfRetriever()
        self.semantic = SemanticRetriever(cache_file=cache_file)
        self.fuzzy = FuzzyMatcher()
        
        self.faq_records: List[Dict] = []
        self.is_ready = False

    def fit(self, faq_records: List[Dict], force_rebuild_embeddings: bool = False):
        """Initializes and fits all sub-retrievers on the FAQ knowledge base."""
        self.faq_records = faq_records
        
        # 1. Fit TF-IDF dual index
        self.tfidf.fit(faq_records)
        
        # 2. Build or load Semantic embeddings
        self.semantic.build_index(faq_records, force_rebuild=force_rebuild_embeddings)
        
        # 3. Fit Fuzzy matcher
        self.fuzzy.fit(faq_records)
        
        self.is_ready = True
        return self

    def rank(
        self,
        query: str,
        category_filter: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Ranks candidate FAQs using calibrated multi-signal hybrid scoring.
        """
        if not self.is_ready:
            raise ValueError("HybridRanker is not initialized. Call fit() first.")
            
        # Extract entities for specialized boosting
        entities = self.preprocessor.extract_entities(query)
        
        # 1. Compute individual score vectors
        sem_scores = self.semantic.score(query)
        word_scores, char_scores = self.tfidf.score(query)
        fuzzy_scores = self.fuzzy.score(query)
        
        # 2. Base weighted linear fusion
        hybrid_scores = (
            self.w_sem * sem_scores +
            self.w_tfidf * word_scores +
            self.w_char * char_scores +
            self.w_fuzzy * fuzzy_scores
        )
        
        # 3. Apply domain entity bonuses and category alignment
        for idx, faq in enumerate(self.faq_records):
            bonus = 0.0
            
            # Exact course code match bonus (e.g., CSE2001)
            for code in entities["course_codes"]:
                if code in faq["question"].upper() or code in faq["answer"].upper():
                    bonus += 0.12
                    
            # Negation alignment: penalize answers that don't match negation polarity
            if entities["has_negation"]:
                if "not" in faq["answer"].lower() or "no" in faq["answer"].lower() or "neither" in faq["answer"].lower():
                    bonus += 0.05
                    
            # Category filter bonus if user requested specific domain
            if category_filter and faq.get("category", "").lower() == category_filter.lower():
                bonus += 0.08

            q_faq = faq["question"].lower()
            a_faq = faq["answer"].lower()
            text_faq = q_faq + " " + a_faq
            text_faq_clean = re.sub(r"['’]", "", text_faq)
            q_faq_clean = re.sub(r"['’]", "", q_faq)

            # Intent categorization of FAQ
            is_faq_fee = ("fee" in q_faq_clean or "cost" in q_faq_clean or "tuition" in q_faq_clean or faq.get("category") == "Fees & Scholarships")
            is_faq_contact = ("contact" in q_faq_clean or "whom" in q_faq_clean or "helpline" in q_faq_clean or "phone" in q_faq_clean or "who can i contact" in q_faq_clean)
            is_faq_rules = ("rule" in q_faq_clean or "curfew" in q_faq_clean or "leave" in q_faq_clean or "attendance" in q_faq_clean)
            is_faq_blocks = ("block" in text_faq_clean and ("accommodation" in q_faq_clean or "available" in q_faq_clean or "room type" in q_faq_clean))

            # Query intent: fee
            if entities.get("is_fee_query"):
                if is_faq_fee:
                    bonus += 0.20
                elif is_faq_contact:
                    bonus -= 0.15

            # Query intent: contact
            if entities.get("is_contact_query"):
                if is_faq_contact:
                    bonus += 0.22
                elif is_faq_fee and not entities.get("is_fee_query"):
                    bonus -= 0.15

            # Query intent: available blocks / accommodation options
            if any(w in query.lower() for w in ["which hostel", "what ladies hostel", "what girls hostel", "blocks", "accommodation option"]):
                if is_faq_blocks:
                    bonus += 0.22

            # Ladies hostel alignment & disambiguation
            if entities.get("is_ladies_hostel"):
                if any(w in text_faq_clean for w in ["ladies hostel", "girls hostel", "female student", "women hostel", "lh"]):
                    bonus += 0.18
                if any(w in q_faq_clean for w in ["mens", "boys hostel", "mens hostel"]):
                    bonus -= 0.25
                elif "men's" in q_faq or "mens" in q_faq_clean:
                    bonus -= 0.15

            # BCA course & fee alignment
            if entities.get("is_bca"):
                if "bca" in q_faq_clean or "bachelor of computer applications" in q_faq_clean:
                    bonus += 0.25

            # B.Sc. programme & fee alignment
            if entities.get("is_bsc"):
                if "b.sc" in q_faq or "bsc" in q_faq_clean or "bachelor of science" in q_faq_clean:
                    bonus += 0.22

            # Integrated M.Tech alignment
            if entities.get("is_integrated_mtech"):
                if "integrated m.tech" in q_faq or "integrated mtech" in q_faq_clean:
                    bonus += 0.22

            # Tuition fee vs hostel/mess fee alignment ("does fee include hostel")
            if entities.get("is_fee_include_hostel"):
                if "include hostel" in q_faq_clean or "academic fee vs residential" in faq.get("source_title", "").lower():
                    bonus += 0.35

            # Official fee structure directory alignment
            if entities.get("is_official_fee_structure_query"):
                if "where can i find the official fee structure" in q_faq_clean:
                    bonus += 0.30
                
            hybrid_scores[idx] += bonus

        # 4. Clip to valid [0.0, 1.0] range
        hybrid_scores = np.clip(hybrid_scores, 0.0, 1.0)
        
        # 5. Extract top candidates
        top_indices = np.argsort(hybrid_scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            results.append({
                "faq": self.faq_records[idx],
                "score": round(float(hybrid_scores[idx]), 4),
                "signals": {
                    "semantic": round(float(sem_scores[idx]), 4),
                    "tfidf_word": round(float(word_scores[idx]), 4),
                    "tfidf_char": round(float(char_scores[idx]), 4),
                    "fuzzy": round(float(fuzzy_scores[idx]), 4)
                }
            })
            
        return results
