"""Integration tests for end-to-end functionality."""
import pytest
import asyncio
from google.genai import types

from agents.faq_agent import faq_agent
from agents.order_agent import order_agent
from agents.orchestrator_agent import orchestrator_agent
from google.adk.runners import InMemoryRunner
from utils.validation import validate_message, sanitize_message
from utils.rate_limiter import rate_limiter
from utils.cache import faq_cache, order_cache


@pytest.mark.asyncio
async def test_faq_agent_integration():
    """Test FAQ agent with validation and caching."""
    # Validate input
    query = "What is your refund policy?"
    is_valid, error = validate_message(query)
    assert is_valid
    
    # Sanitize
    sanitized = sanitize_message(query)
    
    # Run agent
    runner = InMemoryRunner(agent=faq_agent)
    events = await runner.run_debug(sanitized)
    
    # Check response
    response_text = ""
    for event in events:
        if event.is_final_response() and event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    response_text = part.text
                    break
            if response_text:
                break
    
    assert len(response_text) > 0
    assert "refund" in response_text.lower() or "return" in response_text.lower()


@pytest.mark.asyncio
async def test_order_agent_integration():
    """Test order agent with validation."""
    query = "What's the status of order 12345?"
    is_valid, error = validate_message(query)
    assert is_valid
    
    runner = InMemoryRunner(agent=order_agent)
    events = await runner.run_debug(query)
    
    response_text = ""
    for event in events:
        if event.is_final_response() and event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    response_text = part.text
                    break
            if response_text:
                break
    
    assert len(response_text) > 0
    assert "12345" in response_text or "order" in response_text.lower()


@pytest.mark.asyncio
async def test_orchestrator_routing():
    """Test orchestrator routing with rate limiting."""
    # Check rate limit
    is_allowed, error = rate_limiter.is_allowed("test_user")
    assert is_allowed
    
    query = "I want to know about refunds"
    runner = InMemoryRunner(agent=orchestrator_agent)
    events = await runner.run_debug(query)
    
    response_text = ""
    for event in events:
        if event.is_final_response() and event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    response_text = part.text
                    break
            if response_text:
                break
    
    assert len(response_text) > 0


def test_rate_limiting_integration():
    """Test rate limiting with multiple requests."""
    from utils.rate_limiter import RateLimiter
    limiter = RateLimiter(max_requests=3, window_seconds=60)
    
    # Make requests up to limit
    for i in range(3):
        is_allowed, error = limiter.is_allowed("integration_test")
        assert is_allowed
    
    # Next request should be blocked
    is_allowed, error = limiter.is_allowed("integration_test")
    assert not is_allowed


def test_cache_integration():
    """Test cache integration with FAQ tool."""
    from tools.faq_tool import search_faq
    
    # First call - should not be cached
    result1 = search_faq("What is your refund policy?")
    
    # Second call - should be cached (same query)
    result2 = search_faq("What is your refund policy?")
    
    # Results should be identical
    assert result1 == result2

