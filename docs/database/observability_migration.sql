-- ============================================================================
-- Knowledge Base Observability Platform - Database Schema Migration
-- ============================================================================
-- Creates 3 tables for tracking ingestion pipeline metrics:
--   1. ingestion_metrics_realtime - Per-source ingestion results
--   2. ingestion_metrics_hourly - Hourly aggregations
--   3. ingestion_metrics_daily - Daily rollups
--
-- Run in Supabase SQL Editor or via psql
-- ============================================================================

-- Table 1: Real-time Ingestion Metrics
-- ============================================================================
-- Tracks every source processed through the 7-stage ingestion pipeline
-- Stores stage-by-stage timing, quality scores, and errors

CREATE TABLE IF NOT EXISTS ingestion_metrics_realtime (
    id BIGSERIAL PRIMARY KEY,

    -- Source identification
    source_url TEXT NOT NULL,
    source_type VARCHAR(20) NOT NULL CHECK (source_type IN ('web', 'pdf', 'youtube')),
    source_hash VARCHAR(64) NOT NULL,

    -- Results
    status VARCHAR(20) NOT NULL CHECK (status IN ('success', 'partial', 'failed')),
    atoms_created INTEGER DEFAULT 0 CHECK (atoms_created >= 0),
    atoms_failed INTEGER DEFAULT 0 CHECK (atoms_failed >= 0),
    chunks_processed INTEGER DEFAULT 0 CHECK (chunks_processed >= 0),

    -- Quality metrics
    avg_quality_score FLOAT CHECK (avg_quality_score >= 0 AND avg_quality_score <= 1),
    quality_pass_rate FLOAT CHECK (quality_pass_rate >= 0 AND quality_pass_rate <= 1),

    -- Stage timings (milliseconds)
    -- Stage 1: Source Acquisition (download/fetch)
    stage_1_acquisition_ms INTEGER CHECK (stage_1_acquisition_ms >= 0),

    -- Stage 2: Content Extraction (parse text)
    stage_2_extraction_ms INTEGER CHECK (stage_2_extraction_ms >= 0),

    -- Stage 3: Semantic Chunking (split into atoms)
    stage_3_chunking_ms INTEGER CHECK (stage_3_chunking_ms >= 0),

    -- Stage 4: Atom Generation (LLM extraction)
    stage_4_generation_ms INTEGER CHECK (stage_4_generation_ms >= 0),

    -- Stage 5: Quality Validation (score 0-100)
    stage_5_validation_ms INTEGER CHECK (stage_5_validation_ms >= 0),

    -- Stage 6: Embedding Generation (OpenAI)
    stage_6_embedding_ms INTEGER CHECK (stage_6_embedding_ms >= 0),

    -- Stage 7: Storage & Indexing (Supabase)
    stage_7_storage_ms INTEGER CHECK (stage_7_storage_ms >= 0),

    -- Total duration
    total_duration_ms INTEGER CHECK (total_duration_ms >= 0),

    -- Error tracking
    error_stage VARCHAR(50),
    error_message TEXT,

    -- Metadata (extracted from atoms)
    vendor TEXT,
    equipment_type TEXT,

    -- Timestamps
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,

    -- Ensure completed_at is after started_at
    CHECK (completed_at IS NULL OR completed_at >= started_at)
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_realtime_completed_at
    ON ingestion_metrics_realtime(completed_at DESC);

CREATE INDEX IF NOT EXISTS idx_realtime_status
    ON ingestion_metrics_realtime(status);

CREATE INDEX IF NOT EXISTS idx_realtime_vendor
    ON ingestion_metrics_realtime(vendor)
    WHERE vendor IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_realtime_source_type
    ON ingestion_metrics_realtime(source_type);

CREATE INDEX IF NOT EXISTS idx_realtime_source_hash
    ON ingestion_metrics_realtime(source_hash);

-- Composite index for dashboard queries (last 24h by vendor)
CREATE INDEX IF NOT EXISTS idx_realtime_recent_by_vendor
    ON ingestion_metrics_realtime(completed_at DESC, vendor)
    WHERE completed_at IS NOT NULL;

-- ============================================================================
-- Table 2: Hourly Aggregation Metrics
-- ============================================================================
-- Aggregated statistics per hour for trend analysis and dashboards

CREATE TABLE IF NOT EXISTS ingestion_metrics_hourly (
    id BIGSERIAL PRIMARY KEY,
    hour_start TIMESTAMPTZ NOT NULL UNIQUE,

    -- Throughput metrics
    sources_processed INTEGER DEFAULT 0 CHECK (sources_processed >= 0),
    atoms_created INTEGER DEFAULT 0 CHECK (atoms_created >= 0),
    atoms_failed INTEGER DEFAULT 0 CHECK (atoms_failed >= 0),
    success_rate FLOAT CHECK (success_rate >= 0 AND success_rate <= 1),

    -- Quality metrics
    avg_quality_score FLOAT CHECK (avg_quality_score >= 0 AND avg_quality_score <= 1),
    quality_pass_rate FLOAT CHECK (quality_pass_rate >= 0 AND quality_pass_rate <= 1),

    -- Performance metrics
    avg_total_duration_ms INTEGER CHECK (avg_total_duration_ms >= 0),
    p95_duration_ms INTEGER CHECK (p95_duration_ms >= 0),

    -- Stage bottleneck analysis (avg milliseconds per stage)
    avg_stage_1_ms INTEGER CHECK (avg_stage_1_ms >= 0),
    avg_stage_2_ms INTEGER CHECK (avg_stage_2_ms >= 0),
    avg_stage_3_ms INTEGER CHECK (avg_stage_3_ms >= 0),
    avg_stage_4_ms INTEGER CHECK (avg_stage_4_ms >= 0),
    avg_stage_5_ms INTEGER CHECK (avg_stage_5_ms >= 0),
    avg_stage_6_ms INTEGER CHECK (avg_stage_6_ms >= 0),
    avg_stage_7_ms INTEGER CHECK (avg_stage_7_ms >= 0),

    -- Coverage analysis (JSONB for flexibility)
    -- Example: {"Siemens": 45, "Rockwell": 38, "ABB": 23}
    vendor_counts JSONB,

    -- Example: {"PLC": 67, "VFD": 41, "HMI": 19}
    equipment_counts JSONB,

    -- Error tracking
    failed_sources INTEGER DEFAULT 0 CHECK (failed_sources >= 0),

    -- Example: {"stage_4": 3, "stage_5": 1}
    error_distribution JSONB,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_hourly_hour_start
    ON ingestion_metrics_hourly(hour_start DESC);

-- ============================================================================
-- Table 3: Daily Rollup Metrics
-- ============================================================================
-- Daily aggregates for long-term trend analysis and reporting

CREATE TABLE IF NOT EXISTS ingestion_metrics_daily (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,

    -- Throughput metrics
    sources_processed INTEGER DEFAULT 0 CHECK (sources_processed >= 0),
    atoms_created INTEGER DEFAULT 0 CHECK (atoms_created >= 0),
    atoms_failed INTEGER DEFAULT 0 CHECK (atoms_failed >= 0),
    success_rate FLOAT CHECK (success_rate >= 0 AND success_rate <= 1),

    -- Quality metrics
    avg_quality_score FLOAT CHECK (avg_quality_score >= 0 AND avg_quality_score <= 1),

    -- Coverage analysis
    unique_vendors INTEGER CHECK (unique_vendors >= 0),
    unique_equipment_types INTEGER CHECK (unique_equipment_types >= 0),

    -- Distribution (JSONB)
    vendor_distribution JSONB,
    equipment_distribution JSONB,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_daily_date
    ON ingestion_metrics_daily(date DESC);

-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Function: Calculate hourly aggregates from realtime table
CREATE OR REPLACE FUNCTION aggregate_hourly_metrics(target_hour TIMESTAMPTZ)
RETURNS VOID AS $$
BEGIN
    INSERT INTO ingestion_metrics_hourly (
        hour_start,
        sources_processed,
        atoms_created,
        atoms_failed,
        success_rate,
        avg_quality_score,
        quality_pass_rate,
        avg_total_duration_ms,
        p95_duration_ms,
        avg_stage_1_ms,
        avg_stage_2_ms,
        avg_stage_3_ms,
        avg_stage_4_ms,
        avg_stage_5_ms,
        avg_stage_6_ms,
        avg_stage_7_ms,
        vendor_counts,
        equipment_counts,
        failed_sources,
        error_distribution
    )
    SELECT
        DATE_TRUNC('hour', target_hour) as hour_start,
        COUNT(*) as sources_processed,
        SUM(atoms_created) as atoms_created,
        SUM(atoms_failed) as atoms_failed,
        AVG(CASE WHEN status = 'success' THEN 1.0 ELSE 0.0 END) as success_rate,
        AVG(avg_quality_score) as avg_quality_score,
        AVG(quality_pass_rate) as quality_pass_rate,
        AVG(total_duration_ms)::INTEGER as avg_total_duration_ms,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total_duration_ms)::INTEGER as p95_duration_ms,
        AVG(stage_1_acquisition_ms)::INTEGER as avg_stage_1_ms,
        AVG(stage_2_extraction_ms)::INTEGER as avg_stage_2_ms,
        AVG(stage_3_chunking_ms)::INTEGER as avg_stage_3_ms,
        AVG(stage_4_generation_ms)::INTEGER as avg_stage_4_ms,
        AVG(stage_5_validation_ms)::INTEGER as avg_stage_5_ms,
        AVG(stage_6_embedding_ms)::INTEGER as avg_stage_6_ms,
        AVG(stage_7_storage_ms)::INTEGER as avg_stage_7_ms,
        jsonb_object_agg(vendor, vendor_count) as vendor_counts,
        jsonb_object_agg(equipment_type, equipment_count) as equipment_counts,
        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END)::INTEGER as failed_sources,
        jsonb_object_agg(error_stage, error_count) FILTER (WHERE error_stage IS NOT NULL) as error_distribution
    FROM (
        SELECT
            *,
            COUNT(*) FILTER (WHERE vendor IS NOT NULL) OVER (PARTITION BY vendor) as vendor_count,
            COUNT(*) FILTER (WHERE equipment_type IS NOT NULL) OVER (PARTITION BY equipment_type) as equipment_count,
            COUNT(*) FILTER (WHERE error_stage IS NOT NULL) OVER (PARTITION BY error_stage) as error_count
        FROM ingestion_metrics_realtime
        WHERE completed_at >= DATE_TRUNC('hour', target_hour)
          AND completed_at < DATE_TRUNC('hour', target_hour) + INTERVAL '1 hour'
    ) subq
    ON CONFLICT (hour_start) DO UPDATE SET
        sources_processed = EXCLUDED.sources_processed,
        atoms_created = EXCLUDED.atoms_created,
        atoms_failed = EXCLUDED.atoms_failed,
        success_rate = EXCLUDED.success_rate,
        avg_quality_score = EXCLUDED.avg_quality_score,
        quality_pass_rate = EXCLUDED.quality_pass_rate,
        avg_total_duration_ms = EXCLUDED.avg_total_duration_ms,
        p95_duration_ms = EXCLUDED.p95_duration_ms,
        avg_stage_1_ms = EXCLUDED.avg_stage_1_ms,
        avg_stage_2_ms = EXCLUDED.avg_stage_2_ms,
        avg_stage_3_ms = EXCLUDED.avg_stage_3_ms,
        avg_stage_4_ms = EXCLUDED.avg_stage_4_ms,
        avg_stage_5_ms = EXCLUDED.avg_stage_5_ms,
        avg_stage_6_ms = EXCLUDED.avg_stage_6_ms,
        avg_stage_7_ms = EXCLUDED.avg_stage_7_ms,
        vendor_counts = EXCLUDED.vendor_counts,
        equipment_counts = EXCLUDED.equipment_counts,
        failed_sources = EXCLUDED.failed_sources,
        error_distribution = EXCLUDED.error_distribution;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Sample Data for Testing
-- ============================================================================

-- Insert sample realtime record
COMMENT ON TABLE ingestion_metrics_realtime IS
'Tracks every source processed through the 7-stage KB ingestion pipeline.
Use for real-time monitoring and Telegram notifications.';

COMMENT ON TABLE ingestion_metrics_hourly IS
'Hourly aggregates for trend analysis and dashboard queries.
Populated by aggregate_hourly_metrics() function.';

COMMENT ON TABLE ingestion_metrics_daily IS
'Daily rollups for long-term reporting and capacity planning.';

-- ============================================================================
-- Grant Permissions (if using RLS)
-- ============================================================================

-- Grant access to service role
-- ALTER TABLE ingestion_metrics_realtime OWNER TO postgres;
-- ALTER TABLE ingestion_metrics_hourly OWNER TO postgres;
-- ALTER TABLE ingestion_metrics_daily OWNER TO postgres;

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- List all tables created
-- SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE 'ingestion_metrics%';

-- Check table sizes
-- SELECT
--     tablename,
--     pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
-- FROM pg_tables
-- WHERE schemaname = 'public' AND tablename LIKE 'ingestion_metrics%';

-- Test insert into realtime table
-- INSERT INTO ingestion_metrics_realtime (
--     source_url, source_type, source_hash, status,
--     atoms_created, atoms_failed, chunks_processed,
--     avg_quality_score, quality_pass_rate,
--     stage_1_acquisition_ms, stage_2_extraction_ms, stage_3_chunking_ms,
--     stage_4_generation_ms, stage_5_validation_ms, stage_6_embedding_ms,
--     stage_7_storage_ms, total_duration_ms,
--     vendor, equipment_type,
--     started_at, completed_at
-- ) VALUES (
--     'https://example.com/manual.pdf', 'pdf', 'abc123xyz789', 'success',
--     15, 2, 8,
--     0.87, 0.93,
--     1200, 850, 450,
--     2100, 780, 950,
--     340, 6670,
--     'Siemens', 'PLC',
--     NOW() - INTERVAL '10 minutes', NOW()
-- );

-- Query recent ingestions
-- SELECT * FROM ingestion_metrics_realtime ORDER BY completed_at DESC LIMIT 10;

-- Test hourly aggregation
-- SELECT aggregate_hourly_metrics(NOW() - INTERVAL '1 hour');
-- SELECT * FROM ingestion_metrics_hourly ORDER BY hour_start DESC LIMIT 5;

-- ============================================================================
-- TRACEABILITY TABLES (Added for 24/7 Ingestion Pipeline)
-- ============================================================================
-- These tables enable full traceability from atom → source URL → agent executions
-- Part of the 24/7 Knowledge Base Ingestion Pipeline implementation

-- Table 4: Ingestion Sessions
-- ============================================================================
-- Tracks each source URL processing run from start to finish
-- Links atoms to their originating ingestion session
-- Enables queries like "show me all atoms from this PDF"

CREATE TABLE IF NOT EXISTS ingestion_sessions (
    session_id UUID PRIMARY KEY,
    source_url TEXT NOT NULL,
    source_hash VARCHAR(16) NOT NULL,  -- SHA-256 hash (first 16 chars) for deduplication
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'processing', 'success', 'partial', 'failed')),

    -- Results
    atoms_created INTEGER DEFAULT 0 CHECK (atoms_created >= 0),
    atoms_failed INTEGER DEFAULT 0 CHECK (atoms_failed >= 0),

    -- Timing
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,

    -- Error tracking
    error_stage VARCHAR(50),  -- Which stage failed (acquisition, extraction, etc.)
    error_message TEXT,

    -- Ensure completed_at is after started_at
    CHECK (completed_at IS NULL OR completed_at >= started_at),

    -- Ensure source_hash uniqueness (prevent duplicate ingestions)
    UNIQUE(source_hash)
);

