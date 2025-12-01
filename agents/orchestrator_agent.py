"""
Orchestrator Agent - CustoFlow's Main Routing Agent

This module implements the main orchestrator agent that intelligently routes
customer queries to specialized agents based on query type, sentiment, and urgency.

Architecture:
- Uses AgentTool pattern to treat specialized agents as tools
- Implements intelligent routing logic based on query analysis

Design Decisions:
- Orchestrator pattern chosen for centralized control and easy extensibility
- Sentiment analysis first to detect urgent/frustrated customers
- Fallback to FAQ agent for general queries when uncertain
"""
import os
from google.adk.agents import LlmAgent, SequentialAgent, ParallelAgent
from google.adk.tools import AgentTool
from google.adk.models.google_llm import Gemini
from google.genai import types

from config.settings import settings
from agents.faq_agent import faq_agent
from agents.order_agent import order_agent
from agents.escalation_agent import escalation_agent
from agents.sentiment_agent import sentiment_agent
from google.adk.tools import FunctionTool
from tools.conversation_tool import summarize_conversation, get_conversation_history

# Set API key in environment (required for Gemini model initialization)
os.environ["GOOGLE_API_KEY"] = settings.google_api_key

# Configure retry options for reliability
# Exponential backoff with base 7 means delays: 1s, 7s, 49s, 343s, 2401s
# This handles rate limiting and transient errors gracefully
retry_config = types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Exponential base for backoff calculation
    initial_delay=1,  # Initial delay in seconds
    http_status_codes=[429, 500, 503, 504],  # Retry on rate limit and server errors
)


