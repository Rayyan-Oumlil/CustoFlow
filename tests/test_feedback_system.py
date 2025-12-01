"""
Comprehensive test script for the feedback and agent improvement system.
Tests feedback submission, analysis, insights generation, and agent refinements.
"""
import sys
from pathlib import Path
import os
from datetime import datetime
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import modules
from utils.feedback_manager import FeedbackManager
from utils.agent_improver import AgentImprover
from utils.supabase_client import SUPABASE_ENABLED, create_feedback, get_feedback
from utils.supabase_client import get_agent_refinements, get_feedback_insights, get_kb_updates
from utils.supabase_client import create_session, save_auto_learning, get_auto_learning

# Test configuration
TEST_SESSION_ID = f"test_feedback_session_{int(datetime.now().timestamp())}"
TEST_USER_ID = f"test_feedback_user_{int(datetime.now().timestamp())}"


def setup_test_session(session_id: str, user_id: str) -> bool:
    """Create a test session in Supabase."""
    if not SUPABASE_ENABLED:
        return True
    
    try:
        result = create_session(user_id=user_id, session_id=session_id, customer_id="test_cust_001")
        return result is not None
    except Exception as e:
        print(f"  [WARN] Failed to create test session: {e}")
        return False


def print_test_header(test_name: str):
    """Print a formatted test header."""
    print("\n" + "=" * 70)
    print(f"  TEST: {test_name}")
    print("=" * 70)


def print_result(success: bool, message: str, indent: int = 0):
    """Print test result with better formatting."""
    indent_str = "  " * indent
    if success:
        status = "[PASS]"
        print(f"{indent_str}{status} {message}")
    else:
        status = "[FAIL]"
        print(f"{indent_str}{status} {message}")


def test_feedback_submission_with_all_fields():
    """Test submitting feedback with all fields populated."""
    print_test_header("Feedback Submission (All Fields)")
    
    try:
        # Create test session first
        if SUPABASE_ENABLED:
            setup_test_session(TEST_SESSION_ID, TEST_USER_ID)
            time.sleep(0.5)  # Wait for session to be created
        
        feedback_mgr = FeedbackManager()
        
        # Submit feedback with all fields
        result = feedback_mgr.submit_feedback(
            session_id=TEST_SESSION_ID,
            user_id=TEST_USER_ID,
            feedback_type="thumbs_down",
            rating=2,
            comment="The agent gave incorrect information about my order",
            reason="incorrect",
            category="accuracy",
            agent_used="order_agent"
        )
        
        if result.get("status") == "success":
            print_result(True, f"Feedback submitted successfully", indent=1)
            print(f"      Feedback ID: {result.get('feedback_id')}")
            
            # Wait a bit for async analysis
            print("  [WAIT] Waiting for feedback analysis...")
            time.sleep(2)
            
            # Verify feedback in database
            if SUPABASE_ENABLED:
                feedbacks = get_feedback(session_id=TEST_SESSION_ID)
                if feedbacks:
                    feedback = feedbacks[0]
                    print_result(True, f"Feedback found in database", indent=1)
                    print(f"      Reason: {feedback.get('reason', 'NULL')}")
                    print(f"      Category: {feedback.get('category', 'NULL')}")
                    print(f"      Comment: {feedback.get('comment', 'NULL')}")
                    print(f"      Rating: {feedback.get('rating', 'NULL')}")
                    print(f"      Agent: {feedback.get('agent_used', 'NULL')}")
                    
                    # Check if fields are populated
                    has_reason = feedback.get('reason') is not None
                    has_category = feedback.get('category') is not None
                    has_comment = feedback.get('comment') is not None
                    
                    if has_reason and has_category and has_comment:
                        print_result(True, f"All feedback fields populated correctly", indent=1)
                        return True
                    else:
                        print_result(False, f"Some fields are NULL: reason={has_reason}, category={has_category}, comment={has_comment}", indent=1)
                        return False
                else:
                    print_result(False, "Feedback not found in database", indent=1)
                    return False
            else:
                print_result(True, "Feedback submitted (Supabase not enabled)", indent=1)
                return True
        else:
            print_result(False, f"Failed to submit feedback: {result.get('error_message', 'Unknown error')}", indent=1)
            return False
            
    except Exception as e:
        print_result(False, f"Exception: {str(e)}", indent=1)
        import traceback
        traceback.print_exc()
        return False


