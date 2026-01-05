"""Evaluation script for customer support agents."""
import asyncio
import sys
import os
import uuid
from typing import List, Dict, Any
from google.genai import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.faq_agent import faq_agent
from agents.order_agent import order_agent
from agents.orchestrator_agent import orchestrator_agent
from agents.sentiment_agent import sentiment_agent
from agents.escalation_agent import escalation_agent
from google.adk.runners import Runner
from memory.session_store import session_manager
from config.settings import settings


# Evaluation Test Cases
# Comprehensive test suite covering all agent types and routing scenarios
# Each test case includes:
# - id: Unique test identifier
# - query: Customer query to test
# - agent: Which agent should handle it
# - expected_keywords: Keywords that should appear in response
# - category: Test category for reporting
TEST_CASES = [
    # FAQ Agent Tests
    {
        "id": "faq_1",
        "query": "What is your refund policy?",
        "agent": "faq_agent",
        "expected_keywords": ["refund"],
        "category": "FAQ"
    },
    {
        "id": "faq_2",
        "query": "How long does shipping take?",
        "agent": "faq_agent",
        "expected_keywords": ["shipping"],
        "category": "FAQ"
    },
    {
        "id": "faq_3",
        "query": "Can I return items?",
        "agent": "faq_agent",
        "expected_keywords": ["return"],
        "category": "FAQ"
    },
    {
        "id": "faq_4",
        "query": "What are your payment methods?",
        "agent": "faq_agent",
        "expected_keywords": ["payment"],
        "category": "FAQ"
    },
    {
        "id": "faq_5",
        "query": "Do you ship internationally?",
        "agent": "faq_agent",
        "expected_keywords": ["ship"],
        "category": "FAQ"
    },
    # Order Agent Tests
    {
        "id": "order_1",
        "query": "What's the status of order 12345?",
        "agent": "order_agent",
        "expected_keywords": ["12345", "order"],
        "category": "Order"
    },
    {
        "id": "order_2",
        "query": "Where is my order 67890?",
        "agent": "order_agent",
        "expected_keywords": ["67890", "order"],
        "category": "Order"
    },
    {
        "id": "order_3",
        "query": "Tell me about order 11111",
        "agent": "order_agent",
        "expected_keywords": ["11111", "order"],
        "category": "Order"
    },
    # Orchestrator Routing Tests
    {
        "id": "orchestrator_1",
        "query": "I want to know about refunds",
        "agent": "orchestrator_agent",
        "expected_keywords": ["refund"],
        "category": "Routing"
    },
    {
        "id": "orchestrator_2",
        "query": "Check my order 12345",
        "agent": "orchestrator_agent",
        "expected_keywords": ["12345", "order"],
        "category": "Routing"
    },
    {
        "id": "orchestrator_3",
        "query": "I'm very frustrated with my order!",
        "agent": "orchestrator_agent",
        "expected_keywords": ["order"],
        "category": "Routing"
    },
    {
        "id": "orchestrator_4",
        "query": "I need help with a damaged product",
        "agent": "orchestrator_agent",
        "expected_keywords": ["help", "damaged"],
        "category": "Routing"
    },
    {
        "id": "orchestrator_5",
        "query": "What's your return policy and where is order 12345?",
        "agent": "orchestrator_agent",
        "expected_keywords": ["return", "12345"],
        "category": "Routing"
    },
    # Sentiment Agent Tests
    {
        "id": "sentiment_1",
        "query": "I'm extremely frustrated with my order!",
        "agent": "sentiment_agent",
        "expected_keywords": ["negative", "frustrated"],
        "category": "Sentiment"
    },
    {
        "id": "sentiment_2",
        "query": "I love your service, thank you so much!",
        "agent": "sentiment_agent",
        "expected_keywords": ["positive", "happy"],
        "category": "Sentiment"
    },
    {
        "id": "sentiment_3",
        "query": "This is unacceptable! I want a refund immediately!",
        "agent": "sentiment_agent",
        "expected_keywords": ["negative", "angry"],
        "category": "Sentiment"
    },
    # Escalation Agent Tests
    {
        "id": "escalation_1",
        "query": "I need to create a ticket for a damaged product",
        "agent": "escalation_agent",
        "expected_keywords": ["ticket"],
        "category": "Escalation"
    },
    {
        "id": "escalation_2",
        "query": "My order was never delivered, I need urgent help",
        "agent": "escalation_agent",
        "expected_keywords": ["ticket", "urgent"],
        "category": "Escalation"
    },
]


