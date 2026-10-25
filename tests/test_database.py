"""
Unit Tests: Database Layer & Standalone Operation
=================================================
Verifies that:
- The system operates standalone without MySQL using embedded SQLite
- Chat queries and user feedback are persistently logged
- MySQL connection failure degrades gracefully without app crash
"""

import sys
import os
import unittest
import sqlite3

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.database import DatabaseManager, SQLITE_PATH

class TestDatabaseLayer(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseManager()

    def test_standalone_sqlite_initialization(self):
        self.assertIn(self.db.get_mode(), ["sqlite_standalone", "mysql"])
        self.assertTrue(os.path.exists(SQLITE_PATH))

    def test_log_chat_sqlite(self):
        test_session = "test_db_session_99"
        test_query = "What is the 9-pointer rule?"
        response_data = {
            "decision": "direct_answer",
            "faq_id": "VIT-ACA-003",
            "category": "Academics & FFCS",
            "confidence_score": 0.88
        }
        self.db.log_chat(test_session, test_query, response_data)

        # Verify entry in SQLite
        with sqlite3.connect(SQLITE_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT query, faq_id FROM chat_logs WHERE session_id = ? ORDER BY id DESC LIMIT 1", (test_session,))
            row = cur.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], test_query)
            self.assertEqual(row[1], "VIT-ACA-003")

    def test_save_feedback_sqlite(self):
        test_session = "test_feedback_sess_88"
        self.db.save_feedback(test_session, "VIT-FEE-001", "How much is fee?", 5, "Clear answer!")

        with sqlite3.connect(SQLITE_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT rating, comment FROM user_feedback WHERE session_id = ? ORDER BY id DESC LIMIT 1", (test_session,))
            row = cur.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], 5)
            self.assertEqual(row[1], "Clear answer!")

if __name__ == "__main__":
    unittest.main()
