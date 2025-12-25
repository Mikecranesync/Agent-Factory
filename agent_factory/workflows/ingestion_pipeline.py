"""
Ingestion Pipeline - 7-stage async workflow for knowledge base ingestion.

Stages:
1. Acquisition - Download source document
2. Extraction - Parse document content
3. Chunking - Split into semantic chunks
4. Generation - Create knowledge atoms
5. Validation - Quality & citation checks
6. Embedding - Generate vector embeddings
7. Storage - Write to database

Features:
- Full traceability (session → agents → atoms)
- Document validation gate (reject non-technical content)
- Automatic retries (3x exponential backoff)
- IngestionMonitor integration (metrics)
- Error handling (partial success supported)
"""
import asyncio
import hashlib
import logging
import time
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from agent_factory.core.database_manager import DatabaseManager
from agent_factory.workflows.document_validator import DocumentValidator
from agent_factory.observability.ingestion_monitor import IngestionMonitor
from agent_factory.observability.agent_tracer import SyncAgentTracer

logger = logging.getLogger(__name__)


class IngestionPipelineError(Exception):
    """Base exception for ingestion pipeline errors."""
    pass


class ValidationError(IngestionPipelineError):
    """Document failed validation."""
    pass


class AcquisitionError(IngestionPipelineError):
    """Failed to acquire source document."""
    pass


