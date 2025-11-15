"""
Escalation Agent - Ticket Creation and Issue Escalation Specialist

This agent handles complex issues that require human intervention:
- Creates support tickets with appropriate priority
- Determines urgency based on issue type and sentiment
- Uses LRO (Long-Running Operations) for high-priority tickets requiring approval

Tools:
- create_ticket: Standard ticket creation
- get_ticket_status: Check ticket status
- create_ticket_with_approval (LRO): Human-in-the-loop approval for urgent tickets

Priority Levels:
- low: Standard inquiries
- normal: Regular support requests
- high: Important issues requiring attention
- urgent: Critical issues requiring immediate action

LRO Pattern:
For high/urgent tickets, the agent can pause and wait for human approval
before creating the ticket, demonstrating the Long-Running Operations pattern.
"""
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
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Exponential backoff base
    initial_delay=1,  # Initial delay
    http_status_codes=[429, 500, 503, 504],  # Retry on rate limit and server errors
)


# ============================================================================
# Escalation Agent
# ============================================================================
# Creates support tickets and escalates issues to human agents.
# Demonstrates LRO pattern with human-in-the-loop approval.
# ============================================================================
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