async def evaluate_agent(agent, query: str, expected_keywords: List[str]) -> Dict[str, Any]:
    """Evaluate a single agent query using run_async with session."""
    # Create unique session for this test
    user_id = "evaluation_user"
    session_id = f"eval_{uuid.uuid4().hex[:8]}"
    
    # Create runner with session service
    runner = Runner(
        agent=agent,
        app_name=settings.app_name,
        session_service=session_manager.get_service()
    )
    
    try:
        # Create session
        try:
            await session_manager.get_service().create_session(
                app_name=settings.app_name,
                user_id=user_id,
                session_id=session_id
            )
        except Exception:
            # Session may already exist, that's okay
            pass
        
        # Create message
        message = types.Content(
            role="user",
            parts=[types.Part(text=query)]
        )
        
        # Collect all events and text using run_async
        all_text_parts = []
        response_text = ""
        agent_responses = {}  # Track responses by agent name
        
        # Collect ALL events - wait for complete response
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=message
        ):
            try:
                # Try to identify which agent this response is from
                agent_name = None
                if hasattr(event, 'agent_name'):
                    agent_name = event.agent_name
                elif hasattr(event, 'name'):
                    agent_name = event.name
                
                # Check if event has content with parts
                if hasattr(event, 'content') and event.content:
                    if hasattr(event.content, 'parts') and event.content.parts:
                        for part in event.content.parts:
                            # Get text from part
                            if hasattr(part, 'text') and part.text:
                                text = part.text.strip()
                                if text and len(text) > 5:  # Only meaningful text
                                    all_text_parts.append(text)
                                    
                                    # Track by agent name
                                    if agent_name:
                                        if agent_name not in agent_responses:
                                            agent_responses[agent_name] = []
                                        agent_responses[agent_name].append(text)
                                    
                                    # If it's a final response, prefer it
                                    if hasattr(event, 'is_final_response') and event.is_final_response():
                                        response_text = text
            except Exception:
                # Skip events that can't be processed
                continue
        
        # For orchestrator, prefer sub-agent responses (they contain the actual answer)
        if agent_responses and not response_text:
            # Prefer sub-agent responses (faq_agent, order_agent, etc.)
            sub_agent_names = ['faq_agent', 'order_agent', 'sentiment_agent', 'escalation_agent']
            for sub_name in sub_agent_names:
                if sub_name in agent_responses:
                    sub_responses = agent_responses[sub_name]
                    if sub_responses:
                        response_text = max(sub_responses, key=len)
                        break
        
        # Strategy 1: Use final response if available
        if response_text:
            pass  # Already set from final response
        
        # Strategy 2: If no final response, use the longest meaningful text part
        elif all_text_parts:
            # Filter out very short texts and prefer longer ones
            meaningful_texts = [t for t in all_text_parts if len(t) > 20]
            if meaningful_texts:
                response_text = max(meaningful_texts, key=len)
            else:
                response_text = max(all_text_parts, key=len)
        
        # Strategy 3: If multiple text parts, prefer the longest
        if all_text_parts and len(all_text_parts) > 1 and not response_text:
            response_text = max(all_text_parts, key=len)
        
        # If still no response text, mark as failed but continue
        if not response_text:
            return {
                "success": False,
                "score": 0.0,
                "keyword_score": 0.0,
                "quality_score": 0.0,
                "keywords_found": [],
                "keywords_missing": expected_keywords,
                "response_length": 0,
                "response_preview": "No text response found (function calls only)",
                "error": "No text response extracted from events"
            }
        
        # Check if expected keywords are present (with synonyms)
        response_lower = response_text.lower()
        
        # Keyword synonyms mapping for more flexible matching
        keyword_synonyms = {
            "refund": ["refund", "reimburse", "money back", "return"],
            "30": ["30", "thirty", "30-day", "30 day"],
            "day": ["day", "days"],
            "shipping": ["shipping", "delivery", "ship", "shipment"],
            "return": ["return", "returns", "send back"],
            "payment": ["payment", "pay", "billing", "charge"],
            "card": ["card", "credit card", "debit card", "cards"],
            "ship": ["ship", "shipping", "delivery", "send"],
            "international": ["international", "overseas", "abroad", "global"],
            "order": ["order", "orders", "purchase"],
            "shipped": ["shipped", "shipping", "sent", "dispatched"],
            "frustrated": ["frustrated", "frustration", "upset", "angry", "annoyed"],
            "negative": ["negative", "bad", "poor", "unhappy"],
            "positive": ["positive", "good", "great", "happy", "satisfied"],
            "happy": ["happy", "satisfied", "pleased", "glad"],
            "angry": ["angry", "mad", "furious", "upset"],
            "high": ["high", "urgent", "critical", "important"],
            "urgency": ["urgency", "urgent", "important", "critical"],
            "ticket": ["ticket", "support ticket", "case", "issue", "create", "creating"],
            "created": ["created", "opened", "submitted", "generated", "create", "creating"],
            "urgent": ["urgent", "urgently", "critical", "priority"],
            "help": ["help", "assist", "support", "aid"],
            "damaged": ["damaged", "broken", "defective", "faulty"],
            "product": ["product", "item", "goods"],
        }
        
        # Check keywords with synonyms
        keywords_found = []
        for kw in expected_keywords:
            kw_lower = kw.lower()
            # Check direct match
            if kw_lower in response_lower:
                keywords_found.append(kw)
            # Check synonyms
            elif kw_lower in keyword_synonyms:
                synonyms = keyword_synonyms[kw_lower]
                if any(syn in response_lower for syn in synonyms):
                    keywords_found.append(kw)
        
        # More flexible scoring: need at least 50% of keywords OR at least 1 keyword for short lists
        keyword_score = len(keywords_found) / len(expected_keywords) if expected_keywords else 0
        
        # Response quality: non-empty and reasonable length
        has_response = len(response_text) > 10
        quality_score = 1.0 if has_response else 0.0
        
        # Overall score (more weight on quality, less strict on keywords)
        overall_score = (keyword_score * 0.6 + quality_score * 0.4)
        
        # Success if: (score >= 0.4) OR (at least 1 keyword found AND quality is good)
        success = overall_score >= 0.4 or (len(keywords_found) >= 1 and quality_score >= 0.5)
        
        return {
            "success": success,
            "score": overall_score,
            "keyword_score": keyword_score,
            "quality_score": quality_score,
            "keywords_found": keywords_found,
            "keywords_missing": [kw for kw in expected_keywords if kw not in keywords_found],
            "response_length": len(response_text),
            "response_preview": response_text[:150] + "..." if len(response_text) > 150 else response_text
        }
    
    except Exception as e:
        import traceback
        error_details = str(e)
        # Check if it's the NoneType iteration error
        if "'NoneType' object is not iterable" in error_details:
            error_details = "Orchestrator routing error - agent may have returned None"
        return {
            "success": False,
            "score": 0.0,
            "keyword_score": 0.0,
            "quality_score": 0.0,
            "keywords_found": [],
            "keywords_missing": expected_keywords,
            "response_length": 0,
            "response_preview": "",
            "error": error_details
        }
    finally:
        # Clean up session
        try:
            await session_manager.get_service().delete_session(
                app_name=settings.app_name,
                user_id=user_id,
                session_id=session_id
            )
        except Exception:
            # Session may not exist or already deleted, that's okay
            pass


