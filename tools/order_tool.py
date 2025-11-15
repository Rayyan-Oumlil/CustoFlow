"""Order lookup tool for customer support."""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import random


# Mock order database (in production, this would query a real database)
_MOCK_ORDERS = {
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


def lookup_order(order_id: str) -> Dict[str, any]:
    """
    Look up order information by order ID.
    
    This tool searches the order database to retrieve order details including
    status, items, shipping information, and tracking numbers.
    
    Args:
        order_id: The order ID to look up (e.g., "12345")
        
    Returns:
        Dictionary with status and order information:
        - Success: {"status": "success", "order": {...}}
        - Error: {"status": "error", "error_message": "..."}
    """
    try:
        order_id = str(order_id).strip()
        
        if not order_id:
            return {
                "status": "error",
                "error_message": "Order ID cannot be empty"
            }
        
        # Look up order in mock database
        order = _MOCK_ORDERS.get(order_id)
        
        if order:
            return {
                "status": "success",
                "order": order
            }
        else:
            # Provide helpful guidance even when order not found
            return {
                "status": "error",
                "error_message": f"Order {order_id} not found. Please check the order ID and try again.",
                "helpful_info": "Order IDs are typically 5-10 digits. You can find your order number in your confirmation email or account dashboard. If you're having trouble, please contact support with your email address or customer ID."
            }
    
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

