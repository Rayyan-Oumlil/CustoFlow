"""Tracing utilities for request tracking."""
from contextlib import contextmanager
from typing import Optional
import time
import logging

logger = logging.getLogger(__name__)


@contextmanager
def trace_span(name: str, metadata: Optional[dict] = None):
    """
    Context manager for tracing a span of execution.
    
    Args:
        name: Name of the span
        metadata: Optional metadata to log
        
    Example:
        with trace_span("order_lookup", {"order_id": "12345"}):
            # Do work
            pass
    """
    start_time = time.time()
    logger.debug(f"Span started: {name}", extra={"metadata": metadata or {}})
    
    try:
        yield
    finally:
        duration = time.time() - start_time
        logger.debug(
            f"Span completed: {name} (duration: {duration:.3f}s)",
            extra={"metadata": metadata or {}, "duration": duration}
        )

