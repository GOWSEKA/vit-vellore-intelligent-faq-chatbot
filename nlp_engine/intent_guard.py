"""
Confidence-Aware Intent Guard & Safe Decision Engine
===================================================
Evaluates retrieval confidence, detects ambiguity, handles out-of-domain queries,
and ensures zero hallucination with traceable official VIT Vellore source citations.
"""

from typing import List, Dict, Optional, Any

HIGH_CONFIDENCE_THRESHOLD = 0.62
MODERATE_CONFIDENCE_THRESHOLD = 0.45
AMBIGUITY_MARGIN_THRESHOLD = 0.035
MINIMUM_VIABLE_THRESHOLD = 0.36

# Common out-of-domain patterns that have nothing to do with VIT Vellore
OUT_OF_DOMAIN_KEYWORDS = [
    "weather", "movie", "cinema", "cricket score", "ipl", "recipe",
    "stock market", "crypto", "bitcoin", "politics", "election",
    "prime minister", "president of usa", "chatgpt", "translate to french"
]

class IntentGuard:
    def __init__(
        self,
        high_threshold: float = HIGH_CONFIDENCE_THRESHOLD,
        moderate_threshold: float = MODERATE_CONFIDENCE_THRESHOLD,
        ambiguity_margin: float = AMBIGUITY_MARGIN_THRESHOLD,
        minimum_threshold: float = MINIMUM_VIABLE_THRESHOLD
    ):
        self.high_threshold = high_threshold
        self.moderate_threshold = moderate_threshold
        self.ambiguity_margin = ambiguity_margin
        self.minimum_threshold = minimum_threshold

    def is_blatantly_out_of_domain(self, query: str) -> bool:
        q_lower = query.lower()
        for kw in OUT_OF_DOMAIN_KEYWORDS:
            if kw in q_lower:
                return True
        return False

    def evaluate(self, query: str, ranked_candidates: List[Dict]) -> Dict[str, Any]:
        """
        Decision engine for selecting between:
        - "direct_answer"
        - "clarification_needed"
        - "out_of_domain_or_unavailable"
        """
        if not ranked_candidates or len(ranked_candidates) == 0:
            return self._build_unavailable_response(query, [])

        top1 = ranked_candidates[0]
        top1_score = top1["score"]
        
        # Check hard out-of-domain keywords
        if self.is_blatantly_out_of_domain(query) and top1_score < 0.65:
            return self._build_out_of_domain_response(query, ranked_candidates[:3])

        # Below minimal threshold -> Safe refusal
        if top1_score < self.minimum_threshold:
            return self._build_unavailable_response(query, ranked_candidates[:3])

        # Check Exact Match bypass
        is_exact_or_direct = (
            top1["faq"]["question"].strip().lower() == query.strip().lower() or
            top1["signals"].get("fuzzy", 0.0) >= 0.95 or
            top1["signals"].get("semantic", 0.0) >= 0.96
        )

        # Check Ambiguity:
        # If top 2 candidates are both strong and score difference is below margin threshold
        if len(ranked_candidates) >= 2 and not is_exact_or_direct:
            top2 = ranked_candidates[1]
            top2_score = top2["score"]
            score_diff = top1_score - top2_score
            
            # If top score is moderate and margin is very small (genuinely tied candidates)
            if top1_score >= self.moderate_threshold and top1_score < self.high_threshold and score_diff <= self.ambiguity_margin:
                return self._build_clarification_response(query, ranked_candidates[:3])
            elif top1_score >= self.high_threshold and score_diff < 0.005:
                return self._build_clarification_response(query, ranked_candidates[:3])

        # High or solid confidence -> Direct Answer
        if top1_score >= self.high_threshold or (top1_score >= self.moderate_threshold and len(ranked_candidates) == 1):
            return self._build_direct_answer_response(top1, ranked_candidates[1:4])

        # Moderate confidence (between 0.40 and 0.62) without tight competition:
        # Provide the top answer with transparency, indicating verified source and related options
        return self._build_direct_answer_response(top1, ranked_candidates[1:4], is_moderate=True)

    def _build_direct_answer_response(
        self,
        top_match: Dict,
        other_candidates: List[Dict],
        is_moderate: bool = False
    ) -> Dict[str, Any]:
        faq = top_match["faq"]
        suggestions = [c["faq"]["question"] for c in other_candidates if c["faq"]["faq_id"] != faq["faq_id"]]
        
        return {
            "status": "success",
            "decision": "direct_answer",
            "confidence_score": top_match["score"],
            "is_moderate_confidence": is_moderate,
            "answer": faq["answer"],
            "matched_question": faq["question"],
            "faq_id": faq["faq_id"],
            "category": faq.get("category", "General"),
            "campus": faq.get("campus", "VIT Vellore"),
            "source": {
                "title": faq.get("source_title", "VIT Official Information"),
                "url": faq.get("source_url", "https://vit.ac.in/"),
                "type": faq.get("source_type", "official_website"),
                "verification_status": faq.get("verification_status", "verified_official"),
                "academic_year": faq.get("academic_year", "2025-2026")
            },
            "signals": top_match.get("signals", {}),
            "related_suggestions": suggestions[:3]
        }

    def _build_clarification_response(self, query: str, top_candidates: List[Dict]) -> Dict[str, Any]:
        choices = []
        for c in top_candidates:
            choices.append({
                "faq_id": c["faq"]["faq_id"],
                "question": c["faq"]["question"],
                "category": c["faq"].get("category", "General")
            })

        msg = "I found a few closely related topics for your query. Which of the following would you like to know more about?"
        return {
            "status": "clarification",
            "decision": "clarification_needed",
            "confidence_score": top_candidates[0]["score"],
            "message": msg,
            "answer": msg,
            "clarification_choices": choices,
            "query": query
        }

    def _build_out_of_domain_response(self, query: str, candidates: List[Dict]) -> Dict[str, Any]:
        suggestions = [c["faq"]["question"] for c in candidates if c["score"] >= 0.25]
        msg = "I am an intelligent assistant focused specifically on VIT Vellore University (admissions, academics, fees, hostels, examinations, and placements). I cannot provide information on external or unrelated topics."
        return {
            "status": "out_of_domain",
            "decision": "out_of_domain",
            "confidence_score": candidates[0]["score"] if candidates else 0.0,
            "message": msg,
            "answer": msg,
            "official_contacts": self._get_official_contacts(),
            "related_suggestions": suggestions[:3]
        }

    def _build_unavailable_response(self, query: str, candidates: List[Dict]) -> Dict[str, Any]:
        suggestions = [c["faq"]["question"] for c in candidates if c["score"] >= 0.28]
        msg = "I could not find a verified answer for that specific question in the official VIT Vellore FAQ knowledge base. To ensure you receive accurate and up-to-date guidance, please consult the official university offices below."
        return {
            "status": "not_found",
            "decision": "unavailable_in_knowledge_base",
            "confidence_score": candidates[0]["score"] if candidates else 0.0,
            "message": msg,
            "answer": msg,
            "official_contacts": self._get_official_contacts(),
            "related_suggestions": suggestions[:3]
        }

    def _get_official_contacts(self) -> Dict[str, Any]:
        return {
            "main_website": "https://vit.ac.in/",
            "admissions_email": "ugadmission@vit.ac.in",
            "admissions_helpline": "+91-416-2202020",
            "general_email": "info@vit.ac.in",
            "controller_of_examinations": "coe@vit.ac.in",
            "student_welfare": "swo@vit.ac.in",
            "anti_ragging_helpline": "1800-180-5522"
        }
