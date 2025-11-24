"""
Client Supabase pour remplacer les fichiers JSON

Ce module fournit les mêmes fonctions que les modules JSON
mais utilise Supabase comme backend.
"""
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    from supabase import create_client, Client
    from dotenv import load_dotenv
    
    # Charger les variables d'environnement
    load_dotenv()
    
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    if SUPABASE_URL and SUPABASE_KEY:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        SUPABASE_ENABLED = True
    else:
        SUPABASE_ENABLED = False
        print("⚠️  Supabase non configuré. Utilisation des fichiers JSON.")
except ImportError:
    SUPABASE_ENABLED = False
    print("⚠️  Supabase non installé. Utilisation des fichiers JSON.")


# ============================================================================
# Sessions
# ============================================================================

def get_session(session_id: str) -> Optional[Dict]:
    """Récupérer une session par ID."""
    if not SUPABASE_ENABLED:
        # Fallback vers JSON
        from memory.session_metadata import session_metadata
        return session_metadata.get_session(session_id)
    
    try:
        result = supabase.table("sessions").select("*").eq("session_id", session_id).execute()
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        print(f"Erreur Supabase get_session: {e}")
        return None


def create_session(session_id: str, user_id: str, name: Optional[str] = None) -> Dict:
    """Créer une nouvelle session."""
    if not SUPABASE_ENABLED:
        from memory.session_metadata import session_metadata
        return session_metadata.create_session(session_id, user_id, name)
    
    try:
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "name": name or f"Session {session_id[-8:]}",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "message_count": 0
        }
        
        result = supabase.table("sessions").upsert(session_data).execute()
        return result.data[0] if result.data else session_data
    except Exception as e:
        print(f"Erreur Supabase create_session: {e}")
        return {}


def get_user_sessions(user_id: str) -> List[Dict]:
    """Récupérer toutes les sessions d'un utilisateur."""
    if not SUPABASE_ENABLED:
        from memory.session_metadata import session_metadata
        return session_metadata.get_user_sessions(user_id)
    
    try:
        result = supabase.table("sessions").select("*").eq("user_id", user_id).order("updated_at", desc=True).execute()
        return result.data or []
    except Exception as e:
        print(f"Erreur Supabase get_user_sessions: {e}")
        return []


# ============================================================================
# Messages
# ============================================================================

