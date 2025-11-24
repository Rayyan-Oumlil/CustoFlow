-- ============================================================================
-- Add analytics_interactions table to existing Supabase database
-- Run this script if you already have the database and just need to add analytics
-- ============================================================================

-- Create sequence if it doesn't exist
CREATE SEQUENCE IF NOT EXISTS analytics_interactions_id_seq;

-- Create analytics_interactions table
CREATE TABLE IF NOT EXISTS public.analytics_interactions (
    id bigint NOT NULL DEFAULT nextval('analytics_interactions_id_seq'::regclass),
    user_id character varying NOT NULL,
    session_id character varying,
    query text,
    response_length integer,
    agent_used character varying,
    response_time double precision,
    timestamp timestamp with time zone DEFAULT now(),
    CONSTRAINT analytics_interactions_pkey PRIMARY KEY (id),
    CONSTRAINT analytics_interactions_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.sessions(session_id)
);

-- Create indexes to improve performance
CREATE INDEX IF NOT EXISTS idx_analytics_interactions_user_id ON public.analytics_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_analytics_interactions_session_id ON public.analytics_interactions(session_id);
CREATE INDEX IF NOT EXISTS idx_analytics_interactions_timestamp ON public.analytics_interactions(timestamp);
CREATE INDEX IF NOT EXISTS idx_analytics_interactions_agent_used ON public.analytics_interactions(agent_used);

-- Confirmation
DO $$ 
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE '✅ analytics_interactions table created!';
    RAISE NOTICE '========================================';
END $$;

