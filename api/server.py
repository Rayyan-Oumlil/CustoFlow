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
        except Exception:
            # Session may already exist, that's okay
            pass
        
        # Increment metrics
        metrics.increment("messages_received")
        
        # Create message with sanitized content
        message = types.Content(
            role="user",
            parts=[types.Part(text=sanitized_message)]
        )
        
        # Get agent response with timeout protection
        import time
        response_start_time = time.time()
        response_text = ""
        
        async def get_response():
            """Inner async function for timeout handling."""
            nonlocal response_text
            all_texts = []  # Collect all text responses
            tool_results = []  # Collect tool results as fallback
            
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
                                if isinstance(result, str) and len(result) > 10:
                                    tool_results.append(result)
                                elif isinstance(result, dict):
                                    # Extract answer from FAQ tool result
                                    if "answer" in result:
                                        tool_results.append(result["answer"])
                                    elif "error_message" in result:
                                        tool_results.append(result["error_message"])
                            except:
                                pass
                    
                    if response_text and event.is_final_response():
                        break
            
            # If no final response, use the longest text collected
            if not response_text and all_texts:
                # Filter meaningful texts (longer than 20 chars)
                meaningful = [t for t in all_texts if len(t) > 20]
                if meaningful:
                    response_text = max(meaningful, key=len)
                else:
                    response_text = max(all_texts, key=len)
            
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
        
        # Calculate response time
        response_time = time.time() - response_start_time
        
        metrics.increment("messages_sent")
        logger.info(f"Response sent to user: {request.user_id}")
        
        # Log analytics
        analytics.log_interaction(
            user_id=request.user_id,
            query=sanitized_message,
            response=response_text,
            agent_used="orchestrator",  # Could extract from response metadata
            response_time=response_time
        )
        
        # Store in conversation history
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
            metadata={"response_time": response_time, "agent": "orchestrator"}
        )
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
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


@app.get("/analytics")
async def get_analytics():
    """Get analytics data."""
    return analytics.get_stats()


@app.post("/feedback")
async def submit_feedback(
    session_id: str,
    feedback_type: str,
    rating: Optional[int] = None,
    comment: Optional[str] = None
):
    """
    Submit user feedback.
    
    Args:
        session_id: Session identifier
        feedback_type: "thumbs_up", "thumbs_down", or "rating"
        rating: Numeric rating (1-5) if feedback_type is "rating"
        comment: Optional comment
    """
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
    return {"user_id": user_id, "history": history, "count": len(history)}


@app.get("/sessions/{user_id}")
async def get_user_sessions(user_id: str):
    """Get all session IDs for a user."""
    sessions = conversation_history.get_user_sessions(user_id)
    return {"user_id": user_id, "sessions": sessions, "count": len(sessions)}


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


@app.get("/tickets")
async def get_tickets():
    """Get all tickets from the system."""
    from tools.ticket_tool import _TICKETS
    tickets_list = list(_TICKETS.values())
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
    from tools.ticket_tool import _TICKETS
    ticket = _TICKETS.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    return {"ticket": ticket}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level="info"
    )

