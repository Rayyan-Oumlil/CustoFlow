"""
Conversation History Management

Stores conversation history beyond session scope for analytics and context.
"""
from typing import List, Dict, Optional
from datetime import datetime
from collections import defaultdict
import threading
import json
from pathlib import Path


# File path for persistent storage
HISTORY_FILE = Path(__file__).parent.parent / "data" / "conversation_history.json"


def _load_history() -> Dict[str, List[Dict]]:
    """Load conversation history from file."""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Convert string keys back to defaultdict structure
                history = defaultdict(list)
                for user_id, messages in data.items():
                    history[user_id] = messages
                return history
        except Exception:
            return defaultdict(list)
    return defaultdict(list)


def _save_history(history: Dict[str, List[Dict]]) -> None:
    """Save conversation history to file."""
    try:
        # Ensure data directory exists
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert defaultdict to regular dict for JSON serialization
        data = dict(history)
        
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass  # Silently fail if save fails


class ConversationHistory:
    """
    Thread-safe conversation history storage with file persistence.
    
    In production, this would use a database (PostgreSQL, MongoDB, etc.)
    """
    
    def __init__(self):
        """Initialize conversation history storage."""
        self._history: Dict[str, List[Dict]] = _load_history()
        self._lock = threading.Lock()
        self._save_counter = 0  # Save every N messages for performance
    
    def add_message(
        self,
        user_id: str,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Add a message to conversation history.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            role: "user" or "assistant"
            content: Message content
            metadata: Optional metadata (agent used, response time, etc.)
        """
        # Essayer Supabase d'abord
        try:
            from utils.supabase_client import SUPABASE_ENABLED, add_message as supabase_add_message
            if SUPABASE_ENABLED:
                supabase_add_message(user_id, session_id, role, content, metadata)
                return  # Succès, on ne sauvegarde pas en JSON
        except Exception:
            pass  # Fallback vers JSON
        
        # Fallback vers JSON
        with self._lock:
            message = {
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "role": role,
                "content": content[:1000],  # Truncate for storage
                "metadata": metadata or {}
            }
            self._history[user_id].append(message)
            self._save_counter += 1
            
            # Save to file every 5 messages for performance
            if self._save_counter >= 5:
                self._save_counter = 0
                _save_history(self._history)
    
    def get_history(
        self,
        user_id: str,
        limit: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Get conversation history for a user.
        
        Args:
            user_id: User identifier (ignored if session_id is provided)
            limit: Maximum number of messages to return
            session_id: Optional session filter (if provided, user_id is ignored)
            
        Returns:
            List of conversation messages
        """
        # Essayer Supabase d'abord
        try:
            from utils.supabase_client import SUPABASE_ENABLED, get_messages as supabase_get_messages
            if SUPABASE_ENABLED:
                # If session_id is provided, user_id will be ignored in get_messages
                result = supabase_get_messages(user_id, session_id, limit or 100)
                if result is not None:  # Check for None, not just truthy (empty list is valid)
                    # Convertir le format Supabase vers le format attendu
                    formatted = []
                    for msg in result:
                        formatted_msg = {
                            "timestamp": msg.get("timestamp"),
                            "session_id": msg.get("session_id"),
                            "role": msg.get("role"),
                            "content": msg.get("content"),
                            "metadata": msg.get("metadata", {})
                        }
                        formatted.append(formatted_msg)
                    return formatted
        except Exception:
            pass  # Fallback vers JSON
        
        # Fallback vers JSON
        with self._lock:
            # If session_id is provided, search across ALL users (ignore user_id)
            # This handles cases where user_id changed between sessions
            if session_id:
                # Search across all user histories for this session_id
                history = []
                for user_msgs in self._history.values():
                    for msg in user_msgs:
                        if msg.get("session_id") == session_id:
                            history.append(msg)
                # Sort by timestamp
                history.sort(key=lambda x: x.get("timestamp", ""))
            else:
                # If no session_id, filter by user_id only
                history = self._history.get(user_id, [])
            
            # Apply limit
            if limit:
                history = history[-limit:]
            
            return history
    
    def get_user_sessions(self, user_id: str) -> List[str]:
        """
        Get all session IDs for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of session IDs
        """
        with self._lock:
            sessions = set()
            for msg in self._history.get(user_id, []):
                sessions.add(msg.get("session_id"))
            return list(sessions)
    
    def clear_history(self, user_id: Optional[str] = None) -> None:
        """
        Clear conversation history.
        
        Args:
            user_id: Optional user ID to clear specific user's history
        """
        with self._lock:
            if user_id:
                if user_id in self._history:
                    del self._history[user_id]
            else:
                self._history.clear()
            _save_history(self._history)


# Global conversation history instance
conversation_history = ConversationHistory()

