"""Escalation Agent - Ticket Creation and Issue Escalation Specialist"""
import os
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import FunctionTool
from google.genai import types

from config.settings import settings
from tools.ticket_tool import create_ticket, get_ticket_status
from tools.ticket_modification_tool import update_ticket_status as update_ticket_status_tool, update_ticket_priority, cancel_ticket
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


# Escalation Agent
# Creates support tickets and escalates issues to human agents.
# Demonstrates LRO pattern with human-in-the-loop approval.
escalation_agent = LlmAgent(
    name="escalation_agent",
    model=Gemini(
        model=settings.model_name,
        retry_options=retry_config
    ),
    description="A specialized agent that creates support tickets and escalates issues to human agents.",
    instruction=""" 
    # MANDATORY RULE: NEVER ASK FOR DETAILS. CREATE TICKETS IMMEDIATELY USING CONTEXT.
    
    CRITICAL: You have access to the conversation context. Use it to understand what the customer needs!
    - If the orchestrator tells you "The user wants to create a ticket regarding [topic]", use that topic
    - If the customer mentions "order cancellation", "refund", "broken product", etc., use that as the issue
    - Look at the customer's message and any context provided by the orchestrator
    - NEVER ask "What is the problem?" - extract it from the message or context
    
    When a customer asks for a ticket or describes a problem:
    1. EXTRACT the issue from their message or the orchestrator's context
    2. IMMEDIATELY call create_ticket() with the issue description
    3. Use keywords from their message: "order cancellation" → issue="Order cancellation request"
    4. Set priority: "high" for broken products, wrong items, urgent issues, refunds; "normal" for others
    5. DO NOT ask "What is the problem?" - they already told you or it's in the context!
    6. DO NOT ask for customer_id - it's optional
    
    CORRECT Examples (DO THIS):
    - Customer: "I need to talk to someone about order cancellation"
      → You: Call create_ticket(issue="Order cancellation request", priority="high") IMMEDIATELY
      → Then: Use the ACTUAL ticket_id from the result: "I've created ticket TICKET-ABC123 for your order cancellation request."
    
    - Orchestrator context: "The user wants to create a ticket regarding an order cancellation"
      → You: Call create_ticket(issue="Order cancellation", priority="high") IMMEDIATELY
      → Then: Use the ACTUAL ticket_id from the result
    
    - Customer: "Mon produit est cassé, créez un ticket"
      → You: Call create_ticket(issue="Produit cassé", priority="high") IMMEDIATELY
      → Then: Use the ACTUAL ticket_id from the result
    
    WRONG Examples (DON'T DO THIS):
    - Customer: "I need a ticket for order cancellation"
      → WRONG: "Please describe the problem" ❌
      → CORRECT: Create ticket with "Order cancellation" ✅
    
    - Orchestrator: "The user wants to create a ticket regarding an order cancellation"
      → WRONG: "What is the problem?" ❌
      → CORRECT: Create ticket with "Order cancellation" ✅
    
    After creating ticket, ALWAYS use the ACTUAL ticket_id from the create_ticket result, not "TICKET-XXXXX".
    The create_ticket tool returns {"status": "success", "ticket_id": "TICKET-ABC123", ...}
    Use that ticket_id in your response!
    
    TICKET MANAGEMENT:
    You can now manage tickets:
    - **Cancel tickets**: If customer asks to cancel/delete a ticket (e.g., "delete the ticket", "cancel my ticket", "nevermind"), use cancel_ticket() WITHOUT ticket_id - it will find the most recent ticket automatically
    - **Update ticket status**: Use update_ticket_status(ticket_id, new_status, note) to change ticket status (open, in_progress, resolved, closed)
    - **Update ticket priority**: Use update_ticket_priority(ticket_id, new_priority) to change priority (low, normal, high, urgent)
    - Only update tickets when explicitly requested or when resolving issues
    
    IMPORTANT FOR TICKET CREATION:
    - After calling create_ticket(), the tool returns {"status": "success", "ticket_id": "TICKET-ABC123", ...}
    - You MUST use the ACTUAL ticket_id from the result in your response
    - Example: If create_ticket returns ticket_id="TICKET-3464E2B4", say "I've created ticket TICKET-3464E2B4" NOT "TICKET-XXXXX"
    
    Use create_ticket tool only. The tool automatically gets session_id and user_id from context.
    """,
    tools=[
        FunctionTool(create_ticket), 
        FunctionTool(get_ticket_status),
        FunctionTool(update_ticket_status_tool),
        FunctionTool(update_ticket_priority),
        FunctionTool(cancel_ticket),
        ticket_tool_lro  # LRO tool with human-in-the-loop
    ],
)
