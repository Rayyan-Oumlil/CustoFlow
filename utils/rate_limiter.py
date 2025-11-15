"""
Rate Limiting Utilities

Provides rate limiting to prevent abuse and spam.
"""
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import threading


class RateLimiter:
    """
    Thread-safe rate limiter.
    
    Tracks requests per user/IP and enforces limits.
    """
    
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
        """
        self._max_requests = max_requests
        self._window = timedelta(seconds=window_seconds)
        self._requests: Dict[str, list[datetime]] = defaultdict(list)
        self._lock = threading.Lock()
    
    def is_allowed(self, identifier: str) -> Tuple[bool, Optional[str]]:
        """
        Check if request is allowed.
        
        Args:
            identifier: User ID or IP address
            
        Returns:
            Tuple of (is_allowed, error_message)
        """
        with self._lock:
            now = datetime.now()
            cutoff = now - self._window
            
            # Clean old requests
            self._requests[identifier] = [
                req_time for req_time in self._requests[identifier]
                if req_time > cutoff
            ]
            
            # Check limit
            if len(self._requests[identifier]) >= self._max_requests:
                return False, f"Rate limit exceeded. Maximum {self._max_requests} requests per {self._window.total_seconds()} seconds."
            
            # Record request
            self._requests[identifier].append(now)
            return True, None
    
    def reset(self, identifier: str) -> None:
        """Reset rate limit for an identifier."""
        with self._lock:
            if identifier in self._requests:
                del self._requests[identifier]
    
    def get_remaining(self, identifier: str) -> int:
        """Get remaining requests for an identifier."""
        with self._lock:
            now = datetime.now()
            cutoff = now - self._window
            
            self._requests[identifier] = [
                req_time for req_time in self._requests[identifier]
                if req_time > cutoff
            ]
            
            return max(0, self._max_requests - len(self._requests[identifier]))


# Global rate limiter instance
# 60 requests per minute per user
rate_limiter = RateLimiter(max_requests=60, window_seconds=60)

