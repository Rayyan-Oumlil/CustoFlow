"""
Order Modification Tools for Customer Support Agents

This module provides tools that allow agents to modify orders on behalf of customers.
These tools enable agents to perform actions like:
- Updating order status
- Cancelling orders
- Updating delivery addresses
- Modifying order items (with restrictions)

IMPORTANT: These tools should only be used when the customer explicitly requests
a modification. Always confirm the action with the customer before proceeding.
"""
from typing import Dict, Optional
from datetime import datetime
import sys
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.validation import validate_order_id, validate_customer_id


def update_order_status(order_id: str, new_status: str, reason: Optional[str] = None) -> Dict[str, any]:
    """
    Update the status of an order.
    
    This tool allows agents to change order status (e.g., cancel, mark as shipped, etc.)
    when requested by the customer.
    
    Args:
        order_id: The order ID to update
        new_status: New status (must be one of: processing, shipped, delivering, delivery_soon, delivered, cancelled)
        reason: Optional reason for the status change (for logging/audit)
        
    Returns:
        Dictionary with status and order information:
        - Success: {"status": "success", "message": "...", "order": {...}}
        - Error: {"status": "error", "error_message": "..."}
    """
    try:
        # Validate order ID
        is_valid, error_msg = validate_order_id(order_id)
        if not is_valid:
            return {
                "status": "error",
                "error_message": error_msg or "Invalid order ID format"
            }
        
        # Validate status
        valid_statuses = ["processing", "shipped", "delivering", "delivery_soon", "delivered", "cancelled"]
        if new_status.lower() not in valid_statuses:
            return {
                "status": "error",
                "error_message": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            }
        
        # Get existing order
        from tools.order_tool import lookup_order
        existing_order_result = lookup_order(order_id)
        
        if existing_order_result.get("status") == "error":
            return {
                "status": "error",
                "error_message": f"Order {order_id} not found"
            }
        
        existing_order = existing_order_result.get("order", {})
        current_status = existing_order.get("status", "").lower()
        
        # Check if status change is valid
        # Can't change delivered or cancelled orders
        if current_status in ["delivered", "cancelled"]:
            return {
                "status": "error",
                "error_message": f"Cannot modify a {current_status} order. Please contact support for assistance."
            }
        
        # Update order status
        from tools.order_tool import add_order
        updated_order = existing_order.copy()
        updated_order["status"] = new_status.lower()
        updated_order["updated_at"] = datetime.now().isoformat()
        
        # Add reason to metadata if provided
        if reason:
            if "metadata" not in updated_order:
                updated_order["metadata"] = {}
            if "status_changes" not in updated_order["metadata"]:
                updated_order["metadata"]["status_changes"] = []
            updated_order["metadata"]["status_changes"].append({
                "from": current_status,
                "to": new_status.lower(),
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            })
        
        # Save updated order
        success = add_order(updated_order)
        
        if not success:
            return {
                "status": "error",
                "error_message": "Failed to update order status"
            }
        
        # Generate user-friendly message
        status_messages = {
            "cancelled": f"Order {order_id} has been cancelled successfully.",
            "shipped": f"Order {order_id} has been marked as shipped.",
            "delivering": f"Order {order_id} is now marked as delivering.",
            "delivery_soon": f"Order {order_id} is marked as delivery soon.",
            "delivered": f"Order {order_id} has been marked as delivered.",
            "processing": f"Order {order_id} status has been updated to processing."
        }
        
        message = status_messages.get(new_status.lower(), f"Order {order_id} status updated to {new_status}.")
        
        return {
            "status": "success",
            "message": message,
            "order": updated_order,
            "previous_status": current_status,
            "new_status": new_status.lower()
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error updating order status: {str(e)}"
        }


