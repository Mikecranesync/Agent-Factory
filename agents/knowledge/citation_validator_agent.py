#!/usr/bin/env python3
"""
CITATION VALIDATOR AGENT - Autonomous Citation Integrity Management

Validates source URL health, detects link rot, finds Wayback Machine alternatives.
Runs monthly to ensure all citations remain accessible.

Responsibilities:
1. Source URL Health Checking - Detect 404s, timeouts, server errors
2. Link Rot Detection - Track URLs that become unavailable over time
3. Wayback Machine Integration - Auto-find archived versions of broken URLs
4. Citation Integrity Scoring - Overall citation health score
5. Auto-Update Citations - Replace broken URLs with Wayback alternatives

Usage:
    # Validate single atom's citations
    validator = CitationValidatorAgent()
    result = validator.validate_citations(atom_id="plc:ab:motor-start-stop")

    # Validate all citations
    report = validator.validate_all_citations()

    # Find Wayback alternative for broken URL
    archive_url = validator.find_wayback_alternative(url="https://example.com/manual.pdf")

Autonomous Operation:
- Runs monthly (via scheduler_kb_weekly.py)
- Auto-updates broken URLs with Wayback alternatives
- Flags atoms with broken citations (no archive found)
- Generates monthly citation health report

Author: Agent Factory
Created: 2025-12-11
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv
import time

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

# URL checking settings
URL_CHECK_TIMEOUT = 10      # Seconds to wait for URL response
MAX_RETRIES = 3             # Retry count for failed URLs
RETRY_DELAY = 2             # Seconds between retries
USER_AGENT = "AgentFactory-CitationValidator/1.0"  # Identify ourselves

# Wayback Machine API
WAYBACK_API = "https://archive.org/wayback/available"
WAYBACK_SAVE_API = "https://web.archive.org/save/"

# Citation health thresholds
MIN_CITATION_SCORE = 0.7    # Flag if below this

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class URLHealthResult:
    """Result of URL health check"""
    url: str
    status: str  # "ok", "redirect", "broken", "timeout", "error"
    status_code: Optional[int]
    redirect_url: Optional[str]
    error_message: Optional[str]
    response_time_ms: Optional[int]
    checked_at: str

@dataclass
class CitationValidationResult:
    """Result of citation validation for an atom"""
    atom_id: str
    total_citations: int
    valid_citations: int
    broken_citations: List[Dict[str, Any]]
    archived_alternatives: List[Dict[str, Any]]
    citation_score: float  # 0.0-1.0
    needs_review: bool
    timestamp: str

@dataclass
class CitationHealthReport:
    """Overall citation health report"""
    total_atoms: int
    atoms_with_valid_citations: int
    atoms_with_broken_citations: int
    total_urls_checked: int
    valid_urls: int
    broken_urls: int
    archived_urls: int
    average_citation_score: float
    timestamp: str

# ============================================================================
# CITATION VALIDATOR AGENT
# ============================================================================

class CitationValidatorAgent:
    """
    Autonomous agent for citation integrity management.

    Responsibilities:
    - Check source URL health (404, timeout, server errors)
    - Detect link rot over time
    - Find Wayback Machine alternatives for broken URLs
    - Auto-update citations with archived versions
    - Generate citation health reports

    Autonomous Capabilities:
    - Runs monthly validation checks
    - Auto-updates broken URLs (with approval gate)
    - Flags atoms with missing citations
    - No human intervention unless auto-fix fails
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize citation validator agent"""
        self.agent_name = "citation_validator_agent"
        self.logger = logger or self._setup_logger()

        # Initialize Supabase client
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Supabase credentials not found in environment")

        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.logger.info(f"{self.agent_name} initialized")

        # Session for persistent connections
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

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
    # URL HEALTH CHECKING
    # ========================================================================

    def check_url_health(self, url: str) -> URLHealthResult:
        """
        Check if URL is accessible.

        Args:
            url: URL to check

        Returns:
            URLHealthResult with status and details
        """
        # Skip non-HTTP URLs (local files, etc.)
        if not url.startswith("http"):
            return URLHealthResult(
                url=url,
                status="ok",  # Assume local files are OK
                status_code=None,
                redirect_url=None,
                error_message=None,
                response_time_ms=None,
                checked_at=datetime.now().isoformat()
            )

        for attempt in range(MAX_RETRIES):
            try:
                start_time = time.time()

                # Use HEAD request (faster than GET)
                response = self.session.head(
                    url,
                    timeout=URL_CHECK_TIMEOUT,
                    allow_redirects=True
                )

                response_time_ms = int((time.time() - start_time) * 1000)

                # Determine status
                if response.status_code == 200:
                    status = "ok"
                elif 300 <= response.status_code < 400:
                    status = "redirect"
                elif response.status_code == 404:
                    status = "broken"
                elif response.status_code >= 500:
                    status = "error"
                else:
                    status = "ok"  # 2xx and other successful codes

                redirect_url = response.url if response.url != url else None

                return URLHealthResult(
                    url=url,
                    status=status,
                    status_code=response.status_code,
                    redirect_url=redirect_url,
                    error_message=None,
                    response_time_ms=response_time_ms,
                    checked_at=datetime.now().isoformat()
                )

            except requests.exceptions.Timeout:
                if attempt < MAX_RETRIES - 1:
                    self.logger.warning(f"Timeout checking {url}, retry {attempt + 1}/{MAX_RETRIES}")
                    time.sleep(RETRY_DELAY)
                    continue

                return URLHealthResult(
                    url=url,
                    status="timeout",
                    status_code=None,
                    redirect_url=None,
                    error_message="Request timeout",
                    response_time_ms=None,
                    checked_at=datetime.now().isoformat()
                )

            except requests.exceptions.RequestException as e:
                if attempt < MAX_RETRIES - 1:
                    self.logger.warning(f"Error checking {url}, retry {attempt + 1}/{MAX_RETRIES}")
                    time.sleep(RETRY_DELAY)
                    continue

                return URLHealthResult(
                    url=url,
                    status="error",
                    status_code=None,
                    redirect_url=None,
                    error_message=str(e),
                    response_time_ms=None,
                    checked_at=datetime.now().isoformat()
                )

        # Should never reach here
        return URLHealthResult(
            url=url,
            status="error",
            status_code=None,
            redirect_url=None,
            error_message="Max retries exceeded",
            response_time_ms=None,
            checked_at=datetime.now().isoformat()
        )

    # ========================================================================
    # WAYBACK MACHINE INTEGRATION
    # ========================================================================

    def find_wayback_alternative(self, url: str) -> Optional[str]:
        """
        Find Wayback Machine archived version of URL.

        Args:
            url: Broken URL to find alternative for

        Returns:
            Wayback Machine URL if found, None otherwise
        """
        try:
            self.logger.info(f"Searching Wayback Machine for: {url}")

            # Query Wayback API
            response = self.session.get(
                WAYBACK_API,
                params={"url": url},
                timeout=URL_CHECK_TIMEOUT
            )

            if response.status_code != 200:
                self.logger.warning(f"Wayback API returned {response.status_code}")
                return None

            data = response.json()

            # Check if archived snapshot exists
            if "archived_snapshots" in data and "closest" in data["archived_snapshots"]:
                snapshot = data["archived_snapshots"]["closest"]
                if snapshot.get("available"):
                    archive_url = snapshot["url"]
                    archive_date = snapshot.get("timestamp", "")
                    self.logger.info(f"Found archive from {archive_date}: {archive_url}")
                    return archive_url

            self.logger.info(f"No Wayback archive found for {url}")
            return None

        except Exception as e:
            self.logger.error(f"Wayback search failed: {e}")
            return None

    def save_to_wayback(self, url: str) -> Optional[str]:
        """
        Save URL to Wayback Machine (create new snapshot).

        Args:
            url: URL to save

        Returns:
            Wayback Machine URL if saved, None otherwise
        """
        try:
            self.logger.info(f"Saving to Wayback Machine: {url}")

            # Request save
            response = self.session.get(
                f"{WAYBACK_SAVE_API}{url}",
                timeout=30  # Longer timeout for saving
            )

            if response.status_code == 200:
                # Extract Wayback URL from response
                wayback_url = response.url
                self.logger.info(f"Saved to Wayback: {wayback_url}")
                return wayback_url

            return None

        except Exception as e:
            self.logger.error(f"Wayback save failed: {e}")
            return None

    # ========================================================================
    # CITATION VALIDATION
    # ========================================================================

    def validate_citations(self, atom_id: str) -> CitationValidationResult:
        """
        Validate all citations for a single atom.

        Args:
            atom_id: Atom ID to validate

        Returns:
            CitationValidationResult with citation health details
        """
        self.logger.info(f"Validating citations for atom: {atom_id}")

        try:
            # Fetch atom from Supabase
            result = self.supabase.table("knowledge_atoms").select("*").eq("atom_id", atom_id).execute()

            if not result.data:
                self.logger.error(f"Atom not found: {atom_id}")
                return CitationValidationResult(
                    atom_id=atom_id,
                    total_citations=0,
                    valid_citations=0,
                    broken_citations=[],
                    archived_alternatives=[],
                    citation_score=0.0,
                    needs_review=True,
                    timestamp=datetime.now().isoformat()
                )

            atom = result.data[0]

            # Collect all URLs to check
            urls_to_check = []

            # Primary source URL
            if atom.get("source_url"):
                urls_to_check.append({
                    "type": "source_url",
                    "url": atom["source_url"]
                })

            # Additional citations in content
            # (Could parse markdown links, but for now just check source_url)

            total_citations = len(urls_to_check)
            valid_citations = 0
            broken_citations = []
            archived_alternatives = []

            # Check each URL
            for citation in urls_to_check:
                url = citation["url"]
                health = self.check_url_health(url)

                if health.status == "ok":
                    valid_citations += 1

                elif health.status in ["broken", "timeout", "error"]:
                    # URL is broken - try to find Wayback alternative
                    archive_url = self.find_wayback_alternative(url)

                    broken_info = {
                        "url": url,
                        "type": citation["type"],
                        "status": health.status,
                        "error": health.error_message
                    }

                    if archive_url:
                        broken_info["wayback_url"] = archive_url
                        archived_alternatives.append(broken_info)
                        self.logger.info(f"Found Wayback alternative for {url}")
                    else:
                        broken_citations.append(broken_info)
                        self.logger.warning(f"No Wayback alternative found for {url}")

                elif health.status == "redirect":
                    # Follow redirect, consider valid
                    valid_citations += 1
                    self.logger.info(f"URL redirects to {health.redirect_url}")

            # Calculate citation score
            if total_citations > 0:
                citation_score = valid_citations / total_citations
            else:
                citation_score = 0.0

            # Add archived alternatives to score (partial credit)
            if archived_alternatives:
                citation_score += (len(archived_alternatives) / total_citations) * 0.5

            citation_score = min(1.0, citation_score)

            # Determine if needs review
            needs_review = citation_score < MIN_CITATION_SCORE

            return CitationValidationResult(
                atom_id=atom_id,
                total_citations=total_citations,
                valid_citations=valid_citations,
                broken_citations=broken_citations,
                archived_alternatives=archived_alternatives,
                citation_score=round(citation_score, 2),
                needs_review=needs_review,
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            self.logger.error(f"Citation validation failed for {atom_id}: {e}", exc_info=True)
            return CitationValidationResult(
                atom_id=atom_id,
                total_citations=0,
                valid_citations=0,
                broken_citations=[],
                archived_alternatives=[],
                citation_score=0.0,
                needs_review=True,
                timestamp=datetime.now().isoformat()
            )

    def validate_all_citations(self) -> CitationHealthReport:
        """
        Validate citations for all atoms.

        Returns:
            CitationHealthReport with overall statistics
        """
        self.logger.info("Validating all citations...")

        # Fetch all atoms
        result = self.supabase.table("knowledge_atoms").select("atom_id").execute()
        atom_ids = [atom["atom_id"] for atom in result.data]

        return self._validate_batch(atom_ids)

    def _validate_batch(self, atom_ids: List[str]) -> CitationHealthReport:
        """Validate batch of atoms and generate report"""
        total_atoms = len(atom_ids)
        atoms_with_valid = 0
        atoms_with_broken = 0
        total_urls = 0
        valid_urls = 0
        broken_urls = 0
        archived_urls = 0
        total_citation_score = 0.0

        for atom_id in atom_ids:
            result = self.validate_citations(atom_id)

            total_urls += result.total_citations
            valid_urls += result.valid_citations
            broken_urls += len(result.broken_citations)
            archived_urls += len(result.archived_alternatives)
            total_citation_score += result.citation_score

            if result.citation_score >= MIN_CITATION_SCORE:
                atoms_with_valid += 1
            else:
                atoms_with_broken += 1

        avg_citation_score = total_citation_score / total_atoms if total_atoms > 0 else 0.0

        report = CitationHealthReport(
            total_atoms=total_atoms,
            atoms_with_valid_citations=atoms_with_valid,
            atoms_with_broken_citations=atoms_with_broken,
            total_urls_checked=total_urls,
            valid_urls=valid_urls,
            broken_urls=broken_urls,
            archived_urls=archived_urls,
            average_citation_score=round(avg_citation_score, 2),
            timestamp=datetime.now().isoformat()
        )

        self._log_report(report)
        return report

    def _log_report(self, report: CitationHealthReport):
        """Log citation health report"""
        self.logger.info("")
        self.logger.info("=" * 80)
        self.logger.info("CITATION HEALTH REPORT")
        self.logger.info("=" * 80)
        self.logger.info(f"Total Atoms: {report.total_atoms}")
        self.logger.info(f"Atoms with Valid Citations: {report.atoms_with_valid_citations} ({report.atoms_with_valid_citations/report.total_atoms*100:.1f}%)")
        self.logger.info(f"Atoms with Broken Citations: {report.atoms_with_broken_citations} ({report.atoms_with_broken_citations/report.total_atoms*100:.1f}%)")
        self.logger.info("")
        self.logger.info(f"Total URLs Checked: {report.total_urls_checked}")
        self.logger.info(f"Valid URLs: {report.valid_urls} ({report.valid_urls/report.total_urls_checked*100:.1f}%)")
        self.logger.info(f"Broken URLs: {report.broken_urls} ({report.broken_urls/report.total_urls_checked*100:.1f}%)")
        self.logger.info(f"Archived URLs (Wayback): {report.archived_urls}")
        self.logger.info("")
        self.logger.info(f"Average Citation Score: {report.average_citation_score}")
        self.logger.info("=" * 80)
        self.logger.info("")

    # ========================================================================
    # AUTO-UPDATE CITATIONS
    # ========================================================================

    def auto_update_broken_citations(self, atom_id: str, dry_run: bool = True):
        """
        Auto-update broken citations with Wayback alternatives.

        Args:
            atom_id: Atom ID to update
            dry_run: If True, only log what would be updated (default: True)
        """
        result = self.validate_citations(atom_id)

        if not result.archived_alternatives:
            self.logger.info(f"No Wayback alternatives found for {atom_id}")
            return

        # Update source_url if broken
        for alt in result.archived_alternatives:
            if alt["type"] == "source_url":
                old_url = alt["url"]
                new_url = alt["wayback_url"]

                if dry_run:
                    self.logger.info(f"[DRY RUN] Would update {atom_id}:")
                    self.logger.info(f"  Old: {old_url}")
                    self.logger.info(f"  New: {new_url}")
                else:
                    self.logger.info(f"Updating {atom_id} citation:")
                    self.logger.info(f"  Old: {old_url}")
                    self.logger.info(f"  New: {new_url}")

                    # Update in Supabase
                    self.supabase.table("knowledge_atoms").update({
                        "source_url": new_url,
                        "citation_updated_at": datetime.now().isoformat()
                    }).eq("atom_id", atom_id).execute()


# ============================================================================
# MAIN (for testing)
# ============================================================================

def main():
    """Test citation validator agent"""
    import argparse

    parser = argparse.ArgumentParser(description="Citation Validator Agent")
    parser.add_argument("--atom-id", help="Validate citations for single atom")
    parser.add_argument("--all", action="store_true", help="Validate all citations")
    parser.add_argument("--check-url", help="Check health of single URL")
    parser.add_argument("--wayback", help="Find Wayback alternative for URL")

    args = parser.parse_args()

    validator = CitationValidatorAgent()

    if args.check_url:
        health = validator.check_url_health(args.check_url)
        print(f"\nURL Health Check:")
        print(f"  URL: {health.url}")
        print(f"  Status: {health.status}")
        print(f"  Status Code: {health.status_code}")
        print(f"  Response Time: {health.response_time_ms}ms")
        if health.redirect_url:
            print(f"  Redirects To: {health.redirect_url}")
        if health.error_message:
            print(f"  Error: {health.error_message}")

    elif args.wayback:
        archive_url = validator.find_wayback_alternative(args.wayback)
        if archive_url:
            print(f"\nWayback Archive Found:")
            print(f"  {archive_url}")
        else:
            print(f"\nNo Wayback archive found for: {args.wayback}")

    elif args.atom_id:
        result = validator.validate_citations(args.atom_id)
        print(f"\nCitation Validation for {result.atom_id}:")
        print(f"  Total Citations: {result.total_citations}")
        print(f"  Valid Citations: {result.valid_citations}")
        print(f"  Citation Score: {result.citation_score}")
        print(f"  Needs Review: {result.needs_review}")

        if result.broken_citations:
            print(f"\n  Broken Citations:")
            for broken in result.broken_citations:
                print(f"    - {broken['url']} ({broken['status']})")

        if result.archived_alternatives:
            print(f"\n  Wayback Alternatives Found:")
            for alt in result.archived_alternatives:
                print(f"    - {alt['url']}")
                print(f"      Archive: {alt['wayback_url']}")

    elif args.all:
        report = validator.validate_all_citations()

    else:
        print("Usage: python citation_validator_agent.py [--atom-id ID | --all | --check-url URL | --wayback URL]")


if __name__ == "__main__":
    main()
