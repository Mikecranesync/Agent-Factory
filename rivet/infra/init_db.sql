-- Rivet Industrial KB Factory - Database Schema
-- PostgreSQL 16 with pgvector extension

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Knowledge atoms table
CREATE TABLE IF NOT EXISTS knowledge_atoms (
    atom_id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Core fields
    atom_type VARCHAR(50) NOT NULL CHECK (atom_type IN ('fault', 'pattern', 'concept', 'procedure')),
    vendor VARCHAR(100),
    product VARCHAR(100),

    -- Content
    title VARCHAR(500) NOT NULL,
    summary TEXT NOT NULL,
    content TEXT NOT NULL,

    -- Fault-specific fields
    code VARCHAR(50),
    symptoms TEXT[],
    causes TEXT[],
    fixes TEXT[],

    -- Pattern-specific fields
    pattern_type VARCHAR(100),
    prerequisites TEXT[],
    steps TEXT[],

    -- Metadata
    keywords TEXT[],
    difficulty VARCHAR(20) CHECK (difficulty IN ('beginner', 'intermediate', 'advanced') OR difficulty IS NULL),
    source_url TEXT,
    source_pages VARCHAR(100),

    -- Vector embedding for semantic search
    embedding vector(768)  -- nomic-embed-text dimension
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_atoms_type ON knowledge_atoms(atom_type);
CREATE INDEX IF NOT EXISTS idx_atoms_vendor ON knowledge_atoms(vendor);
CREATE INDEX IF NOT EXISTS idx_atoms_product ON knowledge_atoms(product);
CREATE INDEX IF NOT EXISTS idx_atoms_difficulty ON knowledge_atoms(difficulty);
CREATE INDEX IF NOT EXISTS idx_atoms_keywords ON knowledge_atoms USING GIN(keywords);

-- Vector similarity index (HNSW for fast nearest-neighbor search)
CREATE INDEX IF NOT EXISTS idx_atoms_embedding ON knowledge_atoms
USING hnsw (embedding vector_cosine_ops);

-- Full-text search index
CREATE INDEX IF NOT EXISTS idx_atoms_fulltext ON knowledge_atoms
USING GIN(to_tsvector('english', title || ' ' || summary || ' ' || content));

-- Ingestion jobs tracking table (optional - for future use)
CREATE TABLE IF NOT EXISTS ingestion_jobs (
    job_id UUID PRIMARY KEY,
    source_url TEXT NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    atoms_extracted INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_jobs_status ON ingestion_jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created ON ingestion_jobs(created_at);

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_atoms_updated_at BEFORE UPDATE ON knowledge_atoms
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO rivet;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO rivet;
