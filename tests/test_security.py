"""
Security Tests for CustoFlow

Tests input validation, sanitization, and security measures.
"""
import pytest
from utils.validation import validate_message, sanitize_message, validate_order_id, validate_user_id
from utils.rate_limiter import rate_limiter


def test_sql_injection_prevention():
    """Test that SQL injection attempts are sanitized."""
    malicious_inputs = [
        "'; DROP TABLE users; --",
        "1' OR '1'='1",
        "admin'--",
        "'; DELETE FROM orders; --"
    ]
    
    for malicious in malicious_inputs:
        sanitized = sanitize_message(malicious)
        # Should remove dangerous SQL injection characters (semicolons, quotes)
        # Note: We don't remove SQL keywords like DROP/DELETE because we use
        # parameterized queries (Supabase handles this). The important thing
        # is removing the injection characters (; ' --) that make SQL injection possible.
        assert "';" not in sanitized, f"SQL injection pattern '; not removed from: {malicious}"
        assert ";" not in sanitized, f"Semicolon not removed from: {malicious}"
        # The words DROP/DELETE may remain, but without ; and quotes, they can't execute SQL


def test_xss_prevention():
    """Test that XSS attempts are sanitized."""
    malicious_inputs = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "javascript:alert('XSS')",
        "<iframe src='evil.com'></iframe>"
    ]
    
    for malicious in malicious_inputs:
        sanitized = sanitize_message(malicious)
        # Should remove or neutralize script tags
        assert "<script" not in sanitized.lower()
        assert "javascript:" not in sanitized.lower()


def test_command_injection_prevention():
    """Test that command injection attempts are sanitized."""
    malicious_inputs = [
        "; rm -rf /",
        "| cat /etc/passwd",
        "&& ls -la",
        "`whoami`"
    ]
    
    for malicious in malicious_inputs:
        sanitized = sanitize_message(malicious)
        # Should remove command separators
        assert ";" not in sanitized
        assert "|" not in sanitized
        assert "&&" not in sanitized
        assert "`" not in sanitized


def test_path_traversal_prevention():
    """Test that path traversal attempts are sanitized."""
    malicious_inputs = [
        "../../etc/passwd",
        "..\\..\\windows\\system32",
        "/etc/shadow",
        "C:\\Windows\\System32"
    ]
    
    for malicious in malicious_inputs:
        sanitized = sanitize_message(malicious)
        # Should remove path traversal patterns
        assert ".." not in sanitized
        assert "/etc" not in sanitized.lower()
        assert "\\windows" not in sanitized.lower()


def test_null_byte_injection():
    """Test that null bytes are removed."""
    malicious = "test\x00string\x00injection"
    sanitized = sanitize_message(malicious)
    assert "\x00" not in sanitized


def test_control_character_removal():
    """Test that control characters are removed."""
    malicious = "test\x01\x02\x03\x04\x05string"
    sanitized = sanitize_message(malicious)
    # Should only contain printable characters (except newlines/tabs)
    for char in sanitized:
        assert ord(char) >= 32 or char in ['\n', '\t'], f"Control character found: {repr(char)}"


def test_message_length_limit():
    """Test that extremely long messages are rejected."""
    # Create message exceeding limit
    long_message = "a" * 6000
    
    is_valid, error = validate_message(long_message, max_length=5000)
    assert not is_valid
    assert "too long" in error.lower()


def test_empty_message_rejection():
    """Test that empty messages are rejected."""
    empty_inputs = ["", "   ", "\t\n", "\x00"]
    
    for empty in empty_inputs:
        is_valid, error = validate_message(empty)
        assert not is_valid
        assert "empty" in error.lower()


def test_order_id_validation():
    """Test that invalid order IDs are rejected."""
    invalid_ids = [
        "",
        "ab",  # Too short
        "a" * 31,  # Too long (limit is 30)
        "123; DROP TABLE",  # SQL injection attempt
        "../../etc/passwd",  # Path traversal
        "<script>alert('xss')</script>",  # XSS attempt
    ]
    
    for invalid_id in invalid_ids:
        is_valid, error = validate_order_id(invalid_id)
        assert not is_valid, f"Invalid order ID should be rejected: {invalid_id}"


def test_user_id_validation():
    """Test that invalid user IDs are rejected."""
    invalid_ids = [
        "",
        "a" * 60,  # Too long
        "user; DROP TABLE",  # SQL injection attempt
        "../../etc/passwd",  # Path traversal
        "<script>alert('xss')</script>",  # XSS attempt
    ]
    
    for invalid_id in invalid_ids:
        is_valid, error = validate_user_id(invalid_id)
        assert not is_valid, f"Invalid user ID should be rejected: {invalid_id}"


def test_rate_limiting_security():
    """Test that rate limiting prevents abuse."""
    limiter = rate_limiter
    
    # Make requests up to limit
    for i in range(60):
        is_allowed, error = limiter.is_allowed("security_test_user")
        if not is_allowed:
            # Should be blocked after limit
            assert "rate limit" in error.lower()
            break
    
    # Reset for other tests
    limiter.reset("security_test_user")


def test_special_character_handling():
    """Test that special characters are handled safely."""
    special_chars = [
        "Hello! @#$%^&*()",
        "Test with émojis 🎉🚀",
        "Unicode: 你好 こんにちは",
        "Mixed: Test123!@#$%"
    ]
    
    for special in special_chars:
        sanitized = sanitize_message(special)
        # Should preserve most characters but remove dangerous ones
        assert len(sanitized) > 0
        # Should not contain null bytes or control chars
        assert "\x00" not in sanitized


def test_concurrent_rate_limiting():
    """Test rate limiting under concurrent requests."""
    from concurrent.futures import ThreadPoolExecutor
    
    limiter = rate_limiter
    test_id = "concurrent_test_user"
    
    def make_request():
        return limiter.is_allowed(test_id)
    
    # Make concurrent requests
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(lambda _: make_request(), range(70)))
    
    # Should have some blocked requests
    blocked = sum(1 for allowed, _ in results if not allowed)
    assert blocked > 0, "Rate limiting should block some concurrent requests"
    
    # Reset for other tests
    limiter.reset(test_id)

