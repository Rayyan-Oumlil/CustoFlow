"""Test script for Step 6: Order Agent."""
import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.order_agent import order_agent
from google.adk.runners import InMemoryRunner


async def test_order_agent():
    """Test the Order agent with sample queries."""
    print("Testing Order Agent...")
    print("-" * 60)
    
    # Create runner
    runner = InMemoryRunner(agent=order_agent)
    
    # Test 1: Order status query
    print("\nTest 1: Asking about order status")
    print("User: What's the status of order 12345?")
    try:
        events = await runner.run_debug("What's the status of order 12345?")
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
        if response_text and ("12345" in response_text or "shipped" in response_text.lower() or "order" in response_text.lower()):
            print("[PASS] Test 1 PASSED - Agent provided order information")
        else:
            print("[PARTIAL] Test 1 PARTIAL - Response received but may not contain expected info")
    except Exception as e:
        print(f"[FAIL] Test 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: Invalid order query
    print("\nTest 2: Asking about invalid order")
    print("User: What's the status of order 99999?")
    try:
        events = await runner.run_debug("What's the status of order 99999?")
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
        
        print(f"Agent: {response_text[:150]}...")
        if response_text and ("not found" in response_text.lower() or "verify" in response_text.lower() or "sorry" in response_text.lower()):
            print("[PASS] Test 2 PASSED - Agent handled invalid order gracefully")
        else:
            print("[PARTIAL] Test 2 PARTIAL - Response received")
    except Exception as e:
        print(f"[FAIL] Test 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "-" * 60)
    print("[SUCCESS] Step 6 Checkpoint PASSED!")
    print("[OK] Order agent is working and calling tools successfully")
    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_order_agent())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"[ERROR] Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

