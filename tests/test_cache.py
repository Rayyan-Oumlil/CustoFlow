"""Tests for caching utilities."""
import time
from utils.cache import TTLCache, generate_cache_key


def test_cache_set_get():
    """Test basic cache set and get."""
    cache = TTLCache(ttl_seconds=60)
    
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"


def test_cache_expiration():
    """Test cache expiration."""
    cache = TTLCache(ttl_seconds=1)  # 1 second TTL
    
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"
    
    # Wait for expiration
    time.sleep(1.1)
    
    # Should be expired
    assert cache.get("key1") is None


def test_cache_clear():
    """Test cache clear functionality."""
    cache = TTLCache(ttl_seconds=60)
    
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    
    assert cache.size() == 2
    
    cache.clear()
    
    assert cache.size() == 0
    assert cache.get("key1") is None


def test_generate_cache_key():
    """Test cache key generation."""
    key1 = generate_cache_key("faq", "query1")
    key2 = generate_cache_key("faq", "query1")
    key3 = generate_cache_key("faq", "query2")
    
    # Same inputs should generate same key
    assert key1 == key2
    
    # Different inputs should generate different keys
    assert key1 != key3

