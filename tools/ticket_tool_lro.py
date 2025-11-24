"""
Long-Running Operation (LRO) Tool for Ticket Creation

This tool demonstrates the Long-Running Operations pattern from the course,
where an agent can pause tool execution and wait for human approval before
continuing. This is essential for high-priority or sensitive operations.

LRO Pattern:
1. Agent calls tool with high-priority request
2. Tool pauses execution using ToolContext.pause()
3. Human reviews and approves/rejects
4. Tool resumes after approval
5. Operation completes

Use Case:
- High-priority tickets requiring manager approval
- Urgent escalations needing verification
- Sensitive operations requiring oversight

This pattern allows agents to handle complex workflows that require
human judgment while maintaining automation for routine tasks.
"""
from typing import Dict, Optional
from datetime import datetime
import uuid
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext


# Import persistence functions from ticket_tool
from tools.ticket_tool import load_tickets, save_tickets

# Use shared ticket storage
_TICKETS = load_tickets()


def create_ticket_with_approval(
    issue: str,
    customer_id: Optional[str] = None,
    priority: str = "normal",
    tool_context: Optional[ToolContext] = None
) -> Dict[str, any]:
    """
    Create an escalation ticket with human-in-the-loop approval (LRO).
    
    This tool demonstrates Long-Running Operations where the agent pauses
    and waits for human approval before creating high-priority tickets.
    
    Args:
        issue: Description of the customer's issue
        customer_id: Optional customer ID
        priority: Ticket priority - "low", "normal", "high", or "urgent"
        tool_context: ADK ToolContext for pause/resume functionality
        
    Returns:
        Dictionary with status and ticket information
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
        
        # For high-priority or urgent tickets, pause for human approval
        if priority.lower() in ["high", "urgent"] and tool_context:
            # Pause the operation and request human approval
            tool_context.pause(
                reason=f"High-priority ticket creation requires approval. "
                       f"Issue: {issue[:100]}... Priority: {priority}",
                metadata={
                    "issue": issue,
                    "customer_id": customer_id,
                    "priority": priority,
                    "action": "create_ticket"
                }
            )
            # After resume, continue with ticket creation
            # The tool will be called again after approval
        
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
            "assigned_to": None,
            "requires_approval": priority.lower() in ["high", "urgent"]
        }
        
        # Store ticket and persist to file
        _TICKETS[ticket_id] = ticket
        save_tickets(_TICKETS)
        
        print(f"✅ [TICKET-LRO] Created ticket {ticket_id} - Priority: {priority}, Issue: {issue[:50]}...")
        
        return {
            "status": "success",
            "ticket_id": ticket_id,
            "message": f"Ticket {ticket_id} has been created{' and approved' if priority.lower() in ['high', 'urgent'] else ''}. "
                       f"You will receive an email confirmation shortly.",
            "priority": priority,
            "approved": priority.lower() in ["high", "urgent"]
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error creating ticket: {str(e)}"
        }


# Create FunctionTool with LRO support
# Note: FunctionTool automatically extracts description from function docstring
ticket_tool_lro = FunctionTool(create_ticket_with_approval)

