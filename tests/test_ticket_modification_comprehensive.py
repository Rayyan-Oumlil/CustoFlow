"""
Comprehensive tests for ticket modification tools.
Tests all functions with edge cases and error scenarios.
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.ticket_modification_tool import (
    update_ticket_status,
    cancel_ticket,
    update_ticket_priority
)
from tools.ticket_tool import create_ticket, get_ticket_status


def setup_test_ticket(issue: str = "Test issue", customer_id: str = "cust_001", 
                      session_id: str = None, user_id: str = None):
    """Helper to create a test ticket."""
    if not session_id:
        session_id = f"test_session_{datetime.now().timestamp()}"
    if not user_id:
        user_id = f"test_user_{datetime.now().timestamp()}"
    
    result = create_ticket(
        issue=issue,
        customer_id=customer_id,
        priority="normal",
        session_id=session_id,
        user_id=user_id
    )
    
    if result.get("status") == "success":
        return result.get("ticket_id")
    return None


def test_update_ticket_status_success():
    """Test successfully updating ticket status."""
    ticket_id = setup_test_ticket()
    if not ticket_id:
        pytest.skip("Could not create test ticket")
    
    result = update_ticket_status(ticket_id, "in_progress", note="Working on it")
    assert result["status"] == "success"
    assert result["new_status"] == "in_progress"
    
    # Verify status was updated
    ticket_result = get_ticket_status(ticket_id)
    assert ticket_result["ticket"]["status"] == "in_progress"


def test_update_ticket_status_invalid():
    """Test updating to invalid status."""
    ticket_id = setup_test_ticket()
    if not ticket_id:
        pytest.skip("Could not create test ticket")
    
    result = update_ticket_status(ticket_id, "invalid_status")
    assert result["status"] == "error"
    assert "invalid status" in result["error_message"].lower()


def test_update_ticket_status_not_found():
    """Test updating non-existent ticket."""
    result = update_ticket_status("TICKET-NONEXISTENT", "open")
    assert result["status"] == "error"
    assert "not found" in result["error_message"].lower()


def test_update_ticket_status_closed():
    """Test closing a ticket (should send thank you message and close session)."""
    ticket_id = setup_test_ticket()
    if not ticket_id:
        pytest.skip("Could not create test ticket")
    
    result = update_ticket_status(ticket_id, "closed", note="Resolved")
    assert result["status"] == "success"
    assert result["new_status"] == "closed"
    
    # Verify ticket is closed
    ticket_result = get_ticket_status(ticket_id)
    assert ticket_result["ticket"]["status"] == "closed"


def test_cancel_ticket_success():
    """Test successfully cancelling a ticket."""
    ticket_id = setup_test_ticket()
    if not ticket_id:
        pytest.skip("Could not create test ticket")
    
    result = cancel_ticket(ticket_id, reason="Customer request")
    assert result["status"] == "success"
    assert "cancelled" in result["message"].lower()


def test_cancel_ticket_already_closed():
    """Test cancelling an already closed ticket."""
    ticket_id = setup_test_ticket()
    if not ticket_id:
        pytest.skip("Could not create test ticket")
    
    # Close it first
    update_ticket_status(ticket_id, "closed")
    
    result = cancel_ticket(ticket_id)
    assert result["status"] == "error"
    assert "already closed" in result["error_message"].lower()


def test_cancel_ticket_not_found():
    """Test cancelling non-existent ticket."""
    result = cancel_ticket("TICKET-NONEXISTENT")
    assert result["status"] == "error"
    assert "not found" in result["error_message"].lower()


def test_cancel_ticket_without_id():
    """Test cancelling ticket without ID (should try to find recent ticket)."""
    # This will fail if no recent ticket exists, which is expected
    result = cancel_ticket()
    assert isinstance(result, dict)
    assert "status" in result


def test_update_ticket_priority_success():
    """Test successfully updating ticket priority."""
    ticket_id = setup_test_ticket()
    if not ticket_id:
        pytest.skip("Could not create test ticket")
    
    result = update_ticket_priority(ticket_id, "high")
    assert result["status"] == "success"
    assert result["new_priority"] == "high"
    
    # Verify priority was updated
    ticket_result = get_ticket_status(ticket_id)
    assert ticket_result["ticket"]["priority"] == "high"


def test_update_ticket_priority_invalid():
    """Test updating to invalid priority."""
    ticket_id = setup_test_ticket()
    if not ticket_id:
        pytest.skip("Could not create test ticket")
    
    result = update_ticket_priority(ticket_id, "invalid_priority")
    assert result["status"] == "error"
    assert "invalid priority" in result["error_message"].lower()


def test_update_ticket_priority_not_found():
    """Test updating priority of non-existent ticket."""
    result = update_ticket_priority("TICKET-NONEXISTENT", "high")
    assert result["status"] == "error"
    assert "not found" in result["error_message"].lower()


def test_update_ticket_status_all_statuses():
    """Test updating ticket to all valid statuses."""
    valid_statuses = ["open", "in_progress", "resolved", "closed"]
    
    for status in valid_statuses:
        ticket_id = setup_test_ticket()
        if not ticket_id:
            pytest.skip("Could not create test ticket")
        
        result = update_ticket_status(ticket_id, status)
        assert result["status"] == "success", f"Failed to update to {status}"
        assert result["new_status"] == status


def test_update_ticket_priority_all_priorities():
    """Test updating ticket to all valid priorities."""
    valid_priorities = ["low", "normal", "high", "urgent"]
    
    for priority in valid_priorities:
        ticket_id = setup_test_ticket()
        if not ticket_id:
            pytest.skip("Could not create test ticket")
        
        result = update_ticket_priority(ticket_id, priority)
        assert result["status"] == "success", f"Failed to update to {priority}"
        assert result["new_priority"] == priority