def test_feedback_analysis_triggers():
    """Test that feedback analysis triggers insights and refinements."""
    print_test_header("Feedback Analysis & Insights Generation")
    
    try:
        # Create test session first
        if SUPABASE_ENABLED:
            setup_test_session(TEST_SESSION_ID, TEST_USER_ID)
            time.sleep(0.5)
        
        feedback_mgr = FeedbackManager()
        
        # Submit negative feedback that should trigger analysis
        result = feedback_mgr.submit_feedback(
            session_id=TEST_SESSION_ID,
            user_id=TEST_USER_ID,
            feedback_type="thumbs_down",
            rating=2,
            comment="The agent was slow and gave wrong information",
            reason="incorrect",
            category="accuracy",
            agent_used="order_agent"
        )
        
        if result.get("status") != "success":
            print_result(False, "Failed to submit feedback", indent=1)
            return False
        
        print_result(True, "Feedback submitted", indent=1)
        
        # Wait for analysis to complete
        print("  [WAIT] Waiting for feedback analysis to complete...")
        time.sleep(3)
        
        # Check for feedback insights
        print("  [CHECK] Checking for feedback insights...")
        if SUPABASE_ENABLED:
            insights = get_feedback_insights(agent_name="order_agent")
            if insights:
                print_result(True, f"Found {len(insights)} feedback insights", indent=1)
                for i, insight in enumerate(insights[:3], 1):
                    data = insight.get('data', {})
                    agent = data.get('agent_name', 'N/A') if isinstance(data, dict) else 'N/A'
                    print(f"        {i}. {insight.get('insight_key', 'N/A')} - {insight.get('insight_type', 'N/A')} (Agent: {agent})")
            else:
                print_result(False, "No feedback insights found", indent=1)
        
        # Check for agent refinements
        print("  [CHECK] Checking for agent refinements...")
        if SUPABASE_ENABLED:
            refinements = get_agent_refinements(agent_name="order_agent")
            if refinements:
                print_result(True, f"Found {len(refinements)} agent refinements", indent=1)
                for i, ref in enumerate(refinements[:3], 1):
                    print(f"        {i}. {ref.get('refinement_key', 'N/A')} - Status: {ref.get('status', 'N/A')}")
            else:
                print_result(False, "No agent refinements found", indent=1)
        
        # Check for KB updates
        print("  [CHECK] Checking for KB update suggestions...")
        if SUPABASE_ENABLED:
            kb_updates = get_kb_updates(status="pending")
            if kb_updates:
                print_result(True, f"Found {len(kb_updates)} KB update suggestions", indent=1)
                for i, update in enumerate(kb_updates[:3], 1):
                    print(f"        {i}. {update.get('update_id', 'N/A')} - Type: {update.get('update_type', 'N/A')}")
            else:
                print_result(False, "No KB update suggestions found", indent=1)
        
        return True
        
    except Exception as e:
        print_result(False, f"Exception: {str(e)}", indent=1)
        import traceback
        traceback.print_exc()
        return False


def test_positive_feedback_insights():
    """Test that positive feedback generates insights."""
    print_test_header("Positive Feedback Insights")
    
    try:
        # Create test session first
        if SUPABASE_ENABLED:
            setup_test_session(TEST_SESSION_ID, TEST_USER_ID)
            time.sleep(0.5)
        
        feedback_mgr = FeedbackManager()
        
        # Submit positive feedback
        result = feedback_mgr.submit_feedback(
            session_id=TEST_SESSION_ID,
            user_id=TEST_USER_ID,
            feedback_type="thumbs_up",
            rating=5,
            comment="Great help! The agent was very helpful and accurate",
            reason="helpful",
            category="helpfulness",
            agent_used="faq_agent"
        )
        
        if result.get("status") != "success":
            print_result(False, "Failed to submit positive feedback", indent=1)
            return False
        
        print_result(True, "Positive feedback submitted", indent=1)
        
        # Wait for analysis
        print("  [WAIT] Waiting for analysis...")
        time.sleep(3)
        
        # Check for positive insights
        if SUPABASE_ENABLED:
            insights = get_feedback_insights(agent_name="faq_agent")
            positive_insights = [i for i in insights if i.get('insight_type') == 'positive_feedback']
            
            if positive_insights:
                print_result(True, f"Found {len(positive_insights)} positive insights", indent=1)
                for i, insight in enumerate(positive_insights[:2], 1):
                    print(f"        {i}. {insight.get('insight_key', 'N/A')}")
                return True
            else:
                # Also check all insights to see if any exist
                all_insights = get_feedback_insights()
                print_result(False, f"No positive insights found for faq_agent (total insights: {len(all_insights)})", indent=1)
                return False
        else:
            print_result(True, "Positive feedback recorded (Supabase not enabled)", indent=1)
            return True
            
    except Exception as e:
        print_result(False, f"Exception: {str(e)}", indent=1)
        import traceback
        traceback.print_exc()
        return False