def cancel_order(order_id: str, reason: Optional[str] = None) -> Dict[str, any]:
    """
    Cancel an order.
    
    This tool allows agents to cancel orders when requested by the customer.
    IMPORTANT: Only orders in "processing" status can be cancelled.
    Orders that are already shipped, delivering, or delivered cannot be cancelled.
    
    Args:
        order_id: The order ID to cancel
        reason: Optional reason for cancellation
        
    Returns:
        Dictionary with status and order information
    """
    try:
        # Validate order ID
        is_valid, error_msg = validate_order_id(order_id)
        if not is_valid:
            return {
                "status": "error",
                "error_message": error_msg or "Invalid order ID format"
            }
        
        # Get existing order
        from tools.order_tool import lookup_order
        existing_order_result = lookup_order(order_id)
        
        if existing_order_result.get("status") == "error":
            return {
                "status": "error",
                "error_message": f"Order {order_id} not found"
            }
        
        existing_order = existing_order_result.get("order", {})
        current_status = existing_order.get("status", "").lower()
        
        # Check if order can be cancelled
        # ONLY orders in "processing" status can be cancelled
        if current_status != "processing":
            if current_status == "cancelled":
                return {
                    "status": "error",
                    "error_message": f"Order {order_id} is already cancelled."
                }
            elif current_status == "delivered":
                return {
                    "status": "error",
                    "error_message": "Cannot cancel a delivered order. If you need to return it, please use our return process."
                }
            else:
                return {
                    "status": "error",
                    "error_message": f"Order {order_id} cannot be cancelled because it's already {current_status}. Only orders in 'processing' status can be cancelled."
                }
        
        # Cancel the order
        return update_order_status(
            order_id=order_id,
            new_status="cancelled",
            reason=reason or "Cancelled by customer request via agent"
        )
    
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error cancelling order: {str(e)}"
        }


def update_order_delivery_date(order_id: str, new_delivery_date: str) -> Dict[str, any]:
    """
    Update the estimated delivery date of an order.
    
    This tool allows agents to update delivery dates when requested by the customer
    or when there are shipping delays.
    
    Args:
        order_id: The order ID to update
        new_delivery_date: New estimated delivery date (YYYY-MM-DD format)
        
    Returns:
        Dictionary with status and order information
    """
    try:
        # Validate order ID
        is_valid, error_msg = validate_order_id(order_id)
        if not is_valid:
            return {
                "status": "error",
                "error_message": error_msg or "Invalid order ID format"
            }
        
        # Validate date format
        try:
            datetime.strptime(new_delivery_date, "%Y-%m-%d")
        except ValueError:
            return {
                "status": "error",
                "error_message": "Invalid date format. Please use YYYY-MM-DD format (e.g., 2025-12-25)"
            }
        
        # Get existing order
        from tools.order_tool import lookup_order
        existing_order_result = lookup_order(order_id)
        
        if existing_order_result.get("status") == "error":
            return {
                "status": "error",
                "error_message": f"Order {order_id} not found"
            }
        
        existing_order = existing_order_result.get("order", {})
        current_status = existing_order.get("status", "").lower()
        
        # Can't update delivery date for delivered or cancelled orders
        if current_status in ["delivered", "cancelled"]:
            return {
                "status": "error",
                "error_message": f"Cannot update delivery date for {current_status} orders."
            }
        
        # Update order
        from tools.order_tool import add_order
        updated_order = existing_order.copy()
        updated_order["estimated_delivery"] = new_delivery_date
        updated_order["updated_at"] = datetime.now().isoformat()
        
        # Auto-adjust status based on new delivery date
        from datetime import date
        try:
            delivery_date = datetime.strptime(new_delivery_date, "%Y-%m-%d").date()
            today = date.today()
            
            # Only auto-update if status is not "delivered" or "cancelled"
            if current_status not in ["delivered", "cancelled"]:
                if delivery_date < today:
                    updated_order["status"] = "delivery_soon"
                elif delivery_date >= today and current_status not in ["shipped", "delivering"]:
                    updated_order["status"] = "delivering"
        except Exception as e:
            # If date parsing fails, continue without auto-status update
            pass
        
        # Save updated order
        success = add_order(updated_order)
        
        if not success:
            return {
                "status": "error",
                "error_message": "Failed to update delivery date"
            }
        
        return {
            "status": "success",
            "message": f"Estimated delivery date for order {order_id} has been updated to {new_delivery_date}.",
            "order": updated_order,
            "new_delivery_date": new_delivery_date
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error updating delivery date: {str(e)}"
        }


