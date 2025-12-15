-- Knowledge Base Ingestion Chain - Database Migration
-- Run this SQL in Supabase SQL Editor to add required tables

-- ============================================================================
-- Source Fingerprints (Deduplication Tracking)
-- ============================================================================

CREATE TABLE IF NOT EXISTS source_fingerprints (
    id BIGSERIAL PRIMARY KEY,
    fingerprint VARCHAR(32) NOT NULL UNIQUE,  -- SHA-256 hash (first 16 chars)
    url TEXT NOT NULL,
    source_type VARCHAR(20) NOT NULL,  -- 'pdf', 'youtube', 'web'
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atoms_created INTEGER DEFAULT 0,
    atoms_failed INTEGER DEFAULT 0,
    CONSTRAINT source_type_check CHECK (source_type IN ('pdf', 'youtube', 'web'))
);

-- Index for fast duplicate lookups
CREATE INDEX IF NOT EXISTS idx_source_fingerprints_fingerprint
ON source_fingerprints(fingerprint);

CREATE INDEX IF NOT EXISTS idx_source_fingerprints_url
ON source_fingerprints(url);

-- ============================================================================
-- Ingestion Logs (Processing History)
-- ============================================================================

CREATE TABLE IF NOT EXISTS ingestion_logs (
    id BIGSERIAL PRIMARY KEY,
    source_url TEXT NOT NULL,
    source_type VARCHAR(20) NOT NULL,
    stage VARCHAR(50) NOT NULL,  -- 'acquisition', 'extraction', 'chunking', etc.
    status VARCHAR(20) NOT NULL,  -- 'started', 'completed', 'failed'
    atoms_created INTEGER DEFAULT 0,
    atoms_failed INTEGER DEFAULT 0,
    error_message TEXT,
    processing_time_seconds INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT log_status_check CHECK (status IN ('started', 'completed', 'failed'))
);

-- Index for filtering logs
CREATE INDEX IF NOT EXISTS idx_ingestion_logs_source_url
ON ingestion_logs(source_url);

CREATE INDEX IF NOT EXISTS idx_ingestion_logs_status
ON ingestion_logs(status);

CREATE INDEX IF NOT EXISTS idx_ingestion_logs_created_at
ON ingestion_logs(created_at DESC);

-- ============================================================================
-- Failed Ingestions (Error Queue)
-- ============================================================================

CREATE TABLE IF NOT EXISTS failed_ingestions (
    id BIGSERIAL PRIMARY KEY,
    source_url TEXT NOT NULL,
    source_type VARCHAR(20) NOT NULL,
    stage VARCHAR(50) NOT NULL,
    error_message TEXT NOT NULL,
    raw_content TEXT,  -- Store raw content for debugging
    retry_count INTEGER DEFAULT 0,
    last_retry_at TIMESTAMPTZ,
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for retrying failed ingestions
CREATE INDEX IF NOT EXISTS idx_failed_ingestions_resolved
ON failed_ingestions(resolved);

CREATE INDEX IF NOT EXISTS idx_failed_ingestions_retry_count
ON failed_ingestions(retry_count);

-- ============================================================================
-- Human Review Queue (Quality Validation Failures)
-- ============================================================================

CREATE TABLE IF NOT EXISTS human_review_queue (
    id BIGSERIAL PRIMARY KEY,
    atom_id VARCHAR(100),
    atom_title TEXT NOT NULL,
    atom_description TEXT NOT NULL,
    quality_score INTEGER NOT NULL,  -- 0-100
    validation_issues TEXT[],  -- Array of issue descriptions
    source_url TEXT,
    reviewed BOOLEAN DEFAULT FALSE,
    reviewer_decision VARCHAR(20),  -- 'approve', 'reject', 'revise'
    reviewer_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ,
    CONSTRAINT reviewer_decision_check CHECK (reviewer_decision IN ('approve', 'reject', 'revise', NULL))
);

-- Index for unreviewed items
CREATE INDEX IF NOT EXISTS idx_human_review_queue_reviewed
ON human_review_queue(reviewed);

CREATE INDEX IF NOT EXISTS idx_human_review_queue_quality_score
ON human_review_queue(quality_score);

-- ============================================================================
-- Atom Relations (Prerequisite Chains)
-- ============================================================================

CREATE TABLE IF NOT EXISTS atom_relations (
    id BIGSERIAL PRIMARY KEY,
    source_atom_id VARCHAR(100) NOT NULL,
    target_atom_id VARCHAR(100) NOT NULL,
    relation_type VARCHAR(50) NOT NULL,  -- 'requires', 'is_part_of', 'teaches', etc.
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(source_atom_id, target_atom_id, relation_type)
);

-- Indexes for graph traversal
CREATE INDEX IF NOT EXISTS idx_atom_relations_source
ON atom_relations(source_atom_id);

CREATE INDEX IF NOT EXISTS idx_atom_relations_target
ON atom_relations(target_atom_id);

CREATE INDEX IF NOT EXISTS idx_atom_relations_type
ON atom_relations(relation_type);

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE source_fingerprints IS 'Tracks processed sources to prevent duplicate ingestion';
COMMENT ON TABLE ingestion_logs IS 'Complete processing history for all ingestion runs';
COMMENT ON TABLE failed_ingestions IS 'Queue of failed ingestions for manual review and retry';
COMMENT ON TABLE human_review_queue IS 'Atoms that failed quality validation and need human approval';
COMMENT ON TABLE atom_relations IS 'Graph structure of prerequisite relationships between atoms';

-- ============================================================================
-- Grant Permissions (if using RLS)
-- ============================================================================

-- Allow service role to manage all ingestion tables
GRANT ALL ON source_fingerprints TO service_role;
GRANT ALL ON ingestion_logs TO service_role;
GRANT ALL ON failed_ingestions TO service_role;
GRANT ALL ON human_review_queue TO service_role;
GRANT ALL ON atom_relations TO service_role;

-- Grant sequences
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO service_role;

-- ============================================================================
-- Verification Query
-- ============================================================================

-- Run this to verify tables were created:
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN (
    'source_fingerprints',
    'ingestion_logs',
    'failed_ingestions',
    'human_review_queue',
    'atom_relations'
)
ORDER BY table_name;
