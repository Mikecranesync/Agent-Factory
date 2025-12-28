-- ═══════════════════════════════════════════════════════════════════════════
-- RIVET PUBLIC LAUNCH MIGRATION
-- Makes the bot ready for public multi-tenant use
-- ═══════════════════════════════════════════════════════════════════════════

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. RATE LIMITING TABLE
-- Prevents abuse from free tier users
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS rate_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES rivet_users(id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL,  -- 'question', 'upload', 'ocr', 'voice'
    window_start TIMESTAMP NOT NULL DEFAULT NOW(),
    action_count INTEGER DEFAULT 1,
    UNIQUE(user_id, action_type, window_start)
);

CREATE INDEX IF NOT EXISTS idx_rate_limits_user_action 
    ON rate_limits(user_id, action_type, window_start DESC);

-- Rate limit check function
CREATE OR REPLACE FUNCTION check_rate_limit(
    p_user_id UUID,
    p_action_type VARCHAR(50),
    p_limit INTEGER,
    p_window_minutes INTEGER DEFAULT 60
) RETURNS BOOLEAN AS $$
DECLARE
    v_count INTEGER;
    v_window_start TIMESTAMP;
BEGIN
    v_window_start := date_trunc('hour', NOW()) + 
        (EXTRACT(MINUTE FROM NOW())::INTEGER / p_window_minutes) * 
        (p_window_minutes || ' minutes')::INTERVAL;
    
    -- Get or create rate limit record
    INSERT INTO rate_limits (user_id, action_type, window_start, action_count)
    VALUES (p_user_id, p_action_type, v_window_start, 1)
    ON CONFLICT (user_id, action_type, window_start) 
    DO UPDATE SET action_count = rate_limits.action_count + 1
    RETURNING action_count INTO v_count;
    
    RETURN v_count <= p_limit;
END;
$$ LANGUAGE plpgsql;

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. USAGE ANALYTICS TABLE
-- Track usage for billing and insights
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS usage_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES rivet_users(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,  -- 'question', 'upload', 'ocr', 'voice', 'login'
    event_data JSONB DEFAULT '{}',
    tokens_used INTEGER DEFAULT 0,
    cost_usd DECIMAL(10, 6) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_usage_user_date 
    ON usage_events(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_usage_type_date 
    ON usage_events(event_type, created_at DESC);

-- ─────────────────────────────────────────────────────────────────────────────
-- 3. ADD MISSING COLUMNS TO rivet_users
-- Support public user management
-- ─────────────────────────────────────────────────────────────────────────────

-- Add columns if they don't exist
DO $$
BEGIN
    -- Last activity tracking
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'rivet_users' AND column_name = 'last_active_at') THEN
        ALTER TABLE rivet_users ADD COLUMN last_active_at TIMESTAMP DEFAULT NOW();
    END IF;

    -- Onboarding completion
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'rivet_users' AND column_name = 'onboarding_completed') THEN
        ALTER TABLE rivet_users ADD COLUMN onboarding_completed BOOLEAN DEFAULT FALSE;
    END IF;

    -- Monthly question count (for tier limits)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'rivet_users' AND column_name = 'questions_this_month') THEN
        ALTER TABLE rivet_users ADD COLUMN questions_this_month INTEGER DEFAULT 0;
    END IF;

    -- Monthly reset date
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'rivet_users' AND column_name = 'month_reset_at') THEN
        ALTER TABLE rivet_users ADD COLUMN month_reset_at TIMESTAMP DEFAULT NOW();
    END IF;

    -- Referral tracking
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'rivet_users' AND column_name = 'referred_by') THEN
        ALTER TABLE rivet_users ADD COLUMN referred_by UUID REFERENCES rivet_users(id);
    END IF;

    -- Account status
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'rivet_users' AND column_name = 'status') THEN
        ALTER TABLE rivet_users ADD COLUMN status VARCHAR(20) DEFAULT 'active';
    END IF;
END $$;

-- ─────────────────────────────────────────────────────────────────────────────
-- 4. PERFORMANCE INDEXES FOR SCALE
-- ─────────────────────────────────────────────────────────────────────────────

-- User lookups
CREATE INDEX IF NOT EXISTS idx_users_telegram ON rivet_users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_tier ON rivet_users(tier);
CREATE INDEX IF NOT EXISTS idx_users_status ON rivet_users(status);
CREATE INDEX IF NOT EXISTS idx_users_active ON rivet_users(last_active_at DESC);

-- Machine/print lookups
CREATE INDEX IF NOT EXISTS idx_machines_name ON machines(user_id, name);
CREATE INDEX IF NOT EXISTS idx_prints_vectorized ON prints(vectorized, machine_id);

-- Chat history for context
CREATE INDEX IF NOT EXISTS idx_chat_recent ON print_chat_history(user_id, created_at DESC);

