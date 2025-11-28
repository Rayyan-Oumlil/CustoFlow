"""FastAPI server for customer support agent."""
from fastapi import FastAPI, HTTPException, Request, Query, UploadFile, File, Form
from fastapi.responses import Response
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
from utils.validation import validate_message, sanitize_message, validate_user_id, validate_customer_id
from utils.rate_limiter import rate_limiter
from utils.error_handler import handle_api_errors, with_timeout, get_user_friendly_error
from utils.analytics import analytics
from utils.multilingual import detect_language, get_greeting, get_error_message
from memory.conversation_history import conversation_history
from memory.session_metadata import session_metadata
from utils.auto_improver import start_auto_improvements, run_improvements_now

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Start auto-improvement scheduler (runs daily at 2 AM)
try:
    start_auto_improvements(hour=2, minute=0)
    logger.info("Auto-improvement scheduler started (daily at 2:00 AM)")
except Exception as e:
    logger.warning(f"Could not start auto-improvement scheduler: {e}")

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
    customer_id: Optional[str] = Field(default=None, max_length=50, description="Customer identifier")


class ChatResponse(BaseModel):
    response: str
    session_id: str
    agent_used: Optional[str] = "orchestrator"
    response_time: Optional[float] = None
    metrics: dict
    quality_score: Optional[float] = None  # 0.0 to 1.0
    quality_status: Optional[str] = None  # pass, warning, fail
    compliance_flags: Optional[list] = None
    ab_test_variant: Optional[str] = None  # "variant_a" or "variant_b"


