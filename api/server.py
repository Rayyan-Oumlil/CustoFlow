"""FastAPI server for customer support agent."""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import asyncio
import os
from google.genai import types

from config.settings import settings
from agents.orchestrator_agent import orchestrator_agent
from memory.session_store import session_manager
from google.adk.runners import Runner
from observability.logging_config import setup_logging, get_logger, get_logging_plugin
from observability.metrics import metrics
from utils.validation import validate_message, sanitize_message, validate_user_id
from utils.rate_limiter import rate_limiter
from utils.error_handler import handle_api_errors, with_timeout, get_user_friendly_error
from utils.analytics import analytics
from utils.multilingual import detect_language, get_greeting, get_error_message
from memory.conversation_history import conversation_history
from memory.session_metadata import session_metadata

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Get ADK LoggingPlugin for enhanced observability
logging_plugin = get_logging_plugin()

# Create FastAPI app
app = FastAPI(
    title="Customer Support Agent API",
    description="Multi-agent customer support system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create runner with observability plugins
runner = Runner(
    agent=orchestrator_agent,
    app_name=settings.app_name,
    session_service=session_manager.get_service(),
    plugins=[logging_plugin]  # Add logging plugin for observability
)


# Request/Response models
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000, description="User message")
    user_id: Optional[str] = Field(default="guest", max_length=50, description="User identifier")
    session_id: Optional[str] = Field(default=None, max_length=100, description="Session identifier")


class ChatResponse(BaseModel):
    response: str
    session_id: str
    agent_used: Optional[str] = "orchestrator"
    response_time: Optional[float] = None
    metrics: dict


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Customer Support Agent API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "metrics": metrics.get_counts()
    }


