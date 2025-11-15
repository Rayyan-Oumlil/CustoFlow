"""
Order Agent - Specialized Agent for Order Inquiries

This agent handles all order-related customer questions including:
- Order status lookup
- Order tracking information
- Customer order history
- Delivery estimates

Tools:
- lookup_order: Get details for a specific order ID
- get_customer_orders: Get all orders for a customer

Error Handling:
- Provides helpful guidance when order ID is missing or incorrect
- Suggests where to find order information
- Offers alternative lookup methods
"""
import os
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import FunctionTool
from google.genai import types

from config.settings import settings
from tools.order_tool import lookup_order, get_customer_orders

# Set API key in environment (required for Gemini model)
os.environ["GOOGLE_API_KEY"] = settings.google_api_key

# Configure retry options for reliability
# Exponential backoff handles rate limiting and transient errors
retry_config = types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Exponential base for backoff calculation
    initial_delay=1,  # Initial delay in seconds
    http_status_codes=[429, 500, 503, 504],  # Retry on rate limit and server errors
)


# ============================================================================
# Order Agent
# ============================================================================
# Specialized agent for order inquiries and tracking.
# ============================================================================
order_agent = LlmAgent(
    name="order_agent",
    model=Gemini(
        model=settings.model_name,
        retry_options=retry_config
    ),
    description="A specialized agent that looks up order information and order status.",
    instruction="""
    You are a helpful customer support agent specializing in order inquiries.
    
    CRITICAL RULE: You MUST ALWAYS provide a text response to the customer, even if the tool fails or returns an error. Never return None or empty content.
    
    When a customer asks about their order:
    1. Extract the order ID from their message (look for numbers like "12345" or phrases like "order 12345")
    2. Use the lookup_order tool to get order details
    3. After receiving the tool result, you MUST ALWAYS provide a text response to the customer:
       - If the tool returns status "success", provide clear information about:
         * Order status (processing, shipped, delivered, etc.)
         * Items in the order
         * Shipping information (tracking number, estimated delivery)
         * Total amount
         Example: "Your order 12345 has been shipped! It contains Wireless Headphones (1x) for $99.99. Tracking: TRACK123456. Estimated delivery: 2024-01-22."
       - If the tool returns status "error":
         * Apologize and ask them to verify the order ID
         * Use any "helpful_info" from the error to guide them
         * Offer to help them find their order if they provide their email or customer ID
         * Suggest checking their confirmation email or account dashboard
         Example: "I couldn't find order 11111 in our system. Order IDs are typically 5-10 digits. Could you please double-check the order number? You can find it in your confirmation email or account dashboard."
    4. Always be friendly and professional
    5. If they don't have an order ID, help them understand where to find it or offer alternative ways to look up their order
    
    If they ask about "my orders" or "all my orders", use get_customer_orders tool instead.
    
    REMEMBER: You MUST generate a text response after every tool call. If the tool fails, still provide a helpful response explaining the situation and offering alternatives.
    """,
    tools=[FunctionTool(lookup_order), FunctionTool(get_customer_orders)],
)

