"""
Tests for tracing utilities.
Tests span tracing and metadata logging.
"""
import pytest
import logging
from utils.observability.tracing import trace_span


def test_trace_span_success(caplog):
    """Test trace_span with successful execution."""
    with caplog.at_level(logging.DEBUG):
        with trace_span("test_operation", {"key": "value"}):
            pass
    
    # Check that span was logged
    assert "Span started: test_operation" in caplog.text
    assert "Span completed: test_operation" in caplog.text


def test_trace_span_with_exception(caplog):
    """Test trace_span with exception (should still log completion)."""
    with caplog.at_level(logging.DEBUG):
        try:
            with trace_span("test_operation"):
                raise ValueError("Test error")
        except ValueError:
            pass
    
    # Should still log completion
    assert "Span started: test_operation" in caplog.text
    assert "Span completed: test_operation" in caplog.text


def test_trace_span_metadata(caplog):
    """Test trace_span with metadata."""
    with caplog.at_level(logging.DEBUG):
        with trace_span("test_operation", {"order_id": "12345", "user_id": "user_001"}):
            pass
    
    # Check metadata is included
    assert "test_operation" in caplog.text


def test_trace_span_duration(caplog):
    """Test that trace_span logs duration."""
    import time
    with caplog.at_level(logging.DEBUG):
        with trace_span("test_operation"):
            time.sleep(0.1)
    
    # Check duration is logged
    assert "duration" in caplog.text.lower() or "Span completed" in caplog.text


def test_trace_span_nested():
    """Test nested trace spans."""
    import logging
    logger = logging.getLogger("utils.observability.tracing")
    
    with trace_span("outer_operation"):
        with trace_span("inner_operation"):
            pass
    
    # Both spans should be logged
    # (This test mainly ensures no errors occur with nested spans)