@app.post("/chat", response_model=ChatResponse)
@handle_api_errors
async def chat(request: ChatRequest, http_request: Request):
    """
    Chat endpoint for customer support.
    
    Validates input, applies rate limiting, sanitizes message,
    and gets agent response with timeout protection.
    """
    import time
    start_time = time.time()
    try:
        # Validate message
        is_valid, error_msg = validate_message(request.message)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Validate user ID
        is_valid, error_msg = validate_user_id(request.user_id)
        if not is_valid:
            request.user_id = "guest"  # Fallback to guest
        
        # Rate limiting
        # Use user_id for rate limiting, fallback to IP
        rate_limit_id = request.user_id
        if rate_limit_id == "guest":
            # For guests, use IP address
            client_ip = http_request.client.host if http_request.client else "unknown"
            rate_limit_id = f"ip_{client_ip}"
        
        is_allowed, rate_error = rate_limiter.is_allowed(rate_limit_id)
        if not is_allowed:
            raise HTTPException(status_code=429, detail=rate_error)
        
        # Sanitize message
        sanitized_message = sanitize_message(request.message)
        
        # Generate session ID if not provided
        if not request.session_id:
            session_id = f"session_{request.user_id}_{os.urandom(4).hex()}"
        else:
            session_id = request.session_id
        
        # Create session if it doesn't exist
        try:
            await session_manager.get_service().create_session(
                app_name=settings.app_name,
                user_id=request.user_id,
                session_id=session_id
            )
            metrics.increment("sessions_started")
            logger.info(f"New session created: {session_id}")
            # Create metadata if new session (utilise Supabase si disponible)
            session_metadata.create_session(session_id, request.user_id)
        except Exception:
            # Session may already exist, that's okay
            pass
        
        # Update message count in metadata
        session_metadata.increment_message_count(session_id)
        
        # Increment metrics
        metrics.increment("messages_received")
        
        # Create message with sanitized content
        message = types.Content(
            role="user",
            parts=[types.Part(text=sanitized_message)]
        )
        
        # Set context for ticket tools (so they can access session_id and user_id)
        # This context will be available when create_ticket is called by the agent
        from tools.ticket_tool import set_ticket_context, clear_ticket_context
        set_ticket_context(session_id=session_id, user_id=request.user_id, request_id=session_id)
        logger.info(f"Set ticket context: session_id={session_id}, user_id={request.user_id}")
        
        # Also store in a way that's accessible by session_id lookup
        set_ticket_context(session_id=session_id, user_id=request.user_id, request_id=None)
        
        try:
            # Get agent response with timeout protection
            import time
            response_start_time = time.time()
            response_text = ""
            
            async def get_response():
                """Inner async function for timeout handling."""
                nonlocal response_text
                all_texts = []  # Collect all text responses
                tool_results = []  # Collect tool results as fallback
                last_tool_result = None  # Keep track of last tool result for fallback
                
                try:
                    async for event in runner.run_async(
                        user_id=request.user_id,
                        session_id=session_id,
                        new_message=message
                    ):
                        # Collect text from any event with content
                        if event.content and event.content.parts:
                            for part in event.content.parts:
                                if hasattr(part, "text") and part.text:
                                    text = part.text.strip()
                                    if text and len(text) > 5:  # Only meaningful text
                                        all_texts.append(text)
                                        # Prefer final response if available
                                        if event.is_final_response():
                                            response_text = text
                                            break
                                
                                # Also collect function_response results as fallback
                                if hasattr(part, "function_response") and part.function_response:
                                    try:
                                        result = part.function_response.result
                                        last_tool_result = result  # Store for fallback
                                        if isinstance(result, str) and len(result) > 10:
                                            tool_results.append(result)
                                        elif isinstance(result, dict):
                                            # Store the full dict for later processing
                                            tool_results.append(result)
                                            last_tool_result = result
                                            # Also extract specific fields if available
                                            if "answer" in result:
                                                tool_results.append(result["answer"])
                                            elif "error_message" in result:
                                                tool_results.append(result["error_message"])
                                    except:
                                        pass
                        
                        if response_text and event.is_final_response():
                            break
                except TypeError as e:
                    # Handle the specific error from agent_tool when Content is None
                    if "'NoneType' object is not iterable" in str(e) or "NoneType" in str(e):
                        logger.warning(f"Agent returned None content, using tool result fallback: {last_tool_result}")
                        # Use the last tool result if available
                        if last_tool_result:
                            tool_results.append(last_tool_result)
                    else:
                        raise  # Re-raise if it's a different TypeError
                
                # If no final response, use the longest text collected
                if not response_text and all_texts:
                    # Filter meaningful texts (longer than 20 chars)
                    meaningful = [t for t in all_texts if len(t) > 20]
                    if meaningful:
                        response_text = max(meaningful, key=len)
                
                # Fallback: Generate response from tool results if no text response
                if not response_text and tool_results:
                    # Try to construct a response from tool results
                    for result in tool_results:
                        if isinstance(result, str) and len(result) > 20:
                            response_text = result
                            break
                        elif isinstance(result, dict):
                            # Extract useful information from dict results
                            if "orders" in result and result.get("status") == "success":
                                orders = result.get("orders", [])
                                if orders:
                                    order_info = []
                                    for order in orders[:3]:  # Limit to first 3 orders
                                        order_id = order.get("order_id", "N/A")
                                        status = order.get("status", "unknown").title()
                                        total = order.get("total", 0)
                                        items = order.get("items", [])
                                        items_desc = ", ".join([
                                            f"{item.get('quantity', 1)}x {item.get('name', 'item')}"
                                            for item in items[:2]  # Limit items per order
                                        ])
                                        tracking = order.get("tracking_number", "")
                                        estimated_delivery = order.get("estimated_delivery", "")
                                        
                                        # Build natural, conversational order description
                                        status_text = {
                                            "processing": "is currently being processed",
                                            "shipped": "has been shipped and is on its way",
                                            "delivered": "has been delivered",
                                            "cancelled": "was cancelled"
                                        }.get(status.lower(), f"is {status}")
                                        
                                        order_text = f"Order {order_id} {status_text}. It contains {items_desc} for ${total:.2f}."
                                        if tracking:
                                            order_text += f" You can track it using the tracking number {tracking}."
                                        if estimated_delivery:
                                            order_text += f" The estimated delivery date is {estimated_delivery}."
                                        
                                        order_info.append(order_text)
                                    
                                    if len(orders) == 1:
                                        response_text = f"Great! I found 1 order for you. {order_info[0]} Is there anything else you'd like to know about this order?"
                                    else:
                                        response_text = f"I found {len(orders)} orders in your account. "
                                        for i, info in enumerate(order_info, 1):
                                            if i == 1:
                                                response_text += f"First, {info.lower()} "
                                            elif i == len(order_info):
                                                response_text += f"Finally, {info.lower()} "
                                            else:
                                                response_text += f"Second, {info.lower()} "
                                        response_text += "Would you like more details about any of these orders?"
                                    break
                            elif "order" in result and result.get("status") == "success":
                                order = result.get("order", {})
                                order_id = order.get("order_id", "N/A")
                                status = order.get("status", "unknown").title()
                                total = order.get("total", 0)
                                items = order.get("items", [])
                                items_desc = ", ".join([
                                    f"{item.get('quantity', 1)}x {item.get('name', 'item')}"
                                    for item in items[:3]
                                ])
                                tracking = order.get("tracking_number", "")
                                estimated_delivery = order.get("estimated_delivery", "")
                                
                                # Build natural, conversational response
                                status_text = {
                                    "processing": "is currently being processed",
                                    "shipped": "has been shipped and is on its way to you",
                                    "delivered": "has been delivered",
                                    "cancelled": "was cancelled"
                                }.get(status.lower(), f"is {status}")
                                
                                response_text = f"Great news! Your order {order_id} {status_text}. It contains {items_desc} for ${total:.2f}."
                                if tracking:
                                    response_text += f" You can track your package using the tracking number {tracking}."
                                if estimated_delivery:
                                    response_text += f" The estimated delivery date is {estimated_delivery}."
                                response_text += " Is there anything else you'd like to know about your order?"
                                break
                
                # Last resort: use tool result if agent didn't generate text
                if not response_text and tool_results:
                    # Use the longest tool result
                    meaningful_tools = [t for t in tool_results if len(t) > 20]
                    if meaningful_tools:
                        response_text = max(meaningful_tools, key=len)
                    elif tool_results:
                        response_text = max(tool_results, key=len)
                
                return response_text
        
            # Execute with 30 second timeout
            response_text = await with_timeout(
                get_response(),
                timeout_seconds=30,
                default_response="I apologize, but the request took too long to process. Please try again with a simpler question."
            )
            
            if not response_text:
                response_text = "I apologize, but I couldn't generate a response. Please try rephrasing your question."
        finally:
            # Clear context after processing
            clear_ticket_context()
        
        # Calculate response time
        response_time = time.time() - response_start_time
        
        metrics.increment("messages_sent")
        logger.info(f"Response sent to user: {request.user_id}")
        
        # Extract agent_used from response if available (default to orchestrator)
        agent_used = "orchestrator"
        
        # Log analytics (now saves to Supabase)
        analytics.log_interaction(
            user_id=request.user_id,
            query=sanitized_message,
            response=response_text,
            agent_used=agent_used,
            response_time=response_time,
            session_id=session_id
        )
        
        # Store in conversation history (utilise Supabase si disponible)
        conversation_history.add_message(
            user_id=request.user_id,
            session_id=session_id,
            role="user",
            content=sanitized_message
        )
        conversation_history.add_message(
            user_id=request.user_id,
            session_id=session_id,
            role="assistant",
            content=response_text,
            metadata={"response_time": response_time, "agent": agent_used}
        )
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            agent_used=agent_used,
            response_time=response_time,
            metrics=metrics.get_counts()
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions (rate limiting, validation, etc.)
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        metrics.increment("errors")
        user_message = get_user_friendly_error(e)
        raise HTTPException(status_code=500, detail=user_message)