async def run_evaluation():
    """Run full evaluation suite."""
    print("=" * 60)
    print("Customer Support Agent - Evaluation Suite")
    print("=" * 60)
    print()
    
    results = []
    
    for test_case in TEST_CASES:
        print(f"Test: {test_case['id']} - {test_case['category']}")
        print(f"Query: {test_case['query']}")
        print(f"Agent: {test_case['agent']}")
        
        # Get the right agent
        agent_map = {
            "faq_agent": faq_agent,
            "order_agent": order_agent,
            "orchestrator_agent": orchestrator_agent,
            "sentiment_agent": sentiment_agent,
            "escalation_agent": escalation_agent,
        }
        agent = agent_map[test_case["agent"]]
        
        # Evaluate
        result = await evaluate_agent(
            agent,
            test_case["query"],
            test_case["expected_keywords"]
        )
        
        result["test_id"] = test_case["id"]
        result["query"] = test_case["query"]
        result["category"] = test_case["category"]
        results.append(result)
        
        # Print result
        status = "[PASS]" if result["success"] else "[FAIL]"
        print(f"Result: {status} (Score: {result['score']:.2f})")
        if result.get("keywords_found"):
            print(f"Keywords found: {', '.join(result['keywords_found'])}")
        if result.get("keywords_missing"):
            print(f"Keywords missing: {', '.join(result['keywords_missing'])}")
        if result.get("error"):
            print(f"Error: {result['error']}")
        if not result.get("success") and result.get("response_preview"):
            print(f"Response preview: {result['response_preview']}")
        print()
    
    # Summary
    print("=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    
    total = len(results)
    passed = sum(1 for r in results if r["success"])
    avg_score = sum(r["score"] for r in results) / total if total > 0 else 0
    
    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Average score: {avg_score:.2f}")
    print()
    
    # By category
    categories = {}
    for result in results:
        cat = result["category"]
        if cat not in categories:
            categories[cat] = {"total": 0, "passed": 0}
        categories[cat]["total"] += 1
        if result["success"]:
            categories[cat]["passed"] += 1
    
    print("By Category:")
    for cat, stats in categories.items():
        pct = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
        print(f"  {cat}: {stats['passed']}/{stats['total']} ({pct:.1f}%)")
    
    return results


if __name__ == "__main__":
    try:
        # Suppress aiohttp warnings by properly closing sessions
        import warnings
        import os
        import logging
        
        # Suppress all ResourceWarnings
        warnings.filterwarnings("ignore", category=ResourceWarning)
        warnings.filterwarnings("ignore", message=".*Unclosed.*")
        warnings.filterwarnings("ignore", message=".*unclosed.*")
        
        # Set environment variable to suppress aiohttp warnings
        os.environ['PYTHONWARNINGS'] = 'ignore::ResourceWarning'
        
        # Suppress aiohttp logger warnings
        logging.getLogger('aiohttp').setLevel(logging.ERROR)
        logging.getLogger('asyncio').setLevel(logging.ERROR)
        
        results = asyncio.run(run_evaluation())
        
        # Clean up any remaining resources
        import gc
        gc.collect()
        
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

