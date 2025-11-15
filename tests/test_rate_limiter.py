"""Tests for rate limiting utilities."""
import time
from utils.rate_limiter import RateLimiter


def test_rate_limiter_allows_requests():
    """Test that rate limiter allows requests within limit."""
    limiter = RateLimiter(max_requests=5, window_seconds=60)
    
    for i in range(5):
        is_allowed, error = limiter.is_allowed("test_user")
        assert is_allowed
        assert error is None


def test_rate_limiter_blocks_excess():
    """Test that rate limiter blocks requests exceeding limit."""
    limiter = RateLimiter(max_requests=3, window_seconds=60)
    
    # Make 3 requests (should all pass)
    for i in range(3):
        is_allowed, error = limiter.is_allowed("test_user")
        assert is_allowed
    
    # 4th request should be blocked
    is_allowed, error = limiter.is_allowed("test_user")
    assert not is_allowed
    assert "rate limit" in error.lower()


def test_rate_limiter_reset():
    """Test rate limiter reset functionality."""
    limiter = RateLimiter(max_requests=2, window_seconds=60)
    
    # Make 2 requests
    limiter.is_allowed("test_user")
    limiter.is_allowed("test_user")
    
    # Should be blocked
    assert not limiter.is_allowed("test_user")[0]
    
    # Reset
    limiter.reset("test_user")
    
    # Should be allowed again
    assert limiter.is_allowed("test_user")[0]


def test_rate_limiter_get_remaining():
    """Test getting remaining requests."""
    limiter = RateLimiter(max_requests=5, window_seconds=60)
    
    # Initially should have 5 remaining
    assert limiter.get_remaining("test_user") == 5
    
    # Make 2 requests
    limiter.is_allowed("test_user")
    limiter.is_allowed("test_user")
    
    # Should have 3 remaining
    assert limiter.get_remaining("test_user") == 3