class FeedbackRequest(BaseModel):
    session_id: str
    feedback_type: str
    rating: Optional[int] = None
    comment: Optional[str] = None
    user_id: Optional[str] = None
    reason: Optional[str] = None
    category: Optional[str] = None
    agent_used: Optional[str] = None
    ticket_id: Optional[str] = None  # Optional ticket ID to link feedback to a ticket


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
        
        # Validate customer_id if provided
        if request.customer_id:
            is_valid, error_msg = validate_customer_id(request.customer_id)
            if not is_valid:
                raise HTTPException(status_code=400, detail=f"Invalid customer_id: {error_msg}")
        
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
        
        # Check if message contains a customer_id and extract it
        # Look for patterns like "customer_id: cust_001", "mon customer id est cust_001", "cust_001", etc.
        import re
        customer_id_from_message = None
        customer_id_patterns = [
            r'customer[_\s-]?id[:\s]+([A-Za-z0-9_-]+)',
            r'customer[_\s-]?id[:\s]+([A-Za-z0-9_-]+)',
            r'cust[_\s-]?id[:\s]+([A-Za-z0-9_-]+)',
            r'^([A-Za-z0-9_-]{1,50})$',  # Standalone customer ID
            r'\b(cust_[0-9]+)\b',  # cust_001 format
            r'\b(CUST-[0-9]+)\b',  # CUST-123 format
        ]
        for pattern in customer_id_patterns:
            match = re.search(pattern, sanitized_message, re.IGNORECASE)
            if match:
                potential_id = match.group(1) if match.groups() else match.group(0)
                # Validate it looks like a customer ID
                is_valid, _ = validate_customer_id(potential_id)
                if is_valid:
                    customer_id_from_message = potential_id
                    break
        
        # Determine initial customer_id before creating session
        # Priority: 1) customer_id from request, 2) existing context, 3) user_id as default
        from tools.order_tool import get_order_context
        existing_context = get_order_context(session_id)
        existing_customer_id = existing_context.get("customer_id")
        
        # Use customer_id from request if available, otherwise use existing or user_id
        initial_customer_id = request.customer_id if request.customer_id else (existing_customer_id if existing_customer_id else request.user_id)
        
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
            # Use customer_id from request or existing context
            session_metadata.create_session(session_id, request.user_id, customer_id=initial_customer_id)
            logger.info(f"Created session with customer_id: {initial_customer_id}")
        except Exception:
            # Session may already exist, that's okay
            pass
        
        # Check if session is active (not closed) - MUST be done BEFORE processing message
        from utils.supabase_client import SUPABASE_ENABLED, get_session
        session_data = get_session(session_id)
        if session_data and session_data.get("is_active") is False:
            logger.info(f"Session {session_id} is closed, rejecting message from customer")
            # Store user message but don't process
            conversation_history.add_message(
                user_id=request.user_id,
                session_id=session_id,
                role="user",
                content=sanitized_message
            )
            return ChatResponse(
                response="This conversation has been closed. Please start a new conversation or contact support if you need assistance.",
                session_id=session_id,
                agent_used="system",
                response_time=0.1,
                metrics=metrics.get_counts()
            )
        
        # Check if a human agent has already taken over this session
        # If so, don't process with AI agent - human agent is handling it
        from utils.supabase_client import get_messages
        existing_messages = get_messages(request.user_id, session_id=session_id, limit=50)
        has_human_agent_message = any(
            msg.get("role") == "assistant" and 
            (msg.get("metadata", {}).get("is_human_agent") == True or 
             msg.get("metadata", {}).get("agent_used") == "human_agent" or
             msg.get("agent_used") == "human_agent")
            for msg in existing_messages
        )
        
        if has_human_agent_message:
            logger.info(f"Human agent has taken over session {session_id}, skipping AI agent response")
            # Store user message but don't process with AI
            conversation_history.add_message(
                user_id=request.user_id,
                session_id=session_id,
                role="user",
                content=sanitized_message
            )
            # Return a message indicating human agent is handling
            return ChatResponse(
                response="Your message has been received. A human agent is handling your request and will respond shortly.",
                session_id=session_id,
                agent_used="human_agent",
                response_time=0.1,
                metrics=metrics.get_counts()
            )
        
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
        
        # Set context for conversation tools (so they can access session_id and user_id)
        from tools.conversation_tool import set_conversation_context, clear_conversation_context
        set_conversation_context(session_id=session_id, user_id=request.user_id)
        logger.info(f"Set conversation context: session_id={session_id}, user_id={request.user_id}")
        
        # Set customer_id context for order tools
        # Priority: 1) customer_id from request, 2) customer_id from message, 3) existing context, 4) user_id as default
        from tools.order_tool import set_order_context, get_order_context, update_customer_id, clear_order_context
        
        # Get existing context to preserve customer_id if already set
        existing_context = get_order_context(session_id)
        existing_customer_id = existing_context.get("customer_id")
        
        # Determine customer_id: use from request if provided, then from message, then existing, then user_id
        if request.customer_id:
            customer_id = request.customer_id
            # Update context with customer_id from request
            update_customer_id(session_id, customer_id)
            logger.info(f"Customer ID from request: {customer_id}")
        elif customer_id_from_message:
            customer_id = customer_id_from_message
            # Update context with new customer_id
            update_customer_id(session_id, customer_id)
            logger.info(f"Customer ID extracted from message: {customer_id}")
        elif existing_customer_id:
            customer_id = existing_customer_id
            logger.info(f"Using existing customer_id from context: {customer_id}")
        else:
            customer_id = initial_customer_id  # Use the one we set during session creation
            logger.info(f"Using customer_id from session creation: {customer_id}")
        
        # Ensure session has customer_id (always update to be sure)
        if customer_id:
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
                        # Always update customer_id in session in Supabase to ensure it's set
                        supabase.table("sessions").update({"customer_id": customer_id}).eq("session_id", session_id).execute()
                        logger.info(f"Ensured session customer_id is set to: {customer_id}")
                else:
                    # Update in JSON metadata
                    session = session_metadata.get_session(session_id)
                    if session:
                        with session_metadata._lock:
                            session_metadata._metadata[session_id]["customer_id"] = customer_id
                            session_metadata._save_sessions()
            except Exception as e:
                logger.warning(f"Could not update customer_id in session: {e}")
        
        try:
            # Get agent response with timeout protection
            import time
            response_start_time = time.time()
            response_text = ""
            detected_agent = None  # Will be set by get_response() if an agent is detected
            
            async def get_response():
                """Inner async function for timeout handling."""
                nonlocal response_text, detected_agent
                all_texts = []  # Collect all text responses
                tool_results = []  # Collect tool results as fallback
                last_tool_result = None  # Keep track of last tool result for fallback
                
                try:
                    async for event in runner.run_async(
                        user_id=request.user_id,
                        session_id=session_id,
                        new_message=message
                    ):
                        # Detect which agent tool was called
                        if event.content and event.content.parts:
                            for part in event.content.parts:
                                # Check for function calls to detect agent usage
                                if hasattr(part, "function_call") and part.function_call:
                                    function_name = getattr(part.function_call, "name", None)
                                    if function_name:
                                        # AgentTool functions can be named after the agent
                                        # Try exact match first, then partial match
                                        function_lower = function_name.lower()
                                        
                                        # Check for agent names in function name
                                        if "faq" in function_lower or function_lower == "faq_agent":
                                            detected_agent = "faq_agent"
                                            logger.info(f"Detected agent: faq_agent via function {function_name}")
                                        elif "order" in function_lower and "agent" in function_lower:
                                            detected_agent = "order_agent"
                                            logger.info(f"Detected agent: order_agent via function {function_name}")
                                        elif "sentiment" in function_lower:
                                            detected_agent = "sentiment_agent"
                                            logger.info(f"Detected agent: sentiment_agent via function {function_name}")
                                        elif "escalation" in function_lower or "ticket" in function_lower:
                                            detected_agent = "escalation_agent"
                                            logger.info(f"Detected agent: escalation_agent via function {function_name}")
                                
                                # Also check function_response for agent information
                                if hasattr(part, "function_response") and part.function_response:
                                    try:
                                        # Sometimes the agent name is in the response metadata
                                        result = part.function_response.result
                                        if isinstance(result, dict):
                                            # Check if result contains agent info
                                            if "agent" in result:
                                                detected_agent = result["agent"]
                                                logger.info(f"Detected agent from response: {detected_agent}")
                                            elif "agent_used" in result:
                                                detected_agent = result["agent_used"]
                                                logger.info(f"Detected agent_used from response: {detected_agent}")
                                    except:
                                        pass
                                
                                # Collect text from any event with content
                                # IMPORTANT: Collect ALL text, not just final responses
                                # This ensures we capture agent responses even if orchestrator continues
                                if hasattr(part, "text") and part.text:
                                    text = part.text.strip()
                                    if text and len(text) > 5:  # Only meaningful text
                                        all_texts.append(text)
                                        # Prefer final response if available, but don't break
                                        # We want to collect all responses from all agents
                                        if event.is_final_response() and not response_text:
                                            response_text = text
                                            # Don't break here - continue to collect all agent responses
                                
                                # Also collect function_response results as fallback
                                if hasattr(part, "function_response") and part.function_response:
                                    try:
                                        result = part.function_response.result
                                        last_tool_result = result  # Store for fallback
                                        
                                        # Check for agent info in function response
                                        if isinstance(result, dict):
                                            # Store the full dict for later processing
                                            tool_results.append(result)
                                            last_tool_result = result
                                            
                                            # Try to detect agent from response content
                                            # Look for patterns that indicate which agent responded
                                            result_str = str(result).lower()
                                            if not detected_agent:  # Only if not already detected
                                                if "order" in result_str and ("status" in result_str or "tracking" in result_str):
                                                    detected_agent = "order_agent"
                                                    logger.info("Detected order_agent from response content")
                                                elif "ticket" in result_str and ("created" in result_str or "id" in result_str):
                                                    detected_agent = "escalation_agent"
                                                    logger.info("Detected escalation_agent from response content")
                                                elif "refund" in result_str or "shipping" in result_str or "policy" in result_str:
                                                    detected_agent = "faq_agent"
                                                    logger.info("Detected faq_agent from response content")
                                            
                                            # Also extract specific fields if available
                                            if "answer" in result:
                                                tool_results.append(result["answer"])
                                            elif "error_message" in result:
                                                tool_results.append(result["error_message"])
                                        elif isinstance(result, str) and len(result) > 10:
                                            # CRITICAL: AgentTool returns the agent's text response as a string
                                            # This is the actual response from the specialized agent!
                                            tool_results.append(result)
                                            all_texts.append(result)  # Also add to all_texts so it can be selected as final response
                                            logger.info(f"Captured agent response text from function_response (length: {len(result)})")
                                            
                                            # Try to detect agent from text content
                                            if not detected_agent:
                                                result_lower = result.lower()
                                                if "order" in result_lower and ("status" in result_lower or "tracking" in result_lower or "order id" in result_lower):
                                                    detected_agent = "order_agent"
                                                    logger.info("Detected order_agent from text content")
                                                elif "ticket" in result_lower and ("created" in result_lower or "ticket id" in result_lower):
                                                    detected_agent = "escalation_agent"
                                                    logger.info("Detected escalation_agent from text content")
                                                elif "refund" in result_lower or "shipping" in result_lower or "policy" in result_lower:
                                                    detected_agent = "faq_agent"
                                                    logger.info("Detected faq_agent from text content")
                                    except:
                                        pass
                        
                        # Don't break early - we want to collect all agent responses
                        # The orchestrator might call multiple agents, and we need all their responses
                        # Only break if we have a final response AND it's from the orchestrator itself
                        # (not from an agent tool call)
                        if response_text and event.is_final_response():
                            # Check if this is the orchestrator's final response (not an agent tool)
                            # If it's an agent tool response, continue to collect
                            is_agent_tool = False
                            if event.content and event.content.parts:
                                for part in event.content.parts:
                                    if hasattr(part, "function_call") or hasattr(part, "function_response"):
                                        is_agent_tool = True
                                        break
                            # Only break if it's the orchestrator's own final response
                            if not is_agent_tool:
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
                # This captures text from specialized agents even if orchestrator doesn't generate final text
                if not response_text and all_texts:
                    # Filter meaningful texts (longer than 20 chars)
                    meaningful = [t for t in all_texts if len(t) > 20]
                    if meaningful:
                        # Prefer agent responses over orchestrator responses
                        # Agent responses are usually more specific and helpful
                        agent_responses = [t for t in meaningful if any(keyword in t.lower() for keyword in ["order", "ticket", "refund", "policy", "shipping"])]
                        if agent_responses:
                            response_text = max(agent_responses, key=len)
                            logger.info(f"Using agent response from collected texts (length: {len(response_text)})")
                        else:
                            response_text = max(meaningful, key=len)
                            logger.info(f"Using longest text from collected responses (length: {len(response_text)})")
                
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
                # This is critical when orchestrator calls a specialized agent but doesn't generate final text
                if not response_text and tool_results:
                    # Prioritize string results from agent tools (they contain the actual agent responses)
                    string_results = [t for t in tool_results if isinstance(t, str) and len(t) > 20]
                    if string_results:
                        # If we have multiple agent responses, prefer the most relevant one
                        # (usually the longest, but could be enhanced with relevance scoring)
                        response_text = max(string_results, key=len)
                        logger.info(f"Using agent tool response from tool_results (length: {len(response_text)})")
                    elif tool_results:
                        # Fallback to any result
                        longest = max(tool_results, key=lambda x: len(str(x)))
                        response_text = str(longest) if not isinstance(longest, str) else longest
                        logger.info(f"Using fallback tool result (length: {len(response_text)})")
                
                # CRITICAL: If we still don't have a response but have collected texts from agents,
                # use the best one. This handles cases where orchestrator calls agents but doesn't
                # generate its own final response
                if not response_text and all_texts:
                    # Filter meaningful texts
                    meaningful = [t for t in all_texts if len(t) > 20]
                    if meaningful:
                        # Prefer agent-specific responses (they're usually more helpful)
                        agent_keywords = ["order", "ticket", "refund", "policy", "shipping", "cancelled", "status"]
                        agent_responses = [t for t in meaningful if any(kw in t.lower() for kw in agent_keywords)]
                        if agent_responses:
                            response_text = max(agent_responses, key=len)
                            logger.info(f"Using agent response from all_texts (length: {len(response_text)})")
                        else:
                            response_text = max(meaningful, key=len)
                            logger.info(f"Using longest text from all_texts (length: {len(response_text)})")
                
                # Return both response text and detected agent
                return response_text, detected_agent
        
            # Execute with 15 second timeout (reduced from 30)
            result = await with_timeout(
                get_response(),
                timeout_seconds=15,
                default_response=("I apologize, but the request took too long to process. Please try again with a simpler question.", None)
            )
            
            # Handle both tuple (response, agent) and string (fallback) responses
            if isinstance(result, tuple):
                response_text, detected_agent = result
            else:
                response_text = result
                detected_agent = None
            
            if not response_text:
                response_text = "I apologize, but I couldn't generate a response. Please try rephrasing your question."
        finally:
            # Clear context after processing
            clear_ticket_context()
            from tools.conversation_tool import clear_conversation_context
            clear_conversation_context()
        
        # Calculate response time
        response_time = time.time() - response_start_time
        
        metrics.increment("messages_sent")
        logger.info(f"Response sent to user: {request.user_id}")
        
        # Extract agent_used from response if available (default to orchestrator)
        # Use detected_agent if available, otherwise default to orchestrator
        agent_used = detected_agent if detected_agent else "orchestrator"
        
        # Log which agent was detected
        if detected_agent:
            logger.info(f"✅ Agent detected: {detected_agent} for user {request.user_id}")
        else:
            logger.info(f"⚠️ No agent detected, defaulting to orchestrator for user {request.user_id}")
        
        # Initialize A/B testing variant (will be set later if test is active)
        ab_variant = None
        
        # A/B Testing - Get variant if test is active (before storing message)
        try:
            from utils.ab_testing import get_ab_testing
            ab_testing = get_ab_testing()
            
            # Check if there's an active test for this agent
            if agent_used and agent_used in ab_testing.active_tests:
                # Get variant for this user (consistent hashing)
                ab_variant = ab_testing.get_variant(agent_used, request.user_id)
        except Exception as e:
            logger.debug(f"Could not get A/B testing variant: {e}")
            ab_variant = None
        
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
        # Prepare metadata with A/B testing variant
        message_metadata = {
            "response_time": response_time,
            "agent": agent_used
        }
        if ab_variant:
            message_metadata["ab_test_variant"] = ab_variant
        
        conversation_history.add_message(
            user_id=request.user_id,
            session_id=session_id,
            role="assistant",
            content=response_text,
            metadata=message_metadata
        )
        
        # QA & Compliance Check
        qa_result = None
        try:
            from utils.qa_checker import get_qa_checker
            qa_checker = get_qa_checker()
            qa_result = qa_checker.check_response(
                response=response_text,
                user_message=sanitized_message,
                agent_used=agent_used
            )
            
            # Log quality issues if any
            if qa_result.get("overall_status") != "pass":
                logger.warning(
                    f"QA check for session {session_id}: {qa_result.get('overall_status')} "
                    f"(score: {qa_result.get('quality_score', 0):.2f})"
                )
                if qa_result.get("quality_issues"):
                    logger.warning(f"Quality issues: {qa_result.get('quality_issues')}")
            
            # Store QA result in message metadata for analytics
            try:
                from utils.supabase_client import SUPABASE_ENABLED, supabase
                if SUPABASE_ENABLED:
                    # Update last message with QA metadata
                    supabase.table("messages").update({
                        "metadata": {
                            "response_time": response_time,
                            "agent": agent_used,
                            "qa_score": qa_result.get("quality_score"),
                            "qa_status": qa_result.get("overall_status"),
                            "compliance_flags": qa_result.get("compliance_flags", [])
                        }
                    }).eq("session_id", session_id).order("timestamp", desc=True).limit(1).execute()
            except Exception as e:
                logger.debug(f"Could not store QA metadata: {e}")
                
        except Exception as e:
            logger.warning(f"Could not run QA check: {e}")
            qa_result = None
        
        # A/B Testing - Record metrics if test is active (ab_variant already set above)
        if ab_variant:
            try:
                from utils.ab_testing import get_ab_testing
                ab_testing = get_ab_testing()
                
                # Record metrics (will be updated with feedback later)
                ab_testing.record_metrics(
                    agent_name=agent_used,
                    variant=ab_variant,
                    response_time=response_time,
                    escalated=False,  # Will be updated if ticket created
                    resolved=False,  # Will be updated based on feedback
                    thumbs_up=False,  # Will be updated from feedback
                    thumbs_down=False  # Will be updated from feedback
                )
                
                logger.debug(f"A/B Testing: Recorded metrics for {agent_used} variant {ab_variant}")
            except Exception as e:
                logger.debug(f"Could not record A/B testing metrics: {e}")
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            agent_used=agent_used,
            response_time=response_time,
            metrics=metrics.get_counts(),
            quality_score=qa_result.get("quality_score") if qa_result else None,
            quality_status=qa_result.get("overall_status") if qa_result else None,
            compliance_flags=qa_result.get("compliance_flags") if qa_result else None,
            ab_test_variant=ab_variant
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


