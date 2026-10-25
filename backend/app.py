"""
FastAPI Backend Application Entrypoint
======================================
Serves REST API endpoints for Chat, Feedback, Categories, and Health.
Mounts frontend static assets for seamless local development and testing.
"""

import os
import sys
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.config import settings
from backend.models import (
    ChatRequest, ChatResponse, FeedbackRequest,
    FeedbackResponse, HealthResponse, SourceCitation, ClarificationChoice
)
from backend.session_manager import session_manager
from backend.database import db
from nlp_engine import FAQEngine

# Initialize FastAPI App
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Official NLP-powered FAQ retrieval system for VIT Vellore campus."
)

# Enable CORS for GitHub Pages and local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize NLP Engine with Cached Embeddings
faq_engine = FAQEngine(
    data_json_path=settings.FAQ_JSON_PATH,
    cache_embeddings_path=settings.CACHE_EMBEDDINGS_PATH
)

try:
    faq_engine.load_data()
except Exception as e:
    print(f"[Warning] FAQEngine initial load deferred: {e}")

# Frontend static directory
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

# --- API Endpoints ---

@app.get("/api/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """Returns service health, model readiness, FAQ count, and database mode."""
    cats = faq_engine.get_categories() if faq_engine.is_loaded else []
    cached = os.path.exists(settings.CACHE_EMBEDDINGS_PATH)
    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        faq_count=len(faq_engine.faq_records) if faq_engine.is_loaded else 0,
        categories=cats,
        embeddings_cached=cached,
        database_mode=db.get_mode()
    )

@app.post("/api/chat", response_model=ChatResponse, tags=["Chat"])
def chat_endpoint(payload: ChatRequest):
    """
    Main conversational endpoint:
    - Analyzes query with domain-aware preprocessor
    - Performs multi-signal hybrid retrieval (semantic + lexical + fuzzy + entity boost)
    - Validates confidence via Intent Guard
    - Manages isolated session history
    - Logs interaction to database
    """
    if not faq_engine.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Knowledge base engine is initializing. Please try again in a few moments."
        )

    # 1. Manage session
    session_id = session_manager.get_or_create_session(payload.session_id)
    
    # 2. Contextual category hint from previous turn if not explicitly specified
    category_filter = payload.category
    if not category_filter:
        category_filter = session_manager.get_context_category(session_id)

    # 3. Query NLP engine
    try:
        raw_result = faq_engine.query(
            user_message=payload.query,
            category_filter=category_filter
        )
    except Exception as e:
        print(f"[Chat Error] {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing your request: {str(e)}"
        )

    # 4. Record session turn and log interaction
    session_manager.record_turn(session_id, payload.query, raw_result)
    db.log_chat(session_id, payload.query, raw_result)

    # 5. Format response schema
    source_obj = None
    if raw_result.get("source"):
        src = raw_result["source"]
        source_obj = SourceCitation(
            title=src.get("title", "VIT Official Portal"),
            url=src.get("url", "https://vit.ac.in/"),
            type=src.get("type", "official_website"),
            verification_status=src.get("verification_status", "verified_official"),
            academic_year=src.get("academic_year", "2025-2026")
        )

    choices_obj = None
    if raw_result.get("clarification_choices"):
        choices_obj = [
            ClarificationChoice(
                faq_id=c["faq_id"],
                question=c["question"],
                category=c["category"]
            )
            for c in raw_result["clarification_choices"]
        ]

    return ChatResponse(
        status=raw_result.get("status", "success"),
        decision=raw_result.get("decision", "direct_answer"),
        confidence_score=float(raw_result.get("confidence_score", 0.0)),
        answer=raw_result.get("answer", raw_result.get("message", "")),
        faq_id=raw_result.get("faq_id"),
        matched_question=raw_result.get("matched_question"),
        category=raw_result.get("category"),
        campus=raw_result.get("campus", "VIT Vellore"),
        source=source_obj,
        clarification_choices=choices_obj,
        related_suggestions=raw_result.get("related_suggestions"),
        official_contacts=raw_result.get("official_contacts"),
        session_id=session_id,
        timestamp=datetime.now().isoformat()
    )

@app.post("/api/feedback", response_model=FeedbackResponse, tags=["Chat"])
def feedback_endpoint(payload: FeedbackRequest):
    """Saves user rating or feedback for continuous answer quality evaluation."""
    db.save_feedback(
        session_id=payload.session_id,
        faq_id=payload.faq_id,
        user_query=payload.user_query,
        rating=payload.rating,
        comment=payload.comment
    )
    return FeedbackResponse(
        status="success",
        message="Thank you! Your feedback has been recorded."
    )

@app.get("/api/categories", tags=["Knowledge Base"])
def get_categories_endpoint():
    """Returns all available official FAQ categories."""
    if not faq_engine.is_loaded:
        return {"categories": []}
    return {
        "campus": "VIT Vellore",
        "categories": faq_engine.get_categories()
    }

@app.get("/api/faqs", tags=["Knowledge Base"])
def get_faqs_endpoint(category: Optional[str] = None, limit: int = 50):
    """Browse or filter verified FAQs from the knowledge base."""
    if not faq_engine.is_loaded:
        return {"total": 0, "faqs": []}
    
    records = faq_engine.faq_records
    if category:
        records = [r for r in records if r.get("category", "").lower() == category.lower()]
    
    return {
        "total": len(records),
        "faqs": records[:limit]
    }

# --- Static Frontend Serving ---
# Resolve frontend directory with fallback to current working directory
if not os.path.exists(FRONTEND_DIR):
    alt_frontend = os.path.join(os.getcwd(), "frontend")
    if os.path.exists(alt_frontend):
        FRONTEND_DIR = alt_frontend

if os.path.exists(FRONTEND_DIR):
    # Mount frontend static folders
    css_dir = os.path.join(FRONTEND_DIR, "css")
    js_dir = os.path.join(FRONTEND_DIR, "js")
    assets_dir = os.path.join(FRONTEND_DIR, "assets")

    if os.path.exists(css_dir):
        app.mount("/css", StaticFiles(directory=css_dir), name="css")
    if os.path.exists(js_dir):
        app.mount("/js", StaticFiles(directory=js_dir), name="js")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/", tags=["UI"])
    @app.get("/index.html", tags=["UI"])
    def serve_landing_page():
        """Serves the Discover VIT Vellore landing page."""
        landing_file = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(landing_file):
            return FileResponse(landing_file, media_type="text/html")
        return {"message": "VIT Vellore FAQ Chatbot API is running. See /docs for Swagger UI."}

    @app.get("/chat", tags=["UI"])
    @app.get("/chat.html", tags=["UI"])
    def serve_chat_page():
        """Serves the Chatbot - Ask Me dedicated interface."""
        chat_file = os.path.join(FRONTEND_DIR, "chat.html")
        if os.path.exists(chat_file):
            return FileResponse(chat_file, media_type="text/html")
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"), media_type="text/html")

    @app.get("/favicon.ico", tags=["UI"])
    def serve_favicon():
        icon_file = os.path.join(FRONTEND_DIR, "assets", "vit_logo.svg")
        if os.path.exists(icon_file):
            return FileResponse(icon_file, media_type="image/svg+xml")
        return JSONResponse(status_code=204, content=None)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host=settings.HOST, port=settings.PORT, reload=True)
