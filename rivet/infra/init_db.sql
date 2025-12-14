-- Initialize Rivet KB Factory Database
-- Run this manually if auto-schema creation fails

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Knowledge Atoms table
CREATE TABLE IF NOT EXISTS knowledge_atoms (
    id SERIAL PRIMARY KEY,
    atom_type VARCHAR(50),
    vendor VARCHAR(100),
    product VARCHAR(100),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    keywords TEXT[],
    source_url TEXT,
    source_type VARCHAR(50),
    metadata JSONB,
    embedding vector(768),  -- nomic-embed-text produces 768-dim vectors
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for fast search
CREATE INDEX IF NOT EXISTS atoms_type_idx ON knowledge_atoms(atom_type);
CREATE INDEX IF NOT EXISTS atoms_vendor_idx ON knowledge_atoms(vendor);
CREATE INDEX IF NOT EXISTS atoms_created_idx ON knowledge_atoms(created_at DESC);

-- Vector similarity search index (IVFFlat)
CREATE INDEX IF NOT EXISTS atoms_embedding_idx 
ON knowledge_atoms USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Sample query: Find similar atoms
-- SELECT title, content, 1 - (embedding <=> '[0.1, 0.2, ...]'::vector) AS similarity
-- FROM knowledge_atoms
-- ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector
-- LIMIT 10;

COMMENT ON TABLE knowledge_atoms IS 'Industrial maintenance knowledge base atoms with vector embeddings';