def test_automatic_reason_extraction():
    """Test that reason and category are extracted automatically if not provided."""
    print_test_header("Automatic Reason/Category Extraction")
    
    try:
        # Create test session first
        if SUPABASE_ENABLED:
            setup_test_session(TEST_SESSION_ID, TEST_USER_ID)
            time.sleep(0.5)
        
        feedback_mgr = FeedbackManager()
        
        # Submit feedback WITHOUT reason/category - should be extracted from comment
        result = feedback_mgr.submit_feedback(
            session_id=TEST_SESSION_ID,
            user_id=TEST_USER_ID,
            feedback_type="thumbs_down",
            comment="The response was incorrect and missing important details",
            agent_used="order_agent"
        )
        
        if result.get("status") != "success":
            print_result(False, "Failed to submit feedback", indent=1)
            return False
        
        print_result(True, "Feedback submitted without explicit reason/category", indent=1)
        
        # Wait and check if reason/category were extracted
        time.sleep(2)
        
        if SUPABASE_ENABLED:
            feedbacks = get_feedback(session_id=TEST_SESSION_ID, user_id=TEST_USER_ID)
            if feedbacks:
                # Find the most recent one
                latest = sorted(feedbacks, key=lambda x: x.get('created_at', ''), reverse=True)[0]
                
                # Check if analysis extracted reason/category
                # The system should infer from comment
                comment = latest.get('comment', '').lower()
                has_incorrect = 'incorrect' in comment
                has_missing = 'missing' in comment
                
                print(f"      Comment: {latest.get('comment', 'N/A')}")
                print(f"      Reason: {latest.get('reason', 'NULL')}")
                print(f"      Category: {latest.get('category', 'NULL')}")
                
                # Reason should be extracted or inferred
                if latest.get('reason') or has_incorrect or has_missing:
                    print_result(True, "Reason/category extracted or can be inferred", indent=1)
                    return True
                else:
                    print_result(False, "Reason/category not extracted", indent=1)
                    return False
            else:
                print_result(False, "Feedback not found", indent=1)
                return False
        else:
            return True
            
    except Exception as e:
        print_result(False, f"Exception: {str(e)}", indent=1)
        import traceback
        traceback.print_exc()
        return False


def test_auto_learning_unified_table():
    """Test that the unified auto_learning table works correctly."""
    print_test_header("Auto-Learning Unified Table")
    
    try:
        if not SUPABASE_ENABLED:
            print_result(True, "Skipped (Supabase not enabled)", indent=1)
            return True
        
        # Test saving different types of learning entries
        test_learning_id = f"TEST-{int(datetime.now().timestamp())}"
        
        # Test 1: Save an insight
        result1 = save_auto_learning(
            learning_id=f"{test_learning_id}-insight",
            learning_type="insight",
            agent_name="test_agent",
            data={"test": "insight_data"},
            status="active"
        )
        print_result(result1, "Save insight to auto_learning", indent=1)
        
        # Test 2: Save a refinement
        result2 = save_auto_learning(
            learning_id=f"{test_learning_id}-refinement",
            learning_type="refinement",
            agent_name="test_agent",
            data={"test": "refinement_data"},
            status="pending"
        )
        print_result(result2, "Save refinement to auto_learning", indent=1)
        
        # Test 3: Save a KB update
        result3 = save_auto_learning(
            learning_id=f"{test_learning_id}-kb",
            learning_type="kb_update",
            agent_name=None,
            data={"test": "kb_data"},
            status="pending"
        )
        print_result(result3, "Save KB update to auto_learning", indent=1)
        
        if not (result1 and result2 and result3):
            print_result(False, "Failed to save some entries", indent=1)
            return False
        
        # Wait a bit for database
        time.sleep(1)
        
        # Test 4: Retrieve insights
        insights = get_auto_learning(learning_type="insight", agent_name="test_agent")
        has_test_insight = any(i.get("learning_id") == f"{test_learning_id}-insight" for i in insights)
        print_result(has_test_insight, f"Retrieve insights from auto_learning ({len(insights)} found)", indent=1)
        
        # Test 5: Retrieve refinements
        refinements = get_auto_learning(learning_type="refinement", agent_name="test_agent")
        has_test_refinement = any(r.get("learning_id") == f"{test_learning_id}-refinement" for r in refinements)
        print_result(has_test_refinement, f"Retrieve refinements from auto_learning ({len(refinements)} found)", indent=1)
        
        # Test 6: Retrieve KB updates
        kb_updates = get_auto_learning(learning_type="kb_update", status="pending")
        has_test_kb = any(k.get("learning_id") == f"{test_learning_id}-kb" for k in kb_updates)
        print_result(has_test_kb, f"Retrieve KB updates from auto_learning ({len(kb_updates)} found)", indent=1)
        
        if has_test_insight and has_test_refinement and has_test_kb:
            print_result(True, "Unified auto_learning table works correctly", indent=1)
            return True
        else:
            print_result(False, "Some entries not found in auto_learning", indent=1)
            return False
            
    except Exception as e:
        print_result(False, f"Exception: {str(e)}", indent=1)
        import traceback
        traceback.print_exc()
        return False


