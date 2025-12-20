"""
Content validation pipeline for research sources.

Ensures accuracy and quality before adding content to knowledge base.
"""

import logging
import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Union
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Content validation severity levels."""
    PASS = "pass"  # Content is valid
    WARNING = "warning"  # Minor issues, but acceptable
    FAIL = "fail"  # Content should not be added to KB


@dataclass
class ValidationResult:
    """Result of content validation."""

    level: ValidationLevel
    score: float  # 0.0 to 1.0 (quality score)
    issues: List[str]  # List of validation issues found
    metadata: Dict[str, Any]  # Additional validation metadata


class ContentValidator:
    """
    Validates research content before knowledge base ingestion.

    Checks for:
    - Safety compliance (no dangerous procedures)
    - Citation integrity (sources are valid)
    - Content quality (not spam, relevant)
    - Technical accuracy (basic sanity checks)
    """

    # Dangerous keywords that indicate unsafe content
    SAFETY_RED_FLAGS = [
        "bypass safety",
        "disable interlock",
        "remove guard",
        "hot work without permit",
        "arc flash without ppe",
        "energized maintenance",
        "defeat safety",
    ]

    # Spam/low-quality indicators
    SPAM_INDICATORS = [
        "click here",
        "buy now",
        "limited time offer",
        "100% guaranteed",
        "earn money fast",
        "work from home",
    ]

    # Minimum content length for quality check
    MIN_CONTENT_LENGTH = 100  # characters

    def __init__(self, min_quality_score: float = 0.5):
        """
        Initialize content validator.

        Args:
            min_quality_score: Minimum quality score to pass (0.0 to 1.0)
        """
        self.min_quality_score = min_quality_score

    def validate(
        self,
        content: str,
        source_url: str,
        source_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Validate research content.

        Args:
            content: Text content to validate
            source_url: URL of the source
            source_type: Type of source (stackoverflow, reddit, youtube, etc.)
            metadata: Additional metadata about the source

        Returns:
            ValidationResult with validation status and score
        """
        metadata = metadata or {}
        issues = []
        score = 1.0  # Start with perfect score, deduct for issues

        # Check 1: Safety compliance
        safety_issues = self._check_safety(content)
        if safety_issues:
            issues.extend([f"Safety: {issue}" for issue in safety_issues])
            score -= 0.3  # Major penalty for safety issues

        # Check 2: Spam detection
        spam_issues = self._check_spam(content)
        if spam_issues:
            issues.extend([f"Spam: {issue}" for issue in spam_issues])
            score -= 0.4  # Major penalty for spam

        # Check 3: Content quality
        quality_issues = self._check_quality(content, metadata)
        if quality_issues:
            issues.extend([f"Quality: {issue}" for issue in quality_issues])
            score -= 0.1 * len(quality_issues)  # Minor penalties

        # Check 4: Citation integrity
        citation_issues = self._check_citations(content, source_url)
        if citation_issues:
            issues.extend([f"Citation: {issue}" for issue in citation_issues])
            score -= 0.05 * len(citation_issues)  # Minor penalties

        # Check 5: Technical relevance
        relevance_issues = self._check_relevance(content, source_type)
        if relevance_issues:
            issues.extend([f"Relevance: {issue}" for issue in relevance_issues])
            score -= 0.1 * len(relevance_issues)

        # Clamp score to [0.0, 1.0]
        score = max(0.0, min(1.0, score))

        # Determine validation level
        if score < 0.3:
            level = ValidationLevel.FAIL
        elif score < self.min_quality_score:
            level = ValidationLevel.WARNING
        else:
            level = ValidationLevel.PASS

        result = ValidationResult(
            level=level,
            score=score,
            issues=issues,
            metadata={
                "source_url": source_url,
                "source_type": source_type,
                "content_length": len(content),
            }
        )

        logger.info(f"Validation result: {level.value} (score: {score:.2f})")
        return result

    def validate_batch(
        self,
        sources: List[Dict[str, Any]]
    ) -> List[ValidationResult]:
        """
        Validate multiple sources.

        Args:
            sources: List of dicts with keys: content, url, source_type, metadata

        Returns:
            List of ValidationResult objects
        """
        results = []

        for source in sources:
            result = self.validate(
                content=source.get("content", ""),
                source_url=source.get("url", ""),
                source_type=source.get("source_type", "unknown"),
                metadata=source.get("metadata", {})
            )
            results.append(result)

        passed = sum(1 for r in results if r.level == ValidationLevel.PASS)
        logger.info(f"Batch validation: {passed}/{len(results)} passed")

        return results

    def _check_safety(self, content: str) -> List[str]:
        """
        Check for safety compliance issues.

        Args:
            content: Text content

        Returns:
            List of safety issues found
        """
        issues = []
        content_lower = content.lower()

        for red_flag in self.SAFETY_RED_FLAGS:
            if red_flag in content_lower:
                issues.append(f"Dangerous procedure mentioned: '{red_flag}'")

        return issues

    def _check_spam(self, content: str) -> List[str]:
        """
        Check for spam or low-quality content indicators.

        Args:
            content: Text content

        Returns:
            List of spam issues found
        """
        issues = []
        content_lower = content.lower()

        for indicator in self.SPAM_INDICATORS:
            if indicator in content_lower:
                issues.append(f"Spam indicator found: '{indicator}'")

        # Check for excessive capitalization (spam often uses ALL CAPS)
        caps_ratio = sum(1 for c in content if c.isupper()) / max(len(content), 1)
        if caps_ratio > 0.3:  # More than 30% uppercase
            issues.append(f"Excessive capitalization ({caps_ratio:.1%})")

        # Check for excessive special characters
        special_chars = re.findall(r'[!?@#$%^&*]', content)
        if len(special_chars) > len(content) * 0.05:  # More than 5%
            issues.append(f"Excessive special characters ({len(special_chars)} found)")

        return issues

    def _check_quality(
        self,
        content: str,
        metadata: Dict[str, Any]
    ) -> List[str]:
        """
        Check content quality.

        Args:
            content: Text content
            metadata: Source metadata

        Returns:
            List of quality issues found
        """
        issues = []

        # Check minimum length
        if len(content) < self.MIN_CONTENT_LENGTH:
            issues.append(f"Content too short ({len(content)} chars, min {self.MIN_CONTENT_LENGTH})")

        # Check for gibberish (too many consecutive consonants)
        gibberish_matches = re.findall(r'[bcdfghjklmnpqrstvwxyz]{7,}', content.lower())
        if gibberish_matches:
            issues.append(f"Possible gibberish text detected")

        # Check for proper sentence structure (has periods)
        if len(content) > 200 and '.' not in content:
            issues.append("No sentence structure (no periods found)")

        return issues

    def _check_citations(self, content: str, source_url: str) -> List[str]:
        """
        Check citation integrity.

        Args:
            content: Text content
            source_url: Source URL

        Returns:
            List of citation issues found
        """
        issues = []

        # Check for broken URL references in content
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)

        # Warn if content has many external links (possible spam)
        if len(urls) > 5:
            issues.append(f"Too many external links ({len(urls)} found)")

        return issues

    def _check_relevance(self, content: str, source_type: str) -> List[str]:
        """
        Check technical relevance to industrial automation.

        Args:
            content: Text content
            source_type: Source type

        Returns:
            List of relevance issues found
        """
        issues = []

        # Industrial automation keywords
        TECHNICAL_KEYWORDS = [
            "plc", "automation", "control", "industrial", "scada",
            "hmi", "motor", "drive", "sensor", "actuator", "relay",
            "ethernet", "modbus", "profibus", "profinet", "devicenet",
            "ladder", "logic", "program", "fault", "troubleshoot",
            "panel", "wiring", "electrical", "maintenance", "repair"
        ]

        content_lower = content.lower()

        # Count technical keyword matches
        keyword_matches = sum(1 for keyword in TECHNICAL_KEYWORDS if keyword in content_lower)

        # Warn if no technical keywords found
        if keyword_matches == 0:
            issues.append("No industrial automation keywords found - may be off-topic")

        # Warn if very few matches (less than 2)
        elif keyword_matches < 2:
            issues.append(f"Limited technical relevance (only {keyword_matches} keywords)")

        return issues


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    validator = ContentValidator(min_quality_score=0.5)

    # Test case 1: Good technical content
    good_content = """
    To troubleshoot a Siemens S7-1200 PLC ethernet connection issue:
    1. Check physical cable connection (CAT5e or better)
    2. Verify IP address configuration in TIA Portal
    3. Ensure PLC and PC are on same subnet
    4. Use PING command to test connectivity
    5. Check firewall settings on PC
    """

    result = validator.validate(
        content=good_content,
        source_url="https://stackoverflow.com/q/123",
        source_type="stackoverflow"
    )

    print(f"\nTest 1 - Good Content:")
    print(f"  Level: {result.level.value}")
    print(f"  Score: {result.score:.2f}")
    print(f"  Issues: {result.issues or 'None'}")

    # Test case 2: Spam content
    spam_content = """
    CLICK HERE TO BUY NOW!!! 100% GUARANTEED!!!
    Work from home and earn money fast!!!
    """

    result = validator.validate(
        content=spam_content,
        source_url="https://spam.com/page",
        source_type="unknown"
    )

    print(f"\nTest 2 - Spam Content:")
    print(f"  Level: {result.level.value}")
    print(f"  Score: {result.score:.2f}")
    print(f"  Issues: {result.issues}")

    # Test case 3: Safety issue
    unsafe_content = """
    To fix the motor quickly, just bypass safety interlocks
    and perform energized maintenance. This saves time.
    """

    result = validator.validate(
        content=unsafe_content,
        source_url="https://bad-advice.com/post",
        source_type="forum"
    )

    print(f"\nTest 3 - Unsafe Content:")
    print(f"  Level: {result.level.value}")
    print(f"  Score: {result.score:.2f}")
    print(f"  Issues: {result.issues}")
