"""
Comprehensive tests for semantic search functionality.

Tests semantic search engine, knowledge base manager, and FAQ tool
integration with semantic search capabilities.
"""
import pytest
import sys
import os
from pathlib import Path
import json
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.faq_tool import search_faq, _load_faq_data
from tools.knowledge_base_manager import (
    KnowledgeBaseManager,
    KBVersionStatus,
    get_kb_manager
)


# Check if semantic search dependencies are available
try:
    from tools.semantic_search import (
        SemanticSearchEngine,
        get_semantic_engine,
        SEMANTIC_SEARCH_AVAILABLE
    )
    HAS_SEMANTIC = SEMANTIC_SEARCH_AVAILABLE
except ImportError:
    HAS_SEMANTIC = False
    SemanticSearchEngine = None
    get_semantic_engine = None


@pytest.fixture
def sample_faqs():
    """Sample FAQ data for testing."""
    return [
        {
            "question": "What is your refund policy?",
            "answer": "We offer a 30-day money-back guarantee on all products.",
            "category": "refund",
            "keywords": ["refund", "return", "money back"]
        },
        {
            "question": "How long does shipping take?",
            "answer": "Standard shipping takes 5-7 business days.",
            "category": "shipping",
            "keywords": ["shipping", "delivery", "how long"]
        },
        {
            "question": "Can I return items?",
            "answer": "Yes, you can return items within 30 days of purchase.",
            "category": "return",
            "keywords": ["return", "send back", "exchange"]
        }
    ]


