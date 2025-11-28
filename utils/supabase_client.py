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
    
    # Charger les variables d'environnement (fichier .env si présent)
    # Note: Dans Cloud Run, les variables sont déjà dans l'environnement
    load_dotenv()
    
    # Récupérer les variables d'environnement (depuis .env ou variables système)
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            SUPABASE_ENABLED = True
            print(f"✅ Supabase activé: {SUPABASE_URL[:30]}...")
        except Exception as e:
            SUPABASE_ENABLED = False
            print(f"⚠️  Erreur initialisation Supabase: {e}. Utilisation des fichiers JSON.")
    else:
        SUPABASE_ENABLED = False
        print("⚠️  Supabase non configuré (SUPABASE_URL ou SUPABASE_KEY manquants). Utilisation des fichiers JSON.")
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
        print(f"Erreur Supabase get_session: {e}. Fallback vers JSON.")
        # Fallback vers JSON si Supabase échoue
        from memory.session_metadata import session_metadata
        return session_metadata.get_session(session_id)


def create_session(session_id: str, user_id: str, name: Optional[str] = None, customer_id: Optional[str] = None) -> Dict:
    """Créer une nouvelle session."""
    if not SUPABASE_ENABLED:
        from memory.session_metadata import session_metadata
        return session_metadata.create_session(session_id, user_id, name, customer_id)
    
    # Normalize customer_id to lowercase to avoid case-sensitivity issues
    # "Cust_001" becomes "cust_001" for consistency
    normalized_customer_id = customer_id.lower() if customer_id else None
    
    try:
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "customer_id": normalized_customer_id,
            "name": name or f"Session {session_id[-8:]}",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "message_count": 0
        }
        
        print(f"Creating session in Supabase: session_id={session_id}, user_id={user_id}, customer_id={normalized_customer_id}")
        
        # First, try to insert the session
        result = supabase.table("sessions").upsert(session_data).execute()
        
        # If customer_id was provided, ensure it's set (in case upsert didn't work correctly)
        if normalized_customer_id:
            if result.data:
                # Double-check and update customer_id if needed
                existing = result.data[0] if result.data else {}
                if existing.get("customer_id") != normalized_customer_id:
                    print(f"Updating customer_id for session {session_id} from {existing.get('customer_id')} to {normalized_customer_id}")
                    supabase.table("sessions").update({"customer_id": normalized_customer_id}).eq("session_id", session_id).execute()
                    existing["customer_id"] = normalized_customer_id
            else:
                # If no data returned, try to update directly
                print(f"Updating customer_id for session {session_id} to {normalized_customer_id} (no data in result)")
                supabase.table("sessions").update({"customer_id": normalized_customer_id}).eq("session_id", session_id).execute()
        
        final_result = result.data[0] if result.data else session_data
        print(f"Session created successfully: customer_id={final_result.get('customer_id')}")
        return final_result
    except Exception as e:
        print(f"Erreur Supabase create_session: {e}. Fallback vers JSON.")
        # Fallback vers JSON si Supabase échoue
        from memory.session_metadata import session_metadata
        return session_metadata.create_session(session_id, user_id, name, customer_id)


def get_user_sessions(user_id: str, customer_id: Optional[str] = None) -> List[Dict]:
    """Récupérer toutes les sessions d'un utilisateur."""
    if not SUPABASE_ENABLED:
        from memory.session_metadata import session_metadata
        return session_metadata.get_user_sessions(user_id, customer_id)
    
    try:
        # If customer_id is provided, prioritize filtering by customer_id
        # This is more reliable than user_id which can change between browsers/sessions
        if customer_id:
            # Get all sessions for this customer_id (case-insensitive)
            customer_id_lower = customer_id.lower()
            result = supabase.table("sessions").select("*").order("updated_at", desc=True).execute()
            sessions = result.data or []
            # Filter by customer_id case-insensitively and optionally by user_id
            filtered_sessions = [
                s for s in sessions 
                if s.get("customer_id") and s.get("customer_id").lower() == customer_id_lower
                and (not user_id or s.get("user_id") == user_id)  # Optionally match user_id if provided
            ]
            print(f"✅ [SUPABASE] Retrieved {len(filtered_sessions)} sessions from Supabase for customer_id={customer_id} (user_id={user_id})")
            return filtered_sessions
        else:
            # If no customer_id, filter by user_id only
            query = supabase.table("sessions").select("*").eq("user_id", user_id)
            result = query.order("updated_at", desc=True).execute()
            sessions = result.data or []
            print(f"✅ [SUPABASE] Retrieved {len(sessions)} sessions from Supabase for user {user_id}")
            return sessions
    except Exception as e:
        print(f"❌ [SUPABASE] Error get_user_sessions: {e}")
        # Fallback to JSON on error
        from memory.session_metadata import session_metadata
        return session_metadata.get_user_sessions(user_id, customer_id)


