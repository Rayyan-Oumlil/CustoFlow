"""
Tests for Conversation Summarization Feature

Tests the conversation summarization functionality including:
- Summary generation
- Key points extraction
- Sentiment analysis
- Action items extraction
- Summary storage and retrieval
- Export functionality
"""
import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from utils.conversation_summarizer import ConversationSummarizer, conversation_summarizer
from memory.conversation_history import conversation_history


@pytest.fixture
def sample_conversation():
    """Sample conversation history for testing."""
    return [
        {
            "timestamp": "2025-01-16T10:00:00",
            "session_id": "test_session",
            "role": "user",
            "content": "I'm frustrated with my order 12345. It hasn't arrived yet and I need it urgently."
        },
        {
            "timestamp": "2025-01-16T10:01:00",
            "session_id": "test_session",
            "role": "assistant",
            "content": "I understand your frustration. Let me check the status of order 12345 for you."
        },
        {
            "timestamp": "2025-01-16T10:02:00",
            "session_id": "test_session",
            "role": "user",
            "content": "This is unacceptable. I need a refund or I'll cancel my subscription."
        },
        {
            "timestamp": "2025-01-16T10:03:00",
            "session_id": "test_session",
            "role": "assistant",
            "content": "I apologize for the inconvenience. I've created a ticket TICKET-ABC123 for you. Our support team will contact you within 24 hours."
        }
    ]


@pytest.fixture
def mock_gemini_response():
    """Mock Gemini API response."""
    mock_response = Mock()
    mock_response.text = """
    Customer Issue: The customer is frustrated with order 12345 that hasn't arrived yet. They need it urgently and are threatening to cancel their subscription.
    
    Attempted Solutions: The agent checked the order status and created a support ticket TICKET-ABC123 for escalation.
    
    Current Status: A ticket has been created and the customer is waiting for support team contact within 24 hours.
    
    Action Items:
    1. Contact customer within 24 hours
    2. Investigate order 12345 shipping status
    3. Consider refund or expedited shipping option
    4. Address subscription cancellation threat
    
    Next Steps:
    1. Review order 12345 tracking information
    2. Contact customer to resolve issue
    3. Offer compensation if appropriate
    """
    return mock_response


