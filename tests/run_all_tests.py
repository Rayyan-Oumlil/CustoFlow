"""
Script to run all tests in the project.
Executes all test files and provides a comprehensive summary.
"""
import sys
import subprocess
from pathlib import Path
import time
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Test files to run
TEST_FILES = [
    "test_validation.py",
    "test_cache.py",
    "test_rate_limiter.py",
    "test_security.py",
    "test_api.py",
    "test_session.py",
    "test_semantic_search.py",
    "test_conversation_summarizer.py",
    "test_feedback_system.py",
    "test_qa_compliance.py",
    "test_ab_testing.py",
    "test_ticket_session_closure.py",
    "test_faq_agent.py",
    "test_order_agent.py",
    "test_sentiment_agent.py",
    "test_escalation_agent.py",
    "test_orchestrator_agent.py",
    "test_integration.py",
    "test_evaluation.py",
    "test_load.py",
    # New comprehensive tests
    "test_error_handler.py",
    "test_multilingual.py",
    "test_analytics.py",
    "test_conversation_tool.py",
    "test_order_modification_comprehensive.py",
    "test_ticket_modification_comprehensive.py",
    "test_google_speech_mock.py",
    "test_tracing.py",
    "test_long_term_memory.py",
]

# Tests that can be run standalone (not requiring pytest)
STANDALONE_TESTS = [
    "test_ticket_session_closure.py",
    "test_feedback_system.py",
    "test_qa_compliance.py",
    "test_ab_testing.py",
    "test_order_notes_and_refunds.py",
]


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def run_standalone_test(test_file: str) -> tuple[str, bool, str]:
    """Run a standalone test script."""
    test_path = Path(__file__).parent / test_file
    if not test_path.exists():
        return test_file, False, f"File not found: {test_file}"
    
    try:
        print(f"\n  Running {test_file}...")
        result = subprocess.run(
            [sys.executable, str(test_path)],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        output = result.stdout + result.stderr
        success = result.returncode == 0
        
        return test_file, success, output
    except subprocess.TimeoutExpired:
        return test_file, False, "Test timed out after 5 minutes"
    except Exception as e:
        return test_file, False, f"Error running test: {str(e)}"


def run_pytest_test(test_file: str) -> tuple[str, bool, str]:
    """Run a test file using pytest."""
    test_path = Path(__file__).parent / test_file
    if not test_path.exists():
        return test_file, False, f"File not found: {test_file}"
    
    try:
        print(f"\n  Running {test_file} with pytest...")
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_path), "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        output = result.stdout + result.stderr
        success = result.returncode == 0
        
        return test_file, success, output
    except subprocess.TimeoutExpired:
        return test_file, False, "Test timed out after 5 minutes"
    except Exception as e:
        return test_file, False, f"Error running test: {str(e)}"


def main():
    """Run all tests and provide summary."""
    print_header("COMPREHENSIVE TEST SUITE")
    print(f"\n  Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Total test files: {len(TEST_FILES)}")
    
    results = []
    start_time = time.time()
    
    # Run standalone tests first
    print_header("STANDALONE TESTS")
    for test_file in STANDALONE_TESTS:
        if test_file in TEST_FILES:
            test_name, success, output = run_standalone_test(test_file)
            results.append((test_name, success, output))
            status = "[PASS]" if success else "[FAIL]"
            print(f"  {status} {test_name}")
    
    # Run pytest tests
    print_header("PYTEST TESTS")
    pytest_tests = [t for t in TEST_FILES if t not in STANDALONE_TESTS]
    
    for test_file in pytest_tests:
        test_name, success, output = run_pytest_test(test_file)
        results.append((test_name, success, output))
        status = "[PASS]" if success else "[FAIL]"
        print(f"  {status} {test_name}")
    
    # Print summary
    elapsed_time = time.time() - start_time
    print_header("TEST SUMMARY")
    
    passed = sum(1 for _, success, _ in results if success)
    failed = len(results) - passed
    total = len(results)
    
    print(f"\n  Total tests: {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print(f"  Success rate: {(passed/total*100):.1f}%")
    print(f"  Time elapsed: {elapsed_time:.2f} seconds")
    
    print("\n  Detailed results:")
    for test_name, success, output in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"    {status} {test_name}")
        if not success and output:
            # Print last few lines of output for failed tests
            lines = output.strip().split('\n')
            if len(lines) > 5:
                print(f"      ... (showing last 5 lines)")
                for line in lines[-5:]:
                    print(f"      {line}")
            else:
                for line in lines:
                    print(f"      {line}")
    
    print(f"\n  Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if passed == total:
        print("\n  [SUCCESS] All tests passed!")
        return 0
    else:
        print(f"\n  [WARNING] {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

