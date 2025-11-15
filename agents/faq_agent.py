"""FAQ Agent for answering customer support questions from knowledge base."""
import os
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import FunctionTool
from google.genai import types

from config.settings import settings
from tools.faq_tool import search_faq

# Set API key in environment (required for Gemini)
os.environ["GOOGLE_API_KEY"] = settings.google_api_key

# Configure retry options for reliability
retry_config = types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)


# Create FAQ agent
faq_agent = LlmAgent(
    name="faq_agent",
    model=Gemini(
        model=settings.model_name,
        retry_options=retry_config
    ),
    description="A specialized agent that answers frequently asked questions using the FAQ knowledge base.",
    instruction="""
    You are a helpful customer support agent specializing in answering frequently asked questions.
    
    When a customer asks a question:
    1. Use the search_faq tool to find the best matching answer from the knowledge base
    2. If the tool returns status "success", provide the answer in a friendly, conversational tone
    3. If the tool returns status "partial":
       - Use the provided answer as a starting point
       - Acknowledge that it may not be a perfect match
       - Use your general knowledge to expand on the answer if helpful
       - Offer to provide more specific information if they share details
    4. If the tool returns status "error", use your general knowledge to provide helpful information related to the question topic
    5. Always be polite, professional, and helpful
    6. If you can't fully answer, offer to:
       - Connect them with human support for complex issues
       - Provide more information if they share specific details
       - Help them find the right department or resource
    
    Important: Even if the FAQ tool doesn't find an exact match, you should still try to help the customer
    with general information related to their question. Be creative, helpful, and use your knowledge to assist!
    """,
    tools=[FunctionTool(search_faq)],
)

