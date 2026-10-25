"""
Data Models and Request/Response Schemas for FastAPI
====================================================
Pydantic schemas for chat queries, clarification choices, sources,
user feedback, and service health checks.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="User question or enquiry")
    session_id: Optional[str] = Field(None, description="Client session ID for isolated conversation tracking")
    category: Optional[str] = Field(None, description="Optional category filter")

class SourceCitation(BaseModel):
    title: str
    url: str
    type: str
    verification_status: str
    academic_year: str

class ClarificationChoice(BaseModel):
    faq_id: str
    question: str
    category: str

class ChatResponse(BaseModel):
    status: str
    decision: str
    confidence_score: float
    answer: str
    faq_id: Optional[str] = None
    matched_question: Optional[str] = None
    category: Optional[str] = None
    campus: Optional[str] = "VIT Vellore"
    source: Optional[SourceCitation] = None
    clarification_choices: Optional[List[ClarificationChoice]] = None
    related_suggestions: Optional[List[str]] = None
    official_contacts: Optional[Dict[str, Any]] = None
    session_id: str
    timestamp: str

class FeedbackRequest(BaseModel):
    session_id: str
    faq_id: Optional[str] = None
    user_query: Optional[str] = None
    rating: int = Field(..., ge=1, le=5, description="1 to 5 rating or 1=thumb down, 5=thumb up")
    comment: Optional[str] = Field(None, max_length=500)

class FeedbackResponse(BaseModel):
    status: str
    message: str

class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    faq_count: int
    categories: List[str]
    embeddings_cached: bool
    database_mode: str
