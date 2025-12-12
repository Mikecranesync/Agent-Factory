-- ============================================================================
-- DEPLOY KNOWLEDGE ATOMS SCHEMA - PRODUCTION
-- ============================================================================
-- CRITICAL: This drops existing knowledge_atoms table and recreates it
-- Run this in Supabase SQL Editor: https://app.supabase.com/project/_/sql
-- ============================================================================

-- Drop existing table (if it has wrong schema)
DROP TABLE IF EXISTS knowledge_atoms CASCADE;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ============================================================================
-- KNOWLEDGE ATOMS TABLE
-- ============================================================================

CREATE TABLE knowledge_atoms (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Core identification
    atom_id TEXT UNIQUE NOT NULL,
    atom_type TEXT NOT NULL CHECK (
        atom_type IN ('concept', 'procedure', 'specification', 'pattern', 'fault', 'reference')
    ),

    -- Content (optimally chunked for retrieval)
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    content TEXT NOT NULL,

    -- Metadata for filtering
    manufacturer TEXT NOT NULL,
    product_family TEXT,
    product_version TEXT,

    -- Learning metadata
    difficulty TEXT NOT NULL CHECK (
        difficulty IN ('beginner', 'intermediate', 'advanced', 'expert')
    ),
    prerequisites TEXT[] DEFAULT ARRAY[]::TEXT[],
    related_atoms TEXT[] DEFAULT ARRAY[]::TEXT[],

    -- Citations and sources
    source_document TEXT NOT NULL,
    source_pages INTEGER[] NOT NULL,
    source_url TEXT,

    -- Quality and safety
    quality_score FLOAT DEFAULT 1.0 CHECK (
        quality_score >= 0.0 AND quality_score <= 1.0
    ),
    safety_level TEXT DEFAULT 'info' CHECK (
        safety_level IN ('info', 'caution', 'warning', 'danger')
    ),
    safety_notes TEXT,

    -- Search optimization
    keywords TEXT[] DEFAULT ARRAY[]::TEXT[],

    -- Vector embedding (1536 dimensions from OpenAI text-embedding-3-small)
    embedding vector(1536),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_validated_at TIMESTAMPTZ
);

-- ============================================================================
-- INDEXES FOR FAST QUERIES
-- ============================================================================

CREATE INDEX idx_knowledge_atoms_atom_id ON knowledge_atoms(atom_id);
CREATE INDEX idx_knowledge_atoms_type ON knowledge_atoms(atom_type);
CREATE INDEX idx_knowledge_atoms_manufacturer ON knowledge_atoms(manufacturer);
CREATE INDEX idx_knowledge_atoms_product ON knowledge_atoms(product_family);
CREATE INDEX idx_knowledge_atoms_difficulty ON knowledge_atoms(difficulty);

-- Combined filter (manufacturer + product + type)
CREATE INDEX idx_knowledge_atoms_mfr_product_type
ON knowledge_atoms(manufacturer, product_family, atom_type);

-- Full-text search on content
CREATE INDEX idx_knowledge_atoms_content_fts
ON knowledge_atoms USING GIN (to_tsvector('english', title || ' ' || summary || ' ' || content));

-- Keyword search
CREATE INDEX idx_knowledge_atoms_keywords
ON knowledge_atoms USING GIN (keywords);

-- CRITICAL: Vector similarity search (HNSW)
CREATE INDEX idx_knowledge_atoms_embedding
ON knowledge_atoms USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- ============================================================================
-- FUNCTIONS FOR SEARCH
-- ============================================================================

