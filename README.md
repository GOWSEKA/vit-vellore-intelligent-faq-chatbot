# An Intelligent FAQ Chatbot for VIT Vellore University

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.2+-EE4C2C.svg?logo=pytorch&logoColor=white)](https://pytorch.org)
[![Sentence Transformers](https://img.shields.io/badge/Sentence--Transformers-all--MiniLM--L6--v2-blue.svg)](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
[![RapidFuzz](https://img.shields.io/badge/RapidFuzz-3.6+-orange.svg)](https://github.com/maxbachmann/RapidFuzz)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-25%2F25%20Passing-brightgreen.svg)](reports/test_run_summary.json)

An end-to-end, domain-aware Natural Language Processing (NLP) FAQ retrieval system and university portal tailored exclusively for the **Vellore Institute of Technology (VIT), Vellore campus**.

The interactive web client is officially branded as **Chatbot – Ask Me**, backed by a multi-signal hybrid retrieval engine combining dense semantic representations (`all-MiniLM-L6-v2`), dual word/character TF-IDF indices, RapidFuzz typo tolerance, and an Intent Guard that eliminates hallucinations by refusing out-of-domain prompts and offering official contact channels.

---

## Table of Contents

1. [Key Features & Objectives](#key-features--objectives)
2. [Architecture Overview](#architecture-overview)
3. [Project Directory Layout](#project-directory-layout)
4. [Prerequisites & System Requirements](#prerequisites--system-requirements)
5. [Local Setup Guide (Windows PowerShell & VS Code)](#local-setup-guide-windows-powershell--vs-code)
6. [Data Pipeline & Knowledge Base](#data-pipeline--knowledge-base)
7. [Running the Application Locally](#running-the-application-locally)
8. [Automated Test Suite & NLP Evaluation](#automated-test-suite--nlp-evaluation)
9. [Public Deployment Guide](#public-deployment-guide)
   - [Part A: Backend Deployment on Render](#part-a-backend-deployment-on-render)
   - [Part B: Frontend Deployment on GitHub Pages](#part-b-frontend-deployment-on-github-pages)
10. [Optional MySQL Database Setup](#optional-mysql-database-setup)
11. [Troubleshooting & FAQ](#troubleshooting--faq)

---

## Key Features & Objectives

1. **Campus-Specific Scope:** Grounded strictly in the **VIT Vellore campus** (Katpadi), covering Admissions (VITEEE), B.Tech Fee Categories 1–5, Hostels (Men's & Ladies AC/Non-AC blocks), Dining (Veg, Non-Veg, Special), Academics (FFCS, 9-pointer rule), Examinations (CAT 1, CAT 2, FAT), and Placements (Dream, Super Dream, Marquee).
2. **Paraphrase Resilience:** Translates varied student queries into accurate answers via dense vector embeddings (`all-MiniLM-L6-v2`).
3. **Typo & Spelling Tolerance:** Sub-word character n-grams and RapidFuzz token sorting handle phonetic misspellings (e.g. *"hosstel veg chargess"* &rarr; Hostel & Mess Fee Schedule).
4. **Domain-Aware Token Preservation:** Preprocessor preserves course codes (e.g. `CSE2001`, `MAT1011`), negations (`not`, `without`, `never`), academic years (`2025-2026`), and currency formats (`₹1,98,000`, `10 LPA`).
5. **Calibrated Hybrid Ranking:** Linearly fuses Semantic Cosine Similarity (50%), Word TF-IDF (20%), Sub-word Character N-Grams (15%), and Fuzzy Token Sorting (15%) with domain entity boosting.
6. **Intent Guard & Anti-Hallucination:** Calibrated confidence thresholds distinguish high-confidence answers from ambiguous queries (prompting interactive clarification options) and out-of-domain queries (providing official university helplines instead of fabricated text).
7. **Traceable Source Attribution:** Every response includes the official university document, academic year, and live verification URL.
8. **Zero Mandatory Database Dependencies:** Operates out-of-the-box with bundled CSV/JSON/JSONL datasets and embedded SQLite for session and feedback logging, with an optional enterprise MySQL migration pipeline.

---

## Architecture Overview

```
                                  +------------------------------------------+
                                  |            CLIENT BROWSER                |
                                  |  (GitHub Pages / Local Web Server)       |
                                  |   - Discover VIT Vellore Landing Page    |
                                  |   - "Chatbot – Ask Me" Interface         |
                                  +--------------------+---------------------+
                                                       |
                                               HTTPS POST /api/chat
                                                       |
                                                       v
                                  +--------------------+---------------------+
                                  |         FASTAPI BACKEND (Render)         |
                                  |  - CORS & Dynamic Endpoint Routing       |
                                  |  - Session Manager (Bounded History)     |
                                  +--------------------+---------------------+
                                                       |
                                                       v
                                  +--------------------+---------------------+
                                  |             NLP ENGINE                   |
                                  | 1. Text Preprocessor (Preserves Codes)   |
                                  | 2. Hybrid Retrieval Pipeline:            |
                                  |    - Dense Semantic (all-MiniLM-L6-v2)   |
                                  |    - Word & Char N-gram TF-IDF           |
                                  |    - RapidFuzz Lexical Variation Matcher |
                                  | 3. Intent Guard & Decision Engine:       |
                                  |    - Direct Answer (> 0.62 Confidence)   |
                                  |    - Clarification (Margin <= 0.035)     |
                                  |    - Safe Refusal (< 0.36 or OOD)        |
                                  +--------------------+---------------------+
                                                       |
                                       +---------------+---------------+
                                       |                               |
                                       v                               v
                        +--------------+-------------+  +--------------+-------------+
                        |   VERIFIED KNOWLEDGE BASE  |  |       DATABASE LAYER       |
                        | - 195 Structured FAQs      |  | - Standalone SQLite (Logs) |
                        | - Compressed NPZ Cache     |  | - Optional MySQL Schema    |
                        | - Source-Attributed URLs   |  |   & Migration Script       |
                        +----------------------------+  +----------------------------+
```

---

## Project Directory Layout

```text
d:\FALL SEM VII 26-27\NLP PROJECT\VIT ChatBot\
├── .github/
│   └── workflows/
│       └── deploy.yml              # Automated GitHub Pages CI/CD workflow
├── backend/
│   ├── app.py                      # FastAPI application entrypoint
│   ├── config.py                   # Environment settings & CORS policy
│   ├── database.py                 # SQLite / MySQL abstraction layer
│   ├── models.py                   # Pydantic request/response schemas
│   └── session_manager.py          # Bounded conversation history
├── data/
│   ├── processed/
│   │   ├── vit_vellore_faq.csv     # Structured CSV dataset (195 verified FAQs)
│   │   ├── vit_vellore_faq.json    # JSON format
│   │   ├── vit_vellore_faq.jsonl   # JSONL format
│   │   ├── faq_embeddings.npz      # Precomputed dense embeddings cache
│   │   └── data_validation_report.json # Dataset health audit
│   ├── raw/
│   │   └── vit_sources_manifest.json # Live source endpoints check
│   └── test/
│       └── test_queries.json       # Held-out benchmark evaluation dataset
├── database/
│   ├── schema.sql                  # MySQL database DDL schema
│   ├── import_to_mysql.py          # Automated MySQL loader script
│   └── MYSQL_WINDOWS_SETUP_GUIDE.md# Windows MySQL setup documentation
├── frontend/
│   ├── assets/
│   │   └── vit_logo.svg            # Official university SVG crest
│   ├── css/
│   │   ├── style.css               # Portal design system (Navy, Red, Gold)
│   │   └── chat.css                # Dedicated chat interface styling
│   ├── js/
│   │   ├── config.js               # Dynamic API environment resolver
│   │   ├── main.js                 # Landing page interactivity
│   │   └── chat.js                 # Chatbot client-side engine
│   ├── index.html                  # "Discover VIT Vellore" Landing Page
│   └── chat.html                   # Dedicated "Chatbot – Ask Me" Interface
├── nlp_engine/
│   ├── __init__.py                 # FAQEngine unified interface
│   ├── preprocessor.py             # Domain-aware text normalizer
│   ├── tfidf_retriever.py          # Word + Character n-gram baseline
│   ├── semantic_retriever.py       # SentenceTransformers all-MiniLM-L6-v2
│   ├── fuzzy_matcher.py            # RapidFuzz typo & spelling matcher
│   ├── hybrid_ranker.py            # Multi-signal weighted fusion
│   ├── reranker.py                 # Cross-encoder candidate reranker
│   └── intent_guard.py             # Ambiguity & Out-of-Domain decision engine
├── reports/
│   ├── charts/                     # Generated visual comparison charts
│   │   ├── accuracy_comparison.png
│   │   ├── latency_comparison.png
│   │   └── query_type_breakdown.png
│   ├── evaluation_report.md        # Results and discussion text
│   ├── nlp_evaluation_metrics.csv  # Measured metrics
│   ├── error_analysis.json         # Per-query error logs
│   └── test_run_summary.json       # Automated test suite execution summary
├── scripts/
│   ├── build_embeddings.py         # Embedding precomputation script
│   ├── collect_vit_data.py         # Official VIT source collector
│   ├── run_evaluation.py           # NLP model benchmarking suite
│   └── validate_and_clean_data.py  # Data quality validator
├── tests/
│   ├── test_api_endpoints.py       # FastAPI REST endpoint tests
│   ├── test_database.py            # Database fallback tests
│   ├── test_intent_guard.py        # Ambiguity & safe refusal tests
│   ├── test_nlp_preprocessing.py   # Token preservation tests
│   ├── test_retrieval_accuracy.py  # Paraphrase & typo accuracy tests
│   └── run_all_tests.py            # Master test runner
├── .env.example                    # Environment variable template
├── .gitignore                      # Clean Git ignore rules
├── Dockerfile                      # Production container declaration
├── Procfile                        # Process startup declaration
├── render.yaml                     # Render 1-click blueprint
└── requirements.txt                # Python dependencies
```

---

## Prerequisites & System Requirements

- **Operating System:** Windows 10 or 11 (64-bit), macOS, or Linux
- **Python:** Python 3.10 to 3.13 (Python 3.13 verified)
- **Git:** Git 2.40+ installed
- **Code Editor:** Visual Studio Code (recommended) or any modern editor
- **Hardware:** Standard CPU (No dedicated GPU required)

---

## Local Setup Guide (Windows PowerShell & VS Code)

### Step 1: Open the Project in VS Code
Open Windows PowerShell and navigate to the project directory:

```powershell
code "d:\FALL SEM VII 26-27\NLP PROJECT\VIT ChatBot"
```

### Step 2: Create and Activate a Python Virtual Environment
Inside VS Code's integrated terminal (Press ``Ctrl + ` ``):

```powershell
# Create a virtual environment named .venv
python -m venv .venv

# Activate the virtual environment
.\.venv\Scripts\Activate.ps1
```

*(Note: If PowerShell displays an `ExecutionPolicy` error, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` once and activate again).*

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

---

## Data Pipeline & Knowledge Base

The repository includes a curated, validated knowledge base of **195 official VIT Vellore FAQs** across 11 core categories:
1. Admissions & VITEEE
2. Fees & Scholarships (Category 1–5 structures)
3. Courses & Schools (SCOPE, SITE, SMEC, SELECT, etc.)
4. Hostels & Dining (AC/Non-AC blocks, Mess caterers, Curfew rules)
5. Academics & FFCS (Fully Flexible Credit System, 9-pointer rule)
6. Examinations & Grading (CAT 1, CAT 2, FAT, 10-point scale)
7. Placements & Internships (Dream, Super Dream, Marquee CTC)
8. Campus Facilities (Library, Riviera fest, Sports, Health Centre)
9. Student Portals & Administration (VTOP, Proctor system, COE)
10. Parent Enquiries (Parent VTOP, Guest house, Student safety)
11. Verified Rankings (NIRF 2024 & NAAC A++)

### Validate Data Health:
```powershell
python scripts/validate_and_clean_data.py
```

### Recompute Embeddings Cache:
```powershell
python scripts/build_embeddings.py
```
*(Cold starts take less than 5ms once precomputed into `data/processed/faq_embeddings.npz`).*

---

## Running the Application Locally

### Option 1: Start the Full-Stack FastAPI Server
Start the Uvicorn ASGI server:

```powershell
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser to:
- **Landing Page:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Interactive Chatbot ("Chatbot – Ask Me"):** [http://127.0.0.1:8000/chat](http://127.0.0.1:8000/chat)
- **Interactive Swagger API Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Endpoint:** [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

---

## Automated Test Suite & NLP Evaluation

### 1. Run the Complete Automated Test Suite (25 Tests)
```powershell
python tests/run_all_tests.py
```

**Expected Output:**
```text
===========================================================================
VIT Vellore Intelligent FAQ Chatbot: Automated Test Suite
===========================================================================
Ran 25 tests in 14.75s

OK
===========================================================================
Test Execution Summary:
  * Total Tests Run:   25
  * Passed:            25
  * Failures:          0
  * Errors:            0
  * Status:            ALL PASSED ✓
  * Saved Report:      reports\test_run_summary.json
===========================================================================
```

### 2. Run NLP Benchmarks & Generate Charts
```powershell
python scripts/run_evaluation.py
```

This generates:
- `reports/nlp_evaluation_metrics.csv`
- `reports/charts/accuracy_comparison.png`
- `reports/charts/latency_comparison.png`
- `reports/charts/query_type_breakdown.png`
- `reports/evaluation_report.md`

#### Measured Benchmark Results:

| Model Architecture | Top-1 Accuracy | Top-3 Accuracy | OOD Guard Accuracy | Mean Latency (CPU) |
| :--- | :---: | :---: | :---: | :---: |
| **TF-IDF Lexical Baseline** | 80.0% | 100.0% | 100.0% | ~5.04 ms |
| **Sentence-Transformers (MiniLM)** | 80.0% | 80.0% | 0.0% *(no threshold)* | ~156.77 ms |
| **RapidFuzz (Typo Matcher)** | 52.0% | 68.0% | 0.0% *(no threshold)* | ~3.89 ms |
| **Hybrid Engine + Intent Guard** | **76.0%** | **84.0%** | **100.0%** | **~116.20 ms** |

---

## Public Deployment Guide

To achieve a 100% publicly accessible website without subscription costs:
- **Backend (FastAPI & NLP Engine):** Deployed on **Render** (Free Web Service)
- **Frontend (Website & Chat UI):** Deployed on **GitHub Pages** via automated GitHub Actions

### Part A: GitHub Repository Setup

1. In PowerShell, initialize your local repository:
   ```powershell
   git init
   git add .
   git commit -m "Initial commit: Complete VIT Vellore Intelligent FAQ Chatbot"
   ```

2. Create a new public repository on [GitHub](https://github.com/new) named `vit-vellore-intelligent-faq-chatbot`.

3. Push your repository:
   ```powershell
   git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/vit-vellore-intelligent-faq-chatbot.git
   git branch -M main
   git push -u origin main
   ```

---

### Part B: Deploying the Backend on Render

1. Log into [Render](https://dashboard.render.com/) with your GitHub account.
2. Click **New +** &rarr; **Web Service**.
3. Select your repository: `vit-vellore-intelligent-faq-chatbot`.
4. Configure the service settings:
   - **Name:** `vit-vellore-intelligent-faq-chatbot`
   - **Region:** Oregon (US West) or Singapore
   - **Runtime:** `Python 3`
   - **Build Command:**
     ```bash
     pip install torch --index-url https://download.pytorch.org/whl/cpu && pip install -r requirements.txt && python scripts/build_embeddings.py
     ```
   - **Start Command:**
     ```bash
     uvicorn backend.app:app --host 0.0.0.0 --port $PORT
     ```
   - **Plan:** Free
5. Click **Create Web Service**.
6. Wait 3–4 minutes for build completion. Render will assign you a live HTTPS URL:
   `https://vit-vellore-intelligent-faq-chatbot.onrender.com`
7. Test the live health endpoint:
   `https://vit-vellore-intelligent-faq-chatbot.onrender.com/api/health`

---

### Part C: Deploying the Frontend on GitHub Pages

1. In `frontend/js/config.js`, `PRODUCTION_API_URL` is configured to match your live Render backend URL:
   ```javascript
   const PRODUCTION_API_URL = "https://vit-vellore-intelligent-faq-chatbot.onrender.com";
   ```

2. Commit and push:
   ```powershell
   git add frontend/js/config.js
   git commit -m "Configure production backend URL"
   git push
   ```

3. Enable GitHub Pages:
   - In your GitHub repository, navigate to **Settings** &rarr; **Pages**.
   - Under **Build and deployment** &rarr; **Source**, select **GitHub Actions**.
   - The workflow `.github/workflows/deploy.yml` will automatically build and publish your frontend!

4. Your website is now live globally at:
   `https://<YOUR_GITHUB_USERNAME>.github.io/vit-vellore-intelligent-faq-chatbot/`

---

## Optional MySQL Database Setup

The application automatically logs sessions and feedback to embedded SQLite (`data/chatbot_local.db`). To enable enterprise MySQL storage:

1. Refer to the complete step-by-step guide in [database/MYSQL_WINDOWS_SETUP_GUIDE.md](database/MYSQL_WINDOWS_SETUP_GUIDE.md).
2. Set credentials in `.env`:
   ```env
   USE_MYSQL=true
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=your_password
   MYSQL_DATABASE=vit_faq_db
   ```
3. Run the automated data migration script:
   ```powershell
   python database/import_to_mysql.py
   ```

---

## Troubleshooting & FAQ

### 1. Render Free-Tier Spin-Down
Render's free tier spins down after 15 minutes of inactivity. When you send your first message after a hiatus, Render may take 30–45 seconds to spin up. The frontend interface shows a friendly status indicator and retry prompt during this period.

### 2. CORS Errors
The backend FastAPI application includes permissive CORS middleware (`allow_origins=["*"]`), ensuring requests from GitHub Pages over HTTPS function smoothly without origin rejection.

### 3. Modifying Backend URL in Browser
If you switch backend hosts, click the **⚙️ API** button in the chat header to update the backend URL directly in the browser via `localStorage`.

---

## License
MIT License. Developed for academic demonstration and research purposes under the NLP Project curriculum.
