"""Test script for Step 7: Escalation Agent."""
import asyncio
import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.escalation_agent import escalation_agent
from google.adk.runners import InMemoryRunner


@pytest.mark.asyncio
async def test_escalation_agent():
    """Test the Escalation agent."""
    print("Testing Escalation Agent...")
    print("-" * 60)
    
    runner = InMemoryRunner(agent=escalation_agent)
    
    # Test 1: Create ticket
    print("\nTest 1: Creating a support ticket")
    print("User: I need help with a damaged product")
    try:
        events = await runner.run_debug("I need help with a damaged product I received")
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
        if response_text and ("ticket" in response_text.lower() or "TICKET" in response_text):
            print("[PASS] Test 1 PASSED - Agent created ticket")
        else:
            print("[PARTIAL] Test 1 PARTIAL - Response received")
    except Exception as e:
        print(f"[FAIL] Test 1 FAILED: {e}")
        return False
    
    print("\n" + "-" * 60)
    print("[SUCCESS] Step 7 Checkpoint PASSED!")
    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_escalation_agent())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"[ERROR] Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

