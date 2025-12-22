-- Migration: KB Gaps Tracking Table
-- Created: 2025-12-22
-- Purpose: Track knowledge base gaps to identify missing content and measure coverage

CREATE TABLE IF NOT EXISTS kb_gaps (
    id SERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    intent_vendor VARCHAR(50),
    intent_equipment VARCHAR(50),
    intent_symptom TEXT,
    search_filters JSONB,
    triggered_at TIMESTAMP DEFAULT NOW(),
    user_id TEXT,
    frequency INT DEFAULT 1,
    last_asked_at TIMESTAMP DEFAULT NOW(),
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    resolution_atom_ids TEXT[]
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_kb_gaps_query ON kb_gaps(query);
CREATE INDEX IF NOT EXISTS idx_kb_gaps_resolved ON kb_gaps(resolved);
CREATE INDEX IF NOT EXISTS idx_kb_gaps_frequency ON kb_gaps(frequency DESC);
CREATE INDEX IF NOT EXISTS idx_kb_gaps_triggered_at ON kb_gaps(triggered_at DESC);

-- Comments for documentation
COMMENT ON TABLE kb_gaps IS 'Tracks knowledge base gaps when Route C is triggered (no KB match)';
COMMENT ON COLUMN kb_gaps.query IS 'Original user query that had no KB match';
COMMENT ON COLUMN kb_gaps.frequency IS 'Number of times this query (or similar) was asked within 7 days';
COMMENT ON COLUMN kb_gaps.resolved IS 'Whether this gap has been filled with KB content';
COMMENT ON COLUMN kb_gaps.resolution_atom_ids IS 'Array of atom IDs that resolved this gap';
