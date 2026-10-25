"""
Import Knowledge Base to MySQL
==============================
Connects to MySQL, creates tables if needed, and loads all 195+ FAQs
from data/processed/vit_vellore_faq.json into the faqs table.
"""

import os
import sys
import json

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.config import settings

def import_faqs():
    json_path = os.path.join(PROJECT_ROOT, "data", "processed", "vit_vellore_faq.json")
    schema_path = os.path.join(PROJECT_ROOT, "database", "schema.sql")
    
    print("=" * 70)
    print("Importing VIT Vellore FAQs to MySQL Database")
    print("=" * 70)
    print(f"Target MySQL Host: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}")
    print(f"Database:          {settings.MYSQL_DATABASE}")
    
    try:
        import pymysql
    except ImportError:
        print("\n[Notice] 'pymysql' package is not installed.")
        print("To install, run: pip install pymysql")
        return False
        
    try:
        # Connect to MySQL server (without selecting DB first to create it if not present)
        conn = pymysql.connect(
            host=settings.MYSQL_HOST,
            port=settings.MYSQL_PORT,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            autocommit=True
        )
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS {settings.MYSQL_DATABASE} CHARACTER SET utf8mb4;")
            cur.execute(f"USE {settings.MYSQL_DATABASE};")
            
            # Execute schema statements
            with open(schema_path, "r", encoding="utf-8") as sf:
                schema_sql = sf.read()
                
            statements = [stmt.strip() for stmt in schema_sql.split(";") if stmt.strip()]
            for stmt in statements:
                if not stmt.upper().startswith("CREATE DATABASE") and not stmt.upper().startswith("USE"):
                    cur.execute(stmt)
                    
            # Load FAQs
            with open(json_path, "r", encoding="utf-8") as jf:
                records = json.load(f=jf)
                
            print(f"\nPopulating {len(records)} FAQs into MySQL...")
            insert_sql = """
                INSERT INTO faqs (
                    faq_id, question, answer, category, campus,
                    academic_year, source_url, source_title, source_type,
                    verification_status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    question = VALUES(question),
                    answer = VALUES(answer),
                    category = VALUES(category),
                    source_url = VALUES(source_url),
                    source_title = VALUES(source_title);
            """
            
            rows = [
                (
                    r["faq_id"], r["question"], r["answer"], r["category"],
                    r.get("campus", "VIT Vellore"), r.get("academic_year", "2025-2026"),
                    r.get("source_url", ""), r.get("source_title", ""),
                    r.get("source_type", "official_website"),
                    r.get("verification_status", "verified_official")
                )
                for r in records
            ]
            cur.executemany(insert_sql, rows)
            
            print(f"[Success] Successfully imported {len(rows)} records into MySQL!")
            conn.close()
            return True
            
    except Exception as e:
        print(f"\n[Error connecting to MySQL] {e}")
        print("Ensure MySQL service is running and credentials in .env are correct.")
        print("Note: The chatbot continues to run seamlessly using the bundled dataset and local SQLite.")
        return False

if __name__ == "__main__":
    import_faqs()