def add_message(
    user_id: str,
    session_id: str,
    role: str,
    content: str,
    metadata: Optional[Dict] = None
) -> None:
    """Ajouter un message à l'historique."""
    if not SUPABASE_ENABLED:
        from memory.conversation_history import conversation_history
        conversation_history.add_message(user_id, session_id, role, content, metadata)
        return
    
    try:
        message_data = {
            "user_id": user_id,
            "session_id": session_id,
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        
        supabase.table("messages").insert(message_data).execute()
    except Exception as e:
        print(f"Erreur Supabase add_message: {e}")


def get_messages(user_id: str, session_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
    """Récupérer les messages d'un utilisateur."""
    if not SUPABASE_ENABLED:
        from memory.conversation_history import conversation_history
        return conversation_history.get_history(user_id, limit=limit, session_id=session_id)
    
    try:
        query = supabase.table("messages").select("*").eq("user_id", user_id)
        
        if session_id:
            query = query.eq("session_id", session_id)
        
        result = query.order("timestamp", desc=False).limit(limit).execute()
        return result.data or []
    except Exception as e:
        print(f"Erreur Supabase get_messages: {e}")
        return []


# ============================================================================
# Tickets
# ============================================================================

def create_ticket(
    issue: str,
    customer_id: Optional[str] = None,
    priority: str = "normal",
    session_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> Dict:
    """Créer un ticket."""
    if not SUPABASE_ENABLED:
        from tools.ticket_tool import create_ticket as create_ticket_json
        return create_ticket_json(issue, customer_id, priority, session_id, user_id)
    
    try:
        import uuid
        ticket_id = f"TICKET-{uuid.uuid4().hex[:8].upper()}"
        
        ticket_data = {
            "ticket_id": ticket_id,
            "customer_id": customer_id or "unknown",
            "user_id": user_id,
            "session_id": session_id,
            "issue": issue,
            "priority": priority,
            "status": "open",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        result = supabase.table("tickets").insert(ticket_data).execute()
        return {
            "status": "success",
            "ticket_id": ticket_id,
            "message": f"Ticket {ticket_id} has been created."
        }
    except Exception as e:
        print(f"Erreur Supabase create_ticket: {e}")
        return {"status": "error", "error_message": str(e)}


def get_tickets(session_id: Optional[str] = None) -> List[Dict]:
    """Récupérer les tickets."""
    if not SUPABASE_ENABLED:
        from tools.ticket_tool import get_all_tickets
        tickets = get_all_tickets()
        if session_id:
            return [t for t in tickets.values() if t.get("session_id") == session_id]
        return list(tickets.values())
    
    try:
        query = supabase.table("tickets").select("*")
        
        if session_id:
            query = query.eq("session_id", session_id)
        
        result = query.order("created_at", desc=True).execute()
        return result.data or []
    except Exception as e:
        print(f"Erreur Supabase get_tickets: {e}")
        return []


# ============================================================================
# Orders
# ============================================================================

def get_orders(customer_id: Optional[str] = None) -> List[Dict]:
    """Récupérer les commandes."""
    if not SUPABASE_ENABLED:
        from tools.order_tool import get_all_orders
        orders = get_all_orders()
        if customer_id:
            return [o for o in orders if o.get("customer_id") == customer_id]
        return orders
    
    try:
        query = supabase.table("orders").select("*")
        
        if customer_id:
            query = query.eq("customer_id", customer_id)
        
        result = query.order("created_at", desc=True).execute()
        return result.data or []
    except Exception as e:
        print(f"Erreur Supabase get_orders: {e}")
        return []


# ============================================================================
# Conversation Summaries
# ============================================================================

def save_conversation_summary(
    summary_key: str,
    user_id: str,
    session_id: str,
    summary: str,
    key_points: Optional[Dict] = None,
    sentiment: Optional[Dict] = None,
    action_items: Optional[List] = None,
    next_steps: Optional[List] = None,
    summary_length: str = "medium",
    ticket_id: Optional[str] = None
) -> Dict:
    """Sauvegarder un résumé de conversation."""
    if not SUPABASE_ENABLED:
        # Fallback vers JSON
        from utils.conversation_summarizer import _load_summaries, _save_summaries
        summaries = _load_summaries()
        summaries[summary_key] = {
            "summary": summary,
            "key_points": key_points or {},
            "sentiment": sentiment or {},
            "action_items": action_items or [],
            "next_steps": next_steps or [],
            "timestamp": datetime.now().isoformat(),
            "ticket_id": ticket_id
        }
        _save_summaries(summaries)
        return summaries[summary_key]
    
    try:
        summary_data = {
            "summary_key": summary_key,
            "user_id": user_id,
            "session_id": session_id,
            "summary": summary,
            "key_points": key_points or {},
            "sentiment": sentiment or {},
            "action_items": action_items or [],
            "next_steps": next_steps or [],
            "summary_length": summary_length,
            "ticket_id": ticket_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        result = supabase.table("conversation_summaries").upsert(summary_data).execute()
        return result.data[0] if result.data else summary_data
    except Exception as e:
        print(f"Erreur Supabase save_conversation_summary: {e}")
        return {}


def get_conversation_summary(summary_key: str) -> Optional[Dict]:
    """Récupérer un résumé de conversation par clé."""
    if not SUPABASE_ENABLED:
        from utils.conversation_summarizer import _load_summaries
        summaries = _load_summaries()
        return summaries.get(summary_key)
    
    try:
        result = supabase.table("conversation_summaries").select("*").eq("summary_key", summary_key).execute()
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        print(f"Erreur Supabase get_conversation_summary: {e}")
        return None


def get_session_summaries(session_id: str) -> List[Dict]:
    """Récupérer tous les résumés d'une session."""
    if not SUPABASE_ENABLED:
        from utils.conversation_summarizer import _load_summaries
        summaries = _load_summaries()
        return [s for k, s in summaries.items() if k.endswith(f"_{session_id}")]
    
    try:
        result = supabase.table("conversation_summaries").select("*").eq("session_id", session_id).order("created_at", desc=True).execute()
        return result.data or []
    except Exception as e:
        print(f"Erreur Supabase get_session_summaries: {e}")
        return []


# ============================================================================
# Feedback
# ============================================================================

def create_feedback(
    session_id: str,
    user_id: str,
    feedback_type: str,
    rating: Optional[int] = None,
    comment: Optional[str] = None,
    reason: Optional[str] = None,
    category: Optional[str] = None,
    agent_used: Optional[str] = None,
    ticket_id: Optional[str] = None,
    sentiment_score: Optional[float] = None
) -> Dict:
    """Créer un feedback."""
    if not SUPABASE_ENABLED:
        # Fallback vers JSON
        from utils.feedback_manager import FeedbackManager
        feedback_mgr = FeedbackManager()
        return feedback_mgr.add_feedback(
            session_id=session_id,
            user_id=user_id,
            feedback_type=feedback_type,
            rating=rating,
            comment=comment,
            reason=reason,
            category=category,
            agent_used=agent_used
        )
    
    try:
        import uuid
        feedback_id = f"FEEDBACK-{uuid.uuid4().hex[:8].upper()}"
        
        feedback_data = {
            "feedback_id": feedback_id,
            "session_id": session_id,
            "user_id": user_id,
            "ticket_id": ticket_id,
            "feedback_type": feedback_type,
            "rating": rating,
            "comment": comment,
            "reason": reason,
            "category": category,
            "agent_used": agent_used,
            "sentiment_score": sentiment_score,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        result = supabase.table("feedback").insert(feedback_data).execute()
        return {
            "status": "success",
            "feedback_id": feedback_id,
            **feedback_data
        }
    except Exception as e:
        print(f"Erreur Supabase create_feedback: {e}")
        return {"status": "error", "error_message": str(e)}


def get_feedback(session_id: Optional[str] = None, user_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
    """Récupérer les feedbacks."""
    if not SUPABASE_ENABLED:
        from utils.feedback_manager import FeedbackManager
        feedback_mgr = FeedbackManager()
        feedbacks = feedback_mgr.get_all_feedback()
        if session_id:
            feedbacks = [f for f in feedbacks if f.get("session_id") == session_id]
        if user_id:
            feedbacks = [f for f in feedbacks if f.get("user_id") == user_id]
        return feedbacks[:limit]
    
    try:
        query = supabase.table("feedback").select("*")
        
        if session_id:
            query = query.eq("session_id", session_id)
        if user_id:
            query = query.eq("user_id", user_id)
        
        result = query.order("created_at", desc=True).limit(limit).execute()
        return result.data or []
    except Exception as e:
        print(f"Erreur Supabase get_feedback: {e}")
        return []


def get_feedback_stats() -> Dict:
    """Récupérer les statistiques de feedback."""
    if not SUPABASE_ENABLED:
        from utils.feedback_manager import FeedbackManager
        feedback_mgr = FeedbackManager()
        return feedback_mgr.get_insights()
    
    try:
        # Compter les feedbacks par type
        result = supabase.table("feedback").select("feedback_type").execute()
        feedbacks = result.data or []
        
        stats = {
            "total": len(feedbacks),
            "by_type": {},
            "average_rating": 0.0,
            "positive_count": 0,
            "negative_count": 0
        }
        
        ratings = []
        for fb in feedbacks:
            fb_type = fb.get("feedback_type", "unknown")
            stats["by_type"][fb_type] = stats["by_type"].get(fb_type, 0) + 1
            
            if fb_type in ["positive", "thumbs_up"]:
                stats["positive_count"] += 1
            elif fb_type in ["negative", "thumbs_down"]:
                stats["negative_count"] += 1
            
            if fb.get("rating"):
                ratings.append(fb["rating"])
        
        if ratings:
            stats["average_rating"] = sum(ratings) / len(ratings)
        
        return stats
    except Exception as e:
        print(f"Erreur Supabase get_feedback_stats: {e}")
        return {}


# ============================================================================
# Analytics
# ============================================================================

def log_analytics_interaction(
    user_id: str,
    session_id: Optional[str] = None,
    query: Optional[str] = None,
    response_length: Optional[int] = None,
    agent_used: Optional[str] = None,
    response_time: Optional[float] = None
) -> bool:
    """Log an analytics interaction to Supabase."""
    if not SUPABASE_ENABLED:
        return False
    
    try:
        interaction_data = {
            "user_id": user_id,
            "session_id": session_id,
            "query": query,
            "response_length": response_length,
            "agent_used": agent_used,
            "response_time": response_time,
            "timestamp": datetime.now().isoformat()
        }
        
        result = supabase.table("analytics_interactions").insert(interaction_data).execute()
        return True
    except Exception as e:
        print(f"Error Supabase log_analytics_interaction: {e}")
        return False


def get_analytics_interactions(
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    limit: int = 100
) -> List[Dict]:
    """Get analytics interactions from Supabase."""
    if not SUPABASE_ENABLED:
        return []
    
    try:
        query = supabase.table("analytics_interactions").select("*")
        
        if user_id:
            query = query.eq("user_id", user_id)
        if session_id:
            query = query.eq("session_id", session_id)
        
        result = query.order("timestamp", desc=True).limit(limit).execute()
        return result.data or []
    except Exception as e:
        print(f"Error Supabase get_analytics_interactions: {e}")
        return []


def get_analytics_stats() -> Dict:
    """Get analytics statistics from Supabase."""
    if not SUPABASE_ENABLED:
        return {}
    
    try:
        # Get total interactions
        total_result = supabase.table("analytics_interactions").select("id", count="exact").limit(1).execute()
        total_interactions = total_result.count if hasattr(total_result, 'count') and total_result.count is not None else 0
        
        # Get agent performance
        agent_result = supabase.table("analytics_interactions").select("agent_used").execute()
        interactions = agent_result.data or []
        
        agent_performance = {}
        for interaction in interactions:
            agent = interaction.get("agent_used")
            if agent:
                if agent not in agent_performance:
                    agent_performance[agent] = {"calls": 0, "errors": 0}
                agent_performance[agent]["calls"] += 1
        
        # Get query patterns (first 3 words)
        query_patterns = {}
        for interaction in interactions:
            query = interaction.get("query", "")
            if query:
                query_words = query.lower().split()[:3]
                pattern = " ".join(query_words)
                query_patterns[pattern] = query_patterns.get(pattern, 0) + 1
        
        # Get top query patterns
        top_patterns = dict(sorted(
            query_patterns.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10])
        
        return {
            "total_interactions": total_interactions,
            "agent_performance": agent_performance,
            "top_query_patterns": top_patterns
        }
    except Exception as e:
        print(f"Error Supabase get_analytics_stats: {e}")
        return {}

