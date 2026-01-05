"""Ticket Creation and Status Lookup Tool"""
from typing import Dict, Optional
from datetime import datetime
import uuid
import json
from pathlib import Path
import threading

# Ticket storage file
TICKETS_FILE = Path(__file__).parent.parent / "data" / "tickets.json"

# Global context storage for ticket creation (session_id, user_id)
# Key: request_id (unique per request), Value: dict with session_id and user_id
_ticket_contexts = {}
_context_lock = threading.Lock()


# Ticket Storage with Persistence
def load_tickets() -> Dict[str, Dict]:
 """Load tickets from JSON file."""
 if TICKETS_FILE.exists():
 try:
 with open(TICKETS_FILE, "r", encoding="utf-8") as f:
 data = json.load(f)
 # Convert list to dict if needed (for backward compatibility)
 if isinstance(data, list):
 return {t["ticket_id"]: t for t in data}
 elif isinstance(data, dict):
 return data
 except Exception as e:
 print(f"Error loading tickets: {e}")
 return {}


def save_tickets(tickets: Dict[str, Dict]):
 """Save tickets to JSON file."""
 try:
 TICKETS_FILE.parent.mkdir(parents=True, exist_ok=True)
 # Simple write with flush (atomic write not needed for test environment)
 with open(TICKETS_FILE, "w", encoding="utf-8") as f:
 json.dump(tickets, f, indent=2, ensure_ascii=False)
 f.flush()
 try:
 import os
 os.fsync(f.fileno()) # Force write to disk if available
 except (AttributeError, OSError):
 pass # os.fsync not available on all systems
 except Exception as e:
 print(f"Error saving tickets: {e}")


# Private aliases for backward compatibility
_load_tickets = load_tickets
_save_tickets = save_tickets


# Load tickets on module import
_TICKETS = load_tickets()


