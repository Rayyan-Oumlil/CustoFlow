"""
Sentiment Agent - Customer Emotion Analysis Specialist

This agent analyzes customer messages to determine:
- Sentiment: positive, neutral, or negative
- Emotion: specific emotion (happy, frustrated, angry, etc.)
- Urgency: low, medium, or high
- Escalation recommendation: whether human intervention is needed

Output Format:
Returns structured JSON with sentiment analysis results that can be used
by the orchestrator to make routing and escalation decisions.

Use Cases:
- Pre-routing sentiment check for frustrated customers
- Escalation trigger based on negative sentiment
- Priority assignment for tickets
- Customer satisfaction monitoring
"""
import os
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import AgentTool
from google.genai import types

from config.settings import settings

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
# Sentiment Agent
# ============================================================================
# Analyzes customer sentiment and emotion to inform routing decisions.
# Returns structured JSON for programmatic use by orchestrator.
# ============================================================================
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
    
    A2A PROTOCOL (Agent-to-Agent Communication):
    If you detect high urgency (urgency="high") and escalation_recommended=true, you can directly call escalation_agent 
    to create a ticket with the appropriate priority based on the urgency level.
    - For high urgency + negative sentiment: Call escalation_agent with priority="urgent"
    - For medium urgency + negative sentiment: Call escalation_agent with priority="high"
    - This allows immediate ticket creation without requiring the orchestrator to route again
    
    Respond with ONLY a JSON object in this format:
    {
        "sentiment": "positive|neutral|negative",
        "emotion": "specific emotion",
        "urgency": "low|medium|high",
        "escalation_recommended": true|false,
        "reason": "brief explanation"
    }
    
    If escalation_recommended is true and urgency is "high" or "medium", you may also call escalation_agent 
    directly to create a ticket with appropriate priority.
    """,
    tools=[],
)

# Add A2A protocol: Sentiment agent can call Escalation agent
# Import here to avoid circular dependency
from agents.escalation_agent import escalation_agent
sentiment_agent.tools.append(AgentTool(escalation_agent))

