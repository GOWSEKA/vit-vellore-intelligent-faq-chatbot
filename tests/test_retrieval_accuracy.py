"""
Unit & Integration Tests: Retrieval Accuracy & Source Attribution
=================================================================
Verifies that:
- Normal and paraphrased queries retrieve correct FAQs
- Typo-heavy questions find the expected answer
- Source attribution is present, verified, and includes official URLs
"""

import sys
import os
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from nlp_engine import FAQEngine

class TestRetrievalAccuracy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        json_path = os.path.join(PROJECT_ROOT, "data", "processed", "vit_vellore_faq.json")
        cache_path = os.path.join(PROJECT_ROOT, "data", "processed", "faq_embeddings.npz")
        cls.engine = FAQEngine(data_json_path=json_path, cache_embeddings_path=cache_path).load_data()

    def test_normal_question_retrieval(self):
        query = "What is the 9-Pointer Attendance Rule at VIT Vellore?"
        resp = self.engine.query(query)
        self.assertEqual(resp["status"], "success")
        self.assertEqual(resp["faq_id"], "VIT-ACA-003")
        self.assertIn("9.00", resp["answer"])

    def test_paraphrased_retrieval(self):
        query = "How much do I have to pay for B.Tech CSE under Category 1 at Vellore?"
        resp = self.engine.query(query)
        self.assertEqual(resp["status"], "success")
        self.assertEqual(resp["faq_id"], "VIT-FEE-001")
        self.assertIn("1,98,000", resp["answer"])

    def test_typo_handling_with_rapidfuzz(self):
        query = "what is ffcss credit system and how timetable is maded"
        resp = self.engine.query(query)
        self.assertEqual(resp["status"], "success")
        self.assertEqual(resp["faq_id"], "VIT-ACA-001")
        self.assertIn("timetable", resp["answer"].lower())

    def test_source_attribution_integrity(self):
        query = "What are the latest NIRF rankings of VIT University?"
        resp = self.engine.query(query)
        self.assertIn("source", resp)
        self.assertIsNotNone(resp["source"])
        self.assertIn("http", resp["source"]["url"])
        self.assertEqual(resp["source"]["verification_status"], "verified_official")

    def test_branch_eligibility_paraphrase(self):
        query = "Can students with PCB in 12th get into engineering at VIT?"
        resp = self.engine.query(query)
        self.assertEqual(resp["status"], "success")
        self.assertEqual(resp["faq_id"], "VIT-ADM-005")
        self.assertIn("Biotechnology", resp["answer"])

if __name__ == "__main__":
    unittest.main()