@app.get("/ab-testing/results")
async def get_ab_test_results(
    agent_name: Optional[str] = Query(None, description="Agent name to get results for")
):
    """
    Get A/B test results.
    
    Args:
        agent_name: Optional agent name to filter results
        
    Returns:
        A/B test results with statistical analysis
    """
    try:
        from utils.ab_testing import get_ab_testing
        ab_testing = get_ab_testing()
        
        if agent_name:
            result = ab_testing.get_test_results(agent_name)
            return result
        else:
            # Return all tests
            all_tests = ab_testing.get_all_tests()
            return {
                "status": "success",
                "tests": all_tests
            }
    except Exception as e:
        logger.error(f"Error getting A/B test results: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting A/B test results: {str(e)}")


@app.post("/ab-testing/create")
async def create_ab_test(request: dict):
    """
    Create a new A/B test for an agent.
    
    Body:
    {
        "agent_name": "order_agent",
        "variant_a_instruction": "Current instruction...",
        "variant_b_instruction": "Test instruction...",
        "description": "Optional description"
    }
    """
    try:
        from utils.ab_testing import get_ab_testing
        ab_testing = get_ab_testing()
        
        agent_name = request.get("agent_name")
        variant_a = request.get("variant_a_instruction")
        variant_b = request.get("variant_b_instruction")
        description = request.get("description")
        
        if not agent_name or not variant_a or not variant_b:
            raise HTTPException(status_code=400, detail="agent_name, variant_a_instruction, and variant_b_instruction are required")
        
        success = ab_testing.create_test(
            agent_name=agent_name,
            variant_a_instruction=variant_a,
            variant_b_instruction=variant_b,
            description=description
        )
        
        if success:
            return {
                "status": "success",
                "message": f"A/B test created for {agent_name}",
                "test": ab_testing.get_test_results(agent_name)
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create A/B test")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating A/B test: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating A/B test: {str(e)}")


