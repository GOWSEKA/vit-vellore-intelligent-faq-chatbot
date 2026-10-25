"""
Unit Tests: Intent Guard, Ambiguity, Out-of-Domain & Safe Fallback
==================================================================
Verifies that:
- Underspecified/ambiguous queries trigger clarification options
- Out-of-domain questions are detected and refused without hallucination
- Official contact channels and sources are provided safely
"""

import sys
import os
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from nlp_engine import FAQEngine

class TestIntentGuard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        json_path = os.path.join(PROJECT_ROOT, "data", "processed", "vit_vellore_faq.json")
        cache_path = os.path.join(PROJECT_ROOT, "data", "processed", "faq_embeddings.npz")
        cls.engine = FAQEngine(data_json_path=json_path, cache_embeddings_path=cache_path).load_data()

    def test_out_of_domain_detection(self):
        query = "What is the weather in Paris tomorrow?"
        resp = self.engine.query(query)
        self.assertIn(resp["decision"], ["out_of_domain", "unavailable_in_knowledge_base"])
        self.assertIn("official_contacts", resp)
        self.assertNotIn("Paris", resp["answer"])

    def test_cricket_out_of_domain(self):
        query = "Who won the cricket match yesterday?"
        resp = self.engine.query(query)
        self.assertIn(resp["decision"], ["out_of_domain", "unavailable_in_knowledge_base"])
        self.assertIn("VIT Vellore", resp["answer"])

    def test_bitcoin_out_of_domain(self):
        query = "Should I buy bitcoin today?"
        resp = self.engine.query(query)
        self.assertEqual(resp["decision"], "out_of_domain")

    def test_ambiguous_short_query_handling(self):
        query = "mess"
        resp = self.engine.query(query)
        # Should either trigger clarification choices or provide direct hostel/mess answer
        if resp["decision"] == "clarification_needed":
            self.assertGreater(len(resp["clarification_choices"]), 1)
        else:
            self.assertIn("mess", resp["answer"].lower())

    def test_empty_query_safe_handling(self):
        query = "   "
        resp = self.engine.query(query)
        self.assertEqual(resp["status"], "empty_query")

if __name__ == "__main__":
    unittest.main()
