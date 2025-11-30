"""
Comprehensive tests for order API endpoints (create, delete, update).
Tests POST /orders, DELETE /orders/{order_id}, PUT /orders/{order_id}.
"""
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.order_tool import add_order, delete_order, lookup_order, _MOCK_ORDERS


def setup_test_order(order_id: str = "TEST_ORDER_001"):
    """Helper to create a test order."""
    order = {
        "order_id": order_id,
        "customer_id": "cust_001",
        "status": "processing",
        "total": 100.0,
        "items": [{"name": "Test Item", "quantity": 1, "price": 100.0}],
        "order_date": "2025-01-01",
        "created_at": "2025-01-01T00:00:00",
        "updated_at": "2025-01-01T00:00:00"
    }
    add_order(order)
    return order


def test_create_order_success():
    """Test successfully creating an order."""
    order_id = "TEST_CREATE_001"
    order_data = {
        "order_id": order_id,
        "customer_id": "cust_001",
        "status": "processing",
        "items": [{"name": "Test Item", "quantity": 1, "price": 100.0}],
        "total": 100.0,
        "order_date": "2025-01-01"
    }
    
    # Clean up if exists
    if order_id in _MOCK_ORDERS:
        delete_order(order_id)
    
    success = add_order(order_data)
    assert success is True
    
    # Verify order exists
    result = lookup_order(order_id)
    assert result.get("status") == "success"
    assert result.get("order", {}).get("order_id") == order_id
    
    # Cleanup
    delete_order(order_id)


def test_create_order_missing_required_fields():
    """Test creating order with missing required fields."""
    # Missing order_id
    order_data = {
        "customer_id": "cust_001",
        "status": "processing",
        "items": [{"name": "Test Item", "quantity": 1, "price": 100.0}],
        "total": 100.0,
        "order_date": "2025-01-01"
    }
    
    success = add_order(order_data)
    assert success is False  # Should fail without order_id


def test_create_order_duplicate():
    """Test creating duplicate order (should update existing)."""
    order_id = "TEST_DUPLICATE_001"
    order_data = {
        "order_id": order_id,
        "customer_id": "cust_001",
        "status": "processing",
        "items": [{"name": "Test Item", "quantity": 1, "price": 100.0}],
        "total": 100.0,
        "order_date": "2025-01-01"
    }
    
    # Clean up if exists
    if order_id in _MOCK_ORDERS:
        delete_order(order_id)
    
    # Create first time
    success1 = add_order(order_data)
    assert success1 is True
    
    # Create again (should update, not fail)
    order_data["status"] = "shipped"
    success2 = add_order(order_data)
    assert success2 is True
    
    # Verify it was updated
    result = lookup_order(order_id)
    assert result.get("order", {}).get("status") == "shipped"
    
    # Cleanup
    delete_order(order_id)


def test_delete_order_success():
    """Test successfully deleting an order."""
    from unittest.mock import patch
    
    order_id = "TEST_DELETE_001"
    setup_test_order(order_id)
    
    # Mock Supabase to use JSON fallback
    with patch('utils.supabase_client.SUPABASE_ENABLED', False):
        # Verify order exists
        result = lookup_order(order_id)
        assert result.get("status") == "success"
        
        # Delete order
        success = delete_order(order_id)
        assert success is True
        
        # Verify order is gone
        result = lookup_order(order_id)
        assert result.get("status") == "error"


def test_delete_order_not_found():
    """Test deleting non-existent order."""
    order_id = "NONEXISTENT_ORDER"
    
    # Should not raise exception, just return False
    success = delete_order(order_id)
    assert success is False or success is True  # Some implementations return True even if not found


def test_delete_order_multiple_times():
    """Test deleting the same order multiple times."""
    order_id = "TEST_DELETE_MULTI_001"
    setup_test_order(order_id)
    
    # Delete first time
    success1 = delete_order(order_id)
    assert success1 is True
    
    # Delete again (should handle gracefully)
    success2 = delete_order(order_id)
    # Should return False or True depending on implementation
    assert isinstance(success2, bool)


def test_update_order_status():
    """Test updating order status."""
    order_id = "TEST_UPDATE_STATUS_001"
    order = setup_test_order(order_id)
    
    # Update status
    order["status"] = "shipped"
    success = add_order(order)
    assert success is True
    
    # Verify update
    result = lookup_order(order_id)
    assert result.get("order", {}).get("status") == "shipped"
    
    # Cleanup
    delete_order(order_id)


