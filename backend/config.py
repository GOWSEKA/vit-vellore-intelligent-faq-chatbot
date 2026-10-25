"""
Backend Configuration & Environment Settings
===========================================
Handles environment variables, CORS policies, data file locations,
and optional database connection strings without external dependencies.
"""

import os
from typing import List

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Settings:
    APP_NAME: str = "VIT Vellore Intelligent FAQ Chatbot API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # CORS Configuration - Allows GitHub Pages, Render, and local development
    CORS_ORIGINS: List[str] = [
        "*",
        "https://*.github.io",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://127.0.0.1:8000"
    ]
    
    # Knowledge Base Paths
    FAQ_JSON_PATH: str = os.path.join(PROJECT_ROOT, "data", "processed", "vit_vellore_faq.json")
    FAQ_CSV_PATH: str = os.path.join(PROJECT_ROOT, "data", "processed", "vit_vellore_faq.csv")
    CACHE_EMBEDDINGS_PATH: str = os.path.join(PROJECT_ROOT, "data", "processed", "faq_embeddings.npz")
    
    # Database Settings (Optional MySQL with automatic SQLite fallback)
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "vit_faq_db")
    USE_MYSQL: bool = os.getenv("USE_MYSQL", "false").lower() in ("true", "1", "yes")

settings = Settings()
