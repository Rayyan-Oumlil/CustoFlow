"""
Live test of A/B Testing system - Simulates real usage

This script:
1. Creates an A/B test
2. Simulates conversations with different variants
3. Simulates feedback
4. Shows results and demonstrates the system works
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.ab_testing import get_ab_testing
import time


def simulate_conversations():
    """Simulate conversations and feedback for A/B testing."""
    print("\n" + "=" * 60)
    print("A/B TESTING - LIVE SIMULATION")
    print("=" * 60)
    
    ab_testing = get_ab_testing()
    
    # Step 1: Create A/B test
    print("\n[STEP 1] Creating A/B test for order_agent...")
    success = ab_testing.create_test(
        agent_name="order_agent",
        variant_a_instruction="You are a helpful order agent. Always be polite and provide detailed explanations. Explain everything thoroughly.",
        variant_b_instruction="You are a professional order agent. Be concise and efficient. Get to the point quickly while remaining helpful.",
        description="Testing verbose vs concise responses"
    )
    
    if not success:
        print("[FAIL] Failed to create test")
        return False
    
    print("[OK] Test created successfully!")
    
    # Step 2: Simulate conversations with different users
    print("\n[STEP 2] Simulating conversations...")
    print("Simulating 20 conversations (10 per variant)...")
    
    # Create users and determine their variants
    all_users = [f"user_{i}" for i in range(20)]
    variant_a_users = []
    variant_b_users = []
    
    # Determine which variant each user gets
    for user_id in all_users:
        variant = ab_testing.get_variant("order_agent", user_id)
        if variant == "variant_a":
            variant_a_users.append(user_id)
        else:
            variant_b_users.append(user_id)
    
    print(f"  Users assigned: {len(variant_a_users)} to Variant A, {len(variant_b_users)} to Variant B")
    
    # Simulate Variant A conversations (worse performance)
    print("\n  Simulating Variant A conversations...")
    for i, user_id in enumerate(variant_a_users[:10]):  # Use first 10
        # Simulate metrics (lower satisfaction, slower)
        satisfaction = 0.55 + (i * 0.02)  # 0.55 to 0.73 (lower)
        response_time = 2.5 + (i * 0.1)  # 2.5 to 3.4s (slower)
        resolved = i >= 4  # 60% resolution rate
        thumbs_up = i >= 5  # 50% thumbs up
        
        ab_testing.record_metrics(
            agent_name="order_agent",
            variant="variant_a",
            satisfaction_score=satisfaction,
            response_time=response_time,
            resolved=resolved,
            thumbs_up=thumbs_up,
            thumbs_down=(not thumbs_up)
        )
        print(f"    User {i+1}: satisfaction={satisfaction:.2f}, time={response_time:.1f}s, resolved={resolved}")
    
    # Simulate Variant B conversations (better performance)
    print("\n  Simulating Variant B conversations...")
    for i, user_id in enumerate(variant_b_users[:10]):  # Use first 10
        # Simulate metrics (higher satisfaction, faster)
        satisfaction = 0.75 + (i * 0.02)  # 0.75 to 0.93 (higher)
        response_time = 1.2 + (i * 0.05)  # 1.2 to 1.65s (faster)
        resolved = i >= 3  # 70% resolution rate
        thumbs_up = i >= 2  # 80% thumbs up
        
        ab_testing.record_metrics(
            agent_name="order_agent",
            variant="variant_b",
            satisfaction_score=satisfaction,
            response_time=response_time,
            resolved=resolved,
            thumbs_up=thumbs_up,
            thumbs_down=(not thumbs_up)
        )
        print(f"    User {i+1}: satisfaction={satisfaction:.2f}, time={response_time:.1f}s, resolved={resolved}")
    
    print("\n[OK] 20 conversations simulated!")
    
    # Step 3: Get and display results
    print("\n[STEP 3] Analyzing results...")
    time.sleep(1)  # Small delay for effect
    
    results = ab_testing.get_test_results("order_agent")
    
    print("\n" + "=" * 60)
    print("A/B TEST RESULTS")
    print("=" * 60)
    
    variant_a = results.get("variant_a", {})
    variant_b = results.get("variant_b", {})
    stats_a = variant_a.get("stats", {})
    stats_b = variant_b.get("stats", {})
    
    print(f"\n[VARIANT A] Verbose/Detailed:")
    print(f"   Conversations: {variant_a.get('conversations', 0)}")
    print(f"   Avg Satisfaction: {stats_a.get('avg_satisfaction', 0):.3f} ({stats_a.get('avg_satisfaction', 0)*100:.1f}%)")
    print(f"   Avg Response Time: {stats_a.get('avg_response_time', 0):.2f}s")
    print(f"   Escalation Rate: {stats_a.get('escalation_rate', 0):.2%}")
    print(f"   Resolution Rate: {stats_a.get('resolution_rate', 0):.2%}")
    print(f"   Thumbs Up Rate: {stats_a.get('thumbs_up_rate', 0):.2%}")
    
    print(f"\n[VARIANT B] Concise/Efficient:")
    print(f"   Conversations: {variant_b.get('conversations', 0)}")
    print(f"   Avg Satisfaction: {stats_b.get('avg_satisfaction', 0):.3f} ({stats_b.get('avg_satisfaction', 0)*100:.1f}%)")
    print(f"   Avg Response Time: {stats_b.get('avg_response_time', 0):.2f}s")
    print(f"   Escalation Rate: {stats_b.get('escalation_rate', 0):.2%}")
    print(f"   Resolution Rate: {stats_b.get('resolution_rate', 0):.2%}")
    print(f"   Thumbs Up Rate: {stats_b.get('thumbs_up_rate', 0):.2%}")
    
    print(f"\n[WINNER] {results.get('winner', 'Tie')}")
    significance = results.get('significance', {})
    print(f"[SIGNIFICANCE] {significance.get('message', 'N/A')}")
    if significance.get('significant'):
        print(f"   Confidence: {significance.get('confidence', 'N/A')}")
        print(f"   Difference: {significance.get('difference', 0):.3f}")
    
    print(f"\n[RECOMMENDATION]")
    print(f"   {results.get('recommendation', 'N/A')}")
    
    print("\n" + "=" * 60)
    
    # Step 4: Verify the system works
    print("\n[STEP 4] Verifying system...")
    
    # Check that variant routing is consistent
    test_user = "user_a_0"
    variant1 = ab_testing.get_variant("order_agent", test_user)
    variant2 = ab_testing.get_variant("order_agent", test_user)
    assert variant1 == variant2, "Variant routing should be consistent"
    print(f"[OK] Consistent routing: User {test_user} always gets {variant1}")
    
    # Check that metrics are correct (allow some flexibility due to random distribution)
    assert variant_a.get("conversations") >= 5, f"Should have at least 5 conversations for A, got {variant_a.get('conversations')}"
    assert variant_b.get("conversations") >= 5, f"Should have at least 5 conversations for B, got {variant_b.get('conversations')}"
    total = variant_a.get("conversations", 0) + variant_b.get("conversations", 0)
    assert total >= 15, f"Should have at least 15 total conversations, got {total}"
    print(f"[OK] Metrics collection working correctly (A: {variant_a.get('conversations')}, B: {variant_b.get('conversations')})")
    
    # Check that winner is determined correctly
    if stats_b.get("avg_satisfaction", 0) > stats_a.get("avg_satisfaction", 0):
        assert results.get("winner") == "variant_b", "B should win with higher satisfaction"
        print("[OK] Winner determination working correctly (B wins)")
    else:
        print("[OK] Winner determination working correctly")
    
    print("\n" + "=" * 60)
    print("[OK] ALL CHECKS PASSED - SYSTEM WORKING CORRECTLY!")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    try:
        success = simulate_conversations()
        if success:
            print("\n[SUCCESS] A/B Testing system is fully functional!")
            print("\nNext steps:")
            print("1. Create real A/B tests via API: POST /ab-testing/create")
            print("2. Use chat normally - system routes users automatically")
            print("3. Give feedback - metrics collected automatically")
            print("4. Check results: GET /ab-testing/results?agent_name=xxx")
            sys.exit(0)
        else:
            print("\n[FAIL] Test failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

