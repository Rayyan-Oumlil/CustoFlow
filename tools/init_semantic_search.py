"""
Initialize Semantic Search Index

This script initializes the semantic search index from the FAQ knowledge base.
Run this script after installing dependencies to build the FAISS index.

Usage:
    python -m tools.init_semantic_search
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.semantic_search import get_semantic_engine
from tools.faq_tool import _load_faq_data
from tools.knowledge_base_manager import get_kb_manager, KBVersionStatus


def initialize_semantic_search():
    """Initialize semantic search index from FAQ data."""
    print("Initializing Semantic Search Index...")
    print("-" * 60)
    
    # Check if semantic search is available
    try:
        from tools.semantic_search import SEMANTIC_SEARCH_AVAILABLE
        if not SEMANTIC_SEARCH_AVAILABLE:
            print("ERROR: Semantic search dependencies not installed.")
            print("Please install: pip install sentence-transformers faiss-cpu")
            return False
    except ImportError:
        print("ERROR: Semantic search module not found.")
        return False
    
    # Load FAQ data
    print("\n1. Loading FAQ data...")
    faqs = _load_faq_data()
    
    if not faqs:
        print("ERROR: No FAQ data found.")
        print("Please ensure data/faq_knowledge_base.json exists.")
        return False
    
    print(f"   Loaded {len(faqs)} FAQs")
    
    # Initialize KB manager and create version
    print("\n2. Setting up knowledge base versioning...")
    try:
        kb_manager = get_kb_manager()
        
        # Check if active version exists
        active_version = kb_manager.get_active_version()
        if not active_version:
            # Create initial version
            version_id = kb_manager.create_version(
                faqs,
                version_name="initial_version",
                description="Initial FAQ knowledge base version",
                tags=["initial", "production"]
            )
            kb_manager.activate_version(version_id)
            print(f"   Created and activated version: {version_id}")
        else:
            print(f"   Active version already exists: {active_version.get('version_name')}")
    except Exception as e:
        print(f"   Warning: KB versioning setup failed: {str(e)}")
        print("   Continuing with semantic index build...")
    
    # Build semantic search index
    print("\n3. Building semantic search index...")
    try:
        engine = get_semantic_engine()
        if engine is None:
            print("ERROR: Failed to initialize semantic search engine.")
            return False
        
        # Build index
        engine.build_index(faqs)
        
        if engine.is_index_loaded():
            stats = engine.get_index_stats()
            print(f"   ✓ Index built successfully!")
            print(f"   - FAQs indexed: {stats['num_faqs']}")
            print(f"   - Embedding dimension: {stats['dimension']}")
            print(f"   - Model: {stats['model_name']}")
            
            # Test search
            print("\n4. Testing semantic search...")
            test_query = "What is your refund policy?"
            results = engine.search(test_query, top_k=3)
            
            if results:
                print(f"   ✓ Search test successful!")
                print(f"   - Query: '{test_query}'")
                print(f"   - Top result: '{results[0][0].get('question', '')[:50]}...'")
                print(f"   - Similarity: {results[0][1]:.3f}")
            else:
                print("   ⚠ Search test returned no results")
            
            print("\n" + "-" * 60)
            print("SUCCESS: Semantic search initialized and ready!")
            return True
        else:
            print("ERROR: Index build failed.")
            return False
            
    except Exception as e:
        print(f"ERROR: Failed to build index: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = initialize_semantic_search()
    sys.exit(0 if success else 1)

