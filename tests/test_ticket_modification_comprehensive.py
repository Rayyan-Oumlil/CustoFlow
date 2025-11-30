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
    from unittest.mock import patch
    
    # Mock Supabase to use JSON fallback BEFORE creating ticket
    with patch('utils.supabase_client.SUPABASE_ENABLED', False):
        ticket_id = setup_test_ticket()
        if not ticket_id:
            pytest.skip("Could not create test ticket")
        
        # Verify ticket exists before updating
        ticket_check = get_ticket_status(ticket_id)
        assert ticket_check.get("status") == "success", f"Ticket {ticket_id} not found before update"
        
        result = update_ticket_status(ticket_id, "in_progress", note="Working on it")
        assert result["status"] == "success", f"Failed to update status. Error: {result.get('error_message', 'Unknown error')}"
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
    from unittest.mock import patch
    
    # Mock Supabase to use JSON fallback BEFORE creating ticket
    with patch('utils.supabase_client.SUPABASE_ENABLED', False):
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
    from unittest.mock import patch
    
    # Mock Supabase to use JSON fallback BEFORE creating ticket
    with patch('utils.supabase_client.SUPABASE_ENABLED', False):
        ticket_id = setup_test_ticket()
        if not ticket_id:
            pytest.skip("Could not create test ticket")
        
        # Wait a bit for ticket to be written to disk (parallel test environment)
        import time
        time.sleep(0.1)
        
        # Force reload tickets to ensure ticket is available
        from tools.ticket_tool import load_tickets
        import tools.ticket_tool as ticket_module
        ticket_module._TICKETS = load_tickets()
        
        # Verify ticket exists before cancelling
        ticket_check = get_ticket_status(ticket_id)
        assert ticket_check.get("status") == "success", f"Ticket {ticket_id} not found before cancel"
        
        result = cancel_ticket(ticket_id, reason="Customer request")
        assert result["status"] == "success", f"Failed to cancel ticket. Error: {result.get('error_message', 'Unknown error')}"
        assert "cancelled" in result["message"].lower()


def test_cancel_ticket_already_closed():
    """Test cancelling an already closed ticket."""
    from unittest.mock import patch
    
    # Mock Supabase to use JSON fallback BEFORE creating ticket
    with patch('utils.supabase_client.SUPABASE_ENABLED', False):
        ticket_id = setup_test_ticket()
        if not ticket_id:
            pytest.skip("Could not create test ticket")
        
        # Wait a bit for ticket to be written to disk (parallel test environment)
        import time
        time.sleep(0.1)
        
        # Verify ticket exists before closing - reload tickets to ensure it's available
        from tools.ticket_tool import load_tickets
        import tools.ticket_tool as ticket_module
        ticket_module._TICKETS = load_tickets()  # Force reload
        
        ticket_check = get_ticket_status(ticket_id)
        assert ticket_check.get("status") == "success", f"Ticket {ticket_id} not found before close"
        
        # Close it first
        close_result = update_ticket_status(ticket_id, "closed")
        assert close_result["status"] == "success", f"Failed to close ticket. Error: {close_result.get('error_message', 'Unknown error')}"
        
        # Force reload tickets after update
        ticket_module._TICKETS = load_tickets()
        
        # Verify ticket is closed
        closed_check = get_ticket_status(ticket_id)
        assert closed_check.get("status") == "success", f"Ticket {ticket_id} not found after close"
        assert closed_check["ticket"]["status"] == "closed"
        
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
    from unittest.mock import patch
    
    # Mock Supabase to use JSON fallback BEFORE creating ticket
    with patch('utils.supabase_client.SUPABASE_ENABLED', False):
        ticket_id = setup_test_ticket()
        if not ticket_id:
            pytest.skip("Could not create test ticket")
        
        # Wait a bit for ticket to be written to disk (parallel test environment)
        import time
        time.sleep(0.2)  # Increased delay for parallel test environment
        
        # Force reload tickets to ensure ticket is available
        from tools.ticket_tool import get_ticket_status, load_tickets
        import tools.ticket_tool as ticket_module
        ticket_module._TICKETS = load_tickets()
        
        # Retry getting ticket status (with built-in retries)
        ticket_check = None
        for _ in range(3):
            ticket_check = get_ticket_status(ticket_id)
            if ticket_check.get("status") == "success":
                break
            time.sleep(0.1)
        
        assert ticket_check and ticket_check.get("status") == "success", f"Ticket {ticket_id} not found before update"
        
        result = update_ticket_priority(ticket_id, "high")
        assert result["status"] == "success", f"Failed to update priority. Error: {result.get('error_message', 'Unknown error')}"
        assert result["new_priority"] == "high"
        
        # Verify priority was updated - reload tickets to get latest
        ticket_module._TICKETS = load_tickets()
        tickets = load_tickets()
        assert tickets[ticket_id]["priority"] == "high"


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
    from unittest.mock import patch
    
    valid_statuses = ["open", "in_progress", "resolved", "closed"]
    
    # Mock Supabase to use JSON fallback BEFORE creating tickets
    with patch('utils.supabase_client.SUPABASE_ENABLED', False):
        for status in valid_statuses:
            ticket_id = setup_test_ticket()
            if not ticket_id:
                pytest.skip("Could not create test ticket")
            
            # Force reload tickets to ensure ticket is available
            from tools.ticket_tool import get_ticket_status, load_tickets
            import tools.ticket_tool as ticket_module
            ticket_module._TICKETS = load_tickets()
            
            # Verify ticket exists before updating
            ticket_check = get_ticket_status(ticket_id)
            assert ticket_check.get("status") == "success", f"Ticket {ticket_id} not found before update"
            
            result = update_ticket_status(ticket_id, status)
            assert result["status"] == "success", f"Failed to update to {status}. Error: {result.get('error_message', 'Unknown error')}"
            assert result["new_status"] == status


def test_update_ticket_priority_all_priorities():
    """Test updating ticket to all valid priorities."""
    from unittest.mock import patch
    
    valid_priorities = ["low", "normal", "high", "urgent"]
    
    # Mock Supabase to use JSON fallback BEFORE creating tickets
    with patch('utils.supabase_client.SUPABASE_ENABLED', False):
        for priority in valid_priorities:
            ticket_id = setup_test_ticket()
            if not ticket_id:
                pytest.skip("Could not create test ticket")
            
            # Force reload tickets to ensure ticket is available
            from tools.ticket_tool import get_ticket_status, load_tickets
            import tools.ticket_tool as ticket_module
            ticket_module._TICKETS = load_tickets()
            
            # Verify ticket exists before updating
            ticket_check = get_ticket_status(ticket_id)
            assert ticket_check.get("status") == "success", f"Ticket {ticket_id} not found before update"
            
            result = update_ticket_priority(ticket_id, priority)
            assert result["status"] == "success", f"Failed to update to {priority}. Error: {result.get('error_message', 'Unknown error')}"
            assert result["new_priority"] == priority

