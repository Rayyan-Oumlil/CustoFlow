# 🏗️ CustoFlow Architecture Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Component Details](#component-details)
4. [Data Flow](#data-flow)
5. [Technology Stack](#technology-stack)
6. [Scalability & Performance](#scalability--performance)
7. [Security](#security)
8. [Deployment](#deployment)

---

## System Overview

CustoFlow is a **multi-agent customer support system** built with Google's Agent Development Kit (ADK). It uses intelligent routing to automatically direct customer queries to specialized AI agents, each optimized for specific types of inquiries.

### Core Principles
- **Modular Design**: Each agent is independent and can be updated separately
- **Intelligent Routing**: Orchestrator agent routes queries to the best specialist
- **Context Preservation**: Conversations maintain context across sessions
- **Scalable Architecture**: Handles 1000+ concurrent users
- **Production-Ready**: Error handling, logging, monitoring, and persistence

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                              │
├─────────────────────────────────────────────────────────────────┤
│  React Frontend       │  REST API  │  CLI Interface            │
└────────────┬───────────┴──────┬─────┴────────────┬──────────────┘
             │                  │                  │
             └──────────────────┼──────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │   FastAPI Server      │
                    │   (api/server.py)     │
                    │  - Request Validation │
                    │  - Rate Limiting     │
                    │  - Error Handling    │
                    │  - Session Management│
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │  Orchestrator Agent    │
                    │  (Main Router)         │
                    │  - Query Analysis      │
                    │  - Agent Selection     │
                    │  - Response Aggregation│
                    └───────────┬───────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌───────▼────────┐   ┌─────────▼─────────┐   ┌────────▼────────┐
│  FAQ Agent     │   │  Order Agent      │   │ Sentiment Agent │
│  - FAQ Search  │   │  - Order Lookup   │   │  - Emotion Det. │
│  - Knowledge   │   │  - Order History  │   │  - Urgency Score│
│    Base Query  │   │  - Tracking Info  │   │  - Escalation   │
└───────┬────────┘   └─────────┬─────────┘   └────────┬────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Escalation Agent       │
                    │   - Ticket Creation     │
                    │   - Human Handoff        │
                    └────────────┬────────────┘
                                 │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌───────▼────────┐   ┌─────────▼─────────┐   ┌────────▼────────┐
│  Tools Layer    │   │  Memory Layer     │   │ Observability   │
│  - FAQ Tool     │   │  - Sessions       │   │  - Logging      │
│  - Order Tool   │   │  - History        │   │  - Metrics      │
│  - Ticket Tool  │   │  - Metadata       │   │  - Analytics    │
└─────────────────┘   └───────────────────┘   └─────────────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Data Persistence       │
                    │   - Supabase (PostgreSQL)│
                    │   - Session Storage      │
                    │   - Conversation History│
                    │   - Analytics & Feedback │
                    └──────────────────────────┘
```

---

## Component Details

### 1. Client Layer

#### React Frontend (`frontend/`)
- **Purpose**: Web-based user interface
- **Technology**: Next.js 15, React, TypeScript, Tailwind CSS
- **Features**:
  - Real-time chat interface with typing indicators
  - Agent attribution display (shows which agent responded)
  - Interactive feedback (thumbs up/down) with agent tracking
  - Customer ID authentication and validation
  - Session management and filtering
  - Orders and tickets dashboard
  - Real-time analytics dashboard (no hardcoded data)
  - Auto-focus on input field for better UX
  - Real-time chat interface
  - Conversation history
  - Analytics dashboard
  - Order and ticket management
  - Session management
- **Technology**: React, Next.js, TypeScript, Tailwind CSS

#### REST API (`api/server.py`)
- **Purpose**: Programmatic access to the system
- **Endpoints**:
  - `POST /chat` - Send messages (with QA & A/B testing integration)
  - `GET /health` - Health check
  - `GET /metrics` - System metrics
  - `GET /analytics` - Analytics data
  - `GET /orders` - Order management
  - `GET /tickets` - Ticket management
  - `GET /sessions/{user_id}` - Session management
  - `POST /feedback` - Submit user feedback
  - `GET /qa/check` - Get QA results for responses
  - `POST /ab-testing/create` - Create A/B test
  - `GET /ab-testing/results` - Get A/B test results
  - `POST /speech/transcribe` - Transcribe audio
  - `POST /speech/synthesize` - Text-to-speech
  - `GET /refunds` - Get refund requests
  - `PUT /refunds/{refund_id}/status` - Update refund status
  - `POST /tickets/{ticket_id}/message` - Send message via ticket
- **Technology**: FastAPI, Uvicorn

#### CLI Interface (`main.py`)
- **Purpose**: Command-line interface for testing
- **Features**: Interactive chat loop

---

### 2. Agent Layer

#### Orchestrator Agent (`agents/orchestrator_agent.py`)
- **Role**: Main routing agent
- **Responsibilities**:
  - Analyze incoming queries
  - Route to appropriate specialist agent
  - Aggregate responses from multiple agents
  - Handle complex multi-part questions
  - Detect which agent handled each response
  - Capture agent responses even when orchestrator returns None
- **Tools**: AgentTool wrappers for all specialist agents
- **Agent Detection**: Automatic detection via function calls and response content analysis

#### FAQ Agent (`agents/faq_agent.py`)
- **Role**: Handle general questions and FAQs
- **Capabilities**:
  - Search knowledge base
  - Answer policy questions
  - Provide product information
  - Handle refund/shipping queries
  - **A2A Protocol**: Can call Order Agent to get order context for personalized answers
- **Tools**: `search_faq` tool, `order_agent` (via A2A)

#### Order Agent (`agents/order_agent.py`)
- **Role**: Handle order-related inquiries
- **Capabilities**:
  - Look up order status
  - Retrieve order history
  - Provide tracking information
  - Handle order modifications
  - Add notes to orders
  - Request refunds
  - **A2A Protocol**: Can call FAQ Agent to get policy information for complete answers
- **Tools**: `lookup_order`, `get_customer_orders`, `add_order_note`, `request_refund`, `faq_agent` (via A2A)

#### Sentiment Agent (`agents/sentiment_agent.py`)
- **Role**: Analyze customer emotion and urgency
- **Capabilities**:
  - Detect sentiment (positive, neutral, negative)
  - Assess urgency level
  - Recommend escalation if needed
  - **A2A Protocol**: Can call Escalation Agent directly to create urgent tickets
- **Tools**: Sentiment analysis, `escalation_agent` (via A2A)

#### Escalation Agent (`agents/escalation_agent.py`)
- **Role**: Handle complex issues requiring human intervention
- **Capabilities**:
  - Create support tickets
  - Escalate to human agents
  - Provide escalation context
  - Cancel tickets
  - Use conversation context (no asking for details)
- **Tools**: `create_ticket`, `cancel_ticket`

---

### 3. Tools Layer

#### FAQ Tool (`tools/faq_tool.py`)
- **Function**: Search FAQ knowledge base
- **Implementation**: Semantic search using FAISS vector embeddings
- **Features**: 
  - 50+ FAQs with vector embeddings
  - Sentence Transformers for semantic similarity
  - Automatic fallback to LLM knowledge
  - Supabase Storage for index persistence

#### Order Tool (`tools/order_tool.py`)
- **Function**: Retrieve order information
- **Implementation**: Supabase PostgreSQL database
- **Features**: 
  - Order lookup by ID
  - Customer order history (automatic customer_id from session)
  - Order creation and updates
  - Status management (processing, shipped, delivering, delivery_soon, delivered, cancelled)
  - Automatic status updates based on estimated_delivery date

#### Ticket Tool (`tools/ticket_tool.py`)
- **Function**: Create and manage support tickets
- **Implementation**: Supabase PostgreSQL database
- **Features**:
  - Ticket creation with automatic summarization
  - Priority assignment (low, normal, high, urgent)
  - Status tracking (open, in_progress, resolved, closed)
  - Sentiment analysis integration
  - Key points extraction

#### Shipping Tool (`tools/shipping_tool.py`)
- **Function**: Real-time shipping tracking via OpenAPI (mock)
- **Implementation**: Mock OpenAPI tool simulating carrier APIs (UPS, FedEx, DHL, USPS)
- **Features**:
  - Real-time shipment tracking using order data from Supabase
  - Current location and status updates based on order status
  - Estimated delivery times from order data
  - Status mapping (processing → Warehouse, shipped → Origin Facility, etc.)
  - Carrier name mapping (UPS, FedEx, DHL, USPS)
  - Demonstrates OpenAPI Tools concept for capstone
  - **Comprehensive test coverage**: 16 test scenarios covering all carriers, statuses, error cases
- **Note**: This is a mock implementation. In production, would use `OpenAPITool.from_openapi_spec()` with real carrier APIs
- **Integration**: Integrated with Order Agent for real-time tracking when customers ask about shipments

---

### 4. Memory Layer

#### Session Store (`memory/session_store.py`)
- **Purpose**: Manage conversation sessions
- **Implementation**: ADK's InMemorySessionService
- **Features**: Session creation, retrieval, context preservation

#### Conversation History (`memory/conversation_history.py`)
- **Purpose**: Store conversation history
- **Implementation**: Thread-safe in-memory storage with JSON persistence
- **Features**: Message storage, history retrieval, session filtering

#### Session Metadata (`memory/session_metadata.py`)
- **Purpose**: Track session metadata (name, message count, timestamps)
- **Implementation**: JSON-based persistence
- **Features**: Session naming, metadata tracking, persistence

---

### 5. Observability Layer

#### Logging (`observability/logging_config.py`)
- **Purpose**: Structured logging
- **Features**: 
  - ADK logging plugin integration
  - Request/response logging
  - Error tracking
  - Performance metrics

#### Metrics (`observability/metrics.py`)
- **Purpose**: System metrics collection
- **Metrics**:
  - Messages received/sent
  - Sessions started
  - Errors
  - Response times

#### Analytics (`utils/analytics.py`)
- **Purpose**: Business analytics
- **Features**:
  - Agent performance tracking
  - Query pattern analysis
  - Success rate calculation
  - Real-time metrics collection
  - Feedback aggregation
  - Agent usage statistics

#### QA & Compliance (`utils/qa_checker.py`)
- **Purpose**: Automated quality assurance and compliance checking
- **Features**:
  - Quality scoring (0.0-1.0) based on response characteristics
  - Compliance keyword detection (GDPR, privacy, security, legal, financial)
  - Profanity detection
  - Quality issue flagging (pass, warning, fail)
  - Batch QA checking for multiple responses
  - Automatic integration with chat endpoint

#### A/B Testing (`utils/ab_testing.py`)
- **Purpose**: Statistical A/B testing framework for agent optimization
- **Features**:
  - Create A/B tests for agent instruction variants
  - Consistent variant routing (50/50 split using hashing)
  - Metrics collection (satisfaction, response time, escalations, resolutions, feedback)
  - Statistical analysis (t-test) to determine winner
  - Automatic winner recommendation
  - Persistent storage of test data

#### Audio Processing (`utils/google_speech.py`)
- **Purpose**: Speech-to-Text and Text-to-Speech integration
- **Features**:
  - Google Cloud Speech-to-Text for audio transcription
  - Google Cloud Text-to-Speech for response audio generation
  - Support for multiple audio formats
  - Client-side WebM to WAV conversion

---

### 6. Utilities Layer

#### Validation (`utils/validation.py`)
- **Purpose**: Input validation and sanitization
- **Features**: Message validation, user ID validation, order ID validation

#### Rate Limiting (`utils/rate_limiter.py`)
- **Purpose**: Prevent abuse and ensure fair usage
- **Implementation**: Token bucket algorithm
- **Features**: Per-user rate limiting, configurable limits

#### Error Handling (`utils/error_handler.py`)
- **Purpose**: Centralized error handling
- **Features**: Timeout protection, user-friendly error messages, error logging

#### Caching (`utils/cache.py`)
- **Purpose**: Performance optimization
- **Features**: Order caching, FAQ caching, TTL-based expiration

---

## Data Flow

### 1. Message Processing Flow

```
User Message
    │
    ▼
FastAPI Server (Validation, Rate Limiting)
    │
    ▼
Orchestrator Agent (Query Analysis)
    │
    ▼
Specialist Agent Selection & Detection
    │
    ├─► FAQ Agent ──► FAQ Tool ──► Semantic Search (FAISS)
    ├─► Order Agent ──► Order Tool ──► Order Database (Supabase)
    ├─► Sentiment Agent ──► Sentiment Analysis
    └─► Escalation Agent ──► Ticket Tool ──► Ticket Database
    │
    ▼
Agent Response Capture
    │ (Captures response even if orchestrator returns None)
    ▼
Agent Attribution
    │ (Detects and stores which agent handled the response)
    ▼
Response Aggregation
    │
    ▼
Conversation History Storage (Supabase)
    │
    ▼
Analytics & Feedback Logging
    │
    ▼
Response to User (with agent_used metadata)
```

### 2. Session Management Flow

```
User Request
    │
    ▼
Session ID Check
    │
    ├─► Existing Session ──► Load Context
    └─► New Session ──► Create Session ──► Initialize Context
    │
    ▼
Process Message (with context)
    │
    ▼
Update Session Metadata
    │
    ▼
Save to Persistence Layer
```

---

## Technology Stack

### Core Framework
- **Google ADK (Agent Development Kit)**: Multi-agent orchestration
- **Gemini 2.5 Flash Lite**: LLM for all agents
- **Python 3.10+**: Programming language

### Web Framework
- **FastAPI**: REST API server
- **Uvicorn**: ASGI server
- **React/Next.js**: Web dashboard

### Data Storage
- **Supabase (PostgreSQL)**: Primary database for all persistent data
  - Messages, sessions, orders, tickets, feedback
  - Analytics, agent refinements, KB updates
- **In-Memory**: Session management, caching
- **FAISS**: Vector embeddings for semantic search

### Libraries
- **Pydantic**: Data validation
- **Supabase**: PostgreSQL database and storage
- **Sentence Transformers**: Semantic search embeddings
- **FAISS**: Vector similarity search
- **APScheduler**: Scheduled tasks (agent improvements)
- **Google Cloud Speech**: Speech-to-Text and Text-to-Speech
- **scipy**: Statistical analysis for A/B testing
- **numpy**: Numerical operations for A/B testing

---

## Database Schema

The complete database schema for Supabase (PostgreSQL) is defined below. This script creates all tables, indexes, and constraints needed for CustoFlow.

```sql
-- ============================================================================
-- Complete script to create the entire Supabase database
-- Run this script to create all tables with their constraints
-- ============================================================================

-- Drop existing tables (in reverse dependency order)
DROP TABLE IF EXISTS refunds CASCADE;
DROP TABLE IF EXISTS kb_updates_from_feedback CASCADE;
DROP TABLE IF EXISTS analytics_interactions CASCADE;
DROP TABLE IF EXISTS agent_refinements CASCADE;
DROP TABLE IF EXISTS feedback_insights CASCADE;
DROP TABLE IF EXISTS conversation_summaries CASCADE;
DROP TABLE IF EXISTS feedback CASCADE;
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS tickets CASCADE;
DROP TABLE IF EXISTS sessions CASCADE;
DROP TABLE IF EXISTS orders CASCADE;

-- ============================================================================
-- 1. SESSIONS table (must be created first as it's referenced by others)
-- ============================================================================

CREATE TABLE public.sessions (
    session_id character varying NOT NULL,
    user_id character varying NOT NULL,
    customer_id character varying,
    name character varying,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    message_count integer DEFAULT 0,
    is_active boolean DEFAULT TRUE,
    CONSTRAINT sessions_pkey PRIMARY KEY (session_id)
);

-- ============================================================================
-- 2. ORDERS table (independent)
-- ============================================================================

CREATE TABLE public.orders (
    order_id character varying NOT NULL,
    customer_id character varying NOT NULL,
    status character varying NOT NULL,
    total numeric NOT NULL,
    items jsonb NOT NULL,
    notes jsonb DEFAULT '[]'::jsonb,
    tracking_number character varying,
    estimated_delivery date,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT orders_pkey PRIMARY KEY (order_id)
);

-- ============================================================================
-- 3. MESSAGES table (depends on sessions)
-- ============================================================================

CREATE TABLE public.messages (
    id integer NOT NULL DEFAULT nextval('messages_id_seq'::regclass),
    user_id character varying NOT NULL,
    session_id character varying NOT NULL,
    role character varying NOT NULL,
    content text NOT NULL,
    metadata jsonb,
    timestamp timestamp without time zone DEFAULT now(),
    CONSTRAINT messages_pkey PRIMARY KEY (id),
    CONSTRAINT messages_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.sessions(session_id)
);

-- Create sequence if it doesn't exist
CREATE SEQUENCE IF NOT EXISTS messages_id_seq;

-- ============================================================================
-- 4. TICKETS table (depends on sessions)
-- ============================================================================

CREATE TABLE public.tickets (
    ticket_id character varying NOT NULL,
    customer_id character varying,
    user_id character varying,
    session_id character varying,
    issue text NOT NULL,
    priority character varying DEFAULT 'normal'::character varying,
    status character varying DEFAULT 'open'::character varying,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT tickets_pkey PRIMARY KEY (ticket_id),
    CONSTRAINT tickets_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.sessions(session_id)
);

-- ============================================================================
-- 5. CONVERSATION_SUMMARIES table (depends on sessions)
-- ============================================================================

CREATE TABLE public.conversation_summaries (
    id bigint NOT NULL DEFAULT nextval('conversation_summaries_id_seq'::regclass),
    summary_key character varying NOT NULL UNIQUE,
    user_id character varying NOT NULL,
    session_id character varying NOT NULL,
    ticket_id character varying,
    summary text NOT NULL,
    key_points jsonb,
    sentiment jsonb,
    action_items jsonb,
    next_steps jsonb,
    summary_length character varying DEFAULT 'medium'::character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT conversation_summaries_pkey PRIMARY KEY (id),
    CONSTRAINT conversation_summaries_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.sessions(session_id)
);

-- Create sequence if it doesn't exist
CREATE SEQUENCE IF NOT EXISTS conversation_summaries_id_seq;

-- ============================================================================
-- 6. FEEDBACK table (depends on sessions)
-- ============================================================================

CREATE TABLE public.feedback (
    id bigint NOT NULL DEFAULT nextval('feedback_id_seq'::regclass),
    feedback_id character varying NOT NULL UNIQUE,
    session_id character varying,
    user_id character varying NOT NULL,
    ticket_id character varying,
    feedback_type character varying NOT NULL,
    rating integer CHECK (rating >= 1 AND rating <= 5),
    comment text,
    reason text,
    category character varying,
    agent_used character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT feedback_pkey PRIMARY KEY (id),
    CONSTRAINT feedback_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.sessions(session_id)
);

-- Create sequence if it doesn't exist
CREATE SEQUENCE IF NOT EXISTS feedback_id_seq;

-- ============================================================================
-- 7. FEEDBACK_INSIGHTS table (independent)
-- ============================================================================

CREATE TABLE public.feedback_insights (
    id bigint NOT NULL DEFAULT nextval('feedback_insights_id_seq'::regclass),
    insight_key character varying NOT NULL UNIQUE,
    insight_type character varying NOT NULL,
    data jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT feedback_insights_pkey PRIMARY KEY (id)
);

-- Create sequence if it doesn't exist
CREATE SEQUENCE IF NOT EXISTS feedback_insights_id_seq;

-- ============================================================================
-- 8. KB_UPDATES_FROM_FEEDBACK table (depends on feedback)
-- ============================================================================

CREATE TABLE public.kb_updates_from_feedback (
    id bigint NOT NULL DEFAULT nextval('kb_updates_from_feedback_id_seq'::regclass),
    update_id character varying NOT NULL UNIQUE,
    feedback_id character varying,
    update_type character varying NOT NULL,
    content jsonb NOT NULL,
    status character varying DEFAULT 'pending'::character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT kb_updates_from_feedback_pkey PRIMARY KEY (id),
    CONSTRAINT kb_updates_from_feedback_feedback_id_fkey FOREIGN KEY (feedback_id) REFERENCES public.feedback(feedback_id)
);

-- Create sequence if it doesn't exist
CREATE SEQUENCE IF NOT EXISTS kb_updates_from_feedback_id_seq;

-- ============================================================================
-- 9. ANALYTICS_INTERACTIONS table (for tracking user interactions)
-- ============================================================================

CREATE TABLE public.analytics_interactions (
    id bigint NOT NULL DEFAULT nextval('analytics_interactions_id_seq'::regclass),
    user_id character varying NOT NULL,
    session_id character varying,
    query text,
    response_length integer,
    agent_used character varying,
    response_time double precision,
    timestamp timestamp with time zone DEFAULT now(),
    CONSTRAINT analytics_interactions_pkey PRIMARY KEY (id),
    CONSTRAINT analytics_interactions_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.sessions(session_id)
);

-- Create sequence if it doesn't exist
CREATE SEQUENCE IF NOT EXISTS analytics_interactions_id_seq;

-- ============================================================================
-- 10. AGENT_REFINEMENTS table (independent)
-- ============================================================================

CREATE TABLE public.agent_refinements (
    id bigint NOT NULL DEFAULT nextval('agent_refinements_id_seq'::regclass),
    refinement_key character varying NOT NULL UNIQUE,
    agent_name character varying NOT NULL,
    refinement_type character varying NOT NULL,
    changes jsonb NOT NULL,
    feedback_sources jsonb,
    status character varying DEFAULT 'pending'::character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT agent_refinements_pkey PRIMARY KEY (id)
);

-- Create sequence if it doesn't exist
CREATE SEQUENCE IF NOT EXISTS agent_refinements_id_seq;

-- ============================================================================
-- 11. REFUNDS table (depends on orders)
-- ============================================================================

CREATE TABLE public.refunds (
    id bigint NOT NULL DEFAULT nextval('refunds_id_seq'::regclass),
    refund_id character varying NOT NULL UNIQUE,
    order_id character varying NOT NULL,
    customer_id character varying NOT NULL,
    amount numeric NOT NULL,
    reason text,
    status character varying DEFAULT 'pending'::character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT refunds_pkey PRIMARY KEY (id),
    CONSTRAINT refunds_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(order_id)
);

-- Create sequence if it doesn't exist
CREATE SEQUENCE IF NOT EXISTS refunds_id_seq;

-- ============================================================================
-- 12. Create indexes to improve performance
-- ============================================================================

-- Indexes for sessions
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON public.sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON public.sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_is_active ON public.sessions(is_active);

-- Indexes for messages
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON public.messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_user_id ON public.messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON public.messages(timestamp);

-- Indexes for tickets
CREATE INDEX IF NOT EXISTS idx_tickets_session_id ON public.tickets(session_id);
CREATE INDEX IF NOT EXISTS idx_tickets_user_id ON public.tickets(user_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON public.tickets(status);

-- Indexes for orders
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON public.orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON public.orders(status);

-- Indexes for refunds
CREATE INDEX IF NOT EXISTS idx_refunds_order_id ON public.refunds(order_id);
CREATE INDEX IF NOT EXISTS idx_refunds_customer_id ON public.refunds(customer_id);
CREATE INDEX IF NOT EXISTS idx_refunds_status ON public.refunds(status);
CREATE INDEX IF NOT EXISTS idx_refunds_created_at ON public.refunds(created_at);

-- Indexes for conversation_summaries
CREATE INDEX IF NOT EXISTS idx_conversation_summaries_session_id ON public.conversation_summaries(session_id);
CREATE INDEX IF NOT EXISTS idx_conversation_summaries_user_id ON public.conversation_summaries(user_id);
CREATE INDEX IF NOT EXISTS idx_conversation_summaries_ticket_id ON public.conversation_summaries(ticket_id);

-- Indexes for feedback
CREATE INDEX IF NOT EXISTS idx_feedback_session_id ON public.feedback(session_id);
CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON public.feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_ticket_id ON public.feedback(ticket_id);
CREATE INDEX IF NOT EXISTS idx_feedback_type ON public.feedback(feedback_type);
CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON public.feedback(created_at);

-- Indexes for analytics_interactions
CREATE INDEX IF NOT EXISTS idx_analytics_interactions_user_id ON public.analytics_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_analytics_interactions_session_id ON public.analytics_interactions(session_id);
CREATE INDEX IF NOT EXISTS idx_analytics_interactions_timestamp ON public.analytics_interactions(timestamp);
CREATE INDEX IF NOT EXISTS idx_analytics_interactions_agent_used ON public.analytics_interactions(agent_used);
```

### Tables Overview

- **sessions**: Conversation sessions with user and customer tracking
- **orders**: Customer orders with status, items, and tracking
- **messages**: Chat messages linked to sessions
- **tickets**: Support tickets with priority and status
- **conversation_summaries**: AI-generated conversation summaries
- **feedback**: User feedback with ratings and comments
- **feedback_insights**: Aggregated insights from feedback analysis
- **kb_updates_from_feedback**: Knowledge base updates triggered by feedback
- **analytics_interactions**: User interaction tracking and metrics
- **agent_refinements**: Agent improvement suggestions from feedback
- **refunds**: Refund requests linked to orders

---

## Scalability & Performance

### Current Capacity
- **Concurrent Users**: 1000+
- **Response Time**: <30 seconds average
- **Throughput**: 100+ messages/second

### Optimization Strategies
1. **Caching**: FAQ and order data cached to reduce database queries
2. **Rate Limiting**: Prevents abuse and ensures fair resource usage
3. **Async Processing**: Non-blocking I/O for better concurrency
4. **Connection Pooling**: Efficient database connections (when implemented)

### Optimization Strategies
1. **Caching**: FAQ and order data cached to reduce database queries
2. **Rate Limiting**: Prevents abuse and ensures fair resource usage
3. **Async Processing**: Non-blocking I/O for better concurrency
4. **Lazy Loading**: Sentence Transformer model loaded only when needed
5. **Singleton Pattern**: Single instance of expensive resources (SemanticSearchEngine, QAChecker, ABTestingManager)
6. **Connection Pooling**: Efficient database connections via Supabase client

### Future Scalability
- **Load Balancing**: Multiple API server instances
- **Caching Layer**: Redis for distributed caching
- **Message Queue**: RabbitMQ/Kafka for async processing
- **CDN**: Static asset delivery for frontend

---

## Security

### Current Security Measures
1. **Input Validation**: All inputs validated and sanitized
2. **Rate Limiting**: Prevents abuse and DDoS attacks
3. **Error Handling**: No sensitive information in error messages
4. **Session Management**: Secure session handling

### Future Security Enhancements
1. **Authentication**: JWT-based authentication
2. **Authorization**: Role-based access control
3. **Encryption**: TLS/SSL for all communications
4. **Data Encryption**: Encrypt sensitive data at rest
5. **Audit Logging**: Comprehensive audit trails

---

## Deployment

### Development
```bash
# Start API server
python -m api.server

# Start React frontend
cd frontend && npm run dev
```

### Production (Recommended)
1. **Containerization**: Docker containers
2. **Orchestration**: Docker Compose or Kubernetes
3. **Reverse Proxy**: Nginx for load balancing
4. **Monitoring**: Prometheus + Grafana
5. **Logging**: ELK Stack or CloudWatch

### Environment Variables
- `GOOGLE_API_KEY`: Required for Gemini API
- `MODEL_NAME`: Gemini model to use (default: gemini-2.5-flash-lite)
- `API_HOST`: API server host (default: 0.0.0.0)
- `API_PORT`: API server port (default: 8000)

---

## A2A Protocol (Agent-to-Agent Communication)

CustoFlow implements **A2A Protocol** to enable direct communication between specialized agents, creating more intelligent and context-aware workflows.

### A2A Connections

1. **FAQ Agent ↔ Order Agent**
   - FAQ Agent can call Order Agent to get order context when answering order-related FAQs
   - Example: "What's the refund policy for my order?" → FAQ Agent gets order details → Provides personalized answer

2. **Order Agent ↔ FAQ Agent**
   - Order Agent can call FAQ Agent to get policy information
   - Example: "Can I cancel my order?" → Order Agent checks order status → FAQ Agent provides cancellation policy → Combined answer

3. **Sentiment Agent → Escalation Agent**
   - Sentiment Agent can directly call Escalation Agent for urgent issues
   - Example: High urgency detected → Sentiment Agent creates ticket with appropriate priority immediately

### Benefits

- **Context-Aware Responses**: Agents gather all needed context before responding
- **Faster Resolution**: One response instead of multiple back-and-forth exchanges
- **Better Prioritization**: Urgent issues get flagged immediately
- **Reduced Orchestrator Overhead**: Agents handle their own sub-routing

### Implementation

A2A Protocol is implemented using ADK's `AgentTool` pattern, allowing agents to call each other as tools. This enables:
- Direct agent-to-agent communication
- Context sharing between agents
- Intelligent sub-routing decisions
- More natural multi-agent workflows

See [docs/A2A_BENEFITS.md](A2A_BENEFITS.md) for detailed use cases and benefits.

## Architecture Decisions

### Why Multi-Agent?
- **Specialization**: Each agent optimized for specific tasks
- **Maintainability**: Easier to update individual agents
- **Scalability**: Can scale agents independently
- **Accuracy**: Better routing = better responses
- **A2A Protocol**: Agents can collaborate directly for context-aware responses

### Why Supabase (PostgreSQL)?
- **Production-Ready**: Full-featured database with RLS policies
- **Scalability**: Handles large datasets efficiently
- **Real-time**: Built-in real-time subscriptions
- **Storage**: Integrated file storage for FAISS indices
- **Security**: Row-level security for data access control

### Why FastAPI + React?
- **FastAPI**: High performance, async support, automatic docs
- **React/Next.js**: Modern, performant web framework with TypeScript
- **Separation**: API and UI can scale independently

---

## Quality Assurance & Compliance

### QA System
- **Automatic Quality Scoring**: Every assistant response is scored (0.0-1.0)
- **Compliance Detection**: Keywords related to GDPR, privacy, security, legal, financial
- **Profanity Filtering**: Flags inappropriate language
- **Quality Indicators**: Checks for helpfulness, politeness, actionable information
- **Status Classification**: Responses categorized as pass, warning, or fail

### A/B Testing System
- **Variant Management**: Create and manage instruction variants for agents
- **Consistent Routing**: Same user always gets same variant (hashing-based)
- **Metrics Collection**: Satisfaction, response time, escalations, resolutions, feedback
- **Statistical Analysis**: T-test to determine if one variant performs significantly better
- **Automatic Recommendations**: System suggests the best-performing variant

---

## Future Architecture Improvements

1. **Microservices**: Split into separate services
2. **Event-Driven**: Message queue for async processing
3. **Caching**: Redis for hot data
4. **CDN**: Static asset delivery
5. **Monitoring**: APM tools (Datadog, New Relic)
6. **ML Integration**: Predictive escalation with ML models

---

*Last Updated: 2025-01-27*
*Version: 2.0*

