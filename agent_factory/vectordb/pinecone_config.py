"""
Pinecone Index Configuration for Knowledge Atoms

Based on Part 4 of Knowledge Atom Standard v1.0.
Optimized for industrial maintenance knowledge retrieval.
"""

from typing import Dict, List, Any
from pydantic import BaseModel, Field


class PineconeIndexConfig(BaseModel):
    """
    Pinecone index configuration for Knowledge Atoms.

    PURPOSE:
        Defines index structure, namespaces, and metadata filtering.
        Based on Knowledge Atom Standard Part 4 (Pinecone schema).

    WHAT THIS CONTAINS:
        - index_name: Name of Pinecone index
        - namespaces: Industry vertical partitioning
        - dimension: Vector dimension (OpenAI text-embedding-3-large = 3072)
        - metric: Distance metric (cosine for semantic similarity)
        - metadata_config: Filterable metadata fields

    PLC ANALOGY:
        Like industrial equipment database schema:
        - index_name = Database name
        - namespaces = Data partitions (by industry vertical)
        - metadata_config = Indexed fields for fast queries
    """
    index_name: str = Field(
        default="industrial-maintenance-atoms",
        description="Pinecone index name"
    )

    # Namespace structure (horizontal partitioning by industry vertical)
    namespaces: List[str] = Field(
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
        description="Industry vertical namespaces for partitioning"
    )

    # Vector configuration
    dimension: int = Field(
        default=3072,
        description="Vector dimension (OpenAI text-embedding-3-large)"
    )

    metric: str = Field(
        default="cosine",
        description="Distance metric for similarity search"
    )

    # Metadata filtering fields (queryable without loading vectors)
    metadata_indexed_fields: List[str] = Field(
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
        description="Metadata fields indexed for filtering"
    )

    def get_metadata_structure_example(self) -> Dict[str, Any]:
        """
        Get example metadata structure for a single vector.

        PURPOSE:
            Shows what metadata should be extracted from Knowledge Atom
            and stored alongside vector in Pinecone.

        RETURNS:
            Example metadata dictionary

        EXAMPLE:
            >>> config = PineconeIndexConfig()
            >>> example = config.get_metadata_structure_example()
            >>> print(example.keys())
        """
        return {
            "atom_id": "urn:industrial-maintenance:atom:uuid",
            "atom_type": "error_code",
            "source_tier": "manufacturer_official",
            "manufacturer": "abb",
            "error_code": "F032",
            "product_family": "abb_acs880",
            "confidence_score": 0.95,
            "status": "validated",
            "component_type": "vfd",
            "industry_vertical": "hvac",
            "severity": "high",
            "date_created": "2024-01-15T00:00:00Z",
            "date_modified": "2024-12-08T00:00:00Z",
            "corroboration_count": 3,
            "citation_count": 47,
            "source_url": "https://...",
            "author_reputation": "manufacturer_official"
        }

    def get_query_example(self) -> Dict[str, Any]:
        """
        Get example query with filters.

        PURPOSE:
            Shows how to query Pinecone with metadata filters.

        RETURNS:
            Example query dictionary

        EXAMPLE:
            >>> config = PineconeIndexConfig()
            >>> query = config.get_query_example()
        """
        return {
            "vector": "[query_embedding_goes_here]",
            "top_k": 10,
            "namespace": "hvac",
            "filter": {
                "source_tier": {"$in": ["manufacturer_official", "stack_overflow"]},
                "confidence_score": {"$gte": 0.80},
                "manufacturer": {"$eq": "abb"},
                "status": {"$eq": "validated"}
            }
        }


# Global configuration instance
PINECONE_CONFIG = PineconeIndexConfig()


__all__ = [
    "PineconeIndexConfig",
    "PINECONE_CONFIG",
]
