"""
Session Metadata Management

Manages session metadata like custom names, creation dates, etc.
Now with file-based persistence (like orders).
"""
from typing import Dict, Optional
from datetime import datetime
from collections import defaultdict
import threading
import json
from pathlib import Path


class SessionMetadata:
    """
    Thread-safe session metadata storage with file persistence.
    
    Stores custom names and metadata for sessions.
    Sessions are saved to data/sessions.json for persistence.
    """
    
    SESSIONS_FILE = Path(__file__).parent.parent / "data" / "sessions.json"
    
    def __init__(self):
        """Initialize session metadata storage."""
        self._metadata: Dict[str, Dict] = defaultdict(dict)
        self._lock = threading.Lock()
        # Load existing sessions from file
        self._load_sessions()
    
    def _load_sessions(self) -> None:
        """Load sessions from JSON file."""
        try:
            if self.SESSIONS_FILE.exists():
                with open(self.SESSIONS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self._metadata = defaultdict(dict, data)
                    elif isinstance(data, list):
                        # Convert list to dict
                        self._metadata = defaultdict(dict, {
                            session["session_id"]: session for session in data
                        })
        except Exception as e:
            print(f"Warning: Could not load sessions from file: {e}. Starting with empty sessions.")
            self._metadata = defaultdict(dict)
    
    def _save_sessions(self) -> bool:
        """Save sessions to JSON file."""
        try:
            # Ensure data directory exists
            self.SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert to regular dict for JSON serialization
            sessions_dict = dict(self._metadata)
            
            # Save as JSON
            with open(self.SESSIONS_FILE, 'w', encoding='utf-8') as f:
                json.dump(sessions_dict, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving sessions to file: {e}")
            return False
    
    def create_session(
        self,
        session_id: str,
        user_id: str,
        name: Optional[str] = None,
        customer_id: Optional[str] = None
    ) -> Dict:
        """
        Create or update session metadata.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            name: Optional custom name for the session
            
        Returns:
            Session metadata dictionary
        """
        # Essayer Supabase d'abord
        try:
            from utils.supabase_client import SUPABASE_ENABLED, create_session as supabase_create_session
            if SUPABASE_ENABLED:
                result = supabase_create_session(session_id, user_id, name, customer_id)
                if result:
                    return result
        except Exception:
            pass  # Fallback vers JSON
        
        # Fallback vers JSON
        with self._lock:
            if session_id not in self._metadata:
                self._metadata[session_id] = {
                    "session_id": session_id,
                    "user_id": user_id,
                    "customer_id": customer_id,
                    "name": name or f"Session {session_id[-8:]}",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "message_count": 0
                }
            else:
                # Update existing session
                self._metadata[session_id]["updated_at"] = datetime.now().isoformat()
                if name:
                    self._metadata[session_id]["name"] = name
                if customer_id:
                    self._metadata[session_id]["customer_id"] = customer_id
            
            # Save to file after modification
            self._save_sessions()
            
            return self._metadata[session_id].copy()
    
    def rename_session(self, session_id: str, new_name: str) -> bool:
        """
        Rename a session.
        
        Args:
            session_id: Session identifier
            new_name: New name for the session
            
        Returns:
            True if renamed, False if session not found
        """
        # Try Supabase first
        try:
            from utils.supabase_client import SUPABASE_ENABLED, rename_session as supabase_rename_session
            if SUPABASE_ENABLED:
                success = supabase_rename_session(session_id, new_name)
                if success:
                    return True
        except Exception:
            pass  # Fallback to JSON
        
        # Fallback to JSON
        with self._lock:
            if session_id in self._metadata:
                self._metadata[session_id]["name"] = new_name
                self._metadata[session_id]["updated_at"] = datetime.now().isoformat()
                # Save to file after modification
                self._save_sessions()
                return True
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get session metadata.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session metadata or None if not found
        """
        with self._lock:
            return self._metadata.get(session_id, {}).copy() if session_id in self._metadata else None
    
    def get_user_sessions(self, user_id: str, customer_id: Optional[str] = None) -> list[Dict]:
        """
        Get all sessions for a user, optionally filtered by customer_id.
        If customer_id is provided, user_id is IGNORED completely.
        
        Args:
            user_id: User identifier (ignored if customer_id is provided)
            customer_id: Optional customer identifier to filter sessions
            
        Returns:
            List of session metadata dictionaries
        """
        # Essayer Supabase d'abord
        try:
            from utils.supabase_client import SUPABASE_ENABLED, get_user_sessions as supabase_get_user_sessions
            if SUPABASE_ENABLED:
                result = supabase_get_user_sessions(user_id, customer_id)
                if result is not None:  # Check for None, not just truthy (empty list is valid)
                    return result
        except Exception:
            pass  # Fallback vers JSON
        
        # Fallback vers JSON
        with self._lock:
            if customer_id:
                # If customer_id is provided, IGNORE user_id completely
                # Normalize customer_id to lowercase for case-insensitive matching
                customer_id_lower = customer_id.lower()
                sessions = [
                    metadata.copy()
                    for metadata in self._metadata.values()
                    if metadata.get("customer_id") and metadata.get("customer_id").lower() == customer_id_lower
                ]
            else:
                # If no customer_id, filter by user_id only
                sessions = [
                    metadata.copy()
                    for metadata in self._metadata.values()
                    if metadata.get("user_id") == user_id
                ]
            # Sort by updated_at (most recent first)
            sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
            return sessions
    
    def increment_message_count(self, session_id: str) -> None:
        """Increment message count for a session."""
        # Try Supabase first
        try:
            from utils.supabase_client import SUPABASE_ENABLED, increment_message_count as supabase_increment_message_count
            if SUPABASE_ENABLED:
                supabase_increment_message_count(session_id)
                return
        except Exception:
            pass  # Fallback to JSON
        
        # Fallback to JSON
        with self._lock:
            if session_id in self._metadata:
                self._metadata[session_id]["message_count"] = self._metadata[session_id].get("message_count", 0) + 1
                self._metadata[session_id]["updated_at"] = datetime.now().isoformat()
                # Save to file after modification (but less frequently for performance)
                # Only save every 5 messages to avoid too many file writes
                if self._metadata[session_id]["message_count"] % 5 == 0:
                    self._save_sessions()
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete session metadata.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False if not found
        """
        # Try Supabase first
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
                    # IMPORTANT: We do NOT delete tickets when deleting a session!
                    # Tickets are important business entities that must persist even if the session is deleted.
                    # Tickets are linked to session_id but should remain accessible for support history.
                    
                    # Delete in correct order to respect foreign key constraints:
                    # 1. Delete analytics_interactions first
                    try:
                        supabase.table("analytics_interactions").delete().eq("session_id", session_id).execute()
                    except Exception as e:
                        print(f"Warning: Could not delete analytics_interactions: {e}")
                    
                    # 2. Delete messages
                    try:
                        supabase.table("messages").delete().eq("session_id", session_id).execute()
                    except Exception as e:
                        print(f"Warning: Could not delete messages: {e}")
                    
                    # 3. Delete conversation_summaries if they reference session_id
                    try:
                        supabase.table("conversation_summaries").delete().eq("session_id", session_id).execute()
                    except Exception as e:
                        print(f"Warning: Could not delete conversation_summaries: {e}")
                    
                    # 4. Delete feedback linked to session (but keep auto_learning entries - they're important)
                    try:
                        supabase.table("feedback").delete().eq("session_id", session_id).execute()
                    except Exception as e:
                        print(f"Warning: Could not delete feedback: {e}")
                    
                    # 5. Close all tickets associated with this session (but don't delete them)
                    # Tickets are important business entities that must persist for support history
                    try:
                        from utils.supabase_client import get_tickets, update_ticket_status
                        tickets = get_tickets(session_id=session_id)
                        closed_count = 0
                        if not tickets:
                            print(f"ℹ️  No tickets found for session {session_id}")
                        else:
                            print(f"ℹ️  Found {len(tickets)} ticket(s) for session {session_id}")
                            for ticket in tickets:
                                ticket_id = ticket.get("ticket_id")
                                current_status = ticket.get("status", "").lower() if ticket.get("status") else ""
                                print(f"ℹ️  Ticket {ticket_id} current status: {current_status}")
                                # Only close if not already closed
                                if current_status not in ["closed", "resolved"]:
                                    try:
                                        success = update_ticket_status(ticket_id, "closed")
                                        if success:
                                            closed_count += 1
                                            print(f"✅ Closed ticket {ticket_id} associated with session {session_id}")
                                        else:
                                            print(f"❌ Failed to close ticket {ticket_id} (update_ticket_status returned False)")
                                    except Exception as ticket_error:
                                        print(f"❌ Warning: Could not close ticket {ticket_id}: {ticket_error}")
                                        import traceback
                                        traceback.print_exc()
                                else:
                                    print(f"ℹ️  Ticket {ticket_id} already closed/resolved, skipping")
                            if closed_count > 0:
                                print(f"✅ Closed {closed_count} ticket(s) associated with session {session_id}")
                            else:
                                print(f"ℹ️  No tickets needed to be closed for session {session_id}")
                    except Exception as e:
                        print(f"❌ Warning: Could not close tickets for session {session_id}: {e}")
                        import traceback
                        traceback.print_exc()
                    
                    # 6. Finally delete session
                    # NOTE: Tickets are NOT deleted - they are closed but persist for support history
                    # First check if session exists
                    check_result = supabase.table("sessions").select("session_id").eq("session_id", session_id).limit(1).execute()
                    if check_result.data and len(check_result.data) > 0:
                        # Session exists, delete it
                        result = supabase.table("sessions").delete().eq("session_id", session_id).execute()
                        print(f"✅ Session {session_id} deleted from Supabase. Associated tickets were closed but preserved.")
                        return True
                    else:
                        # Session doesn't exist in Supabase, but we still cleaned up related data
                        # This is idempotent - return True even if session was already deleted
                        print(f"ℹ️  Session {session_id} not found in Supabase (may have been already deleted). Related data cleaned up.")
                        return True
        except Exception as e:
            print(f"Error deleting session from Supabase: {e}")
        
        # Fallback to JSON
        # Before deleting session:
        # 1. Close all associated tickets
        # 2. Delete all associated feedback (but keep auto_learning entries - they're important)
        try:
            from tools.ticket_tool import get_all_tickets
            from tools.ticket_modification_tool import update_ticket_status
            all_tickets = get_all_tickets()
            closed_count = 0
            
            # Find tickets for this session
            if isinstance(all_tickets, dict):
                tickets_list = list(all_tickets.values())
            else:
                tickets_list = all_tickets if isinstance(all_tickets, list) else []
            
            # Filter tickets for this session
            session_tickets = [t for t in tickets_list if t.get("session_id") == session_id]
            
            if not session_tickets:
                print(f"ℹ️  No tickets found in JSON mode for session {session_id}")
            else:
                print(f"ℹ️  Found {len(session_tickets)} ticket(s) for session {session_id} in JSON mode")
                for ticket in session_tickets:
                    ticket_id = ticket.get("ticket_id")
                    current_status = ticket.get("status", "").lower() if ticket.get("status") else ""
                    print(f"ℹ️  Ticket {ticket_id} current status: {current_status}")
                    # Only close if not already closed
                    if current_status not in ["closed", "resolved"]:
                        try:
                            result = update_ticket_status(ticket_id, "closed", note="Session deleted by user")
                            if result.get("status") == "success":
                                closed_count += 1
                                print(f"✅ Closed ticket {ticket_id} associated with session {session_id}")
                            else:
                                print(f"❌ Failed to close ticket {ticket_id}: {result.get('error_message', 'Unknown error')}")
                        except Exception as ticket_error:
                            print(f"❌ Warning: Could not close ticket {ticket_id}: {ticket_error}")
                            import traceback
                            traceback.print_exc()
                    else:
                        print(f"ℹ️  Ticket {ticket_id} already closed/resolved, skipping")
            
            if closed_count > 0:
                print(f"✅ Closed {closed_count} ticket(s) associated with session {session_id}")
            else:
                print(f"ℹ️  No tickets needed to be closed for session {session_id}")
        except Exception as e:
            print(f"Warning: Could not close tickets for session {session_id}: {e}")
        
        # Delete messages associated with this session (JSON mode)
        try:
            from memory.conversation_history import conversation_history
            # Get all messages for this session
            all_messages = conversation_history.get_history(user_id="", limit=None, session_id=session_id)
            if all_messages:
                # Remove messages from conversation history
                with conversation_history._lock:
                    # Remove messages from all user histories
                    for user_id in list(conversation_history._history.keys()):
                        conversation_history._history[user_id] = [
                            msg for msg in conversation_history._history[user_id]
                            if msg.get("session_id") != session_id
                        ]
                    # Save to file
                    from memory.conversation_history import _save_history
                    _save_history(conversation_history._history)
                print(f"✅ Deleted {len(all_messages)} message(s) for session {session_id}")
        except Exception as e:
            print(f"Warning: Could not delete messages for session {session_id}: {e}")
        
        # Delete feedback associated with this session (JSON mode)
        try:
            from utils.feedback_manager import FeedbackManager
            feedback_mgr = FeedbackManager()
            # Get all feedback for this session
            all_feedback = feedback_mgr.get_feedback_list(limit=None)  # Get all feedback
            feedback_to_delete = [f for f in all_feedback if f.get("session_id") == session_id]
            
            if feedback_to_delete:
                # Remove feedback entries from the list
                with feedback_mgr._lock:
                    feedback_mgr._feedback = [
                        f for f in feedback_mgr._feedback 
                        if f.get("session_id") != session_id
                    ]
                    feedback_mgr._save_data()
                print(f"✅ Deleted {len(feedback_to_delete)} feedback entry/entries for session {session_id}")
        except Exception as e:
            print(f"Warning: Could not delete feedback for session {session_id}: {e}")
        
        # Now delete session metadata
        with self._lock:
            if session_id in self._metadata:
                del self._metadata[session_id]
                # Save to file after deletion
                self._save_sessions()
                print(f"✅ Session {session_id} deleted from JSON. Associated tickets were closed but preserved.")
                return True
            else:
                # Session doesn't exist in JSON, but we still cleaned up related data
                # This is idempotent - return True even if session was already deleted
                print(f"ℹ️  Session {session_id} not found in JSON (may have been already deleted). Related data cleaned up.")
                return True


# Global session metadata instance
session_metadata = SessionMetadata()

