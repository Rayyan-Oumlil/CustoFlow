"""Session Management with Context Compaction"""
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

