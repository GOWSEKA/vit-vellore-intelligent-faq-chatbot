"""
Download Official ONNX Model & Tokenizer for MiniLM-L6-v2
=========================================================
Downloads the official ONNX model and tokenizer for sentence-transformers/all-MiniLM-L6-v2.
Used during Render build phase to ensure zero PyTorch memory footprint at runtime.
"""

import os
import sys
import urllib.request

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(PROJECT_ROOT, "data", "model_onnx")
ONNX_PATH = os.path.join(MODEL_DIR, "model.onnx")
TOKENIZER_PATH = os.path.join(MODEL_DIR, "tokenizer.json")

TOKENIZER_URL = "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/raw/main/tokenizer.json"
ONNX_URL = "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main/onnx/model.onnx"

def ensure_onnx_model():
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    # 1. Download tokenizer.json
    if not os.path.exists(TOKENIZER_PATH) or os.path.getsize(TOKENIZER_PATH) < 1000:
        print("[ONNX] Downloading tokenizer.json from Hugging Face...")
        try:
            urllib.request.urlretrieve(TOKENIZER_URL, TOKENIZER_PATH)
            print(f"[ONNX] Saved tokenizer.json ({os.path.getsize(TOKENIZER_PATH):,} bytes)")
        except Exception as e:
            print(f"[ONNX Error] Failed to download tokenizer.json: {e}")
            return False
    else:
        print(f"[ONNX] tokenizer.json present ({os.path.getsize(TOKENIZER_PATH):,} bytes)")

    # 2. Download model.onnx
    if not os.path.exists(ONNX_PATH) or os.path.getsize(ONNX_PATH) < 50_000_000:
        print("[ONNX] Downloading official model.onnx (~90 MB) from Hugging Face...")
        try:
            def report_hook(block_num, block_size, total_size):
                if total_size > 0 and block_num % 1000 == 0:
                    pct = (block_num * block_size / total_size) * 100
                    print(f"[ONNX Download] {pct:.1f}% complete", end="\r", flush=True)

            urllib.request.urlretrieve(ONNX_URL, ONNX_PATH, reporthook=report_hook)
            print(f"\n[ONNX] Saved model.onnx ({os.path.getsize(ONNX_PATH):,} bytes)")
        except Exception as e:
            print(f"\n[ONNX Error] Failed to download model.onnx: {e}")
            return False
    else:
        print(f"[ONNX] model.onnx present ({os.path.getsize(ONNX_PATH):,} bytes)")

    return True

if __name__ == "__main__":
    success = ensure_onnx_model()
    sys.exit(0 if success else 1)
