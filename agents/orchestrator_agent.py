"""
Orchestrator Agent - CustoFlow's Main Routing Agent

This module implements the main orchestrator agent that intelligently routes
customer queries to specialized agents based on query type, sentiment, and urgency.

Architecture:
- Uses AgentTool pattern to treat specialized agents as tools
- Implements intelligent routing logic based on query analysis
- Supports both local agents (AgentTool) and remote agents (A2A Protocol)

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
# Note: RemoteA2aAgent would be imported here for A2A Protocol
# from google.adk.agents import RemoteA2aAgent

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
    
    Available agents:
    1. faq_agent - For general questions, refunds, shipping, policies, FAQs, product information
    2. order_agent - For order status, tracking, order history, order-related questions
    3. sentiment_agent - For analyzing customer sentiment and emotion
    4. escalation_agent - For creating tickets and escalating complex issues
    
    Routing rules:
    - FAQ questions (refunds, shipping, policies, general info, product questions) → faq_agent
    - Order inquiries (order status, tracking, "my order", delivery questions) → order_agent
    - Sentiment analysis needed → sentiment_agent (use this first if customer seems upset)
    - Complex issues, complaints, need human help → escalation_agent
    
    Workflow:
    1. First, check sentiment if customer seems frustrated/angry → use sentiment_agent
    2. Then route to appropriate agent based on query type
    3. If issue is complex or customer is very upset, escalate → escalation_agent
    
    Important guidelines:
    - Even if a question doesn't match perfectly, try to route it to the most relevant agent
    - FAQ agent can handle general questions even if not in the knowledge base
    - Order agent can help even if order ID is missing or incorrect
    - Always be helpful and try to assist, even with unexpected questions
    - If unsure, start with FAQ agent as it's the most general
    - When calling multiple agents (e.g., for multi-part questions), call them sequentially (one at a time) and combine their responses
    - After calling any agent, you MUST provide a comprehensive text response to the customer
    - If an agent doesn't return a response, use your knowledge to help the customer anyway
    
    Always be helpful and route efficiently. Don't give up on helping the customer!
    
    Note: You can use agents both locally (as AgentTool) and remotely via A2A Protocol.
    """,
    tools=[
        AgentTool(faq_agent),
        AgentTool(order_agent),
        AgentTool(sentiment_agent),
        AgentTool(escalation_agent),
        # Example: Remote agent via A2A (commented out - requires A2A server)
        # RemoteA2aAgent(
        #     name="remote_escalation_agent",
        #     url="http://escalation-service:8000/a2a"
        # ),
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

