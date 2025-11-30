"""
Comprehensive tests for error handling utilities.
Tests error handling, timeouts, and user-friendly error messages.
"""
import pytest
import asyncio
from utils.error_handler import APIError, handle_api_errors, with_timeout, get_user_friendly_error


def test_api_error_creation():
    """Test APIError creation with different parameters."""
    # Test with all parameters
    error = APIError("Internal error", status_code=500, user_message="Something went wrong")
    assert error.message == "Internal error"
    assert error.status_code == 500
    assert error.user_message == "Something went wrong"
    
    # Test with default user_message
    error2 = APIError("Another error", status_code=404)
    assert error2.message == "Another error"
    assert error2.status_code == 404
    assert error2.user_message == "An error occurred. Please try again later."


def test_api_error_inheritance():
    """Test that APIError is a proper Exception."""
    error = APIError("Test error")
    assert isinstance(error, Exception)
    assert str(error) == "Test error"


@pytest.mark.asyncio
async def test_handle_api_errors_success():
    """Test handle_api_errors decorator with successful function."""
    @handle_api_errors
    async def successful_function():
        return {"status": "success", "data": "test"}
    
    result = await successful_function()
    assert result["status"] == "success"
    assert result["data"] == "test"


@pytest.mark.asyncio
async def test_handle_api_errors_api_error():
    """Test handle_api_errors decorator with APIError."""
    @handle_api_errors
    async def function_with_api_error():
        raise APIError("API error", status_code=400, user_message="Bad request")
    
    with pytest.raises(APIError) as exc_info:
        await function_with_api_error()
    
    assert exc_info.value.status_code == 400
    assert exc_info.value.user_message == "Bad request"


@pytest.mark.asyncio
async def test_handle_api_errors_generic_exception():
    """Test handle_api_errors decorator with generic exception."""
    @handle_api_errors
    async def function_with_generic_error():
        raise ValueError("Something went wrong")
    
    with pytest.raises(APIError) as exc_info:
        await function_with_generic_error()
    
    assert exc_info.value.status_code == 500
    assert "unexpected error" in exc_info.value.user_message.lower()


@pytest.mark.asyncio
async def test_with_timeout_success():
    """Test with_timeout with successful coroutine."""
    async def fast_operation():
        await asyncio.sleep(0.1)
        return "success"
    
    result = await with_timeout(fast_operation(), timeout_seconds=1)
    assert result == "success"


@pytest.mark.asyncio
async def test_with_timeout_timeout():
    """Test with_timeout with timeout."""
    async def slow_operation():
        await asyncio.sleep(2)
        return "too slow"
    
    result = await with_timeout(slow_operation(), timeout_seconds=0.5, default_response="timeout")
    assert result == "timeout"


@pytest.mark.asyncio
async def test_with_timeout_no_default():
    """Test with_timeout with timeout and no default."""
    async def slow_operation():
        await asyncio.sleep(2)
        return "too slow"
    
    result = await with_timeout(slow_operation(), timeout_seconds=0.5)
    assert result is None


def test_get_user_friendly_error_timeout():
    """Test get_user_friendly_error with timeout error."""
    error = Exception("Request timed out after 30 seconds")
    message = get_user_friendly_error(error)
    assert "too long" in message.lower() or "try again" in message.lower()


def test_get_user_friendly_error_rate_limit():
    """Test get_user_friendly_error with rate limit error."""
    error = Exception("Rate limit exceeded: 429")
    message = get_user_friendly_error(error)
    assert "too many requests" in message.lower() or "wait" in message.lower()


def test_get_user_friendly_error_auth():
    """Test get_user_friendly_error with authentication error."""
    error = Exception("Invalid API key")
    message = get_user_friendly_error(error)
    assert "configuration" in message.lower() or "contact support" in message.lower()


def test_get_user_friendly_error_not_found():
    """Test get_user_friendly_error with not found error."""
    error = Exception("Resource not found: 404")
    message = get_user_friendly_error(error)
    assert "not found" in message.lower()


def test_get_user_friendly_error_generic():
    """Test get_user_friendly_error with generic error."""
    error = Exception("Some random error")
    message = get_user_friendly_error(error)
    assert "error occurred" in message.lower() or "try again" in message.lower()


def test_get_user_friendly_error_empty():
    """Test get_user_friendly_error with empty error message."""
    error = Exception("")
    message = get_user_friendly_error(error)
    assert len(message) > 0  # Should return default message


