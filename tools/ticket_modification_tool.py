"""
Ticket Modification Tools for Customer Support Agents

This module provides tools that allow agents to modify tickets.
These tools enable agents to:
- Update ticket status
- Update ticket priority
- Add notes/comments to tickets
"""
from typing import Dict, Optional
from datetime import datetime
import sys
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def update_ticket_status(ticket_id: str, new_status: str, note: Optional[str] = None) -> Dict[str, any]:
    """
    Update the status of a support ticket.
    
    Args:
        ticket_id: The ticket ID to update
        new_status: New status (must be one of: open, in_progress, resolved, closed)
        note: Optional note about the status change
        
    Returns:
        Dictionary with status and ticket information
    """
    try:
        # Validate status
        valid_statuses = ["open", "in_progress", "resolved", "closed"]
        if new_status.lower() not in valid_statuses:
            return {
                "status": "error",
                "error_message": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            }
        
        # Get existing ticket
        from tools.ticket_tool import get_ticket_status
        existing_ticket_result = get_ticket_status(ticket_id)
        
        if existing_ticket_result.get("status") == "error":
            return {
                "status": "error",
                "error_message": f"Ticket {ticket_id} not found"
            }
        
        existing_ticket = existing_ticket_result.get("ticket", {})
        session_id = existing_ticket.get("session_id")
        user_id = existing_ticket.get("user_id")
        
        # Update ticket status via Supabase or JSON
        try:
            from utils.supabase_client import SUPABASE_ENABLED, update_ticket_status as supabase_update, close_session, add_message
            if SUPABASE_ENABLED:
                success = supabase_update(ticket_id, new_status.lower())
                if success:
                    # If ticket is being closed, send thank you message and close session
                    if new_status.lower() == "closed" and session_id and user_id:
                        try:
                            # Send automatic thank you message to customer BEFORE closing session
                            thank_you_message = "Thank you for contacting us! Your ticket has been resolved and closed. If you need any further assistance, please don't hesitate to reach out. Have a great day!"
                            add_message(
                                user_id=user_id,
                                session_id=session_id,
                                role="assistant",
                                content=thank_you_message,
                                metadata={"agent_used": "system", "is_system_message": True, "ticket_closed": True},
                                is_human_agent=False
                            )
                            print(f"[TICKET] Sent thank you message to customer for ticket {ticket_id}")
                            
                            # Close session AFTER sending message
                            close_session(session_id)
                            print(f"[TICKET] Session {session_id} closed automatically after ticket closure")
                        except Exception as e:
                            print(f"[WARNING] Failed to send message or close session {session_id}: {e}")
                    
                    return {
                        "status": "success",
                        "message": f"Ticket {ticket_id} status updated to {new_status}.",
                        "ticket_id": ticket_id,
                        "previous_status": existing_ticket.get("status"),
                        "new_status": new_status.lower()
                    }
        except Exception as e:
            pass  # Fallback to JSON
        
        # Fallback to JSON
        from tools.ticket_tool import get_all_tickets, save_tickets, load_tickets
        tickets = load_tickets()  # Reload to get latest
        if isinstance(tickets, dict) and ticket_id in tickets:
            tickets[ticket_id]["status"] = new_status.lower()
            tickets[ticket_id]["updated_at"] = datetime.now().isoformat()
            if note:
                if "notes" not in tickets[ticket_id]:
                    tickets[ticket_id]["notes"] = []
                tickets[ticket_id]["notes"].append({
                    "note": note,
                    "timestamp": datetime.now().isoformat(),
                    "type": "status_change"
                })
            save_tickets(tickets)
            
            # Update global cache to ensure get_ticket_status can find it
            import tools.ticket_tool as ticket_module
            ticket_module._TICKETS = tickets
            # Also update the specific ticket in cache
            if ticket_id in tickets:
                ticket_module._TICKETS[ticket_id] = tickets[ticket_id]
            
            # Close session if ticket is being closed (only if Supabase is enabled)
            if new_status.lower() == "closed" and session_id:
                try:
                    from utils.supabase_client import SUPABASE_ENABLED, close_session, add_message
                    if SUPABASE_ENABLED:
                        user_id = existing_ticket.get("user_id")
                        
                        # Send automatic thank you message to customer BEFORE closing session
                        if user_id:
                            thank_you_message = "Thank you for contacting us! Your ticket has been resolved and closed. If you need any further assistance, please don't hesitate to reach out. Have a great day!"
                            try:
                                add_message(
                                    user_id=user_id,
                                    session_id=session_id,
                                    role="assistant",
                                    content=thank_you_message,
                                    metadata={"agent_used": "system", "is_system_message": True, "ticket_closed": True},
                                    is_human_agent=False
                                )
                                print(f"[TICKET] Sent thank you message to customer for ticket {ticket_id}")
                            except Exception as msg_error:
                                print(f"[WARNING] Failed to send message: {msg_error}")
                        
                        # Close session AFTER sending message
                        try:
                            close_session(session_id)
                            print(f"[TICKET] Session {session_id} closed automatically after ticket closure")
                        except Exception as close_error:
                            print(f"[WARNING] Failed to close session: {close_error}")
                except Exception as e:
                    print(f"[WARNING] Failed to send message or close session {session_id}: {e}")
            
            return {
                "status": "success",
                "message": f"Ticket {ticket_id} status updated to {new_status}.",
                "ticket_id": ticket_id,
                "previous_status": existing_ticket.get("status"),
                "new_status": new_status.lower()
            }
        
        return {
            "status": "error",
            "error_message": f"Ticket {ticket_id} not found"
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error updating ticket status: {str(e)}"
        }


