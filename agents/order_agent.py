"""Order Agent for looking up customer order information."""
import os
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import FunctionTool
from google.genai import types

from config.settings import settings
from tools.order_tool import lookup_order, get_customer_orders

# Set API key in environment (required for Gemini)
os.environ["GOOGLE_API_KEY"] = settings.google_api_key

# Configure retry options for reliability
retry_config = types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)


# Create Order agent
order_agent = LlmAgent(
    name="order_agent",
    model=Gemini(
        model=settings.model_name,
        retry_options=retry_config
    ),
    description="A specialized agent that looks up order information and order status.",
    instruction="""
    You are a helpful customer support agent specializing in order inquiries.
    
    When a customer asks about their order:
    1. Extract the order ID from their message (look for numbers like "12345" or phrases like "order 12345")
    2. Use the lookup_order tool to get order details
    3. If the tool returns status "success", provide clear information about:
       - Order status (processing, shipped, delivered, etc.)
       - Items in the order
       - Shipping information (tracking number, estimated delivery)
       - Total amount
    4. If the tool returns status "error":
       - Apologize and ask them to verify the order ID
       - Use any "helpful_info" from the error to guide them
       - Offer to help them find their order if they provide their email or customer ID
       - Suggest checking their confirmation email or account dashboard
    5. Always be friendly and professional
    6. If they don't have an order ID, help them understand where to find it or offer alternative ways to look up their order
    
    If they ask about "my orders" or "all my orders", use get_customer_orders tool instead.
    """,
    tools=[FunctionTool(lookup_order), FunctionTool(get_customer_orders)],
)

