"""
Document Validator - LLM-based validation gate for ingestion pipeline.

Filters out non-technical content before expensive ingestion:
- Marketing PDFs (brochures, catalogs)
- Wrong language (non-English)
- Corrupted or malformed files
- Non-industrial content

Writes validation results to document_validations table.
"""
import hashlib
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from agent_factory.core.database_manager import DatabaseManager
from agent_factory.llm.router import LLMRouter
from agent_factory.llm.types import ModelCapability, LLMConfig, LLMProvider

logger = logging.getLogger(__name__)


class DocumentValidationResult:
    """Result of document validation."""

    def __init__(
        self,
        is_valid: bool,
        score: int,
        is_technical_manual: bool,
        document_type: str,
        language: str,
        manufacturer: Optional[str] = None,
        model: Optional[str] = None,
        reason: Optional[str] = None
    ):
        self.is_valid = is_valid
        self.score = score
        self.is_technical_manual = is_technical_manual
        self.document_type = document_type
        self.language = language
        self.manufacturer = manufacturer
        self.model = model
        self.reason = reason


class DocumentValidator:
    """
    LLM-based document validation gate.

    Validates documents before ingestion to filter out:
    - Marketing content
    - Wrong language
    - Corrupted files
    - Non-technical content
    """

    def __init__(self, db: DatabaseManager, min_score: int = 60):
        """
        Initialize document validator.

        Args:
            db: DatabaseManager instance for writing validation results
            min_score: Minimum score (0-100) to pass validation (default: 60)
        """
        self.db = db
        self.min_score = min_score
        self.llm = LLMRouter()

    def validate_document(self, source_url: str, content_sample: str) -> DocumentValidationResult:
        """
        Validate document using LLM analysis.

        Args:
            source_url: URL of the document
            content_sample: First 2-3 pages of extracted text (~2000 chars)

        Returns:
            DocumentValidationResult with validation decision and metadata
        """
        source_hash = hashlib.sha256(source_url.encode()).hexdigest()[:16]

        # Check if already validated (cached result)
        cached = self._get_cached_validation(source_hash)
        if cached:
            logger.info(f"Using cached validation for {source_url[:50]}... (score: {cached['score']})")
            return self._build_result_from_db(cached)

        try:
            # Build validation prompt
            prompt = self._build_validation_prompt(content_sample)

            # Build messages for LLM
            messages = [{"role": "user", "content": prompt}]

            # Create config for SIMPLE capability (cheapest model)
            config = LLMConfig(
                provider=LLMProvider.OPENAI,
                model="gpt-3.5-turbo",  # Cheapest for SIMPLE tasks
                temperature=0.1,  # Low temperature for consistent validation
                max_tokens=500
            )

            # Call LLM
            llm_response = self.llm.complete(messages, config)

            # Parse LLM response
            validation_data = self._parse_llm_response(llm_response.content)

            # Determine if valid
            is_valid = (
                validation_data["score"] >= self.min_score and
                validation_data["is_technical_manual"] and
                validation_data["language"].lower() in ["en", "english"]
            )

            # Write to database
            self._write_validation_result(
                source_url,
                source_hash,
                validation_data,
                is_valid
            )

            # Build result
            result = DocumentValidationResult(
                is_valid=is_valid,
                score=validation_data["score"],
                is_technical_manual=validation_data["is_technical_manual"],
                document_type=validation_data["document_type"],
                language=validation_data["language"],
                manufacturer=validation_data.get("manufacturer"),
                model=validation_data.get("model"),
                reason=validation_data.get("reason")
            )

            logger.info(
                f"Validated {source_url[:50]}... → "
                f"{'PASS' if is_valid else 'REJECT'} (score: {validation_data['score']}, "
                f"type: {validation_data['document_type']})"
            )

            return result

        except Exception as e:
            logger.error(f"Validation failed for {source_url}: {e}", exc_info=True)
            # On error, fail-safe: reject the document
            return DocumentValidationResult(
                is_valid=False,
                score=0,
                is_technical_manual=False,
                document_type="error",
                language="unknown",
                reason=f"Validation error: {str(e)}"
            )

    def _build_validation_prompt(self, content_sample: str) -> str:
        """
        Build LLM prompt for document validation.

        Args:
            content_sample: First few pages of document text

        Returns:
            Structured prompt for validation
        """
        return f"""Analyze this document excerpt and determine if it's a technical manual for industrial equipment.

DOCUMENT EXCERPT:
{content_sample[:2000]}

Provide your analysis in this exact format:

SCORE: [0-100 integer]
IS_TECHNICAL_MANUAL: [yes/no]
DOCUMENT_TYPE: [manual/datasheet/catalog/marketing/other]
LANGUAGE: [en/es/de/fr/other]
MANUFACTURER: [detected manufacturer or "unknown"]
MODEL: [detected model number or "unknown"]
REASON: [one sentence explanation]

Scoring guidelines:
- 80-100: Technical manual with procedures, specifications, troubleshooting
- 60-79: Datasheet or quick reference with technical details
- 40-59: Catalog with some technical info but mostly marketing
- 20-39: Marketing brochure with minimal technical content
- 0-19: Non-technical content (corrupted, wrong language, unrelated)

Examples of REJECT (score < 60):
- Marketing brochures ("Industry-leading performance!")
- Product catalogs (just product listings)
- Non-English manuals
- Corrupted or unreadable files

Examples of PASS (score >= 60):
- Installation manuals with step-by-step procedures
- Programming guides with code examples
- Troubleshooting guides with diagnostics
- Datasheets with specifications and wiring diagrams
"""

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """
        Parse structured LLM response into validation data.

        Args:
            response: LLM response text

        Returns:
            Dictionary with validation fields
        """
        lines = response.strip().split("\n")
        data = {
            "score": 0,
            "is_technical_manual": False,
            "document_type": "unknown",
            "language": "unknown",
            "manufacturer": None,
            "model": None,
            "reason": None
        }

        for line in lines:
            line = line.strip()
            if line.startswith("SCORE:"):
                try:
                    data["score"] = int(line.split(":", 1)[1].strip())
                except ValueError:
                    logger.warning(f"Failed to parse score from: {line}")

            elif line.startswith("IS_TECHNICAL_MANUAL:"):
                value = line.split(":", 1)[1].strip().lower()
                data["is_technical_manual"] = value in ["yes", "true", "1"]

            elif line.startswith("DOCUMENT_TYPE:"):
                data["document_type"] = line.split(":", 1)[1].strip().lower()

            elif line.startswith("LANGUAGE:"):
                data["language"] = line.split(":", 1)[1].strip().lower()

            elif line.startswith("MANUFACTURER:"):
                value = line.split(":", 1)[1].strip()
                if value.lower() != "unknown":
                    data["manufacturer"] = value

            elif line.startswith("MODEL:"):
                value = line.split(":", 1)[1].strip()
                if value.lower() != "unknown":
                    data["model"] = value

            elif line.startswith("REASON:"):
                data["reason"] = line.split(":", 1)[1].strip()

        return data

    def _write_validation_result(
        self,
        source_url: str,
        source_hash: str,
        validation_data: Dict[str, Any],
        is_valid: bool
    ):
        """
        Write validation result to document_validations table.

        Args:
            source_url: Document URL
            source_hash: Hash of source URL (for deduplication)
            validation_data: Parsed validation data from LLM
            is_valid: Whether document passed validation
        """
        query = """
            INSERT INTO document_validations (
                source_url, source_hash, is_technical_manual, validation_score,
                language_detected, document_type, manufacturer_detected,
                model_detected, validation_reason, validated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            ON CONFLICT (source_hash) DO UPDATE SET
                is_technical_manual = EXCLUDED.is_technical_manual,
                validation_score = EXCLUDED.validation_score,
                language_detected = EXCLUDED.language_detected,
                document_type = EXCLUDED.document_type,
                manufacturer_detected = EXCLUDED.manufacturer_detected,
                model_detected = EXCLUDED.model_detected,
                validation_reason = EXCLUDED.validation_reason,
                validated_at = EXCLUDED.validated_at
        """

        params = (
            source_url,
            source_hash,
            validation_data["is_technical_manual"],
            validation_data["score"],
            validation_data["language"],
            validation_data["document_type"],
            validation_data.get("manufacturer"),
            validation_data.get("model"),
            validation_data.get("reason"),
            datetime.now(timezone.utc)
        )

        self.db.execute_query(query, params, fetch_mode="none")

        logger.debug(
            f"Wrote validation result: {source_url[:50]}... → "
            f"score={validation_data['score']}, valid={is_valid}"
        )

    def _get_cached_validation(self, source_hash: str) -> Optional[Dict[str, Any]]:
        """
        Check if validation result already exists for this document.

        Args:
            source_hash: Hash of source URL

        Returns:
            Cached validation data or None if not found
        """
        query = """
            SELECT
                is_technical_manual, validation_score, language_detected,
                document_type, manufacturer_detected, model_detected,
                validation_reason
            FROM document_validations
            WHERE source_hash = $1
            AND validated_at > NOW() - INTERVAL '30 days'
        """

        result = self.db.execute_query(query, (source_hash,))

        if result:
            row = result[0]
            return {
                "is_technical_manual": row[0],
                "score": row[1],
                "language": row[2],
                "document_type": row[3],
                "manufacturer": row[4],
                "model": row[5],
                "reason": row[6]
            }

        return None

    def _build_result_from_db(self, cached: Dict[str, Any]) -> DocumentValidationResult:
        """
        Build DocumentValidationResult from cached database data.

        Args:
            cached: Cached validation data from database

        Returns:
            DocumentValidationResult
        """
        is_valid = (
            cached["score"] >= self.min_score and
            cached["is_technical_manual"] and
            cached["language"].lower() in ["en", "english"]
        )

        return DocumentValidationResult(
            is_valid=is_valid,
            score=cached["score"],
            is_technical_manual=cached["is_technical_manual"],
            document_type=cached["document_type"],
            language=cached["language"],
            manufacturer=cached.get("manufacturer"),
            model=cached.get("model"),
            reason=cached.get("reason")
        )

    def get_validation_stats(self) -> Dict[str, Any]:
        """
        Get validation statistics for monitoring.

        Returns:
            Dictionary with validation metrics
        """
        query = """
            SELECT
                COUNT(*) as total_validations,
                SUM(CASE WHEN is_technical_manual = TRUE
                    AND validation_score >= $1
                    AND language_detected IN ('en', 'english')
                    THEN 1 ELSE 0 END) as passed,
                AVG(validation_score) as avg_score,
                COUNT(DISTINCT manufacturer_detected) as unique_manufacturers
            FROM document_validations
            WHERE validated_at > NOW() - INTERVAL '7 days'
        """

        result = self.db.execute_query(query, (self.min_score,))

        if result:
            row = result[0]
            total = row[0] or 0
            passed = row[1] or 0

            return {
                "total_validations": total,
                "passed": passed,
                "rejected": total - passed,
                "pass_rate": (passed / total * 100) if total > 0 else 0.0,
                "avg_score": float(row[2]) if row[2] else 0.0,
                "unique_manufacturers": row[3] or 0
            }

        return {
            "total_validations": 0,
            "passed": 0,
            "rejected": 0,
            "pass_rate": 0.0,
            "avg_score": 0.0,
            "unique_manufacturers": 0
        }


# ============================================================================
# Helper Functions
# ============================================================================

def create_document_validator(db: DatabaseManager, min_score: int = 60) -> DocumentValidator:
    """
    Factory function for creating document validators.

    Args:
        db: DatabaseManager instance
        min_score: Minimum validation score (0-100) to pass

    Returns:
        DocumentValidator instance

    Example:
        >>> db = DatabaseManager()
        >>> validator = create_document_validator(db, min_score=65)
        >>> result = await validator.validate_document(url, content_sample)
        >>> if result.is_valid:
        >>>     # Proceed with ingestion
    """
    return DocumentValidator(db, min_score)
