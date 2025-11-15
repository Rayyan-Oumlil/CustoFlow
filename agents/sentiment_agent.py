"""Sentiment Agent for analyzing customer sentiment."""
import os
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.genai import types

from config.settings import settings

# Set API key in environment
os.environ["GOOGLE_API_KEY"] = settings.google_api_key

# Configure retry options
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)


# Create Sentiment agent
sentiment_agent = LlmAgent(
    name="sentiment_agent",
    model=Gemini(
        model=settings.model_name,
        retry_options=retry_config
    ),
    description="Analyzes customer sentiment and emotional state from messages.",
    instruction="""
    You are a sentiment analysis agent. Analyze customer messages and determine:
    1. Sentiment: "positive", "neutral", or "negative"
    2. Emotion: specific emotion (happy, frustrated, angry, etc.)
    3. Urgency: "low", "medium", or "high"
    4. Escalation needed: true or false
    
    Respond with ONLY a JSON object in this format:
    {
        "sentiment": "positive|neutral|negative",
        "emotion": "specific emotion",
        "urgency": "low|medium|high",
        "escalation_recommended": true|false,
        "reason": "brief explanation"
    }
    """,
    tools=[],
)

