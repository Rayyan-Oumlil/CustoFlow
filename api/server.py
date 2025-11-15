"""FastAPI server for customer support agent."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import asyncio
import os
from google.genai import types

from config.settings import settings
from agents.orchestrator_agent import orchestrator_agent
from memory.session_store import session_manager
from google.adk.runners import Runner
from observability.logging_config import setup_logging, get_logger, get_logging_plugin
from observability.metrics import metrics

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Get ADK LoggingPlugin for enhanced observability
logging_plugin = get_logging_plugin()

# Create FastAPI app
app = FastAPI(
    title="Customer Support Agent API",
    description="Multi-agent customer support system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create runner with observability plugins
runner = Runner(
    agent=orchestrator_agent,
    app_name=settings.app_name,
    session_service=session_manager.get_service(),
    plugins=[logging_plugin]  # Add logging plugin for observability
)


# Request/Response models
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "guest"
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    metrics: dict


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Customer Support Agent API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "metrics": metrics.get_counts()
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint for customer support."""
    try:
        # Generate session ID if not provided
        if not request.session_id:
            session_id = f"session_{request.user_id}_{os.urandom(4).hex()}"
        else:
            session_id = request.session_id
        
        # Create session if it doesn't exist
        try:
            await session_manager.get_service().create_session(
                app_name=settings.app_name,
                user_id=request.user_id,
                session_id=session_id
            )
            metrics.increment("sessions_started")
            logger.info(f"New session created: {session_id}")
        except Exception:
            # Session may already exist, that's okay
            pass
        
        # Increment metrics
        metrics.increment("messages_received")
        
        # Create message
        message = types.Content(
            role="user",
            parts=[types.Part(text=request.message)]
        )
        
        # Get agent response
        response_text = ""
        async for event in runner.run_async(
            user_id=request.user_id,
            session_id=session_id,
            new_message=message
        ):
            if event.is_final_response() and event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        response_text = part.text
                        break
                if response_text:
                    break
        
        metrics.increment("messages_sent")
        logger.info(f"Response sent to user: {request.user_id}")
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            metrics=metrics.get_counts()
        )
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        metrics.increment("errors")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def get_metrics():
    """Get current metrics."""
    return metrics.get_counts()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level="info"
    )

