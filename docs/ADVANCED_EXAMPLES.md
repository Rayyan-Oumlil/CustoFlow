# Advanced Usage Examples

This document provides advanced examples and use cases for CustoFlow.

## Table of Contents
- [Custom Agent Integration](#custom-agent-integration)
- [Analytics and Monitoring](#analytics-and-monitoring)
- [Conversation History](#conversation-history)
- [Multilingual Support](#multilingual-support)
- [Rate Limiting Configuration](#rate-limiting-configuration)
- [Cache Management](#cache-management)
- [Error Handling Patterns](#error-handling-patterns)
- [Performance Optimization](#performance-optimization)

## Custom Agent Integration

### Creating a Custom Agent

```python
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import FunctionTool
from google.genai import types
import os

# Set API key
os.environ["GOOGLE_API_KEY"] = "your_api_key"

# Create custom tool
def custom_search(query: str) -> dict:
    """Custom search function."""
    return {"status": "success", "results": f"Searching for: {query}"}

# Create agent
custom_agent = LlmAgent(
    name="custom_agent",
    model=Gemini(model="gemini-2.5-flash-lite"),
    description="Custom agent for specific tasks",
    instruction="You are a helpful assistant that uses custom tools.",
    tools=[FunctionTool(custom_search)]
)
```

### Adding Agent to Orchestrator

```python
from agents.orchestrator_agent import orchestrator_agent
from google.adk.tools import AgentTool

# Add custom agent to orchestrator
orchestrator_agent.tools.append(AgentTool(custom_agent))
```

## Analytics and Monitoring

### Tracking User Interactions

```python
from utils.analytics import analytics

# Log an interaction
analytics.log_interaction(
    user_id="user123",
    query="What is your refund policy?",
    response="We offer a 30-day return policy...",
    agent_used="faq_agent",
    response_time=1.5
)

# Get analytics statistics
stats = analytics.get_stats()
print(f"Total interactions: {stats['total_interactions']}")
print(f"Top query patterns: {stats['top_query_patterns']}")
print(f"Agent performance: {stats['agent_performance']}")
```

### Collecting User Feedback

```python
# Submit feedback
analytics.log_feedback(
    session_id="session_123",
    feedback_type="thumbs_up",
    rating=None,
    comment="Very helpful!"
)

# Or with rating
analytics.log_feedback(
    session_id="session_123",
    feedback_type="rating",
    rating=5,
    comment="Excellent service!"
)
```

## Conversation History

### Retrieving Conversation History

```python
from memory.conversation_history import conversation_history

# Get all messages for a user
history = conversation_history.get_history(
    user_id="user123",
    limit=50
)

# Get messages for specific session
session_history = conversation_history.get_history(
    user_id="user123",
    session_id="session_456",
    limit=20
)

# Get all sessions for a user
sessions = conversation_history.get_user_sessions("user123")
```

### Using History for Context

```python
# Get recent conversation context
recent_history = conversation_history.get_history(
    user_id="user123",
    limit=10
)

# Build context string
context = "\n".join([
    f"{msg['role']}: {msg['content']}"
    for msg in recent_history
])

# Use context in agent query
query_with_context = f"Previous conversation:\n{context}\n\nNew question: {user_query}"
```

## Multilingual Support

### Language Detection

```python
from utils.multilingual import detect_language, get_greeting, get_error_message

# Detect language
user_message = "Bonjour, j'ai besoin d'aide"
language = detect_language(user_message)
print(f"Detected language: {language}")  # Output: "fr"

# Get greeting in detected language
greeting = get_greeting(language)
print(greeting)  # Output: "Bonjour! Comment puis-je vous aider aujourd'hui?"

# Get error message in user's language
error_msg = get_error_message(language)
print(error_msg)  # Output: "Je m'excuse, mais j'ai rencontré une erreur..."
```

### Custom Language Support

```python
# Add custom language to multilingual.py
LANGUAGE_PATTERNS = {
    "fr": ["bonjour", "salut", "merci"],
    "es": ["hola", "gracias"],
    "custom": ["custom_keyword1", "custom_keyword2"]
}

greetings = {
    "en": "Hello!",
    "fr": "Bonjour!",
    "custom": "Custom greeting!"
}
```

## Rate Limiting Configuration

### Custom Rate Limits

```python
from utils.rate_limiter import RateLimiter

# Create custom rate limiter
custom_limiter = RateLimiter(
    max_requests=100,  # 100 requests
    window_seconds=60  # per minute
)

# Check if request is allowed
is_allowed, error = custom_limiter.is_allowed("user123")
if not is_allowed:
    print(f"Rate limit exceeded: {error}")

# Get remaining requests
remaining = custom_limiter.get_remaining("user123")
print(f"Remaining requests: {remaining}")

# Reset rate limit for a user
custom_limiter.reset("user123")
```

### Per-Endpoint Rate Limiting

```python
# Different limits for different endpoints
faq_limiter = RateLimiter(max_requests=60, window_seconds=60)
order_limiter = RateLimiter(max_requests=30, window_seconds=60)
escalation_limiter = RateLimiter(max_requests=10, window_seconds=60)
```

## Cache Management

### Custom Cache Configuration

```python
from utils.cache import TTLCache, generate_cache_key

# Create custom cache with different TTL
short_cache = TTLCache(ttl_seconds=300)  # 5 minutes
long_cache = TTLCache(ttl_seconds=3600)  # 1 hour

# Store in cache
short_cache.set("key1", "value1")
long_cache.set("key2", "value2")

# Retrieve from cache
value1 = short_cache.get("key1")
value2 = long_cache.get("key2")

# Clear cache
short_cache.clear()
```

### Cache Statistics

```python
from utils.cache import faq_cache, order_cache

# Get cache size
faq_size = faq_cache.size()
order_size = order_cache.size()

print(f"FAQ cache: {faq_size} entries")
print(f"Order cache: {order_size} entries")

# Clear caches
faq_cache.clear()
order_cache.clear()
```

## Error Handling Patterns

### Custom Error Handling

```python
from utils.error_handler import APIError, get_user_friendly_error

try:
    # Your code here
    result = some_operation()
except Exception as e:
    # Get user-friendly error message
    user_message = get_user_friendly_error(e)
    print(f"Error: {user_message}")
    
    # Or raise custom API error
    raise APIError(
        message=str(e),
        status_code=500,
        user_message="A custom error occurred. Please try again."
    )
```

### Timeout Handling

```python
from utils.error_handler import with_timeout
import asyncio

async def long_operation():
    await asyncio.sleep(10)
    return "result"

# Execute with timeout
result = await with_timeout(
    long_operation(),
    timeout_seconds=5,
    default_response="Operation timed out"
)
```

## Performance Optimization

### Batch Processing

```python
from concurrent.futures import ThreadPoolExecutor
from tools.faq_tool import search_faq

# Process multiple queries in parallel
queries = [
    "What is your refund policy?",
    "How long does shipping take?",
    "What are your payment methods?"
]

with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(search_faq, queries))

for query, result in zip(queries, results):
    print(f"Query: {query}")
    print(f"Result: {result['status']}")
```

### Response Time Monitoring

```python
import time
from utils.analytics import analytics

# Measure response time
start_time = time.time()

# Your operation
response = await agent.run(query)

response_time = time.time() - start_time

# Log with analytics
analytics.log_interaction(
    user_id="user123",
    query=query,
    response=response,
    agent_used="agent_name",
    response_time=response_time
)

# Alert if slow
if response_time > 5.0:
    print(f"Warning: Slow response time: {response_time:.2f}s")
```

## API Usage Examples

### Python Client

```python
import requests
import time

# Base URL
BASE_URL = "http://localhost:8000"

# Send message
response = requests.post(
    f"{BASE_URL}/chat",
    json={
        "message": "What is your refund policy?",
        "user_id": "user123"
    }
)

data = response.json()
print(f"Response: {data['response']}")
print(f"Session ID: {data['session_id']}")

# Submit feedback
requests.post(
    f"{BASE_URL}/feedback",
    json={
        "session_id": data['session_id'],
        "feedback_type": "thumbs_up",
        "rating": 5
    }
)

# Get conversation history
history = requests.get(
    f"{BASE_URL}/history/user123",
    params={"limit": 20}
).json()

# Get analytics
analytics = requests.get(f"{BASE_URL}/analytics").json()
```

### JavaScript/TypeScript Client

```javascript
const BASE_URL = 'http://localhost:8000';

// Send message
async function sendMessage(message, userId) {
    const response = await fetch(`${BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            message: message,
            user_id: userId
        })
    });
    
    const data = await response.json();
    return data;
}

// Submit feedback
async function submitFeedback(sessionId, feedbackType, rating) {
    await fetch(`${BASE_URL}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            session_id: sessionId,
            feedback_type: feedbackType,
            rating: rating
        })
    });
}

// Get history
async function getHistory(userId, limit = 50) {
    const response = await fetch(
        `${BASE_URL}/history/${userId}?limit=${limit}`
    );
    return await response.json();
}
```

## Best Practices

1. **Always validate input** before processing
2. **Use caching** for frequently accessed data
3. **Monitor rate limits** to prevent abuse
4. **Log interactions** for analytics and debugging
5. **Handle errors gracefully** with user-friendly messages
6. **Use timeouts** for long-running operations
7. **Track performance metrics** to identify bottlenecks
8. **Collect feedback** to improve agent responses