@app.get("/qa/check")
async def check_qa(
    session_id: Optional[str] = Query(None, description="Session ID to check"),
    limit: int = Query(10, description="Number of recent responses to check")
):
    """
    Get QA results for recent responses.
    
    Returns QA report with quality scores and issues.
    """
    try:
        from utils.qa_checker import get_qa_checker
        from utils.supabase_client import get_messages, SUPABASE_ENABLED
        
        qa_checker = get_qa_checker()
        
        # Get recent messages
        if SUPABASE_ENABLED and session_id:
            messages = get_messages(user_id="", session_id=session_id, limit=limit)
        else:
            from memory.conversation_history import conversation_history
            messages = conversation_history.get_history(session_id=session_id, limit=limit) if session_id else []
        
        # Filter assistant messages
        assistant_messages = [
            {
                "response": msg.get("content", ""),
                "user_message": "",
                "agent_used": msg.get("metadata", {}).get("agent", "unknown")
            }
            for msg in messages if msg.get("role") == "assistant"
        ]
        
        if not assistant_messages:
            return {
                "status": "no_data",
                "message": "No assistant messages found"
            }
        
        # Run batch QA check
        batch_result = qa_checker.check_batch(assistant_messages)
        
        return {
            "status": "success",
            "qa_report": batch_result,
            "checked_responses": len(assistant_messages)
        }
        
    except Exception as e:
        logger.error(f"Error in QA check endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error checking QA: {str(e)}")

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
    active_sessions = 0
    try:
        from utils.supabase_client import SUPABASE_ENABLED, get_user_sessions
        if SUPABASE_ENABLED:
            # Get all sessions from Supabase and count those with messages
            from supabase import create_client
            import os
            from dotenv import load_dotenv
            load_dotenv()
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            if supabase_url and supabase_key:
                supabase = create_client(supabase_url, supabase_key)
                # Get all sessions with message_count > 0 AND is_active = True (exclude closed sessions)
                result = supabase.table("sessions").select("session_id, message_count, is_active").gt("message_count", 0).eq("is_active", True).execute()
                active_sessions = len(result.data) if result.data else 0
        else:
            # Fallback to session_metadata
            from memory.session_metadata import session_metadata
            all_sessions = session_metadata.get_all_sessions()
            active_sessions = sum(1 for s in all_sessions.values() if s.get("message_count", 0) > 0 and s.get("is_active", True) is not False) if isinstance(all_sessions, dict) else 0
    except Exception as e:
        logger.warning(f"Error getting active sessions: {e}")
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
            # Check both avg_rating and average_rating (function returns average_rating)
            if feedback_stats:
                avg_satisfaction = float(feedback_stats.get("average_rating") or feedback_stats.get("avg_rating") or 0.0)
        else:
            # Fallback: try to get from feedback manager
            from utils.feedback_manager import FeedbackManager
            feedback_mgr = FeedbackManager()
            insights = feedback_mgr.get_insights()
            if insights and insights.get("average_rating"):
                avg_satisfaction = float(insights.get("average_rating", 0.0))
    except Exception as e:
        logger.warning(f"Error getting feedback stats: {e}")
    
    # Get additional metrics for better dashboard
    closed_sessions = 0
    open_tickets = 0
    resolved_tickets = 0
    avg_response_time = 0.0
    
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
                # Count closed sessions
                closed_result = supabase.table("sessions").select("session_id").eq("is_active", False).execute()
                closed_sessions = len(closed_result.data) if closed_result.data else 0
                
                # Count open and resolved tickets
                open_result = supabase.table("tickets").select("ticket_id").in_("status", ["open", "in_progress"]).execute()
                open_tickets = len(open_result.data) if open_result.data else 0
                
                resolved_result = supabase.table("tickets").select("ticket_id").eq("status", "resolved").execute()
                resolved_tickets = len(resolved_result.data) if resolved_result.data else 0
                
                # Calculate average response time from messages metadata
                messages_result = supabase.table("messages").select("metadata").eq("role", "assistant").limit(100).execute()
                response_times = []
                if messages_result.data:
                    for msg in messages_result.data:
                        metadata = msg.get("metadata", {})
                        if metadata and metadata.get("response_time"):
                            response_times.append(float(metadata["response_time"]))
                if response_times:
                    avg_response_time = sum(response_times) / len(response_times)
    except Exception as e:
        logger.warning(f"Error getting additional analytics: {e}")
    
    # Calculate resolution rate
    resolution_rate = 0.0
    if len(tickets_list) > 0:
        resolution_rate = (resolved_tickets / len(tickets_list)) * 100
    
    # Return data in the format expected by frontend - all from database, not in-memory
    result = {
        "total_messages": total_messages,
        "active_sessions": active_sessions,
        "closed_sessions": closed_sessions,
        "interactions": interactions,
        "avg_satisfaction": avg_satisfaction,
        "tickets_created": len(tickets_list),
        "open_tickets": open_tickets,
        "resolved_tickets": resolved_tickets,
        "resolution_rate": round(resolution_rate, 1),
        "avg_response_time": round(avg_response_time, 2),
    }
    return result


@app.get("/analytics/daily")
async def get_daily_analytics():
    """Get daily analytics data for charts (last 7 days)."""
    from datetime import datetime, timedelta
    from collections import defaultdict
    
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
                
                # Get last 7 days
                today = datetime.now().date()
                days_data = []
                day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                
                for i in range(6, -1, -1):  # Last 7 days
                    target_date = today - timedelta(days=i)
                    day_name = day_names[target_date.weekday()]
                    
                    # Count messages for this day
                    start_of_day = datetime.combine(target_date, datetime.min.time())
                    end_of_day = datetime.combine(target_date, datetime.max.time())
                    
                    result = supabase.table("messages").select("id", count="exact").gte("created_at", start_of_day.isoformat()).lte("created_at", end_of_day.isoformat()).limit(1).execute()
                    message_count = result.count if hasattr(result, 'count') and result.count is not None else 0
                    interactions = message_count // 2  # Each interaction = user + assistant
                    
                    # Get average satisfaction for this day
                    feedback_result = supabase.table("feedback").select("rating").gte("created_at", start_of_day.isoformat()).lte("created_at", end_of_day.isoformat()).execute()
                    ratings = [f.get("rating") for f in feedback_result.data if f.get("rating") is not None]
                    avg_satisfaction = sum(ratings) / len(ratings) if ratings else 0.0
                    
                    days_data.append({
                        "day": day_name,
                        "interactions": interactions,
                        "satisfaction": round(avg_satisfaction, 1)
                    })
                
                return days_data
    except Exception as e:
        logger.warning(f"Error getting daily analytics: {e}")
    
    # Fallback: return empty data
    return [
        {"day": "Mon", "interactions": 0, "satisfaction": 0},
        {"day": "Tue", "interactions": 0, "satisfaction": 0},
        {"day": "Wed", "interactions": 0, "satisfaction": 0},
        {"day": "Thu", "interactions": 0, "satisfaction": 0},
        {"day": "Fri", "interactions": 0, "satisfaction": 0},
        {"day": "Sat", "interactions": 0, "satisfaction": 0},
        {"day": "Sun", "interactions": 0, "satisfaction": 0},
    ]


@app.get("/analytics/ticket-status")
async def get_ticket_status_distribution():
    """Get ticket status distribution for pie chart."""
    from tools.ticket_tool import get_all_tickets
    
    all_tickets = get_all_tickets()
    if isinstance(all_tickets, dict):
        tickets_list = list(all_tickets.values())
    else:
        tickets_list = all_tickets if isinstance(all_tickets, list) else []
    
    # Count by status
    status_counts = {
        "Open": 0,
        "In Progress": 0,
        "Resolved": 0,
        "Closed": 0
    }
    
    for ticket in tickets_list:
        status = ticket.get("status", "").title()
        if status == "In_Progress" or status == "In Progress":
            status_counts["In Progress"] += 1
        elif status in status_counts:
            status_counts[status] += 1
        elif status:
            # Handle other statuses
            status_counts["Open"] += 1
    
    # Convert to array format for chart
    chart_colors = [
        "hsl(var(--chart-1))",
        "hsl(var(--chart-2))",
        "hsl(var(--chart-3))",
        "hsl(var(--chart-4))"
    ]
    
    result = []
    for i, (status, count) in enumerate(status_counts.items()):
        if count > 0:  # Only include statuses with tickets
            result.append({
                "name": status,
                "value": count,
                "fill": chart_colors[i % len(chart_colors)]
            })
    
    return result


@app.get("/feedback/improvements/{agent_name}")
async def get_agent_improvements(agent_name: str):
    """
    Get improvement suggestions and applied refinements for an agent.
    
    Shows how feedback is being used to improve the agent.
    """
    try:
        from utils.supabase_client import SUPABASE_ENABLED, get_agent_refinements, get_feedback_insights
        
        if not SUPABASE_ENABLED:
            return {"error": "Supabase not enabled"}
        
        # Get refinements
        all_refinements = get_agent_refinements(agent_name=agent_name)
        pending = [r for r in all_refinements if r.get("status") == "pending"]
        applied = [r for r in all_refinements if r.get("status") == "applied"]
        
        # Get feedback insights
        insights = get_feedback_insights(agent_name=agent_name)
        
        return {
            "agent_name": agent_name,
            "pending_refinements": len(pending),
            "applied_refinements": len(applied),
            "total_refinements": len(all_refinements),
            "pending_details": pending[:5],  # Last 5 pending
            "applied_details": applied[-5:],  # Last 5 applied
            "feedback_insights": insights[-10:] if insights else [],  # Last 10 insights
            "total_feedback_count": len(insights) if insights else 0,
            "message": f"Feedback is being analyzed to improve {agent_name}. Refinements are automatically applied daily at 2 AM."
        }
    except Exception as e:
        logger.error(f"Error getting improvements: {e}")
        return {"error": str(e)}


