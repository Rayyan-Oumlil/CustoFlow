"""
Ticket Creation and Status Lookup Tool

This tool manages support ticket creation and status retrieval.
In production, this would integrate with a ticket management system
like Zendesk, Jira, or a custom ticketing system.

Features:
- Ticket creation with priority levels (low, normal, high, urgent)
- Ticket status lookup
- Unique ticket ID generation
- Priority-based routing

Production Integration:
- Replace _TICKETS with database or API calls
- Integrate with existing ticketing system
- Add webhook notifications
- Add ticket assignment logic
"""
from typing import Dict, Optional
from datetime import datetime
import uuid


# ============================================================================
# Mock Ticket Storage
# ============================================================================
# In production, replace with:
# - Database table (tickets)
# - Ticket management API (Zendesk, Jira, etc.)
# - CRM integration
# ============================================================================
_TICKETS = {}


def create_ticket(issue: str, customer_id: Optional[str] = None, priority: str = "normal") -> Dict[str, any]:
    """
    Create an escalation ticket for customer support.
    
    This tool creates a support ticket when an issue needs to be escalated
    to a human agent. Tickets are assigned unique IDs and tracked for resolution.
    
    Args:
        issue: Description of the customer's issue
        customer_id: Optional customer ID (if available)
        priority: Ticket priority - "low", "normal", "high", or "urgent"
        
    Returns:
        Dictionary with status and ticket information:
        - Success: {"status": "success", "ticket_id": "...", "message": "..."}
        - Error: {"status": "error", "error_message": "..."}
    """
    try:
        if not issue or not issue.strip():
            return {
                "status": "error",
                "error_message": "Issue description cannot be empty"
            }
        
        # Validate priority
        valid_priorities = ["low", "normal", "high", "urgent"]
        if priority.lower() not in valid_priorities:
            priority = "normal"
        
        # Generate unique ticket ID
        ticket_id = f"TICKET-{uuid.uuid4().hex[:8].upper()}"
        
        # Create ticket record
        ticket = {
            "ticket_id": ticket_id,
            "customer_id": customer_id or "unknown",
            "issue": issue.strip(),
            "priority": priority.lower(),
            "status": "open",
            "created_at": datetime.now().isoformat(),
            "assigned_to": None
        }
        
        # Store ticket (in production, this would be saved to a database)
        _TICKETS[ticket_id] = ticket
        
        return {
            "status": "success",
            "ticket_id": ticket_id,
            "message": f"Ticket {ticket_id} has been created and will be reviewed by our support team. "
                       f"You will receive an email confirmation shortly."
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error creating ticket: {str(e)}"
        }


def get_ticket_status(ticket_id: str) -> Dict[str, any]:
    """
    Get the status of an existing ticket.
    
    Args:
        ticket_id: The ticket ID to look up
        
    Returns:
        Dictionary with ticket status information
    """
    try:
        ticket_id = str(ticket_id).strip()
        
        ticket = _TICKETS.get(ticket_id)
        
        if ticket:
            return {
                "status": "success",
                "ticket": ticket
            }
        else:
            return {
                "status": "error",
                "error_message": f"Ticket {ticket_id} not found"
            }
    
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error looking up ticket: {str(e)}"
        }

