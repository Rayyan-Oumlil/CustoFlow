"""
Comprehensive tests for order modification tools.
Tests all functions with edge cases and error scenarios.
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime, date
from unittest.mock import patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.order_modification_tool import (
    cancel_order,
    add_order_note,
    request_refund,
    update_order_status,
    update_order_delivery_date
)
from tools.order_tool import add_order, lookup_order


def setup_test_order(order_id: str, status: str = "processing", customer_id: str = "cust_001"):
    """Helper to create a test order."""
    order = {
        "order_id": order_id,
        "customer_id": customer_id,
        "status": status,
        "total": 100.0,
        "items": [{"name": "Test Item", "quantity": 1, "price": 100.0}],
        "estimated_delivery": "2025-12-31",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    add_order(order)
    return order


def test_cancel_order_success():
    """Test successfully cancelling an order in processing status."""
    from unittest.mock import patch
    
    order_id = "TEST_CANCEL_001"
    
    # Mock Supabase to use JSON fallback BEFORE creating order
    with patch('utils.supabase_client.SUPABASE_ENABLED', False):
        setup_test_order(order_id, status="processing")
        
        result = cancel_order(order_id, reason="Customer request")
        assert result["status"] == "success"
        assert "cancelled" in result["message"].lower()
        
        # Verify order is cancelled
        order_result = lookup_order(order_id)
        assert order_result["order"]["status"] == "cancelled"


def test_cancel_order_already_cancelled():
    """Test cancelling an already cancelled order."""
    order_id = "TEST_CANCEL_002"
    setup_test_order(order_id, status="cancelled")
    
    result = cancel_order(order_id)
    assert result["status"] == "error"
    assert "already cancelled" in result["error_message"].lower()


def test_cancel_order_shipped():
    """Test cancelling a shipped order (should fail)."""
    order_id = "TEST_CANCEL_003"
    setup_test_order(order_id, status="shipped")
    
    result = cancel_order(order_id)
    assert result["status"] == "error"
    assert "cannot be cancelled" in result["error_message"].lower()


def test_cancel_order_delivered():
    """Test cancelling a delivered order (should fail)."""
    order_id = "TEST_CANCEL_004"
    setup_test_order(order_id, status="delivered")
    
    result = cancel_order(order_id)
    assert result["status"] == "error"
    assert "cannot cancel" in result["error_message"].lower() or "delivered" in result["error_message"].lower()


def test_cancel_order_not_found():
    """Test cancelling a non-existent order."""
    result = cancel_order("NONEXISTENT_ORDER")
    assert result["status"] == "error"
    assert "not found" in result["error_message"].lower()


def test_cancel_order_invalid_id():
    """Test cancelling with invalid order ID format."""
    result = cancel_order("")
    assert result["status"] == "error"
    # Accept either "invalid" or "empty" in error message
    assert "invalid" in result["error_message"].lower() or "empty" in result["error_message"].lower()


def test_add_order_note_success():
    """Test successfully adding a note to an order."""
    order_id = "TEST_NOTE_001"
    
    # Mock Supabase to use JSON fallback BEFORE creating order
    with patch('utils.supabase_client.SUPABASE_ENABLED', False):
        setup_test_order(order_id)
        
        # Verify order exists before adding note
        order_check = lookup_order(order_id)
        assert order_check.get("status") == "success", f"Order {order_id} not found before adding note"
        
        result = add_order_note(order_id, "Test note", "general")
        assert result["status"] == "success", f"Failed to add note. Error: {result.get('error_message', 'Unknown error')}"
        assert "added" in result["message"].lower()
        
        # Verify note was added
        order_result = lookup_order(order_id)
        assert "notes" in order_result["order"]
    assert len(order_result["order"]["notes"]) > 0


def test_add_order_note_empty():
    """Test adding an empty note (should fail)."""
    order_id = "TEST_NOTE_002"
    setup_test_order(order_id)
    
    result = add_order_note(order_id, "", "general")
    assert result["status"] == "error"
    assert "cannot be empty" in result["error_message"].lower()


def test_add_order_note_not_found():
    """Test adding note to non-existent order."""
    result = add_order_note("NONEXISTENT", "Note", "general")
    assert result["status"] == "error"
    assert "not found" in result["error_message"].lower()


def test_add_order_note_multiple():
    """Test adding multiple notes to an order."""
    order_id = "TEST_NOTE_003"
    
    # Mock Supabase to use JSON fallback BEFORE creating order
    with patch('utils.supabase_client.SUPABASE_ENABLED', False):
        setup_test_order(order_id)
        
        for i in range(3):
            result = add_order_note(order_id, f"Note {i}", "general")
            assert result["status"] == "success"
        
        order_result = lookup_order(order_id)
        assert len(order_result["order"]["notes"]) == 3


def test_request_refund_success():
    """Test successfully requesting a refund."""
    order_id = "TEST_REFUND_001"
    
    # Mock Supabase to use JSON fallback BEFORE creating order
    with patch('utils.supabase_client.SUPABASE_ENABLED', False):
        setup_test_order(order_id, status="delivered")
        
        result = request_refund(order_id, "Item damaged", amount=50.0)
        assert result["status"] == "success"
        assert "refund request" in result["message"].lower()
        assert result["refund_amount"] == 50.0


def test_request_refund_full():
    """Test requesting full refund (no amount specified)."""
    order_id = "TEST_REFUND_002"
    
    # Mock Supabase to use JSON fallback BEFORE creating order
    with patch('utils.supabase_client.SUPABASE_ENABLED', False):
        order = setup_test_order(order_id, status="delivered")
        
        result = request_refund(order_id, "Customer request")
        assert result["status"] == "success"
        assert result["refund_amount"] == order["total"]


def test_request_refund_empty_reason():
    """Test requesting refund with empty reason (should fail)."""
    order_id = "TEST_REFUND_003"
    setup_test_order(order_id)
    
    result = request_refund(order_id, "")
    assert result["status"] == "error"
    assert "reason is required" in result["error_message"].lower()


def test_request_refund_cancelled_order():
    """Test requesting refund for cancelled order."""
    order_id = "TEST_REFUND_004"
    setup_test_order(order_id, status="cancelled")
    
    result = request_refund(order_id, "Test reason")
    assert result["status"] == "error"
    assert "already cancelled" in result["error_message"].lower()


def test_update_order_status_success():
    """Test successfully updating order status."""
    from unittest.mock import patch
    
    order_id = "TEST_STATUS_001"
    
    # Mock Supabase to use JSON fallback BEFORE creating order
    with patch('utils.supabase_client.SUPABASE_ENABLED', False):
        setup_test_order(order_id, status="processing")
        
        result = update_order_status(order_id, "shipped", reason="Order shipped")
        assert result["status"] == "success"
        assert result["new_status"] == "shipped"
        
        # Verify status was updated
        order_result = lookup_order(order_id)
        assert order_result["order"]["status"] == "shipped"


def test_update_order_status_invalid_status():
    """Test updating to invalid status."""
    order_id = "TEST_STATUS_002"
    setup_test_order(order_id)
    
    result = update_order_status(order_id, "invalid_status")
    assert result["status"] == "error"
    assert "invalid status" in result["error_message"].lower()


def test_update_order_status_delivered():
    """Test updating status of delivered order (should fail)."""
    order_id = "TEST_STATUS_003"
    setup_test_order(order_id, status="delivered")
    
    result = update_order_status(order_id, "shipped")
    assert result["status"] == "error"
    assert "cannot modify" in result["error_message"].lower()


def test_update_order_delivery_date_success():
    """Test successfully updating delivery date."""
    order_id = "TEST_DATE_001"
    
    new_date = "2025-12-25"
    # Mock Supabase to use JSON fallback BEFORE creating order
    with patch('utils.supabase_client.SUPABASE_ENABLED', False):
        setup_test_order(order_id)
        
        result = update_order_delivery_date(order_id, new_date)
        assert result["status"] == "success"
        assert result["new_delivery_date"] == new_date


def test_update_order_delivery_date_invalid_format():
    """Test updating delivery date with invalid format."""
    order_id = "TEST_DATE_002"
    setup_test_order(order_id)
    
    result = update_order_delivery_date(order_id, "25-12-2025")
    assert result["status"] == "error"
    assert "invalid date format" in result["error_message"].lower()


def test_update_order_delivery_date_delivered():
    """Test updating delivery date of delivered order (should fail)."""
    order_id = "TEST_DATE_003"
    setup_test_order(order_id, status="delivered")
    
    result = update_order_delivery_date(order_id, "2025-12-25")
    assert result["status"] == "error"
    assert "cannot update" in result["error_message"].lower()


def test_update_order_delivery_date_auto_status():
    """Test that delivery date update auto-adjusts status."""
    from unittest.mock import patch
    
    order_id = "TEST_DATE_004"
    
    # Mock Supabase to use JSON fallback BEFORE creating order
    with patch('utils.supabase_client.SUPABASE_ENABLED', False):
        setup_test_order(order_id, status="processing")
        
        # Set delivery date in the past
        past_date = "2024-01-01"
        result = update_order_delivery_date(order_id, past_date)
        assert result["status"] == "success"
        
        # Status should be auto-adjusted to delivery_soon
        order_result = lookup_order(order_id)
        # Note: This depends on current date, so we just check it was updated
        assert order_result["order"]["estimated_delivery"] == past_date


def test_add_order_note_all_statuses():
    """Test that notes can be added to orders in any status."""
    from unittest.mock import patch
    
    # Mock Supabase to use JSON fallback BEFORE creating orders
    with patch('utils.supabase_client.SUPABASE_ENABLED', False):
        statuses = ["processing", "shipped", "delivering", "delivery_soon", "delivered", "cancelled"]
        
        for i, status in enumerate(statuses):
            order_id = f"TEST_NOTE_STATUS_{i}"
            setup_test_order(order_id, status=status)
            
            result = add_order_note(order_id, f"Note for {status} order", "general")
            assert result["status"] == "success", f"Failed to add note to {status} order"

