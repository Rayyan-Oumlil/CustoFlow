"""
Error Handling Utilities

Provides consistent error handling and user-friendly error messages.
"""
from typing import Optional, Dict, Any
import logging
import asyncio
from functools import wraps

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Custom API error with user-friendly message."""
    
    def __init__(self, message: str, status_code: int = 500, user_message: Optional[str] = None):
        """
        Initialize API error.
        
        Args:
            message: Internal error message
            status_code: HTTP status code
            user_message: User-friendly error message
        """
        self.message = message
        self.status_code = status_code
        self.user_message = user_message or "An error occurred. Please try again later."
        super().__init__(self.message)


def handle_api_errors(func):
    """
    Decorator to handle API errors gracefully.
    
    Catches exceptions and returns user-friendly error messages.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except APIError as e:
            logger.error(f"API Error: {e.message}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
            raise APIError(
                message=str(e),
                status_code=500,
                user_message="An unexpected error occurred. Please try again later."
            )
    return wrapper


async def with_timeout(coro, timeout_seconds: int = 30, default_response: Any = None):
    """
    Execute coroutine with timeout.
    
    Args:
        coro: Coroutine to execute
        timeout_seconds: Timeout in seconds
        default_response: Response if timeout occurs
        
    Returns:
        Coroutine result or default_response if timeout
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        logger.warning(f"Operation timed out after {timeout_seconds} seconds")
        return default_response


def get_user_friendly_error(error: Exception) -> str:
    """
    Convert technical error to user-friendly message.
    
    Args:
        error: Exception that occurred
        
    Returns:
        User-friendly error message
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    # Map common errors to user-friendly messages
    if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
        return "The request took too long. Please try again."
    
    if "rate limit" in error_msg.lower() or "429" in error_msg:
        return "Too many requests. Please wait a moment and try again."
    
    if "api key" in error_msg.lower() or "authentication" in error_msg.lower():
        return "Service configuration error. Please contact support."
    
    if "not found" in error_msg.lower() or "404" in error_msg:
        return "The requested resource was not found."
    
    # Default user-friendly message
    return "An error occurred. Please try again or contact support if the problem persists."