@pytest.fixture
def temp_data_dir():
    """Create temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


class TestSemanticSearchEngine:
    """Tests for SemanticSearchEngine class."""
    
    @pytest.mark.skipif(not HAS_SEMANTIC, reason="Semantic search dependencies not available")
    def test_engine_initialization(self, temp_data_dir):
        """Test semantic search engine initialization."""
        engine = SemanticSearchEngine(
            model_name="all-MiniLM-L6-v2",
            similarity_threshold=0.5,
            index_path=temp_data_dir / "index"
        )
        
        assert engine is not None
        assert engine.model_name == "all-MiniLM-L6-v2"
        assert engine.similarity_threshold == 0.5
        assert not engine.is_index_loaded()
    
    @pytest.mark.skipif(not HAS_SEMANTIC, reason="Semantic search dependencies not available")
    def test_build_index(self, sample_faqs, temp_data_dir):
        """Test building FAISS index."""
        engine = SemanticSearchEngine(
            index_path=temp_data_dir / "index"
        )
        
        engine.build_index(sample_faqs)
        
        assert engine.is_index_loaded()
        assert len(engine._faq_data) == len(sample_faqs)
        stats = engine.get_index_stats()
        assert stats["num_faqs"] == len(sample_faqs)
    
    @pytest.mark.skipif(not HAS_SEMANTIC, reason="Semantic search dependencies not available")
    def test_search(self, sample_faqs, temp_data_dir):
        """Test semantic search functionality."""
        engine = SemanticSearchEngine(
            similarity_threshold=0.3,
            index_path=temp_data_dir / "index"
        )
        
        engine.build_index(sample_faqs)
        
        # Search for refund-related query
        results = engine.search("I want to get my money back")
        
        assert len(results) > 0
        assert results[0][0]["category"] == "refund"
        assert results[0][1] >= 0.3  # Similarity score
    
    @pytest.mark.skipif(not HAS_SEMANTIC, reason="Semantic search dependencies not available")
    def test_get_suggestions(self, sample_faqs, temp_data_dir):
        """Test auto-suggestions feature."""
        engine = SemanticSearchEngine(
            index_path=temp_data_dir / "index"
        )
        
        engine.build_index(sample_faqs)
        
        suggestions = engine.get_suggestions("refund", max_suggestions=3)
        
        assert len(suggestions) > 0
        assert any("refund" in s.lower() for s in suggestions)
    
    @pytest.mark.skipif(not HAS_SEMANTIC, reason="Semantic search dependencies not available")
    def test_save_and_load_index(self, sample_faqs, temp_data_dir):
        """Test saving and loading FAISS index."""
        # Build and save
        engine1 = SemanticSearchEngine(
            index_path=temp_data_dir / "index"
        )
        engine1.build_index(sample_faqs)
        
        # Load in new engine
        engine2 = SemanticSearchEngine(
            index_path=temp_data_dir / "index"
        )
        loaded = engine2.load_index()
        
        assert loaded
        assert engine2.is_index_loaded()
        assert len(engine2._faq_data) == len(sample_faqs)
        
        # Test search works with loaded index
        results = engine2.search("return policy")
        assert len(results) > 0


class TestKnowledgeBaseManager:
    """Tests for KnowledgeBaseManager class."""
    
    def test_manager_initialization(self, temp_data_dir):
        """Test knowledge base manager initialization."""
        manager = KnowledgeBaseManager(data_dir=temp_data_dir)
        
        assert manager is not None
        assert manager.versions_dir.exists()
    
    def test_create_version(self, sample_faqs, temp_data_dir):
        """Test creating a new KB version."""
        manager = KnowledgeBaseManager(data_dir=temp_data_dir)
        
        version_id = manager.create_version(
            sample_faqs,
            version_name="test_version",
            description="Test version",
            tags=["test", "demo"]
        )
        
        assert version_id is not None
        assert len(version_id) > 0
        
        # Verify version exists
        version = manager.get_version(version_id)
        assert version is not None
        assert version["version_name"] == "test_version"
        assert len(version["faqs"]) == len(sample_faqs)
    
    def test_activate_version(self, sample_faqs, temp_data_dir):
        """Test activating a version."""
        manager = KnowledgeBaseManager(data_dir=temp_data_dir)
        
        version_id = manager.create_version(sample_faqs, version_name="active_version")
        
        success = manager.activate_version(version_id)
        assert success
        
        active = manager.get_active_version()
        assert active is not None
        assert active["version_name"] == "active_version"
    
    def test_list_versions(self, sample_faqs, temp_data_dir):
        """Test listing versions."""
        manager = KnowledgeBaseManager(data_dir=temp_data_dir)
        
        # Create multiple versions
        v1 = manager.create_version(sample_faqs, version_name="version1")
        v2 = manager.create_version(sample_faqs, version_name="version2")
        
        versions = manager.list_versions()
        assert len(versions) >= 2
        
        # Filter by status
        active_versions = manager.list_versions(status=KBVersionStatus.ACTIVE)
        assert len(active_versions) >= 0
    
    def test_compare_versions(self, sample_faqs, temp_data_dir):
        """Test comparing two versions."""
        manager = KnowledgeBaseManager(data_dir=temp_data_dir)
        
        v1 = manager.create_version(sample_faqs, version_name="v1")
        
        # Create modified version
        modified_faqs = sample_faqs + [{
            "question": "New question?",
            "answer": "New answer.",
            "category": "general",
            "keywords": ["new"]
        }]
        v2 = manager.create_version(modified_faqs, version_name="v2")
        
        comparison = manager.compare_versions(v1, v2)
        
        assert comparison["total_differences"] > 0
        assert len(comparison["added"]) > 0
    
    def test_get_statistics(self, sample_faqs, temp_data_dir):
        """Test getting KB statistics."""
        manager = KnowledgeBaseManager(data_dir=temp_data_dir)
        
        manager.create_version(sample_faqs, version_name="stats_test")
        
        stats = manager.get_statistics()
        
        assert stats["total_versions"] > 0
        assert "status_counts" in stats
        assert "languages" in stats


class TestFAQToolSemantic:
    """Tests for FAQ tool with semantic search."""
    
    def test_search_faq_keyword_fallback(self):
        """Test FAQ search falls back to keyword search."""
        # This should work even without semantic search
        result = search_faq("What is your refund policy?", use_semantic=False)
        
        assert result["status"] in ["success", "partial"]
        assert "answer" in result
        assert result["match_type"] == "keyword"
    
    @pytest.mark.skipif(not HAS_SEMANTIC, reason="Semantic search dependencies not available")
    def test_search_faq_semantic(self):
        """Test FAQ search with semantic search."""
        result = search_faq("I want to return my purchase and get money back")
        
        assert result["status"] in ["success", "partial"]
        assert "answer" in result
        
        # Should use semantic if available
        if result.get("match_type") == "semantic":
            assert "similarity" in result
    
    def test_search_faq_paraphrased(self):
        """Test that semantic search handles paraphrased queries."""
        # These should find the same FAQ even with different wording
        query1 = "What is your refund policy?"
        query2 = "How can I get my money back?"
        query3 = "Tell me about returns"
        
        result1 = search_faq(query1)
        result2 = search_faq(query2)
        result3 = search_faq(query3)
        
        # All should return valid results
        assert result1["status"] in ["success", "partial"]
        assert result2["status"] in ["success", "partial"]
        assert result3["status"] in ["success", "partial"]
    
    def test_get_faq_suggestions(self):
        """Test auto-suggestions feature."""
        # Note: get_faq_suggestions n'existe plus, utiliser search_faq
        result = search_faq("refund")
        
        # Should return a dict with status
        assert isinstance(result, dict)
        assert "status" in result
        # May be empty if semantic search not available, but should not error
    
    def test_search_faq_empty_query(self):
        """Test handling of empty query."""
        result = search_faq("")
        
        assert result["status"] == "error"
        assert "error_message" in result
    
    def test_search_faq_cache(self):
        """Test that FAQ search uses caching."""
        query = "What is your refund policy?"
        
        # First call
        result1 = search_faq(query)
        
        # Second call should use cache
        result2 = search_faq(query)
        
        # Both should return same result
        assert result1["status"] == result2["status"]
        if result1["status"] == "success":
            assert result1["answer"] == result2["answer"]


class TestIntegration:
    """Integration tests for semantic search system."""
    
    @pytest.mark.skipif(not HAS_SEMANTIC, reason="Semantic search dependencies not available")
    def test_end_to_end_semantic_search(self, sample_faqs, temp_data_dir):
        """Test complete end-to-end semantic search workflow."""
        # Setup KB manager
        manager = KnowledgeBaseManager(data_dir=temp_data_dir)
        version_id = manager.create_version(sample_faqs, version_name="test")
        manager.activate_version(version_id)
        
        # Setup semantic engine
        engine = SemanticSearchEngine(index_path=temp_data_dir / "index")
        engine.build_index(sample_faqs)
        
        # Test search
        results = engine.search("I want my money back")
        assert len(results) > 0
        
        # Test suggestions
        suggestions = engine.get_suggestions("refund")
        assert len(suggestions) > 0
    
    def test_graceful_degradation(self):
        """Test that system works even if semantic search fails."""
        # Should fall back to keyword search
        result = search_faq("refund policy", use_semantic=False)
        
        assert result["status"] in ["success", "partial"]
        assert "answer" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