@app.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """
    Submit user feedback.
    
    Args:
        request: FeedbackRequest with session_id, feedback_type, and optional fields
    """
    # Essayer Supabase d'abord
    try:
        from utils.supabase_client import SUPABASE_ENABLED, create_feedback
        from utils.feedback_manager import FeedbackManager
        
        if SUPABASE_ENABLED and request.user_id:
            # Try to get ticket_id from session if not provided
            ticket_id = request.ticket_id
            if not ticket_id and request.session_id:
                try:
                    # Get ticket_id from session using the same logic as the endpoint
                    from utils.supabase_client import SUPABASE_ENABLED as SUPABASE_CHECK, get_tickets
                    if SUPABASE_CHECK:
                        tickets = get_tickets(session_id=request.session_id)
                        if tickets and len(tickets) > 0:
                            # Get the most recent ticket
                            ticket_id = tickets[0].get("ticket_id")
                    else:
                        # Fallback: try JSON
                        from tools.ticket_tool import get_all_tickets
                        all_tickets = get_all_tickets()
                        if isinstance(all_tickets, dict):
                            tickets = [t for t in all_tickets.values() if t.get("session_id") == request.session_id]
                        else:
                            tickets = [t for t in all_tickets if t.get("session_id") == request.session_id]
                        if tickets and len(tickets) > 0:
                            tickets.sort(key=lambda x: x.get("created_at", ""), reverse=True)
                            ticket_id = tickets[0].get("ticket_id")
                except Exception as e:
                    logger.debug(f"Could not get ticket_id from session: {e}")
                    ticket_id = None
            
            result = create_feedback(
                session_id=request.session_id,
                user_id=request.user_id,
                feedback_type=request.feedback_type,
                rating=request.rating,
                comment=request.comment,
                reason=request.reason,
                category=request.category,
                agent_used=request.agent_used,
                ticket_id=ticket_id
            )
            if result.get("status") == "success":
                analytics.log_feedback(request.session_id, request.feedback_type, request.rating, request.comment)
                
                # Auto-extract reason and category from comment if not provided
                reason = request.reason
                category = request.category
                
                if not reason and request.comment:
                    comment_lower = request.comment.lower()
                    # Extract reason from comment
                    if any(word in comment_lower for word in ["incorrect", "wrong", "error", "mistake"]):
                        reason = "incorrect"
                    elif any(word in comment_lower for word in ["missing", "incomplete", "more info", "details"]):
                        reason = "missing_info"
                    elif any(word in comment_lower for word in ["unclear", "confusing", "vague", "don't understand"]):
                        reason = "unclear"
                    elif any(word in comment_lower for word in ["slow", "delay", "waiting", "took too long"]):
                        reason = "slow"
                    elif any(word in comment_lower for word in ["helpful", "useful", "good", "great", "excellent"]):
                        reason = "helpful"
                
                if not category and request.comment:
                    comment_lower = request.comment.lower()
                    # Extract category from comment
                    if any(word in comment_lower for word in ["wrong", "incorrect", "error", "accurate", "accuracy"]):
                        category = "accuracy"
                    elif any(word in comment_lower for word in ["slow", "fast", "quick", "speed", "delay"]):
                        category = "speed"
                    elif any(word in comment_lower for word in ["unclear", "confusing", "understand", "explain", "clarity"]):
                        category = "clarity"
                    elif any(word in comment_lower for word in ["helpful", "useful", "helpfulness"]):
                        category = "helpfulness"
                    elif any(word in comment_lower for word in ["missing", "incomplete", "complete", "details"]):
                        category = "completeness"
                
                # If still no reason/category, set defaults based on feedback_type
                if not reason:
                    if request.feedback_type == "thumbs_up":
                        reason = "helpful"
                    elif request.feedback_type == "thumbs_down":
                        reason = "low_rating"
                
                if not category:
                    category = "general"
                
                # Update feedback in database with extracted reason/category if they were missing
                if (not request.reason and reason) or (not request.category and category):
                    try:
                        from supabase import create_client
                        import os
                        supabase_url = os.getenv("SUPABASE_URL")
                        supabase_key = os.getenv("SUPABASE_KEY")
                        if supabase_url and supabase_key:
                            supabase = create_client(supabase_url, supabase_key)
                            update_data = {}
                            if not request.reason and reason:
                                update_data["reason"] = reason
                            if not request.category and category:
                                update_data["category"] = category
                            if update_data:
                                supabase.table("feedback").update(update_data).eq("feedback_id", result.get("feedback_id")).execute()
                    except Exception as e:
                        logger.warning(f"Failed to update feedback with extracted fields: {e}")
                
                # Analyze feedback for improvements (async, non-blocking)
                try:
                    feedback_manager = FeedbackManager()
                    feedback_data = {
                        "id": result.get("feedback_id"),
                        "session_id": request.session_id,
                        "user_id": request.user_id,
                        "feedback_type": request.feedback_type,
                        "rating": request.rating,
                        "comment": request.comment,
                        "reason": reason,  # Use extracted or provided reason
                        "category": category,  # Use extracted or provided category
                        "agent_used": request.agent_used or "orchestrator"
                    }
                    # Analyze feedback asynchronously (won't block response)
                    feedback_manager._analyze_feedback_async(feedback_data)
                except Exception as e:
                    logger.warning(f"Failed to analyze feedback: {e}")
                    import traceback
                    traceback.print_exc()
                
                # Record A/B Testing metrics from feedback
                try:
                    from utils.ab_testing import get_ab_testing
                    ab_testing = get_ab_testing()
                    
                    if request.agent_used and request.agent_used in ab_testing.active_tests:
                        # Get variant from most recent message metadata
                        try:
                            from utils.supabase_client import get_messages, SUPABASE_ENABLED
                            if SUPABASE_ENABLED:
                                recent_messages = get_messages(user_id=request.user_id, session_id=request.session_id, limit=1)
                                if recent_messages:
                                    variant = recent_messages[0].get("metadata", {}).get("ab_test_variant")
                                    if variant:
                                        # Calculate satisfaction score from feedback
                                        satisfaction = None
                                        if request.feedback_type == "thumbs_up":
                                            satisfaction = 1.0
                                        elif request.feedback_type == "thumbs_down":
                                            satisfaction = 0.0
                                        elif request.rating:
                                            satisfaction = request.rating / 5.0
                                        
                                        # Record metrics
                                        ab_testing.record_metrics(
                                            agent_name=request.agent_used,
                                            variant=variant,
                                            satisfaction_score=satisfaction,
                                            resolved=(request.feedback_type == "thumbs_up" or (request.rating and request.rating >= 4)),
                                            thumbs_up=(request.feedback_type == "thumbs_up"),
                                            thumbs_down=(request.feedback_type == "thumbs_down")
                                        )
                        except Exception as e:
                            logger.debug(f"Could not record A/B testing metrics from feedback: {e}")
                except Exception as e:
                    logger.debug(f"Could not process A/B testing for feedback: {e}")
                
                return {
                    "status": "success", 
                    "message": "Feedback recorded and will be analyzed for improvements", 
                    "feedback_id": result.get("feedback_id")
                }
    except Exception as e:
        logger.error(f"Error processing feedback: {e}")
        pass  # Fallback vers analytics
    
    # Fallback vers analytics (JSON)
    analytics.log_feedback(request.session_id, request.feedback_type, request.rating, request.comment)
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
async def get_user_sessions(user_id: str, customer_id: Optional[str] = Query(None)):
    """Get all sessions for a user with metadata, optionally filtered by customer_id."""
    sessions = session_metadata.get_user_sessions(user_id, customer_id)
    # Return array directly for frontend compatibility
    return sessions


@app.get("/sessions/all/active")
async def get_all_active_sessions():
    """Get all active sessions for human agent monitoring."""
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
                # Get all active sessions with messages
                result = supabase.table("sessions").select("*").eq("is_active", True).gt("message_count", 0).order("updated_at", desc=True).execute()
                sessions = result.data or []
                # Calculate message_count dynamically for each session
                for session in sessions:
                    try:
                        msg_result = supabase.table("messages").select("id", count="exact").eq("session_id", session["session_id"]).execute()
                        session["message_count"] = msg_result.count if hasattr(msg_result, 'count') and msg_result.count is not None else 0
                    except Exception as e:
                        logger.warning(f"Error calculating message_count for session {session['session_id']}: {e}")
                        session["message_count"] = 0
                return sessions
        else:
            # Fallback to session_metadata
            from memory.session_metadata import session_metadata
            all_sessions = session_metadata.get_all_sessions()
            active_sessions = [
                s for s in all_sessions.values() 
                if s.get("message_count", 0) > 0 and s.get("is_active", True) is not False
            ] if isinstance(all_sessions, dict) else []
            # Sort by updated_at descending
            active_sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
            return active_sessions
    except Exception as e:
        logger.error(f"Error getting all active sessions: {e}")
        return []


