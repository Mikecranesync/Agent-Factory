-- Rivet Discovery Database Schema
-- Supabase PostgreSQL with Row Level Security (RLS)
--
-- Two-stream architecture:
-- 1. Stream 1: 24/7 autonomous scraping (equipment_manuals table)
-- 2. Stream 2: User query intelligence (diagnostic_sessions table)

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- EQUIPMENT MANUALS TABLE (Stream 1)
-- Stores all discovered equipment manuals with metadata and diagnostic logic
-- ============================================================================

CREATE TABLE equipment_manuals (
    -- Primary identifiers
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    manual_id VARCHAR(255) UNIQUE NOT NULL,  -- e.g., "ABB-ACS880-SERVICE-v2.1"

    -- Metadata
    manufacturer VARCHAR(100) NOT NULL,
    equipment_model VARCHAR(100) NOT NULL,
    equipment_name VARCHAR(255) NOT NULL,
    manual_type VARCHAR(50) NOT NULL,  -- installation, service, troubleshooting, wiring, parts, maintenance, operators, safety
    manual_title TEXT NOT NULL,
    manual_version VARCHAR(50),
    publication_date TIMESTAMP,
    page_count INTEGER,
    language VARCHAR(5) DEFAULT 'en',

    -- Quality scores
    quality_score DECIMAL(3,2) CHECK (quality_score >= 0 AND quality_score <= 1),
    completeness_score DECIMAL(3,2) CHECK (completeness_score >= 0 AND completeness_score <= 1),

    -- Discovery metadata
    source_url TEXT,
    discovered_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_updated TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Raw content (for RAG/vector search)
    raw_content TEXT,
    chunks JSONB,  -- Array of {text, embedding, metadata}

    -- Diagnostic logic (CORE VALUE - this is the secret weapon)
    diagnostic_flows JSONB,  -- Array of diagnostic decision trees

    -- Specs and facts
    specifications JSONB,  -- {voltage: "400V", current: "32A", power: "22kW"}
    error_codes JSONB,  -- {"2210": "Motor overload protection triggered"}
    maintenance_schedule JSONB,
    parts_list JSONB,

    -- File storage
    file_path TEXT,
    file_size_bytes BIGINT,
    file_hash VARCHAR(64),  -- SHA-256 for deduplication

    -- Usage tracking (Stream 2 intelligence)
    view_count INTEGER DEFAULT 0,
    diagnostic_session_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Indexes
    CONSTRAINT unique_file_hash UNIQUE (file_hash)
);

-- Indexes for fast queries
CREATE INDEX idx_manuals_manufacturer ON equipment_manuals(manufacturer);
CREATE INDEX idx_manuals_equipment_model ON equipment_manuals(equipment_model);
CREATE INDEX idx_manuals_manual_type ON equipment_manuals(manual_type);
CREATE INDEX idx_manuals_quality_score ON equipment_manuals(quality_score);
CREATE INDEX idx_manuals_discovered_at ON equipment_manuals(discovered_at DESC);
CREATE INDEX idx_manuals_last_accessed ON equipment_manuals(last_accessed DESC);

-- Full-text search index
CREATE INDEX idx_manuals_search ON equipment_manuals USING GIN(
    to_tsvector('english',
        coalesce(manual_title, '') || ' ' ||
        coalesce(equipment_name, '') || ' ' ||
        coalesce(equipment_model, '')
    )
);

-- JSONB indexes for diagnostic flows and error codes
CREATE INDEX idx_manuals_diagnostic_flows ON equipment_manuals USING GIN(diagnostic_flows);
CREATE INDEX idx_manuals_error_codes ON equipment_manuals USING GIN(error_codes);

-- ============================================================================
-- DIAGNOSTIC SESSIONS TABLE (Stream 2)
-- Logs every diagnostic conversation to learn patterns
-- ============================================================================