def cancel_ticket(ticket_id: Optional[str] = None, reason: Optional[str] = None) -> Dict[str, any]:
    """
    Cancel a support ticket.
    
    If ticket_id is not provided, will search for the most recent ticket for the user/session.
    
    Args:
        ticket_id: The ticket ID to cancel (optional - will search for recent ticket if not provided)
        reason: Optional reason for cancellation
        session_id: Optional session ID to find recent ticket if ticket_id not provided
        user_id: Optional user ID to find recent ticket if ticket_id not provided
        
    Returns:
        Dictionary with status and ticket information
    """
    try:
        # If no ticket_id provided, try to find the most recent ticket using context
        if not ticket_id:
            try:
                # Get context from ticket_tool (same way create_ticket does)
                from tools.ticket_tool import get_ticket_context
                context = get_ticket_context()
                session_id = context.get("session_id")
                user_id = context.get("user_id")
                
                from utils.supabase_client import SUPABASE_ENABLED, get_tickets
                if SUPABASE_ENABLED:
                    # Get tickets for this session/user
                    tickets = get_tickets(session_id=session_id)
                    if tickets:
                        # Get the most recent ticket (first one in the list, already sorted by created_at desc)
                        most_recent = tickets[0]
                        ticket_id = most_recent.get("ticket_id")
                        if ticket_id:
                            # Found a ticket, continue with cancellation
                            pass
                        else:
                            return {
                                "status": "error",
                                "error_message": "No recent ticket found. Please provide the ticket ID."
                            }
                    else:
                        return {
                            "status": "error",
                            "error_message": "No tickets found. Please provide the ticket ID."
                        }
                else:
                    # Fallback to JSON
                    from tools.ticket_tool import get_all_tickets
                    tickets = get_all_tickets()
                    if isinstance(tickets, dict):
                        # Find most recent ticket for this session/user
                        matching_tickets = []
                        for tid, ticket in tickets.items():
                            if session_id and ticket.get("session_id") == session_id:
                                matching_tickets.append((tid, ticket))
                            elif user_id and ticket.get("user_id") == user_id:
                                matching_tickets.append((tid, ticket))
                        
                        if matching_tickets:
                            # Sort by created_at and get most recent
                            matching_tickets.sort(key=lambda x: x[1].get("created_at", ""), reverse=True)
                            ticket_id = matching_tickets[0][0]
                        else:
                            return {
                                "status": "error",
                                "error_message": "No recent ticket found. Please provide the ticket ID."
                            }
                    else:
                        return {
                            "status": "error",
                            "error_message": "No tickets found. Please provide the ticket ID."
                        }
            except Exception as e:
                return {
                    "status": "error",
                    "error_message": f"Could not find recent ticket: {str(e)}. Please provide the ticket ID."
                }
        
        if not ticket_id:
            return {
                "status": "error",
                "error_message": "Ticket ID is required. Please provide the ticket ID or ensure you have a recent ticket."
            }
        
        # Get existing ticket
        from tools.ticket_tool import get_ticket_status
        existing_ticket_result = get_ticket_status(ticket_id)
        
        if existing_ticket_result.get("status") == "error":
            return {
                "status": "error",
                "error_message": f"Ticket {ticket_id} not found. Please check the ticket ID."
            }
        
        existing_ticket = existing_ticket_result.get("ticket", {})
        current_status = existing_ticket.get("status", "").lower()
        
        # Check if ticket can be cancelled
        if current_status == "closed":
            return {
                "status": "error",
                "error_message": f"Ticket {ticket_id} is already closed."
            }
        
        # Cancel the ticket (set status to closed)
        result = update_ticket_status(
            ticket_id=ticket_id,
            new_status="closed",
            note=reason or "Cancelled by customer request via agent"
        )
        
        if result.get("status") == "success":
            result["message"] = f"Ticket {ticket_id} has been cancelled successfully."
            # Session will be closed only when ticket is closed (status = "closed"), not when cancelled
        
        return result
    
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error cancelling ticket: {str(e)}"
        }


