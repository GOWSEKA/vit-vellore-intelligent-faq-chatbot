"""
Unit Tests: NLP Preprocessing Pipeline
======================================
Verifies that domain-specific tokens are preserved:
- Negation tokens ("not", "never", "without")
- Course codes (e.g., "CSE2001", "MAT1011")
- Fee currency amounts (e.g., "₹1,98,000", "10 LPA")
- Academic years (e.g., "2025-2026")
- Acronym normalization
"""

import sys
import os
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from nlp_engine.preprocessor import TextPreprocessor

class TestNLPPreprocessing(unittest.TestCase):
    def setUp(self):
        self.preprocessor = TextPreprocessor()

    def test_course_code_preservation(self):
        query = "What is the syllabus of cse 2001 and mat 1011?"
        entities = self.preprocessor.extract_entities(query)
        self.assertIn("CSE2001", entities["course_codes"])
        self.assertIn("MAT1011", entities["course_codes"])

    def test_fee_currency_preservation(self):
        query = "Can I get a job package above 10 LPA or 25 LPA with ₹1,98,000 fees?"
        entities = self.preprocessor.extract_entities(query)
        self.assertTrue(any("10 LPA" in f.upper() for f in entities["fees_and_packages"]))
        self.assertTrue(any("₹1,98,000" in f for f in entities["fees_and_packages"]))

    def test_negation_detection(self):
        q1 = "Can I enter without writing VITEEE?"
        entities1 = self.preprocessor.extract_entities(q1)
        self.assertTrue(entities1["has_negation"])

        q2 = "Is hostel not compulsory for day scholars?"
        entities2 = self.preprocessor.extract_entities(q2)
        self.assertTrue(entities2["has_negation"])

        q3 = "What is the tuition fee for CSE?"
        entities3 = self.preprocessor.extract_entities(q3)
        self.assertFalse(entities3["has_negation"])

    def test_academic_year_preservation(self):
        query = "What is the academic calendar for 2025-2026?"
        entities = self.preprocessor.extract_entities(query)
        self.assertIn("2025-2026", entities["years"])

    def test_acronym_expansion(self):
        query = "How to register in FFCS through VTOP for CAT 1?"
        processed = self.preprocessor.preprocess_for_retrieval(query, for_semantic=False)
        self.assertIn("ffcs fully flexible credit system", processed)
        self.assertIn("vtop student portal", processed)
        self.assertIn("continuous assessment test", processed)

if __name__ == "__main__":
    unittest.main()
