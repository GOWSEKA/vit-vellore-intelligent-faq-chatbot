"""
Integration Tests: FastAPI REST Endpoints & Session Isolation
=============================================================
Tests:
- GET /api/health
- POST /api/chat
- POST /api/feedback
- GET /api/categories
- GET /api/faqs
- Session isolation & payload validation
"""

import sys
import os
import unittest
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.app import app

class TestAPIEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_endpoint(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "healthy")
        self.assertGreater(data["faq_count"], 100)
        self.assertTrue(data["embeddings_cached"])

    def test_chat_endpoint_valid_query(self):
        payload = {
            "query": "What is the Category 1 tuition fee for CSE?",
            "category": "Fees & Scholarships"
        }
        resp = self.client.post("/api/chat", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("1,98,000", data["answer"])
        self.assertIsNotNone(data["session_id"])
        self.assertIsNotNone(data["source"])

    def test_feedback_endpoint(self):
        payload = {
            "session_id": "test_session_123",
            "faq_id": "VIT-FEE-001",
            "user_query": "What is CSE fee?",
            "rating": 5,
            "comment": "Accurate and verified!"
        }
        resp = self.client.post("/api/feedback", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")

    def test_categories_endpoint(self):
        resp = self.client.get("/api/categories")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("Admissions", data["categories"])
        self.assertIn("Hostels & Dining", data["categories"])
        self.assertEqual(data["campus"], "VIT Vellore")

    def test_faqs_browse_endpoint(self):
        resp = self.client.get("/api/faqs?limit=10")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreater(data["total"], 100)
        self.assertEqual(len(data["faqs"]), 10)

    def test_session_isolation(self):
        # Session A
        resp_a = self.client.post("/api/chat", json={
            "query": "What are the hostel room types?",
            "session_id": "session_user_A"
        })
        self.assertEqual(resp_a.status_code, 200)
        self.assertEqual(resp_a.json()["session_id"], "session_user_A")

        # Session B
        resp_b = self.client.post("/api/chat", json={
            "query": "What are the passing marks in FAT?",
            "session_id": "session_user_B"
        })
        self.assertEqual(resp_b.status_code, 200)
        self.assertEqual(resp_b.json()["session_id"], "session_user_B")
        self.assertNotEqual(resp_a.json()["session_id"], resp_b.json()["session_id"])

    def test_invalid_payload_validation(self):
        # Empty json payload
        resp = self.client.post("/api/chat", json={})
        self.assertEqual(resp.status_code, 422)

if __name__ == "__main__":
    unittest.main()