def update_ticket_priority(ticket_id: str, new_priority: str) -> Dict[str, any]:
    """
    Update the priority of a support ticket.
    
    Args:
        ticket_id: The ticket ID to update
        new_priority: New priority (must be one of: low, normal, high, urgent)
        
    Returns:
        Dictionary with status and ticket information
    """
    try:
        # Validate priority
        valid_priorities = ["low", "normal", "high", "urgent"]
        if new_priority.lower() not in valid_priorities:
            return {
                "status": "error",
                "error_message": f"Invalid priority. Must be one of: {', '.join(valid_priorities)}"
            }
        
        # Get existing ticket
        from tools.ticket_tool import get_ticket_status
        existing_ticket_result = get_ticket_status(ticket_id)
        
        if existing_ticket_result.get("status") == "error":
            return {
                "status": "error",
                "error_message": f"Ticket {ticket_id} not found"
            }
        
        # Update via Supabase
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
                    supabase.table("tickets").update({
                        "priority": new_priority.lower(),
                        "updated_at": datetime.now().isoformat()
                    }).eq("ticket_id", ticket_id).execute()
                    
                    return {
                        "status": "success",
                        "message": f"Ticket {ticket_id} priority updated to {new_priority}.",
                        "ticket_id": ticket_id,
                        "new_priority": new_priority.lower()
                    }
        except Exception as e:
            pass  # Fallback to JSON
        
        # Fallback to JSON
        from tools.ticket_tool import get_all_tickets, save_tickets, load_tickets
        tickets = load_tickets()  # Reload to get latest
        if isinstance(tickets, dict) and ticket_id in tickets:
            tickets[ticket_id]["priority"] = new_priority.lower()
            tickets[ticket_id]["updated_at"] = datetime.now().isoformat()
            save_tickets(tickets)
            
            # Update global cache to ensure get_ticket_status can find it
            import tools.ticket_tool as ticket_module
            ticket_module._TICKETS = tickets
            # Also update the specific ticket in cache
            if ticket_id in tickets:
                ticket_module._TICKETS[ticket_id] = tickets[ticket_id]
            
            return {
                "status": "success",
                "message": f"Ticket {ticket_id} priority updated to {new_priority}.",
                "ticket_id": ticket_id,
                "new_priority": new_priority.lower()
            }
        
        return {
            "status": "error",
            "error_message": f"Ticket {ticket_id} not found"
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error updating ticket priority: {str(e)}"
        }

