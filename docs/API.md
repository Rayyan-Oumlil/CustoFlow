# CustoFlow API Documentation

## Overview

CustoFlow provides a RESTful API for interacting with the multi-agent customer support system. The API is built with FastAPI and supports session management, metrics, and health monitoring.

## Base URL

```
http://localhost:8000
```

## Endpoints

### Health Check

**GET** `/health`

Check the health status of the API and get current metrics.

**Response:**
```json
{
  "status": "healthy",
  "metrics": {
    "sessions_started": 10,
    "messages_received": 45,
    "messages_sent": 45,
    "errors": 0
  }
}
```

### Chat Endpoint

**POST** `/chat`

Send a message to CustoFlow and get a response.

**Request Body:**
```json
{
  "message": "What is your refund policy?",
  "user_id": "user123",
  "session_id": "session_abc123"  // Optional: omit to create new session
}
```

**Response:**
```json
{
  "response": "We offer a 30-day money-back guarantee...",
  "session_id": "session_abc123",
  "metrics": {
    "sessions_started": 10,
    "messages_received": 46,
    "messages_sent": 46,
    "errors": 0
  }
}
```

**Example using curl:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is your refund policy?",
    "user_id": "user123"
  }'
```

**Example using Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/chat",
    json={
        "message": "What is your refund policy?",
        "user_id": "user123"
    }
)

data = response.json()
print(data["response"])
```

### Metrics Endpoint

**GET** `/metrics`

Get current system metrics.

**Response:**
```json
{
  "sessions_started": 10,
  "messages_received": 45,
  "messages_sent": 45,
  "errors": 0
}
```

## Session Management

Sessions are automatically created on first message if `session_id` is not provided. The same `session_id` should be used for subsequent messages in the same conversation to maintain context.

**Example conversation flow:**
```python
# First message - creates new session
response1 = requests.post("/chat", json={
    "message": "What is your refund policy?",
    "user_id": "user123"
})
session_id = response1.json()["session_id"]

# Second message - continues same session
response2 = requests.post("/chat", json={
    "message": "Can you tell me more?",
    "user_id": "user123",
    "session_id": session_id  # Use same session_id
})
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200 OK`: Successful request
- `400 Bad Request`: Invalid request body
- `500 Internal Server Error`: Server error

Error responses include error details:
```json
{
  "detail": "Error message here"
}
```

## Rate Limiting

Currently no rate limiting is implemented. For production, consider adding rate limiting based on `user_id` or IP address.

## CORS

CORS is enabled for all origins. For production, restrict to specific domains.

