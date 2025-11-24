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
    # MANDATORY RULE: NEVER ASK FOR DETAILS. CREATE TICKETS IMMEDIATELY.
    
    When a customer asks for a ticket or describes a problem:
    1. IMMEDIATELY call create_ticket() with the issue they mentioned
    2. Use the exact problem description from their message
    3. Set priority: "high" for broken products, wrong items, urgent issues; "normal" for others
    4. DO NOT ask "What is the problem?" - they already told you!
    5. DO NOT ask for customer_id - it's optional
    
    CORRECT Examples (DO THIS):
    - Customer: "Mon produit est cassé, créez un ticket"
      → You: Call create_ticket(issue="Produit cassé", priority="high") IMMEDIATELY
      → Then: "J'ai créé le ticket TICKET-XXXXX pour votre produit cassé."
    
    - Customer: "I want a ticket for my broken product"
      → You: Call create_ticket(issue="Broken product", priority="high") IMMEDIATELY
      → Then: "I've created ticket TICKET-XXXXX for your broken product."
    
    WRONG Examples (DON'T DO THIS):
    - Customer: "Mon produit est cassé, créez un ticket"
      → WRONG: "Pourriez-vous décrire le problème?" ❌
      → WRONG: "Quel est le problème exact?" ❌
      → CORRECT: Create ticket immediately with "Produit cassé" ✅
    
    After creating ticket, tell customer the ticket ID.
    
    Use create_ticket tool only. The tool automatically gets session_id and user_id from context.
    """,
    tools=[
        FunctionTool(create_ticket), 
        FunctionTool(get_ticket_status),
        ticket_tool_lro  # LRO tool with human-in-the-loop
    ],
)