CREATE TABLE diagnostic_sessions (
    -- Primary identifiers
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,  -- Hashed for privacy

    -- Initial query
    initial_symptom TEXT NOT NULL,
    equipment_model VARCHAR(100),
    error_code VARCHAR(50),

    -- Diagnostic flow
    steps_taken JSONB,  -- Array of {step, question, answer, timestamp}
    manuals_referenced TEXT[],  -- Array of manual_ids

    -- Outcome
    resolution_found BOOLEAN DEFAULT FALSE,
    root_cause TEXT,
    actions_taken TEXT[],

    -- Session metadata
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    duration_minutes INTEGER,

    -- Learning data
    user_feedback TEXT,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for analytics
CREATE INDEX idx_sessions_user_id ON diagnostic_sessions(user_id);
CREATE INDEX idx_sessions_equipment_model ON diagnostic_sessions(equipment_model);
CREATE INDEX idx_sessions_error_code ON diagnostic_sessions(error_code);
CREATE INDEX idx_sessions_resolution_found ON diagnostic_sessions(resolution_found);
CREATE INDEX idx_sessions_rating ON diagnostic_sessions(rating);
CREATE INDEX idx_sessions_started_at ON diagnostic_sessions(started_at DESC);

-- Full-text search on symptoms
CREATE INDEX idx_sessions_symptom_search ON diagnostic_sessions USING GIN(
    to_tsvector('english', initial_symptom)
);

-- ============================================================================
-- SCRAPER RUNS TABLE
-- Track each scraping execution for monitoring and debugging
-- ============================================================================

CREATE TABLE scraper_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id VARCHAR(255) UNIQUE NOT NULL,

    -- Run metadata
    manufacturers TEXT[],
    mode VARCHAR(50) NOT NULL,  -- automated, test, full_scan
    trigger VARCHAR(50),  -- scheduled, manual, api
    triggered_by VARCHAR(255),  -- user_id or 'system'

    -- Results
    status VARCHAR(50) NOT NULL,  -- running, success, partial, failed
    manuals_found INTEGER DEFAULT 0,
    manuals_high_quality INTEGER DEFAULT 0,
    manuals_needs_review INTEGER DEFAULT 0,
    errors TEXT[],

    -- Execution metadata
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    duration_seconds INTEGER,

    -- GitHub Actions metadata (if applicable)
    github_run_id VARCHAR(255),
    github_run_number INTEGER,

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_scraper_runs_status ON scraper_runs(status);
CREATE INDEX idx_scraper_runs_started_at ON scraper_runs(started_at DESC);

-- ============================================================================
-- QUERY INTELLIGENCE TABLE (Stream 2)
-- Aggregated analytics - which equipment is valuable
-- ============================================================================

CREATE TABLE query_intelligence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Equipment identifier
    manufacturer VARCHAR(100) NOT NULL,
    equipment_model VARCHAR(100) NOT NULL,

    -- Query statistics
    total_queries INTEGER DEFAULT 0,
    unique_users INTEGER DEFAULT 0,
    avg_session_duration_minutes DECIMAL(5,2),
    avg_rating DECIMAL(3,2),
    resolution_rate DECIMAL(3,2),  -- Percentage resolved successfully

    -- Priority score (for Stream 1 prioritization)
    priority_score DECIMAL(5,2),  -- Calculated from queries, ratings, resolutions

    -- Timestamps
    first_queried TIMESTAMP,
    last_queried TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_equipment UNIQUE (manufacturer, equipment_model)
);

CREATE INDEX idx_intelligence_priority ON query_intelligence(priority_score DESC);
CREATE INDEX idx_intelligence_total_queries ON query_intelligence(total_queries DESC);

