-- ============================================
-- RIVET Pro Phase 5: Research Pipeline
-- Database Migration
-- ============================================
-- Created: 2025-12-27
-- Purpose: Enable autonomous KB growth via forum scraping
--
-- Features:
-- - URL fingerprinting for deduplication
-- - Ingestion tracking (queued → completed)
-- - Support for multiple source types (Stack Overflow, Reddit, YouTube, PDFs)
--
-- Usage:
-- 1. Deploy to Supabase SQL Editor
-- 2. Verify with: SELECT COUNT(*) FROM source_fingerprints;
-- ============================================

-- ====================
-- Table: source_fingerprints
-- ====================
-- Tracks all sources discovered by research pipeline
-- Prevents re-ingestion of same URLs
-- Monitors ingestion progress

CREATE TABLE IF NOT EXISTS source_fingerprints (
  id SERIAL PRIMARY KEY,
  url_hash VARCHAR(64) UNIQUE NOT NULL,
  url TEXT NOT NULL,
  source_type VARCHAR(20) NOT NULL, -- 'stackoverflow', 'reddit', 'youtube', 'pdf', 'manual'
  created_at TIMESTAMP DEFAULT NOW(),
  queued_for_ingestion BOOLEAN DEFAULT TRUE,
  ingestion_completed_at TIMESTAMP
);

-- ====================
-- Indexes for Performance
-- ====================

-- Fast duplicate checking (used on every research pipeline run)
CREATE INDEX IF NOT EXISTS idx_source_fingerprints_hash
  ON source_fingerprints(url_hash);

-- Filter pending ingestions (used by ingestion worker)
CREATE INDEX IF NOT EXISTS idx_source_fingerprints_queued
  ON source_fingerprints(queued_for_ingestion)
  WHERE queued_for_ingestion = TRUE;

-- Sort by creation date (used for dashboard analytics)
CREATE INDEX IF NOT EXISTS idx_source_fingerprints_created
  ON source_fingerprints(created_at DESC);

-- Filter by source type (used for analytics)
CREATE INDEX IF NOT EXISTS idx_source_fingerprints_source_type
  ON source_fingerprints(source_type);

-- ====================
-- Verification
-- ====================

-- Test query: Check table exists and is empty
-- SELECT COUNT(*) as initial_count FROM source_fingerprints;
-- Expected: 0 rows

-- Test query: Insert test fingerprint
-- INSERT INTO source_fingerprints (url_hash, url, source_type)
-- VALUES ('test_hash_123', 'https://stackoverflow.com/questions/123', 'stackoverflow')
-- RETURNING *;

-- Test query: Check indexes exist
-- SELECT indexname, indexdef FROM pg_indexes
-- WHERE tablename = 'source_fingerprints';
-- Expected: 5 indexes (1 PK + 4 created above)

-- ====================
-- Analytics Queries (Optional)
-- ====================

-- Daily ingestion activity
-- SELECT
--   DATE(created_at) as date,
--   source_type,
--   COUNT(*) as sources_discovered,
--   COUNT(ingestion_completed_at) as sources_ingested,
--   ROUND(100.0 * COUNT(ingestion_completed_at) / COUNT(*), 2) as completion_rate
-- FROM source_fingerprints
-- GROUP BY DATE(created_at), source_type
-- ORDER BY date DESC;

-- Ingestion backlog
-- SELECT
--   source_type,
--   COUNT(*) as pending_count
-- FROM source_fingerprints
-- WHERE queued_for_ingestion = TRUE AND ingestion_completed_at IS NULL
-- GROUP BY source_type;

-- Most recent ingestions
-- SELECT
--   url,
--   source_type,
--   created_at,
--   ingestion_completed_at,
--   EXTRACT(EPOCH FROM (ingestion_completed_at - created_at)) / 60 as minutes_to_complete
-- FROM source_fingerprints
-- WHERE ingestion_completed_at IS NOT NULL
-- ORDER BY ingestion_completed_at DESC
-- LIMIT 10;

-- ====================
-- End of Migration
-- ====================
