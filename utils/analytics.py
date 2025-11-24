"""
Analytics Utilities

Tracks user interactions, feedback, and performance metrics.
Now uses Supabase for persistence instead of in-memory storage.
"""
from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict
import threading
import json


class Analytics:
    """
    Thread-safe analytics tracker.
    
    Tracks:
    - User interactions
    - Response quality (if feedback provided)
    - Query patterns
    - Agent performance
    """
    
    def __init__(self):
        """Initialize analytics tracker."""
        self._interactions: List[Dict] = []
        self._feedback: Dict[str, Dict] = {}
        self._query_patterns: Dict[str, int] = defaultdict(int)
        self._agent_performance: Dict[str, Dict] = defaultdict(lambda: {"calls": 0, "errors": 0})
        self._lock = threading.Lock()
    
    def log_interaction(
        self,
        user_id: str,
        query: str,
        response: str,
        agent_used: Optional[str] = None,
        response_time: Optional[float] = None,
        session_id: Optional[str] = None
    ) -> None:
        """
        Log a user interaction to Supabase (or in-memory if Supabase disabled).
        
        Args:
            user_id: User identifier
            query: User query
            response: Agent response
            agent_used: Which agent handled the query
            response_time: Response time in seconds
            session_id: Optional session identifier
        """
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "query": query[:200],  # Truncate for storage
            "response_length": len(response),
            "agent_used": agent_used,
            "response_time": response_time,
            "session_id": session_id
        }
        
        # Try to save to Supabase first
        try:
            from utils.supabase_client import SUPABASE_ENABLED, log_analytics_interaction
            if SUPABASE_ENABLED:
                log_analytics_interaction(
                    user_id=user_id,
                    session_id=session_id,
                    query=query[:200],
                    response_length=len(response),
                    agent_used=agent_used,
                    response_time=response_time
                )
                # Still keep in-memory for quick access
                with self._lock:
                    self._interactions.append(interaction)
                    # Track query patterns (first few words)
                    query_words = query.lower().split()[:3]
                    pattern = " ".join(query_words)
                    self._query_patterns[pattern] += 1
                    # Track agent performance
                    if agent_used:
                        self._agent_performance[agent_used]["calls"] += 1
                return
        except Exception as e:
            print(f"Warning: Failed to log interaction to Supabase: {e}")
        
        # Fallback to in-memory storage
        with self._lock:
            self._interactions.append(interaction)
            
            # Track query patterns (first few words)
            query_words = query.lower().split()[:3]
            pattern = " ".join(query_words)
            self._query_patterns[pattern] += 1
            
            # Track agent performance
            if agent_used:
                self._agent_performance[agent_used]["calls"] += 1
    
    def log_feedback(
        self,
        session_id: str,
        feedback_type: str,
        rating: Optional[int] = None,
        comment: Optional[str] = None
    ) -> None:
        """
        Log user feedback.
        
        Args:
            session_id: Session identifier
            feedback_type: "thumbs_up", "thumbs_down", or "rating"
            rating: Numeric rating (1-5) if feedback_type is "rating"
            comment: Optional comment
        """
        with self._lock:
            self._feedback[session_id] = {
                "timestamp": datetime.now().isoformat(),
                "type": feedback_type,
                "rating": rating,
                "comment": comment
            }
    
    def get_stats(self) -> Dict:
        """
        Get analytics statistics.
        
        Returns:
            Dictionary with analytics data
        """
        with self._lock:
            return {
                "total_interactions": len(self._interactions),
                "total_feedback": len(self._feedback),
                "top_query_patterns": dict(sorted(
                    self._query_patterns.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]),
                "agent_performance": dict(self._agent_performance),
                "recent_interactions": self._interactions[-10:] if self._interactions else []
            }
    
    def reset(self) -> None:
        """Reset all analytics data."""
        with self._lock:
            self._interactions.clear()
            self._feedback.clear()
            self._query_patterns.clear()
            self._agent_performance.clear()


# Global analytics instance
analytics = Analytics()

