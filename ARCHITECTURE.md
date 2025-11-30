# CustoFlow - Architecture Documentation

## Overview

CustoFlow is a production-ready multi-agent customer support system built with Google's Agent Development Kit (ADK). The system automates 80%+ of customer support queries through intelligent routing, specialized AI agents, and real-time analytics.

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend Layer                          │
│  React/Next.js 15 (Vercel) - Chat, Orders, Tickets, Analytics  │
└────────────────────────────┬────────────────────────────────────┘
                              │ HTTP/REST
┌─────────────────────────────▼────────────────────────────────────┐
│                         API Layer                                │
│  FastAPI Server (Google Cloud Run) - REST API, Rate Limiting     │
└────────────────────────────┬────────────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────────────┐
│                      Agent Orchestration Layer                   │
│  Orchestrator Agent (Google ADK) - Routes to Specialists       │
└────────────────────────────┬────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼──────┐    ┌─────────▼─────────┐  ┌───────▼────────┐
│ FAQ Agent    │    │  Order Agent       │  │ Sentiment Agent │
│              │    │                    │  │                 │
│ - Semantic   │    │ - Order Lookup    │  │ - Emotion       │
│   Search     │    │ - Tracking         │  │   Analysis      │
│ - Knowledge  │    │ - Modifications   │  │ - Urgency       │
│   Base       │    │ - Document        │  │   Detection     │
│              │    │   Analysis        │  │                 │
└──────────────┘    └────────────────────┘  └────────┬─────────┘
                                                     │
                                            ┌────────▼─────────┐
                                            │ Escalation Agent │
                                            │                  │
                                            │ - Ticket Creation│
                                            │ - Summarization  │
                                            └──────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────────────┐
│                         Tools Layer                              │
│  FAQ Tool, Order Tool, Ticket Tool, Shipping Tool, etc.         │
└────────────────────────────┬────────────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────────────┐
│                      Data Persistence Layer                      │
│  Supabase (PostgreSQL) - Messages, Sessions, Orders, Tickets    │
│  FAISS - Vector Embeddings for Semantic Search                   │
└──────────────────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. Frontend Layer (React/Next.js)

**Location**: `frontend/`

**Components**:
- **Chat Interface** (`app/chat/page.tsx`): Customer-facing chat with TTS/STT
- **Orders Dashboard** (`app/orders/page.tsx`): Order management and creation
- **Tickets Dashboard** (`app/tickets/page.tsx`): Ticket viewing and management
- **Analytics Dashboard** (`app/analytics/page.tsx`): Real-time metrics
- **Monitoring Dashboard** (`app/monitoring/page.tsx`): Human agent monitoring

**Key Features**:
- Adaptive polling (2s active → 15s inactive)
- In-memory caching with TTL
- Optimistic UI updates
- Automatic retry on network errors
- Per-message text-to-speech

**State Management**:
- Zustand for global state
- React hooks for local state
- API client with retry logic

### 2. API Layer (FastAPI)

**Location**: `api/server.py`

**Responsibilities**:
- Request validation and sanitization
- Rate limiting (60 req/min per user)
- CORS handling
- Error handling with user-friendly messages
- Session management
- Agent orchestration

**Key Endpoints**:
- `POST /chat` - Main chat endpoint
- `GET /orders` - Order management
- `GET /tickets` - Ticket management
- `GET /sessions` - Session management
- `GET /analytics` - Analytics data
- `POST /feedback` - User feedback
- `POST /speech/transcribe` - Speech-to-text
- `POST /speech/synthesize` - Text-to-speech

**Middleware**:
- CORS middleware for cross-origin requests
- Exception handlers for error responses
- Rate limiting middleware

### 3. Agent Orchestration Layer

**Location**: `agents/orchestrator_agent.py`

**Orchestrator Agent**:
- Analyzes incoming queries
- Routes to appropriate specialist agent
- Coordinates multi-agent workflows
- Aggregates responses

**Routing Logic**:
1. **Ticket Requests** → Escalation Agent (immediate)
2. **Emotions/Sentiment** → Sentiment Agent (first), then route
3. **Order Inquiries** → Order Agent (immediate, no order ID needed)
4. **FAQ Questions** → FAQ Agent
5. **Document Analysis** → Order Agent

### 4. Specialist Agents

**Location**: `agents/`

#### FAQ Agent (`faq_agent.py`)
- Handles general questions, policies, product info
- Uses semantic search (FAISS) for knowledge base
- Can call Order Agent via A2A for personalized responses

#### Order Agent (`order_agent.py`)
- Manages order inquiries, tracking, modifications
- Uses customer context from session (no order ID needed)
- Analyzes documents (receipts, invoices)
- Real-time shipping tracking via OpenAPI pattern

#### Sentiment Agent (`sentiment_agent.py`)
- Analyzes customer emotion and urgency
- Detects frustration, anger, satisfaction
- Can trigger escalation for high urgency

#### Escalation Agent (`escalation_agent.py`)
- Creates support tickets with auto-summarization
- Extracts key points, sentiment, action items
- Provides context for human agent handoff

### 5. Tools Layer

**Location**: `tools/`

