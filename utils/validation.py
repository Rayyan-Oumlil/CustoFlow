"""
Input Validation Utilities

Provides validation and sanitization functions for user inputs
to prevent security issues and ensure data quality.
"""
import re
from typing import Optional


def validate_message(message: str, max_length: int = 5000) -> tuple[bool, Optional[str]]:
    """
    Validate user message.
    
    Args:
        message: User message to validate
        max_length: Maximum allowed length
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not message or not message.strip():
        return False, "Message cannot be empty"
    
    if len(message) > max_length:
        return False, f"Message is too long (max {max_length} characters)"
    
    return True, None


def sanitize_message(message: str) -> str:
    """
    Sanitize user message to prevent injection attacks.
    
    Removes potentially dangerous characters while preserving
    normal text content.
    
    Args:
        message: Raw user message
        
    Returns:
        Sanitized message
    """
    # Remove null bytes
    message = message.replace('\x00', '')
    
    # Remove control characters except newlines and tabs
    message = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', message)
    
    # Limit consecutive whitespace
    message = re.sub(r'\s+', ' ', message)
    
    # Strip and limit length
    message = message.strip()[:5000]
    
    return message


def validate_order_id(order_id: str) -> tuple[bool, Optional[str]]:
    """
    Validate order ID format.
    
    Args:
        order_id: Order ID to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not order_id or not order_id.strip():
        return False, "Order ID cannot be empty"
    
    # Order IDs should be alphanumeric, typically 5-10 characters
    if not re.match(r'^[A-Za-z0-9-]{3,20}$', order_id.strip()):
        return False, "Invalid order ID format"
    
    return True, None


def validate_user_id(user_id: str) -> tuple[bool, Optional[str]]:
    """
    Validate user ID format.
    
    Args:
        user_id: User ID to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not user_id or not user_id.strip():
        return False, "User ID cannot be empty"
    
    # User IDs should be alphanumeric with underscores/hyphens
    if not re.match(r'^[A-Za-z0-9_-]{1,50}$', user_id.strip()):
        return False, "Invalid user ID format"
    
    return True, None