-- Indexes for fast session queries
CREATE INDEX IF NOT EXISTS idx_sessions_status
    ON ingestion_sessions(status);

CREATE INDEX IF NOT EXISTS idx_sessions_completed_at
    ON ingestion_sessions(completed_at DESC)
    WHERE completed_at IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_sessions_source_hash
    ON ingestion_sessions(source_hash);

COMMENT ON TABLE ingestion_sessions IS
'Tracks each source URL processing run. Links atoms to their originating ingestion session.
Enables full traceability: atom → session → source URL.';

-- ============================================================================
-- Table 5: Agent Traces
-- ============================================================================
-- Stores execution metadata for each agent involved in ingestion
-- Tracks: AtomBuilder, CitationValidator, QualityChecker, GeminiJudge
-- Enables performance analysis and cost tracking per agent

CREATE TABLE IF NOT EXISTS agent_traces (
    trace_id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES ingestion_sessions(session_id) ON DELETE CASCADE,
    agent_name VARCHAR(100) NOT NULL,

    -- Performance metrics
    duration_ms INTEGER NOT NULL CHECK (duration_ms >= 0),
    tokens_used INTEGER DEFAULT 0 CHECK (tokens_used >= 0),
    cost_usd NUMERIC(10, 6) DEFAULT 0 CHECK (cost_usd >= 0),

    -- Success tracking
    success BOOLEAN NOT NULL,
    error_message TEXT,

    -- Timing
    started_at TIMESTAMPTZ NOT NULL
);

