-- Script to clean the database and start fresh
-- KEEPS ONLY ORDERS
-- ⚠️ WARNING: This script deletes ALL data except orders

-- ============================================================================
-- 1. Delete all data from tables (keep the tables)
-- ============================================================================

-- Delete conversation summaries
TRUNCATE TABLE conversation_summaries CASCADE;

-- Delete KB updates (depends on feedback)
TRUNCATE TABLE kb_updates_from_feedback CASCADE;

-- Delete agent refinements
TRUNCATE TABLE agent_refinements CASCADE;

-- Delete feedback insights
TRUNCATE TABLE feedback_insights CASCADE;

-- Delete feedbacks
TRUNCATE TABLE feedback CASCADE;

-- Delete tickets
TRUNCATE TABLE tickets CASCADE;

-- Delete messages
TRUNCATE TABLE messages CASCADE;

-- Delete sessions
TRUNCATE TABLE sessions CASCADE;

-- ⚠️ DO NOT DELETE ORDERS - We keep orders

-- ============================================================================
-- 2. Reset sequences (so IDs start from 1)
-- ============================================================================

-- Reset sequences for tables with BIGSERIAL id
ALTER SEQUENCE conversation_summaries_id_seq RESTART WITH 1;
ALTER SEQUENCE feedback_id_seq RESTART WITH 1;
ALTER SEQUENCE feedback_insights_id_seq RESTART WITH 1;
ALTER SEQUENCE kb_updates_from_feedback_id_seq RESTART WITH 1;
ALTER SEQUENCE agent_refinements_id_seq RESTART WITH 1;

-- ============================================================================
-- 3. Verification
-- ============================================================================

-- Display the number of records in each table
SELECT 
    'sessions' as table_name, 
    COUNT(*) as count 
FROM sessions
UNION ALL
SELECT 
    'messages' as table_name, 
    COUNT(*) as count 
FROM messages
UNION ALL
SELECT 
    'tickets' as table_name, 
    COUNT(*) as count 
FROM tickets
UNION ALL
SELECT 
    'conversation_summaries' as table_name, 
    COUNT(*) as count 
FROM conversation_summaries
UNION ALL
SELECT 
    'feedback' as table_name, 
    COUNT(*) as count 
FROM feedback
UNION ALL
SELECT 
    'orders' as table_name, 
    COUNT(*) as count 
FROM orders
ORDER BY table_name;

-- Confirmation message
DO $$ 
BEGIN
    RAISE NOTICE '✅ Database cleaned successfully!';
    RAISE NOTICE '📦 Orders have been preserved.';
    RAISE NOTICE '🔄 All other data has been deleted.';
END $$;