@app.get("/metrics")
async def get_metrics():
    """Get current metrics."""
    return metrics.get_counts()

@app.post("/metrics/reset")
async def reset_metrics():
    """Reset all in-memory metrics (for testing/cleanup)."""
    metrics.reset()
    analytics.reset()
    return {"status": "success", "message": "Metrics reset"}


@app.get("/analytics")
async def get_analytics():
    """Get analytics data."""
    # Get ticket count from database
    from tools.ticket_tool import get_all_tickets
    all_tickets = get_all_tickets()
    if isinstance(all_tickets, dict):
        tickets_list = list(all_tickets.values())
    else:
        tickets_list = all_tickets if isinstance(all_tickets, list) else []
    
    # Get active sessions count (sessions with messages) from database
    from memory.session_metadata import session_metadata
    try:
        # Try to get active sessions from Supabase or JSON
        all_sessions = session_metadata.get_all_sessions()
        active_sessions = sum(1 for s in all_sessions.values() if s.get("message_count", 0) > 0) if isinstance(all_sessions, dict) else 0
    except:
        active_sessions = 0
    
    # Get total messages from database (count directly from Supabase)
    total_messages = 0
    try:
        from utils.supabase_client import SUPABASE_ENABLED
        if SUPABASE_ENABLED:
            from supabase import create_client
            import os
            from dotenv import load_dotenv
            load_dotenv()
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            if supabase_url and supabase_key:
                supabase = create_client(supabase_url, supabase_key)
                # Count all messages
                result = supabase.table("messages").select("id", count="exact").limit(1).execute()
                total_messages = result.count if hasattr(result, 'count') and result.count is not None else 0
        else:
            # Count from JSON
            from memory.conversation_history import conversation_history
            all_history = conversation_history.get_history("", limit=10000)
            total_messages = len(all_history) if all_history else 0
    except Exception as e:
        logger.warning(f"Error counting messages: {e}")
        total_messages = 0
    
    # Get interactions (same as total_messages for now)
    interactions = total_messages // 2  # Each interaction = user message + assistant response
    
    # Calculate average satisfaction from feedback if available
    avg_satisfaction = 0.0
    try:
        from utils.supabase_client import SUPABASE_ENABLED, get_feedback_stats
        if SUPABASE_ENABLED:
            feedback_stats = get_feedback_stats()
            if feedback_stats and feedback_stats.get("avg_rating"):
                avg_satisfaction = float(feedback_stats.get("avg_rating", 0.0))
    except Exception as e:
        logger.warning(f"Error getting feedback stats: {e}")
    
    # Return data in the format expected by frontend - all from database, not in-memory
    result = {
        "total_messages": total_messages,
        "active_sessions": active_sessions,
        "interactions": interactions,
        "avg_satisfaction": avg_satisfaction,
        "tickets_created": len(tickets_list),
    }
    return result