-- Indexes for fast trace queries
CREATE INDEX IF NOT EXISTS idx_traces_session
    ON agent_traces(session_id);

CREATE INDEX IF NOT EXISTS idx_traces_agent_name
    ON agent_traces(agent_name);

CREATE INDEX IF NOT EXISTS idx_traces_started_at
    ON agent_traces(started_at DESC);

-- Composite index for session + agent queries
CREATE INDEX IF NOT EXISTS idx_traces_session_agent
    ON agent_traces(session_id, agent_name);

COMMENT ON TABLE agent_traces IS
'Stores execution metadata for each agent in the ingestion pipeline.
Enables performance analysis, cost tracking, and debugging per agent execution.';

-- ============================================================================
-- Table Modification: Link Atoms to Sessions
-- ============================================================================
-- Add foreign key from knowledge_atoms to ingestion_sessions
-- This enables querying all atoms created in a specific ingestion run

-- Check if column exists first (idempotent)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'knowledge_atoms'
        AND column_name = 'ingestion_session_id'
    ) THEN
        ALTER TABLE knowledge_atoms
            ADD COLUMN ingestion_session_id UUID REFERENCES ingestion_sessions(session_id) ON DELETE SET NULL;

        CREATE INDEX idx_atoms_session ON knowledge_atoms(ingestion_session_id);
    END IF;
