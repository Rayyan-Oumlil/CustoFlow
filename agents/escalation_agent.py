"""Escalation Agent for creating support tickets and escalating issues."""
import os
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import FunctionTool
from google.genai import types

from config.settings import settings
from tools.ticket_tool import create_ticket, get_ticket_status
from tools.ticket_tool_lro import ticket_tool_lro

# Set API key in environment (required for Gemini)
os.environ["GOOGLE_API_KEY"] = settings.google_api_key

# Configure retry options for reliability
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)


# Create Escalation agent
escalation_agent = LlmAgent(
    name="escalation_agent",
    model=Gemini(
        model=settings.model_name,
        retry_options=retry_config
    ),
    description="A specialized agent that creates support tickets and escalates issues to human agents.",
    instruction="""
    You are a customer support escalation agent. Your job is to:
    1. Create support tickets when issues need human intervention
    2. Determine the appropriate priority level (low, normal, high, urgent)
    3. Provide clear ticket information to customers
    
    When creating a ticket:
    - Use the create_ticket tool with the customer's issue description
    - Set priority based on urgency: "urgent" for critical issues, "high" for important, "normal" for standard
    - Always be empathetic and reassure the customer that their issue will be addressed
    
    After creating a ticket, provide the ticket ID and next steps to the customer.
    
    For high-priority or urgent tickets, use create_ticket_with_approval which will
    pause for human approval before creating the ticket.
    """,
    tools=[
        FunctionTool(create_ticket), 
        FunctionTool(get_ticket_status),
        ticket_tool_lro  # LRO tool with human-in-the-loop
    ],
)

