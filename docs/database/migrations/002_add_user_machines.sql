-- Migration: Add User Machines Library Tables
-- Created: 2025-12-23
-- Purpose: Personal Machine Library for RivetCEO Bot

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- User's saved machines
CREATE TABLE IF NOT EXISTS user_machines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,                  -- Telegram user ID
    nickname VARCHAR(50) NOT NULL,          -- User-friendly name: "Line 3 Robot", "Basement Compressor"
    manufacturer VARCHAR(100),              -- Fanuc, Siemens, Allen-Bradley, etc.
    model_number VARCHAR(100),              -- M-20iA, S7-1200, 1756-L83E, etc.
    serial_number VARCHAR(100),             -- Equipment serial number
    location TEXT,                          -- Building A, Line 3, Basement, etc.
    notes TEXT,                             -- User notes: "Replaced servo amp 2024-03"
    photo_file_id TEXT,                     -- Telegram CDN file_id for reference photo
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_queried TIMESTAMPTZ,               -- Last time user troubleshooted this machine
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, nickname)               -- Prevent duplicate nicknames per user
);

-- Query history per machine
CREATE TABLE IF NOT EXISTS user_machine_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    machine_id UUID REFERENCES user_machines(id) ON DELETE CASCADE,
    query_text TEXT NOT NULL,
    response_summary TEXT,                  -- First 500 chars of response
    atoms_used TEXT[],                      -- Knowledge atoms referenced in answer
    route_taken VARCHAR(10),                -- A, B, C, or D (RivetOrchestrator route)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_machines_user ON user_machines(user_id);
CREATE INDEX IF NOT EXISTS idx_user_machines_nickname ON user_machines(user_id, nickname);
CREATE INDEX IF NOT EXISTS idx_user_machines_updated ON user_machines(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_machine_history_machine ON user_machine_history(machine_id);
CREATE INDEX IF NOT EXISTS idx_machine_history_created ON user_machine_history(created_at DESC);

-- Helper function: Get machine count for user
CREATE OR REPLACE FUNCTION get_user_machine_count(p_user_id TEXT)
RETURNS INTEGER AS $$
BEGIN
    RETURN (SELECT COUNT(*) FROM user_machines WHERE user_id = p_user_id);
END;
$$ LANGUAGE plpgsql;

-- Helper function: Get machine details with query count
CREATE OR REPLACE FUNCTION get_machine_details(p_machine_id UUID)
RETURNS TABLE (
    id UUID,
    nickname VARCHAR,
    manufacturer VARCHAR,
    model_number VARCHAR,
    serial_number VARCHAR,
    location TEXT,
    notes TEXT,
    query_count BIGINT,
    last_queried TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        m.id,
        m.nickname,
        m.manufacturer,
        m.model_number,
        m.serial_number,
        m.location,
        m.notes,
        COUNT(h.id) as query_count,
        m.last_queried
    FROM user_machines m
    LEFT JOIN user_machine_history h ON h.machine_id = m.id
    WHERE m.id = p_machine_id
    GROUP BY m.id;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Update updated_at timestamp on machine changes
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_machines_modtime
    BEFORE UPDATE ON user_machines
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();

-- Sample queries for testing:
--
-- -- Get all machines for user
-- SELECT * FROM user_machines WHERE user_id = 'telegram_123456789' ORDER BY updated_at DESC;
--
-- -- Get machine with history count
-- SELECT * FROM get_machine_details('uuid-here');
--
-- -- Get recent queries for machine
-- SELECT query_text, response_summary, route_taken, created_at
-- FROM user_machine_history
-- WHERE machine_id = 'uuid-here'
-- ORDER BY created_at DESC
-- LIMIT 10;
--
-- -- Check duplicate nicknames
-- SELECT user_id, nickname, COUNT(*)
-- FROM user_machines
-- GROUP BY user_id, nickname
-- HAVING COUNT(*) > 1;