END$$;

COMMENT ON COLUMN knowledge_atoms.ingestion_session_id IS
'Links atom to the ingestion session that created it. Enables full traceability.';

-- ============================================================================
-- Table 6: Gap Requests (Autonomous Discovery)
-- ============================================================================
-- Tracks user queries that resulted in Route C (no KB coverage)
-- These become high-priority ingestion targets (gap-driven discovery)

CREATE TABLE IF NOT EXISTS gap_requests (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    query_text TEXT NOT NULL,
    equipment_detected TEXT,  -- manufacturer/model extracted from query
    route VARCHAR(10) NOT NULL CHECK (route IN ('A', 'B', 'C', 'D')),
    confidence FLOAT,
    kb_atoms_found INTEGER DEFAULT 0,

    -- Priority scoring
    request_count INTEGER DEFAULT 1,  -- How many times this gap was requested
    priority_score FLOAT DEFAULT 50.0,  -- Auto-calculated: request_count * 10 + confidence

    -- Ingestion tracking
    ingestion_queued BOOLEAN DEFAULT FALSE,
    ingestion_queued_at TIMESTAMPTZ,
    ingestion_completed BOOLEAN DEFAULT FALSE,

    -- Timestamps
    first_requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Ensure priority_score is valid
    CHECK (priority_score >= 0 AND priority_score <= 100)
);

