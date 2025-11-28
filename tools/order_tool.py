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
import threading

# Add utils to path for cache import
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.cache import order_cache, generate_cache_key
from utils.validation import validate_order_id, validate_customer_id

# Global context storage for order operations (session_id, user_id, customer_id)
# Key: session_id, Value: dict with session_id, user_id, and customer_id
_order_contexts = {}
_order_context_lock = threading.Lock()


def set_order_context(session_id: Optional[str] = None, user_id: Optional[str] = None, customer_id: Optional[str] = None):
    """Set context for order operations (session_id, user_id, customer_id)."""
    if not session_id:
        return
    key = session_id
    with _order_context_lock:
        # If context already exists, update it (don't overwrite existing customer_id unless new one is provided)
        if key in _order_contexts and customer_id is None:
            existing_customer_id = _order_contexts[key].get("customer_id")
            customer_id = existing_customer_id
        _order_contexts[key] = {
            "session_id": session_id,
            "user_id": user_id,
            "customer_id": customer_id
        }


def update_customer_id(session_id: str, customer_id: str):
    """Update customer_id for a session (called when user provides their customer_id)."""
    if not session_id:
        return
    key = session_id
    with _order_context_lock:
        if key in _order_contexts:
            _order_contexts[key]["customer_id"] = customer_id
        else:
            # Create context if it doesn't exist
            _order_contexts[key] = {
                "session_id": session_id,
                "user_id": None,
                "customer_id": customer_id
            }


def get_order_context(session_id: Optional[str] = None) -> Dict:
    """Get context for order operations."""
    if not session_id:
        return {}
    key = session_id
    with _order_context_lock:
        return _order_contexts.get(key, {})


def clear_order_context(session_id: Optional[str] = None):
    """Clear context for order operations."""
    if not session_id:
        return
    key = session_id
    with _order_context_lock:
        if key in _order_contexts:
            del _order_contexts[key]


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
        
        # Try Supabase first
        try:
            from utils.supabase_client import SUPABASE_ENABLED
            if SUPABASE_ENABLED:
                from supabase import create_client
                import os
                from dotenv import load_dotenv
                load_dotenv()
                supabase_url = os.getenv("SUPABASE_URL")
                supabase_key = os.getenv("SUPABASE_KEY")
                if supabase_url and supabase_key:
                    supabase = create_client(supabase_url, supabase_key)
                    # Prepare order data for Supabase
                    # Note: Supabase table has 'created_at' but not 'order_date'
                    # Use 'order_date' from order_data if available, otherwise use 'created_at'
                    order_date_value = order_data.get("order_date") or order_data.get("created_at")
                    created_at_value = order_data.get("created_at") or order_data.get("order_date") or datetime.now().isoformat()
                    
                    supabase_order = {
                        "order_id": order_data.get("order_id"),
                        "customer_id": order_data.get("customer_id"),
                        "status": order_data.get("status"),
                        "items": order_data.get("items", []),
                        "total": order_data.get("total", 0),
                        "notes": order_data.get("notes", []),  # Include notes field
                        "tracking_number": order_data.get("tracking_number"),
                        "estimated_delivery": order_data.get("estimated_delivery"),
                        "created_at": created_at_value,
                        "updated_at": datetime.now().isoformat(),
                    }
                    
                    # Only include shipped_at if it exists in the schema (it might not)
                    # Check if shipped_at exists, otherwise skip it
                    if order_data.get("shipped_at") or order_data.get("shipped_date"):
                        # Note: shipped_at might not be in the schema, so we'll skip it for now
                        # If you need shipped_at, add it to the schema first
                        pass
                    # Insert or update in Supabase
                    supabase.table("orders").upsert(supabase_order).execute()
                    # Return True if Supabase is enabled (don't need to save to JSON)
                    return True
        except Exception as e:
            print(f"Warning: Could not save order to Supabase: {e}. Falling back to JSON.")
        
        # Fallback to JSON only if Supabase is not available
        global _MOCK_ORDERS
        _MOCK_ORDERS[order_id] = order_data
        
        # Save to file
        return _save_orders(_MOCK_ORDERS)
    except Exception as e:
        print(f"Error adding order: {e}")
        return False


