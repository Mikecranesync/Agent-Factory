-- Agent Factory Supervisory Schema for Neon PostgreSQL

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Agent Tasks
CREATE TABLE IF NOT EXISTS agent_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(255) NOT NULL UNIQUE,
    task_type VARCHAR(50) NOT NULL,
    task_name VARCHAR(500) NOT NULL,
    description TEXT,
    repo_scope VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    
    slack_channel VARCHAR(50),
    slack_thread_ts VARCHAR(50),
    requested_by VARCHAR(50),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    result_summary TEXT,
    error_message TEXT,
    artifacts JSONB DEFAULT '[]'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    
    CONSTRAINT valid_status CHECK (status IN ('pending', 'approved', 'running', 'completed', 'failed', 'cancelled'))
);

CREATE INDEX idx_tasks_status ON agent_tasks(status);
CREATE INDEX idx_tasks_created ON agent_tasks(created_at DESC);
CREATE INDEX idx_tasks_channel ON agent_tasks(slack_channel);

-- Agent Checkpoints
CREATE TABLE IF NOT EXISTS agent_checkpoints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES agent_tasks(id) ON DELETE CASCADE,
    agent_id VARCHAR(255) NOT NULL,
    
    checkpoint_type VARCHAR(50) NOT NULL,
    action_description TEXT NOT NULL,
    progress INTEGER DEFAULT 0,
    tokens_used INTEGER DEFAULT 0,
    context_limit INTEGER DEFAULT 200000,
    status VARCHAR(50) NOT NULL,
    elapsed_seconds INTEGER DEFAULT 0,
    
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_checkpoints_agent ON agent_checkpoints(agent_id);
CREATE INDEX idx_checkpoints_created ON agent_checkpoints(created_at DESC);

-- Human Interventions
CREATE TABLE IF NOT EXISTS human_interventions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES agent_tasks(id) ON DELETE CASCADE,
    agent_id VARCHAR(255) NOT NULL,
    
    intervention_type VARCHAR(50) NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    action_details TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_interventions_agent ON human_interventions(agent_id);

-- Task Artifacts
CREATE TABLE IF NOT EXISTS task_artifacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES agent_tasks(id) ON DELETE CASCADE,
    agent_id VARCHAR(255) NOT NULL,
    
    artifact_type VARCHAR(50) NOT NULL,
    artifact_name VARCHAR(255) NOT NULL,
    artifact_url TEXT,
    artifact_content TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_artifacts_agent ON task_artifacts(agent_id);

-- Auto-update timestamp trigger
CREATE OR REPLACE FUNCTION update_timestamp() RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tasks_updated BEFORE UPDATE ON agent_tasks
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();
