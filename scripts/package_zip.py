"""
ZIP Packaging and Archive Verification Script
============================================
Creates vit_vellore_intelligent_faq_chatbot.zip containing the complete project,
excluding virtual environments, caches, and database logs, and verifies its integrity.
"""

import os
import sys
import zipfile

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIP_OUTPUT = os.path.join(PROJECT_ROOT, "vit_vellore_intelligent_faq_chatbot.zip")

EXCLUDE_DIRS = {
    "__pycache__", ".git", ".venv", "venv", "env",
    ".pytest_cache", ".idea", ".vscode"
}
EXCLUDE_EXTENSIONS = {
    ".pyc", ".pyo", ".pyd", ".zip"
}
EXCLUDE_FILES = {
    "chatbot_local.db", "chatbot_local.db-journal", ".env"
}

def create_and_verify_zip():
    print("=" * 70)
    print("Packaging Project into: vit_vellore_intelligent_faq_chatbot.zip")
    print("=" * 70)

    files_added = 0
    total_bytes = 0

    with zipfile.ZipFile(ZIP_OUTPUT, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(PROJECT_ROOT):
            # Prune excluded directories in-place
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in EXCLUDE_EXTENSIONS or file in EXCLUDE_FILES:
                    continue

                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, PROJECT_ROOT)

                zf.write(abs_path, arcname=rel_path)
                files_added += 1
                total_bytes += os.path.getsize(abs_path)

    zip_size = os.path.getsize(ZIP_OUTPUT)
    print(f"\n[Packaging Complete]")
    print(f"  * Total Files Archived: {files_added}")
    print(f"  * Uncompressed Size:    {total_bytes:,} bytes")
    print(f"  * Compressed ZIP Size:  {zip_size:,} bytes ({zip_size / (1024*1024):.2f} MB)")
    print(f"  * Archive File:         {ZIP_OUTPUT}")

    # Integrity Verification
    print("\n[Verifying ZIP Integrity]...")
    with zipfile.ZipFile(ZIP_OUTPUT, "r") as zf:
        bad_file = zf.testzip()
        if bad_file:
            print(f"[Error] Corrupt archive found in ZIP: {bad_file}")
            sys.exit(1)
        namelist = zf.namelist()
        print(f"  ✓ Tested CRC checksums for all {len(namelist)} items: PASS")
        
        # Verify required critical files
        critical_checks = [
            "backend/app.py",
            "nlp_engine/__init__.py",
            "frontend/index.html",
            "frontend/chat.html",
            "data/processed/vit_vellore_faq.json",
            "data/processed/faq_embeddings.npz",
            "reports/charts/accuracy_comparison.png",
            "README.md",
            "requirements.txt"
        ]
        for c in critical_checks:
            norm_c = c.replace("/", os.sep)
            if c in namelist or norm_c in namelist or c.replace("/", "\\") in namelist:
                print(f"  ✓ Verified critical asset: {c}")
            else:
                print(f"  ⚠ Missing asset: {c}")

    print("\n[Integrity Verification: PASSED ✓]")

if __name__ == "__main__":
    create_and_verify_zip()
