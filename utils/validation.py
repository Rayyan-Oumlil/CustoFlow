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


def validate_customer_id(customer_id: str, custom_pattern: Optional[str] = None) -> tuple[bool, Optional[str]]:
    """
    Validate customer ID format.
    
    Default format: cust_XXX or CUST-XXX (e.g., cust_001, CUST-123)
    Must start with "cust" (case insensitive) followed by underscore/hyphen and numbers.
    
    Args:
        customer_id: Customer ID to validate
        custom_pattern: Optional custom regex pattern. If None, uses default pattern.
                       Default: r'^cust[_\-][0-9]+$' for "cust_001" or "CUST-123" format
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not customer_id or not customer_id.strip():
        return False, "Customer ID cannot be empty"
    
    trimmed = customer_id.strip()
    
    # Check minimum length (cust_001 = 8 chars minimum)
    if len(trimmed) < 6:
        return False, "Customer ID is too short. Must be at least 6 characters (e.g., cust_001)"
    
    # Check maximum length
    if len(trimmed) > 50:
        return False, "Customer ID is too long. Maximum 50 characters"
    
    # Default pattern: Must start with "cust" (case insensitive) followed by underscore/hyphen and numbers
    # Examples: cust_001, CUST-123, cust_12345, CUST_999
    default_pattern = r'^cust[_\-][0-9]+$'
    pattern = custom_pattern if custom_pattern is not None else default_pattern
    
    if not re.match(pattern, trimmed, re.IGNORECASE):
        return False, "Invalid customer ID format. Must be in format: cust_XXX or CUST-XXX (e.g., cust_001, CUST-123)"
    
    return True, None