def create_ticket(issue: str, customer_id: Optional[str] = None, priority: str = "normal", session_id: Optional[str] = None, user_id: Optional[str] = None) -> Dict[str, any]:
 """
 Create an escalation ticket for customer support.
 
 This tool creates a support ticket when an issue needs to be escalated
 to a human agent. Tickets are assigned unique IDs and tracked for resolution.
 
 Args:
 issue: Description of the customer's issue
 customer_id: Optional customer ID (if available)
 priority: Ticket priority - "low", "normal", "high", or "urgent"
 session_id: Optional session ID to link ticket to conversation
 user_id: Optional user ID to link ticket to user
 
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
 
 # Check if an active ticket already exists for this session (max 1 active ticket per session)
 # Multiple tickets allowed only if previous ones are closed/resolved
 if session_id:
 _TICKETS = load_tickets() # Reload to get latest state
 existing_tickets = []
 if isinstance(_TICKETS, dict):
 existing_tickets = [t for t in _TICKETS.values() if t.get("session_id") == session_id]
 elif isinstance(_TICKETS, list):
 existing_tickets = [t for t in _TICKETS if t.get("session_id") == session_id]
 
 # Check for active tickets (not closed/resolved)
 active_tickets = [t for t in existing_tickets if t.get("status", "").lower() not in ["closed", "resolved"]]
 if active_tickets:
 # Return existing ticket instead of creating duplicate (max 1 active ticket per session)
 existing_ticket = active_tickets[0] # Get most recent
 return {
 "status": "success",
 "ticket_id": existing_ticket.get("ticket_id"),
 "message": f"Ticket {existing_ticket.get('ticket_id')} already exists for this session. Only one active ticket per session is allowed.",
 "existing": True
 }
 
 # Validate priority
 valid_priorities = ["low", "normal", "high", "urgent"]
 if priority.lower() not in valid_priorities:
 priority = "normal"
 
 # Generate unique ticket ID
 ticket_id = f"TICKET-{uuid.uuid4().hex[:8].upper()}"
 
 # Note: customer_id will be retrieved AFTER we get session_id from context
 # This is done later in the code after session_id is determined
 
 # Create ticket record
 ticket = {
 "ticket_id": ticket_id,
 "customer_id": customer_id or "unknown",
 "issue": issue.strip(),
 "priority": priority.lower(),
 "status": "open",
 "created_at": datetime.now().isoformat()
 }
 
 # Add session_id and user_id if provided (from parameters or context)
 # Try multiple methods to get session_id and user_id
 
 # Method 1: From parameters (direct) - already have session_id and user_id if provided
 
 # Method 2: From context (if set by API server) - check this FIRST before trying other methods
 ctx = {}
 if not session_id or not user_id:
 # Try to get context - this is set by API server before calling the agent
 with _context_lock:
 if _ticket_contexts:
 # Get the most recent context (last item in dict)
 last_key = list(_ticket_contexts.keys())[-1]
 ctx = _ticket_contexts[last_key]
 # Use context values if we don't have them
 if not session_id and ctx.get("session_id"):
 session_id = ctx["session_id"]
 if not user_id and ctx.get("user_id"):
 user_id = ctx["user_id"]
 
 # Method 3: From conversation history (find most recent session)
 # This is the most reliable method - get session_id from the most recent message
 # Only use this if we still don't have session_id or user_id after checking context
 if not session_id or not user_id:
 try:
 # Try Supabase first - but we need user_id to query efficiently
 from utils.supabase_client import SUPABASE_ENABLED, get_messages
 if SUPABASE_ENABLED:
 # If we have user_id from context, use it to get messages
 if user_id:
 recent_messages = get_messages(user_id=user_id, session_id=None, limit=10)
 elif ctx.get("user_id"):
 recent_messages = get_messages(user_id=ctx["user_id"], session_id=None, limit=10)
 else:
 # Can't query Supabase without user_id, skip this method
 recent_messages = []
 
 if recent_messages:
 # Get the most recent message
 most_recent_msg = recent_messages[-1]
 if not session_id and most_recent_msg.get("session_id"):
 session_id = most_recent_msg["session_id"]
 if not user_id and most_recent_msg.get("user_id"):
 user_id = most_recent_msg["user_id"]
 else:
 # Fallback to JSON
 from memory.conversation_history import conversation_history
 # Get the most recent message from any user to find the current session
 with conversation_history._lock:
 all_history = dict(conversation_history._history)
 
 # Find the most recent message across all users
 most_recent_msg = None
 most_recent_user = None
 most_recent_time = ""
 
 for user_id_key, messages in all_history.items():
 if messages:
 # Get the last message (most recent)
 last_msg = messages[-1]
 msg_time = last_msg.get("timestamp", "")
 if msg_time > most_recent_time:
 most_recent_time = msg_time
 most_recent_msg = last_msg
 most_recent_user = user_id_key
 
 if most_recent_msg:
 if not session_id and most_recent_msg.get("session_id"):
 session_id = most_recent_msg["session_id"]
 if not user_id and most_recent_user:
 user_id = most_recent_user
 except Exception as e:
 # Try fallback: session metadata
 try:
 from utils.supabase_client import SUPABASE_ENABLED, get_user_sessions
 if SUPABASE_ENABLED:
 # Try to get most recent session from Supabase
 # We need a user_id to query, so try to get from context first
 if ctx.get("user_id"):
 sessions = get_user_sessions(ctx["user_id"])
 if sessions:
 most_recent = sessions[0] # Already sorted by updated_at desc
 if not session_id and most_recent.get("session_id"):
 session_id = most_recent["session_id"]
 if not user_id and most_recent.get("user_id"):
 user_id = most_recent["user_id"]
 else:
 # Fallback to JSON
 from memory.session_metadata import session_metadata
 with session_metadata._lock:
 all_sessions = dict(session_metadata._metadata)
 
 if all_sessions:
 sorted_sessions = sorted(
 [s for s in all_sessions.values() if isinstance(s, dict)],
 key=lambda x: x.get("updated_at", ""),
 reverse=True
 )
 if sorted_sessions:
 most_recent = sorted_sessions[0]
 if not session_id and most_recent.get("session_id"):
 session_id = most_recent["session_id"]
 if not user_id and most_recent.get("user_id"):
 user_id = most_recent["user_id"]
 except Exception:
 pass # Both methods failed, continue without session_id/user_id
 
 # NOW try to get customer_id from session if we have session_id but not customer_id
 if not customer_id and session_id:
 # Method 1: Try to get from session in Supabase
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
 print(f"[TICKET] Retrieved customer_id from session (after getting session_id): {customer_id}")
 except Exception as e:
 print(f"[TICKET] Could not get customer_id from session: {e}")
 
 # Method 2: Try to get from order context
 if not customer_id:
 try:
 from tools.order_tool import get_order_context
 ctx = get_order_context(session_id)
 customer_id = ctx.get("customer_id")
 if customer_id:
 print(f"[TICKET] Retrieved customer_id from order context: {customer_id}")
 except Exception as e:
 print(f"[TICKET] Could not get customer_id from order context: {e}")
 
 # Set session_id and user_id in ticket (use whatever we found)
 if session_id:
 ticket["session_id"] = session_id
 if user_id:
 ticket["user_id"] = user_id
 
 # Update customer_id in ticket if we found it (should already be set, but ensure it)
 if customer_id and customer_id != "unknown":
 ticket["customer_id"] = customer_id
 print(f"[TICKET] Using customer_id from context/session: {customer_id}")
 else:
 print(f"[TICKET] Warning: customer_id not found, will be 'unknown'")
 
 # Try Supabase first
 try:
 from utils.supabase_client import SUPABASE_ENABLED, create_ticket as supabase_create_ticket, close_session
 if SUPABASE_ENABLED:
 # Use the customer_id we found (not "unknown")
 ticket_customer_id = ticket.get("customer_id") or customer_id
 if not ticket_customer_id or ticket_customer_id == "unknown":
 print(f"[TICKET] Warning: customer_id is None or 'unknown', supabase_create_ticket will try to get it from session")
 result = supabase_create_ticket(issue, ticket_customer_id, priority, session_id, user_id)
 if result.get("status") == "success":
 ticket_id = result.get("ticket_id", ticket_id)
 print(f"[TICKET] Created ticket {ticket_id} in Supabase - Priority: {priority}, Issue: {issue[:50]}...")
 # Session will be closed only when ticket is closed, not when created
 
 # Generate conversation summary automatically if we have session_id and user_id
 if session_id and user_id:
 try:
 from utils.conversation_summarizer import ConversationSummarizer
 summarizer = ConversationSummarizer()
 summary_result = summarizer.generate_summary(
 user_id=user_id,
 session_id=session_id,
 ticket_id=ticket_id,
 summary_length="medium",
 ticket_issue=issue # Pass the ticket issue to focus the summary
 )
 if summary_result.get("status") == "success":
 print(f"[SUMMARY] Generated summary for ticket {ticket_id}")
 else:
 print(f"[WARNING] [SUMMARY] Failed to generate summary: {summary_result.get('error_message', 'Unknown error')}")
 except Exception as e:
 print(f" [SUMMARY] Error generating summary: {e}")
 
 return result
 except Exception as e:
 print(f" [TICKET] Supabase error, using JSON fallback: {e}")
 
 # Fallback to JSON
 _TICKETS[ticket_id] = ticket
 save_tickets(_TICKETS)
 
 print(f"[TICKET] Created ticket {ticket_id} in JSON - Priority: {priority}, Issue: {issue[:50]}...")
 
 # Generate conversation summary automatically if we have session_id and user_id
 if session_id and user_id:
 try:
 from utils.conversation_summarizer import ConversationSummarizer
 summarizer = ConversationSummarizer()
 summary_result = summarizer.generate_summary(
 user_id=user_id,
 session_id=session_id,
 ticket_id=ticket_id,
 summary_length="medium",
 ticket_issue=issue # Pass the ticket issue to focus the summary
 )
 if summary_result.get("status") == "success":
 print(f"[SUMMARY] Generated summary for ticket {ticket_id}")
 else:
 print(f"[WARNING] [SUMMARY] Failed to generate summary: {summary_result.get('error_message', 'Unknown error')}")
 except Exception as e:
 print(f" [SUMMARY] Error generating summary: {e}")
 
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
 global _TICKETS
 import time
 
 ticket_id = str(ticket_id).strip()
 
 # First check in-memory cache (fastest, most up-to-date)
 ticket = _TICKETS.get(ticket_id)
 if ticket:
 return {
 "status": "success",
 "ticket": ticket
 }
 
 # Try Supabase if enabled
 try:
 from utils.supabase_client import SUPABASE_ENABLED, get_tickets
 if SUPABASE_ENABLED:
 # Get all tickets and find the one we need
 tickets = get_tickets()
 for ticket in tickets:
 if ticket.get("ticket_id") == ticket_id:
 # Update in-memory cache
 _TICKETS[ticket_id] = ticket
 return {
 "status": "success",
 "ticket": ticket
 }
 except Exception as e:
 print(f"Warning: Could not check Supabase for ticket: {e}")
 
 # Reload from file to get latest (important in parallel test environments)
 # Try multiple times in case file is being written (common in parallel test environments)
 max_retries = 5
 for attempt in range(max_retries):
 _TICKETS = load_tickets() # Reload to get latest
 
 # Check in-memory cache after reload
 ticket = _TICKETS.get(ticket_id)
 if ticket:
 return {
 "status": "success",
 "ticket": ticket
 }
 
 # If not found and not last attempt, wait a bit for file to be written
 if attempt < max_retries - 1:
 time.sleep(0.05) # 50ms delay (increased for parallel test environments)
 
 # Ticket not found after retries
 return {
 "status": "error",
 "error_message": f"Ticket {ticket_id} not found"
 }
 
 except Exception as e:
 return {
 "status": "error",
 "error_message": f"Error looking up ticket: {str(e)}"
 }


def get_all_tickets() -> Dict[str, Dict]:
 """Get all tickets (reloads from file or Supabase). Prioritizes Supabase when enabled."""
 # Always try Supabase first if enabled
 from utils.supabase_client import SUPABASE_ENABLED
 if SUPABASE_ENABLED:
 try:
 from utils.supabase_client import get_tickets as supabase_get_tickets
 tickets_list = supabase_get_tickets()
 # Even if empty, stay with Supabase (don't use JSON fallback)
 print(f" [TICKET] Loaded {len(tickets_list)} tickets from Supabase")
 # Convertir en dict pour compatibilité
 return {t["ticket_id"]: t for t in tickets_list}
 except Exception as e:
 print(f" [TICKET] Supabase error (will use JSON fallback): {e}")
 import traceback
 traceback.print_exc()
 # Only fallback to JSON on error, not on empty list
 
 # Fallback vers JSON (only if Supabase is disabled or failed with error)
 global _TICKETS
 _TICKETS = load_tickets()
 if _TICKETS:
 print(f" [TICKET] Loaded {len(_TICKETS)} tickets from JSON fallback")
 return _TICKETS


def set_ticket_context(session_id: Optional[str] = None, user_id: Optional[str] = None, request_id: Optional[str] = None):
 """
 Set context for ticket creation.
 This allows tools to access session_id and user_id without passing them explicitly.
 
 Args:
 session_id: Session identifier
 user_id: User identifier
 request_id: Optional unique request identifier (if None, uses session_id as key)
 """
 key = request_id or session_id or "default"
 with _context_lock:
 _ticket_contexts[key] = {
 "session_id": session_id,
 "user_id": user_id
 }


def get_ticket_context(request_id: Optional[str] = None, session_id: Optional[str] = None) -> Dict:
 """
 Get context for ticket creation.
 
 Args:
 request_id: Optional request identifier
 session_id: Optional session identifier (used as fallback key)
 
 Returns:
 Dict with session_id and user_id, or empty dict
 """
 key = request_id or session_id or "default"
 with _context_lock:
 return _ticket_contexts.get(key, {})


def clear_ticket_context(request_id: Optional[str] = None, session_id: Optional[str] = None):
 """
 Clear context for ticket creation.
 
 Args:
 request_id: Optional request identifier
 session_id: Optional session identifier (used as fallback key)
 """
 key = request_id or session_id or "default"
 with _context_lock:
 if key in _ticket_contexts:
 del _ticket_contexts[key]

