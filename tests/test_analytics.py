"""
Comprehensive tests for analytics utilities.
Tests interaction logging, feedback tracking, and statistics.
"""
import pytest
import time
from utils.analytics import Analytics


def test_analytics_initialization():
    """Test Analytics class initialization."""
    analytics = Analytics()
    assert analytics._interactions == []
    assert analytics._feedback == {}
    assert analytics._query_patterns == {}
    assert analytics._agent_performance == {}


def test_log_interaction():
    """Test logging a user interaction."""
    analytics = Analytics()
    analytics.log_interaction(
        user_id="user_001",
        query="What is your refund policy?",
        response="Our refund policy is...",
        agent_used="faq_agent",
        response_time=1.5,
        session_id="session_001"
    )
    
    stats = analytics.get_stats()
    assert stats["total_interactions"] == 1
    assert "faq_agent" in stats["agent_performance"]


def test_log_interaction_multiple():
    """Test logging multiple interactions."""
    analytics = Analytics()
    
    for i in range(5):
        analytics.log_interaction(
            user_id=f"user_{i}",
            query=f"Query {i}",
            response=f"Response {i}",
            agent_used="order_agent" if i % 2 == 0 else "faq_agent",
            response_time=1.0 + i * 0.1
        )
    
    stats = analytics.get_stats()
    assert stats["total_interactions"] == 5
    assert stats["agent_performance"]["order_agent"]["calls"] == 3
    assert stats["agent_performance"]["faq_agent"]["calls"] == 2


def test_log_feedback():
    """Test logging user feedback."""
    analytics = Analytics()
    analytics.log_feedback(
        session_id="session_001",
        feedback_type="thumbs_up",
        rating=5,
        comment="Great service!"
    )
    
    stats = analytics.get_stats()
    assert stats["total_feedback"] == 1


def test_log_feedback_multiple():
    """Test logging multiple feedback entries."""
    analytics = Analytics()
    
    for i in range(3):
        analytics.log_feedback(
            session_id=f"session_{i}",
            feedback_type="thumbs_up" if i % 2 == 0 else "thumbs_down",
            rating=5 if i % 2 == 0 else 2
        )
    
    stats = analytics.get_stats()
    assert stats["total_feedback"] == 3


def test_get_stats_empty():
    """Test get_stats with no data."""
    analytics = Analytics()
    stats = analytics.get_stats()
    
    assert stats["total_interactions"] == 0
    assert stats["total_feedback"] == 0
    assert stats["top_query_patterns"] == {}
    assert stats["agent_performance"] == {}
    assert stats["recent_interactions"] == []


def test_get_stats_query_patterns():
    """Test query pattern tracking."""
    analytics = Analytics()
    
    analytics.log_interaction("user_1", "What is refund policy?", "Response", "faq_agent")
    analytics.log_interaction("user_2", "What is shipping time?", "Response", "faq_agent")
    analytics.log_interaction("user_3", "What is refund policy?", "Response", "faq_agent")
    
    stats = analytics.get_stats()
    assert "what is refund" in stats["top_query_patterns"]
    assert stats["top_query_patterns"]["what is refund"] == 2


def test_reset():
    """Test resetting analytics data."""
    analytics = Analytics()
    
    # Add some data
    analytics.log_interaction("user_1", "Query", "Response", "faq_agent")
    analytics.log_feedback("session_1", "thumbs_up", rating=5)
    
    # Reset
    analytics.reset()
    
    stats = analytics.get_stats()
    assert stats["total_interactions"] == 0
    assert stats["total_feedback"] == 0


def test_log_interaction_thread_safety():
    """Test that log_interaction is thread-safe."""
    import threading
    
    analytics = Analytics()
    
    def log_interactions():
        for i in range(10):
            analytics.log_interaction(
                user_id=f"user_{i}",
                query=f"Query {i}",
                response=f"Response {i}",
                agent_used="faq_agent"
            )
    
    threads = [threading.Thread(target=log_interactions) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    stats = analytics.get_stats()
    assert stats["total_interactions"] == 50  # 5 threads * 10 interactions


def test_log_interaction_with_none_values():
    """Test log_interaction with None values."""
    analytics = Analytics()
    analytics.log_interaction(
        user_id="user_001",
        query="Query",
        response="Response",
        agent_used=None,
        response_time=None,
        session_id=None
    )
    
    stats = analytics.get_stats()
    assert stats["total_interactions"] == 1


def test_recent_interactions_limit():
    """Test that recent_interactions is limited to 10."""
    analytics = Analytics()
    
    for i in range(15):
        analytics.log_interaction(
            user_id=f"user_{i}",
            query=f"Query {i}",
            response=f"Response {i}",
            agent_used="faq_agent"
        )
    
    stats = analytics.get_stats()
    assert len(stats["recent_interactions"]) == 10
    # Should be the last 10
    assert stats["recent_interactions"][-1]["user_id"] == "user_14"