-- ============================================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================================

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to equipment_manuals
CREATE TRIGGER update_equipment_manuals_updated_at
    BEFORE UPDATE ON equipment_manuals
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Update query intelligence from diagnostic sessions
CREATE OR REPLACE FUNCTION update_query_intelligence()
RETURNS TRIGGER AS $$
BEGIN
    -- Only process completed sessions
    IF NEW.completed_at IS NOT NULL AND OLD.completed_at IS NULL THEN
        INSERT INTO query_intelligence (
            manufacturer,
            equipment_model,
            total_queries,
            unique_users,
            avg_session_duration_minutes,
            avg_rating,
            resolution_rate,
            first_queried,
            last_queried
        )
        VALUES (
            SPLIT_PART(NEW.equipment_model, ' ', 1),  -- Extract manufacturer from model
            NEW.equipment_model,
            1,
            1,
            NEW.duration_minutes,
            NEW.rating,
            CASE WHEN NEW.resolution_found THEN 1.0 ELSE 0.0 END,
            NEW.started_at,
            NEW.started_at
        )
        ON CONFLICT (manufacturer, equipment_model) DO UPDATE SET
            total_queries = query_intelligence.total_queries + 1,
            avg_session_duration_minutes = (
                query_intelligence.avg_session_duration_minutes * query_intelligence.total_queries + NEW.duration_minutes
            ) / (query_intelligence.total_queries + 1),
            avg_rating = CASE
                WHEN NEW.rating IS NOT NULL THEN
                    (COALESCE(query_intelligence.avg_rating, 0) * query_intelligence.total_queries + NEW.rating)
                    / (query_intelligence.total_queries + 1)
                ELSE query_intelligence.avg_rating
            END,
            resolution_rate = (
                query_intelligence.resolution_rate * query_intelligence.total_queries +
                CASE WHEN NEW.resolution_found THEN 1.0 ELSE 0.0 END
            ) / (query_intelligence.total_queries + 1),
            last_queried = NEW.started_at,
            updated_at = NOW();
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_intelligence_from_sessions
    AFTER UPDATE ON diagnostic_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_query_intelligence();

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- Enable multi-tenancy when ready for production
-- ============================================================================

-- Enable RLS (commented out for now - enable when auth is implemented)
-- ALTER TABLE equipment_manuals ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE diagnostic_sessions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE scraper_runs ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE query_intelligence ENABLE ROW LEVEL SECURITY;

-- Public read access to manuals (can restrict later)
-- CREATE POLICY "Public read access to manuals" ON equipment_manuals
--     FOR SELECT USING (true);

-- Users can only see their own diagnostic sessions
-- CREATE POLICY "Users can view own sessions" ON diagnostic_sessions
--     FOR SELECT USING (auth.uid()::text = user_id);

-- ============================================================================
-- INITIAL DATA / SEED
-- ============================================================================

-- Insert initial query intelligence for high-priority equipment
-- (This kickstarts Stream 1 prioritization)
INSERT INTO query_intelligence (manufacturer, equipment_model, total_queries, priority_score, updated_at)
VALUES
    ('ABB', 'ACS880', 0, 10.0, NOW()),
    ('ABB', 'ACS580', 0, 9.0, NOW()),
    ('Siemens', 'S7-1200', 0, 10.0, NOW()),
    ('Rockwell', 'ControlLogix', 0, 9.0, NOW()),
    ('Carrier', '30XA', 0, 8.0, NOW())
ON CONFLICT (manufacturer, equipment_model) DO NOTHING;

-- ============================================================================
-- VIEWS FOR ANALYTICS
-- ============================================================================

-- High-value equipment (for Stream 1 prioritization)
CREATE VIEW high_value_equipment AS
SELECT
    manufacturer,
    equipment_model,
    total_queries,
    resolution_rate,
    priority_score,
    last_queried
FROM query_intelligence
WHERE total_queries > 0
ORDER BY priority_score DESC, total_queries DESC
LIMIT 100;

-- Manual coverage gaps (equipment with queries but no manuals)
CREATE VIEW manual_coverage_gaps AS
SELECT
    qi.manufacturer,
    qi.equipment_model,
    qi.total_queries,
    qi.priority_score,
    COUNT(em.id) as manual_count
FROM query_intelligence qi
LEFT JOIN equipment_manuals em
    ON qi.equipment_model = em.equipment_model
GROUP BY qi.manufacturer, qi.equipment_model, qi.total_queries, qi.priority_score
HAVING COUNT(em.id) = 0 AND qi.total_queries > 0
ORDER BY qi.priority_score DESC;

-- Recent scraper performance
CREATE VIEW scraper_performance AS
SELECT
    DATE(started_at) as date,
    COUNT(*) as runs,
    SUM(manuals_found) as total_manuals,
    AVG(duration_seconds) as avg_duration,
    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_runs
FROM scraper_runs
WHERE started_at > NOW() - INTERVAL '30 days'
GROUP BY DATE(started_at)
ORDER BY date DESC;
