-- =============================================================================
-- Migration: Add Conversation Sessions for Natural Language Intelligence
-- =============================================================================
-- Phase 1: Conversation Memory
-- Enables bot to remember and reference previous messages
--
-- Deploy: poetry run python scripts/run_migration.py 001
-- =============================================================================

-- Conversation Sessions Table
CREATE TABLE IF NOT EXISTS conversation_sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    telegram_user_id BIGINT,

    -- Conversation data
    messages JSONB NOT NULL DEFAULT '[]'::jsonb,
    context_summary TEXT,
    last_topic TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_conversation_sessions_user ON conversation_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_conversation_sessions_telegram ON conversation_sessions(telegram_user_id);
CREATE INDEX IF NOT EXISTS idx_conversation_sessions_updated ON conversation_sessions(updated_at);

-- GIN index for messages JSON searching (Phase 2+)
CREATE INDEX IF NOT EXISTS idx_conversation_sessions_messages_gin
ON conversation_sessions USING GIN(messages);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_conversation_sessions_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_conversation_sessions_updated_at
    BEFORE UPDATE ON conversation_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_sessions_timestamp();

-- Helper function: Get user's conversation context
CREATE OR REPLACE FUNCTION get_conversation_context(p_user_id TEXT)
RETURNS JSONB AS $$
DECLARE
    v_result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'session_id', session_id,
        'last_topic', last_topic,
        'message_count', jsonb_array_length(messages),
        'last_updated', updated_at,
        'context_summary', context_summary
    ) INTO v_result
    FROM conversation_sessions
    WHERE user_id = p_user_id;

    RETURN COALESCE(v_result, '{}'::jsonb);
END;
$$ LANGUAGE plpgsql;

-- Helper function: Clean up old sessions
CREATE OR REPLACE FUNCTION cleanup_old_conversation_sessions(p_days INT DEFAULT 30)
RETURNS INT AS $$
DECLARE
    v_deleted INT;
BEGIN
    DELETE FROM conversation_sessions
    WHERE updated_at < NOW() - (p_days || ' days')::INTERVAL;

    GET DIAGNOSTICS v_deleted = ROW_COUNT;
    RETURN v_deleted;
END;
$$ LANGUAGE plpgsql;

-- Seed data for testing
INSERT INTO conversation_sessions (session_id, user_id, telegram_user_id, messages, last_topic)
VALUES (
    'test_session_001',
    'test_user_free',
    123456789,
    '[
        {"role": "user", "content": "Motor running hot", "timestamp": "2025-12-15T10:00:00Z"},
        {"role": "assistant", "content": "Let me help diagnose that...", "timestamp": "2025-12-15T10:00:05Z"}
    ]'::jsonb,
    'motor overheating'
)
ON CONFLICT (session_id) DO NOTHING;

-- Verify migration
DO $$
BEGIN
    ASSERT EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_name = 'conversation_sessions'
    ), 'conversation_sessions table not created';

    ASSERT EXISTS (
        SELECT FROM pg_proc
        WHERE proname = 'get_conversation_context'
    ), 'get_conversation_context function not created';

    RAISE NOTICE 'Migration 001: Conversation Sessions - SUCCESS';
END $$;
