"""
Tests for DocumentValidator - LLM-based validation gate.
"""
import pytest
from unittest.mock import Mock, patch

from agent_factory.workflows.document_validator import (
    DocumentValidator,
    DocumentValidationResult,
    create_document_validator
)


@pytest.fixture
def mock_db():
    """Mock DatabaseManager for testing."""
    db = Mock()
    db.execute_query = Mock(return_value=[])
    return db


@pytest.fixture
def validator(mock_db):
    """Create DocumentValidator instance for testing."""
    return DocumentValidator(mock_db, min_score=60)


def test_parse_llm_response_valid_manual(validator):
    """Test parsing LLM response for valid technical manual."""
    response = """
SCORE: 85
IS_TECHNICAL_MANUAL: yes
DOCUMENT_TYPE: manual
LANGUAGE: en
MANUFACTURER: Allen-Bradley
MODEL: 1756-L83E
REASON: Comprehensive programming manual with ladder logic examples and troubleshooting procedures.
"""

    data = validator._parse_llm_response(response)

    assert data["score"] == 85
    assert data["is_technical_manual"] is True
    assert data["document_type"] == "manual"
    assert data["language"] == "en"
    assert data["manufacturer"] == "Allen-Bradley"
    assert data["model"] == "1756-L83E"
    assert "programming manual" in data["reason"]


def test_parse_llm_response_marketing_content(validator):
    """Test parsing LLM response for marketing content (should reject)."""
    response = """
SCORE: 25
IS_TECHNICAL_MANUAL: no
DOCUMENT_TYPE: marketing
LANGUAGE: en
MANUFACTURER: Siemens
MODEL: unknown
REASON: Marketing brochure with product listings, no technical procedures.
"""

    data = validator._parse_llm_response(response)

    assert data["score"] == 25
    assert data["is_technical_manual"] is False
    assert data["document_type"] == "marketing"
    assert data["manufacturer"] == "Siemens"
    assert data["model"] is None  # "unknown" should be None


def test_parse_llm_response_non_english(validator):
    """Test parsing LLM response for non-English manual (should reject)."""
    response = """
SCORE: 70
IS_TECHNICAL_MANUAL: yes
DOCUMENT_TYPE: manual
LANGUAGE: de
MANUFACTURER: Schneider Electric
MODEL: TM221C24R
REASON: German language technical manual with good content but wrong language.
"""

    data = validator._parse_llm_response(response)

    assert data["score"] == 70
    assert data["is_technical_manual"] is True
    assert data["language"] == "de"  # German - should reject


def test_build_validation_prompt(validator):
    """Test validation prompt construction."""
    content = "This is a sample ControlLogix programming manual..."

    prompt = validator._build_validation_prompt(content)

    assert "SCORE:" in prompt
    assert "IS_TECHNICAL_MANUAL:" in prompt
    assert "DOCUMENT_TYPE:" in prompt
    assert "ControlLogix programming manual" in prompt
    assert "80-100: Technical manual" in prompt  # Scoring guidelines


def test_validate_document_pass(validator, mock_db):
    """Test document validation - should PASS."""
    # Mock LLM response content
    llm_content = """
SCORE: 85
IS_TECHNICAL_MANUAL: yes
DOCUMENT_TYPE: manual
LANGUAGE: en
MANUFACTURER: Rockwell Automation
MODEL: 1756-RM003
REASON: Comprehensive ControlLogix reference manual with programming examples.
"""

    # Create mock LLMResponse
    mock_response = Mock()
    mock_response.content = llm_content

    with patch.object(validator.llm, 'complete', return_value=mock_response) as mock_llm:
        result = validator.validate_document(
            source_url="https://example.com/manual.pdf",
            content_sample="ControlLogix programming..."
        )

        # Verify result
        assert result.is_valid is True
        assert result.score == 85
        assert result.is_technical_manual is True
        assert result.document_type == "manual"
        assert result.language == "en"
        assert result.manufacturer == "Rockwell Automation"

        # Verify database write
        assert mock_db.execute_query.called


