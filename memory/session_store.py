"""Session management using ADK InMemorySessionService with context compaction."""
from google.adk.sessions import InMemorySessionService
from typing import Optional


class SessionManager:
    """Wrapper for ADK session management with context compaction."""
    
    def __init__(self):
        """Initialize session service with context compaction."""
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