@app.post("/feedback")
async def submit_feedback(
    session_id: str,
    feedback_type: str,
    rating: Optional[int] = None,
    comment: Optional[str] = None,
    user_id: Optional[str] = None,
    reason: Optional[str] = None,
    category: Optional[str] = None,
    agent_used: Optional[str] = None
):
    """
    Submit user feedback.
    
    Args:
        session_id: Session identifier
        feedback_type: "thumbs_up", "thumbs_down", or "rating"
        rating: Numeric rating (1-5) if feedback_type is "rating"
        comment: Optional comment
        user_id: Optional user identifier
        reason: Optional reason for feedback
        category: Optional feedback category
        agent_used: Optional agent that handled the conversation
    """
    # Essayer Supabase d'abord
    try:
        from utils.supabase_client import SUPABASE_ENABLED, create_feedback
        if SUPABASE_ENABLED and user_id:
            result = create_feedback(
                session_id=session_id,
                user_id=user_id,
                feedback_type=feedback_type,
                rating=rating,
                comment=comment,
                reason=reason,
                category=category,
                agent_used=agent_used
            )
            if result.get("status") == "success":
                analytics.log_feedback(session_id, feedback_type, rating, comment)
                return {"status": "success", "message": "Feedback recorded", "feedback_id": result.get("feedback_id")}
    except Exception:
        pass  # Fallback vers analytics
    
    # Fallback vers analytics (JSON)
    analytics.log_feedback(session_id, feedback_type, rating, comment)
    return {"status": "success", "message": "Feedback recorded"}


