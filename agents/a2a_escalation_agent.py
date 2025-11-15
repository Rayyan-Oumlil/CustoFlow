"""Escalation Agent exposed via A2A Protocol for remote access."""
import os
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import FunctionTool
from google.genai import types

from config.settings import settings
from tools.ticket_tool import create_ticket, get_ticket_status

# Set API key in environment
os.environ["GOOGLE_API_KEY"] = settings.google_api_key

# Configure retry options
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)


# Create Escalation agent
escalation_agent_base = LlmAgent(
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
    """,
    tools=[FunctionTool(create_ticket), FunctionTool(get_ticket_status)],
)


# A2A Protocol Architecture
# 
# This agent is designed to be exposed via A2A Protocol for remote access.
# In production, this would be:
# 1. Deployed as a separate service (e.g., FastAPI server)
# 2. Exposed via A2A endpoint (e.g., /a2a)
# 3. Consumed by other services using RemoteA2aAgent
#
# Example deployment:
# - Service URL: http://escalation-service:8000
# - A2A Endpoint: http://escalation-service:8000/a2a
# - Other agents can use: RemoteA2aAgent(name="escalation", url="http://escalation-service:8000/a2a")
#
# For now, we use the agent directly via AgentTool in orchestrator.
# The A2A architecture is documented and ready for deployment.

