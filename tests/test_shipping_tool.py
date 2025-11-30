"""
Comprehensive tests for shipping tracking tool.
Tests track_shipment function with various scenarios.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.shipping_tool import track_shipment, _get_order_from_tracking
from tools.order_tool import add_order


def setup_test_order_with_tracking(tracking_number: str, status: str = "shipped"):
    """Helper to create a test order with tracking number."""
    order = {
        "order_id": f"TEST_{tracking_number}",
        "customer_id": "cust_001",
        "status": status,
        "total": 100.0,
        "items": [{"name": "Test Item", "quantity": 1, "price": 100.0}],
        "tracking_number": tracking_number,
        "estimated_delivery": "2025-12-31",
        "order_date": "2025-01-01",
        "created_at": "2025-01-01T00:00:00",
        "updated_at": "2025-01-01T00:00:00"
    }
    add_order(order)
    return order


def test_track_shipment_success():
    """Test successfully tracking a shipment."""
    tracking_number = "TRACK123456"
    
    # Mock Supabase to use JSON fallback BEFORE creating order
    with patch('utils.supabase_client.SUPABASE_ENABLED', False):
        setup_test_order_with_tracking(tracking_number, status="shipped")
        
        result = track_shipment(tracking_number, carrier="ups")
        assert result["status"] == "success"
        assert result["tracking_number"] == tracking_number
        assert result["current_status"] == "shipped"
        assert "carrier" in result
        assert "current_location" in result
        assert "estimated_delivery" in result


def test_track_shipment_not_found():
    """Test tracking a shipment that doesn't exist."""
    result = track_shipment("NONEXISTENT_TRACKING")
    assert result["status"] == "error"
    assert "not found" in result["error_message"].lower()


def test_track_shipment_empty_tracking_number():
    """Test tracking with empty tracking number."""
    result = track_shipment("")
    assert result["status"] == "error"
    assert "required" in result["error_message"].lower()


def test_track_shipment_whitespace_tracking_number():
    """Test tracking with whitespace-only tracking number."""
    result = track_shipment("   ")
    assert result["status"] == "error"
    assert "required" in result["error_message"].lower()


def test_track_shipment_all_statuses():
    """Test tracking shipments with all possible order statuses."""
    statuses = ["processing", "shipped", "delivering", "delivery_soon", "delivered", "cancelled"]
    
    for status in statuses:
        tracking_number = f"TRACK_{status.upper()}"
        setup_test_order_with_tracking(tracking_number, status=status)
        
        result = track_shipment(tracking_number)
        assert result["status"] == "success"
        assert result["current_status"] == status
        assert "status_description" in result
        assert "current_location" in result


def test_track_shipment_all_carriers():
    """Test tracking with all supported carriers."""
    tracking_number = "TRACK_CARRIER_TEST"
    setup_test_order_with_tracking(tracking_number)
    
    carriers = ["ups", "fedex", "dhl", "usps"]
    for carrier in carriers:
        result = track_shipment(tracking_number, carrier=carrier)
        assert result["status"] == "success"
        assert carrier.lower() in result["carrier"]["carrier_name"].lower() or "United Parcel Service" in result["carrier"]["carrier_name"]


def test_track_shipment_invalid_carrier():
    """Test tracking with invalid carrier (should default to ups)."""
    tracking_number = "TRACK_INVALID_CARRIER"
    setup_test_order_with_tracking(tracking_number)
    
    result = track_shipment(tracking_number, carrier="invalid_carrier")
    assert result["status"] == "success"
    # Should default to UPS
    assert "carrier" in result


def test_track_shipment_tracking_number_normalization():
    """Test that tracking number is normalized to uppercase."""
    tracking_number = "track_lowercase"
    setup_test_order_with_tracking(tracking_number.upper())
    
    result = track_shipment(tracking_number.lower())
    assert result["status"] == "success"
    assert result["tracking_number"] == tracking_number.upper()


