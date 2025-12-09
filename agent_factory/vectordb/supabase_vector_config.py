"""
Supabase + pgvector Configuration for Knowledge Atoms

Based on Part 4 of Knowledge Atom Standard v1.0.
Optimized for industrial maintenance knowledge retrieval using PostgreSQL + pgvector.

ARCHITECTURE:
- PostgreSQL database with pgvector extension
- Same metadata structure as Pinecone (for easy migration)
- Industry vertical partitioning via table columns (not separate tables)
- Cost: $0-25/month during development, scales to $80-120/month in production
"""

from typing import Dict, List, Any, Literal
from pydantic import BaseModel, Field


VectorDBProvider = Literal["pgvector", "pinecone", "qdrant"]


class SupabaseVectorConfig(BaseModel):
    """
    Supabase + pgvector configuration for Knowledge Atoms.

    PURPOSE:
        Defines table structure, indexes, and metadata filtering.
        Based on Knowledge Atom Standard Part 4 (Vector DB schema).
        Uses pgvector extension for similarity search.

    WHAT THIS CONTAINS:
        - table_name: PostgreSQL table name
        - dimension: Vector dimension (OpenAI text-embedding-3-large = 3072)
        - distance_metric: Distance metric (cosine for semantic similarity)
        - index_type: pgvector index type (ivfflat or hnsw)
        - metadata_columns: Filterable metadata fields (indexed)

    PLC ANALOGY:
        Like industrial equipment database schema:
        - table_name = Database table
        - industry_vertical column = Data partition (by industry)
        - metadata_columns = Indexed fields for fast queries

    COST COMPARISON (vs Pinecone):
        - Free tier: $0/month (500MB, ~10K atoms)
        - Pro tier: $25/month (8GB, ~100K atoms)
        - Production: $80-120/month (2XL instance, 500K+ atoms)
        - Pinecone: $50-500+/month minimum
    """

    # Database connection (from Supabase dashboard)
    provider: VectorDBProvider = Field(
        default="pgvector",
        description="Vector database provider"
    )

    supabase_url: str = Field(
        default="",  # User will set via environment variable
        description="Supabase project URL (e.g., https://xxxxx.supabase.co)"
    )

    supabase_key: str = Field(
        default="",  # User will set via environment variable
        description="Supabase service role key (for admin access)"
    )

    # Table configuration
    table_name: str = Field(
        default="knowledge_atoms",
        description="PostgreSQL table name for storing Knowledge Atoms"
    )

    # Vector configuration
    dimension: int = Field(
        default=3072,
        description="Vector dimension (OpenAI text-embedding-3-large)"
    )

    distance_metric: str = Field(
        default="cosine",
        description="Distance metric for similarity search (cosine, l2, inner_product)"
    )

    # Index configuration (pgvector)
    index_type: str = Field(
        default="hnsw",
        description="pgvector index type: 'ivfflat' (faster insert) or 'hnsw' (faster search)"
    )

    index_lists: int = Field(
        default=100,
        description="Number of lists for IVFFlat index (ignored for HNSW)"
    )

    hnsw_m: int = Field(
        default=16,
        description="HNSW M parameter (connections per layer, higher = better recall)"
    )

    hnsw_ef_construction: int = Field(
        default=64,
        description="HNSW ef_construction parameter (higher = better index quality)"
    )

    # Industry vertical partitioning (column-based, not namespace)
    industry_verticals: List[str] = Field(
        default=[
            "hvac",
            "manufacturing",
            "pumping",
            "power_generation",
            "water_treatment",
            "food_beverage",
            "mining",
            "oil_gas",
            "aerospace",
            "automotive",
            "marine"
        ],
        description="Industry vertical values (stored in 'industry_vertical' column)"
    )

    # Metadata filtering fields (indexed columns)
    metadata_indexed_columns: List[str] = Field(
        default=[
            "source_tier",
            "manufacturer",
            "error_code",
            "product_family",
            "confidence_score",
            "status",
            "component_type",
            "industry_vertical",
            "date_created",
            "date_modified",
            "atom_type",
            "severity"
        ],
        description="Metadata columns with indexes for fast filtering"
    )

    def get_table_schema_sql(self) -> str:
        """
        Get SQL DDL statement to create knowledge_atoms table.

        PURPOSE:
            Generates PostgreSQL table creation SQL with:
            - Vector column (pgvector extension)
            - Metadata columns (indexed for filtering)
            - Constraints and defaults

        RETURNS:
            SQL DDL statement as string

        EXAMPLE:
            >>> config = SupabaseVectorConfig()
            >>> sql = config.get_table_schema_sql()
            >>> # Execute in Supabase SQL editor
        """
        return f"""
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create knowledge_atoms table
CREATE TABLE IF NOT EXISTS {self.table_name} (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Atom metadata (from Knowledge Atom Standard)
    atom_id TEXT UNIQUE NOT NULL,
    atom_type TEXT NOT NULL CHECK (atom_type IN (
        'error_code', 'component_spec', 'procedure',
        'troubleshooting_tip', 'safety_requirement',
        'wiring_diagram', 'maintenance_schedule'
    )),

    -- Core content
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    keywords TEXT[] NOT NULL,

    -- Context
    manufacturer TEXT,
    product_family TEXT,
    error_code TEXT,
    component_type TEXT,
    industry_vertical TEXT CHECK (industry_vertical IN (
        'hvac', 'manufacturing', 'pumping', 'power_generation',
        'water_treatment', 'food_beverage', 'mining', 'oil_gas',
        'aerospace', 'automotive', 'marine'
    )),

    -- Quality metrics
    source_tier TEXT CHECK (source_tier IN (
        'manufacturer_official', 'stack_overflow', 'official_forum',
        'reddit', 'blog', 'anecdotal'
    )),
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    status TEXT CHECK (status IN ('draft', 'validated', 'published', 'archived')),
    severity TEXT CHECK (severity IN ('critical', 'high', 'medium', 'low')),

    -- Timestamps
    date_created TIMESTAMPTZ DEFAULT NOW(),
    date_modified TIMESTAMPTZ DEFAULT NOW(),

    -- Vector embedding (pgvector)
    embedding vector({self.dimension}),

    -- Full atom data (JSONB for flexibility)
    atom_data JSONB NOT NULL,

    -- Integrity hash
    integrity_hash TEXT,

    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for fast filtering (metadata)
CREATE INDEX IF NOT EXISTS idx_atoms_atom_type ON {self.table_name}(atom_type);
CREATE INDEX IF NOT EXISTS idx_atoms_manufacturer ON {self.table_name}(manufacturer);
CREATE INDEX IF NOT EXISTS idx_atoms_product_family ON {self.table_name}(product_family);
CREATE INDEX IF NOT EXISTS idx_atoms_error_code ON {self.table_name}(error_code);
CREATE INDEX IF NOT EXISTS idx_atoms_industry_vertical ON {self.table_name}(industry_vertical);
CREATE INDEX IF NOT EXISTS idx_atoms_source_tier ON {self.table_name}(source_tier);
CREATE INDEX IF NOT EXISTS idx_atoms_confidence_score ON {self.table_name}(confidence_score);
CREATE INDEX IF NOT EXISTS idx_atoms_status ON {self.table_name}(status);
CREATE INDEX IF NOT EXISTS idx_atoms_severity ON {self.table_name}(severity);
CREATE INDEX IF NOT EXISTS idx_atoms_date_created ON {self.table_name}(date_created DESC);

-- Vector similarity index ({self.index_type})
CREATE INDEX IF NOT EXISTS idx_atoms_embedding ON {self.table_name}
USING {self.index_type} (embedding vector_{self.distance_metric}_ops)
""" + (f"WITH (lists = {self.index_lists});" if self.index_type == "ivfflat" else f"WITH (m = {self.hnsw_m}, ef_construction = {self.hnsw_ef_construction});")

    def get_query_example_sql(self) -> str:
        """
        Get example SQL query for semantic search with filters.

        PURPOSE:
            Shows how to query pgvector with metadata filters.
            Uses cosine similarity for ranking.

        RETURNS:
            Example SQL query string

        EXAMPLE:
            >>> config = SupabaseVectorConfig()
            >>> sql = config.get_query_example_sql()
            >>> # Adapt for your use case
        """
        return f"""
-- Semantic search with metadata filtering
SELECT
    atom_id,
    name,
    description,
    manufacturer,
    confidence_score,
    1 - (embedding <=> '[query_embedding_array]') AS similarity
FROM {self.table_name}
WHERE
    industry_vertical = 'hvac'
    AND source_tier IN ('manufacturer_official', 'stack_overflow')
    AND confidence_score >= 0.80
    AND status = 'validated'
ORDER BY embedding <=> '[query_embedding_array]'
LIMIT 10;

-- Notes:
-- <=> is cosine distance operator
-- 1 - distance = similarity score (0 to 1)
-- Replace [query_embedding_array] with actual embedding vector
"""

    def get_metadata_structure_example(self) -> Dict[str, Any]:
        """
        Get example metadata structure for a single Knowledge Atom.

        PURPOSE:
            Shows what metadata should be extracted from Knowledge Atom
            and stored in PostgreSQL columns.

        RETURNS:
            Example metadata dictionary

        EXAMPLE:
            >>> config = SupabaseVectorConfig()
            >>> example = config.get_metadata_structure_example()
            >>> print(example.keys())
        """
        return {
            "atom_id": "urn:industrial-maintenance:atom:uuid",
            "atom_type": "error_code",
            "name": "Error F032: Firmware Version Mismatch",
            "description": "Occurs when drive firmware doesn't match expected version",
            "keywords": ["F032", "firmware", "mismatch", "ABB"],
            "manufacturer": "abb",
            "product_family": "abb_acs880",
            "error_code": "F032",
            "component_type": "vfd",
            "industry_vertical": "hvac",
            "source_tier": "manufacturer_official",
            "confidence_score": 0.95,
            "status": "validated",
            "severity": "high",
            "date_created": "2024-01-15T00:00:00Z",
            "date_modified": "2024-12-08T00:00:00Z",
            "integrity_hash": "sha256_hash_here"
        }


# Global configuration instance
SUPABASE_VECTOR_CONFIG = SupabaseVectorConfig()


__all__ = [
    "SupabaseVectorConfig",
    "SUPABASE_VECTOR_CONFIG",
    "VectorDBProvider",
]
