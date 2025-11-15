"""Metrics collection for observability."""
from typing import Dict
from collections import defaultdict
import threading


class Metrics:
    """Thread-safe metrics collector."""
    
    def __init__(self):
        """Initialize metrics with thread-safe storage."""
        self._counters: Dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()
    
    def increment(self, metric_name: str, value: int = 1) -> None:
        """
        Increment a counter metric.
        
        Args:
            metric_name: Name of the metric
            value: Amount to increment (default: 1)
        """
        with self._lock:
            self._counters[metric_name] += value
    
    def get(self, metric_name: str) -> int:
        """
        Get current value of a metric.
        
        Args:
            metric_name: Name of the metric
            
        Returns:
            Current metric value
        """
        with self._lock:
            return self._counters.get(metric_name, 0)
    
    def get_counts(self) -> Dict[str, int]:
        """
        Get all metric counts.
        
        Returns:
            Dictionary of all metrics
        """
        with self._lock:
            return dict(self._counters)
    
    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()


# Global metrics instance
metrics = Metrics()

