"""
Supabase + pgvector Client for Knowledge Atoms

Provides utilities for connecting to Supabase PostgreSQL with pgvector extension.
Handles table creation, indexing, and connection management.

COST: $0-25/month during development (Free/Pro tier)
"""

import os
from typing import Optional, Dict, Any
from supabase import create_client, Client
from pydantic import BaseModel, Field

from agent_factory.vectordb.supabase_vector_config import SupabaseVectorConfig, SUPABASE_VECTOR_CONFIG


class SupabaseConnectionError(Exception):
    """Raised when Supabase connection fails."""
    pass


class SupabaseVectorClient:
    """
    Client for Supabase PostgreSQL with pgvector extension.

    PURPOSE:
        Manages connection to Supabase and provides utilities for:
        - Creating knowledge_atoms table
        - Creating vector similarity indexes
        - Executing raw SQL for setup

    USAGE:
        ```python
        client = SupabaseVectorClient()
        client.connect()
        client.create_table_if_not_exists()
        client.create_indexes()
        ```

    ENVIRONMENT VARIABLES REQUIRED:
        - SUPABASE_URL: Your Supabase project URL
        - SUPABASE_SERVICE_ROLE_KEY: Service role key (admin access)

    PLC ANALOGY:
        Like PLC communication module:
        - connect() = Establish connection to PLC
        - create_table() = Configure PLC memory layout
        - create_indexes() = Set up fast access registers
    """

    def __init__(self, config: Optional[SupabaseVectorConfig] = None):
        """
        Initialize Supabase vector client.

        Args:
            config: Optional custom configuration (defaults to SUPABASE_VECTOR_CONFIG)
        """
        self.config = config or SUPABASE_VECTOR_CONFIG
        self.client: Optional[Client] = None
        self._connected = False

    def connect(self) -> Client:
        """
        Connect to Supabase using environment variables.

        ENVIRONMENT VARIABLES:
            - SUPABASE_URL: Project URL from Supabase dashboard
            - SUPABASE_SERVICE_ROLE_KEY: Service role key (Settings → API)

        RETURNS:
            Supabase client instance

        RAISES:
            SupabaseConnectionError: If connection fails or env vars missing

        EXAMPLE:
            ```python
            client = SupabaseVectorClient()
            supabase = client.connect()
            ```
        """
        # Get credentials from environment
        supabase_url = os.getenv("SUPABASE_URL", self.config.supabase_url)
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", self.config.supabase_key)

        if not supabase_url or not supabase_key:
            raise SupabaseConnectionError(
                "Missing Supabase credentials. Set environment variables:\n"
                "  SUPABASE_URL=https://xxxxx.supabase.co\n"
                "  SUPABASE_SERVICE_ROLE_KEY=your_service_role_key\n\n"
                "Get these from: Supabase Dashboard → Settings → API"
            )

        try:
            self.client = create_client(supabase_url, supabase_key)
            self._connected = True
            return self.client
        except Exception as e:
            raise SupabaseConnectionError(f"Failed to connect to Supabase: {str(e)}")

    def execute_sql(self, sql: str) -> Dict[str, Any]:
        """
        Execute raw SQL statement via Supabase RPC.

        PURPOSE:
            Execute DDL statements (CREATE TABLE, CREATE INDEX, etc.)
            Uses Supabase's sql RPC function for admin operations.

        ARGS:
            sql: SQL statement to execute

        RETURNS:
            Result dictionary from Supabase

        RAISES:
            SupabaseConnectionError: If not connected
            Exception: If SQL execution fails

        EXAMPLE:
            ```python
            client.execute_sql("SELECT version();")
            ```
        """
        if not self._connected or not self.client:
            raise SupabaseConnectionError("Not connected. Call connect() first.")

        try:
            # Supabase RPC for SQL execution
            result = self.client.rpc("sql", {"query": sql}).execute()
            return result.data
        except Exception as e:
            raise Exception(f"SQL execution failed: {str(e)}\n\nSQL:\n{sql}")

    def create_table_if_not_exists(self) -> None:
        """
        Create knowledge_atoms table with pgvector extension.

        PURPOSE:
            Sets up PostgreSQL table with:
            - pgvector extension enabled
            - Vector embedding column (3072 dimensions)
            - Metadata columns (indexed for filtering)
            - Constraints and defaults

        WHAT IT DOES:
            1. Enables pgvector extension (if not already enabled)
            2. Creates knowledge_atoms table
            3. Creates metadata indexes
            4. Creates vector similarity index (HNSW or IVFFlat)

        RAISES:
            Exception: If table creation fails

        EXAMPLE:
            ```python
            client = SupabaseVectorClient()
            client.connect()
            client.create_table_if_not_exists()
            ```

        NOTE:
            This is idempotent - safe to run multiple times.
            Uses IF NOT EXISTS clauses.
        """
        if not self._connected or not self.client:
            raise SupabaseConnectionError("Not connected. Call connect() first.")

        sql = self.config.get_table_schema_sql()

        print(f"Creating table '{self.config.table_name}' with pgvector...")
        print(f"  - Dimension: {self.config.dimension}")
        print(f"  - Index type: {self.config.index_type}")
        print(f"  - Distance metric: {self.config.distance_metric}")

        try:
            self.execute_sql(sql)
            print(f"[OK] Table '{self.config.table_name}' created successfully")
        except Exception as e:
            print(f"[FAIL] Table creation failed: {str(e)}")
            raise

    def test_connection(self) -> bool:
        """
        Test Supabase connection by running simple query.

        RETURNS:
            True if connection works, False otherwise

        EXAMPLE:
            ```python
            client = SupabaseVectorClient()
            client.connect()
            if client.test_connection():
                print("Connection OK")
            ```
        """
        if not self._connected or not self.client:
            return False

        try:
            # Test with simple query
            result = self.client.table(self.config.table_name).select("count").limit(1).execute()
            return True
        except:
            return False

    def get_table_info(self) -> Dict[str, Any]:
        """
        Get information about knowledge_atoms table.

        RETURNS:
            Dictionary with table metadata:
            - row_count: Number of Knowledge Atoms
            - table_size: Table size in bytes
            - index_size: Index size in bytes

        EXAMPLE:
            ```python
            info = client.get_table_info()
            print(f"Atoms: {info['row_count']}")
            print(f"Size: {info['table_size_mb']:.2f} MB")
            ```
        """
        if not self._connected or not self.client:
            raise SupabaseConnectionError("Not connected. Call connect() first.")

        sql = f"""
        SELECT
            (SELECT COUNT(*) FROM {self.config.table_name}) as row_count,
            pg_total_relation_size('{self.config.table_name}') as table_size_bytes,
            pg_indexes_size('{self.config.table_name}') as index_size_bytes;
        """

        try:
            result = self.execute_sql(sql)
            if result and len(result) > 0:
                row = result[0]
                return {
                    "row_count": row.get("row_count", 0),
                    "table_size_bytes": row.get("table_size_bytes", 0),
                    "table_size_mb": row.get("table_size_bytes", 0) / (1024 * 1024),
                    "index_size_bytes": row.get("index_size_bytes", 0),
                    "index_size_mb": row.get("index_size_bytes", 0) / (1024 * 1024),
                }
            return {"row_count": 0, "table_size_bytes": 0, "index_size_bytes": 0}
        except Exception as e:
            print(f"[WARN] Could not get table info: {str(e)}")
            return {"row_count": 0, "table_size_bytes": 0, "index_size_bytes": 0}

    def close(self) -> None:
        """
        Close Supabase connection.

        NOTE:
            Supabase Python client manages connections automatically.
            This is mainly for cleanup in testing.
        """
        self.client = None
        self._connected = False


__all__ = [
    "SupabaseVectorClient",
    "SupabaseConnectionError",
]
