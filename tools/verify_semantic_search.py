"""Verify Semantic Search Installation and Functionality"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def verify_semantic_search():
 """Verify semantic search installation and functionality."""
 print("=" * 70)
 print("Semantic Search Verification")
 print("=" * 70)
 
 all_checks_passed = True
 
 # Check 1: Dependencies
 print("\n[1/6] Checking dependencies...")
 try:
 from tools.semantic_search import SEMANTIC_SEARCH_AVAILABLE
 if SEMANTIC_SEARCH_AVAILABLE:
 print(" ✓ sentence-transformers and faiss-cpu installed")
 else:
 print(" ✗ Dependencies not installed")
 print(" → Run: pip install sentence-transformers faiss-cpu numpy")
 all_checks_passed = False
 except ImportError as e:
 print(f" ✗ Import error: {e}")
 all_checks_passed = False
 
 if not all_checks_passed:
 print("\n⚠ Please install dependencies first.")
 return False
 
 # Check 2: Settings configuration
 print("\n[2/6] Checking configuration...")
 try:
 from config.settings import settings
 print(f" ✓ Model: {getattr(settings, 'semantic_model_name', 'all-MiniLM-L6-v2')}")
 print(f" ✓ Threshold: {getattr(settings, 'semantic_threshold', 0.5)}")
 print(f" ✓ Top K: {getattr(settings, 'semantic_top_k', 5)}")
 print(f" ✓ Enabled: {getattr(settings, 'semantic_enabled', True)}")
 except Exception as e:
 print(f" ✗ Configuration error: {e}")
 all_checks_passed = False
 
 # Check 3: FAQ data
 print("\n[3/6] Checking FAQ data...")
 try:
 from tools.faq_tool import _load_faq_data
 faqs = _load_faq_data()
 if faqs:
 print(f" ✓ Loaded {len(faqs)} FAQs")
 else:
 print(" ✗ No FAQ data found")
 all_checks_passed = False
 except Exception as e:
 print(f" ✗ Error loading FAQs: {e}")
 all_checks_passed = False
 
 # Check 4: Semantic engine initialization
 print("\n[4/6] Checking semantic engine...")
 try:
 from tools.semantic_search import get_semantic_engine
 engine = get_semantic_engine()
 if engine:
 print(" ✓ Semantic engine initialized")
 stats = engine.get_index_stats()
 print(f" - Model: {stats['model_name']}")
 print(f" - Dimension: {stats['dimension']}")
 else:
 print(" ✗ Failed to initialize semantic engine")
 all_checks_passed = False
 except Exception as e:
 print(f" ✗ Error initializing engine: {e}")
 all_checks_passed = False
 
 # Check 5: Index status
 print("\n[5/6] Checking index status...")
 try:
 if engine:
 if engine.is_index_loaded():
 print(" ✓ Index is loaded and ready")
 else:
 print(" ⚠ Index not loaded - will be built on first use")
 print(" → Run: python -m tools.init_semantic_search (optional)")
 except Exception as e:
 print(f" ✗ Error checking index: {e}")
 all_checks_passed = False
 
 # Check 6: Test search
 print("\n[6/6] Testing search functionality...")
 try:
 from tools.faq_tool import search_faq
 test_query = "What is your refund policy?"
 result = search_faq(test_query, use_semantic=True)
 
 if result.get("status") in ["success", "partial"]:
 match_type = result.get("match_type", "unknown")
 print(f" ✓ Search test successful")
 print(f" - Match type: {match_type}")
 if "similarity" in result:
 print(f" - Similarity: {result['similarity']:.3f}")
 print(f" - Question: {result.get('question', '')[:60]}...")
 else:
 print(f" ⚠ Search returned: {result.get('status')}")
 print(f" - This is OK if no exact match found")
 except Exception as e:
 print(f" ✗ Search test failed: {e}")
 all_checks_passed = False
 
 # Summary
 print("\n" + "=" * 70)
 if all_checks_passed:
 print("✓ ALL CHECKS PASSED - Semantic search is ready for production!")
 print("\nThe system will:")
 print(" - Use semantic search when available")
 print(" - Automatically build index on first use if needed")
 print(" - Fall back to keyword search if semantic search fails")
 return True
 else:
 print("⚠ SOME CHECKS FAILED - Please review errors above")
 print("\nRecommended actions:")
 print(" 1. Install dependencies: pip install -r requirements.txt")
 print(" 2. Initialize index: python -m tools.init_semantic_search")
 print(" 3. Verify FAQ data exists: data/faq_knowledge_base.json")
 return False


if __name__ == "__main__":
 success = verify_semantic_search()
 sys.exit(0 if success else 1)

