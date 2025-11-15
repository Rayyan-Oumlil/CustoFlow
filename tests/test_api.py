"""Test script for FastAPI server."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_api_imports():
    """Test that API server can be imported."""
    print("Testing API server imports...")
    print("-" * 60)
    
    try:
        from api.server import app
        print("[PASS] API server imported successfully")
        
        # Test that app is a FastAPI instance
        from fastapi import FastAPI
        assert isinstance(app, FastAPI), "app should be FastAPI instance"
        print("[PASS] FastAPI app created correctly")
        
        return True
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = test_api_imports()
    if result:
        print("\n[SUCCESS] API server is ready!")
        print("Run it with: python api/server.py")
        print("Or: uvicorn api.server:app --reload")
    sys.exit(0 if result else 1)