def close_session(session_id: str) -> bool:
    """Mark a session as inactive/closed."""
    if not SUPABASE_ENABLED:
        # Fallback: store in JSON
        from memory.session_metadata import session_metadata
        return session_metadata.close_session(session_id)
    
    try:
        result = supabase.table("sessions").update({"is_active": False}).eq("session_id", session_id).execute()
        return bool(result.data)
    except Exception as e:
        print(f"Erreur Supabase close_session: {e}")
        return False


def reopen_session(session_id: str) -> bool:
    """Reopen a closed session (mark as active)."""
    if not SUPABASE_ENABLED:
        # Fallback: store in JSON
        from memory.session_metadata import session_metadata
        return session_metadata.reopen_session(session_id)
    
    try:
        result = supabase.table("sessions").update({"is_active": True}).eq("session_id", session_id).execute()
        return bool(result.data)
    except Exception as e:
        print(f"Erreur Supabase reopen_session: {e}")
        return False


def rename_session(session_id: str, new_name: str) -> bool:
    """Rename a session in Supabase."""
    if not SUPABASE_ENABLED:
        from memory.session_metadata import session_metadata
        return session_metadata.rename_session(session_id, new_name)
    
    try:
        result = supabase.table("sessions").update({
            "name": new_name,
            "updated_at": datetime.now().isoformat()
        }).eq("session_id", session_id).execute()
        return len(result.data) > 0 if result.data else False
    except Exception as e:
        print(f"Erreur Supabase rename_session: {e}")
        return False


def increment_message_count(session_id: str) -> None:
    """Increment message count for a session in Supabase."""
    if not SUPABASE_ENABLED:
        from memory.session_metadata import session_metadata
        session_metadata.increment_message_count(session_id)
        return
    
    try:
        # Calculate actual count from messages table
        # Use count="exact" without limit to get accurate count
        msg_result = supabase.table("messages").select("id", count="exact").eq("session_id", session_id).execute()
        actual_count = msg_result.count if hasattr(msg_result, 'count') and msg_result.count is not None else 0
        
        # Update session with actual count
        supabase.table("sessions").update({
            "message_count": actual_count,
            "updated_at": datetime.now().isoformat()
        }).eq("session_id", session_id).execute()
    except Exception as e:
        print(f"Erreur Supabase increment_message_count: {e}")


# ============================================================================
# Messages
# ============================================================================

def add_message(
    user_id: str,
    session_id: str,
    role: str,
    content: str,
    metadata: Optional[Dict] = None,
    is_human_agent: bool = False
) -> None:
    """Ajouter un message à l'historique et mettre à jour le message_count."""
    if not SUPABASE_ENABLED:
        from memory.conversation_history import conversation_history
        metadata = metadata or {}
        if is_human_agent:
            metadata["is_human_agent"] = True
            metadata["agent_used"] = "human_agent"
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
        
        # Add human agent flag to metadata
        if is_human_agent:
            message_data["metadata"]["is_human_agent"] = True
            message_data["metadata"]["agent_used"] = "human_agent"
        
        supabase.table("messages").insert(message_data).execute()
        
        # Update message_count in sessions table
        increment_message_count(session_id)
    except Exception as e:
        print(f"Erreur Supabase add_message: {e}. Fallback vers JSON.")
        # Fallback vers JSON si Supabase échoue
        from memory.conversation_history import conversation_history
        metadata = metadata or {}
        if is_human_agent:
            metadata["is_human_agent"] = True
            metadata["agent_used"] = "human_agent"
        conversation_history.add_message(user_id, session_id, role, content, metadata)


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
        print(f"Erreur Supabase get_messages: {e}. Fallback vers JSON.")
        # Fallback vers JSON si Supabase échoue
        from memory.conversation_history import conversation_history
        return conversation_history.get_history(user_id, limit=limit, session_id=session_id)


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
        
        # Try to get customer_id from session if not provided
        if not customer_id and session_id:
            try:
                session_result = supabase.table("sessions").select("customer_id").eq("session_id", session_id).limit(1).execute()
                if session_result.data and len(session_result.data) > 0:
                    customer_id = session_result.data[0].get("customer_id")
                    if customer_id:
                        print(f"[TICKET] Retrieved customer_id from session in supabase_client: {customer_id}")
            except Exception as e:
                print(f"[TICKET] Could not get customer_id from session: {e}")
        
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