class CreateSessionRequest(BaseModel):
    user_id: str
    name: Optional[str] = None
    customer_id: Optional[str] = None


@app.put("/sessions/{session_id}/close")
async def close_session(session_id: str):
    """
    Mark a session as inactive/closed.
    This prevents the AI agent from responding to new messages in this session.
    """
    try:
        from utils.supabase_client import SUPABASE_ENABLED, supabase
        if SUPABASE_ENABLED:
            result = supabase.table("sessions").update({"is_active": False}).eq("session_id", session_id).execute()
            if result.data:
                logger.info(f"Session {session_id} marked as inactive")
                return {"status": "success", "message": "Session closed successfully"}
            else:
                return {"status": "error", "message": "Session not found"}
        else:
            # Fallback to JSON storage
            from memory.session_metadata import session_metadata
            session_metadata.close_session(session_id)
            return {"status": "success", "message": "Session closed successfully"}
    except Exception as e:
        logger.error(f"Error closing session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to close session: {str(e)}")


@app.put("/sessions/{session_id}/reopen")
async def reopen_session(session_id: str):
    """
    Reopen a closed session (mark as active again).
    """
    try:
        from utils.supabase_client import SUPABASE_ENABLED, supabase
        if SUPABASE_ENABLED:
            result = supabase.table("sessions").update({"is_active": True}).eq("session_id", session_id).execute()
            if result.data:
                logger.info(f"Session {session_id} reopened")
                return {"status": "success", "message": "Session reopened successfully"}
            else:
                return {"status": "error", "message": "Session not found"}
        else:
            # Fallback to JSON storage
            from memory.session_metadata import session_metadata
            session_metadata.reopen_session(session_id)
            return {"status": "success", "message": "Session reopened successfully"}
    except Exception as e:
        logger.error(f"Error reopening session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reopen session: {str(e)}")


