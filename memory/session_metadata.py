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
        name: Optional[str] = None
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
        with self._lock:
            if session_id not in self._metadata:
                self._metadata[session_id] = {
                    "session_id": session_id,
                    "user_id": user_id,
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
    
    def get_user_sessions(self, user_id: str) -> list[Dict]:
        """
        Get all sessions for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of session metadata dictionaries
        """
        with self._lock:
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
        with self._lock:
            if session_id in self._metadata:
                del self._metadata[session_id]
                # Save to file after deletion
                self._save_sessions()
                return True
            return False


# Global session metadata instance
session_metadata = SessionMetadata()

