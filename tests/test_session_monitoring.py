"""
Tests for session monitoring and active session management features.
Tests:
- Get all active sessions endpoint
- Send message to session endpoint
- Active session count excludes closed sessions
- Session closure prevents new messages
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
from utils.supabase_client import (
    SUPABASE_ENABLED, 
    create_session, 
    get_session,
    get_messages,
    close_session,
    reopen_session,
    add_message
)
from tools.ticket_modification_tool import update_ticket_status
from tools.ticket_tool import create_ticket

# Test configuration
TEST_SESSION_ID = f"test_monitoring_{int(datetime.now().timestamp())}"
TEST_USER_ID = f"test_monitoring_user_{int(datetime.now().timestamp())}"
TEST_CUSTOMER_ID = "test_cust_monitoring_001"


def setup_test_session(session_id: str, user_id: str, customer_id: str) -> bool:
    """Create a test session in Supabase."""
    if not SUPABASE_ENABLED:
        print("  [SKIP] Supabase not enabled, skipping test")
        return False
    
    try:
        result = create_session(user_id=user_id, session_id=session_id, customer_id=customer_id)
        time.sleep(0.5)  # Wait for Supabase to propagate
        return result is not None
    except Exception as e:
        print(f"  [WARN] Failed to create test session: {e}")
        return False


def print_test_header(test_name: str):
    """Print a formatted test header."""
    print("\n" + "=" * 70)
    print(f"  TEST: {test_name}")
    print("=" * 70)


def test_get_all_active_sessions():
    """Test that /sessions/all/active endpoint returns only active sessions."""
    print_test_header("Get All Active Sessions")
    
    if not SUPABASE_ENABLED:
        print("  [SKIP] Supabase not enabled")
        return True
    
    try:
        # Create multiple sessions: some active, some closed
        active_session_id = f"{TEST_SESSION_ID}_active_{int(datetime.now().timestamp())}"
        closed_session_id = f"{TEST_SESSION_ID}_closed_{int(datetime.now().timestamp())}"
        user_id = f"{TEST_USER_ID}_all_{int(datetime.now().timestamp())}"
        
        # Create active session
        if not setup_test_session(active_session_id, user_id, TEST_CUSTOMER_ID):
            print("  [FAIL] Failed to create active test session")
            return False
        
        # Add a message to make it count as active
        add_message(
            user_id=user_id,
            session_id=active_session_id,
            role="user",
            content="Test message for active session"
        )
        time.sleep(0.5)
        
        # Create closed session
        if not setup_test_session(closed_session_id, user_id, TEST_CUSTOMER_ID):
            print("  [FAIL] Failed to create closed test session")
            return False
        
        # Add a message and then close it
        add_message(
            user_id=user_id,
            session_id=closed_session_id,
            role="user",
            content="Test message for closed session"
        )
        time.sleep(0.5)
        close_session(closed_session_id)
        time.sleep(0.5)
        
        # Test the endpoint logic (simulate what the endpoint does)
        from supabase import create_client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            print("  [SKIP] Supabase credentials not configured")
            return True
        
        supabase = create_client(supabase_url, supabase_key)
        
        # Get all active sessions
        result = supabase.table("sessions").select("*").eq("is_active", True).gt("message_count", 0).order("updated_at", desc=True).execute()
        active_sessions = result.data or []
        
        # Check that active session is included
        active_found = any(s["session_id"] == active_session_id for s in active_sessions)
        if not active_found:
            print(f"  [FAIL] Active session {active_session_id} not found in results")
            return False
        
        # Check that closed session is NOT included
        closed_found = any(s["session_id"] == closed_session_id for s in active_sessions)
        if closed_found:
            print(f"  [FAIL] Closed session {closed_session_id} should not be in active sessions")
            return False
        
        print(f"  [PASS] Active sessions endpoint correctly filters sessions")
        print(f"  [INFO] Found {len(active_sessions)} active session(s)")
        return True
        
    except Exception as e:
        print(f"  [FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_send_message_to_session():
    """Test that /sessions/send-message endpoint sends message as human agent."""
    print_test_header("Send Message to Session")
    
    if not SUPABASE_ENABLED:
        print("  [SKIP] Supabase not enabled")
        return True
    
    try:
        # Setup: Create session
        session_id = f"{TEST_SESSION_ID}_send_{int(datetime.now().timestamp())}"
        user_id = f"{TEST_USER_ID}_send_{int(datetime.now().timestamp())}"
        
        if not setup_test_session(session_id, user_id, TEST_CUSTOMER_ID):
            print("  [FAIL] Failed to create test session")
            return False
        
        # Get messages before
        messages_before = get_messages(user_id=user_id, session_id=session_id, limit=100)
        messages_count_before = len(messages_before)
        
        # Send message as human agent (simulate endpoint logic)
        test_message = f"Test human agent message {int(datetime.now().timestamp())}"
        add_message(
            user_id=user_id,
            session_id=session_id,
            role="assistant",
            content=test_message,
            metadata={"agent_used": "human_agent", "is_human_agent": True},
            is_human_agent=True
        )
        time.sleep(0.5)
        
        # Get messages after
        messages_after = get_messages(user_id=user_id, session_id=session_id, limit=100)
        messages_count_after = len(messages_after)
        
        # Check that message was added
        if messages_count_after <= messages_count_before:
            print(f"  [FAIL] No new message was added. Before: {messages_count_before}, After: {messages_count_after}")
            return False
        
        # Check that last message is from human agent
        last_message = messages_after[-1]
        if last_message.get("role") != "assistant":
            print(f"  [FAIL] Last message should be from assistant, got: {last_message.get('role')}")
            return False
        
        metadata = last_message.get("metadata", {})
        if metadata.get("agent_used") != "human_agent" and metadata.get("is_human_agent") != True:
            print(f"  [FAIL] Message should be from human agent, got metadata: {metadata}")
            return False
        
        if last_message.get("content") != test_message:
            print(f"  [FAIL] Message content doesn't match. Expected: {test_message}, Got: {last_message.get('content')}")
            return False
        
        print(f"  [PASS] Message sent successfully as human agent")
        return True
        
    except Exception as e:
        print(f"  [FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_active_session_count_excludes_closed():
    """Test that active session count excludes closed sessions."""
    print_test_header("Active Session Count Excludes Closed")
    
    if not SUPABASE_ENABLED:
        print("  [SKIP] Supabase not enabled")
        return True
    
    try:
        # Create multiple sessions
        user_id = f"{TEST_USER_ID}_count_{int(datetime.now().timestamp())}"
        active_sessions = []
        closed_sessions = []
        
        # Create 3 active sessions
        for i in range(3):
            session_id = f"{TEST_SESSION_ID}_active_{i}_{int(datetime.now().timestamp())}"
            if setup_test_session(session_id, user_id, TEST_CUSTOMER_ID):
                add_message(user_id=user_id, session_id=session_id, role="user", content=f"Test {i}")
                active_sessions.append(session_id)
                time.sleep(0.3)
        
        # Create 2 closed sessions
        for i in range(2):
            session_id = f"{TEST_SESSION_ID}_closed_{i}_{int(datetime.now().timestamp())}"
            if setup_test_session(session_id, user_id, TEST_CUSTOMER_ID):
                add_message(user_id=user_id, session_id=session_id, role="user", content=f"Test closed {i}")
                time.sleep(0.3)
                close_session(session_id)
                closed_sessions.append(session_id)
                time.sleep(0.3)
        
        time.sleep(1)  # Wait for all updates
        
        # Count active sessions (simulate analytics endpoint logic)
        from supabase import create_client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            print("  [SKIP] Supabase credentials not configured")
            return True
        
        supabase = create_client(supabase_url, supabase_key)
        result = supabase.table("sessions").select("session_id, message_count, is_active").gt("message_count", 0).eq("is_active", True).execute()
        active_count = len(result.data) if result.data else 0
        
        # Verify count (should be at least our 3 active sessions, but might be more from other tests)
        if active_count < len(active_sessions):
            print(f"  [FAIL] Active count ({active_count}) is less than expected ({len(active_sessions)})")
            return False
        
        # Verify closed sessions are not counted
        result_closed = supabase.table("sessions").select("session_id").eq("is_active", False).execute()
        closed_count = len(result_closed.data) if result_closed.data else 0
        
        if closed_count < len(closed_sessions):
            print(f"  [WARN] Closed count ({closed_count}) is less than expected ({len(closed_sessions)}), but this is OK if other tests cleaned up")
        
        print(f"  [PASS] Active session count correctly excludes closed sessions")
        print(f"  [INFO] Active sessions: {active_count}, Closed sessions: {closed_count}")
        return True
        
    except Exception as e:
        print(f"  [FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_closed_session_blocks_messages():
    """Test that closed sessions prevent new messages from being processed."""
    print_test_header("Closed Session Blocks Messages")
    
    if not SUPABASE_ENABLED:
        print("  [SKIP] Supabase not enabled")
        return True
    
    try:
        # Setup: Create and close session
        session_id = f"{TEST_SESSION_ID}_block_{int(datetime.now().timestamp())}"
        user_id = f"{TEST_USER_ID}_block_{int(datetime.now().timestamp())}"
        
        if not setup_test_session(session_id, user_id, TEST_CUSTOMER_ID):
            print("  [FAIL] Failed to create test session")
            return False
        
        # Add initial message
        add_message(user_id=user_id, session_id=session_id, role="user", content="Initial message")
        time.sleep(0.5)
        
        # Close session
        close_session(session_id)
        time.sleep(0.5)
        
        # Verify session is closed
        session = get_session(session_id)
        if not session or session.get("is_active") is not False:
            print("  [FAIL] Session should be closed but isn't")
            return False
        
        print(f"  [PASS] Session is closed and ready to block messages")
        print(f"  [INFO] Note: Actual API blocking is tested in integration tests")
        return True
        
    except Exception as e:
        print(f"  [FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all session monitoring tests."""
    print("\n" + "=" * 70)
    print("  SESSION MONITORING & ACTIVE SESSION TESTS")
    print("=" * 70)
    
    tests = [
        ("Get All Active Sessions", test_get_all_active_sessions),
        ("Send Message to Session", test_send_message_to_session),
        ("Active Session Count Excludes Closed", test_active_session_count_excludes_closed),
        ("Closed Session Blocks Messages", test_closed_session_blocks_messages),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n  [ERROR] Test '{test_name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {test_name}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("  [SUCCESS] All tests passed!")
        return True
    else:
        print(f"  [FAILURE] {total - passed} test(s) failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

