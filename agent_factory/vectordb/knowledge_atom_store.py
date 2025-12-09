"""
Knowledge Atom Store - CRUD Operations for Supabase + pgvector

Provides high-level interface for inserting, querying, updating, and deleting
Knowledge Atoms in Supabase PostgreSQL with pgvector.

ARCHITECTURE:
- Validates atoms using 6-stage validation pipeline
- Generates embeddings using OpenAI text-embedding-3-large
- Stores in PostgreSQL with pgvector for semantic search
- Enforces data quality standards

COST: $0-25/month during development (Supabase Free/Pro tier)
"""

import os
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4

import openai
from pydantic import BaseModel

from agent_factory.models.knowledge_atom import KnowledgeAtom
from agent_factory.validation.knowledge_atom_validator import (
    KnowledgeAtomValidator,
    SchemaViolationError,
)
from agent_factory.vectordb.supabase_vector_client import (
    SupabaseVectorClient,
    SupabaseConnectionError,
)


class InsertionError(Exception):
    """Raised when Knowledge Atom insertion fails."""
    pass


class QueryError(Exception):
    """Raised when semantic search query fails."""
    pass


class KnowledgeAtomStore:
    """
    High-level interface for Knowledge Atom storage and retrieval.

    PURPOSE:
        Manages complete lifecycle of Knowledge Atoms:
        - Validation (6-stage pipeline)
        - Embedding generation (OpenAI)
        - Storage (Supabase + pgvector)
        - Semantic search (cosine similarity)
        - Metadata filtering (manufacturer, confidence, etc.)

    USAGE:
        ```python
        store = KnowledgeAtomStore()
        store.connect()

        # Insert atom
        atom = KnowledgeAtom.create(...)
        store.insert(atom)

        # Semantic search
        results = store.query("VFD firmware mismatch error", filters={
            "manufacturer": "abb",
            "confidence_score": {"gte": 0.80}
        })
        ```

    ENVIRONMENT VARIABLES REQUIRED:
        - SUPABASE_URL: Supabase project URL
        - SUPABASE_SERVICE_ROLE_KEY: Service role key
        - OPENAI_API_KEY: OpenAI API key for embeddings

    PLC ANALOGY:
        Like industrial data historian:
        - insert() = Write process data to historian
        - query() = Search historical trends
        - Validation = Data quality checks before storage
    """

    def __init__(
        self,
        client: Optional[SupabaseVectorClient] = None,
        validator: Optional[KnowledgeAtomValidator] = None,
        auto_connect: bool = False,
    ):
        """
        Initialize Knowledge Atom Store.

        Args:
            client: Optional Supabase client (creates default if None)
            validator: Optional validator (creates default if None)
            auto_connect: Automatically connect to Supabase (default: False)
        """
        self.client = client or SupabaseVectorClient()
        self.validator = validator or KnowledgeAtomValidator()
        self._connected = False

        # OpenAI for embeddings
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            print("[WARN] OPENAI_API_KEY not set - embeddings will fail")

        if auto_connect:
            self.connect()

    def connect(self) -> None:
        """
        Connect to Supabase and verify setup.

        WHAT IT DOES:
            1. Connects to Supabase
            2. Creates table if it doesn't exist
            3. Creates indexes

        RAISES:
            SupabaseConnectionError: If connection fails

        EXAMPLE:
            ```python
            store = KnowledgeAtomStore()
            store.connect()
            ```
        """
        if self._connected:
            print("[INFO] Already connected to Supabase")
            return

        print("Connecting to Supabase...")
        self.client.connect()

        print("Creating knowledge_atoms table (if not exists)...")
        self.client.create_table_if_not_exists()

        self._connected = True
        print("[OK] Knowledge Atom Store ready")

    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate vector embedding using OpenAI.

        ARGS:
            text: Text to embed (usually concatenation of name + description)

        RETURNS:
            List of floats (3072 dimensions for text-embedding-3-large)

        RAISES:
            Exception: If OpenAI API call fails

        EXAMPLE:
            ```python
            embedding = store._generate_embedding("VFD firmware mismatch")
            # Returns [0.123, -0.456, ...] (3072 dimensions)
            ```
        """
        if not self.openai_api_key:
            raise Exception("OPENAI_API_KEY not set - cannot generate embeddings")

        try:
            openai.api_key = self.openai_api_key
            response = openai.embeddings.create(
                model="text-embedding-3-large",
                input=text,
            )
            return response.data[0].embedding
        except Exception as e:
            raise Exception(f"Embedding generation failed: {str(e)}")

    def insert(self, atom: KnowledgeAtom, skip_validation: bool = False) -> str:
        """
        Insert Knowledge Atom into vector database.

        PROCESS:
            1. Validate atom (6-stage pipeline) - unless skip_validation=True
            2. Generate text embedding (OpenAI)
            3. Insert into PostgreSQL with pgvector
            4. Return integrity hash

        ARGS:
            atom: Knowledge Atom to insert (Pydantic model)
            skip_validation: Skip validation (NOT RECOMMENDED)

        RETURNS:
            Integrity hash (SHA-256) for verification

        RAISES:
            SchemaViolationError: If validation fails
            InsertionError: If database insertion fails

        EXAMPLE:
            ```python
            atom = KnowledgeAtom.create(
                atom_type=AtomType.ERROR_CODE,
                name="Error F032: Firmware Mismatch",
                description="Occurs when firmware doesn't match...",
                ...
            )
            hash = store.insert(atom)
            print(f"Inserted with hash: {hash}")
            ```
        """
        if not self._connected:
            raise SupabaseConnectionError("Not connected. Call connect() first.")

        # Step 1: Validate (6-stage pipeline)
        if not skip_validation:
            print(f"Validating atom: {atom.name}...")
            atom_dict = atom.model_dump(by_alias=True)
            integrity_hash = self.validator.validate(atom_dict)
            print(f"[OK] Validation passed (hash: {integrity_hash[:16]}...)")
        else:
            print("[WARN] Skipping validation - not recommended!")
            integrity_hash = "skipped"

        # Step 2: Generate embedding
        print("Generating embedding...")
        embedding_text = f"{atom.name} {atom.description}"
        embedding = self._generate_embedding(embedding_text)
        print(f"[OK] Embedding generated ({len(embedding)} dimensions)")

        # Step 3: Prepare data for insertion
        atom_dict = atom.model_dump(by_alias=True)

        row_data = {
            "atom_id": atom.atom_id,
            "atom_type": atom.atom_type.value,
            "name": atom.name,
            "description": atom.description,
            "keywords": atom.keywords,
            "manufacturer": atom.manufacturers[0].name.lower() if atom.manufacturers else None,
            "product_family": atom.product_families[0].identifier if atom.product_families else None,
            "error_code": atom.error_code,
            "component_type": atom.component_types[0].value if atom.component_types else None,
            "industry_vertical": atom.industry_verticals[0].value if atom.industry_verticals else None,
            "source_tier": atom.provider.source_tier.value,
            "confidence_score": atom.quality.confidence_score,
            "status": atom.status.value,
            "severity": atom.severity.value if atom.severity else None,
            "date_created": atom.date_created.isoformat(),
            "date_modified": atom.date_modified.isoformat(),
            "embedding": embedding,
            "atom_data": atom_dict,  # Full atom as JSONB
            "integrity_hash": integrity_hash,
        }

        # Step 4: Insert into PostgreSQL
        try:
            print(f"Inserting into {self.client.config.table_name}...")
            result = self.client.client.table(self.client.config.table_name).insert(row_data).execute()

            if result.data and len(result.data) > 0:
                print(f"[OK] Inserted atom: {atom.name}")
                return integrity_hash
            else:
                raise InsertionError("Insert succeeded but no data returned")

        except Exception as e:
            raise InsertionError(f"Failed to insert atom: {str(e)}")

    def query(
        self,
        query_text: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        min_similarity: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for Knowledge Atoms.

        PROCESS:
            1. Generate embedding for query text
            2. Find similar vectors using cosine distance
            3. Apply metadata filters (manufacturer, confidence, etc.)
            4. Return top K results with similarity scores

        ARGS:
            query_text: Natural language query ("VFD firmware error")
            top_k: Number of results to return (default: 10)
            filters: Metadata filters (e.g., {"manufacturer": "abb"})
            min_similarity: Minimum similarity score (0.0 to 1.0)

        RETURNS:
            List of dictionaries with:
            - atom_id, name, description, manufacturer, etc.
            - similarity: Cosine similarity score (0.0 to 1.0)

        EXAMPLE:
            ```python
            results = store.query(
                "VFD firmware mismatch",
                top_k=5,
                filters={
                    "manufacturer": "abb",
                    "confidence_score": {"gte": 0.80},
                    "status": "validated"
                },
                min_similarity=0.70
            )

            for result in results:
                print(f"{result['name']}: {result['similarity']:.2f}")
            ```
        """
        if not self._connected:
            raise SupabaseConnectionError("Not connected. Call connect() first.")

        # Step 1: Generate query embedding
        print(f"Generating embedding for query: '{query_text}'...")
        query_embedding = self._generate_embedding(query_text)
        print(f"[OK] Query embedding generated ({len(query_embedding)} dimensions)")

        # Step 2: Build filter conditions
        filter_conditions = []
        if filters:
            for key, value in filters.items():
                if isinstance(value, dict):
                    # Handle comparison operators: {"gte": 0.80}
                    for op, val in value.items():
                        if op == "gte":
                            filter_conditions.append(f"{key} >= {val}")
                        elif op == "lte":
                            filter_conditions.append(f"{key} <= {val}")
                        elif op == "gt":
                            filter_conditions.append(f"{key} > {val}")
                        elif op == "lt":
                            filter_conditions.append(f"{key} < {val}")
                        elif op == "eq":
                            filter_conditions.append(f"{key} = '{val}'")
                else:
                    # Simple equality
                    filter_conditions.append(f"{key} = '{value}'")

        where_clause = " AND ".join(filter_conditions) if filter_conditions else "TRUE"

        # Step 3: Build SQL query (pgvector cosine similarity)
        sql = f"""
        SELECT
            atom_id,
            atom_type,
            name,
            description,
            manufacturer,
            product_family,
            confidence_score,
            status,
            severity,
            1 - (embedding <=> '[{','.join(map(str, query_embedding))}]') AS similarity,
            atom_data
        FROM {self.client.config.table_name}
        WHERE {where_clause}
          AND (1 - (embedding <=> '[{','.join(map(str, query_embedding))}]')) >= {min_similarity}
        ORDER BY embedding <=> '[{','.join(map(str, query_embedding))}]'
        LIMIT {top_k};
        """

        # Step 4: Execute query
        try:
            print(f"Searching {self.client.config.table_name} (top_k={top_k})...")
            result = self.client.execute_sql(sql)

            if result:
                print(f"[OK] Found {len(result)} results")
                return result
            else:
                print("[INFO] No results found")
                return []

        except Exception as e:
            raise QueryError(f"Query failed: {str(e)}")

    def get_by_atom_id(self, atom_id: str) -> Optional[Dict[str, Any]]:
        """
        Get Knowledge Atom by atom_id (URN).

        ARGS:
            atom_id: Atom identifier (e.g., "urn:industrial-maintenance:atom:uuid")

        RETURNS:
            Atom data dictionary or None if not found

        EXAMPLE:
            ```python
            atom = store.get_by_atom_id("urn:industrial-maintenance:atom:123")
            if atom:
                print(atom['name'])
            ```
        """
        if not self._connected:
            raise SupabaseConnectionError("Not connected. Call connect() first.")

        try:
            result = (
                self.client.client.table(self.client.config.table_name)
                .select("*")
                .eq("atom_id", atom_id)
                .execute()
            )

            if result.data and len(result.data) > 0:
                return result.data[0]
            return None

        except Exception as e:
            print(f"[ERROR] Failed to get atom: {str(e)}")
            return None

    def delete(self, atom_id: str) -> bool:
        """
        Delete Knowledge Atom by atom_id.

        ARGS:
            atom_id: Atom identifier

        RETURNS:
            True if deleted, False if not found

        EXAMPLE:
            ```python
            if store.delete("urn:industrial-maintenance:atom:123"):
                print("Deleted")
            ```
        """
        if not self._connected:
            raise SupabaseConnectionError("Not connected. Call connect() first.")

        try:
            result = (
                self.client.client.table(self.client.config.table_name)
                .delete()
                .eq("atom_id", atom_id)
                .execute()
            )

            return result.data and len(result.data) > 0

        except Exception as e:
            print(f"[ERROR] Failed to delete atom: {str(e)}")
            return False

    def batch_insert(self, atoms: List[KnowledgeAtom], skip_validation: bool = False) -> List[str]:
        """
        Insert multiple Knowledge Atoms (batch operation).

        ARGS:
            atoms: List of Knowledge Atoms to insert
            skip_validation: Skip validation for all atoms

        RETURNS:
            List of integrity hashes (one per atom)

        EXAMPLE:
            ```python
            atoms = [atom1, atom2, atom3]
            hashes = store.batch_insert(atoms)
            print(f"Inserted {len(hashes)} atoms")
            ```
        """
        hashes = []
        for i, atom in enumerate(atoms):
            print(f"\nInserting atom {i+1}/{len(atoms)}: {atom.name}")
            try:
                hash = self.insert(atom, skip_validation=skip_validation)
                hashes.append(hash)
            except Exception as e:
                print(f"[ERROR] Failed to insert {atom.name}: {str(e)}")
                hashes.append(None)

        return hashes

    def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.

        RETURNS:
            Dictionary with:
            - total_atoms: Total number of Knowledge Atoms
            - by_manufacturer: Count by manufacturer
            - by_status: Count by status
            - by_industry: Count by industry vertical

        EXAMPLE:
            ```python
            stats = store.get_stats()
            print(f"Total atoms: {stats['total_atoms']}")
            ```
        """
        if not self._connected:
            raise SupabaseConnectionError("Not connected. Call connect() first.")

        info = self.client.get_table_info()

        return {
            "total_atoms": info.get("row_count", 0),
            "table_size_mb": info.get("table_size_mb", 0),
            "index_size_mb": info.get("index_size_mb", 0),
        }


__all__ = [
    "KnowledgeAtomStore",
    "InsertionError",
    "QueryError",
]