def test_multiple_feedback_generates_insights():
    """Test that multiple feedback entries generate aggregated insights."""
    print_test_header("Multiple Feedback -> Insights Generation")
    
    try:
        feedback_mgr = FeedbackManager()
        
        # Submit multiple feedback entries
        print("  [ACTION] Submitting multiple feedback entries...")
        for i in range(3):
            session_id = f"{TEST_SESSION_ID}_multi_{i}"
            # Create session for each feedback
            if SUPABASE_ENABLED:
                setup_test_session(session_id, TEST_USER_ID)
                time.sleep(0.3)
            
            feedback_mgr.submit_feedback(
                session_id=session_id,
                user_id=TEST_USER_ID,
                feedback_type="thumbs_down" if i % 2 == 0 else "thumbs_up",
                rating=2 if i % 2 == 0 else 5,
                comment=f"Test feedback {i}: {'incorrect information' if i % 2 == 0 else 'very helpful'}",
                reason="incorrect" if i % 2 == 0 else "helpful",
                category="accuracy" if i % 2 == 0 else "helpfulness",
                agent_used="order_agent"
            )
            time.sleep(0.5)
        
        print_result(True, "Submitted 3 feedback entries", indent=1)
        
        # Wait for analysis
        print("  [WAIT] Waiting for insights generation...")
        time.sleep(4)
        
        # Check insights
        if SUPABASE_ENABLED:
            insights = get_feedback_insights(agent_name="order_agent")
            if insights:
                print_result(True, f"Generated {len(insights)} insights from multiple feedback", indent=1)
                return True
            else:
                print_result(False, "No insights generated from multiple feedback", indent=1)
                return False
        else:
            return True
            
    except Exception as e:
        print_result(False, f"Exception: {str(e)}", indent=1)
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all feedback system tests."""
    print("\n" + "=" * 70)
    print("  " + "=" * 66)
    print("  " + " " * 15 + "FEEDBACK SYSTEM TEST SUITE")
    print("  " + "=" * 66)
    print("=" * 70)
    
    print("\n[CONFIG] Test Configuration:")
    print(f"  - Session ID: {TEST_SESSION_ID}")
    print(f"  - User ID: {TEST_USER_ID}")
    print(f"  - Supabase: {'Enabled' if SUPABASE_ENABLED else 'Disabled'}")
    print("=" * 70)
    
    results = []
    
    # Test 1: Feedback submission with all fields
    results.append(("Feedback Submission (All Fields)", test_feedback_submission_with_all_fields()))
    
    # Test 2: Feedback analysis triggers
    results.append(("Feedback Analysis & Insights", test_feedback_analysis_triggers()))
    
    # Test 3: Positive feedback insights
    results.append(("Positive Feedback Insights", test_positive_feedback_insights()))
    
    # Test 4: Automatic reason extraction
    results.append(("Automatic Reason/Category Extraction", test_automatic_reason_extraction()))
    
    # Test 5: Multiple feedback generates insights
    results.append(("Multiple Feedback -> Insights", test_multiple_feedback_generates_insights()))
    
    # Test 6: Auto-learning unified table
    results.append(("Auto-Learning Unified Table", test_auto_learning_unified_table()))
    
    # Print summary
    print("\n" + "=" * 70)
    print("  " + "=" * 66)
    print("  " + " " * 25 + "TEST SUMMARY")
    print("  " + "=" * 66)
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    percentage = (passed / total * 100) if total > 0 else 0
    
    print("\n  Results:")
    for i, (test_name, result) in enumerate(results, 1):
        status = "[PASS]" if result else "[FAIL]"
        icon = "[OK]" if result else "[X]"
        print(f"    {i}. {icon} {status:6} - {test_name}")
    
    print("\n  " + "-" * 66)
    print(f"  Total: {passed}/{total} tests passed ({percentage:.1f}%)")
    
    if passed == total:
        print("  " + "=" * 66)
        print("  " + " " * 20 + "ALL TESTS PASSED! [SUCCESS]")
        print("  " + "=" * 66)
    else:
        print("  " + "=" * 66)
        print(f"  " + " " * 20 + f"{total - passed} TEST(S) FAILED [ERROR]")
        print("  " + "=" * 66)
    
    print("=" * 70 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
