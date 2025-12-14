-- Rivet KB Factory - Postgres Schema Initialization
-- Requires PostgreSQL 16+ with pgvector extension

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Knowledge atoms table with vector embeddings
CREATE TABLE IF NOT EXISTS knowledge_atoms (
    id SERIAL PRIMARY KEY,
    atom_id VARCHAR(255) UNIQUE,
    atom_type VARCHAR(50) NOT NULL,  -- fault, procedure, concept, pattern
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    vendor VARCHAR(100),
    product VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    embedding vector(768),  -- nomic-embed-text dimension
    source_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast vector similarity search
CREATE INDEX IF NOT EXISTS knowledge_atoms_embedding_idx 
ON knowledge_atoms USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Index for filtering by type
CREATE INDEX IF NOT EXISTS knowledge_atoms_type_idx ON knowledge_atoms(atom_type);

-- Index for vendor/product lookups
CREATE INDEX IF NOT EXISTS knowledge_atoms_vendor_idx ON knowledge_atoms(vendor);
CREATE INDEX IF NOT EXISTS knowledge_atoms_product_idx ON knowledge_atoms(product);

-- Source tracking table (optional, for scheduler)
CREATE TABLE IF NOT EXISTS ingestion_sources (
    id SERIAL PRIMARY KEY,
    source_url TEXT UNIQUE NOT NULL,
    source_type VARCHAR(50),  -- pdf, html, api
    vendor VARCHAR(100),
    product VARCHAR(100),
    priority INT DEFAULT 5,
    last_ingested_at TIMESTAMP,
    next_ingest_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',  -- pending, processing, completed, failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Job history for observability
CREATE TABLE IF NOT EXISTS ingestion_jobs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(255) UNIQUE NOT NULL,
    source_url TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'running',  -- running, completed, failed
    atoms_created INT DEFAULT 0,
    atoms_indexed INT DEFAULT 0,
    errors JSONB DEFAULT '[]',
    logs JSONB DEFAULT '[]',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Create update trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_knowledge_atoms_updated_at 
BEFORE UPDATE ON knowledge_atoms 
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Verify pgvector is working
DO $$
BEGIN
    RAISE NOTICE 'pgvector extension installed and ready';
END $$;
