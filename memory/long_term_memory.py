"""
Long-Term Memory Management with Automatic Ingestion

This module provides long-term memory capabilities that persist across sessions,
enabling the agent to learn from past interactions and provide personalized service.

Key Concepts:
- Sessions: Short-term conversation context (current conversation)
- Memory: Long-term persistent knowledge (across all conversations)
- Ingestion: Process of converting session data into long-term memory

Memory Consolidation:
After a session ends, key information can be ingested into long-term memory,
allowing the agent to remember:
- Customer preferences
- Past issues and resolutions
- Sentiment history
- Common patterns

This enables personalized service and faster resolution of recurring issues.
"""
from google.adk.memory import InMemoryMemoryService
from typing import Optional, Dict, Any
from google.genai import types


class MemoryManager:
    """
    Memory Manager with Automatic Ingestion
    
    Manages long-term memory storage and provides methods to ingest
    session data into persistent memory.
    
    Usage:
        memory_manager = MemoryManager()
        service = memory_manager.get_service()
        await memory_manager.ingest_session_data(...)
    """
    
    def __init__(self):
        """
        Initialize memory service.
        
        Uses InMemoryMemoryService for demonstration. In production,
        use a persistent storage backend like DatabaseMemoryService
        or Vertex AI Memory Bank.
        """
        self.memory_service = InMemoryMemoryService()
    
    def get_service(self) -> InMemoryMemoryService:
        """
        Get the underlying memory service.
        
        Returns:
            MemoryService instance
        """
        return self.memory_service
    
    async def ingest_session_data(
        self,
        app_name: str,
        user_id: str,
        session_id: str,
        session_service
    ) -> None:
        """
        Ingest session data into long-term memory.
        
        This demonstrates memory consolidation - converting session
        conversations into long-term knowledge.
        
        Args:
            app_name: Application name
            user_id: User ID
            session_id: Session ID to ingest
            session_service: Session service to retrieve session data
        """
        try:
            # Get session data
            session = await session_service.get_session(
                app_name=app_name,
                user_id=user_id,
                session_id=session_id
            )
            
            if session and session.events:
                # Extract key information from session
                # In production, this would use more sophisticated extraction
                summary = f"Customer {user_id} had a support session about various topics."
                
                # Ingest into memory
                await self.memory_service.ingest(
                    app_name=app_name,
                    user_id=user_id,
                    content=types.Content(
                        role="user",
                        parts=[types.Part(text=summary)]
                    )
                )
        except Exception as e:
            # Log error but don't fail
            print(f"Error ingesting session data: {e}")


# Global memory manager instance
memory_manager = MemoryManager()