def test_validate_document_reject_marketing(validator, mock_db):
    """Test document validation - should REJECT (marketing content)."""
    # Mock LLM response content
    llm_content = """
SCORE: 30
IS_TECHNICAL_MANUAL: no
DOCUMENT_TYPE: marketing
LANGUAGE: en
MANUFACTURER: Siemens
MODEL: unknown
REASON: Product catalog with marketing language, minimal technical details.
"""

    mock_response = Mock()
    mock_response.content = llm_content

    with patch.object(validator.llm, 'complete', return_value=mock_response) as mock_llm:
        result = validator.validate_document(
            source_url="https://example.com/catalog.pdf",
            content_sample="Industry-leading performance..."
        )

        # Verify result
        assert result.is_valid is False  # Score < 60
        assert result.score == 30
        assert result.is_technical_manual is False
        assert result.document_type == "marketing"


def test_validate_document_reject_wrong_language(validator, mock_db):
    """Test document validation - should REJECT (German manual)."""
    # Mock LLM response content
    llm_content = """
SCORE: 75
IS_TECHNICAL_MANUAL: yes
DOCUMENT_TYPE: manual
LANGUAGE: de
MANUFACTURER: Schneider Electric
MODEL: TM221C24R
REASON: Good technical content but in German language.
"""

    mock_response = Mock()
    mock_response.content = llm_content

    with patch.object(validator.llm, 'complete', return_value=mock_response) as mock_llm:
        result = validator.validate_document(
            source_url="https://example.com/manual_de.pdf",
            content_sample="Betriebsanleitung..."
        )

        # Verify result
        assert result.is_valid is False  # Wrong language
        assert result.score == 75
        assert result.language == "de"


def test_validate_document_cached(validator, mock_db):
    """Test document validation - cached result."""
    # Mock cached validation result (database returns tuples, not dicts)
    cached_result = [(
        True,  # is_technical_manual
        85,    # validation_score
        "en",  # language_detected
        "manual",  # document_type
        "Rockwell",  # manufacturer_detected
        "1756-L83E",  # model_detected
        "Cached validation"  # validation_reason
    )]
    mock_db.execute_query.return_value = cached_result

    result = validator.validate_document(
        source_url="https://example.com/manual.pdf",
        content_sample="Sample content..."
    )

    # Verify result from cache
    assert result.is_valid is True
    assert result.score == 85
    assert result.manufacturer == "Rockwell"

    # Verify LLM NOT called (cached)
    # (mock_llm not used in this test)


def test_get_validation_stats(validator, mock_db):
    """Test validation statistics retrieval."""
    # Mock stats query result
    stats_result = [(100, 75, 68.5, 12)]  # total, passed, avg_score, unique_mfg
    mock_db.execute_query.return_value = stats_result

    stats = validator.get_validation_stats()

    assert stats["total_validations"] == 100
    assert stats["passed"] == 75
    assert stats["rejected"] == 25
    assert stats["pass_rate"] == 75.0
    assert stats["avg_score"] == 68.5
    assert stats["unique_manufacturers"] == 12


def test_create_document_validator(mock_db):
    """Test factory function."""
    validator = create_document_validator(mock_db, min_score=65)

    assert isinstance(validator, DocumentValidator)
    assert validator.min_score == 65
    assert validator.db == mock_db


def test_validate_document_error_handling(validator, mock_db):
    """Test document validation - LLM error (fail-safe: reject)."""
    # Mock LLM error
    with patch.object(validator.llm, 'complete', side_effect=Exception("LLM API timeout")):
        result = validator.validate_document(
            source_url="https://example.com/manual.pdf",
            content_sample="Sample content..."
        )

        # Verify fail-safe: reject on error
        assert result.is_valid is False
        assert result.score == 0
        assert result.document_type == "error"
        assert "LLM API timeout" in result.reason