-- ─────────────────────────────────────────────────────────────────────────────
-- 5. TIER LIMITS CONFIGURATION TABLE
-- Easily adjustable without code changes
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS tier_limits (
    tier VARCHAR(50) PRIMARY KEY,
    questions_per_month INTEGER NOT NULL,
    machines_max INTEGER NOT NULL,
    prints_per_machine INTEGER NOT NULL,
    voice_minutes_per_month INTEGER NOT NULL,
    ocr_scans_per_month INTEGER NOT NULL,
    expert_calls_included INTEGER DEFAULT 0,
    price_monthly_usd DECIMAL(10, 2) NOT NULL,
    features JSONB DEFAULT '{}'
);

-- Insert default tiers
INSERT INTO tier_limits (tier, questions_per_month, machines_max, prints_per_machine, 
                         voice_minutes_per_month, ocr_scans_per_month, expert_calls_included,
                         price_monthly_usd, features)
VALUES 
    ('free', 10, 2, 5, 5, 10, 0, 0.00, 
     '{"basic_troubleshooting": true, "manual_search": true}'),
    ('pro', 100, 10, 25, 60, 100, 0, 49.00, 
     '{"basic_troubleshooting": true, "manual_search": true, "priority_response": true, "export_pdf": true}'),
    ('enterprise', -1, -1, -1, -1, -1, 2, 199.00, 
     '{"basic_troubleshooting": true, "manual_search": true, "priority_response": true, "export_pdf": true, "dedicated_support": true, "custom_kb": true}')
ON CONFLICT (tier) DO UPDATE SET
    questions_per_month = EXCLUDED.questions_per_month,
    machines_max = EXCLUDED.machines_max,
    prints_per_machine = EXCLUDED.prints_per_machine,
    voice_minutes_per_month = EXCLUDED.voice_minutes_per_month,
    ocr_scans_per_month = EXCLUDED.ocr_scans_per_month,
    expert_calls_included = EXCLUDED.expert_calls_included,
    price_monthly_usd = EXCLUDED.price_monthly_usd,
    features = EXCLUDED.features;

-- ─────────────────────────────────────────────────────────────────────────────
-- 6. MONTHLY RESET FUNCTION
-- Reset usage counts on billing cycle
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION reset_monthly_usage() RETURNS void AS $$
BEGIN
    UPDATE rivet_users 
    SET questions_this_month = 0,
        month_reset_at = NOW()
    WHERE month_reset_at < NOW() - INTERVAL '30 days';
    
    -- Clean up old rate limit records
    DELETE FROM rate_limits WHERE window_start < NOW() - INTERVAL '24 hours';
END;
$$ LANGUAGE plpgsql;

-- ─────────────────────────────────────────────────────────────────────────────
-- 7. ADMIN USERS TABLE
-- Separate admin access from regular users
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS admin_users (
    telegram_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    role VARCHAR(50) DEFAULT 'admin',  -- 'admin', 'super_admin', 'support'
    added_at TIMESTAMP DEFAULT NOW(),
    added_by BIGINT
);

-- Add Mike as super admin
INSERT INTO admin_users (telegram_id, username, role)
VALUES (8445149012, 'hharpercrew', 'super_admin')
ON CONFLICT (telegram_id) DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────────────
-- VERIFICATION
-- ─────────────────────────────────────────────────────────────────────────────

DO $$
BEGIN
    RAISE NOTICE '═══════════════════════════════════════════════════════════════';
    RAISE NOTICE 'PUBLIC LAUNCH MIGRATION COMPLETE';
    RAISE NOTICE '═══════════════════════════════════════════════════════════════';
    RAISE NOTICE '';
    RAISE NOTICE 'New tables:';
    RAISE NOTICE '  ✓ rate_limits - Per-user rate limiting';
    RAISE NOTICE '  ✓ usage_events - Analytics and billing';
    RAISE NOTICE '  ✓ tier_limits - Configurable tier restrictions';
    RAISE NOTICE '  ✓ admin_users - Admin access control';
    RAISE NOTICE '';
    RAISE NOTICE 'New columns on rivet_users:';
    RAISE NOTICE '  ✓ last_active_at';
    RAISE NOTICE '  ✓ onboarding_completed';
    RAISE NOTICE '  ✓ questions_this_month';
    RAISE NOTICE '  ✓ month_reset_at';
    RAISE NOTICE '  ✓ referred_by';
    RAISE NOTICE '  ✓ status';
    RAISE NOTICE '';
    RAISE NOTICE 'Functions:';
    RAISE NOTICE '  ✓ check_rate_limit()';
    RAISE NOTICE '  ✓ reset_monthly_usage()';
    RAISE NOTICE '';
    RAISE NOTICE 'Your Telegram ID (8445149012) added as super_admin';
    RAISE NOTICE '═══════════════════════════════════════════════════════════════';
END $$;
