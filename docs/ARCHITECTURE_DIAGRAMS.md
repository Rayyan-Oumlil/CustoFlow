# Architecture Diagrams

Visual representations of CustoFlow's architecture and data flow.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Customer Interface                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Web UI     │  │   Mobile App │  │   API Client │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
                    ┌────────▼────────┐
                    │   FastAPI Server │
                    │   (api/server.py)│
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
    ┌─────▼─────┐    ┌───────▼──────┐   ┌──────▼──────┐
    │ Validation│    │ Rate Limiter │   │   Cache     │
    │  & Sanitize│    │              │   │             │
    └─────┬─────┘    └───────┬──────┘   └──────┬──────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Orchestrator    │
                    │     Agent        │
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
    ┌─────▼─────┐    ┌───────▼──────┐   ┌──────▼──────┐
    │  FAQ      │    │    Order     │   │  Sentiment  │
    │  Agent    │    │    Agent     │   │   Agent     │
    └─────┬─────┘    └───────┬──────┘   └──────┬──────┘
          │                  │                  │
    ┌─────▼─────┐    ┌───────▼──────┐   ┌──────▼──────┐
    │  FAQ      │    │   Order      │   │  Escalation │
    │  Tool     │    │   Tool       │   │   Agent     │
    └───────────┘    └──────────────┘   └──────┬──────┘
                                                │
                                        ┌───────▼──────┐
                                        │  Ticket Tool │
                                        │  (with LRO)  │
                                        └──────────────┘
```

## Agent Communication Flow

```
User Query
    │
    ▼
┌─────────────────┐
│  Orchestrator   │  ← Analyzes query, determines routing
└────────┬────────┘
         │
         ├─── FAQ Query? ────────► FAQ Agent ───► FAQ Tool
         │
         ├─── Order Query? ───────► Order Agent ──► Order Tool
         │
         ├─── Sentiment Needed? ──► Sentiment Agent
         │
         └─── Escalation? ─────────► Escalation Agent ──► Ticket Tool
                                         │
                                         └─── High Priority? ──► LRO Tool
                                                                    │
                                                                    ▼
                                                              Human Approval
                                                                    │
                                                                    ▼
                                                              Ticket Created
```

## Data Flow

```
┌──────────────┐
│ User Message │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│ Input Validation │  ← Check length, format, sanitize
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Rate Limiting   │  ← Check request limits
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│   Cache Check    │  ← Look for cached response
└──────┬───────────┘
       │
       ├─── Cache Hit? ────► Return Cached Response
       │
       └─── Cache Miss? ────►
                              │
                              ▼
                    ┌──────────────────┐
                    │  Agent Processing │  ← Route to appropriate agent
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Tool Execution   │  ← Execute tools (FAQ, Order, etc.)
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Cache Result    │  ← Store in cache
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Log Analytics   │  ← Track interaction
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Store History   │  ← Save to conversation history
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Return Response │
                    └──────────────────┘
```

## Memory Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Session Memory                        │
│  ┌──────────────────────────────────────────────────┐   │
│  │  InMemorySessionService                          │   │
│  │  - Current conversation context                  │   │
│  │  - Automatic context compaction                  │   │
│  │  - Event history                                 │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                            │
                            │ (After session ends)
                            ▼
┌─────────────────────────────────────────────────────────┐
│              Conversation History                        │
│  ┌──────────────────────────────────────────────────┐   │
│  │  ConversationHistory                             │   │
│  │  - Persistent across sessions                    │   │
│  │  - User-specific history                         │   │
│  │  - Session tracking                              │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                            │
                            │ (Key information extraction)
                            ▼
┌─────────────────────────────────────────────────────────┐
│                Long-Term Memory                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  MemoryManager                                   │   │
│  │  - Customer preferences                          │   │
│  │  - Past issues and resolutions                   │   │
│  │  - Sentiment history                             │   │
│  │  - Common patterns                              │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Observability Stack

```
┌─────────────────────────────────────────────────────────┐
│                    Application                           │
└────────┬─────────────────────────────────────────────────┘
         │
         ├─── Logging ──────────► ┌──────────────────┐
         │                        │  LoggingPlugin    │
         │                        │  - ADK logs       │
         │                        │  - Structured logs│
         │                        └───────────────────┘
         │
         ├─── Metrics ───────────► ┌──────────────────┐
         │                        │  Metrics          │
         │                        │  - Counters        │
         │                        │  - Sessions       │
         │                        │  - Errors         │
         │                        └───────────────────┘
         │
         ├─── Tracing ───────────► ┌──────────────────┐
         │                        │  Tracing          │
         │                        │  - Request spans  │
         │                        │  - Tool calls     │
         │                        │  - Agent decisions│
         │                        └───────────────────┘
         │
         └─── Analytics ─────────► ┌──────────────────┐
                                   │  Analytics        │
                                   │  - Interactions   │
                                   │  - Query patterns │
                                   │  - Agent perf     │
                                   │  - Feedback       │
                                   └───────────────────┘