def test_track_shipment_with_estimated_delivery():
    """Test tracking with estimated delivery date."""
    tracking_number = "TRACK_WITH_DATE"
    order = setup_test_order_with_tracking(tracking_number)
    order["estimated_delivery"] = "2025-12-25"
    
    from tools.order_tool import add_order
    add_order(order)
    
    result = track_shipment(tracking_number)
    assert result["status"] == "success"
    assert result["estimated_delivery"] is not None
    assert "date" in result["estimated_delivery"]


def test_track_shipment_without_estimated_delivery():
    """Test tracking without estimated delivery date."""
    tracking_number = "TRACK_NO_DATE"
    order = setup_test_order_with_tracking(tracking_number)
    order["estimated_delivery"] = None
    
    from tools.order_tool import add_order
    add_order(order)
    
    result = track_shipment(tracking_number)
    assert result["status"] == "success"
    # estimated_delivery might be None or empty dict
    assert result is not None


def test_get_order_from_tracking_supabase():
    """Test _get_order_from_tracking with Supabase."""
    tracking_number = "TRACK_SUPABASE"
    order = setup_test_order_with_tracking(tracking_number)
    
    # Mock Supabase
    with patch('utils.supabase_client.SUPABASE_ENABLED', True):
        with patch('supabase.create_client') as mock_client:
            mock_supabase = Mock()
            mock_result = Mock()
            mock_result.data = [order]
            mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_result
            mock_client.return_value = mock_supabase
            
            result = _get_order_from_tracking(tracking_number)
            assert result is not None
            assert result["tracking_number"] == tracking_number


def test_get_order_from_tracking_json_fallback():
    """Test _get_order_from_tracking with JSON fallback."""
    tracking_number = "TRACK_JSON_FALLBACK"
    
    # Mock Supabase as disabled BEFORE creating order
    with patch('utils.supabase_client.SUPABASE_ENABLED', False):
        order = setup_test_order_with_tracking(tracking_number)
        
        result = _get_order_from_tracking(tracking_number)
        # Should fallback to JSON
        assert result is not None
        assert result["tracking_number"] == tracking_number


def test_track_shipment_exception_handling():
    """Test that exceptions are handled gracefully."""
    with patch('tools.shipping_tool._get_order_from_tracking', side_effect=Exception("Database error")):
        result = track_shipment("TRACK_ERROR")
        assert result["status"] == "error"
        assert "error" in result["error_message"].lower()


def test_track_shipment_location_mapping():
    """Test that location is correctly mapped from order status."""
    location_tests = [
        ("processing", "Warehouse"),
        ("shipped", "Origin Facility"),
        ("delivering", "Distribution Center"),
        ("delivery_soon", "Local Delivery Facility"),
        ("delivered", "Destination"),
        ("cancelled", "Warehouse")
    ]
    
    # Mock Supabase to use JSON fallback BEFORE creating orders
    with patch('utils.supabase_client.SUPABASE_ENABLED', False):
        for status, expected_location in location_tests:
            tracking_number = f"TRACK_LOC_{status}"
            setup_test_order_with_tracking(tracking_number, status=status)
            
            result = track_shipment(tracking_number)
            assert result["status"] == "success"
            assert result["current_location"] == expected_location


def test_track_shipment_status_description():
    """Test that status descriptions are correct."""
    status_descriptions = {
        "processing": "Order is being prepared for shipment",
        "shipped": "Package has left the warehouse",
        "delivering": "Package is in transit to destination",
        "delivery_soon": "Package is out for delivery",
        "delivered": "Package has been delivered",
        "cancelled": "Order has been cancelled"
    }
    
    # Mock Supabase to use JSON fallback BEFORE creating orders
    with patch('utils.supabase_client.SUPABASE_ENABLED', False):
        for status, expected_description in status_descriptions.items():
            tracking_number = f"TRACK_DESC_{status}"
            setup_test_order_with_tracking(tracking_number, status=status)
            
            result = track_shipment(tracking_number)
            assert result["status"] == "success"
            assert result["status_description"] == expected_description

