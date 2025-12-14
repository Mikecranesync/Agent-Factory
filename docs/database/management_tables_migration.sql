-- =============================================================================
-- MANAGEMENT DASHBOARD TABLES
-- =============================================================================
-- Database migrations for CEO/Executive dashboard functionality via Telegram bot
--
-- Tables created:
--   1. video_approval_queue - Videos awaiting CEO approval before publishing
--   2. agent_status - Real-time tracking of all 24 agents
--   3. alert_history - Log of all alerts sent to management
--
-- Usage:
--   Run against Neon, Supabase, or Railway database
--
--   Neon:
--     psql "$NEON_DB_URL" < management_tables_migration.sql
--
--   Supabase:
--     psql "postgresql://postgres:$SUPABASE_DB_PASSWORD@db.$SUPABASE_PROJECT_ID.supabase.co:5432/postgres" < management_tables_migration.sql
--
--   Railway:
--     psql "$RAILWAY_DB_URL" < management_tables_migration.sql
--
-- =============================================================================

-- Drop tables if they exist (for clean migration)
DROP TABLE IF EXISTS alert_history CASCADE;
DROP TABLE IF EXISTS agent_status CASCADE;
DROP TABLE IF EXISTS video_approval_queue CASCADE;

-- =============================================================================
-- TABLE: video_approval_queue
-- =============================================================================
-- Stores videos awaiting CEO/management approval before publishing to YouTube
--
-- Workflow:
--   1. VideoAssemblyAgent produces video → inserts row (status=pending)
--   2. CEO receives Telegram notification → views /pending
--   3. CEO approves (/approve <id>) or rejects (/reject <id> <reason>)
--   4. If approved → YouTubeUploaderAgent publishes
--   5. If rejected → VideoQualityReviewerAgent re-produces with feedback
--
-- Priority levels:
--   0: Normal
--   1: High (trending topic, time-sensitive)
--   2: Urgent (breaking news, critical fix)
--   -1: Low priority (evergreen content)
-- =============================================================================

CREATE TABLE video_approval_queue (
    -- Primary key
    video_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign key to video_scripts table (script used for this video)
    script_id UUID REFERENCES video_scripts(script_id) ON DELETE SET NULL,

    -- File paths
    video_path TEXT NOT NULL,  -- Local or S3 path to rendered video file
    thumbnail_path TEXT,       -- Path to thumbnail image
    audio_path TEXT,          -- Path to voice narration file

    -- Video metadata
    metadata JSONB DEFAULT '{}',  -- Title, description, tags, duration, etc.

    -- Approval workflow
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'published')),
    priority INTEGER DEFAULT 0,  -- -1 (low), 0 (normal), 1 (high), 2 (urgent)

    -- Timestamps
    submitted_at TIMESTAMP DEFAULT NOW(),
    reviewed_at TIMESTAMP,
    published_at TIMESTAMP,

    -- Review details
    reviewed_by VARCHAR(100),  -- Telegram user_id or 'auto' for autonomous approval
    review_notes TEXT,         -- CEO feedback or rejection reason

    -- YouTube publish details
    youtube_video_id VARCHAR(20),  -- YouTube video ID after publishing
    youtube_url TEXT,              -- Full YouTube URL

    -- Additional metadata
    quality_score DECIMAL(3, 2),  -- Quality score from VideoQualityReviewerAgent (0.00-1.00)
    estimated_views INTEGER,       -- Predicted views from AnalyticsAgent
    target_keywords TEXT[],        -- SEO keywords for discoverability

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for video_approval_queue
CREATE INDEX idx_video_approval_status ON video_approval_queue(status);
CREATE INDEX idx_video_approval_priority ON video_approval_queue(priority DESC);
CREATE INDEX idx_video_approval_submitted ON video_approval_queue(submitted_at DESC);
CREATE INDEX idx_video_approval_reviewed_by ON video_approval_queue(reviewed_by);

-- Comments for documentation
COMMENT ON TABLE video_approval_queue IS 'Videos awaiting CEO approval before YouTube publishing';
COMMENT ON COLUMN video_approval_queue.priority IS 'Priority: -1 (low), 0 (normal), 1 (high), 2 (urgent)';
COMMENT ON COLUMN video_approval_queue.quality_score IS 'Quality score from VideoQualityReviewerAgent (0.00-1.00)';

-- =============================================================================
-- TABLE: agent_status
-- =============================================================================
-- Real-time tracking of all 24 agents (health, uptime, errors, performance)
--
-- Updated by:
--   - Each agent on startup (status=running)
--   - Each agent on completion (last_run_at, success_count++)
--   - Each agent on error (error_count++, last_error)
--   - Management commands (/pause, /resume, /restart)
--
-- Used by:
--   - /status command (overall health)
--   - /agents command (detailed status per agent)
--   - Alert system (detect failures, trigger notifications)
-- =============================================================================

