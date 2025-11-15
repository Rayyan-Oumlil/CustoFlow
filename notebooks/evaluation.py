"""Evaluation script for customer support agents."""
import asyncio
import sys
import os
from typing import List, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.faq_agent import faq_agent
from agents.order_agent import order_agent
from agents.orchestrator_agent import orchestrator_agent
from google.adk.runners import InMemoryRunner


# ============================================================================
# Evaluation Test Cases
# ============================================================================
# Comprehensive test suite covering all agent types and routing scenarios
# Each test case includes:
# - id: Unique test identifier
# - query: Customer query to test
# - agent: Which agent should handle it
# - expected_keywords: Keywords that should appear in response
# - category: Test category for reporting
# ============================================================================
TEST_CASES = [
    # FAQ Agent Tests
    {
        "id": "faq_1",
        "query": "What is your refund policy?",
        "agent": "faq_agent",
        "expected_keywords": ["refund", "30", "day"],
        "category": "FAQ"
    },
    {
        "id": "faq_2",
        "query": "How long does shipping take?",
        "agent": "faq_agent",
        "expected_keywords": ["shipping", "day"],
        "category": "FAQ"
    },
    {
        "id": "faq_3",
        "query": "Can I return items?",
        "agent": "faq_agent",
        "expected_keywords": ["return", "30"],
        "category": "FAQ"
    },
    {
        "id": "faq_4",
        "query": "What are your payment methods?",
        "agent": "faq_agent",
        "expected_keywords": ["payment", "card"],
        "category": "FAQ"
    },
    {
        "id": "faq_5",
        "query": "Do you ship internationally?",
        "agent": "faq_agent",
        "expected_keywords": ["ship", "international"],
        "category": "FAQ"
    },
    # Order Agent Tests
    {
        "id": "order_1",
        "query": "What's the status of order 12345?",
        "agent": "order_agent",
        "expected_keywords": ["12345", "order", "shipped"],
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
        "expected_keywords": ["order", "frustrated"],
        "category": "Routing"
    },
    {
        "id": "orchestrator_4",
        "query": "I need help with a damaged product",
        "agent": "orchestrator_agent",
        "expected_keywords": ["help", "damaged", "product"],
        "category": "Routing"
    },
    {
        "id": "orchestrator_5",
        "query": "What's your return policy and where is order 12345?",
        "agent": "orchestrator_agent",
        "expected_keywords": ["return", "12345"],
        "category": "Routing"
    },
]


async def evaluate_agent(agent, query: str, expected_keywords: List[str]) -> Dict[str, Any]:
    """Evaluate a single agent query."""
    runner = InMemoryRunner(agent=agent)
    
    try:
        events = await runner.run_debug(query)
        
        # Extract response text
        response_text = ""
        for event in events:
            if event.is_final_response() and event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        response_text = part.text
                        break
                if response_text:
                    break
        
        # Check if expected keywords are present
        response_lower = response_text.lower()
        keywords_found = [kw for kw in expected_keywords if kw.lower() in response_lower]
        keyword_score = len(keywords_found) / len(expected_keywords) if expected_keywords else 0
        
        # Response quality: non-empty and reasonable length
        has_response = len(response_text) > 10
        quality_score = 1.0 if has_response else 0.0
        
        # Overall score
        overall_score = (keyword_score * 0.7 + quality_score * 0.3)
        
        return {
            "success": overall_score >= 0.5,
            "score": overall_score,
            "keyword_score": keyword_score,
            "quality_score": quality_score,
            "keywords_found": keywords_found,
            "response_length": len(response_text),
            "response_preview": response_text[:100] + "..." if len(response_text) > 100 else response_text
        }
    
    except Exception as e:
        return {
            "success": False,
            "score": 0.0,
            "error": str(e)
        }


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
        results = asyncio.run(run_evaluation())
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