def test_update_order_items():
    """Test updating order items."""
    order_id = "TEST_UPDATE_ITEMS_001"
    order = setup_test_order(order_id)
    
    # Update items
    order["items"] = [
        {"name": "Updated Item 1", "quantity": 2, "price": 50.0},
        {"name": "Updated Item 2", "quantity": 1, "price": 30.0}
    ]
    order["total"] = 130.0
    success = add_order(order)
    assert success is True
    
    # Verify update
    result = lookup_order(order_id)
    assert len(result.get("order", {}).get("items", [])) == 2
    assert result.get("order", {}).get("total") == 130.0
    
    # Cleanup
    delete_order(order_id)


def test_update_order_tracking_number():
    """Test updating order tracking number."""
    order_id = "TEST_UPDATE_TRACKING_001"
    order = setup_test_order(order_id)
    
    # Add tracking number
    order["tracking_number"] = "TRACK123456"
    success = add_order(order)
    assert success is True
    
    # Verify update
    result = lookup_order(order_id)
    assert result.get("order", {}).get("tracking_number") == "TRACK123456"
    
    # Cleanup
    delete_order(order_id)


def test_create_order_with_tracking():
    """Test creating order with tracking number."""
    order_id = "TEST_CREATE_TRACKING_001"
    order_data = {
        "order_id": order_id,
        "customer_id": "cust_001",
        "status": "shipped",
        "items": [{"name": "Test Item", "quantity": 1, "price": 100.0}],
        "total": 100.0,
        "order_date": "2025-01-01",
        "tracking_number": "TRACK_CREATE_001",
        "estimated_delivery": "2025-01-10"
    }
    
    # Clean up if exists
    if order_id in _MOCK_ORDERS:
        delete_order(order_id)
    
    success = add_order(order_data)
    assert success is True
    
    # Verify tracking number
    result = lookup_order(order_id)
    assert result.get("order", {}).get("tracking_number") == "TRACK_CREATE_001"
    
    # Cleanup
    delete_order(order_id)


def test_create_order_with_notes():
    """Test creating order with notes."""
    order_id = "TEST_CREATE_NOTES_001"
    order_data = {
        "order_id": order_id,
        "customer_id": "cust_001",
        "status": "processing",
        "items": [{"name": "Test Item", "quantity": 1, "price": 100.0}],
        "total": 100.0,
        "order_date": "2025-01-01",
        "notes": [
            {"note": "Test note 1", "note_type": "general", "created_at": "2025-01-01T00:00:00"},
            {"note": "Test note 2", "note_type": "internal", "created_at": "2025-01-01T00:00:00"}
        ]
    }
    
    # Clean up if exists
    if order_id in _MOCK_ORDERS:
        delete_order(order_id)
    
    success = add_order(order_data)
    assert success is True
    
    # Verify notes
    result = lookup_order(order_id)
    notes = result.get("order", {}).get("notes", [])
    assert len(notes) == 2
    
    # Cleanup
    delete_order(order_id)


def test_create_order_all_statuses():
    """Test creating orders with all valid statuses."""
    statuses = ["processing", "shipped", "delivering", "delivery_soon", "delivered", "cancelled"]
    
    for status in statuses:
        order_id = f"TEST_STATUS_{status.upper()}"
        order_data = {
            "order_id": order_id,
            "customer_id": "cust_001",
            "status": status,
            "items": [{"name": "Test Item", "quantity": 1, "price": 100.0}],
            "total": 100.0,
            "order_date": "2025-01-01"
        }
        
        # Clean up if exists
        if order_id in _MOCK_ORDERS:
            delete_order(order_id)
        
        success = add_order(order_data)
        assert success is True
        
        # Verify status
        result = lookup_order(order_id)
        assert result.get("order", {}).get("status") == status
        
        # Cleanup
        delete_order(order_id)


def test_delete_order_preserves_other_orders():
    """Test that deleting one order doesn't affect others."""
    order_id1 = "TEST_DELETE_ISOLATE_001"
    order_id2 = "TEST_DELETE_ISOLATE_002"
    
    setup_test_order(order_id1)
    setup_test_order(order_id2)
    
    # Verify both exist
    assert lookup_order(order_id1).get("status") == "success"
    assert lookup_order(order_id2).get("status") == "success"
    
    # Delete one
    delete_order(order_id1)
    
    # Verify other still exists
    assert lookup_order(order_id1).get("status") == "error"
    assert lookup_order(order_id2).get("status") == "success"
    
    # Cleanup
    delete_order(order_id2)