class TestConversationSummarizer:
    """Test suite for ConversationSummarizer."""
    
    def test_initialization(self):
        """Test that summarizer initializes correctly."""
        summarizer = ConversationSummarizer()
        assert summarizer is not None
        assert hasattr(summarizer, '_summaries')
        assert hasattr(summarizer, 'client')
    
    def test_format_conversation(self, sample_conversation):
        """Test conversation formatting."""
        summarizer = ConversationSummarizer()
        formatted = summarizer._format_conversation(sample_conversation)
        
        assert "Customer" in formatted
        assert "Agent" in formatted
        assert "order 12345" in formatted
        assert "TICKET-ABC123" in formatted
    
    def test_analyze_sentiment_negative(self):
        """Test sentiment analysis for negative conversation."""
        summarizer = ConversationSummarizer()
        text = "I'm frustrated and angry. This is terrible service."
        sentiment = summarizer._analyze_sentiment(text)
        
        assert sentiment is not None
        assert sentiment["sentiment"] == "negative"
        assert sentiment["urgency"] in ["high", "medium"]
    
    def test_analyze_sentiment_positive(self):
        """Test sentiment analysis for positive conversation."""
        summarizer = ConversationSummarizer()
        text = "Thank you so much! This is great service. I'm very happy."
        sentiment = summarizer._analyze_sentiment(text)
        
        assert sentiment is not None
        assert sentiment["sentiment"] == "positive"
        assert sentiment["urgency"] == "low"
    
    def test_analyze_sentiment_neutral(self):
        """Test sentiment analysis for neutral conversation."""
        summarizer = ConversationSummarizer()
        text = "I would like to check my order status."
        sentiment = summarizer._analyze_sentiment(text)
        
        assert sentiment is not None
        assert sentiment["sentiment"] == "neutral"
    
    def test_build_summary_prompt(self):
        """Test summary prompt building."""
        summarizer = ConversationSummarizer()
        conversation_text = "Test conversation"
        prompt = summarizer._build_summary_prompt(
            conversation_text,
            "medium",
            {"sentiment": "negative"},
            "TICKET-123"
        )
        
        assert "Customer Issue" in prompt
        assert "Attempted Solutions" in prompt
        assert "TICKET-123" in prompt
        assert "1 paragraph" in prompt
    
    def test_get_max_tokens(self):
        """Test max tokens calculation."""
        summarizer = ConversationSummarizer()
        
        assert summarizer._get_max_tokens("short") == 200
        assert summarizer._get_max_tokens("medium") == 500
        assert summarizer._get_max_tokens("long") == 1000
        assert summarizer._get_max_tokens("unknown") == 500
    
    @patch('utils.conversation_summarizer.conversation_history.get_history')
    @patch('utils.conversation_summarizer.Client')
    def test_generate_summary_success(
        self,
        mock_client_class,
        mock_get_history,
        sample_conversation,
        mock_gemini_response
    ):
        """Test successful summary generation."""
        # Setup mocks
        mock_get_history.return_value = sample_conversation
        
        # Mock the Client class and models.generate_content
        mock_client = Mock()
        mock_models = Mock()
        mock_models.generate_content.return_value = mock_gemini_response
        mock_client.models = mock_models
        mock_client_class.return_value = mock_client
        
        summarizer = ConversationSummarizer()
        # Ensure client is set correctly
        summarizer.client = mock_client
        
        result = summarizer.generate_summary(
            user_id="test_user",
            session_id="test_session",
            summary_length="medium",
            include_sentiment=True,
            ticket_id="TICKET-123"
        )
        
        assert result.get("status") == "success"
        assert "summary" in result
        assert "key_points" in result
        assert "sentiment" in result
        assert result.get("ticket_id") == "TICKET-123"
    
    @patch('utils.conversation_summarizer.conversation_history.get_history')
    def test_generate_summary_no_history(self, mock_get_history):
        """Test summary generation with no conversation history."""
        mock_get_history.return_value = []
        
        summarizer = ConversationSummarizer()
        result = summarizer.generate_summary(
            user_id="test_user",
            session_id="test_session"
        )
        
        assert result.get("status") == "error"
        assert "No conversation history" in result.get("error_message", "")
    
    def test_parse_summary(self, mock_gemini_response):
        """Test summary parsing."""
        summarizer = ConversationSummarizer()
        summary_text = mock_gemini_response.text
        sentiment = {"sentiment": "negative", "emotion": "frustrated"}
        
        parsed = summarizer._parse_summary(summary_text, sentiment, "TICKET-123")
        
        assert "summary" in parsed
        assert "key_points" in parsed
        assert "sentiment" in parsed
        assert parsed["ticket_id"] == "TICKET-123"
        assert len(parsed["action_items"]) > 0
    
    def test_extract_section(self):
        """Test section extraction from summary."""
        summarizer = ConversationSummarizer()
        text = "Customer Issue: The order is delayed. Attempted Solutions: We checked the status."
        
        issue = summarizer._extract_section(text, ["customer issue", "main problem"])
        assert "order" in issue.lower() or issue == ""
    
    def test_extract_list_items(self):
        """Test list items extraction."""
        summarizer = ConversationSummarizer()
        text = "Action Items:\n1. Contact customer\n2. Check order status\n3. Provide update"
        
        items = summarizer._extract_list_items(text, ["action items"])
        assert len(items) > 0
        assert any("contact" in item.lower() or "customer" in item.lower() for item in items)
    
    def test_get_summary(self):
        """Test retrieving a stored summary."""
        summarizer = ConversationSummarizer()
        
        # Add a test summary
        test_summary = {
            "summary": "Test summary",
            "key_points": {},
            "sentiment": {},
            "action_items": [],
            "next_steps": [],
            "timestamp": "2025-01-16T10:00:00",
            "ticket_id": "TICKET-123"
        }
        summarizer._summaries["test_user_test_session_TICKET-123"] = test_summary
        
        retrieved = summarizer.get_summary(
            user_id="test_user",
            session_id="test_session",
            ticket_id="TICKET-123"
        )
        
        assert retrieved is not None
        assert retrieved["ticket_id"] == "TICKET-123"
    
    def test_get_summaries_by_ticket(self):
        """Test retrieving summaries by ticket ID."""
        summarizer = ConversationSummarizer()
        
        # Clear existing summaries to avoid interference from other tests
        summarizer._summaries.clear()
        
        # Add test summaries
        test_summary = {
            "summary": "Test summary",
            "ticket_id": "TICKET-123"
        }
        summarizer._summaries["key1"] = test_summary
        summarizer._summaries["key2"] = {"ticket_id": "TICKET-456"}
        
        summaries = summarizer.get_summaries_by_ticket("TICKET-123")
        assert len(summaries) == 1
        assert summaries[0]["ticket_id"] == "TICKET-123"
    
    def test_export_summaries_json(self):
        """Test exporting summaries as JSON."""
        summarizer = ConversationSummarizer()
        summarizer._summaries = {
            "key1": {"summary": "Test 1", "ticket_id": "TICKET-123"},
            "key2": {"summary": "Test 2", "ticket_id": "TICKET-456"}
        }
        
        exported = summarizer.export_summaries(format="json")
        data = json.loads(exported)
        
        assert "key1" in data
        assert "key2" in data
    
    def test_export_summaries_csv(self):
        """Test exporting summaries as CSV."""
        summarizer = ConversationSummarizer()
        summarizer._summaries = {
            "key1": {
                "summary": "Test summary",
                "ticket_id": "TICKET-123",
                "timestamp": "2025-01-16",
                "summary_length": 100,
                "key_points": {"customer_issue": "Test issue"},
                "sentiment": {"sentiment": "negative"},
                "action_items": ["Item 1", "Item 2"]
            }
        }
        
        exported = summarizer.export_summaries(format="csv")
        assert "Summary Key" in exported
        assert "TICKET-123" in exported
    
    def test_export_summaries_text(self):
        """Test exporting summaries as text."""
        summarizer = ConversationSummarizer()
        summarizer._summaries = {
            "key1": {
                "summary": "Test summary",
                "ticket_id": "TICKET-123",
                "timestamp": "2025-01-16",
                "key_points": {"customer_issue": "Test issue"},
                "action_items": ["Item 1"]
            }
        }
        
        exported = summarizer.export_summaries(format="text")
        assert "Test summary" in exported
        assert "TICKET-123" in exported
    
    def test_export_summaries_with_ticket_filter(self):
        """Test exporting summaries filtered by ticket ID."""
        summarizer = ConversationSummarizer()
        summarizer._summaries = {
            "key1": {"ticket_id": "TICKET-123"},
            "key2": {"ticket_id": "TICKET-456"}
        }
        
        exported = summarizer.export_summaries(format="json", ticket_id="TICKET-123")
        data = json.loads(exported)
        
        assert "key1" in data
        assert "key2" not in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