CREATE TABLE agent_status (
    -- Primary key
    agent_name VARCHAR(100) PRIMARY KEY,

    -- Agent classification
    team VARCHAR(50),  -- Executive, Research, Content, Media, Engagement, Orchestration

    -- Current status
    status VARCHAR(20) DEFAULT 'stopped' CHECK (status IN ('running', 'paused', 'error', 'stopped')),

    -- Execution tracking
    last_run_at TIMESTAMP,
    last_success_at TIMESTAMP,
    last_error_at TIMESTAMP,
    last_error TEXT,

    -- Counters
    run_count INTEGER DEFAULT 0,        -- Total executions
    success_count INTEGER DEFAULT 0,    -- Successful completions
    error_count INTEGER DEFAULT 0,      -- Failed executions
    uptime_seconds INTEGER DEFAULT 0,   -- Total uptime (cumulative)

    -- Performance metrics
    avg_execution_time_seconds DECIMAL(10, 2),  -- Average time per run
    last_execution_time_seconds DECIMAL(10, 2), -- Last run duration

    -- Resource usage (optional)
    memory_usage_mb INTEGER,      -- Current memory usage
    cpu_usage_percent DECIMAL(5, 2),  -- Current CPU usage

    -- Configuration
    enabled BOOLEAN DEFAULT true,  -- Can be disabled by management
    auto_restart BOOLEAN DEFAULT true,  -- Auto-restart on error?

    -- Metadata
    metadata JSONB DEFAULT '{}',  -- Agent-specific config, logs, etc.

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for agent_status
CREATE INDEX idx_agent_status_status ON agent_status(status);
CREATE INDEX idx_agent_status_team ON agent_status(team);
CREATE INDEX idx_agent_status_last_run ON agent_status(last_run_at DESC);
CREATE INDEX idx_agent_status_enabled ON agent_status(enabled);

-- Comments
COMMENT ON TABLE agent_status IS 'Real-time tracking of all 24 agents (health, uptime, performance)';
COMMENT ON COLUMN agent_status.status IS 'running, paused, error, stopped';
COMMENT ON COLUMN agent_status.uptime_seconds IS 'Cumulative uptime (sum of all run durations)';

-- =============================================================================
-- TABLE: alert_history
-- =============================================================================
-- Log of all alerts sent to CEO/management via Telegram
--
-- Alert types:
--   - error: Critical errors requiring immediate attention
--   - warning: Non-critical issues that may need action
--   - info: Informational notifications
--   - milestone: Celebrate achievements (1K subs, $100 revenue, etc.)
--   - approval_needed: Videos awaiting approval
--   - budget: Cost warnings
--
-- Severity levels:
--   - critical: Immediate action required (service down, security breach)
--   - high: Important but not urgent (agent failed 3x, budget at 80%)
--   - medium: Moderate importance (approval queue > 5, new subscriber milestone)
--   - low: Nice to know (daily report sent, backup completed)
-- =============================================================================

CREATE TABLE alert_history (
    -- Primary key
    alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Alert classification
    alert_type VARCHAR(50) NOT NULL,  -- error, warning, info, milestone, approval_needed, budget
    severity VARCHAR(20) DEFAULT 'medium' CHECK (severity IN ('critical', 'high', 'medium', 'low')),

    -- Alert content
    title VARCHAR(200) NOT NULL,  -- Short title for notification
    message TEXT NOT NULL,        -- Full message sent via Telegram
    metadata JSONB DEFAULT '{}',  -- Additional context (agent_name, video_id, error_details, etc.)

    -- Delivery tracking
    sent_at TIMESTAMP DEFAULT NOW(),
    delivered_at TIMESTAMP,  -- When Telegram confirmed delivery
    read_at TIMESTAMP,       -- When user opened/acknowledged (if tracked)

    -- Acknowledgment
    acknowledged_at TIMESTAMP,
    acknowledged_by VARCHAR(100),  -- Telegram user_id
    acknowledgment_notes TEXT,     -- CEO response or action taken

    -- Action tracking
    action_required BOOLEAN DEFAULT false,  -- Does this need CEO action?
    action_taken TEXT,                      -- What action was taken (if any)
    resolved_at TIMESTAMP,                  -- When issue was resolved

    -- Related entities
    related_agent VARCHAR(100),  -- Agent that triggered alert (if applicable)
    related_video_id UUID,       -- Video ID (if approval_needed)
    related_error_id UUID,       -- Error log ID (if error alert)

    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for alert_history
CREATE INDEX idx_alert_history_type ON alert_history(alert_type);
CREATE INDEX idx_alert_history_severity ON alert_history(severity);
CREATE INDEX idx_alert_history_sent ON alert_history(sent_at DESC);
CREATE INDEX idx_alert_history_acknowledged ON alert_history(acknowledged_at);
CREATE INDEX idx_alert_history_action_required ON alert_history(action_required);
CREATE INDEX idx_alert_history_related_agent ON alert_history(related_agent);

-- Comments
COMMENT ON TABLE alert_history IS 'Log of all alerts sent to CEO/management via Telegram';
COMMENT ON COLUMN alert_history.alert_type IS 'error, warning, info, milestone, approval_needed, budget';
COMMENT ON COLUMN alert_history.severity IS 'critical, high, medium, low';
COMMENT ON COLUMN alert_history.action_required IS 'Does this alert require CEO action?';

-- =============================================================================
-- INITIAL DATA: Populate agent_status with all 24 agents
-- =============================================================================

INSERT INTO agent_status (agent_name, team, status) VALUES
    -- Executive Team (2)
    ('AICEOAgent', 'Executive', 'stopped'),
    ('AIChiefOfStaffAgent', 'Executive', 'stopped'),

    -- Research & Knowledge Team (6)
    ('ResearchAgent', 'Research', 'stopped'),
    ('AtomBuilderAgent', 'Research', 'stopped'),
    ('AtomLibrarianAgent', 'Research', 'stopped'),
    ('QualityCheckerAgent', 'Research', 'stopped'),
    ('OEMPDFScraperAgent', 'Research', 'stopped'),
    ('AtomBuilderFromPDF', 'Research', 'stopped'),

    -- Content Production Team (8)
    ('MasterCurriculumAgent', 'Content', 'stopped'),
    ('ContentStrategyAgent', 'Content', 'stopped'),
    ('ScriptwriterAgent', 'Content', 'stopped'),
    ('SEOAgent', 'Content', 'stopped'),
    ('ThumbnailAgent', 'Content', 'stopped'),
    ('ContentCuratorAgent', 'Content', 'stopped'),
    ('TrendScoutAgent', 'Content', 'stopped'),
    ('VideoQualityReviewerAgent', 'Content', 'stopped'),

    -- Media & Publishing Team (4)
    ('VoiceProductionAgent', 'Media', 'stopped'),
    ('VideoAssemblyAgent', 'Media', 'stopped'),
    ('PublishingStrategyAgent', 'Media', 'stopped'),
    ('YouTubeUploaderAgent', 'Media', 'stopped'),

    -- Engagement & Analytics Team (3)
    ('CommunityAgent', 'Engagement', 'stopped'),
    ('AnalyticsAgent', 'Engagement', 'stopped'),
    ('SocialAmplifierAgent', 'Engagement', 'stopped'),

    -- Orchestration (1)
    ('MasterOrchestratorAgent', 'Orchestration', 'stopped')
ON CONFLICT (agent_name) DO NOTHING;  -- Idempotent (safe to re-run)

-- =============================================================================
-- SAMPLE ALERT (for testing)
-- =============================================================================

INSERT INTO alert_history (
    alert_type,
    severity,
    title,
    message,
    metadata,
    action_required
) VALUES (
    'info',
    'low',
    '✅ Management Dashboard Deployed',
    'CEO management dashboard successfully deployed!

Available commands:
- /status - System health
- /agents - Agent status
- /metrics - Performance KPIs
- /pending - Videos awaiting approval

All 24 agents ready for production.',
    '{"deployment_time": "2025-12-14", "version": "1.0.0"}',
    false
);

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

-- Verify tables created
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('video_approval_queue', 'agent_status', 'alert_history')
ORDER BY table_name;

-- Verify agent_status populated
SELECT team, COUNT(*) as agent_count
FROM agent_status
GROUP BY team
ORDER BY team;

-- Expected output:
--   Content        8
--   Engagement     3
--   Executive      2
--   Media          4
--   Orchestration  1
--   Research       6

-- Verify initial alert
SELECT alert_type, title, sent_at
FROM alert_history
ORDER BY sent_at DESC
LIMIT 1;

-- =============================================================================
-- MIGRATION COMPLETE
-- =============================================================================

-- Success message
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=============================================================================';
    RAISE NOTICE 'MIGRATION COMPLETE - Management Dashboard Tables Created';
    RAISE NOTICE '=============================================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Tables created:';
    RAISE NOTICE '  ✅ video_approval_queue - Videos awaiting CEO approval';
    RAISE NOTICE '  ✅ agent_status - Real-time agent tracking (24 agents)';
    RAISE NOTICE '  ✅ alert_history - Alert log';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '  1. Register management_handlers.py in Telegram bot';
    RAISE NOTICE '  2. Deploy bot with new commands (/status, /agents, /metrics, etc.)';
    RAISE NOTICE '  3. Test commands via Telegram';
    RAISE NOTICE '';
    RAISE NOTICE 'Telegram Commands Available:';
    RAISE NOTICE '  /status - Overall system health';
    RAISE NOTICE '  /agents - List all 24 agents';
    RAISE NOTICE '  /metrics - Performance KPIs';
    RAISE NOTICE '  /pending - Videos awaiting approval';
    RAISE NOTICE '  /approve <id> - Approve video';
    RAISE NOTICE '  /reject <id> <reason> - Reject with feedback';
    RAISE NOTICE '  /daily - Daily KPI summary';
    RAISE NOTICE '  /weekly - Weekly report';
    RAISE NOTICE '  /monthly - Monthly business metrics';
    RAISE NOTICE '  /config - View configuration';
    RAISE NOTICE '';
    RAISE NOTICE '=============================================================================';
    RAISE NOTICE '';
END $$;