-- Indexes for fast gap queries
CREATE INDEX IF NOT EXISTS idx_gap_equipment
    ON gap_requests(equipment_detected)
    WHERE equipment_detected IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_gap_priority
    ON gap_requests(priority_score DESC)
    WHERE ingestion_queued = FALSE;

CREATE INDEX IF NOT EXISTS idx_gap_route
    ON gap_requests(route)
    WHERE route = 'C';

COMMENT ON TABLE gap_requests IS
'Tracks Route C queries (no KB coverage). Highest-priority ingestion targets.
Enables gap-driven autonomous discovery.';

-- ============================================================================
-- Table 7: Domain Rate Limits
-- ============================================================================
-- Tracks per-domain request timing to prevent getting blocked

CREATE TABLE IF NOT EXISTS domain_rate_limits (
    domain VARCHAR(255) PRIMARY KEY,
    requests_per_hour INTEGER NOT NULL DEFAULT 10,
    delay_seconds INTEGER NOT NULL DEFAULT 6,  -- Delay between requests
    last_request_at TIMESTAMPTZ,
    total_requests INTEGER DEFAULT 0,
    blocked_until TIMESTAMPTZ  -- If we got rate-limited, wait until this time
);

-- Seed with known manufacturer domains
INSERT INTO domain_rate_limits (domain, requests_per_hour, delay_seconds) VALUES
    ('rockwellautomation.com', 10, 6),
    ('literature.rockwellautomation.com', 10, 6),
    ('siemens.com', 5, 12),
    ('cache.industry.siemens.com', 5, 12),
    ('mitsubishielectric.com', 8, 8),
    ('ab.com', 10, 6),
    ('abb.com', 8, 8),
    ('schneider-electric.com', 8, 8),
    ('omron.com', 10, 6)
ON CONFLICT (domain) DO NOTHING;

COMMENT ON TABLE domain_rate_limits IS
'Per-domain rate limiting config. Prevents getting blocked by manufacturer portals.';

