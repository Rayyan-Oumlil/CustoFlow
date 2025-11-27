"""
Tests for long-term memory management.
Tests memory ingestion and consolidation.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from memory.long_term_memory import MemoryManager


def test_memory_manager_initialization():
    """Test MemoryManager initialization."""
    manager = MemoryManager()
    assert manager.memory_service is not None
    assert hasattr(manager, 'get_service')


def test_get_service():
    """Test getting memory service."""
    manager = MemoryManager()
    service = manager.get_service()
    assert service is not None


@pytest.mark.asyncio
async def test_ingest_session_data_success():
    """Test successful session data ingestion."""
    manager = MemoryManager()
    
    # Mock session service
    mock_session = Mock()
    mock_session.events = [Mock()]
    
    mock_session_service = AsyncMock()
    mock_session_service.get_session = AsyncMock(return_value=mock_session)
    
    # Mock memory service ingest
    manager.memory_service.ingest = AsyncMock()
    
    await manager.ingest_session_data(
        app_name="test_app",
        user_id="user_001",
        session_id="session_001",
        session_service=mock_session_service
    )
    
    # Verify ingest was called
    manager.memory_service.ingest.assert_called_once()


@pytest.mark.asyncio
async def test_ingest_session_data_no_session():
    """Test ingestion when session doesn't exist."""
    manager = MemoryManager()
    
    mock_session_service = AsyncMock()
    mock_session_service.get_session = AsyncMock(return_value=None)
    
    # Should not raise error
    await manager.ingest_session_data(
        app_name="test_app",
        user_id="user_001",
        session_id="session_001",
        session_service=mock_session_service
    )
    
    # Ingest should not be called
    manager.memory_service.ingest.assert_not_called()


@pytest.mark.asyncio
async def test_ingest_session_data_no_events():
    """Test ingestion when session has no events."""
    manager = MemoryManager()
    
    mock_session = Mock()
    mock_session.events = []
    
    mock_session_service = AsyncMock()
    mock_session_service.get_session = AsyncMock(return_value=mock_session)
    
    await manager.ingest_session_data(
        app_name="test_app",
        user_id="user_001",
        session_id="session_001",
        session_service=mock_session_service
    )
    
    # Ingest should not be called (no events)
    manager.memory_service.ingest.assert_not_called()


@pytest.mark.asyncio
async def test_ingest_session_data_exception():
    """Test ingestion with exception (should not fail)."""
    manager = MemoryManager()
    
    mock_session_service = AsyncMock()
    mock_session_service.get_session = AsyncMock(side_effect=Exception("Error"))
    
    # Should not raise error
    await manager.ingest_session_data(
        app_name="test_app",
        user_id="user_001",
        session_id="session_001",
        session_service=mock_session_service
    )

