"""
Master Automated Test Runner
============================
Executes all unit and integration test suites:
1. NLP Preprocessing Tests
2. Retrieval Accuracy & Source Attribution Tests
3. Intent Guard & Safe Refusal Tests
4. FastAPI Endpoint & Session Isolation Tests
5. Database & Standalone Fallback Tests
Outputs a structured JSON summary to reports/test_run_summary.json.
"""

import sys
import os
import unittest
import time
import json
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

def run_all_suites():
    print("=" * 75)
    print("VIT Vellore Intelligent FAQ Chatbot: Automated Test Suite")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 75)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Discover and add test cases
    test_files = [
        "test_nlp_preprocessing.py",
        "test_retrieval_accuracy.py",
        "test_intent_guard.py",
        "test_api_endpoints.py",
        "test_database.py"
    ]

    for tf in test_files:
        test_path = os.path.join(PROJECT_ROOT, "tests", tf)
        if os.path.exists(test_path):
            module_name = f"tests.{tf[:-3]}"
            suite.addTests(loader.loadTestsFromName(module_name))

    print(f"Loaded {suite.countTestCases()} test cases across {len(test_files)} test suites.\n")
    
    t0 = time.perf_counter()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    elapsed = time.perf_counter() - t0

    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": result.testsRun,
        "passed": result.testsRun - len(result.failures) - len(result.errors),
        "failures": len(result.failures),
        "errors": len(result.errors),
        "success": result.wasSuccessful(),
        "elapsed_seconds": round(elapsed, 3),
        "failure_details": [
            {"test": str(f[0]), "trace": f[1]} for f in result.failures
        ],
        "error_details": [
            {"test": str(e[0]), "trace": e[1]} for e in result.errors
        ]
    }

    report_path = os.path.join(PROJECT_ROOT, "reports", "test_run_summary.json")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 75)
    print("Test Execution Summary:")
    print(f"  * Total Tests Run:   {summary['total_tests']}")
    print(f"  * Passed:            {summary['passed']}")
    print(f"  * Failures:          {summary['failures']}")
    print(f"  * Errors:            {summary['errors']}")
    print(f"  * Total Time:        {summary['elapsed_seconds']:.2f} seconds")
    print(f"  * Status:            {'ALL PASSED ✓' if summary['success'] else 'FAILED ✗'}")
    print(f"  * Saved Report:      {report_path}")
    print("=" * 75)

    return 0 if summary["success"] else 1

if __name__ == "__main__":
    exit_code = run_all_suites()
    sys.exit(exit_code)