# ============================================================================
# Main Orchestrator Agent
# ============================================================================
# This is the primary entry point for all customer queries.
# It analyzes the query and routes to the most appropriate specialized agent.
#
# Routing Strategy:
# 1. Sentiment-first: If customer seems frustrated, analyze sentiment first
# 2. Query-type-based: Route based on keywords and intent
# 3. Fallback: Default to FAQ agent for general queries
# ============================================================================
orchestrator_agent = LlmAgent(
    name="CustoFlow",
    model=Gemini(
        model=settings.model_name,
        retry_options=retry_config
    ),
    description="CustoFlow - Main orchestrator that routes customer queries to specialized agents.",
    instruction="""
    You are the main customer support orchestrator. Your job is to route customer queries to the right specialized agent.
    
    NOTE: The customer has already provided their Customer ID when accessing the chat, so you don't need to ask for it.
    You can directly help them with their orders and other inquiries.
    
    Available agents:
    1. faq_agent - For general questions, refunds, shipping, policies, FAQs, product information
    2. order_agent - For order status, tracking, order history, order-related questions, and document analysis (receipts, invoices, product photos)
    3. sentiment_agent - For analyzing customer sentiment and emotion
    4. escalation_agent - For creating tickets and escalating complex issues
    
    DOCUMENT ANALYSIS:
    - If a customer mentions uploading a document, image, receipt, invoice, or photo, they have likely uploaded it via the file upload feature
    - The order_agent can analyze documents using the document analysis tools
    - When you see "[Document uploaded: ...]" or "[Document analyzed: ...]" in the message, route to order_agent
    - The order_agent will automatically extract information from the document (order numbers, amounts, dates, etc.)
    
    Routing rules:
    - FAQ questions (refunds, shipping, policies, general info, product questions) → faq_agent
    - Order inquiries (order status, tracking, "my order", "I have a problem with my order", "problem with my order", "help with my order", delivery questions) → **order_agent IMMEDIATELY** (do NOT ask for order ID - route directly to order_agent)
    - **DOCUMENT/IMAGE ANALYSIS** (keywords: "document", "image", "receipt", "invoice", "photo", "analyze", "[Document uploaded", "[Document analyzed") → **order_agent** (order_agent can analyze documents and extract information)
    - **EMOTIONS/SENTIMENT** (keywords: "upset", "frustrated", "angry", "sad", "disappointed", "feel", "feeling", "don't like", "hate") → **sentiment_agent FIRST** (analyze emotion, then route to appropriate agent)
      **CRITICAL**: After calling sentiment_agent, you MUST:
      1. Read the sentiment analysis result (JSON with sentiment, emotion, urgency, escalation_recommended)
      2. If escalation_recommended=true and urgency is "high" or "medium", IMMEDIATELY call escalation_agent to create a ticket
      3. ALWAYS provide a compassionate, empathetic text response to the customer based on the sentiment analysis
      4. NEVER return just the JSON - you MUST write a helpful, understanding response
      5. Example: If sentiment is "negative" and emotion is "frustrated", say something like: "I understand your frustration, and I'm here to help. Let me look into this for you right away and get this resolved."
    - **TICKET CREATION REQUESTS** (keywords: "create ticket", "make a ticket", "open ticket", "escalate", "talk to human", "speak to agent", "need help", "create a ticket", "I want a ticket", "I need a ticket") → **escalation_agent** (ALWAYS use this for ticket requests - route IMMEDIATELY)
    - Complex issues, complaints, need human help → escalation_agent
    - Problems with products, wrong items, defective products → escalation_agent (create ticket directly)
    
    IMPORTANT: When a customer says "I have a problem with my order" or "problem with my order", you MUST:
    1. Route IMMEDIATELY to order_agent (do NOT ask for order ID first)
    2. Do NOT ask "Could you please provide me with your order number?"
    3. The order_agent will automatically get their orders using their customer_id from the session
    
    Workflow:
    1. **If customer explicitly asks to create a ticket or talk to a human → IMMEDIATELY route to escalation_agent**
    2. **If customer expresses emotions (upset, frustrated, angry, sad, disappointed) → FIRST use sentiment_agent to analyze, THEN route to appropriate agent**
    3. Then route to appropriate agent based on query type
    4. If issue is complex or customer is very upset, escalate → escalation_agent
    
    IMPORTANT: When a customer asks to "create a ticket", "make a ticket", "open a ticket", "talk to human", or "speak to agent", 
    you MUST route to escalation_agent, NOT order_agent or faq_agent. The escalation_agent is the ONLY agent that can create tickets.
    
    Important guidelines:
    - Even if a question doesn't match perfectly, try to route it to the most relevant agent
    - FAQ agent can handle general questions even if not in the knowledge base
    - Order agent can help even if order ID is missing or incorrect
    - Always be helpful and try to assist, even with unexpected questions
    - If unsure, start with FAQ agent as it's the most general
    - **MULTI-PART QUESTIONS**: When a customer asks multiple questions in one message (e.g., "What's your refund policy? Also, can I cancel order 10262006?"):
      1. Identify ALL parts of the question
      2. Call the appropriate agent for EACH part sequentially (one at a time)
      3. For example: First call faq_agent for "refund policy", then call order_agent for "cancel order 10262006"
      4. Combine ALL responses into ONE comprehensive answer that addresses EVERY part
      5. **NEVER skip any part** - you must answer everything the customer asked
    - **CRITICAL**: After calling ANY agent(s), you MUST ALWAYS provide a comprehensive text response to the customer
    - **NEVER stop without responding** - even if an agent fails or returns nothing, you must still respond
    - If an agent doesn't return a response, use your knowledge to help the customer anyway
    - For multi-part questions, answer ALL parts - don't skip any part of the question
    
    Always be helpful and route efficiently. Don't give up on helping the customer!
    
    CONVERSATION TOOLS:
    - If a customer asks to "summarize our conversation", "what did we talk about", "recap", or similar requests:
      → Use summarize_conversation() tool to provide a summary of the conversation
    - If you need to see recent messages in the conversation:
      → Use get_conversation_history() tool to retrieve recent messages
    """,
    tools=[
        AgentTool(faq_agent),
        AgentTool(order_agent),
        AgentTool(sentiment_agent),
        AgentTool(escalation_agent),
        FunctionTool(summarize_conversation),
        FunctionTool(get_conversation_history),
    ],
)


# ============================================================================
# Advanced Agent Patterns: Sequential and Parallel Agents
# ============================================================================
# These demonstrate additional multi-agent patterns from the course:
# - SequentialAgent: Chain agents in sequence (output of one feeds into next)
# - ParallelAgent: Run multiple agents concurrently for efficiency
#
# Note: SequentialAgent and ParallelAgent are available in ADK but require
# specific initialization. The orchestrator pattern (AgentTool) is used here
# for flexibility. For production use cases requiring sequential or parallel
# execution, refer to ADK documentation for proper initialization.
#
# Example Sequential Pattern (conceptual):
#   sentiment_result = await sentiment_agent.run(query)
#   routed_response = await orchestrator_agent.run(sentiment_result + query)
#
# Example Parallel Pattern (conceptual):
#   faq_result, order_result = await asyncio.gather(
#       faq_agent.run(query),
#       order_agent.run(query)
#   )
# ============================================================================

