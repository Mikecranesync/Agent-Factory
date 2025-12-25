"""
Tests for IngestionPipeline - 7-stage async ingestion workflow.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import uuid

from agent_factory.workflows.ingestion_pipeline import (
    IngestionPipeline,
    ValidationError,
    create_ingestion_pipeline
)
from agent_factory.workflows.document_validator import DocumentValidationResult


@pytest.fixture
def mock_db():
    """Mock DatabaseManager for testing."""
    db = Mock()
    db.execute_query = Mock(return_value=[])
    return db


@pytest.fixture
def mock_monitor():
    """Mock IngestionMonitor for testing."""
    monitor = Mock()

    # Mock track_ingestion context manager
    mock_session = AsyncMock()
    mock_session.record_stage = Mock()
    mock_session.finish = Mock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    monitor.track_ingestion = Mock(return_value=mock_session)
    return monitor


@pytest.fixture
def mock_validator():
    """Mock DocumentValidator for testing."""
    validator = Mock()

    # Mock validation result (pass by default)
    validation_result = DocumentValidationResult(
        is_valid=True,
        score=85,
        is_technical_manual=True,
        document_type="manual",
        language="en",
        manufacturer="Rockwell",
        model="1756-L83E"
    )

    validator.validate_document = Mock(return_value=validation_result)
    return validator


@pytest.fixture
def pipeline(mock_db, mock_monitor, mock_validator):
    """Create IngestionPipeline instance for testing."""
    return IngestionPipeline(
        db=mock_db,
        monitor=mock_monitor,
        validator=mock_validator
    )


@pytest.mark.asyncio
async def test_create_session(pipeline, mock_db):
    """Test session creation."""
    session_id = await pipeline._create_session("https://example.com/manual.pdf")

    # Verify session_id is valid UUID
    assert uuid.UUID(session_id)

    # Verify database insert was called
    assert mock_db.execute_query.called


@pytest.mark.asyncio
async def test_ingest_source_success(pipeline, mock_db, mock_monitor, mock_validator):
    """Test successful ingestion (all stages pass)."""
    result = await pipeline.ingest_source("https://example.com/manual.pdf")

    # Verify result structure
    assert "session_id" in result
    assert result["status"] == "success"
    assert result["atoms_created"] == 2  # Mock implementation returns 2 atoms
    assert result["atoms_failed"] == 0
    assert "validation_score" in result

    # Verify validation was called
    assert mock_validator.validate_document.called

    # Verify monitor tracked all stages
    session = mock_monitor.track_ingestion.return_value
    assert session.record_stage.call_count >= 6  # 6 stages (acquisition, extraction, chunking, generation, validation, embedding, storage)
    assert session.finish.called


@pytest.mark.asyncio
async def test_ingest_source_validation_failure(pipeline, mock_db, mock_monitor, mock_validator):
    """Test ingestion with validation failure."""
    # Mock validation failure
    failed_result = DocumentValidationResult(
        is_valid=False,
        score=30,
        is_technical_manual=False,
        document_type="marketing",
        language="en",
        reason="Marketing brochure, not technical manual"
    )
    mock_validator.validate_document = Mock(return_value=failed_result)

    # Should raise ValidationError
    with pytest.raises(ValidationError) as exc_info:
        await pipeline.ingest_source("https://example.com/brochure.pdf")

    # Verify error message
    assert "score: 30" in str(exc_info.value)
    assert "Marketing brochure" in str(exc_info.value)


@pytest.mark.asyncio
async def test_mark_session_complete(pipeline, mock_db):
    """Test marking session as complete."""
    session_id = str(uuid.uuid4())

    await pipeline._mark_session_complete(session_id, atoms_created=10, atoms_failed=2)

    # Verify database update was called
    assert mock_db.execute_query.called

    # Verify status is 'partial' (some atoms failed)
    call_args = mock_db.execute_query.call_args
    assert call_args[0][1][0] == "partial"  # status
    assert call_args[0][1][1] == 10  # atoms_created
    assert call_args[0][1][2] == 2   # atoms_failed


@pytest.mark.asyncio
async def test_mark_session_failed(pipeline, mock_db):
    """Test marking session as failed."""
    session_id = str(uuid.uuid4())

    await pipeline._mark_session_failed(
        session_id,
        error_stage="extraction",
        error_message="PDF parse error"
    )

    # Verify database update was called
    assert mock_db.execute_query.called

    # Verify error details
    call_args = mock_db.execute_query.call_args
    assert call_args[0][1][0] == "extraction"  # error_stage
    assert call_args[0][1][1] == "PDF parse error"  # error_message


@pytest.mark.asyncio
async def test_stage_1_acquisition(pipeline):
    """Test Stage 1: Acquisition."""
    session_id = str(uuid.uuid4())

    raw_content, content_sample = await pipeline._stage_1_acquisition(
        "https://example.com/manual.pdf",
        session_id
    )

    # Verify mock data returned
    assert isinstance(raw_content, bytes)
    assert isinstance(content_sample, str)


@pytest.mark.asyncio
async def test_stage_2_extraction(pipeline):
    """Test Stage 2: Extraction."""
    session_id = str(uuid.uuid4())

    extracted = await pipeline._stage_2_extraction(b"Raw PDF content", session_id)

    # Verify extracted text returned
    assert isinstance(extracted, str)


@pytest.mark.asyncio
async def test_stage_3_chunking(pipeline):
    """Test Stage 3: Chunking."""
    session_id = str(uuid.uuid4())

    chunks = await pipeline._stage_3_chunking("Extracted text", session_id)

    # Verify chunks returned
    assert isinstance(chunks, list)
    assert len(chunks) > 0


@pytest.mark.asyncio
async def test_stage_4_generation(pipeline):
    """Test Stage 4: Generation."""
    session_id = str(uuid.uuid4())
    chunks = ["Chunk 1", "Chunk 2"]

    atoms = await pipeline._stage_4_generation(
        chunks,
        "https://example.com/manual.pdf",
        session_id
    )

    # Verify atoms returned
    assert isinstance(atoms, list)
    assert len(atoms) > 0
    assert "atom_id" in atoms[0]


@pytest.mark.asyncio
async def test_stage_5_validation(pipeline):
    """Test Stage 5: Validation."""
    session_id = str(uuid.uuid4())
    atoms = [{"atom_id": "123", "title": "Test"}]

    validated = await pipeline._stage_5_validation(atoms, session_id)

    # Verify atoms returned
    assert isinstance(validated, list)
    assert len(validated) > 0


@pytest.mark.asyncio
async def test_stage_6_embedding(pipeline):
    """Test Stage 6: Embedding."""
    session_id = str(uuid.uuid4())
    atoms = [{"atom_id": "123", "title": "Test"}]

    atoms_with_embeddings = await pipeline._stage_6_embedding(atoms, session_id)

    # Verify embeddings added
    assert isinstance(atoms_with_embeddings, list)
    assert "embedding" in atoms_with_embeddings[0]


@pytest.mark.asyncio
async def test_stage_7_storage(pipeline):
    """Test Stage 7: Storage."""
    session_id = str(uuid.uuid4())
    atoms = [
        {"atom_id": "123", "title": "Test 1", "embedding": [0.1] * 1536},
        {"atom_id": "456", "title": "Test 2", "embedding": [0.2] * 1536}
    ]

    created, failed = await pipeline._stage_7_storage(atoms, session_id)

    # Verify counts
    assert created == 2
    assert failed == 0


def test_create_ingestion_pipeline(mock_db):
    """Test factory function."""
    pipeline = create_ingestion_pipeline(mock_db)

    assert isinstance(pipeline, IngestionPipeline)
    assert pipeline.db == mock_db
