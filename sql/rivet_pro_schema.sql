-- ═══════════════════════════════════════════════════════════════════════════
-- RIVET Pro - User Management & Usage Tracking Schema
-- Deploy to Neon PostgreSQL
-- ═══════════════════════════════════════════════════════════════════════════

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ───────────────────────────────────────────────────────────────────────────
-- USERS TABLE - Core user management with Stripe integration
-- ───────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS rivet_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Telegram identity
    telegram_id BIGINT UNIQUE NOT NULL,
    telegram_username VARCHAR(100),
    telegram_first_name VARCHAR(100),
    telegram_last_name VARCHAR(100),
    
    -- Subscription status
    is_pro BOOLEAN DEFAULT FALSE,
    tier VARCHAR(20) DEFAULT 'free', -- free, pro, team
    
    -- Stripe integration
    stripe_customer_id VARCHAR(100),
    stripe_subscription_id VARCHAR(100),
    stripe_price_id VARCHAR(100),
    subscription_status VARCHAR(20) DEFAULT 'none', -- none, active, cancelled, past_due, trialing
    subscription_started_at TIMESTAMP,
    subscription_ends_at TIMESTAMP,
    
    -- Usage tracking
    lookup_count INTEGER DEFAULT 0,
    lookup_reset_at TIMESTAMP DEFAULT NOW(),
    total_lookups_all_time INTEGER DEFAULT 0,
    
    -- Chat with Print usage
    print_sessions_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_active_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rivet_users_telegram ON rivet_users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_rivet_users_stripe ON rivet_users(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_rivet_users_tier ON rivet_users(tier);

-- ───────────────────────────────────────────────────────────────────────────
-- USAGE LOG - Every action for analytics
-- ───────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS rivet_usage_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES rivet_users(id),
    telegram_id BIGINT NOT NULL,
    
    -- Action details
    action_type VARCHAR(50) NOT NULL, -- photo_lookup, chat_print, manual_search, command
    action_subtype VARCHAR(50), -- ocr, search, answer, etc.
    
    -- Request/Response
    request_data JSONB,
    response_summary TEXT,
    
    -- Performance
    tokens_used INTEGER,
    latency_ms INTEGER,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    
    -- Context
    workflow_id VARCHAR(100),
    session_id UUID,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rivet_usage_user ON rivet_usage_log(user_id);
CREATE INDEX IF NOT EXISTS idx_rivet_usage_telegram ON rivet_usage_log(telegram_id);
CREATE INDEX IF NOT EXISTS idx_rivet_usage_date ON rivet_usage_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_rivet_usage_type ON rivet_usage_log(action_type);

-- ───────────────────────────────────────────────────────────────────────────
-- PRINT SESSIONS - Chat with Print-it feature
-- ───────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS rivet_print_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES rivet_users(id),
    telegram_id BIGINT NOT NULL,
    
    -- Document info
    pdf_file_id VARCHAR(200), -- Telegram file_id
    pdf_name VARCHAR(255),
    pdf_size_bytes INTEGER,
    pdf_base64 TEXT, -- Stored for Claude API calls
    pdf_page_count INTEGER,
    
    -- Session state
    conversation_history JSONB DEFAULT '[]'::jsonb,
    message_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Analytics
    questions_asked INTEGER DEFAULT 0,
    tokens_used_total INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    last_message_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_rivet_print_sessions_user ON rivet_print_sessions(telegram_id, is_active);
CREATE INDEX IF NOT EXISTS idx_rivet_print_sessions_active ON rivet_print_sessions(is_active) WHERE is_active = TRUE;

-- ───────────────────────────────────────────────────────────────────────────
-- STRIPE EVENTS - Webhook event log for debugging
-- ───────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS rivet_stripe_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stripe_event_id VARCHAR(100) UNIQUE NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    customer_id VARCHAR(100),
    subscription_id VARCHAR(100),
    payload JSONB,
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rivet_stripe_events_type ON rivet_stripe_events(event_type);
CREATE INDEX IF NOT EXISTS idx_rivet_stripe_events_customer ON rivet_stripe_events(customer_id);

-- ═══════════════════════════════════════════════════════════════════════════
-- FUNCTIONS
-- ═══════════════════════════════════════════════════════════════════════════

-- ───────────────────────────────────────────────────────────────────────────
-- Get or create user by Telegram ID
-- ───────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION get_or_create_user(
    p_telegram_id BIGINT,
    p_username VARCHAR DEFAULT NULL,
    p_first_name VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    user_id UUID,
    is_pro BOOLEAN,
    tier VARCHAR,
    lookup_count INTEGER,
    lookups_remaining INTEGER,
    is_new_user BOOLEAN
) AS $$
DECLARE
    v_user rivet_users%ROWTYPE;
    v_is_new BOOLEAN := FALSE;
BEGIN
    -- Try to get existing user
    SELECT * INTO v_user FROM rivet_users WHERE telegram_id = p_telegram_id;
    
    -- Create if doesn't exist
    IF v_user.id IS NULL THEN
        INSERT INTO rivet_users (telegram_id, telegram_username, telegram_first_name)
        VALUES (p_telegram_id, p_username, p_first_name)
        RETURNING * INTO v_user;
        v_is_new := TRUE;
    ELSE
        -- Update last active
        UPDATE rivet_users 
        SET last_active_at = NOW(),
            telegram_username = COALESCE(p_username, telegram_username),
            telegram_first_name = COALESCE(p_first_name, telegram_first_name)
        WHERE telegram_id = p_telegram_id;
    END IF;
    
    -- Reset monthly lookups if needed
    IF v_user.lookup_reset_at < NOW() - INTERVAL '30 days' THEN
        UPDATE rivet_users 
        SET lookup_count = 0, lookup_reset_at = NOW()
        WHERE telegram_id = p_telegram_id;
        v_user.lookup_count := 0;
    END IF;
    
    RETURN QUERY SELECT 
        v_user.id,
        v_user.is_pro,
        v_user.tier,
        v_user.lookup_count,
        CASE WHEN v_user.is_pro THEN 999 ELSE GREATEST(0, 10 - v_user.lookup_count) END,
        v_is_new;
END;
$$ LANGUAGE plpgsql;

-- ───────────────────────────────────────────────────────────────────────────
-- Check and increment lookup count
-- Returns: allowed, remaining, is_pro, user_id
-- ───────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION check_and_increment_lookup(p_telegram_id BIGINT)
RETURNS TABLE (
    allowed BOOLEAN,
    remaining INTEGER,
    is_pro BOOLEAN,
    user_id UUID,
    message TEXT
) AS $$
DECLARE
    v_user rivet_users%ROWTYPE;
BEGIN
    -- Get or create user
    INSERT INTO rivet_users (telegram_id)
    VALUES (p_telegram_id)
    ON CONFLICT (telegram_id) DO NOTHING;
    
    SELECT * INTO v_user FROM rivet_users WHERE telegram_id = p_telegram_id;
    
    -- Reset if needed
    IF v_user.lookup_reset_at < NOW() - INTERVAL '30 days' THEN
        UPDATE rivet_users 
        SET lookup_count = 0, lookup_reset_at = NOW()
        WHERE telegram_id = p_telegram_id;
        v_user.lookup_count := 0;
    END IF;
    
    -- Pro users always allowed
    IF v_user.is_pro THEN
        UPDATE rivet_users 
        SET total_lookups_all_time = total_lookups_all_time + 1,
            last_active_at = NOW()
        WHERE telegram_id = p_telegram_id;
        
        RETURN QUERY SELECT TRUE, 999, TRUE, v_user.id, 'Pro user - unlimited'::TEXT;
        RETURN;
    END IF;
    
    -- Check free tier limit
    IF v_user.lookup_count >= 10 THEN
        RETURN QUERY SELECT FALSE, 0, FALSE, v_user.id, 
            'Free limit reached. Upgrade to Pro for unlimited lookups!'::TEXT;
        RETURN;
    END IF;
    
    -- Increment and return
    UPDATE rivet_users 
    SET lookup_count = lookup_count + 1,
        total_lookups_all_time = total_lookups_all_time + 1,
        last_active_at = NOW(),
        updated_at = NOW()
    WHERE telegram_id = p_telegram_id;
    
    RETURN QUERY SELECT TRUE, (9 - v_user.lookup_count)::INTEGER, FALSE, v_user.id,
        format('%s lookups remaining this month', 9 - v_user.lookup_count)::TEXT;
END;
$$ LANGUAGE plpgsql;

-- ───────────────────────────────────────────────────────────────────────────
-- Update user subscription from Stripe
-- ───────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION update_subscription(
    p_telegram_id BIGINT,
    p_stripe_customer_id VARCHAR,
    p_stripe_subscription_id VARCHAR,
    p_subscription_status VARCHAR,
    p_is_pro BOOLEAN
)
RETURNS VOID AS $$
BEGIN
    UPDATE rivet_users
    SET stripe_customer_id = p_stripe_customer_id,
        stripe_subscription_id = p_stripe_subscription_id,
        subscription_status = p_subscription_status,
        is_pro = p_is_pro,
        tier = CASE WHEN p_is_pro THEN 'pro' ELSE 'free' END,
        subscription_started_at = CASE WHEN p_is_pro AND subscription_started_at IS NULL THEN NOW() ELSE subscription_started_at END,
        updated_at = NOW()
    WHERE telegram_id = p_telegram_id;
END;
$$ LANGUAGE plpgsql;

-- ───────────────────────────────────────────────────────────────────────────
-- Get user status for /status command
-- ───────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION get_user_status(p_telegram_id BIGINT)
RETURNS TABLE (
    telegram_id BIGINT,
    tier VARCHAR,
    is_pro BOOLEAN,
    lookup_count INTEGER,
    lookups_remaining INTEGER,
    total_lookups INTEGER,
    print_sessions INTEGER,
    subscription_status VARCHAR,
    member_since TIMESTAMP,
    days_until_reset INTEGER
) AS $$
DECLARE
    v_user rivet_users%ROWTYPE;
BEGIN
    SELECT * INTO v_user FROM rivet_users WHERE rivet_users.telegram_id = p_telegram_id;
    
    IF v_user.id IS NULL THEN
        RETURN;
    END IF;
    
    RETURN QUERY SELECT 
        v_user.telegram_id,
        v_user.tier,
        v_user.is_pro,
        v_user.lookup_count,
        CASE WHEN v_user.is_pro THEN 999 ELSE GREATEST(0, 10 - v_user.lookup_count) END,
        v_user.total_lookups_all_time,
        v_user.print_sessions_count,
        v_user.subscription_status,
        v_user.created_at,
        GREATEST(0, 30 - EXTRACT(DAY FROM NOW() - v_user.lookup_reset_at)::INTEGER);
END;
$$ LANGUAGE plpgsql;

-- ───────────────────────────────────────────────────────────────────────────
-- Start a print chat session
-- ───────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION start_print_session(
    p_telegram_id BIGINT,
    p_pdf_file_id VARCHAR,
    p_pdf_name VARCHAR,
    p_pdf_base64 TEXT
)
RETURNS TABLE (
    session_id UUID,
    success BOOLEAN,
    message TEXT
) AS $$
DECLARE
    v_user rivet_users%ROWTYPE;
    v_session_id UUID;
BEGIN
    -- Get user
    SELECT * INTO v_user FROM rivet_users WHERE telegram_id = p_telegram_id;
    
    IF v_user.id IS NULL THEN
        RETURN QUERY SELECT NULL::UUID, FALSE, 'User not found'::TEXT;
        RETURN;
    END IF;
    
    -- Check if Pro
    IF NOT v_user.is_pro THEN
        RETURN QUERY SELECT NULL::UUID, FALSE, 'Chat with Print is a Pro feature. Send /upgrade to unlock!'::TEXT;
        RETURN;
    END IF;
    
    -- End any existing active session
    UPDATE rivet_print_sessions 
    SET is_active = FALSE, ended_at = NOW()
    WHERE telegram_id = p_telegram_id AND is_active = TRUE;
    
    -- Create new session
    INSERT INTO rivet_print_sessions (user_id, telegram_id, pdf_file_id, pdf_name, pdf_base64)
    VALUES (v_user.id, p_telegram_id, p_pdf_file_id, p_pdf_name, p_pdf_base64)
    RETURNING id INTO v_session_id;
    
    -- Update user stats
    UPDATE rivet_users 
    SET print_sessions_count = print_sessions_count + 1
    WHERE telegram_id = p_telegram_id;
    
    RETURN QUERY SELECT v_session_id, TRUE, 'Print session started! Ask me anything about this document.'::TEXT;
END;
$$ LANGUAGE plpgsql;

-- ───────────────────────────────────────────────────────────────────────────
-- Get active print session
-- ───────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION get_active_print_session(p_telegram_id BIGINT)
RETURNS TABLE (
    session_id UUID,
    pdf_base64 TEXT,
    pdf_name VARCHAR,
    conversation_history JSONB,
    message_count INTEGER
) AS $$
BEGIN
    RETURN QUERY 
    SELECT 
        rps.id,
        rps.pdf_base64,
        rps.pdf_name,
        rps.conversation_history,
        rps.message_count
    FROM rivet_print_sessions rps
    WHERE rps.telegram_id = p_telegram_id 
      AND rps.is_active = TRUE
    ORDER BY rps.created_at DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- ───────────────────────────────────────────────────────────────────────────
-- Add message to print session
-- ───────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION add_print_message(
    p_session_id UUID,
    p_role VARCHAR, -- 'user' or 'assistant'
    p_content TEXT
)
RETURNS VOID AS $$
BEGIN
    UPDATE rivet_print_sessions
    SET conversation_history = conversation_history || jsonb_build_object(
            'role', p_role,
            'content', p_content,
            'timestamp', NOW()
        ),
        message_count = message_count + 1,
        questions_asked = questions_asked + CASE WHEN p_role = 'user' THEN 1 ELSE 0 END,
        last_message_at = NOW()
    WHERE id = p_session_id;
END;
$$ LANGUAGE plpgsql;

-- ───────────────────────────────────────────────────────────────────────────
-- End print session
-- ───────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION end_print_session(p_telegram_id BIGINT)
RETURNS TABLE (
    success BOOLEAN,
    message TEXT,
    questions_answered INTEGER
) AS $$
DECLARE
    v_session rivet_print_sessions%ROWTYPE;
BEGIN
    SELECT * INTO v_session 
    FROM rivet_print_sessions 
    WHERE telegram_id = p_telegram_id AND is_active = TRUE
    ORDER BY created_at DESC LIMIT 1;
    
    IF v_session.id IS NULL THEN
        RETURN QUERY SELECT FALSE, 'No active print session to end.'::TEXT, 0;
        RETURN;
    END IF;
    
    UPDATE rivet_print_sessions
    SET is_active = FALSE, ended_at = NOW()
    WHERE id = v_session.id;
    
    RETURN QUERY SELECT TRUE, 
        format('Session ended. You asked %s questions about %s.', v_session.questions_asked, v_session.pdf_name)::TEXT,
        v_session.questions_asked;
END;
$$ LANGUAGE plpgsql;

-- ═══════════════════════════════════════════════════════════════════════════
-- GRANT PERMISSIONS (adjust role name as needed)
-- ═══════════════════════════════════════════════════════════════════════════
-- GRANT ALL ON ALL TABLES IN SCHEMA public TO your_neon_user;
-- GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO your_neon_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO your_neon_user;

-- ═══════════════════════════════════════════════════════════════════════════
-- VERIFICATION QUERIES
-- ═══════════════════════════════════════════════════════════════════════════
-- Run these to verify installation:

-- SELECT * FROM get_or_create_user(123456789, 'testuser', 'Test');
-- SELECT * FROM check_and_increment_lookup(123456789);
-- SELECT * FROM get_user_status(123456789);
