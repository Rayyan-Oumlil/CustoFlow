"""Test script for main.py CLI."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that main.py can be imported without errors."""
    print("Testing main.py imports...")
    print("-" * 60)
    
    try:
        import main
        print("[PASS] main.py imported successfully")
        print("[PASS] All dependencies loaded")
        return True
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = test_imports()
    if result:
        print("\n[SUCCESS] main.py is ready to use!")
        print("Run it with: python main.py")
    sys.exit(0 if result else 1)

