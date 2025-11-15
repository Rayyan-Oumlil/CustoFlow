"""Orchestrator Agent that routes customer queries to specialized agents."""
import os
from google.adk.agents import LlmAgent
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

# Set API key in environment
os.environ["GOOGLE_API_KEY"] = settings.google_api_key

# Configure retry options
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)


# Create Orchestrator agent
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

