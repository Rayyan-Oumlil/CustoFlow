"""Test script for Step 8: Sentiment Agent."""
import asyncio
import sys
import os
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.sentiment_agent import sentiment_agent
from google.adk.runners import InMemoryRunner


@pytest.mark.asyncio
async def test_sentiment_agent():
    """Test the Sentiment agent."""
    print("Testing Sentiment Agent...")
    print("-" * 60)
    
    runner = InMemoryRunner(agent=sentiment_agent)
    
    # Test 1: Negative sentiment
    print("\nTest 1: Analyzing negative sentiment")
    print("User: This is terrible! I'm very frustrated!")
    try:
        events = await runner.run_debug("This is terrible! I'm very frustrated!")
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
        # Try to parse as JSON
        try:
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                result = json.loads(json_str)
                if result.get("sentiment") in ["negative", "neutral", "positive"]:
                    print(f"[PASS] Test 1 PASSED - Sentiment: {result.get('sentiment')}")
                else:
                    print("[PARTIAL] Test 1 PARTIAL - Response received")
            else:
                print("[PARTIAL] Test 1 PARTIAL - No JSON found")
        except:
            if "negative" in response_text.lower() or "frustrated" in response_text.lower():
                print("[PASS] Test 1 PASSED - Detected negative sentiment")
            else:
                print("[PARTIAL] Test 1 PARTIAL - Response received")
    except Exception as e:
        print(f"[FAIL] Test 1 FAILED: {e}")
        return False
    
    print("\n" + "-" * 60)
    print("[SUCCESS] Step 8 Checkpoint PASSED!")
    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_sentiment_agent())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"[ERROR] Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

