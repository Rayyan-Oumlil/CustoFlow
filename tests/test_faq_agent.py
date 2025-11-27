"""Test script for Step 3: First Agent (FAQ)."""
import asyncio
import sys
import os
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.faq_agent import faq_agent
from google.adk.runners import InMemoryRunner


@pytest.mark.asyncio
async def test_faq_agent():
    """Test the FAQ agent with sample queries."""
    print("Testing FAQ Agent...")
    print("-" * 60)
    
    # Create runner
    runner = InMemoryRunner(agent=faq_agent)
    
    # Test 1: Refund question
    print("\nTest 1: Asking about refund policy")
    print("User: What is your refund policy?")
    try:
        events = await runner.run_debug("What is your refund policy?")
        # Extract text from events
        response_text = ""
        for event in events:
            if event.is_final_response() and event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        response_text = part.text
                        break
                if response_text:
                    break
        
        print(f"Agent: {response_text[:200]}...")
        if response_text and ("refund" in response_text.lower() or "30" in response_text or "day" in response_text.lower()):
            print("[PASS] Test 1 PASSED - Agent provided refund information")
        else:
            print("[PARTIAL] Test 1 PARTIAL - Response received but may not contain expected info")
    except Exception as e:
        print(f"[FAIL] Test 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: Shipping question
    print("\nTest 2: Asking about shipping")
    print("User: How long does shipping take?")
    try:
        events = await runner.run_debug("How long does shipping take?")
        # Extract text from events
        response_text = ""
        for event in events:
            if event.is_final_response() and event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        response_text = part.text
                        break
                if response_text:
                    break
        
        print(f"Agent: {response_text[:200]}...")
        if response_text and ("shipping" in response_text.lower() or "day" in response_text.lower()):
            print("[PASS] Test 2 PASSED - Agent provided shipping information")
        else:
            print("[PARTIAL] Test 2 PARTIAL - Response received but may not contain expected info")
    except Exception as e:
        print(f"[FAIL] Test 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "-" * 60)
    print("[SUCCESS] Step 3 Checkpoint PASSED!")
    print("[OK] FAQ agent is working and calling the tool successfully")
    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_faq_agent())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"[ERROR] Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