def delete_order(order_id: str) -> bool:
    """
    Delete an order from the database and save to file.
    
    Args:
        order_id: Order ID to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Try Supabase first
        try:
            from utils.supabase_client import SUPABASE_ENABLED
            if SUPABASE_ENABLED:
                from supabase import create_client
                import os
                from dotenv import load_dotenv
                load_dotenv()
                supabase_url = os.getenv("SUPABASE_URL")
                supabase_key = os.getenv("SUPABASE_KEY")
                if supabase_url and supabase_key:
                    supabase = create_client(supabase_url, supabase_key)
                    # Delete from Supabase (always try, even if order doesn't exist)
                    try:
                        supabase.table("orders").delete().eq("order_id", order_id).execute()
                    except Exception as delete_error:
                        # If order doesn't exist in Supabase, that's okay, continue
                        print(f"Note: Order {order_id} may not exist in Supabase: {delete_error}")
                    
                    # Return True if Supabase is enabled (don't need to update JSON)
                    return True
        except Exception as e:
            print(f"Warning: Could not delete order from Supabase: {e}. Falling back to JSON.")
        
        # Fallback to JSON
        global _MOCK_ORDERS
        _MOCK_ORDERS = _load_orders()
        
        if order_id not in _MOCK_ORDERS:
            return False
        
        # Remove order from in-memory dict
        del _MOCK_ORDERS[order_id]
        
        # Save to file
        return _save_orders(_MOCK_ORDERS)
    except Exception as e:
        print(f"Error deleting order: {e}")
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
        
        # Try Supabase first
        try:
            from utils.supabase_client import SUPABASE_ENABLED
            if SUPABASE_ENABLED:
                from supabase import create_client
                import os
                from dotenv import load_dotenv
                load_dotenv()
                supabase_url = os.getenv("SUPABASE_URL")
                supabase_key = os.getenv("SUPABASE_KEY")
                if supabase_url and supabase_key:
                    supabase = create_client(supabase_url, supabase_key)
                    # Look up order in Supabase
                    result = supabase.table("orders").select("*").eq("order_id", order_id).execute()
                    if result.data and len(result.data) > 0:
                        order = result.data[0]
                        response = {
                            "status": "success",
                            "order": order
                        }
                        # Cache successful result
                        order_cache.set(cache_key, response)
                        return response
                    else:
                        # Order not found in Supabase
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
            print(f"Warning: Could not lookup order from Supabase: {e}. Falling back to JSON.")
        
        # Fallback to JSON
        global _MOCK_ORDERS
        _MOCK_ORDERS = _load_orders()
        
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


def get_customer_orders(customer_id: Optional[str] = None, session_id: Optional[str] = None) -> Dict[str, any]:
    """
    Get all orders for a customer.
    
    Args:
        customer_id: The customer ID to look up (optional, will try to get from context if not provided)
        session_id: Optional session ID to get customer_id from context (will try to find from context if not provided)
        
    Returns:
        Dictionary with status and list of orders
    """
    try:
        # If session_id not provided, try to get it from any available context
        if not session_id:
            # Try to get session_id from the most recent context entry
            with _order_context_lock:
                if _order_contexts:
                    # Get the most recent context (last entry in dict)
                    latest_context = list(_order_contexts.values())[-1] if _order_contexts else {}
                    session_id = latest_context.get("session_id")
        
        # If customer_id not provided, try to get it from context
        if not customer_id and session_id:
            ctx = get_order_context(session_id)
            customer_id = ctx.get("customer_id")
        
        # If still no customer_id, try to get from session in Supabase
        if not customer_id and session_id:
            try:
                from utils.supabase_client import SUPABASE_ENABLED
                if SUPABASE_ENABLED:
                    from supabase import create_client
                    import os
                    from dotenv import load_dotenv
                    load_dotenv()
                    supabase_url = os.getenv("SUPABASE_URL")
                    supabase_key = os.getenv("SUPABASE_KEY")
                    if supabase_url and supabase_key:
                        supabase = create_client(supabase_url, supabase_key)
                        # Get session to retrieve customer_id
                        session_result = supabase.table("sessions").select("customer_id").eq("session_id", session_id).limit(1).execute()
                        if session_result.data and len(session_result.data) > 0:
                            customer_id = session_result.data[0].get("customer_id")
                            if customer_id:
                                print(f"[ORDER] Retrieved customer_id from session: {customer_id}")
                                # Update context with found customer_id
                                update_customer_id(session_id, customer_id)
            except Exception as e:
                print(f"[ORDER] Could not get customer_id from session: {e}")
        
        # If still no customer_id, try to extract from user_id (use user_id as customer_id)
        if not customer_id and session_id:
            ctx = get_order_context(session_id)
            user_id = ctx.get("user_id")
            if user_id:
                customer_id = user_id  # Use user_id as customer_id by default
        
        if not customer_id:
            return {
                "status": "error",
                "error_message": "Customer ID is required. Please provide your customer ID or ask about a specific order.",
                "helpful_info": "I need your customer ID to look up your orders. You can also ask about a specific order by providing the order ID."
            }
        
        customer_id = str(customer_id).strip()
        
        # Validate customer ID format (you can customize this in utils/validation.py)
        is_valid, error_msg = validate_customer_id(customer_id)
        if not is_valid:
            return {
                "status": "error",
                "error_message": error_msg or "Invalid customer ID format",
                "helpful_info": "Customer IDs should be alphanumeric with underscores or hyphens (e.g., cust_001, CUST-123). You can customize the validation pattern in utils/validation.py"
            }
        
        # Try Supabase first
        try:
            from utils.supabase_client import SUPABASE_ENABLED
            if SUPABASE_ENABLED:
                from supabase import create_client
                import os
                from dotenv import load_dotenv
                load_dotenv()
                supabase_url = os.getenv("SUPABASE_URL")
                supabase_key = os.getenv("SUPABASE_KEY")
                if supabase_url and supabase_key:
                    supabase = create_client(supabase_url, supabase_key)
                    # Get orders from Supabase
                    result = supabase.table("orders").select("*").eq("customer_id", customer_id).order("created_at", desc=True).execute()
                    all_orders = result.data or []
                    
                    # Filter out test orders (orders with order_id starting with "TEST_")
                    # Prioritize real orders (numeric IDs or meaningful names)
                    real_orders = [
                        order for order in all_orders
                        if not str(order.get("order_id", "")).startswith("TEST_")
                    ]
                    
                    # If we have real orders, use them; otherwise fall back to all orders
                    customer_orders = real_orders if real_orders else all_orders
                    
                    if customer_orders:
                        return {
                            "status": "success",
                            "orders": customer_orders,
                            "count": len(customer_orders),
                            "total_count": len(all_orders),  # Include total for reference
                            "filtered_test_orders": len(all_orders) - len(real_orders) if real_orders else 0
                        }
                    else:
                        return {
                            "status": "error",
                            "error_message": f"No orders found for customer {customer_id}"
                        }
        except Exception as e:
            print(f"Warning: Could not get customer orders from Supabase: {e}. Falling back to JSON.")
        
        # Fallback to JSON
        global _MOCK_ORDERS
        _MOCK_ORDERS = _load_orders()
        
        # Find all orders for this customer
        all_orders = [
            order for order in _MOCK_ORDERS.values()
            if order.get("customer_id") == customer_id
        ]
        
        # Filter out test orders (orders with order_id starting with "TEST_")
        # Prioritize real orders (numeric IDs or meaningful names)
        real_orders = [
            order for order in all_orders
            if not str(order.get("order_id", "")).startswith("TEST_")
        ]
        
        # If we have real orders, use them; otherwise fall back to all orders
        customer_orders = real_orders if real_orders else all_orders
        
        if customer_orders:
            return {
                "status": "success",
                "orders": customer_orders,
                "count": len(customer_orders),
                "total_count": len(all_orders),  # Include total for reference
                "filtered_test_orders": len(all_orders) - len(real_orders) if real_orders else 0
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

