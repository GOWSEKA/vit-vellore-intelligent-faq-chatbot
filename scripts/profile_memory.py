import os
import sys
import psutil
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

def get_mem():
    return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)

print(f"[Step 0] Initial Process Memory: {get_mem():.2f} MB")

from backend.app import app, faq_engine
print(f"[Step 1] After import backend.app & load_data: {get_mem():.2f} MB")

from fastapi.testclient import TestClient
client = TestClient(app)
print(f"[Step 2] After TestClient setup: {get_mem():.2f} MB")

resp = client.get("/api/health")
health_data = resp.json()
print(f"[Step 3] After /api/health: {get_mem():.2f} MB, status: {health_data.get('status')}")

# 1st query
resp = client.post("/api/chat", json={"query": "What is the Category 1 tuition fee for CSE?"})
data = resp.json()
print(f"[Step 4] After 1st /api/chat query: {get_mem():.2f} MB")
print(f"         Status: {data.get('status')}, Confidence: {data.get('confidence_score')}")
print(f"         Answer Preview: {data.get('answer', '')[:80]}...")

# 30 consecutive diverse queries
queries = [
    "How much does ladies hostel cost?",
    "What are the passing criteria in FAT exam?",
    "Tell me about VTOP student portal",
    "Who won the cricket world cup?",
    "What is BCA tuition fee per year?",
    "Can PCB students apply for biotechnology?",
    "How is placement for super dream offers?",
    "What is curfew timing for girls in hostel?",
    "What is scholarship under GVSDP?",
    "Is hostel stay mandatory for day scholars?"
] * 3

for i, q in enumerate(queries):
    resp = client.post("/api/chat", json={"query": q})
    assert resp.status_code == 200
    if (i + 1) % 10 == 0:
        print(f"[Step 5.{i+1}] After {i+1} queries: {get_mem():.2f} MB")

print(f"[Step 6] Final Process Memory: {get_mem():.2f} MB")
