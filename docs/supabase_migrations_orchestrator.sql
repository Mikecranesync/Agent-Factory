-- ============================================================================
-- Agent Factory Orchestrator - Supabase Migration
-- ============================================================================
--
-- This migration creates the database tables needed for the GitHub Webhook
-- → Orchestrator automation system.
--
-- Usage:
--   Run this in your Supabase SQL editor or via migration tools
--
-- Tables Created:
--   1. agent_jobs - Job queue for orchestrator processing
--   2. webhook_events - Audit trail of webhook events received
--
-- ============================================================================

-- Job queue for orchestrator
-- Jobs are created by webhook_handler.py and processed by orchestrator.py
CREATE TABLE IF NOT EXISTS agent_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_type TEXT NOT NULL,
  payload JSONB,
  priority INT DEFAULT 5,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  error TEXT,
  assigned_agent TEXT
);

-- Index for efficient job fetching by orchestrator
-- Orchestrator queries: "SELECT * FROM agent_jobs WHERE status = 'pending' ORDER BY priority DESC, created_at LIMIT N"
CREATE INDEX IF NOT EXISTS idx_agent_jobs_pending ON agent_jobs(status, priority DESC, created_at);

-- Webhook audit trail
-- Stores all webhook events received by webhook_handler.py
CREATE TABLE IF NOT EXISTS webhook_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source TEXT NOT NULL,
  event_type TEXT NOT NULL,
  payload JSONB,
  processed BOOLEAN DEFAULT false,
  received_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for finding unprocessed webhook events
CREATE INDEX IF NOT EXISTS idx_webhook_events_unprocessed ON webhook_events(processed, received_at DESC);

-- ============================================================================
-- Optional: Add comments for documentation
-- ============================================================================

COMMENT ON TABLE agent_jobs IS 'Job queue for orchestrator - jobs created by webhooks and processed by orchestrator.py';
COMMENT ON TABLE webhook_events IS 'Audit trail of all webhook events received from GitHub';

COMMENT ON COLUMN agent_jobs.job_type IS 'Type of job: github_push, github_release, github_issue, etc.';
COMMENT ON COLUMN agent_jobs.payload IS 'JSON payload with job details from webhook event';
COMMENT ON COLUMN agent_jobs.priority IS 'Job priority (1-10, higher = more important)';
COMMENT ON COLUMN agent_jobs.status IS 'Job status: pending, running, completed, failed';
COMMENT ON COLUMN agent_jobs.assigned_agent IS 'Which agent is processing/processed this job';

COMMENT ON COLUMN webhook_events.source IS 'Source of webhook: github, manual, etc.';
COMMENT ON COLUMN webhook_events.event_type IS 'GitHub event type: push, release, issues, etc.';
COMMENT ON COLUMN webhook_events.processed IS 'Whether this event has been converted to a job';

-- ============================================================================
-- Example Queries
-- ============================================================================

-- Get pending jobs (what orchestrator does):
-- SELECT * FROM agent_jobs WHERE status = 'pending' ORDER BY priority DESC, created_at LIMIT 10;

-- Get failed jobs:
-- SELECT * FROM agent_jobs WHERE status = 'failed' ORDER BY created_at DESC LIMIT 10;

-- Get unprocessed webhooks:
-- SELECT * FROM webhook_events WHERE processed = false ORDER BY received_at DESC;

-- Get job statistics:
-- SELECT status, COUNT(*) FROM agent_jobs GROUP BY status;
