"""
Text Preprocessing Pipeline for VIT Vellore Chatbot
===================================================
Domain-aware text normalization that preserves essential semantic tokens:
- Negations ("not", "never", "no", "without", "cannot")
- Course codes (e.g., "CSE2001", "MAT1011", "PHY1701")
- Fee amounts and currency expressions (e.g., "₹1,98,000", "10 LPA", "1.02 Cr")
- Dates and academic years (e.g., "2025-2026", "July 1st")
- Acronym and abbreviation normalization (FFCS, VTOP, VITEEE, FAT, CAT, CDC, etc.)
"""

import re
import unicodedata

# VIT Vellore domain-specific acronym mappings (non-conflicting)
ACRONYM_MAP = {
    r"\bvtop\b": "vtop student portal",
    r"\bviteee\b": "viteee entrance exam",
    r"\bvitmee\b": "vitmee pg entrance exam",
    r"\bvitree\b": "vitree phd entrance exam",
    r"\bffcs\b": "ffcs fully flexible credit system",
    r"\bfat\b": "fat final assessment test",
    r"\bcoe\b": "coe controller of examinations",
    r"\bcdc\b": "cdc career development centre placements",
    r"\bpat\b": "placement and training office",
    r"\bswo\b": "swo student welfare office",
    r"\bgvsdp\b": "gvsdp scholarship",
    r"\bscope\b": "scope school of computer science",
    r"\bsite\b": "site school of information technology",
    r"\bselect\b": "select school of electrical engineering",
    r"\bsmec\b": "smec school of mechanical engineering",
    r"\bsbst\b": "sbst school of biosciences",
    r"\bschyme\b": "schyme school of chemical engineering",
    r"\b9\s*pointer\b": "9 pointer cgpa attendance waiver",
    r"\b9-pointer\b": "9 pointer cgpa attendance waiver",
    r"\bhigh\s*cgpa\s*attendance\b": "9 pointer attendance waiver",
    r"\bdebarred\b": "debarred low attendance n grade",
    r"\barrear\b": "arrear fail f grade re-registration",
    r"\blpa\b": "lpa lakhs per annum salary",
    r"\bpcm\b": "pcm physics chemistry mathematics",
    r"\bpcb\b": "pcb physics chemistry biology",
}

# Negation words that must NOT be removed as stopwords
CRITICAL_NEGATIONS = {
    "no", "not", "never", "none", "neither", "nor", "cannot", "cant",
    "can't", "without", "dont", "don't", "doesnt", "doesn't", "wont",
    "won't", "isnt", "isn't", "arent", "aren't"
}

COURSE_CODE_PATTERN = re.compile(r"\b([A-Z]{3,4}\s*\d{3,4})\b", re.IGNORECASE)
CURRENCY_PATTERN = re.compile(r"(₹\s*[\d,]+|\b\d+\s*(?:lakh|lakhs|lpa|cr|crore)\b)", re.IGNORECASE)
ACADEMIC_YEAR_PATTERN = re.compile(r"\b(20\d\d[-/]\d{2,4})\b")

class TextPreprocessor:
    def __init__(self, expand_acronyms: bool = True):
        self.expand_acronyms = expand_acronyms
        
    def normalize_text(self, text: str) -> str:
        """Standard unicode normalization and whitespace cleanup."""
        if not text:
            return ""
        # Normalize unicode (NFKC)
        text = unicodedata.normalize("NFKC", text)
        # Standardize quotes and dashes
        text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
        text = text.replace("–", "-").replace("—", "-")
        # Standardize spaces
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def preserve_special_tokens(self, text: str) -> str:
        """Standardizes course codes (e.g. 'cse 2001' -> 'CSE2001') and currency."""
        # Unify course code format like 'CSE 2001' -> 'CSE2001'
        def format_code(match):
            raw = match.group(1).upper()
            return re.sub(r"\s+", "", raw)
            
        text = COURSE_CODE_PATTERN.sub(format_code, text)
        return text

    def preprocess_for_retrieval(self, text: str, for_semantic: bool = False) -> str:
        """
        Preprocesses a question or query.
        If for_semantic is True, preserves full sentence structure for Transformers.
        If for_semantic is False, normalizes acronyms and tokens for TF-IDF / lexical matching.
        """
        text = self.normalize_text(text)
        text = self.preserve_special_tokens(text)
        
        if for_semantic:
            # Semantic models (MiniLM) work best with natural sentence structure.
            return text
            
        # Lexical preprocessing
        text_lower = text.lower()
        
        if self.expand_acronyms:
            # Contextual disambiguation for 'cat 1' / 'cat 2'
            if re.search(r"\bcat\s*1\b", text_lower):
                if any(w in text_lower for w in ["rank", "cutoff", "cut-off", "fee", "branch", "seat", "admission", "pay"]):
                    text_lower = re.sub(r"\bcat\s*1\b", "fee category 1 rank cutoff", text_lower)
                else:
                    text_lower = re.sub(r"\bcat\s*1\b", "cat 1 continuous assessment test 1 exam", text_lower)
            if re.search(r"\bcat\s*2\b", text_lower):
                if any(w in text_lower for w in ["rank", "cutoff", "cut-off", "fee", "branch", "seat", "admission", "pay"]):
                    text_lower = re.sub(r"\bcat\s*2\b", "fee category 2 rank cutoff", text_lower)
                else:
                    text_lower = re.sub(r"\bcat\s*2\b", "cat 2 continuous assessment test 2 exam", text_lower)

            for pattern, replacement in ACRONYM_MAP.items():
                text_lower = re.sub(pattern, replacement, text_lower)
                
        # Remove unwanted punctuation while preserving alphanumeric, hyphens, and currency symbols
        cleaned = re.sub(r"[^\w\s₹\-%/]", " ", text_lower)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def extract_entities(self, text: str) -> dict:
        """Extracts key entities like course codes, fee amounts, and years."""
        entities = {
            "course_codes": [],
            "fees_and_packages": [],
            "years": [],
            "has_negation": False
        }
        
        # Course codes
        codes = COURSE_CODE_PATTERN.findall(text)
        entities["course_codes"] = [re.sub(r"\s+", "", c).upper() for c in codes]
        
        # Currency / fees
        fees = CURRENCY_PATTERN.findall(text)
        entities["fees_and_packages"] = [f.strip() for f in fees]
        
        # Years
        years = ACADEMIC_YEAR_PATTERN.findall(text)
        entities["years"] = years
        
        # Negations
        words = set(re.findall(r"\b\w+\b", text.lower()))
        if words.intersection(CRITICAL_NEGATIONS):
            entities["has_negation"] = True
            
        return entities
