"""
Order Lookup Tool for Customer Support

This tool provides order information retrieval capabilities. In production,
this would connect to a real order management system (database, API, or CRM).

Current Implementation:
- Mock order database for demonstration purposes
- Supports order lookup by ID
- Supports customer order history
- Provides helpful error messages with guidance
- Response caching for performance

Production Integration:
- Replace _MOCK_ORDERS with database queries or API calls
- See tools/order_tool_production_example.py for integration patterns
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import random
import sys
import json
from pathlib import Path

# Add utils to path for cache import
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.cache import order_cache, generate_cache_key
from utils.validation import validate_order_id


# ============================================================================
# Order Database with Persistence
# ============================================================================
# Orders are stored in data/orders.json for persistence
# In production, this would be replaced with:
# - Database queries (PostgreSQL, MySQL, etc.)
# - API calls to order management system
# - CRM integration (Salesforce, etc.)
# ============================================================================
ORDERS_FILE = Path(__file__).parent.parent / "data" / "orders.json"

# Default orders (used if file doesn't exist)
_DEFAULT_ORDERS = {
    "12345": {
        "order_id": "12345",
        "customer_id": "cust_001",
        "status": "shipped",
        "items": [
            {"name": "Wireless Headphones", "quantity": 1, "price": 99.99}
        ],
        "total": 99.99,
        "order_date": "2024-01-15",
        "shipped_date": "2024-01-16",
        "tracking_number": "TRACK123456",
        "estimated_delivery": "2024-01-22"
    },
    "67890": {
        "order_id": "67890",
        "customer_id": "cust_002",
        "status": "processing",
        "items": [
            {"name": "Laptop Stand", "quantity": 1, "price": 49.99},
            {"name": "USB-C Cable", "quantity": 2, "price": 12.99}
        ],
        "total": 75.97,
        "order_date": "2024-01-20",
        "shipped_date": None,
        "tracking_number": None,
        "estimated_delivery": "2024-01-27"
    },
    "11111": {
        "order_id": "11111",
        "customer_id": "cust_003",
        "status": "delivered",
        "items": [
            {"name": "Mechanical Keyboard", "quantity": 1, "price": 149.99}
        ],
        "total": 149.99,
        "order_date": "2024-01-10",
        "shipped_date": "2024-01-11",
        "tracking_number": "TRACK789012",
        "estimated_delivery": "2024-01-17",
        "delivered_date": "2024-01-16"
    },
    "22222": {
        "order_id": "22222",
        "customer_id": "cust_001",
        "status": "cancelled",
        "items": [
            {"name": "Mouse Pad", "quantity": 1, "price": 19.99}
        ],
        "total": 19.99,
        "order_date": "2024-01-18",
        "cancelled_date": "2024-01-19",
        "reason": "Customer request"
    }
}


def _load_orders() -> Dict[str, Dict]:
    """
    Load orders from JSON file.
    Returns default orders if file doesn't exist.
    """
    try:
        if ORDERS_FILE.exists():
            with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Convert list to dict if needed (for backward compatibility)
                if isinstance(data, list):
                    return {order["order_id"]: order for order in data}
                elif isinstance(data, dict) and "orders" in data:
                    return {order["order_id"]: order for order in data["orders"]}
                elif isinstance(data, dict):
                    return data
        # Return default orders if file doesn't exist
        return _DEFAULT_ORDERS.copy()
    except Exception as e:
        print(f"Warning: Could not load orders from file: {e}. Using default orders.")
        return _DEFAULT_ORDERS.copy()


def _save_orders(orders: Dict[str, Dict]) -> bool:
    """
    Save orders to JSON file.
    Returns True if successful, False otherwise.
    """
    try:
        # Ensure data directory exists
        ORDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Save as JSON
        with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(orders, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving orders to file: {e}")
        return False


# Load orders at module import
_MOCK_ORDERS = _load_orders()


def add_order(order_data: Dict) -> bool:
    """
    Add a new order to the database and save to file.
    
    Args:
        order_data: Order dictionary with all required fields
        
    Returns:
        True if successful, False otherwise
    """
    try:
        order_id = order_data.get("order_id")
        if not order_id:
            return False
        
        # Add order to in-memory dict
        _MOCK_ORDERS[order_id] = order_data
        
        # Save to file
        return _save_orders(_MOCK_ORDERS)
    except Exception as e:
        print(f"Error adding order: {e}")
        return False


def lookup_order(order_id: str) -> Dict[str, any]:
    """
    Look up order information by order ID.
    
    This tool searches the order database to retrieve comprehensive order details
    including status, items, shipping information, and tracking numbers.
    
    Implementation Details:
    - Validates order ID format
    - Searches mock database (replace with real DB/API in production)
    - Returns structured response with all order information
    - Provides helpful error messages with guidance
    
    Args:
        order_id: The order ID to look up (e.g., "12345")
        
    Returns:
        Dictionary with status and order information:
        - Success: {
            "status": "success",
            "order": {
                "order_id": str,
                "customer_id": str,
                "status": str,  # processing, shipped, delivered, cancelled
                "items": List[Dict],
                "total": float,
                "order_date": str,
                "shipped_date": str | None,
                "tracking_number": str | None,
                "estimated_delivery": str | None
            }
          }
        - Error: {
            "status": "error",
            "error_message": str,
            "helpful_info": str  # Guidance for customer
          }
    """
    try:
        # Validate order ID
        is_valid, error_msg = validate_order_id(str(order_id))
        if not is_valid:
            return {
                "status": "error",
                "error_message": error_msg,
                "helpful_info": "Order IDs are typically 5-10 alphanumeric characters. You can find your order number in your confirmation email or account dashboard."
            }
        
        order_id = str(order_id).strip()
        
        # Check cache first
        cache_key = generate_cache_key("order", order_id)
        cached_result = order_cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # Look up order in mock database
        order = _MOCK_ORDERS.get(order_id)
        
        if order:
            result = {
                "status": "success",
                "order": order
            }
            # Cache successful result
            order_cache.set(cache_key, result)
            return result
        else:
            # Provide helpful guidance even when order not found
            result = {
                "status": "error",
                "error_message": f"Order {order_id} not found. Please check the order ID and try again.",
                "helpful_info": "Order IDs are typically 5-10 digits. You can find your order number in your confirmation email or account dashboard. If you're having trouble, please contact support with your email address or customer ID."
            }
            # Cache error result briefly (5 minutes) to avoid repeated lookups
            error_cache_key = generate_cache_key("order_error", order_id)
            order_cache.set(error_cache_key, result)
            return result
    
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error looking up order: {str(e)}"
        }


def get_customer_orders(customer_id: str) -> Dict[str, any]:
    """
    Get all orders for a customer.
    
    Args:
        customer_id: The customer ID to look up
        
    Returns:
        Dictionary with status and list of orders
    """
    try:
        customer_id = str(customer_id).strip()
        
        if not customer_id:
            return {
                "status": "error",
                "error_message": "Customer ID cannot be empty"
            }
        
        # Find all orders for this customer
        customer_orders = [
            order for order in _MOCK_ORDERS.values()
            if order.get("customer_id") == customer_id
        ]
        
        if customer_orders:
            return {
                "status": "success",
                "orders": customer_orders,
                "count": len(customer_orders)
            }
        else:
            return {
                "status": "error",
                "error_message": f"No orders found for customer {customer_id}"
            }
    
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error looking up customer orders: {str(e)}"
        }