@app.get("/history/{user_id}")
async def get_history(user_id: str, limit: Optional[int] = 50, session_id: Optional[str] = None):
    """
    Get conversation history for a user.
    
    Args:
        user_id: User identifier
        limit: Maximum number of messages to return
        session_id: Optional session filter
    """
    history = conversation_history.get_history(user_id, limit=limit, session_id=session_id)
    # Return array directly for frontend compatibility
    return history


@app.get("/sessions/{user_id}")
async def get_user_sessions(user_id: str):
    """Get all sessions for a user with metadata."""
    sessions = session_metadata.get_user_sessions(user_id)
    return {"user_id": user_id, "sessions": sessions, "count": len(sessions)}


class CreateSessionRequest(BaseModel):
    user_id: str
    name: Optional[str] = None


@app.post("/sessions/create")
async def create_session(request: CreateSessionRequest):
    """
    Create a new session with optional custom name.
    
    Args:
        request: CreateSessionRequest with user_id and optional name
    """
    import os
    session_id = f"session_{request.user_id}_{os.urandom(4).hex()}"
    
    # Create session in ADK
    try:
        await session_manager.get_service().create_session(
            app_name=settings.app_name,
            user_id=request.user_id,
            session_id=session_id
        )
        metrics.increment("sessions_started")
    except Exception:
        pass  # Session may already exist
    
    # Create metadata
    metadata = session_metadata.create_session(session_id, request.user_id, request.name)
    
    return {
        "status": "success",
        "session_id": session_id,
        "metadata": metadata
    }


class RenameSessionRequest(BaseModel):
    new_name: str


@app.put("/sessions/{session_id}/rename")
async def rename_session(session_id: str, request: RenameSessionRequest):
    """
    Rename a session.
    
    Args:
        session_id: Session identifier
        request: RenameSessionRequest with new_name
    """
    if not request.new_name or not request.new_name.strip():
        raise HTTPException(status_code=400, detail="Session name cannot be empty")
    
    success = session_metadata.rename_session(session_id, request.new_name.strip())
    if not success:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    return {
        "status": "success",
        "session_id": session_id,
        "new_name": request.new_name.strip()
    }


@app.get("/sessions/{session_id}/metadata")
async def get_session_metadata(session_id: str):
    """Get metadata for a specific session."""
    metadata = session_metadata.get_session(session_id)
    if not metadata:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return metadata


@app.get("/orders")
async def get_orders():
    """Get all orders from the system."""
    from tools.order_tool import _MOCK_ORDERS
    orders_list = list(_MOCK_ORDERS.values())
    return {
        "orders": orders_list,
        "count": len(orders_list),
        "statuses": {
            status: sum(1 for o in orders_list if o.get("status") == status)
            for status in ["processing", "shipped", "delivered", "cancelled"]
        }
    }


@app.get("/orders/{order_id}")
async def get_order(order_id: str):
    """Get a specific order by ID."""
    from tools.order_tool import _MOCK_ORDERS
    order = _MOCK_ORDERS.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    return {"order": order}


