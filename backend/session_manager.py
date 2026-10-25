"""
Session Manager & Bounded Conversation History
=============================================
Provides session isolation, UUID generation, bounded context history,
and contextual pronoun/topic resolution.
"""

import uuid
import time
from typing import Dict, List, Optional, Any
from collections import deque

MAX_HISTORY_TURNS = 10
SESSION_EXPIRY_SECONDS = 3600 * 4  # 4 hours

class SessionManager:
    def __init__(self, max_history: int = MAX_HISTORY_TURNS):
        self.max_history = max_history
        # Mapping from session_id -> deque of turn dictionaries
        self.sessions: Dict[str, deque] = {}
        # Mapping from session_id -> last_activity_time
        self.last_active: Dict[str, float] = {}

    def get_or_create_session(self, session_id: Optional[str] = None) -> str:
        """Retrieves an existing valid session ID or registers/generates one."""
        self.cleanup_expired()
        if not session_id or not str(session_id).strip():
            sid = str(uuid.uuid4())
        else:
            sid = str(session_id).strip()

        if sid not in self.sessions:
            self.sessions[sid] = deque(maxlen=self.max_history)
        self.last_active[sid] = time.time()
        return sid

    def record_turn(
        self,
        session_id: str,
        user_query: str,
        response_data: Dict[str, Any]
    ):
        """Records a completed conversational turn in bounded memory."""
        sid = self.get_or_create_session(session_id)
        turn = {
            "timestamp": time.time(),
            "query": user_query,
            "category": response_data.get("category"),
            "faq_id": response_data.get("faq_id"),
            "decision": response_data.get("decision")
        }
        self.sessions[sid].append(turn)
        self.last_active[sid] = time.time()

    def get_context_category(self, session_id: str) -> Optional[str]:
        """Inspects recent turns to identify conversational topic/category."""
        if session_id in self.sessions and len(self.sessions[session_id]) > 0:
            last_turn = self.sessions[session_id][-1]
            return last_turn.get("category")
        return None

    def get_history(self, session_id: str) -> List[Dict]:
        """Returns the bounded history for the given session."""
        if session_id in self.sessions:
            return list(self.sessions[session_id])
        return []

    def clear_session(self, session_id: str):
        """Clears memory for a specific session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
        if session_id in self.last_active:
            del self.last_active[session_id]

    def cleanup_expired(self):
        """Prunes stale sessions older than SESSION_EXPIRY_SECONDS."""
        now = time.time()
        expired = [
            sid for sid, t in self.last_active.items()
            if now - t > SESSION_EXPIRY_SECONDS
        ]
        for sid in expired:
            self.clear_session(sid)

session_manager = SessionManager()
