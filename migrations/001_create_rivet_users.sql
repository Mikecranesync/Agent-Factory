-- Migration: 001_create_rivet_users
-- Created: 2025-12-26
-- Description: Create rivet_users table for user account management

CREATE TABLE IF NOT EXISTS rivet_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255),
    telegram_id BIGINT UNIQUE,
    telegram_username VARCHAR(255),
    stripe_customer_id VARCHAR(255),
    atlas_user_id VARCHAR(255),
    tier VARCHAR(50) DEFAULT 'beta',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_rivet_users_email ON rivet_users(email);
CREATE INDEX IF NOT EXISTS idx_rivet_users_telegram_id ON rivet_users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_rivet_users_stripe_customer_id ON rivet_users(stripe_customer_id);

-- Trigger for auto-updating updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_rivet_users_updated_at
    BEFORE UPDATE ON rivet_users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Verification query
SELECT 'rivet_users table created successfully' AS status;