def update_ticket_status(ticket_id: str, status: str) -> bool:
    """Update ticket status."""
    if not SUPABASE_ENABLED:
        # Fallback to JSON
        from tools.ticket_tool import get_all_tickets, save_tickets
        tickets = get_all_tickets()
        if isinstance(tickets, dict) and ticket_id in tickets:
            tickets[ticket_id]["status"] = status
            tickets[ticket_id]["updated_at"] = datetime.now().isoformat()
            save_tickets(tickets)
            return True
        return False
    
    try:
        supabase.table("tickets").update({
            "status": status,
            "updated_at": datetime.now().isoformat()
        }).eq("ticket_id", ticket_id).execute()
        return True
    except Exception as e:
        print(f"Erreur Supabase update_ticket_status: {e}")
        return False


def get_tickets(session_id: Optional[str] = None) -> List[Dict]:
    """Récupérer les tickets depuis Supabase."""
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
        tickets_list = result.data or []
        print(f"✅ [SUPABASE] Retrieved {len(tickets_list)} tickets from Supabase")
        return tickets_list
    except Exception as e:
        print(f"❌ [SUPABASE] Error get_tickets: {e}")
        import traceback
        traceback.print_exc()
        # Don't fallback here - let the caller handle it
        raise


# ============================================================================
# Orders
# ============================================================================

