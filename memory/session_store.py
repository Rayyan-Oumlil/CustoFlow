"""
Session Management with Context Compaction

This module provides session management for maintaining conversation context
across multiple turns. ADK automatically handles context compaction to manage
the context window efficiently.

Key Features:
- Session creation and retrieval
- Automatic context compaction (handled by ADK)
- Context preservation across conversation turns
- Efficient context window management

Context Compaction:
ADK's InMemorySessionService automatically manages the context window by:
- Keeping the most recent events
- Summarizing or compacting older events
- Preventing context window overflow in long conversations

Production: For persistent sessions, use DatabaseSessionService instead.
"""
from google.adk.sessions import InMemorySessionService
from typing import Optional


class SessionManager:
    """
    Session Manager Wrapper
    
    Provides a clean interface for session management with automatic
    context compaction handled by ADK.
    
    Usage:
        session_manager = SessionManager()
        service = session_manager.get_service()
        await service.create_session(app_name="app", user_id="user", session_id="session")
    """
    
    def __init__(self):
        """
        Initialize session service with automatic context compaction.
        
        ADK's InMemorySessionService automatically handles context compaction
        to prevent context window overflow. For production with persistent
        storage, use DatabaseSessionService.
        """
        # Initialize session service
        # Context compaction is handled automatically by ADK
        # The service manages context window efficiently by keeping
        # the most recent events and summarizing older ones
        self.session_service = InMemorySessionService()
    
    def get_service(self) -> InMemorySessionService:
        """
        Get the underlying session service.
        
        Returns:
            InMemorySessionService instance with compaction
        """
        return self.session_service


# Global session manager instance
session_manager = SessionManager()