```

## Security Layers

```
┌─────────────────────────────────────────────────────────┐
│                    User Input                            │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │  Input Validation       │  ← Length, format checks
        └────────────┬────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │  Sanitization           │  ← Remove dangerous chars
        └────────────┬────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │  Rate Limiting          │  ← Prevent abuse
        └────────────┬────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │  Error Handling         │  ← User-friendly errors
        └────────────┬────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │  Processing             │
        └────────────────────────┘
```

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Production                            │
│                                                         │
│  ┌──────────────┐      ┌──────────────┐               │
│  │  Load        │      │  API Server  │               │
│  │  Balancer    │─────►│  (FastAPI)   │               │
│  └──────────────┘      └──────┬───────┘               │
│                               │                        │
│                    ┌──────────┼──────────┐            │
│                    │          │          │            │
│              ┌─────▼───┐ ┌────▼────┐ ┌──▼────┐      │
│              │ Agent   │ │ Agent   │ │ Agent  │      │
│              │ Instance│ │ Instance│ │ Instance│      │
│              └─────────┘ └─────────┘ └────────┘      │
│                                                         │
│  ┌──────────────┐      ┌──────────────┐               │
│  │  Database    │      │  Cache       │               │
│  │  (Sessions)  │      │  (Redis)     │               │
│  └──────────────┘      └──────────────┘               │
│                                                         │
│  ┌──────────────┐      ┌──────────────┐               │
│  │  Monitoring  │      │  Logging     │               │
│  │  (Metrics)   │      │  (Cloud)     │               │
│  └──────────────┘      └──────────────┘               │
└─────────────────────────────────────────────────────────┘
```

## Component Interaction

```
┌─────────────┐
│   Tools     │
│  (FAQ,      │
│   Order)    │
└──────┬──────┘
       │
       │ Uses
       ▼
┌─────────────┐
│   Agents    │
│  (FAQ,      │
│   Order,    │
│   etc.)     │
└──────┬──────┘
       │
       │ Used by
       ▼
┌─────────────┐
│ Orchestrator│
│   Agent     │
└──────┬──────┘
       │
       │ Runs via
       ▼
┌─────────────┐
│   Runner    │
│  (ADK)      │
└──────┬──────┘
       │
       │ Uses
       ▼
┌─────────────┐
│  Sessions   │
│  & Memory   │
└─────────────┘
```

## Request Lifecycle

```
1. Request Received
   │
   ▼
2. Validation & Sanitization
   │
   ▼
3. Rate Limit Check
   │
   ▼
4. Cache Lookup
   │
   ├─── Hit? ────► Return Cached
   │
   └─── Miss? ────►
                   │
                   ▼
5. Orchestrator Routing
   │
   ▼
6. Agent Processing
   │
   ▼
7. Tool Execution
   │
   ▼
8. Response Generation
   │
   ▼
9. Cache Storage
   │
   ▼
10. Analytics Logging
    │
    ▼
11. History Storage
    │
    ▼
12. Response Returned
```

