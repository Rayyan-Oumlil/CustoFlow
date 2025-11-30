"""Tests for input validation utilities."""
import pytest
from utils.validation import validate_message, sanitize_message, validate_order_id, validate_user_id


def test_validate_message_empty():
    """Test validation of empty message."""
    is_valid, error = validate_message("")
    assert not is_valid
    assert "empty" in error.lower()


def test_validate_message_whitespace():
    """Test validation of whitespace-only message."""
    is_valid, error = validate_message("   ")
    assert not is_valid


def test_validate_message_too_long():
    """Test validation of message exceeding max length."""
    long_message = "a" * 6000
    is_valid, error = validate_message(long_message)
    assert not is_valid
    assert "too long" in error.lower()


def test_validate_message_valid():
    """Test validation of valid message."""
    is_valid, error = validate_message("Hello, I need help")
    assert is_valid
    assert error is None


def test_sanitize_message():
    """Test message sanitization."""
    # Test null bytes removal
    message = "Hello\x00World"
    sanitized = sanitize_message(message)
    assert "\x00" not in sanitized
    
    # Test control characters removal
    message = "Hello\x01\x02World"
    sanitized = sanitize_message(message)
    assert "\x01" not in sanitized
    assert "\x02" not in sanitized


def test_validate_order_id():
    """Test order ID validation."""
    # Valid order IDs
    assert validate_order_id("12345")[0] is True
    assert validate_order_id("ABC123")[0] is True
    assert validate_order_id("ORDER-123")[0] is True
    
    # Invalid order IDs
    assert validate_order_id("")[0] is False
    assert validate_order_id("ab")[0] is False  # Too short
    assert validate_order_id("a" * 31)[0] is False  # Too long (limit is 30)


def test_validate_user_id():
    """Test user ID validation."""
    # Valid user IDs
    assert validate_user_id("user123")[0] is True
    assert validate_user_id("user_123")[0] is True
    assert validate_user_id("user-123")[0] is True
    
    # Invalid user IDs
    assert validate_user_id("")[0] is False
    assert validate_user_id("a" * 60)[0] is False  # Too long

