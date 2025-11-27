-- ============================================================================
-- Complete script to create the entire Supabase database
-- Run this script to create all tables with their constraints
-- ============================================================================

-- Drop existing tables (in reverse dependency order)
DROP TABLE IF EXISTS refunds CASCADE;
DROP TABLE IF EXISTS kb_updates_from_feedback CASCADE;
DROP TABLE IF EXISTS analytics_interactions CASCADE;
DROP TABLE IF EXISTS agent_refinements CASCADE;
DROP TABLE IF EXISTS feedback_insights CASCADE;
DROP TABLE IF EXISTS conversation_summaries CASCADE;
DROP TABLE IF EXISTS feedback CASCADE;
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS tickets CASCADE;
DROP TABLE IF EXISTS sessions CASCADE;
DROP TABLE IF EXISTS orders CASCADE;

-- ============================================================================
-- 1. SESSIONS table (must be created first as it's referenced by others)
-- ============================================================================

CREATE TABLE public.sessions (
    session_id character varying NOT NULL,
    user_id character varying NOT NULL,
    customer_id character varying,
    name character varying,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    message_count integer DEFAULT 0,
    CONSTRAINT sessions_pkey PRIMARY KEY (session_id)
);

-- ============================================================================
-- 2. ORDERS table (independent)
-- ============================================================================

CREATE TABLE public.orders (
    order_id character varying NOT NULL,
    customer_id character varying NOT NULL,
    status character varying NOT NULL,
    total numeric NOT NULL,
    items jsonb NOT NULL,
    notes jsonb DEFAULT '[]'::jsonb,
    tracking_number character varying,
    estimated_delivery date,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT orders_pkey PRIMARY KEY (order_id)
);

-- ============================================================================
-- 3. MESSAGES table (depends on sessions)
-- ============================================================================

CREATE TABLE public.messages (
    id integer NOT NULL DEFAULT nextval('messages_id_seq'::regclass),
    user_id character varying NOT NULL,
    session_id character varying NOT NULL,
    role character varying NOT NULL,
    content text NOT NULL,
    metadata jsonb,
    timestamp timestamp without time zone DEFAULT now(),
    CONSTRAINT messages_pkey PRIMARY KEY (id),
    CONSTRAINT messages_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.sessions(session_id)
);

-- Create sequence if it doesn't exist
CREATE SEQUENCE IF NOT EXISTS messages_id_seq;

-- ============================================================================
-- 4. TICKETS table (depends on sessions)
-- ============================================================================

CREATE TABLE public.tickets (
    ticket_id character varying NOT NULL,
    customer_id character varying,
    user_id character varying,
    session_id character varying,
    issue text NOT NULL,
    priority character varying DEFAULT 'normal'::character varying,
    status character varying DEFAULT 'open'::character varying,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT tickets_pkey PRIMARY KEY (ticket_id),
    CONSTRAINT tickets_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.sessions(session_id)
);

-- ============================================================================
-- 5. CONVERSATION_SUMMARIES table (depends on sessions)
-- ============================================================================

CREATE TABLE public.conversation_summaries (
    id bigint NOT NULL DEFAULT nextval('conversation_summaries_id_seq'::regclass),
    summary_key character varying NOT NULL UNIQUE,
    user_id character varying NOT NULL,
    session_id character varying NOT NULL,
    ticket_id character varying,
    summary text NOT NULL,
    key_points jsonb,
    sentiment jsonb,
    action_items jsonb,
    next_steps jsonb,
    summary_length character varying DEFAULT 'medium'::character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT conversation_summaries_pkey PRIMARY KEY (id),
    CONSTRAINT conversation_summaries_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.sessions(session_id)
);

-- Create sequence if it doesn't exist
CREATE SEQUENCE IF NOT EXISTS conversation_summaries_id_seq;

-- ============================================================================
-- 6. FEEDBACK table (depends on sessions)
-- ============================================================================

CREATE TABLE public.feedback (
    id bigint NOT NULL DEFAULT nextval('feedback_id_seq'::regclass),
    feedback_id character varying NOT NULL UNIQUE,
    session_id character varying,
    user_id character varying NOT NULL,
    ticket_id character varying,
    feedback_type character varying NOT NULL,
    rating integer CHECK (rating >= 1 AND rating <= 5),
    comment text,
    reason text,
    category character varying,
    agent_used character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT feedback_pkey PRIMARY KEY (id),
    CONSTRAINT feedback_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.sessions(session_id)
);

-- Create sequence if it doesn't exist
CREATE SEQUENCE IF NOT EXISTS feedback_id_seq;

-- ============================================================================
-- 7. FEEDBACK_INSIGHTS table (independent)
-- ============================================================================

CREATE TABLE public.feedback_insights (
    id bigint NOT NULL DEFAULT nextval('feedback_insights_id_seq'::regclass),
    insight_key character varying NOT NULL UNIQUE,
    insight_type character varying NOT NULL,
    data jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT feedback_insights_pkey PRIMARY KEY (id)
);

-- Create sequence if it doesn't exist
CREATE SEQUENCE IF NOT EXISTS feedback_insights_id_seq;

-- ============================================================================
-- 8. KB_UPDATES_FROM_FEEDBACK table (depends on feedback)
-- ============================================================================

CREATE TABLE public.kb_updates_from_feedback (
    id bigint NOT NULL DEFAULT nextval('kb_updates_from_feedback_id_seq'::regclass),
    update_id character varying NOT NULL UNIQUE,
    feedback_id character varying,
    update_type character varying NOT NULL,
    content jsonb NOT NULL,
    status character varying DEFAULT 'pending'::character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT kb_updates_from_feedback_pkey PRIMARY KEY (id),
    CONSTRAINT kb_updates_from_feedback_feedback_id_fkey FOREIGN KEY (feedback_id) REFERENCES public.feedback(feedback_id)
);

-- Create sequence if it doesn't exist
CREATE SEQUENCE IF NOT EXISTS kb_updates_from_feedback_id_seq;

-- ============================================================================
-- 9. ANALYTICS_INTERACTIONS table (for tracking user interactions)
-- ============================================================================

CREATE TABLE public.analytics_interactions (
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

-- Create sequence if it doesn't exist
CREATE SEQUENCE IF NOT EXISTS analytics_interactions_id_seq;

-- ============================================================================
-- 10. AGENT_REFINEMENTS table (independent)
-- ============================================================================

CREATE TABLE public.agent_refinements (
    id bigint NOT NULL DEFAULT nextval('agent_refinements_id_seq'::regclass),
    refinement_key character varying NOT NULL UNIQUE,
    agent_name character varying NOT NULL,
    refinement_type character varying NOT NULL,
    changes jsonb NOT NULL,
    feedback_sources jsonb,
    status character varying DEFAULT 'pending'::character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT agent_refinements_pkey PRIMARY KEY (id)
);

-- Create sequence if it doesn't exist
CREATE SEQUENCE IF NOT EXISTS agent_refinements_id_seq;

-- ============================================================================
-- 10. Create indexes to improve performance
-- ============================================================================

-- Indexes for sessions
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON public.sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON public.sessions(created_at);

-- Indexes for messages
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON public.messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_user_id ON public.messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON public.messages(timestamp);

-- Indexes for tickets
CREATE INDEX IF NOT EXISTS idx_tickets_session_id ON public.tickets(session_id);
CREATE INDEX IF NOT EXISTS idx_tickets_user_id ON public.tickets(user_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON public.tickets(status);

-- Indexes for orders
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON public.orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON public.orders(status);

-- Indexes for refunds
CREATE INDEX IF NOT EXISTS idx_refunds_order_id ON public.refunds(order_id);
CREATE INDEX IF NOT EXISTS idx_refunds_customer_id ON public.refunds(customer_id);
CREATE INDEX IF NOT EXISTS idx_refunds_status ON public.refunds(status);
CREATE INDEX IF NOT EXISTS idx_refunds_created_at ON public.refunds(created_at);

-- Indexes for conversation_summaries
CREATE INDEX IF NOT EXISTS idx_conversation_summaries_session_id ON public.conversation_summaries(session_id);
CREATE INDEX IF NOT EXISTS idx_conversation_summaries_user_id ON public.conversation_summaries(user_id);
CREATE INDEX IF NOT EXISTS idx_conversation_summaries_ticket_id ON public.conversation_summaries(ticket_id);

-- Indexes for feedback
CREATE INDEX IF NOT EXISTS idx_feedback_session_id ON public.feedback(session_id);
CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON public.feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_ticket_id ON public.feedback(ticket_id);
CREATE INDEX IF NOT EXISTS idx_feedback_type ON public.feedback(feedback_type);
CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON public.feedback(created_at);

-- Indexes for analytics_interactions
CREATE INDEX IF NOT EXISTS idx_analytics_interactions_user_id ON public.analytics_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_analytics_interactions_session_id ON public.analytics_interactions(session_id);
CREATE INDEX IF NOT EXISTS idx_analytics_interactions_timestamp ON public.analytics_interactions(timestamp);
CREATE INDEX IF NOT EXISTS idx_analytics_interactions_agent_used ON public.analytics_interactions(agent_used);

-- ============================================================================
-- Confirmation
-- ============================================================================

DO $$ 
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE '✅ Database created successfully!';
    RAISE NOTICE '📊 Tables created:';
    RAISE NOTICE '   - sessions';
    RAISE NOTICE '   - orders';
    RAISE NOTICE '   - messages';
    RAISE NOTICE '   - tickets';
    RAISE NOTICE '   - conversation_summaries';
    RAISE NOTICE '   - feedback';
    RAISE NOTICE '   - feedback_insights';
    RAISE NOTICE '   - kb_updates_from_feedback';
    RAISE NOTICE '   - analytics_interactions';
    RAISE NOTICE '   - agent_refinements';
    RAISE NOTICE '   - refunds';
    RAISE NOTICE '========================================';
END $$;

