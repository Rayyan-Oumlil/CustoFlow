"""
Tests for Customer Feedback Loop & Continuous Learning System

Tests cover:
- Feedback submission and storage
- Sentiment analysis
- Pattern detection
- KB update suggestions
- Agent refinement suggestions
- Feedback statistics and insights
"""
import pytest
import json
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

from utils.feedback_manager import FeedbackManager


@pytest.fixture
def temp_data_dir():
    """Create temporary data directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def feedback_manager(temp_data_dir):
    """Create feedback manager instance for tests."""
    return FeedbackManager(data_dir=temp_data_dir)


@pytest.fixture
def sample_feedback():
    """Sample feedback data for testing."""
    return {
        "session_id": "test_session_123",
        "user_id": "test_user",
        "feedback_type": "thumbs_down",
        "rating": 2,
        "comment": "The answer was incorrect and unclear",
        "reason": "incorrect",
        "category": "accuracy",
        "agent_used": "faq_agent"
    }


class TestFeedbackSubmission:
    """Test feedback submission functionality."""
    
    def test_submit_basic_feedback(self, feedback_manager, sample_feedback):
        """Test submitting basic feedback."""
        result = feedback_manager.submit_feedback(**sample_feedback)
        
        assert result["status"] == "success"
        assert "feedback_id" in result
        
        # Verify feedback was stored
        feedback_list = feedback_manager.get_feedback_list()
        assert len(feedback_list) == 1
        assert feedback_list[0]["session_id"] == sample_feedback["session_id"]
    
    def test_submit_thumbs_up(self, feedback_manager):
        """Test submitting thumbs up feedback."""
        result = feedback_manager.submit_feedback(
            session_id="session_1",
            user_id="user_1",
            feedback_type="thumbs_up",
            agent_used="order_agent"
        )
        
        assert result["status"] == "success"
        
        feedback_list = feedback_manager.get_feedback_list()
        assert len(feedback_list) == 1
        assert feedback_list[0]["feedback_type"] == "thumbs_up"
    
    def test_submit_rating(self, feedback_manager):
        """Test submitting rating feedback."""
        result = feedback_manager.submit_feedback(
            session_id="session_2",
            user_id="user_2",
            feedback_type="rating",
            rating=5,
            comment="Excellent service!"
        )
        
        assert result["status"] == "success"
        
        feedback_list = feedback_manager.get_feedback_list()
        assert len(feedback_list) == 1
        assert feedback_list[0]["rating"] == 5


class TestSentimentAnalysis:
    """Test sentiment analysis functionality."""
    
    def test_positive_sentiment(self, feedback_manager):
        """Test positive sentiment detection."""
        feedback_manager.submit_feedback(
            session_id="session_1",
            user_id="user_1",
            feedback_type="thumbs_up",
            comment="Great! Very helpful and accurate",
            rating=5
        )
        
        # Wait a bit for async analysis
        import time
        time.sleep(0.5)
        
        feedback_list = feedback_manager.get_feedback_list()
        feedback = feedback_list[0]
        
        assert feedback.get("analyzed", False)
        sentiment = feedback.get("sentiment", {})
        assert sentiment.get("label") == "positive"
        assert sentiment.get("score", 0) >= 0.7
    
    def test_negative_sentiment(self, feedback_manager):
        """Test negative sentiment detection."""
        feedback_manager.submit_feedback(
            session_id="session_2",
            user_id="user_2",
            feedback_type="thumbs_down",
            comment="Wrong answer, very frustrating",
            rating=1,
            reason="incorrect"
        )
        
        import time
        time.sleep(0.5)
        
        feedback_list = feedback_manager.get_feedback_list()
        feedback = feedback_list[0]
        
        assert feedback.get("analyzed", False)
        sentiment = feedback.get("sentiment", {})
        assert sentiment.get("label") == "negative"
        assert sentiment.get("score", 0) <= 0.4
    
    def test_neutral_sentiment(self, feedback_manager):
        """Test neutral sentiment detection."""
        feedback_manager.submit_feedback(
            session_id="session_3",
            user_id="user_3",
            feedback_type="rating",
            comment="It was okay",
            rating=3
        )
        
        import time
        time.sleep(0.5)
        
        feedback_list = feedback_manager.get_feedback_list()
        feedback = feedback_list[0]
        
        sentiment = feedback.get("sentiment", {})
        # Neutral should be between positive and negative
        score = sentiment.get("score", 0.5)
        assert 0.4 <= score <= 0.7


class TestPatternDetection:
    """Test pattern detection functionality."""
    
    def test_detect_common_issues(self, feedback_manager):
        """Test detection of common issues."""
        feedback_manager.submit_feedback(
            session_id="session_1",
            user_id="user_1",
            feedback_type="thumbs_down",
            comment="The answer was unclear and confusing",
            reason="unclear",
            category="clarity"
        )
        
        import time
        time.sleep(0.5)
        
        feedback_list = feedback_manager.get_feedback_list()
        feedback = feedback_list[0]
        
        patterns = feedback.get("patterns", {})
        assert "clarity" in patterns.get("common_issues", [])
    
    def test_detect_topics(self, feedback_manager):
        """Test topic detection."""
        feedback_manager.submit_feedback(
            session_id="session_2",
            user_id="user_2",
            feedback_type="rating",
            comment="I need help with my order and shipping",
            rating=3
        )
        
        import time
        time.sleep(0.5)
        
        feedback_list = feedback_manager.get_feedback_list()
        feedback = feedback_list[0]
        
        patterns = feedback.get("patterns", {})
        topics = patterns.get("topics", [])
        assert "order" in topics or "shipping" in topics


class TestKBUpdateSuggestions:
    """Test knowledge base update suggestions."""
    
    def test_kb_suggestion_creation(self, feedback_manager):
        """Test KB suggestion creation from negative feedback."""
        feedback_manager.submit_feedback(
            session_id="session_1",
            user_id="user_1",
            feedback_type="thumbs_down",
            comment="Missing information about refund policy",
            rating=2,
            reason="missing_info"
        )
        
        import time
        time.sleep(0.5)
        
        suggestions = feedback_manager.get_kb_suggestions()
        assert len(suggestions) > 0
        
        suggestion = suggestions[0]
        assert suggestion.get("status") == "pending"
        assert suggestion.get("suggestion_type") == "add"
        assert suggestion.get("reason") == "missing_info"
    
    def test_kb_suggestion_priority(self, feedback_manager):
        """Test KB suggestion priority assignment."""
        # High priority (rating 1)
        feedback_manager.submit_feedback(
            session_id="session_1",
            user_id="user_1",
            feedback_type="rating",
            comment="Completely wrong",
            rating=1,
            reason="incorrect"
        )
        
        import time
        time.sleep(0.5)
        
        suggestions = feedback_manager.get_kb_suggestions()
        if suggestions:
            assert suggestions[0].get("priority") == "high"


class TestAgentRefinements:
    """Test agent instruction refinement suggestions."""
    
    def test_agent_refinement_creation(self, feedback_manager):
        """Test agent refinement suggestion creation."""
        feedback_manager.submit_feedback(
            session_id="session_1",
            user_id="user_1",
            feedback_type="rating",
            comment="The response was unclear",
            rating=2,
            reason="unclear",
            agent_used="faq_agent"
        )
        
        import time
        time.sleep(0.5)
        
        refinements = feedback_manager.get_agent_refinements(agent="faq_agent")
        assert "refinements" in refinements
        assert len(refinements["refinements"]) > 0
        
        refinement = refinements["refinements"][0]
        assert refinement.get("status") == "pending"
        assert refinement.get("issue") == "unclear"
        assert "suggested_improvement" in refinement
    
    def test_multiple_agent_refinements(self, feedback_manager):
        """Test refinements for multiple agents."""
        # Feedback for FAQ agent
        feedback_manager.submit_feedback(
            session_id="session_1",
            user_id="user_1",
            feedback_type="rating",
            rating=2,
            agent_used="faq_agent"
        )
        
        # Feedback for Order agent
        feedback_manager.submit_feedback(
            session_id="session_2",
            user_id="user_2",
            feedback_type="rating",
            rating=2,
            agent_used="order_agent"
        )
        
        import time
        time.sleep(0.5)
        
        all_refinements = feedback_manager.get_agent_refinements()
        assert "faq_agent" in all_refinements
        assert "order_agent" in all_refinements


class TestFeedbackStatistics:
    """Test feedback statistics and insights."""
    
    def test_feedback_stats_empty(self, feedback_manager):
        """Test stats with no feedback."""
        stats = feedback_manager.get_feedback_stats()
        
        assert stats["total_feedback"] == 0
        assert stats["kb_suggestions"] == 0
        assert stats["agent_refinements"] == 0
    
    def test_feedback_stats_with_data(self, feedback_manager):
        """Test stats with feedback data."""
        # Submit multiple feedback entries
        for i in range(5):
            feedback_manager.submit_feedback(
                session_id=f"session_{i}",
                user_id=f"user_{i}",
                feedback_type="rating",
                rating=4 if i % 2 == 0 else 2,
                comment=f"Feedback {i}",
                agent_used="faq_agent" if i % 2 == 0 else "order_agent"
            )
        
        import time
        time.sleep(1)  # Wait for analysis
        
        stats = feedback_manager.get_feedback_stats()
        
        assert stats["total_feedback"] == 5
        assert "insights" in stats
        assert stats["insights"].get("total_feedback") == 5
    
    def test_insights_generation(self, feedback_manager):
        """Test insights generation from feedback."""
        # Submit enough feedback to trigger insights
        for i in range(10):
            feedback_manager.submit_feedback(
                session_id=f"session_{i}",
                user_id=f"user_{i}",
                feedback_type="rating",
                rating=4 if i < 7 else 2,
                comment=f"Feedback comment {i}",
                agent_used="faq_agent"
            )
        
        import time
        time.sleep(1.5)  # Wait for analysis and insights
        
        stats = feedback_manager.get_feedback_stats()
        insights = stats.get("insights", {})
        
        if insights:
            assert "satisfaction_rate" in insights
            assert "avg_rating" in insights
            assert "common_issues" in insights
            assert "agent_performance" in insights


class TestFeedbackFiltering:
    """Test feedback filtering functionality."""
    
    def test_filter_by_agent(self, feedback_manager):
        """Test filtering feedback by agent."""
        feedback_manager.submit_feedback(
            session_id="session_1",
            user_id="user_1",
            feedback_type="rating",
            agent_used="faq_agent"
        )
        
        feedback_manager.submit_feedback(
            session_id="session_2",
            user_id="user_2",
            feedback_type="rating",
            agent_used="order_agent"
        )
        
        faq_feedback = feedback_manager.get_feedback_list(agent="faq_agent")
        assert len(faq_feedback) == 1
        assert faq_feedback[0]["agent_used"] == "faq_agent"
    
    def test_limit_feedback_list(self, feedback_manager):
        """Test limiting feedback list."""
        # Submit 10 feedback entries
        for i in range(10):
            feedback_manager.submit_feedback(
                session_id=f"session_{i}",
                user_id=f"user_{i}",
                feedback_type="rating",
                rating=4
            )
        
        limited = feedback_manager.get_feedback_list(limit=5)
        assert len(limited) == 5


class TestDataPersistence:
    """Test data persistence functionality."""
    
    def test_persistence_across_instances(self, temp_data_dir):
        """Test that data persists across FeedbackManager instances."""
        # Create first instance and submit feedback
        manager1 = FeedbackManager(data_dir=temp_data_dir)
        manager1.submit_feedback(
            session_id="session_1",
            user_id="user_1",
            feedback_type="rating",
            rating=5
        )
        
        # Create second instance and verify data
        manager2 = FeedbackManager(data_dir=temp_data_dir)
        feedback_list = manager2.get_feedback_list()
        
        assert len(feedback_list) == 1
        assert feedback_list[0]["session_id"] == "session_1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

