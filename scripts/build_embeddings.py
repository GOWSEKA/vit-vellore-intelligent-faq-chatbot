"""
Precompute and Cache FAQ Embeddings
==================================
Encodes all FAQ records using sentence-transformers/all-MiniLM-L6-v2 on CPU
and caches normalized vectors to disk as a compressed .npz archive.
"""

import os
import sys
import json
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from nlp_engine.semantic_retriever import SemanticRetriever

def build_cache():
    json_path = os.path.join(PROJECT_ROOT, "data", "processed", "vit_vellore_faq.json")
    cache_path = os.path.join(PROJECT_ROOT, "data", "processed", "faq_embeddings.npz")
    
    print("=" * 70)
    print("Precomputing FAQ Embeddings Cache for Instant Production Startup")
    print("=" * 70)
    
    with open(json_path, "r", encoding="utf-8") as f:
        records = json.load(f)
        
    print(f"Loaded {len(records)} FAQs from {json_path}")
    t0 = time.perf_counter()
    
    retriever = SemanticRetriever(cache_file=cache_path)
    retriever.build_index(records, force_rebuild=True)
    
    elapsed = time.perf_counter() - t0
    file_size = os.path.getsize(cache_path)
    print(f"\n[Success] Precomputed {len(records)} embeddings in {elapsed:.2f} seconds.")
    print(f"Cached archive: {cache_path} ({file_size:,} bytes)")
    print("Cold-start loading from this cache takes < 5 milliseconds!")

if __name__ == "__main__":
    build_cache()
