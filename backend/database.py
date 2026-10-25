"""
Database Layer with Seamless SQLite Standalone & Optional MySQL Integration
===========================================================================
Operates standalone out-of-the-box using embedded SQLite for query logging and feedback.
If MySQL environment variables are configured and MySQL is running, seamlessly connects to MySQL.
"""

import os
import sqlite3
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any, List

from backend.config import settings

SQLITE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "chatbot_local.db")

class DatabaseManager:
    def __init__(self):
        self.mode = "sqlite_standalone"
        self._init_database()

    def _init_database(self):
        """Initializes tables in either MySQL or standalone SQLite."""
        if settings.USE_MYSQL:
            try:
                import pymysql
                conn = pymysql.connect(
                    host=settings.MYSQL_HOST,
                    port=settings.MYSQL_PORT,
                    user=settings.MYSQL_USER,
                    password=settings.MYSQL_PASSWORD,
                    database=settings.MYSQL_DATABASE,
                    connect_timeout=3
                )
                conn.close()
                self.mode = "mysql"
                print(f"[Database] Successfully connected to MySQL at {settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}")
                return
            except Exception as e:
                print(f"[Database] MySQL not reachable ({e}). Gracefully activating standalone SQLite mode.")
                self.mode = "sqlite_standalone"
        else:
            self.mode = "sqlite_standalone"

        # Initialize SQLite tables
        os.makedirs(os.path.dirname(SQLITE_PATH), exist_ok=True)
        with sqlite3.connect(SQLITE_PATH) as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    query TEXT NOT NULL,
                    decision TEXT,
                    faq_id TEXT,
                    category TEXT,
                    confidence REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    faq_id TEXT,
                    user_query TEXT,
                    rating INTEGER NOT NULL,
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            print(f"[Database] Standalone SQLite database initialized at {SQLITE_PATH}")

    def log_chat(
        self,
        session_id: str,
        query: str,
        response_data: Dict[str, Any]
    ):
        """Logs chat query and decision for auditing and accuracy monitoring."""
        decision = response_data.get("decision")
        faq_id = response_data.get("faq_id")
        category = response_data.get("category")
        confidence = float(response_data.get("confidence_score", 0.0))

        if self.mode == "mysql":
            try:
                import pymysql
                with pymysql.connect(
                    host=settings.MYSQL_HOST,
                    port=settings.MYSQL_PORT,
                    user=settings.MYSQL_USER,
                    password=settings.MYSQL_PASSWORD,
                    database=settings.MYSQL_DATABASE
                ) as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO chat_logs (session_id, query, decision, faq_id, category, confidence)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (session_id, query, decision, faq_id, category, confidence))
                        conn.commit()
                        return
            except Exception as e:
                print(f"[Database Log Error (MySQL)] {e}. Falling back to SQLite.")

        # Fallback / Default SQLite
        try:
            with sqlite3.connect(SQLITE_PATH) as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO chat_logs (session_id, query, decision, faq_id, category, confidence)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (session_id, query, decision, faq_id, category, confidence))
                conn.commit()
        except Exception as e:
            print(f"[Database Log Error (SQLite)] {e}")

    def save_feedback(
        self,
        session_id: str,
        faq_id: Optional[str],
        user_query: Optional[str],
        rating: int,
        comment: Optional[str]
    ):
        """Stores user thumbs-up / thumbs-down and rating feedback."""
        if self.mode == "mysql":
            try:
                import pymysql
                with pymysql.connect(
                    host=settings.MYSQL_HOST,
                    port=settings.MYSQL_PORT,
                    user=settings.MYSQL_USER,
                    password=settings.MYSQL_PASSWORD,
                    database=settings.MYSQL_DATABASE
                ) as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO user_feedback (session_id, faq_id, user_query, rating, comment)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (session_id, faq_id, user_query, rating, comment))
                        conn.commit()
                        return
            except Exception as e:
                print(f"[Feedback Log Error (MySQL)] {e}. Falling back to SQLite.")

        # SQLite
        try:
            with sqlite3.connect(SQLITE_PATH) as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO user_feedback (session_id, faq_id, user_query, rating, comment)
                    VALUES (?, ?, ?, ?, ?)
                """, (session_id, faq_id, user_query, rating, comment))
                conn.commit()
        except Exception as e:
            print(f"[Feedback Log Error (SQLite)] {e}")

    def get_mode(self) -> str:
        return self.mode

db = DatabaseManager()
