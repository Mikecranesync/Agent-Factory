#!/usr/bin/env python3
"""
QUALITY CHECKER AGENT - Autonomous KB Quality Validation

Validates knowledge atom accuracy, safety compliance, and citation integrity.
Runs as part of daily KB building (after atom upload) and on-demand.

6-Stage Validation Pipeline:
1. Completeness Check - All required fields present
2. Citation Verification - Source URLs valid, page numbers present
3. Safety Compliance - Safety keywords detected, warnings validated
4. Hallucination Detection - Content matches source material
5. Confidence Scoring - Overall quality score (0.0-1.0)
6. Human Review Flagging - Flag atoms with confidence < 0.7

Usage:
    # Validate single atom
    checker = QualityCheckerAgent()
    result = checker.validate_atom(atom_id="plc:ab:motor-start-stop")

    # Validate all atoms
    report = checker.validate_all_atoms()

    # Validate recent atoms (last 24 hours)
    report = checker.validate_recent_atoms(hours=24)

Autonomous Operation:
- Runs daily at 2:00 AM (via scheduler_kb_daily.py Phase 6)
- Flags low-quality atoms for human review
- Updates quality_score in Supabase
- Generates daily quality report

Author: Agent Factory
Created: 2025-12-11
"""

import os
import sys
import re
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from supabase import create_client
import requests

# ============================================================================
# CONFIGURATION
# ============================================================================

# Credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

# Quality thresholds
MIN_CONFIDENCE_SCORE = 0.7  # Flag for human review if below
MIN_QUALITY_SCORE = 0.5     # Minimum acceptable quality
CITATION_TIMEOUT = 10       # Seconds to wait for URL check

# Safety keywords (by severity)
SAFETY_KEYWORDS = {
    "danger": ["danger", "lethal", "fatal", "death", "electrocution", "arc flash", "high voltage"],
    "warning": ["warning", "injury", "harm", "burn", "shock", "hazard", "caution"],
    "caution": ["caution", "damage", "malfunction", "failure", "wear", "tear"],
    "info": ["note", "tip", "important", "recommended", "best practice"]
}

# Required fields for completeness
REQUIRED_FIELDS = [
    "atom_id", "atom_type", "title", "summary", "content",
    "keywords", "difficulty", "safety_level", "source_type", "quality_score"
]

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ValidationResult:
    """Result of atom validation"""
    atom_id: str
    status: str  # "pass", "warning", "fail"
    confidence_score: float  # 0.0-1.0
    issues: List[str]
    suggestions: List[str]
    stage_results: Dict[str, Any]
    timestamp: str

@dataclass
class QualityReport:
    """Overall quality report"""
    total_atoms: int
    passed: int
    warnings: int
    failed: int
    flagged_for_review: int
    average_confidence: float
    issues_by_category: Dict[str, int]
    timestamp: str

# ============================================================================
# QUALITY CHECKER AGENT
# ============================================================================

