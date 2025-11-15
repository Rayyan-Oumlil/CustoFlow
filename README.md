# CustoFlow - Multi-Agent Customer Support System

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Kaggle Capstone](https://img.shields.io/badge/Kaggle-Capstone-orange.svg)](https://www.kaggle.com/competitions/agents-intensive-capstone-project)

**Capstone Project for Kaggle 5-Day AI Agents Intensive Course**

CustoFlow is an intelligent multi-agent customer support system that automates first-line support with smart routing, sentiment analysis, and intelligent escalation. Built with Google's Agent Development Kit (ADK) and powered by Gemini.

## 🎯 Problem Statement

Companies receive thousands of repetitive customer support queries daily (order status, refunds, shipping, FAQs). Human agents get overloaded, response times slow to hours, and conversations lack continuity. This leads to:
- High operational costs
- Slow response times (hours to days)
- Inconsistent service quality
- Customer frustration

**Solution**: CustoFlow automates 80%+ of common queries with intelligent routing, freeing human agents for complex issues while maintaining high-quality, context-aware responses.

## ✨ Key Features

- **Multi-Agent Architecture**: 5 specialized agents working in harmony
- **Intelligent Routing**: Automatically routes queries to the right specialist
- **Sentiment Analysis**: Detects customer emotion and urgency
- **Context-Aware**: Maintains conversation context across turns
- **Smart Escalation**: Creates tickets for complex issues
- **Production-Ready**: FastAPI server with observability

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│         Customer Query                          │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
         ┌─────────────────────┐
         │   CustoFlow         │  ← Main Orchestrator
         │ (Orchestrator)      │
         └──────────┬───────────┘
                    │
       ┌────────────┼────────────┐
       │            │            │
       ▼            ▼            ▼
  ┌────────┐   ┌────────┐   ┌──────────┐
  │  FAQ   │   │ Order  │   │Sentiment │
  │ Agent  │   │ Agent  │   │  Agent   │
  └───┬────┘   └───┬────┘   └────┬─────┘
      │            │              │
      ▼            ▼              ▼
  ┌────────┐   ┌────────┐   ┌──────────┐
  │FAQ Tool│   │Order   │   │Escalation│
  │        │   │Tool    │   │  Agent   │
  └────────┘   └────────┘   └──────────┘
```

## 📚 Course Concepts Demonstrated

This project demonstrates **6+ key concepts** from the Kaggle 5-Day AI Agents Intensive Course:

### 1. ✅ Multi-Agent System
- **CustoFlow (Orchestrator)**: Routes queries to specialized agents
- **FAQ Agent**: Answers general questions from knowledge base
- **Order Agent**: Handles order status and tracking inquiries
- **Sentiment Agent**: Analyzes customer emotion and urgency
- **Escalation Agent**: Creates tickets for human intervention

### 2. ✅ Tools
- `search_faq`: Search FAQ knowledge base with flexible matching
- `lookup_order`: Retrieve order information
- `get_customer_orders`: Get all orders for a customer
- `create_ticket`: Create support tickets
- `get_ticket_status`: Check ticket status
- **Long-Running Operations (LRO)**: `create_ticket_with_approval` with human-in-the-loop

### 3. ✅ Sessions & Memory
- Session management with `InMemorySessionService`
- **Context Compaction**: Automatic context window management
- Context preservation across conversation turns
- Long-term memory with `InMemoryMemoryService`
- **Memory Ingestion**: Automatic consolidation of session data

### 4. ✅ Observability
- **ADK LoggingPlugin** for structured agent logging
- Structured logging with configurable levels
- Metrics collection (sessions, messages, errors)
- Tracing for request tracking
- Tool call logging and agent decision tracking

### 5. ✅ Agent Evaluation
- Comprehensive test suite with 9+ unit tests
- Evaluation suite with automated scoring
- Test coverage for all routing paths
- Category-based performance reporting

### 6. ✅ A2A Protocol
- A2A-ready agent architecture
- Architecture documented for remote agent deployment
- `RemoteA2aAgent` support ready for distributed systems
- Cross-service communication pattern

### 7. ✅ Agent Deployment
- FastAPI production server
- RESTful API endpoints
- Health checks and metrics endpoints
- Ready for Cloud Run / GKE deployment

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Google AI Studio API key ([Get one here](https://aistudio.google.com/app/apikey))

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/Rayyan-Oumlil/CustoFlow.git
cd CustoFlow
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Create `.env` file:**
```bash
GOOGLE_API_KEY=your_api_key_here
```

4. **Run tests to verify setup:**
```bash
python -m pytest tests/
```

## 💻 Usage

### Interactive CLI

```bash
python main.py
```

### API Server

```bash
python -m api.server
```

Then access:
- API: `http://localhost:8000`
- Health: `http://localhost:8000/health`
- Metrics: `http://localhost:8000/metrics`

### Example API Request

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is your refund policy?",
    "user_id": "user123"
  }'