-- ============================================================================
-- Table 8: Ingestion Queue (Persistent JSONL alternative)
-- ============================================================================
-- Database-backed queue (alternative to JSONL file)
-- Enables atomic operations and better concurrency

CREATE TABLE IF NOT EXISTS ingestion_queue (
    id BIGSERIAL PRIMARY KEY,
    source_url TEXT NOT NULL,
    source_hash VARCHAR(16) NOT NULL UNIQUE,  -- Deduplication
    priority INTEGER NOT NULL DEFAULT 50 CHECK (priority >= 0 AND priority <= 100),

    -- Discovery source
    source_type VARCHAR(50) NOT NULL CHECK (source_type IN ('manual', 'gap_request', 'crawler', 'telegram_bot')),
    source_id TEXT,  -- gap_request.id, telegram user_id, etc.

    -- Status tracking
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    retry_count INTEGER DEFAULT 0 CHECK (retry_count >= 0),

    -- Timestamps
    queued_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

-- Indexes for queue operations
CREATE INDEX IF NOT EXISTS idx_queue_status_priority
    ON ingestion_queue(status, priority DESC, queued_at)
    WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS idx_queue_source_hash
    ON ingestion_queue(source_hash);

COMMENT ON TABLE ingestion_queue IS
'Database-backed ingestion queue with deduplication and priority.
Alternative to JSONL file - enables atomic operations and concurrency.';

-- ============================================================================
-- Table 9: Document Validation Results
-- ============================================================================
-- Stores LLM validation scores for ingested documents
-- Filters out marketing PDFs, wrong language, corrupted files

CREATE TABLE IF NOT EXISTS document_validations (
    id BIGSERIAL PRIMARY KEY,
    source_url TEXT NOT NULL,
    source_hash VARCHAR(16) NOT NULL UNIQUE,  -- Enforce deduplication

    -- LLM validation
    is_technical_manual BOOLEAN,
    validation_score INTEGER CHECK (validation_score >= 0 AND validation_score <= 100),
    language_detected VARCHAR(10),
    document_type VARCHAR(50),  -- manual, datasheet, catalog, marketing, etc.

    -- Metadata
    manufacturer_detected TEXT,
    model_detected TEXT,

    -- Validation details
    validation_reason TEXT,
    validated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for validation queries
CREATE INDEX IF NOT EXISTS idx_validation_source_hash
    ON document_validations(source_hash);

CREATE INDEX IF NOT EXISTS idx_validation_score
    ON document_validations(validation_score DESC)
    WHERE is_technical_manual = TRUE;

COMMENT ON TABLE document_validations IS
'LLM validation results for documents before ingestion.
Filters out non-technical content (marketing, wrong language, etc.)';

-- ============================================================================
-- Traceability Query Examples
-- ============================================================================

-- Example 1: Get all atoms from a specific source URL
-- SELECT ka.*
-- FROM knowledge_atoms ka
-- JOIN ingestion_sessions s ON ka.ingestion_session_id = s.session_id
-- WHERE s.source_url = 'https://example.com/manual.pdf';

-- Example 2: Get full trace for an atom (session + agents)
-- SELECT
--     ka.atom_id,
--     ka.title,
--     s.source_url,
--     s.status,
--     t.agent_name,
--     t.duration_ms,
--     t.tokens_used,
--     t.cost_usd,
--     t.success
-- FROM knowledge_atoms ka
-- JOIN ingestion_sessions s ON ka.ingestion_session_id = s.session_id
-- LEFT JOIN agent_traces t ON s.session_id = t.session_id
-- WHERE ka.atom_id = 'your-atom-id'
-- ORDER BY t.started_at;

-- Example 3: Get agent performance summary for last 24h
-- SELECT
--     agent_name,
--     COUNT(*) as executions,
--     AVG(duration_ms) as avg_duration_ms,
--     SUM(tokens_used) as total_tokens,
--     SUM(cost_usd) as total_cost,
--     AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as success_rate
-- FROM agent_traces
-- WHERE started_at > NOW() - INTERVAL '24 hours'
-- GROUP BY agent_name
-- ORDER BY total_cost DESC;

-- Example 4: Get session success rate by hour
-- SELECT
--     DATE_TRUNC('hour', started_at) as hour,
--     COUNT(*) as total_sessions,
--     SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
--     AVG(atoms_created) as avg_atoms_created
-- FROM ingestion_sessions
-- WHERE started_at > NOW() - INTERVAL '24 hours'
-- GROUP BY hour
-- ORDER BY hour DESC;