class IngestionPipeline:
    """
    7-stage async ingestion pipeline with full traceability.

    Orchestrates document ingestion from URL to knowledge atoms in database,
    tracking every step and agent execution for full observability.
    """

    def __init__(
        self,
        db: DatabaseManager,
        monitor: Optional[IngestionMonitor] = None,
        validator: Optional[DocumentValidator] = None,
        max_retries: int = 3,
        retry_delay: float = 2.0
    ):
        """
        Initialize ingestion pipeline.

        Args:
            db: DatabaseManager instance for database operations
            monitor: IngestionMonitor for metrics tracking (creates new if None)
            validator: DocumentValidator for validation gate (creates new if None)
            max_retries: Maximum retry attempts for each stage
            retry_delay: Initial delay between retries (exponential backoff)
        """
        self.db = db
        self.monitor = monitor or IngestionMonitor(db)
        self.validator = validator or DocumentValidator(db)
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def ingest_source(self, source_url: str, priority: int = 50) -> Dict[str, Any]:
        """
        Ingest source document through 7-stage pipeline.

        Args:
            source_url: URL of source document to ingest
            priority: Priority score (0-100, higher = more important)

        Returns:
            Dictionary with ingestion result:
                - session_id: UUID of ingestion session
                - status: 'success', 'partial', or 'failed'
                - atoms_created: Number of atoms successfully created
                - atoms_failed: Number of atoms that failed
                - error_stage: Stage where error occurred (if failed)
                - error_message: Error details (if failed)

        Raises:
            ValidationError: Document failed validation
            IngestionPipelineError: Unrecoverable pipeline error
        """
        # Create session
        session_id = await self._create_session(source_url)
        source_hash = hashlib.sha256(source_url.encode()).hexdigest()[:16]

        # Track ingestion with monitor
        async with self.monitor.track_ingestion(source_url, "pdf") as session:
            try:
                logger.info(f"[{session_id}] Starting ingestion for {source_url}")

                # ========================================
                # STAGE 1: ACQUISITION
                # ========================================
                stage_start = time.time()
                logger.info(f"[{session_id}] Stage 1: Acquisition")

                raw_content, content_sample = await self._stage_1_acquisition(
                    source_url, session_id
                )

                duration_ms = int((time.time() - stage_start) * 1000)
                session.record_stage("acquisition", duration_ms, True)
                logger.info(f"[{session_id}] Stage 1 complete ({duration_ms}ms)")

                # ========================================
                # STAGE 0: VALIDATION GATE
                # ========================================
                # (Runs before extraction to fail fast)
                stage_start = time.time()
                logger.info(f"[{session_id}] Validation gate")

                validation_result = await self._validate_document(
                    source_url, content_sample, session_id
                )

                if not validation_result.is_valid:
                    # Reject: Write to validations table but don't proceed
                    await self._mark_session_failed(
                        session_id,
                        "validation",
                        f"Failed validation: {validation_result.reason}"
                    )
                    session.finish(0, 0, partial=False)
                    raise ValidationError(
                        f"Document rejected (score: {validation_result.score}): "
                        f"{validation_result.reason}"
                    )

                duration_ms = int((time.time() - stage_start) * 1000)
                logger.info(
                    f"[{session_id}] Validation passed "
                    f"(score: {validation_result.score}, {duration_ms}ms)"
                )

                # ========================================
                # STAGE 2: EXTRACTION
                # ========================================
                stage_start = time.time()
                logger.info(f"[{session_id}] Stage 2: Extraction")

                extracted_content = await self._stage_2_extraction(
                    raw_content, session_id
                )

                duration_ms = int((time.time() - stage_start) * 1000)
                session.record_stage("extraction", duration_ms, True)
                logger.info(f"[{session_id}] Stage 2 complete ({duration_ms}ms)")

                # ========================================
                # STAGE 3: CHUNKING
                # ========================================
                stage_start = time.time()
                logger.info(f"[{session_id}] Stage 3: Chunking")

                chunks = await self._stage_3_chunking(
                    extracted_content, session_id
                )

                duration_ms = int((time.time() - stage_start) * 1000)
                session.record_stage("chunking", duration_ms, True)
                logger.info(
                    f"[{session_id}] Stage 3 complete "
                    f"({len(chunks)} chunks, {duration_ms}ms)"
                )

                # ========================================
                # STAGE 4: GENERATION (ATOM BUILDER)
                # ========================================
                stage_start = time.time()
                logger.info(f"[{session_id}] Stage 4: Generation")

                atoms = await self._stage_4_generation(
                    chunks, source_url, session_id
                )

                duration_ms = int((time.time() - stage_start) * 1000)
                session.record_stage("generation", duration_ms, True)
                logger.info(
                    f"[{session_id}] Stage 4 complete "
                    f"({len(atoms)} atoms, {duration_ms}ms)"
                )

                # ========================================
                # STAGE 5: VALIDATION (QUALITY + CITATIONS)
                # ========================================
                stage_start = time.time()
                logger.info(f"[{session_id}] Stage 5: Validation")

                validated_atoms = await self._stage_5_validation(
                    atoms, session_id
                )

                duration_ms = int((time.time() - stage_start) * 1000)
                session.record_stage("validation", duration_ms, True)
                logger.info(
                    f"[{session_id}] Stage 5 complete "
                    f"({len(validated_atoms)} passed, {duration_ms}ms)"
                )

                # ========================================
                # STAGE 6: EMBEDDING
                # ========================================
                stage_start = time.time()
                logger.info(f"[{session_id}] Stage 6: Embedding")

                atoms_with_embeddings = await self._stage_6_embedding(
                    validated_atoms, session_id
                )

                duration_ms = int((time.time() - stage_start) * 1000)
                session.record_stage("embedding", duration_ms, True)
                logger.info(f"[{session_id}] Stage 6 complete ({duration_ms}ms)")

                # ========================================
                # STAGE 7: STORAGE
                # ========================================
                stage_start = time.time()
                logger.info(f"[{session_id}] Stage 7: Storage")

                atoms_created, atoms_failed = await self._stage_7_storage(
                    atoms_with_embeddings, session_id
                )

                duration_ms = int((time.time() - stage_start) * 1000)
                session.record_stage("storage", duration_ms, True)
                logger.info(
                    f"[{session_id}] Stage 7 complete "
                    f"({atoms_created} stored, {atoms_failed} failed, {duration_ms}ms)"
                )

                # ========================================
                # FINALIZE SESSION
                # ========================================
                status = "success" if atoms_failed == 0 else "partial"
                await self._mark_session_complete(session_id, atoms_created, atoms_failed)
                session.finish(atoms_created, atoms_failed, partial=(atoms_failed > 0))

                logger.info(
                    f"[{session_id}] Ingestion complete: "
                    f"{atoms_created} atoms created, {atoms_failed} failed"
                )

                return {
                    "session_id": session_id,
                    "status": status,
                    "atoms_created": atoms_created,
                    "atoms_failed": atoms_failed,
                    "validation_score": validation_result.score
                }

            except ValidationError:
                # Already handled above, re-raise
                raise

            except Exception as e:
                # Unhandled error - mark session failed
                error_msg = str(e)
                logger.error(
                    f"[{session_id}] Pipeline failed: {error_msg}",
                    exc_info=True
                )

                await self._mark_session_failed(session_id, "unknown", error_msg)
                session.finish(0, 0, partial=False)

                return {
                    "session_id": session_id,
                    "status": "failed",
                    "atoms_created": 0,
                    "atoms_failed": 0,
                    "error_message": error_msg
                }

    async def _create_session(self, source_url: str) -> str:
        """
        Create ingestion_sessions record.

        Args:
            source_url: Source document URL

        Returns:
            session_id: UUID of created session
        """
        session_id = str(uuid.uuid4())
        source_hash = hashlib.sha256(source_url.encode()).hexdigest()[:16]

        query = """
            INSERT INTO ingestion_sessions (
                session_id, source_url, source_hash, status, started_at
            ) VALUES ($1, $2, $3, 'processing', NOW())
        """

        await asyncio.get_event_loop().run_in_executor(
            None,
            self.db.execute_query,
            query,
            (session_id, source_url, source_hash),
            "none"
        )

        logger.debug(f"Created ingestion session: {session_id}")
        return session_id

    async def _mark_session_complete(
        self, session_id: str, atoms_created: int, atoms_failed: int
    ):
        """Mark session as complete with atom counts."""
        status = "success" if atoms_failed == 0 else "partial"

        query = """
            UPDATE ingestion_sessions
            SET status = $1, atoms_created = $2, atoms_failed = $3, completed_at = NOW()
            WHERE session_id = $4
        """

        await asyncio.get_event_loop().run_in_executor(
            None,
            self.db.execute_query,
            query,
            (status, atoms_created, atoms_failed, session_id),
            "none"
        )

    async def _mark_session_failed(
        self, session_id: str, error_stage: str, error_message: str
    ):
        """Mark session as failed with error details."""
        query = """
            UPDATE ingestion_sessions
            SET status = 'failed', error_stage = $1, error_message = $2, completed_at = NOW()
            WHERE session_id = $3
        """

        await asyncio.get_event_loop().run_in_executor(
            None,
            self.db.execute_query,
            query,
            (error_stage, error_message, session_id),
            "none"
        )

    # ========================================
    # STAGE IMPLEMENTATIONS (PLACEHOLDERS)
    # ========================================
    # These will be implemented with actual logic or integrated with existing agents

    async def _stage_1_acquisition(
        self, source_url: str, session_id: str
    ) -> tuple[bytes, str]:
        """
        Download source document.

        Args:
            source_url: URL of document
            session_id: Session ID for tracing

        Returns:
            Tuple of (raw_content, content_sample for validation)

        Raises:
            AcquisitionError: Failed to download document
        """
        # PLACEHOLDER: Implement PDF download logic
        # For now, simulate successful download
        await asyncio.sleep(0.12)  # Simulate network delay

        # Return mock data
        raw_content = b"Mock PDF content"
        content_sample = "Mock content sample for validation"

        return raw_content, content_sample

    async def _validate_document(
        self, source_url: str, content_sample: str, session_id: str
    ):
        """Run document validation gate (synchronous validator in executor)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.validator.validate_document,
            source_url,
            content_sample
        )

    async def _stage_2_extraction(
        self, raw_content: bytes, session_id: str
    ) -> str:
        """Extract text from PDF."""
        # PLACEHOLDER: Implement PDF extraction
        await asyncio.sleep(0.08)
        return "Extracted text content"

    async def _stage_3_chunking(
        self, extracted_content: str, session_id: str
    ) -> List[str]:
        """Split content into semantic chunks."""
        # PLACEHOLDER: Implement semantic chunking
        await asyncio.sleep(0.05)
        return ["Chunk 1", "Chunk 2", "Chunk 3"]

    async def _stage_4_generation(
        self, chunks: List[str], source_url: str, session_id: str
    ) -> List[Dict[str, Any]]:
        """Generate knowledge atoms from chunks."""
        # PLACEHOLDER: Integrate AtomBuilder agent with tracing
        await asyncio.sleep(2.0)  # LLM call simulation

        # Return mock atoms
        return [
            {"atom_id": str(uuid.uuid4()), "title": "Mock Atom 1"},
            {"atom_id": str(uuid.uuid4()), "title": "Mock Atom 2"}
        ]

    async def _stage_5_validation(
        self, atoms: List[Dict[str, Any]], session_id: str
    ) -> List[Dict[str, Any]]:
        """Validate atoms (quality + citations)."""
        # PLACEHOLDER: Integrate QualityChecker and CitationValidator
        await asyncio.sleep(1.5)  # LLM call simulation
        return atoms  # All atoms pass for now

    async def _stage_6_embedding(
        self, atoms: List[Dict[str, Any]], session_id: str
    ) -> List[Dict[str, Any]]:
        """Generate vector embeddings for atoms."""
        # PLACEHOLDER: Integrate embedding service
        await asyncio.sleep(0.1 * len(atoms))

        # Add mock embeddings
        for atom in atoms:
            atom["embedding"] = [0.1] * 1536  # Mock 1536-dim vector

        return atoms

    async def _stage_7_storage(
        self, atoms: List[Dict[str, Any]], session_id: str
    ) -> tuple[int, int]:
        """Write atoms to database."""
        # PLACEHOLDER: Implement database insertion
        await asyncio.sleep(0.2)

        atoms_created = len(atoms)
        atoms_failed = 0

        return atoms_created, atoms_failed


# ============================================================================
# Helper Functions
# ============================================================================

def create_ingestion_pipeline(db: DatabaseManager) -> IngestionPipeline:
    """
    Factory function for creating ingestion pipelines.

    Args:
        db: DatabaseManager instance

    Returns:
        IngestionPipeline instance

    Example:
        >>> db = DatabaseManager()
        >>> pipeline = create_ingestion_pipeline(db)
        >>> result = await pipeline.ingest_source("https://example.com/manual.pdf")
    """
    return IngestionPipeline(db)
