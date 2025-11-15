"""
Conversation History Management

Stores conversation history beyond session scope for analytics and context.
"""
from typing import List, Dict, Optional
from datetime import datetime
from collections import defaultdict
import threading
import json


class ConversationHistory:
    """
    Thread-safe conversation history storage.
    
    In production, this would use a database (PostgreSQL, MongoDB, etc.)
    """
    
    def __init__(self):
        """Initialize conversation history storage."""
        self._history: Dict[str, List[Dict]] = defaultdict(list)
        self._lock = threading.Lock()
    
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
        with self._lock:
            message = {
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "role": role,
                "content": content[:1000],  # Truncate for storage
                "metadata": metadata or {}
            }
            self._history[user_id].append(message)
    
    def get_history(
        self,
        user_id: str,
        limit: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Get conversation history for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of messages to return
            session_id: Optional session filter
            
        Returns:
            List of conversation messages
        """
        with self._lock:
            history = self._history.get(user_id, [])
            
            # Filter by session if specified
            if session_id:
                history = [msg for msg in history if msg.get("session_id") == session_id]
            
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


# Global conversation history instance
conversation_history = ConversationHistory()