-- Semantic search (vector similarity)
CREATE OR REPLACE FUNCTION search_atoms_by_embedding(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    atom_id text,
    title text,
    summary text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        ka.atom_id,
        ka.title,
        ka.summary,
        1 - (ka.embedding <=> query_embedding) as similarity
    FROM knowledge_atoms ka
    WHERE 1 - (ka.embedding <=> query_embedding) > match_threshold
    ORDER BY ka.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Hybrid search (vector + text)
CREATE OR REPLACE FUNCTION search_atoms_hybrid(
    query_embedding vector(1536),
    query_text text,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    atom_id text,
    title text,
    summary text,
    vector_score float,
    text_rank float,
    combined_score float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH vector_search AS (
        SELECT
            ka.atom_id,
            ka.title,
            ka.summary,
            1 - (ka.embedding <=> query_embedding) as similarity
        FROM knowledge_atoms ka
        ORDER BY ka.embedding <=> query_embedding
        LIMIT match_count * 3
    ),
    text_search AS (
        SELECT
            ka.atom_id,
            ts_rank(
                to_tsvector('english', ka.title || ' ' || ka.summary || ' ' || ka.content),
                plainto_tsquery('english', query_text)
            ) as rank
        FROM knowledge_atoms ka
        WHERE to_tsvector('english', ka.title || ' ' || ka.summary || ' ' || ka.content)
            @@ plainto_tsquery('english', query_text)
    )
    SELECT
        vs.atom_id,
        vs.title,
        vs.summary,
        vs.similarity as vector_score,
        COALESCE(ts.rank, 0) as text_rank,
        (vs.similarity * 0.7 + COALESCE(ts.rank, 0) * 0.3) as combined_score
    FROM vector_search vs
    LEFT JOIN text_search ts ON vs.atom_id = ts.atom_id
    ORDER BY combined_score DESC
    LIMIT match_count;
END;
$$;

-- Get related atoms (via prerequisites/related_atoms)
CREATE OR REPLACE FUNCTION get_related_atoms(
    source_atom_id text,
    max_depth int DEFAULT 2
)
RETURNS TABLE (
    atom_id text,
    title text,
    relation_type text,
    depth int
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE atom_graph AS (
        SELECT
            ka.atom_id,
            ka.title,
            'prerequisite'::text as relation_type,
            1 as depth
        FROM knowledge_atoms ka
        WHERE ka.atom_id = ANY(
            SELECT unnest(prerequisites)
            FROM knowledge_atoms
            WHERE knowledge_atoms.atom_id = source_atom_id
        )

        UNION

        SELECT
            ka.atom_id,
            ka.title,
            'related'::text as relation_type,
            1 as depth
        FROM knowledge_atoms ka
        WHERE ka.atom_id = ANY(
            SELECT unnest(related_atoms)
            FROM knowledge_atoms
            WHERE knowledge_atoms.atom_id = source_atom_id
        )

        UNION

        SELECT
            ka.atom_id,
            ka.title,
            ag.relation_type,
            ag.depth + 1
        FROM atom_graph ag
        JOIN knowledge_atoms ka ON ka.atom_id = ANY(
            SELECT unnest(ka2.prerequisites || ka2.related_atoms)
            FROM knowledge_atoms ka2
            WHERE ka2.atom_id = ag.atom_id
        )
        WHERE ag.depth < max_depth
    )
    SELECT DISTINCT * FROM atom_graph
    ORDER BY depth, atom_id;
END;
$$;

-- ============================================================================
-- ROW-LEVEL SECURITY
-- ============================================================================

ALTER TABLE knowledge_atoms DISABLE ROW LEVEL SECURITY;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE knowledge_atoms IS
'Knowledge atoms from OEM PLC manuals with vector embeddings for semantic search';

COMMENT ON COLUMN knowledge_atoms.atom_id IS
'Unique identifier: manufacturer:product:topic-slug';

COMMENT ON COLUMN knowledge_atoms.embedding IS
'1536-dimensional vector from OpenAI text-embedding-3-small';

COMMENT ON COLUMN knowledge_atoms.content IS
'Full explanation (200-1000 words) optimally chunked for retrieval';

-- ============================================================================
-- DONE
-- ============================================================================
SELECT 'Schema deployed successfully!' as result;
