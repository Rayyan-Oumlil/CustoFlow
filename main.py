"""Main CLI entry point for customer support agent."""
import asyncio
import sys
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


async def chat_loop():
    """Interactive chat loop with the customer support agent."""
    print("=" * 60)
    print("Customer Support Agent - Interactive Chat")
    print("=" * 60)
    print("Type 'quit' or 'exit' to end the conversation")
    print("=" * 60)
    print()
    
    # Create runner with session support and observability plugins
    runner = Runner(
        agent=orchestrator_agent,
        app_name=settings.app_name,
        session_service=session_manager.get_service(),
        plugins=[logging_plugin]  # Add logging plugin for observability
    )
    
    # Get user ID (in production, this would come from authentication)
    user_id = input("Enter your user ID (or press Enter for 'guest'): ").strip() or "guest"
    session_id = f"session_{user_id}_{os.urandom(4).hex()}"
    
    # Create session
    try:
        await session_manager.get_service().create_session(
            app_name=settings.app_name,
            user_id=user_id,
            session_id=session_id
        )
        logger.info(f"Session created: {session_id} for user: {user_id}")
    except Exception as e:
        logger.warning(f"Session may already exist: {e}")
    
    metrics.increment("sessions_started")
    
    print(f"\nSession started. How can I help you today?\n")
    
    while True:
        try:
            # Get user input
            user_message = input("You: ").strip()
            
            if not user_message:
                continue
            
            if user_message.lower() in ['quit', 'exit', 'q']:
                print("\nThank you for using our customer support. Goodbye!")
                break
            
            # Increment metrics
            metrics.increment("messages_received")
            
            # Create message
            message = types.Content(
                role="user",
                parts=[types.Part(text=user_message)]
            )
            
            # Get agent response
            print("Agent: ", end="", flush=True)
            response_text = ""
            
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=message
            ):
                if event.is_final_response() and event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            response_text = part.text
                            print(part.text, end="", flush=True)
                            break
            
            print()  # New line after response
            metrics.increment("messages_sent")
            
            # Log interaction
            logger.info(f"User: {user_id}, Message: {user_message[:50]}...")
            
        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error in chat loop: {e}", exc_info=True)
            print(f"Sorry, an error occurred: {e}")
            metrics.increment("errors")
    
    # Print session metrics
    print(f"\nSession metrics:")
    print(f"  Messages received: {metrics.get('messages_received')}")
    print(f"  Messages sent: {metrics.get('messages_sent')}")
    print(f"  Errors: {metrics.get('errors')}")


def main():
    """Main entry point."""
    try:
        asyncio.run(chat_loop())
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