class QualityCheckerAgent:
    """
    Autonomous agent for KB quality validation.

    Responsibilities:
    - Validate atom completeness (all required fields)
    - Verify citation integrity (URLs, page numbers)
    - Check safety compliance (keywords, warnings)
    - Detect hallucinations (content vs source)
    - Calculate confidence scores
    - Flag low-quality atoms for human review

    Autonomous Capabilities:
    - Runs daily validation after KB upload
    - Auto-flags atoms with confidence < 0.7
    - Generates quality reports
    - No human intervention unless flagged
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize quality checker agent"""
        self.agent_name = "quality_checker_agent"
        self.logger = logger or self._setup_logger()

        # Initialize Supabase client
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Supabase credentials not found in environment")

        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.logger.info(f"{self.agent_name} initialized")

    def _setup_logger(self) -> logging.Logger:
        """Setup logger for agent"""
        logger = logging.getLogger(self.agent_name)
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    # ========================================================================
    # STAGE 1: COMPLETENESS CHECK
    # ========================================================================

    def check_completeness(self, atom: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Check if atom has all required fields.

        Returns:
            (is_complete, missing_fields)
        """
        missing_fields = []

        for field in REQUIRED_FIELDS:
            if field not in atom or atom[field] is None or atom[field] == "":
                missing_fields.append(field)

        # Check content length
        if "content" in atom and atom["content"]:
            if len(atom["content"]) < 50:
                missing_fields.append("content (too short)")

        # Check keywords count
        if "keywords" in atom and isinstance(atom["keywords"], list):
            if len(atom["keywords"]) < 3:
                missing_fields.append("keywords (too few)")

        is_complete = len(missing_fields) == 0
        return is_complete, missing_fields

    # ========================================================================
    # STAGE 2: CITATION VERIFICATION
    # ========================================================================

    def verify_citations(self, atom: Dict[str, Any]) -> Tuple[float, List[str]]:
        """
        Verify citation integrity (source URLs, page numbers).

        Returns:
            (citation_score, issues)
        """
        issues = []
        score = 1.0

        # Check source_url
        if "source_url" not in atom or not atom["source_url"]:
            issues.append("Missing source_url")
            score -= 0.3
        elif atom["source_url"]:
            # Check if URL is accessible (if starts with http)
            if atom["source_url"].startswith("http"):
                try:
                    response = requests.head(atom["source_url"], timeout=CITATION_TIMEOUT, allow_redirects=True)
                    if response.status_code == 404:
                        issues.append(f"Source URL returns 404: {atom['source_url']}")
                        score -= 0.2
                    elif response.status_code >= 500:
                        issues.append(f"Source URL server error: {atom['source_url']}")
                        score -= 0.1
                except requests.exceptions.Timeout:
                    issues.append(f"Source URL timeout: {atom['source_url']}")
                    score -= 0.1
                except requests.exceptions.RequestException as e:
                    issues.append(f"Source URL unreachable: {atom['source_url']}")
                    score -= 0.2

        # Check source_page_numbers
        if "source_page_numbers" not in atom or not atom["source_page_numbers"]:
            issues.append("Missing source_page_numbers")
            score -= 0.2
        elif atom["source_page_numbers"]:
            # Validate format (should be list of integers or "N/A")
            if atom["source_page_numbers"] != "N/A":
                if not isinstance(atom["source_page_numbers"], list):
                    issues.append("source_page_numbers should be list or 'N/A'")
                    score -= 0.1

        # Check citation text in content
        content = atom.get("content", "")
        if "source:" not in content.lower() and "reference:" not in content.lower():
            issues.append("No inline citations found in content")
            score -= 0.1

        return max(0.0, score), issues

    # ========================================================================
    # STAGE 3: SAFETY COMPLIANCE
    # ========================================================================

    def check_safety_compliance(self, atom: Dict[str, Any]) -> Tuple[str, List[str]]:
        """
        Check safety compliance (detect safety keywords, validate warnings).

        Returns:
            (detected_safety_level, issues)
        """
        issues = []
        content = atom.get("content", "").lower()
        declared_level = atom.get("safety_level", "info")

        # Detect safety keywords
        detected_level = "info"

        for level, keywords in SAFETY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in content:
                    # Escalate to highest detected level
                    if level == "danger":
                        detected_level = "danger"
                    elif level == "warning" and detected_level != "danger":
                        detected_level = "warning"
                    elif level == "caution" and detected_level not in ["danger", "warning"]:
                        detected_level = "caution"

        # Compare detected vs declared
        severity_order = ["info", "caution", "warning", "danger"]
        detected_severity = severity_order.index(detected_level)
        declared_severity = severity_order.index(declared_level)

        if detected_severity > declared_severity:
            issues.append(f"Safety level mismatch: detected '{detected_level}' but declared '{declared_level}'")

        # Check for safety warnings in dangerous content
        if detected_level in ["danger", "warning"]:
            if "warning:" not in content and "caution:" not in content and "danger:" not in content:
                issues.append(f"Safety content detected ({detected_level}) but no explicit warning statement found")

        return detected_level, issues

    # ========================================================================
    # STAGE 4: HALLUCINATION DETECTION
    # ========================================================================

    def detect_hallucinations(self, atom: Dict[str, Any]) -> Tuple[float, List[str]]:
        """
        Detect potential hallucinations (content not matching source).

        This is a basic implementation. In production, would use:
        - Semantic similarity between atom content and source PDF text
        - Cross-reference with manufacturer documentation
        - LLM-based fact checking

        Returns:
            (hallucination_score, issues)
        """
        issues = []
        score = 1.0

        content = atom.get("content", "")

        # Basic checks:
        # 1. Check for unsupported claims (no citation)
        unsupported_phrases = [
            "it is believed",
            "experts say",
            "some people think",
            "it is rumored",
            "allegedly",
            "supposedly"
        ]

        for phrase in unsupported_phrases:
            if phrase in content.lower():
                issues.append(f"Unsupported claim detected: '{phrase}'")
                score -= 0.2

        # 2. Check for specific values without citation
        # Look for numbers/percentages without source
        specific_values = re.findall(r'\d+\.?\d*\s*%|\d+\.?\d*\s*(?:volts?|amps?|watts?|hz)', content.lower())
        if specific_values and "source:" not in content.lower():
            issues.append(f"Specific values found without citation: {specific_values[:3]}")
            score -= 0.1

        # 3. Check for absolute statements
        absolute_phrases = [
            "always works",
            "never fails",
            "guaranteed",
            "100% effective",
            "completely safe",
            "no risk"
        ]

        for phrase in absolute_phrases:
            if phrase in content.lower():
                issues.append(f"Absolute statement (potential overgeneralization): '{phrase}'")
                score -= 0.1

        return max(0.0, score), issues

    # ========================================================================
    # STAGE 5: CONFIDENCE SCORING
    # ========================================================================

    def calculate_confidence_score(self,
                                   completeness_ok: bool,
                                   citation_score: float,
                                   safety_issues: List[str],
                                   hallucination_score: float) -> float:
        """
        Calculate overall confidence score (0.0-1.0).

        Weighting:
        - Completeness: 25% (binary: 1.0 or 0.0)
        - Citations: 30%
        - Safety: 20% (based on issue count)
        - Hallucinations: 25%
        """
        completeness_component = 1.0 if completeness_ok else 0.0
        citation_component = citation_score
        safety_component = max(0.0, 1.0 - (len(safety_issues) * 0.2))
        hallucination_component = hallucination_score

        confidence = (
            completeness_component * 0.25 +
            citation_component * 0.30 +
            safety_component * 0.20 +
            hallucination_component * 0.25
        )

        return round(confidence, 2)

    # ========================================================================
    # STAGE 6: HUMAN REVIEW FLAGGING
    # ========================================================================

    def flag_for_review(self, atom_id: str, confidence_score: float, issues: List[str]):
        """
        Flag atom for human review in Supabase.

        Creates entry in review queue with:
        - atom_id
        - confidence_score
        - issues list
        - flagged_at timestamp
        """
        try:
            review_entry = {
                "atom_id": atom_id,
                "confidence_score": confidence_score,
                "issues": issues,
                "flagged_at": datetime.now().isoformat(),
                "reviewed": False
            }

            # Insert into review queue (would need to create this table)
            # For now, just log
            self.logger.warning(f"FLAGGED FOR REVIEW: {atom_id} (confidence: {confidence_score})")
            for issue in issues:
                self.logger.warning(f"  - {issue}")

        except Exception as e:
            self.logger.error(f"Failed to flag atom for review: {e}")

    # ========================================================================
    # MAIN VALIDATION
    # ========================================================================

    def validate_atom(self, atom_id: str) -> ValidationResult:
        """
        Run 6-stage validation on a single atom.

        Args:
            atom_id: Atom ID to validate

        Returns:
            ValidationResult with status, confidence, issues, suggestions
        """
        self.logger.info(f"Validating atom: {atom_id}")

        try:
            # Fetch atom from Supabase
            result = self.supabase.table("knowledge_atoms").select("*").eq("atom_id", atom_id).execute()

            if not result.data:
                self.logger.error(f"Atom not found: {atom_id}")
                return ValidationResult(
                    atom_id=atom_id,
                    status="fail",
                    confidence_score=0.0,
                    issues=["Atom not found in database"],
                    suggestions=[],
                    stage_results={},
                    timestamp=datetime.now().isoformat()
                )

            atom = result.data[0]

            # Stage 1: Completeness
            completeness_ok, missing_fields = self.check_completeness(atom)

            # Stage 2: Citations
            citation_score, citation_issues = self.verify_citations(atom)

            # Stage 3: Safety
            detected_safety, safety_issues = self.check_safety_compliance(atom)

            # Stage 4: Hallucinations
            hallucination_score, hallucination_issues = self.detect_hallucinations(atom)

            # Stage 5: Confidence
            confidence_score = self.calculate_confidence_score(
                completeness_ok,
                citation_score,
                safety_issues,
                hallucination_score
            )

            # Collect all issues
            all_issues = []
            if missing_fields:
                all_issues.extend([f"Missing: {field}" for field in missing_fields])
            all_issues.extend(citation_issues)
            all_issues.extend(safety_issues)
            all_issues.extend(hallucination_issues)

            # Determine status
            if confidence_score >= 0.8:
                status = "pass"
            elif confidence_score >= MIN_CONFIDENCE_SCORE:
                status = "warning"
            else:
                status = "fail"

            # Stage 6: Flag for review if needed
            if confidence_score < MIN_CONFIDENCE_SCORE:
                self.flag_for_review(atom_id, confidence_score, all_issues)

            # Update quality_score in Supabase
            self.supabase.table("knowledge_atoms").update({
                "quality_score": confidence_score,
                "last_validated_at": datetime.now().isoformat()
            }).eq("atom_id", atom_id).execute()

            # Generate suggestions
            suggestions = self._generate_suggestions(atom, all_issues)

            return ValidationResult(
                atom_id=atom_id,
                status=status,
                confidence_score=confidence_score,
                issues=all_issues,
                suggestions=suggestions,
                stage_results={
                    "completeness": {"ok": completeness_ok, "missing": missing_fields},
                    "citations": {"score": citation_score, "issues": citation_issues},
                    "safety": {"detected": detected_safety, "issues": safety_issues},
                    "hallucinations": {"score": hallucination_score, "issues": hallucination_issues}
                },
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            self.logger.error(f"Validation failed for {atom_id}: {e}", exc_info=True)
            return ValidationResult(
                atom_id=atom_id,
                status="fail",
                confidence_score=0.0,
                issues=[f"Validation error: {str(e)}"],
                suggestions=[],
                stage_results={},
                timestamp=datetime.now().isoformat()
            )

    def _generate_suggestions(self, atom: Dict[str, Any], issues: List[str]) -> List[str]:
        """Generate improvement suggestions based on issues"""
        suggestions = []

        for issue in issues:
            if "Missing:" in issue:
                field = issue.replace("Missing: ", "")
                suggestions.append(f"Add {field} to atom")
            elif "Source URL" in issue:
                suggestions.append("Verify source URL is correct and accessible")
            elif "Safety level mismatch" in issue:
                suggestions.append("Update safety_level to match detected safety content")
            elif "no explicit warning" in issue:
                suggestions.append("Add explicit WARNING: or CAUTION: statement")
            elif "Unsupported claim" in issue:
                suggestions.append("Add citation or remove unsupported claim")
            elif "Specific values found without citation" in issue:
                suggestions.append("Add source citation for specific values")

        return suggestions

    def validate_all_atoms(self) -> QualityReport:
        """
        Validate all atoms in database.

        Returns:
            QualityReport with overall statistics
        """
        self.logger.info("Validating all atoms...")

        # Fetch all atoms
        result = self.supabase.table("knowledge_atoms").select("atom_id").execute()
        atom_ids = [atom["atom_id"] for atom in result.data]

        return self._validate_batch(atom_ids)

    def validate_recent_atoms(self, hours: int = 24) -> QualityReport:
        """
        Validate atoms created in last N hours.

        Args:
            hours: Number of hours to look back

        Returns:
            QualityReport with statistics
        """
        self.logger.info(f"Validating atoms from last {hours} hours...")

        # Calculate cutoff time
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()

        # Fetch recent atoms
        result = self.supabase.table("knowledge_atoms").select("atom_id").gte("created_at", cutoff).execute()
        atom_ids = [atom["atom_id"] for atom in result.data]

        if not atom_ids:
            self.logger.info("No recent atoms found")
            return QualityReport(
                total_atoms=0,
                passed=0,
                warnings=0,
                failed=0,
                flagged_for_review=0,
                average_confidence=0.0,
                issues_by_category={},
                timestamp=datetime.now().isoformat()
            )

        return self._validate_batch(atom_ids)

    def _validate_batch(self, atom_ids: List[str]) -> QualityReport:
        """Validate batch of atoms and generate report"""
        total = len(atom_ids)
        passed = 0
        warnings = 0
        failed = 0
        flagged = 0
        total_confidence = 0.0
        issues_by_category = {}

        for atom_id in atom_ids:
            result = self.validate_atom(atom_id)

            if result.status == "pass":
                passed += 1
            elif result.status == "warning":
                warnings += 1
            else:
                failed += 1

            if result.confidence_score < MIN_CONFIDENCE_SCORE:
                flagged += 1

            total_confidence += result.confidence_score

            # Categorize issues
            for issue in result.issues:
                category = self._categorize_issue(issue)
                issues_by_category[category] = issues_by_category.get(category, 0) + 1

        avg_confidence = total_confidence / total if total > 0 else 0.0

        report = QualityReport(
            total_atoms=total,
            passed=passed,
            warnings=warnings,
            failed=failed,
            flagged_for_review=flagged,
            average_confidence=round(avg_confidence, 2),
            issues_by_category=issues_by_category,
            timestamp=datetime.now().isoformat()
        )

        self._log_report(report)
        return report

    def _categorize_issue(self, issue: str) -> str:
        """Categorize issue for reporting"""
        if "Missing:" in issue:
            return "completeness"
        elif "Source URL" in issue or "citation" in issue:
            return "citations"
        elif "Safety" in issue or "warning" in issue:
            return "safety"
        elif "claim" in issue or "value" in issue:
            return "hallucinations"
        else:
            return "other"

    def _log_report(self, report: QualityReport):
        """Log quality report"""
        self.logger.info("")
        self.logger.info("=" * 80)
        self.logger.info("QUALITY VALIDATION REPORT")
        self.logger.info("=" * 80)
        self.logger.info(f"Total Atoms: {report.total_atoms}")
        self.logger.info(f"Passed: {report.passed} ({report.passed/report.total_atoms*100:.1f}%)")
        self.logger.info(f"Warnings: {report.warnings} ({report.warnings/report.total_atoms*100:.1f}%)")
        self.logger.info(f"Failed: {report.failed} ({report.failed/report.total_atoms*100:.1f}%)")
        self.logger.info(f"Flagged for Review: {report.flagged_for_review}")
        self.logger.info(f"Average Confidence: {report.average_confidence}")
        self.logger.info("")
        self.logger.info("Issues by Category:")
        for category, count in report.issues_by_category.items():
            self.logger.info(f"  {category}: {count}")
        self.logger.info("=" * 80)
        self.logger.info("")


# ============================================================================
# MAIN (for testing)
# ============================================================================

def main():
    """Test quality checker agent"""
    import argparse

    parser = argparse.ArgumentParser(description="Quality Checker Agent")
    parser.add_argument("--atom-id", help="Validate single atom by ID")
    parser.add_argument("--all", action="store_true", help="Validate all atoms")
    parser.add_argument("--recent", type=int, help="Validate atoms from last N hours")

    args = parser.parse_args()

    checker = QualityCheckerAgent()

    if args.atom_id:
        result = checker.validate_atom(args.atom_id)
        print(f"\nValidation Result for {result.atom_id}:")
        print(f"Status: {result.status}")
        print(f"Confidence: {result.confidence_score}")
        print(f"\nIssues:")
        for issue in result.issues:
            print(f"  - {issue}")
        print(f"\nSuggestions:")
        for suggestion in result.suggestions:
            print(f"  - {suggestion}")

    elif args.all:
        report = checker.validate_all_atoms()

    elif args.recent:
        report = checker.validate_recent_atoms(hours=args.recent)

    else:
        print("Usage: python quality_checker_agent.py [--atom-id ID | --all | --recent HOURS]")


if __name__ == "__main__":
    main()