def add_order_note(order_id: str, note: str, note_type: str = "general") -> Dict[str, any]:
    """
    Add a note to an order.
    
    This tool allows agents to add notes to orders for tracking purposes.
    Notes can be internal (for support team) or customer-facing.
    
    Args:
        order_id: The order ID to add a note to
        note: The note text to add
        note_type: Type of note (general, customer_request, internal, refund_request, etc.)
        
    Returns:
        Dictionary with status and order information
    """
    try:
        # Validate order ID
        is_valid, error_msg = validate_order_id(order_id)
        if not is_valid:
            return {
                "status": "error",
                "error_message": error_msg or "Invalid order ID format"
            }
        
        if not note or not note.strip():
            return {
                "status": "error",
                "error_message": "Note cannot be empty"
            }
        
        # Get existing order
        from tools.order_tool import lookup_order
        existing_order_result = lookup_order(order_id)
        
        if existing_order_result.get("status") == "error":
            return {
                "status": "error",
                "error_message": f"Order {order_id} not found"
            }
        
        existing_order = existing_order_result.get("order", {})
        
        # Update order with note
        from tools.order_tool import add_order
        updated_order = existing_order.copy()
        
        # Initialize notes array if it doesn't exist
        if "notes" not in updated_order:
            updated_order["notes"] = []
        
        # Add note
        note_entry = {
            "note": note.strip(),
            "note_type": note_type.lower(),
            "timestamp": datetime.now().isoformat(),
            "added_by": "agent"
        }
        updated_order["notes"].append(note_entry)
        updated_order["updated_at"] = datetime.now().isoformat()
        
        # Save updated order
        success = add_order(updated_order)
        
        if not success:
            return {
                "status": "error",
                "error_message": "Failed to add note to order"
            }
        
        return {
            "status": "success",
            "message": f"Note added to order {order_id} successfully.",
            "order_id": order_id,
            "note": note.strip(),
            "note_type": note_type.lower()
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error adding note: {str(e)}"
        }


def request_refund(order_id: str, reason: str, amount: Optional[float] = None) -> Dict[str, any]:
    """
    Request a refund for an order.
    
    This tool allows agents to create refund requests for customers.
    The refund request is added as a note and can be processed by the finance team.
    
    Args:
        order_id: The order ID to request refund for
        reason: Reason for the refund request
        amount: Optional refund amount (if partial refund). If not provided, full order amount is assumed.
        
    Returns:
        Dictionary with status and refund request information
    """
    try:
        # Validate order ID
        is_valid, error_msg = validate_order_id(order_id)
        if not is_valid:
            return {
                "status": "error",
                "error_message": error_msg or "Invalid order ID format"
            }
        
        if not reason or not reason.strip():
            return {
                "status": "error",
                "error_message": "Refund reason is required"
            }
        
        # Get existing order
        from tools.order_tool import lookup_order
        existing_order_result = lookup_order(order_id)
        
        if existing_order_result.get("status") == "error":
            return {
                "status": "error",
                "error_message": f"Order {order_id} not found"
            }
        
        existing_order = existing_order_result.get("order", {})
        current_status = existing_order.get("status", "").lower()
        order_total = existing_order.get("total", 0)
        
        # Check if refund is possible
        if current_status == "cancelled":
            return {
                "status": "error",
                "error_message": f"Order {order_id} is already cancelled. Refund may have already been processed."
            }
        
        # Determine refund amount
        refund_amount = amount if amount is not None else order_total
        
        # Add refund request note
        refund_note = f"REFUND REQUEST: {reason.strip()}. Amount: ${refund_amount:.2f}. Status: Pending approval."
        
        # Add note to order
        note_result = add_order_note(
            order_id=order_id,
            note=refund_note,
            note_type="refund_request"
        )
        
        if note_result.get("status") == "error":
            return note_result
        
        # Try to create a refund record in Supabase if available
        try:
            from utils.supabase_client import SUPABASE_ENABLED
            if SUPABASE_ENABLED:
                from supabase import create_client
                import os
                from dotenv import load_dotenv
                import uuid
                load_dotenv()
                supabase_url = os.getenv("SUPABASE_URL")
                supabase_key = os.getenv("SUPABASE_KEY")
                if supabase_url and supabase_key:
                    supabase = create_client(supabase_url, supabase_key)
                    refund_id = f"REFUND-{uuid.uuid4().hex[:8].upper()}"
                    
                    refund_data = {
                        "refund_id": refund_id,
                        "order_id": order_id,
                        "customer_id": existing_order.get("customer_id"),
                        "amount": refund_amount,
                        "reason": reason.strip(),
                        "status": "pending",
                        "requested_at": datetime.now().isoformat(),
                        "created_at": datetime.now().isoformat()
                    }
                    
                    # Try to insert into refunds table (if it exists)
                    try:
                        supabase.table("refunds").insert(refund_data).execute()
                    except Exception:
                        # Table might not exist, that's okay - we have the note
                        pass
        except Exception:
            pass  # Continue even if Supabase insert fails
        
        return {
            "status": "success",
            "message": f"Refund request created for order {order_id} in the amount of ${refund_amount:.2f}. The request will be reviewed and processed within 5-7 business days.",
            "order_id": order_id,
            "refund_amount": refund_amount,
            "reason": reason.strip(),
            "refund_status": "pending"
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error requesting refund: {str(e)}"
        }

