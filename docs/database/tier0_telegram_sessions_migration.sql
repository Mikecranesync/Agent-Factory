-- ============================================================================
-- TIER 0.1: Telegram Session Management Table
-- ============================================================================
-- Purpose: Store conversation context per Telegram user for CEO Command & Control
-- Part of: task-38.1 (Telegram Bot Infrastructure)
-- Created: 2025-12-19
-- ============================================================================

-- Create telegram_sessions table
CREATE TABLE IF NOT EXISTS telegram_sessions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,  -- Telegram user ID
    message_history JSONB DEFAULT '[]'::jsonb,  -- Array of message objects
    context JSONB DEFAULT '{}'::jsonb,  -- Arbitrary key-value pairs
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on user_id for fast lookups
CREATE INDEX IF NOT EXISTS idx_telegram_sessions_user_id
ON telegram_sessions(user_id);

-- Create index on updated_at for cleanup queries
CREATE INDEX IF NOT EXISTS idx_telegram_sessions_updated_at
ON telegram_sessions(updated_at);

-- Add comment to table
COMMENT ON TABLE telegram_sessions IS
'TIER 0.1: Telegram conversation sessions for CEO Command & Control interface. Stores message history and context per user.';

-- Add column comments
COMMENT ON COLUMN telegram_sessions.user_id IS
'Telegram user ID (unique identifier)';

COMMENT ON COLUMN telegram_sessions.message_history IS
'Array of message objects with: role, content, type, timestamp';

COMMENT ON COLUMN telegram_sessions.context IS
'Arbitrary key-value pairs for conversation state (active task, preferences, etc.)';

-- ============================================================================
-- Example message_history format:
-- ============================================================================
-- [
--   {
--     "role": "user",
--     "content": "Deploy the new feature",
--     "type": "text",
--     "timestamp": "2025-12-19T12:00:00Z"
--   },
--   {
--     "role": "assistant",
--     "content": "✅ Message Received...",
--     "type": "text",
--     "timestamp": "2025-12-19T12:00:01Z"
--   }
-- ]

-- ============================================================================
-- Example context format:
-- ============================================================================
-- {
--   "active_task_id": "task-123",
--   "last_intent": "deploy",
--   "timezone": "America/New_York",
--   "preferences": {
--     "notification_level": "high"
--   }
-- }

-- ============================================================================
-- Cleanup Policy (Optional)
-- ============================================================================
-- Sessions older than 30 days with no activity can be archived/deleted
-- Run this periodically (e.g., monthly cron job):

-- DELETE FROM telegram_sessions
-- WHERE updated_at < NOW() - INTERVAL '30 days';

-- ============================================================================
-- Row-Level Security (Optional - for multi-tenant Supabase)
-- ============================================================================
-- Enable RLS if using Supabase with user authentication
-- ALTER TABLE telegram_sessions ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their own sessions
-- CREATE POLICY telegram_sessions_user_policy
-- ON telegram_sessions
-- FOR ALL
-- USING (user_id = current_setting('app.current_user_id')::bigint);

-- ============================================================================
-- Grant Permissions
-- ============================================================================
-- Grant read/write to service role (for bot operations)
GRANT ALL ON telegram_sessions TO service_role;
GRANT USAGE, SELECT ON SEQUENCE telegram_sessions_id_seq TO service_role;

-- Grant read-only to authenticated users (for analytics/reporting)
GRANT SELECT ON telegram_sessions TO authenticated;

-- ============================================================================
-- Migration Complete
-- ============================================================================
-- Table: telegram_sessions
-- Indexes: idx_telegram_sessions_user_id, idx_telegram_sessions_updated_at
-- RLS: Disabled by default (enable if multi-tenant)
-- Cleanup: Manual (DELETE sessions older than 30 days)
-- ============================================================================
