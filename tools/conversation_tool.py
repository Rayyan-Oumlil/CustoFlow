"""
Conversation Tools for Agents

Tools that allow agents to access and summarize conversation history.
"""
from typing import Dict, Optional
import sys
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Context for storing session info (set by API server)
_conversation_contexts: Dict[str, Dict] = {}
_context_lock = None

try:
    import threading
    _context_lock = threading.Lock()
except ImportError:
    pass


def set_conversation_context(session_id: Optional[str] = None, user_id: Optional[str] = None):
    """Set conversation context for tools to access."""
    global _conversation_contexts
    if _context_lock:
        with _context_lock:
            if session_id:
                key = f"session_{session_id}"
                _conversation_contexts[key] = {
                    "session_id": session_id,
                    "user_id": user_id
                }
    else:
        if session_id:
            key = f"session_{session_id}"
            _conversation_contexts[key] = {
                "session_id": session_id,
                "user_id": user_id
            }


def get_conversation_context(session_id: Optional[str] = None) -> Dict:
    """Get conversation context."""
    if session_id:
        key = f"session_{session_id}"
        return _conversation_contexts.get(key, {})
    # Return most recent context
    if _conversation_contexts:
        return list(_conversation_contexts.values())[-1]
    return {}


def clear_conversation_context():
    """Clear conversation context."""
    global _conversation_contexts
    if _context_lock:
        with _context_lock:
            _conversation_contexts.clear()
    else:
        _conversation_contexts.clear()


def summarize_conversation(session_id: Optional[str] = None, user_id: Optional[str] = None) -> Dict[str, any]:
    """
    Summarize the current conversation.
    
    This tool allows agents to provide a summary of what has been discussed
    in the conversation so far. Useful when customers ask "what did we talk about?"
    
    Args:
        session_id: Optional session ID (will be retrieved from context if not provided)
        user_id: Optional user ID (will be retrieved from context if not provided)
        
    Returns:
        Dictionary with summary information:
        - Success: {"status": "success", "summary": "...", "key_points": {...}}
        - Error: {"status": "error", "error_message": "..."}
    """
    try:
        # Get context if not provided
        if not session_id or not user_id:
            ctx = get_conversation_context(session_id)
            if not session_id and ctx.get("session_id"):
                session_id = ctx["session_id"]
            if not user_id and ctx.get("user_id"):
                user_id = ctx["user_id"]
        
        if not session_id or not user_id:
            return {
                "status": "error",
                "error_message": "Cannot summarize conversation: session_id and user_id are required. Please provide them or ensure context is set."
            }
        
        # Import summarizer
        from utils.conversation_summarizer import conversation_summarizer
        
        # Generate summary
        result = conversation_summarizer.generate_summary(
            user_id=user_id,
            session_id=session_id,
            summary_length="medium",
            include_sentiment=True
        )
        
        if result.get("status") == "error":
            return result
        
        # Format summary for agent response
        summary_text = result.get("summary", "")
        key_points = result.get("key_points", {})
        sentiment = result.get("sentiment", {})
        action_items = result.get("action_items", [])
        
        # Build a user-friendly summary
        formatted_summary = f"Here's a summary of our conversation:\n\n"
        
        if key_points.get("customer_issue"):
            formatted_summary += f"**Main Issue:** {key_points['customer_issue']}\n\n"
        
        if key_points.get("attempted_solutions"):
            formatted_summary += f"**What We've Discussed:** {key_points['attempted_solutions']}\n\n"
        
        if key_points.get("current_status"):
            formatted_summary += f"**Current Status:** {key_points['current_status']}\n\n"
        
        if sentiment.get("sentiment"):
            formatted_summary += f"**Sentiment:** {sentiment.get('sentiment', 'neutral').title()}\n\n"
        
        if action_items:
            formatted_summary += f"**Next Steps:**\n"
            for item in action_items[:3]:  # Limit to 3 items
                formatted_summary += f"- {item}\n"
        
        return {
            "status": "success",
            "summary": formatted_summary,
            "full_summary": summary_text,
            "key_points": key_points,
            "sentiment": sentiment,
            "action_items": action_items
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error summarizing conversation: {str(e)}"
        }


def get_conversation_history(session_id: Optional[str] = None, user_id: Optional[str] = None, limit: int = 20) -> Dict[str, any]:
    """
    Get recent conversation history.
    
    This tool allows agents to see recent messages in the conversation.
    
    Args:
        session_id: Optional session ID (will be retrieved from context if not provided)
        user_id: Optional user ID (will be retrieved from context if not provided)
        limit: Maximum number of messages to retrieve (default: 20)
        
    Returns:
        Dictionary with conversation history:
        - Success: {"status": "success", "messages": [...], "count": N}
        - Error: {"status": "error", "error_message": "..."}
    """
    try:
        # Get context if not provided
        if not session_id or not user_id:
            ctx = get_conversation_context(session_id)
            if not session_id and ctx.get("session_id"):
                session_id = ctx["session_id"]
            if not user_id and ctx.get("user_id"):
                user_id = ctx["user_id"]
        
        if not session_id or not user_id:
            return {
                "status": "error",
                "error_message": "Cannot get conversation history: session_id and user_id are required."
            }
        
        # Get messages from Supabase or JSON
        from utils.supabase_client import SUPABASE_ENABLED, get_messages
        from memory.conversation_history import conversation_history
        
        if SUPABASE_ENABLED:
            messages = get_messages(user_id=user_id, session_id=session_id, limit=limit)
        else:
            messages = conversation_history.get_history(user_id=user_id, session_id=session_id, limit=limit)
        
        # Format messages for display
        formatted_messages = []
        for msg in messages[-limit:]:  # Get last N messages
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", msg.get("created_at", ""))
            
            formatted_messages.append({
                "role": role,
                "content": content[:500],  # Truncate long messages
                "timestamp": timestamp
            })
        
        return {
            "status": "success",
            "messages": formatted_messages,
            "count": len(formatted_messages)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error getting conversation history: {str(e)}"
        }