```

## 📁 Project Structure

```
CustoFlow/
├── agents/              # Agent definitions
│   ├── orchestrator_agent.py
│   ├── faq_agent.py
│   ├── order_agent.py
│   ├── sentiment_agent.py
│   └── escalation_agent.py
├── tools/              # Custom tools
│   ├── faq_tool.py
│   ├── order_tool.py
│   ├── ticket_tool.py
│   └── ticket_tool_lro.py
├── memory/             # Session & memory management
│   ├── session_store.py
│   └── long_term_memory.py
├── observability/      # Logging, metrics, tracing
│   ├── logging_config.py
│   ├── metrics.py
│   └── tracing.py
├── api/               # FastAPI server
│   └── server.py
├── tests/             # Test suite
├── data/              # Knowledge base
│   └── faq_knowledge_base.json
├── config/           # Configuration
│   └── settings.py
├── main.py           # CLI entry point
└── requirements.txt
```

## 🧪 Testing

Run the full test suite:
```bash
python -m pytest tests/
```

Run evaluation suite:
```bash
python notebooks/evaluation.py
```

## 📊 Evaluation Results

The system has been evaluated on multiple test cases covering:
- FAQ queries (refunds, shipping, policies)
- Order inquiries (status, tracking)
- Sentiment analysis (frustration, urgency)
- Escalation scenarios (complex issues)

See `notebooks/evaluation.py` for detailed evaluation metrics.

## 🔧 Configuration

Configuration is managed via environment variables in `.env`:

```env
GOOGLE_API_KEY=your_api_key
MODEL_NAME=gemini-2.5-flash-lite
APP_NAME=CustoFlow
DEBUG=false
API_HOST=0.0.0.0
API_PORT=8000
```

## 🎓 Course Concepts Summary

| Concept | Status | Implementation |
|---------|--------|----------------|
| Multi-Agent System | ✅ | 5 agents with orchestrator pattern |
| Custom Tools | ✅ | 5 FunctionTools + 1 LRO tool |
| Sessions | ✅ | InMemorySessionService |
| Context Compaction | ✅ | Automatic by ADK |
| Long-Term Memory | ✅ | InMemoryMemoryService + ingestion |
| Logging | ✅ | LoggingPlugin + structured logging |
| Metrics | ✅ | Thread-safe metrics collector |
| Tracing | ✅ | Request-level tracing |
| Evaluation | ✅ | Automated test suite |
| A2A Protocol | ✅ | Architecture ready |
| Deployment | ✅ | FastAPI production server |

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google's Agent Development Kit (ADK) team
- Kaggle 5-Day AI Agents Intensive Course instructors
- Gemini model by Google DeepMind

## 📧 Contact

For questions or issues, please open an issue on GitHub.

---

**Built with ❤️ for the Kaggle 5-Day AI Agents Intensive Course Capstone Project**