@app.post("/sessions/create")
async def create_session(request: CreateSessionRequest):
    """
    Create a new session with optional custom name and customer_id.
    
    Args:
        request: CreateSessionRequest with user_id, optional name, and optional customer_id
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
    
    # Create metadata with customer_id
    logger.info(f"Creating session with user_id={request.user_id}, customer_id={request.customer_id}, name={request.name}")
    metadata = session_metadata.create_session(session_id, request.user_id, request.name, request.customer_id)
    logger.info(f"Session created: {session_id}, metadata: {metadata}")
    
    # Ensure customer_id is saved in Supabase if provided
    if request.customer_id:
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
                    # Ensure customer_id is set in Supabase
                    result = supabase.table("sessions").update({"customer_id": request.customer_id}).eq("session_id", session_id).execute()
                    logger.info(f"Updated session customer_id in Supabase: {request.customer_id}")
        except Exception as e:
            logger.warning(f"Could not update customer_id in Supabase session: {e}")
    
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


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and all its messages."""
    # Delete session metadata (handles both Supabase and JSON)
    success = session_metadata.delete_session(session_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    return {
        "status": "success",
        "message": f"Session {session_id} deleted successfully"
    }


@app.get("/orders")
async def get_orders():
    """Get all orders from the system."""
    # Try Supabase first
    try:
        from utils.supabase_client import SUPABASE_ENABLED, get_orders as supabase_get_orders
        if SUPABASE_ENABLED:
            orders_list = supabase_get_orders()
            return {
                "orders": orders_list,
                "count": len(orders_list),
                "statuses": {
                    status: sum(1 for o in orders_list if o.get("status") == status)
                    for status in ["processing", "shipped", "delivering", "delivery_soon", "delivered", "cancelled"]
                }
            }
    except Exception as e:
        logger.warning(f"Error fetching orders from Supabase: {e}")
    
    # Fallback to JSON
    from tools.order_tool import _MOCK_ORDERS
    orders_list = list(_MOCK_ORDERS.values())
    return {
        "orders": orders_list,
        "count": len(orders_list),
        "statuses": {
            status: sum(1 for o in orders_list if o.get("status") == status)
            for status in ["processing", "shipped", "delivering", "delivery_soon", "delivered", "cancelled"]
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


@app.put("/orders/{order_id}")
async def update_order(order_id: str, order_data: dict):
    """Update an order in the system."""
    from tools.order_tool import lookup_order, add_order
    
    # Check if order exists
    existing_order = lookup_order(order_id)
    if existing_order.get("status") == "error":
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    
    # Merge existing order with updates
    updated_order = existing_order.get("order", {})
    updated_order.update(order_data)
    updated_order["order_id"] = order_id  # Ensure order_id doesn't change
    
    # Validate status if provided
    if "status" in order_data:
        valid_statuses = ["processing", "shipped", "delivering", "delivery_soon", "delivered", "cancelled"]
        if order_data["status"] not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
    
    # Auto-adjust status based on estimated_delivery date
    # If estimated_delivery is updated, check if we need to adjust status
    if "estimated_delivery" in order_data:
        from datetime import datetime, date
        try:
            estimated_delivery = order_data.get("estimated_delivery")
            if estimated_delivery:
                # Parse the date
                if isinstance(estimated_delivery, str):
                    try:
                        delivery_date = datetime.strptime(estimated_delivery.split("T")[0], "%Y-%m-%d").date()
                    except:
                        delivery_date = datetime.strptime(estimated_delivery, "%Y-%m-%d").date()
                else:
                    delivery_date = estimated_delivery
                
                today = date.today()
                current_status = updated_order.get("status", "").lower()
                
                # Only auto-update if status is not "delivered" or "cancelled"
                if current_status not in ["delivered", "cancelled"]:
                    # If date has passed (current date is after estimated_delivery) → "delivery_soon"
                    if delivery_date < today:
                        updated_order["status"] = "delivery_soon"
                    # If date is in the future → "delivering"
                    elif delivery_date >= today:
                        updated_order["status"] = "delivering"
        except Exception as e:
            logger.warning(f"Could not parse estimated_delivery date: {e}")
    
    # Update order
    success = add_order(updated_order)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update order")
    
    metrics.increment("orders_updated")
    
    return {
        "status": "success",
        "message": f"Order {order_id} updated successfully",
        "order": updated_order
    }


@app.delete("/orders/{order_id}")
async def delete_order(order_id: str):
    """Delete an order from the system."""
    from tools.order_tool import delete_order as remove_order
    
    success = remove_order(order_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    
    metrics.increment("orders_deleted")
    
    return {
        "status": "success",
        "message": f"Order {order_id} deleted successfully"
    }


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
        "shipped_at": str | None,  # YYYY-MM-DD (shipping date)
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
    valid_statuses = ["processing", "shipped", "delivery_soon", "delivered", "cancelled"]
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
    
    # Add summary to each ticket
    for ticket in tickets_list:
        ticket_id = ticket.get("ticket_id")
        session_id = ticket.get("session_id")
        user_id = ticket.get("user_id")
        
        if ticket_id and session_id and user_id:
            try:
                from utils.supabase_client import SUPABASE_ENABLED, get_session_summaries
                if SUPABASE_ENABLED:
                    summaries = get_session_summaries(session_id)
                    ticket_summary = next((s for s in summaries if s.get("ticket_id") == ticket_id), None)
                    if ticket_summary:
                        ticket["summary"] = ticket_summary.get("summary")
                else:
                    # Fallback to JSON
                    from utils.conversation_summarizer import _load_summaries
                    summaries = _load_summaries()
                    for key, summary_data in summaries.items():
                        if summary_data.get("ticket_id") == ticket_id:
                            ticket["summary"] = summary_data.get("summary")
                            break
            except Exception as e:
                logger.warning(f"Error fetching summary for ticket {ticket_id}: {e}")
    
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


@app.get("/tickets/by-session/{session_id}")
async def get_ticket_by_session(session_id: str):
    """
    Get the most recent ticket for a session.
    Returns the ticket_id if found, or null if no ticket exists.
    """
    try:
        from utils.supabase_client import SUPABASE_ENABLED, get_tickets
        if SUPABASE_ENABLED:
            tickets = get_tickets(session_id=session_id)
            if tickets and len(tickets) > 0:
                # Return the most recent ticket
                return {"ticket_id": tickets[0].get("ticket_id")}
            return {"ticket_id": None}
        
        # Fallback: try JSON
        from tools.ticket_tool import get_all_tickets
        all_tickets = get_all_tickets()
        if isinstance(all_tickets, dict):
            tickets = [t for t in all_tickets.values() if t.get("session_id") == session_id]
        else:
            tickets = [t for t in all_tickets if t.get("session_id") == session_id]
        
        if tickets and len(tickets) > 0:
            # Sort by created_at descending and return most recent
            tickets.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return {"ticket_id": tickets[0].get("ticket_id")}
        
        return {"ticket_id": None}
    except Exception as e:
        logger.error(f"Error fetching ticket by session: {e}")
        return {"ticket_id": None}


@app.put("/tickets/{ticket_id}/status")
async def update_ticket_status_endpoint(ticket_id: str, request: dict):
    """
    Update ticket status.
    
    Body:
    {
        "status": "open" | "in_progress" | "resolved" | "closed"
    }
    """
    try:
        new_status = request.get("status")
        if not new_status:
            raise HTTPException(status_code=400, detail="Status is required")
        
        from tools.ticket_modification_tool import update_ticket_status
        result = update_ticket_status(ticket_id, new_status)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("error_message", "Failed to update ticket status"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating ticket status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update ticket status: {str(e)}")


@app.post("/sessions/send-message")
async def send_session_message(request: dict):
    """
    Send a message directly to a session (human agent intervention).
    
    Body:
    {
        "session_id": str,
        "user_id": str,
        "customer_id": Optional[str],
        "message": str
    }
    """
    try:
        from utils.supabase_client import add_message
        
        session_id = request.get("session_id")
        user_id = request.get("user_id")
        message_content = request.get("message", "").strip()
        
        if not session_id or not user_id:
            raise HTTPException(status_code=400, detail="session_id and user_id are required")
        
        if not message_content:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Add message to conversation history as assistant message from human agent
        add_message(
            user_id=user_id,
            session_id=session_id,
            role="assistant",
            content=message_content,
            metadata={"agent_used": "human_agent", "is_human_agent": True},
            is_human_agent=True
        )
        
        logger.info(f"Human agent sent message to session {session_id}")
        
        return {
            "status": "success",
            "message": "Message sent successfully",
            "session_id": session_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message to session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


@app.post("/tickets/{ticket_id}/message")
async def send_ticket_message(ticket_id: str, request: dict):
    """
    Send a message to the customer from a ticket (human agent response).
    
    The message will appear in the customer's chat as if from a human agent.
    """
    try:
        from tools.ticket_tool import get_all_tickets
        from utils.supabase_client import add_message
        
        # Get ticket information
        all_tickets = get_all_tickets()
        ticket = None
        if isinstance(all_tickets, dict):
            ticket = all_tickets.get(ticket_id)
        elif isinstance(all_tickets, list):
            ticket = next((t for t in all_tickets if t.get("ticket_id") == ticket_id), None)
        
        if not ticket:
            raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
        
        # Get message content
        message_content = request.get("message", "").strip()
        if not message_content:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Get user_id and session_id from ticket
        user_id = ticket.get("user_id")
        session_id = ticket.get("session_id")
        
        if not user_id or not session_id:
            raise HTTPException(
                status_code=400, 
                detail="Ticket must have user_id and session_id to send messages"
            )
        
        # Add message to conversation history as assistant message from human agent
        add_message(
            user_id=user_id,
            session_id=session_id,
            role="assistant",
            content=message_content,
            is_human_agent=True
        )
        
        # Update ticket status to "in_progress" if it's "open"
        if ticket.get("status") == "open":
            try:
                from utils.supabase_client import SUPABASE_ENABLED, update_ticket_status
                if SUPABASE_ENABLED:
                    update_ticket_status(ticket_id, "in_progress")
            except Exception as e:
                logger.warning(f"Failed to update ticket status: {e}")
        
        logger.info(f"Human agent message sent for ticket {ticket_id} to user {user_id}")
        
        return {
            "status": "success",
            "message": "Message sent to customer",
            "ticket_id": ticket_id,
            "user_id": user_id,
            "session_id": session_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending ticket message: {e}")
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")


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


# ============================================================================
# Agent Improvement & KB Update Endpoints
# ============================================================================

@app.get("/agent-refinements/{agent_name}")
async def get_agent_refinements_endpoint(agent_name: str):
    """Get pending refinements for an agent."""
    try:
        from utils.agent_improver import AgentImprover
        improver = AgentImprover()
        refinements = improver.get_pending_refinements(agent_name=agent_name)
        summary = improver.get_improvement_summary(agent_name)
        return {
            "agent_name": agent_name,
            "pending_refinements": refinements,
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Error getting agent refinements: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent-refinements/{agent_name}/apply")
async def apply_agent_refinements(agent_name: str):
    """Apply pending refinements to an agent."""
    try:
        from utils.agent_improver import AgentImprover
        from agents import orchestrator_agent, faq_agent, order_agent, escalation_agent
        
        # Map agent names to modules
        agent_modules = {
            "orchestrator": orchestrator_agent,
            "faq_agent": faq_agent,
            "order_agent": order_agent,
            "escalation_agent": escalation_agent
        }
        
        agent_module = agent_modules.get(agent_name)
        if not agent_module:
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
        
        improver = AgentImprover()
        applied_count = improver.auto_apply_refinements(agent_name, agent_module)
        
        return {
            "status": "success",
            "agent_name": agent_name,
            "refinements_applied": applied_count,
            "message": f"Applied {applied_count} refinements to {agent_name}"
        }
    except Exception as e:
        logger.error(f"Error applying agent refinements: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/kb-updates")
async def get_kb_updates_endpoint(status: Optional[str] = None):
    """
    Get KB update suggestions.
    
    Status options:
    - "pending": Suggestions waiting for manual approval (default)
    - "applied": Already applied to FAQ
    - "rejected": Rejected by company
    """
    try:
        from utils.supabase_client import get_kb_updates
        updates = get_kb_updates(status=status or "pending")
        return {
            "updates": updates,
            "count": len(updates),
            "note": "KB updates require manual approval. Use POST /kb-updates/{update_id}/apply to approve."
        }
    except Exception as e:
        logger.error(f"Error getting KB updates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/kb-updates/pending")
async def get_pending_kb_updates():
    """Get all pending KB update suggestions (requires manual approval)."""
    try:
        from utils.supabase_client import get_kb_updates
        updates = get_kb_updates(status="pending")
        return {
            "status": "success",
            "updates": updates,
            "count": len(updates),
            "message": "These are suggestions that require manual approval before being added to FAQ"
        }
    except Exception as e:
        logger.error(f"Error getting pending KB updates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/kb-updates/{update_id}/apply")
async def apply_single_kb_update(
    update_id: str,
    question: Optional[str] = None,
    answer: Optional[str] = None,
    category: Optional[str] = "General"
):
    """
    Apply a single KB update suggestion (with optional manual edits).
    
    Args:
        update_id: ID of the KB update to apply
        question: Optional - override the auto-generated question
        answer: Optional - override the auto-generated answer (RECOMMENDED)
        category: Optional - FAQ category (default: "General")
    """
    try:
        from utils.kb_updater import KBUpdater
        from utils.supabase_client import get_kb_updates, update_kb_update_status
        
        updater = KBUpdater()
        
        # Get the specific update
        all_updates = get_kb_updates(status="pending")
        update = next((u for u in all_updates if u.get("update_id") == update_id), None)
        
        if not update:
            raise HTTPException(status_code=404, detail=f"KB update {update_id} not found")
        
        # Apply with manual overrides if provided
        content = update.get("content", {})
        customer_comment = content.get("customer_comment", "")
        
        # Use provided question/answer or generate from feedback
        final_question = question or updater._extract_question(customer_comment)
        final_answer = answer or updater._generate_answer(customer_comment, content.get("reason", ""))
        
        # Load current KB
        import json
        from pathlib import Path
        kb_file = Path(__file__).parent.parent / "data" / "faq_knowledge_base.json"
        
        if not kb_file.exists():
            raise HTTPException(status_code=500, detail="FAQ knowledge base file not found")
        
        with open(kb_file, "r", encoding="utf-8") as f:
            kb_data = json.load(f)
        
        # Create new FAQ entry
        new_faq = {
            "id": f"faq_{len(kb_data.get('faqs', [])) + 1}",
            "question": final_question,
            "answer": final_answer,
            "category": category,
            "tags": ["feedback", "approved"],
            "source": "feedback",
            "created_from_feedback": True,
            "approved_by": "manual"  # Indicates manual approval
        }
        
        # Add to KB
        if "faqs" not in kb_data:
            kb_data["faqs"] = []
        kb_data["faqs"].append(new_faq)
        
        # Save KB
        with open(kb_file, "w", encoding="utf-8") as f:
            json.dump(kb_data, f, indent=2, ensure_ascii=False)
        
        # Mark update as applied
        update_kb_update_status(update_id, "applied")
        
        logger.info(f"Applied KB update {update_id} with manual approval")
        
        return {
            "status": "success",
            "update_id": update_id,
            "faq_added": new_faq,
            "message": "KB update applied successfully with manual approval"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying KB update: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/kb-updates/{update_id}/reject")
async def reject_kb_update(update_id: str, reason: Optional[str] = None):
    """Reject a KB update suggestion."""
    try:
        from utils.supabase_client import update_kb_update_status
        update_kb_update_status(update_id, "rejected")
        
        return {
            "status": "success",
            "update_id": update_id,
            "message": f"KB update {update_id} rejected",
            "reason": reason
        }
    except Exception as e:
        logger.error(f"Error rejecting KB update: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/improvements/run-now")
async def run_improvements_now_endpoint():
    """Manually trigger improvements (refinements + KB updates) immediately."""
    try:
        result = run_improvements_now()
        return {
            "status": "success",
            **result,
            "message": f"Applied {result.get('refinements_applied', 0)} refinements and {result.get('kb_updates_applied', 0)} KB updates"
        }
    except Exception as e:
        logger.error(f"Error running improvements: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/refunds")
async def get_refunds():
    """
    Get all refund requests.
    Returns a list of all refunds in the database.
    """
    try:
        from utils.supabase_client import SUPABASE_ENABLED
        if SUPABASE_ENABLED:
            from supabase import create_client
            import os
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            if supabase_url and supabase_key:
                supabase = create_client(supabase_url, supabase_key)
                result = supabase.table("refunds").select("*").order("created_at", desc=True).execute()
                return result.data or []
        
        # Fallback: return empty list if Supabase not enabled
        return []
    except Exception as e:
        logger.error(f"Error fetching refunds: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch refunds: {str(e)}")


@app.put("/refunds/{refund_id}/status")
async def update_refund_status(refund_id: str, request: dict):
    """
    Update the status of a refund request.
    
    Body:
    {
        "status": "pending" | "approved" | "rejected" | "processed",
        "note": "optional note"
    }
    """
    try:
        new_status = request.get("status")
        note = request.get("note")
        
        if new_status not in ["pending", "approved", "rejected", "processed"]:
            raise HTTPException(status_code=400, detail="Invalid status. Must be: pending, approved, rejected, or processed")
        
        from utils.supabase_client import SUPABASE_ENABLED
        if SUPABASE_ENABLED:
            from supabase import create_client
            from datetime import datetime
            import os
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            if supabase_url and supabase_key:
                supabase = create_client(supabase_url, supabase_key)
                
                # Update refund status
                update_data = {
                    "status": new_status,
                    "updated_at": datetime.now().isoformat()
                }
                
                # If status is processed, set processed_at
                if new_status == "processed":
                    update_data["processed_at"] = datetime.now().isoformat()
                
                result = supabase.table("refunds").update(update_data).eq("refund_id", refund_id).execute()
                
                if not result.data:
                    raise HTTPException(status_code=404, detail=f"Refund {refund_id} not found")
                
                return {
                    "status": "success",
                    "refund_id": refund_id,
                    "new_status": new_status,
                    "message": f"Refund status updated to {new_status}"
                }
        
        raise HTTPException(status_code=500, detail="Supabase not enabled")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating refund status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update refund status: {str(e)}")


@app.post("/speech/transcribe")
async def transcribe_speech(
    audio: UploadFile = File(..., description="Audio file to transcribe"),
    language_code: str = Form("en-US", description="Language code (e.g., en-US, fr-FR)")
):
    """
    Transcribe audio to text using Google Cloud Speech-to-Text.
    
    Args:
        audio: Audio file (WebM, WAV, FLAC, or LINEAR16 format)
        language_code: Language code (default: en-US)
    
    Returns:
        {
            "status": "success",
            "transcript": "transcribed text"
        }
    """
    try:
        from utils.google_speech import transcribe_audio
        
        # Read audio file
        audio_data = await audio.read()
        
        if not audio_data or len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file")
        
        # Transcribe audio
        transcript = transcribe_audio(audio_data, language_code)
        
        if not transcript:
            raise HTTPException(
                status_code=500,
                detail="Failed to transcribe audio. The audio might be too short, silent, or in an unsupported format. Please try recording again."
            )
        
        return {
            "status": "success",
            "transcript": transcript
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to transcribe audio: {str(e)}"
        )


@app.post("/speech/synthesize")
async def synthesize_speech(request: dict):
    """
    Convert text to speech using Google Cloud Text-to-Speech.
    
    Body:
    {
        "text": "Text to convert to speech",
        "language_code": "en-US" (optional, default: en-US),
        "voice_name": "en-US-Standard-B" (optional)
    }
    
    Returns:
        Audio file (MP3 format) as binary response
    """
    try:
        from utils.google_speech import text_to_speech
        
        text = request.get("text")
        if not text:
            raise HTTPException(status_code=400, detail="Missing 'text' field in request body")
        
        language_code = request.get("language_code", "en-US")
        voice_name = request.get("voice_name")
        
        # Synthesize speech
        audio_data = text_to_speech(text, language_code, voice_name)
        
        if not audio_data:
            raise HTTPException(status_code=500, detail="Failed to synthesize speech")
        
        # Return audio as MP3
        return Response(
            content=audio_data,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=speech.mp3"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error synthesizing speech: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to synthesize speech: {str(e)}"
        )


@app.post("/documents/analyze")
async def analyze_document_endpoint(
    file: UploadFile = File(..., description="Document file (PDF, JPG, PNG, WebP)"),
    analysis_type: str = Form("auto", description="Type of analysis: auto, receipt, invoice, product_photo, order_confirmation, general"),
    context: Optional[str] = Form(None, description="Optional context about what to look for")
):
    """
    Analyze a document (PDF or image) using Gemini Vision API.
    
    Supported file types:
    - PDF files
    - Images: JPG, PNG, WebP
    
    Analysis types:
    - auto: Automatically detect and extract relevant information
    - receipt: Extract order/receipt information (order number, amount, date, items)
    - invoice: Extract invoice information
    - product_photo: Analyze product photo for defects/issues
    - order_confirmation: Extract order confirmation details
    - general: General text extraction and summary
    
    Returns:
    {
        "status": "success" | "error",
        "document_type": "receipt" | "invoice" | "product_photo" | "unknown",
        "extracted_data": {
            "order_id": "...",
            "amount": 99.99,
            "date": "2024-01-15",
            "items": [...],
            ...
        },
        "text_content": "Full extracted text",
        "summary": "Brief summary",
        "confidence": 0.95,
        "error_message": "..." (if error)
    }
    """
    try:
        from tools.document_analysis_tool import analyze_document
        
        # Validate file type
        allowed_types = [
            "application/pdf",
            "image/jpeg",
            "image/jpg",
            "image/png",
            "image/webp"
        ]
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type}. Supported: PDF, JPG, PNG, WebP"
            )
        
        # Read file data
        file_data = await file.read()
        
        if not file_data or len(file_data) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Check file size (max 20MB for Gemini Vision)
        max_size = 20 * 1024 * 1024  # 20MB
        if len(file_data) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: 20MB. Your file: {len(file_data) / 1024 / 1024:.2f}MB"
            )
        
        # Analyze document
        result = analyze_document(
            file_data=file_data,
            file_type=file.content_type,
            analysis_type=analysis_type,
            context=context
        )
        
        if result.get("status") == "error":
            raise HTTPException(
                status_code=500,
                detail=result.get("error_message", "Failed to analyze document")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing document: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze document: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level="info"
    )