@app.post("/orders")
async def create_order(order_data: dict):
    """
    Create a new order (Admin function).
    
    This endpoint allows administrators to manually add orders to the system.
    Tickets are created automatically by the bot, so this endpoint only handles orders.
    
    Expected order structure:
    {
        "order_id": str,
        "customer_id": str,
        "status": str,  # processing, shipped, delivered, cancelled
        "items": [
            {"name": str, "quantity": int, "price": float}
        ],
        "total": float,
        "order_date": str,  # YYYY-MM-DD
        "shipped_date": str | None,  # YYYY-MM-DD
        "tracking_number": str | None,
        "estimated_delivery": str | None  # YYYY-MM-DD
    }
    """
    from tools.order_tool import _MOCK_ORDERS
    
    # Validate required fields
    required_fields = ["order_id", "customer_id", "status", "items", "total", "order_date"]
    for field in required_fields:
        if field not in order_data:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    order_id = order_data["order_id"]
    
    # Check if order already exists
    if order_id in _MOCK_ORDERS:
        raise HTTPException(status_code=409, detail=f"Order {order_id} already exists")
    
    # Validate status
    valid_statuses = ["processing", "shipped", "delivered", "cancelled"]
    if order_data["status"] not in valid_statuses:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    # Validate items
    if not isinstance(order_data["items"], list) or len(order_data["items"]) == 0:
        raise HTTPException(status_code=400, detail="Items must be a non-empty list")
    
    for item in order_data["items"]:
        if not all(key in item for key in ["name", "quantity", "price"]):
            raise HTTPException(status_code=400, detail="Each item must have 'name', 'quantity', and 'price'")
    
    # Add order to database (with persistence)
    from tools.order_tool import add_order
    success = add_order(order_data)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save order to database")
    
    # Log metrics
    metrics.increment("orders_created")
    
    return {
        "status": "success",
        "message": f"Order {order_id} created successfully",
        "order": order_data
    }


@app.get("/tickets")
async def get_tickets():
    """Get all tickets from the system."""
    from tools.ticket_tool import get_all_tickets
    all_tickets = get_all_tickets()
    # get_all_tickets retourne un dict ou une liste selon la source (Supabase ou JSON)
    if isinstance(all_tickets, dict):
        tickets_list = list(all_tickets.values())
    else:
        tickets_list = all_tickets if isinstance(all_tickets, list) else []
    return {
        "tickets": tickets_list,
        "count": len(tickets_list),
        "statuses": {
            status: sum(1 for t in tickets_list if t.get("status") == status)
            for status in ["open", "in_progress", "resolved", "closed"]
        },
        "priorities": {
            priority: sum(1 for t in tickets_list if t.get("priority") == priority)
            for priority in ["low", "normal", "high", "urgent"]
        }
    }


@app.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str):
    """Get a specific ticket by ID."""
    from tools.ticket_tool import get_all_tickets
    all_tickets = get_all_tickets()
    # Handle both dict and list formats
    if isinstance(all_tickets, dict):
        ticket = all_tickets.get(ticket_id)
    else:
        ticket = next((t for t in all_tickets if t.get("ticket_id") == ticket_id), None)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    return {"ticket": ticket}


@app.get("/tickets/{ticket_id}/summary")
async def get_ticket_summary(ticket_id: str):
    """Get a summary of a specific ticket."""
    from tools.ticket_tool import get_all_tickets
    all_tickets = get_all_tickets()
    ticket = all_tickets.get(ticket_id) if isinstance(all_tickets, dict) else None
    if not ticket:
        # Try to find in list format
        if isinstance(all_tickets, list):
            ticket = next((t for t in all_tickets if t.get("ticket_id") == ticket_id), None)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    
    # Get the actual conversation summary from Supabase or JSON
    summary_text = None
    session_id = ticket.get("session_id")
    user_id = ticket.get("user_id")
    
    if session_id and user_id:
        try:
            from utils.supabase_client import SUPABASE_ENABLED, get_session_summaries
            if SUPABASE_ENABLED:
                summaries = get_session_summaries(session_id)
                # Find summary linked to this ticket
                ticket_summary = next((s for s in summaries if s.get("ticket_id") == ticket_id), None)
                if ticket_summary:
                    summary_text = ticket_summary.get("summary")
            else:
                # Fallback to JSON
                from utils.conversation_summarizer import _load_summaries
                summaries = _load_summaries()
                # Find summary by ticket_id
                for key, summary_data in summaries.items():
                    if summary_data.get("ticket_id") == ticket_id:
                        summary_text = summary_data.get("summary")
                        break
        except Exception as e:
            logger.warning(f"Error fetching summary: {e}")
    
    return {
        "ticket_id": ticket.get("ticket_id"),
        "status": ticket.get("status"),
        "priority": ticket.get("priority"),
        "issue": ticket.get("issue", ""),
        "summary": summary_text,  # Return the actual summary
        "created_at": ticket.get("created_at")
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level="info"
    )