def get_orders(customer_id: Optional[str] = None) -> List[Dict]:
    """Récupérer les commandes avec mise à jour automatique du statut si estimated_delivery est passée."""
    from datetime import datetime, date
    
    if not SUPABASE_ENABLED:
        from tools.order_tool import get_all_orders
        orders = get_all_orders()
        if customer_id:
            orders = [o for o in orders if o.get("customer_id") == customer_id]
        print(f"ℹ️  [ORDERS] Loaded {len(orders)} orders from JSON fallback")
        return orders
    
    # Prioritize Supabase
    try:
        query = supabase.table("orders").select("*")
        
        if customer_id:
            query = query.eq("customer_id", customer_id)
        
        result = query.order("created_at", desc=True).execute()
        orders = result.data or []
        print(f"✅ [SUPABASE] Retrieved {len(orders)} orders from Supabase")
    except Exception as e:
        print(f"❌ [SUPABASE] Error get_orders: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to JSON on error
        from tools.order_tool import get_all_orders
        orders = get_all_orders()
        if customer_id:
            orders = [o for o in orders if o.get("customer_id") == customer_id]
        print(f"ℹ️  [ORDERS] Fallback to JSON: {len(orders)} orders")
        return orders
    
    # Check each order and update status based on estimated_delivery date
    today = date.today()
    updated_orders = []
    
    for order in orders:
        estimated_delivery = order.get("estimated_delivery")
        current_status = order.get("status", "").lower()
        
        # Only update if status is not "delivered" or "cancelled"
        if estimated_delivery and current_status not in ["delivered", "cancelled"]:
            try:
                # Parse the date (handle both date strings and datetime strings)
                if isinstance(estimated_delivery, str):
                    # Try parsing as date first
                    try:
                        delivery_date = datetime.strptime(estimated_delivery.split("T")[0], "%Y-%m-%d").date()
                    except:
                        delivery_date = datetime.strptime(estimated_delivery, "%Y-%m-%d").date()
                else:
                    delivery_date = estimated_delivery
                
                new_status = None
                
                # Only auto-update if status is not "delivered" or "cancelled"
                if current_status not in ["delivered", "cancelled"]:
                    # If date has passed (current date is after estimated_delivery) → "delivery_soon"
                    if delivery_date < today:
                        new_status = "delivery_soon"
                        order["status"] = "delivery_soon"
                    # If date is in the future → "delivering"
                    elif delivery_date >= today:
                        new_status = "delivering"
                        order["status"] = "delivering"
                
                # Update in database if status changed
                if new_status and SUPABASE_ENABLED:
                    try:
                        supabase.table("orders").update({"status": new_status}).eq("order_id", order.get("order_id")).execute()
                    except Exception as e:
                        print(f"Warning: Could not update order status in Supabase: {e}")
            except Exception as e:
                print(f"Warning: Could not parse estimated_delivery for order {order.get('order_id')}: {e}")
        
        updated_orders.append(order)
    
    return updated_orders


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
    ticket_id: Optional[str] = None
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
# Agent Refinements
# ============================================================================

def save_agent_refinement(
    refinement_key: str,
    agent_name: str,
    refinement_type: str,
    changes: Dict,
    feedback_sources: Optional[List[str]] = None,
    status: str = "pending"
) -> bool:
    """Save an agent refinement to Supabase."""
    if not SUPABASE_ENABLED:
        return False
    
    try:
        refinement_data = {
            "refinement_key": refinement_key,
            "agent_name": agent_name,
            "refinement_type": refinement_type,
            "changes": changes,
            "feedback_sources": feedback_sources or [],
            "status": status,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        result = supabase.table("agent_refinements").upsert(refinement_data).execute()
        return True
    except Exception as e:
        print(f"Erreur Supabase save_agent_refinement: {e}")
        return False


def get_agent_refinements(agent_name: Optional[str] = None, status: Optional[str] = None) -> List[Dict]:
    """Get agent refinements from Supabase."""
    if not SUPABASE_ENABLED:
        return []
    
    try:
        query = supabase.table("agent_refinements").select("*")
        
        if agent_name:
            query = query.eq("agent_name", agent_name)
        
        if status:
            query = query.eq("status", status)
        
        result = query.order("created_at", desc=True).execute()
        return result.data or []
    except Exception as e:
        print(f"Erreur Supabase get_agent_refinements: {e}")
        return []


def update_agent_refinement_status(refinement_key: str, status: str) -> bool:
    """Update the status of an agent refinement."""
    if not SUPABASE_ENABLED:
        return False
    
    try:
        supabase.table("agent_refinements").update({
            "status": status,
            "updated_at": datetime.now().isoformat()
        }).eq("refinement_key", refinement_key).execute()
        return True
    except Exception as e:
        print(f"Erreur Supabase update_agent_refinement_status: {e}")
        return False


# ============================================================================
# Feedback Insights
# ============================================================================

def save_feedback_insight(
    insight_key: Optional[str] = None,
    agent_name: Optional[str] = None,
    insight_type: str = "general",
    description: Optional[str] = None,
    sentiment: Optional[Dict] = None,
    feedback_sources: Optional[List[str]] = None,
    insight_data: Optional[Dict] = None,
    summary: Optional[str] = None
) -> bool:
    """Save a feedback insight to Supabase."""
    if not SUPABASE_ENABLED:
        return False
    
    try:
        import uuid
        if not insight_key:
            insight_key = f"INSIGHT-{uuid.uuid4().hex[:8].upper()}"
        
        # Store all data in the JSONB 'data' column (table schema only has insight_key, insight_type, data)
        data_dict = {
            "agent_name": agent_name or "unknown",
            "description": description or summary or "Feedback insight",
            "sentiment": sentiment or {},
            "feedback_sources": feedback_sources or [],
            **(insight_data or {})
        }
        
        insight_data_dict = {
            "insight_key": insight_key,
            "insight_type": insight_type,
            "data": data_dict,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        result = supabase.table("feedback_insights").upsert(insight_data_dict).execute()
        return True
    except Exception as e:
        print(f"Erreur Supabase save_feedback_insight: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_feedback_insights(agent_name: Optional[str] = None, insight_type: Optional[str] = None) -> List[Dict]:
    """Get feedback insights from Supabase."""
    if not SUPABASE_ENABLED:
        return []
    
    try:
        query = supabase.table("feedback_insights").select("*")
        
        if insight_type:
            query = query.eq("insight_type", insight_type)
        
        result = query.order("created_at", desc=True).execute()
        insights = result.data or []
        
        # Filter by agent_name if provided (agent_name is stored in data JSONB)
        if agent_name:
            filtered_insights = []
            for insight in insights:
                data = insight.get("data", {})
                if isinstance(data, dict) and data.get("agent_name") == agent_name:
                    filtered_insights.append(insight)
            return filtered_insights
        
        return insights
    except Exception as e:
        print(f"Erreur Supabase get_feedback_insights: {e}")
        return []


# ============================================================================
# KB Updates from Feedback
# ============================================================================

def save_kb_update(
    update_id: str,
    feedback_id: Optional[str],
    update_type: str,
    content: Dict,
    status: str = "pending"
) -> bool:
    """Save a KB update suggestion to Supabase."""
    if not SUPABASE_ENABLED:
        return False
    
    try:
        kb_update_data = {
            "update_id": update_id,
            "feedback_id": feedback_id,
            "update_type": update_type,
            "content": content,
            "status": status,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        result = supabase.table("kb_updates_from_feedback").upsert(kb_update_data).execute()
        return True
    except Exception as e:
        print(f"Erreur Supabase save_kb_update: {e}")
        return False


def get_kb_updates(status: Optional[str] = None) -> List[Dict]:
    """Get KB update suggestions from Supabase."""
    if not SUPABASE_ENABLED:
        return []
    
    try:
        query = supabase.table("kb_updates_from_feedback").select("*")
        
        if status:
            query = query.eq("status", status)
        
        result = query.order("created_at", desc=True).execute()
        return result.data or []
    except Exception as e:
        print(f"Erreur Supabase get_kb_updates: {e}")
        return []


def update_kb_update_status(update_id: str, status: str) -> bool:
    """Update the status of a KB update."""
    if not SUPABASE_ENABLED:
        return False
    
    try:
        supabase.table("kb_updates_from_feedback").update({
            "status": status,
            "updated_at": datetime.now().isoformat()
        }).eq("update_id", update_id).execute()
        return True
    except Exception as e:
        print(f"Erreur Supabase update_kb_update_status: {e}")
        return False


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