**Custom Tools**:
- **FAQ Tool** (`faq_tool.py`): Semantic search with FAISS
- **Order Tool** (`order_tool.py`): Order lookup and management
- **Order Modification Tool** (`order_modification_tool.py`): Cancellation, notes, refunds
- **Shipping Tool** (`shipping_tool.py`): Real-time tracking (OpenAPI pattern)
- **Ticket Tool** (`ticket_tool.py`): Ticket creation with summarization
- **Ticket Modification Tool** (`ticket_modification_tool.py`): Status/priority updates
- **Conversation Tool** (`conversation_tool.py`): Summarization and history
- **Document Analysis Tool** (`document_analysis_tool.py`): PDF/image analysis with Gemini Vision

### 6. Memory & Session Management

**Location**: `memory/`

**Components**:
- **Session Store** (`session_store.py`): In-memory session management
- **Conversation History** (`conversation_history.py`): Persistent message storage
- **Long-Term Memory** (`long_term_memory.py`): Customer knowledge persistence
- **Session Metadata** (`session_metadata.py`): Session-level metadata

**Storage**:
- Supabase for persistent storage
- In-memory for active sessions
- Automatic context compaction

### 7. Data Persistence Layer

**Location**: `utils/supabase_client.py`

**Database Schema** (Supabase PostgreSQL):
- **sessions**: Conversation sessions with customer_id
- **messages**: Full conversation history
- **orders**: Order details, status, items, tracking
- **tickets**: Support tickets with summaries
- **feedback**: User ratings and comments
- **analytics**: Interaction tracking

**Vector Storage**:
- FAISS index for semantic search
- Stored in Supabase Storage
- Sentence Transformers for embeddings

### 8. Observability Layer

**Location**: `observability/`

**Components**:
- **Logging** (`logging_config.py`): ADK LoggingPlugin, structured logging
- **Metrics** (`metrics.py`): Thread-safe metrics collection
- **Tracing** (`tracing.py`): Request tracing and correlation

**Metrics Tracked**:
- Message counts
- Session activity
- Response times
- Agent usage
- Error rates

### 9. Utilities Layer

**Location**: `utils/`

**Key Utilities**:
- **Validation** (`validation.py`): Input validation and sanitization
- **Rate Limiter** (`rate_limiter.py`): Per-user rate limiting
- **Error Handler** (`error_handler.py`): User-friendly error messages
- **Analytics** (`analytics.py`): Business analytics aggregation
- **Cache** (`cache.py`): In-memory caching with TTL
- **Auto Improver** (`auto_improver.py`): Automatic agent refinement from feedback
- **QA Checker** (`qa_checker.py`): Quality assurance and compliance
- **A/B Testing** (`ab_testing.py`): Statistical A/B testing framework

## Data Flow

### Chat Request Flow

```
1. Customer sends message via Frontend
   ↓
2. Frontend validates and sends POST /chat
   ↓
3. API Layer:
   - Validates input
   - Checks rate limits
   - Retrieves/creates session
   ↓
4. Orchestrator Agent:
   - Analyzes query
   - Routes to specialist agent
   ↓
5. Specialist Agent:
   - Uses relevant tools
   - Generates response
   ↓
6. Tools Layer:
   - Executes operations (DB queries, searches, etc.)
   - Returns results
   ↓
7. Agent generates response
   ↓
8. API Layer:
   - Stores message in Supabase
   - Updates analytics
   - Returns response
   ↓
9. Frontend:
   - Displays response
   - Updates UI optimistically
```

### A2A Communication Flow

```
FAQ Agent needs order context
   ↓
Calls Order Agent via AgentTool
   ↓
Order Agent retrieves order data
   ↓
Returns context to FAQ Agent
   ↓
FAQ Agent generates personalized response
```

## Technology Stack

### Backend
- **Python 3.10+**: Core language
- **Google ADK**: Agent Development Kit
- **Gemini 2.5 Flash Lite**: LLM for all agents
- **FastAPI**: REST API framework
- **Supabase**: PostgreSQL database
- **FAISS**: Vector embeddings
- **Sentence Transformers**: Semantic search

### Frontend
- **React/Next.js 15**: Web framework
- **TypeScript**: Type safety
- **Zustand**: State management
- **shadcn/ui**: UI components
- **Google Cloud Speech**: TTS/STT

### Infrastructure
- **Google Cloud Run**: Backend deployment
- **Vercel**: Frontend deployment
- **Supabase**: Database and storage

## Security & Performance

### Security
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- Rate limiting (60 req/min)
- CORS configuration

### Performance
- Response caching (1 hour TTL)
- Adaptive polling (reduces API calls)
- In-memory caching
- Optimistic UI updates
- Automatic retry with exponential backoff

## Scalability

- **Horizontal Scaling**: Cloud Run auto-scales based on traffic
- **Database**: Supabase handles connection pooling
- **Caching**: Reduces database load
- **Stateless API**: Enables easy scaling

## Deployment

### Backend (Google Cloud Run)
- Containerized with Docker
- Environment variables for configuration
- Health checks and metrics endpoints
- Auto-scaling based on traffic

### Frontend (Vercel)
- Next.js production build
- Automatic deployments from Git
- Edge network for fast global access
- Environment variables for API URL

## Monitoring & Observability

- **Logging**: Structured logs with ADK LoggingPlugin
- **Metrics**: Real-time metrics collection
- **Tracing**: Request correlation IDs
- **Analytics**: Business metrics dashboard
- **Error Tracking**: User-friendly error messages

## Future Enhancements

- MCP tools for file system access
- Payment gateway integration for automated refunds
- Google Cloud Agent Engine deployment option
- Enhanced multilingual support
- Real-time collaboration features

