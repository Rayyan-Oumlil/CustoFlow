"""Test script for evaluation system."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_evaluation_imports():
    """Test that evaluation can be imported."""
    print("Testing evaluation imports...")
    print("-" * 60)
    
    try:
        from notebooks.evaluation import TEST_CASES, evaluate_agent, run_evaluation
        print("[PASS] Evaluation module imported successfully")
        print(f"[PASS] Found {len(TEST_CASES)} test cases")
        return True
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = test_evaluation_imports()
    if result:
        print("\n[SUCCESS] Evaluation system is ready!")
        print("Run full evaluation with: python notebooks/evaluation.py")
    sys.exit(0 if result else 1)

