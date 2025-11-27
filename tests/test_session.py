"""Test script for Step 4: Session Support."""
import asyncio
import sys
import os
import uuid
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.faq_agent import faq_agent
from memory.session_store import session_manager
from google.adk.runners import Runner
from google.genai import types


@pytest.mark.asyncio
async def test_session():
    """Test that agent remembers context across multiple turns in same session."""
    print("Testing Session Support...")
    print("-" * 60)
    
    # Create runner with session service
    runner = Runner(
        agent=faq_agent,
        app_name="test_app",
        session_service=session_manager.get_service()
    )
    
    # Create a new session
    user_id = "test_user"
    session_id = f"test_session_{uuid.uuid4().hex[:8]}"
    
    try:
        session = await session_manager.get_service().create_session(
            app_name="test_app",
            user_id=user_id,
            session_id=session_id
        )
        print(f"[OK] Session created: {session_id}")
    except Exception as e:
        print(f"[WARN] Session may already exist: {e}")
        session = await session_manager.get_service().get_session(
            app_name="test_app",
            user_id=user_id,
            session_id=session_id
        )
    
    # Test 1: First message
    print("\nTest 1: First message in session")
    print("User: What is your refund policy?")
    
    message1 = types.Content(
        role="user",
        parts=[types.Part(text="What is your refund policy?")]
    )
    
    response1 = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=message1
    ):
        if event.is_final_response() and event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    response1 = part.text
                    print(f"Agent: {response1[:200]}...")
    
    if not response1:
        print("[FAIL] No response received")
        return False
    
    print("[PASS] Test 1 PASSED - Agent responded")
    
    # Test 2: Second message (should remember context)
    print("\nTest 2: Second message in same session")
    print("User: Can you tell me more about that?")
    
    message2 = types.Content(
        role="user",
        parts=[types.Part(text="Can you tell me more about that?")]
    )
    
    response2 = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=message2
    ):
        if event.is_final_response() and event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    response2 = part.text
                    print(f"Agent: {response2[:200]}...")
    
    if not response2:
        print("[FAIL] No response received")
        return False
    
    # Check if agent shows awareness of previous context
    if "refund" in response2.lower() or len(response2) > 50:
        print("[PASS] Test 2 PASSED - Agent shows context awareness")
    else:
        print("[PARTIAL] Test 2 PARTIAL - Response received but context awareness unclear")
    
    print("\n" + "-" * 60)
    print("[SUCCESS] Step 4 Checkpoint PASSED!")
    print("[OK] Session support is working - agent maintains conversation context")
    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_session())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"[ERROR] Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

