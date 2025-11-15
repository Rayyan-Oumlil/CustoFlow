"""
Caching Utilities for Performance Optimization

Provides caching for frequently accessed data like FAQ responses
to reduce API calls and improve response times.
"""
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import hashlib
import threading


class TTLCache:
    """
    Thread-safe Time-To-Live cache.
    
    Stores key-value pairs with expiration times.
    Automatically evicts expired entries.
    """
    
    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize cache with TTL.
        
        Args:
            ttl_seconds: Time to live in seconds (default: 1 hour)
        """
        self._cache: Dict[str, tuple[Any, datetime]] = {}
        self._lock = threading.Lock()
        self._ttl = timedelta(seconds=ttl_seconds)
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if not expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key in self._cache:
                value, expiry = self._cache[key]
                if datetime.now() < expiry:
                    return value
                else:
                    # Expired, remove it
                    del self._cache[key]
            return None
    
    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache with expiration.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        with self._lock:
            expiry = datetime.now() + self._ttl
            self._cache[key] = (value, expiry)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
    
    def size(self) -> int:
        """Get current cache size."""
        with self._lock:
            return len(self._cache)


def generate_cache_key(prefix: str, *args) -> str:
    """
    Generate a cache key from prefix and arguments.
    
    Args:
        prefix: Key prefix (e.g., "faq")
        *args: Arguments to include in key
        
    Returns:
        Cache key string
    """
    # Create hash of arguments
    key_string = f"{prefix}:{':'.join(str(arg) for arg in args)}"
    return hashlib.md5(key_string.encode()).hexdigest()


# Global cache instances
faq_cache = TTLCache(ttl_seconds=3600)  # 1 hour TTL for FAQ responses
order_cache = TTLCache(ttl_seconds=1800)  # 30 minutes TTL for order data

