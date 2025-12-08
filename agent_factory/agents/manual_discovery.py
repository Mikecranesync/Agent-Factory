"""
Rivet Manual Discovery Agent - Agent 1 (Stream 1)

24/7 autonomous scraper for industrial equipment manuals.
Controlled via mobile through GitHub Actions.

ARCHITECTURE:
- Runs every 8 hours via GitHub Actions
- 2 manufacturers per run (cost optimization)
- Mobile control via issue comments: /discover ABB Siemens
- Outputs mobile-friendly summary JSON
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from enum import Enum

from agent_factory.models.manual import (
    EquipmentManual,
    ManualMetadata,
    ManualType
)


class DiscoveryMode(str, Enum):
    """Discovery execution modes."""
    AUTOMATED = "automated"  # Scheduled run with defaults
    TEST = "test"  # Test mode - no database writes
    FULL_SCAN = "full_scan"  # Comprehensive scan (slow)


class ManufacturerConfig:
    """Configuration for manufacturer scraping."""

    MANUFACTURERS = {
        "ABB": {
            "name": "ABB",
            "equipment_types": ["motor drives", "VFDs", "switchgear"],
            "base_url": "https://library.abb.com",
            "priority": 1,  # 1 = highest priority
            "enabled": True
        },
        "Siemens": {
            "name": "Siemens",
            "equipment_types": ["PLCs", "automation", "building systems"],
            "base_url": "https://support.industry.siemens.com",
            "priority": 1,
            "enabled": True
        },
        "Rockwell": {
            "name": "Rockwell Automation",
            "equipment_types": ["ControlLogix", "CompactLogix PLCs"],
            "base_url": "https://literature.rockwellautomation.com",
            "priority": 2,
            "enabled": True
        },
        "Carrier": {
            "name": "Carrier",
            "equipment_types": ["commercial HVAC", "chillers"],
            "base_url": "https://www.carrier.com/commercial/en/us/products/",
            "priority": 2,
            "enabled": True
        },
        "Schneider": {
            "name": "Schneider Electric",
            "equipment_types": ["contactors", "breakers", "automation"],
            "base_url": "https://www.se.com",
            "priority": 2,
            "enabled": True
        }
    }

    @classmethod
    def get_config(cls, manufacturer: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a manufacturer."""
        return cls.MANUFACTURERS.get(manufacturer.upper())

    @classmethod
    def list_manufacturers(cls) -> List[str]:
        """List all configured manufacturers."""
        return list(cls.MANUFACTURERS.keys())

    @classmethod
    def get_enabled_manufacturers(cls) -> List[str]:
        """Get list of enabled manufacturers."""
        return [
            name for name, config in cls.MANUFACTURERS.items()
            if config.get("enabled", True)
        ]


class DiscoveryResult:
    """Results from a discovery run."""

    def __init__(self):
        self.status = "RUNNING"
        self.manufacturers_processed: List[str] = []
        self.manuals_found = 0
        self.manuals_high_quality = 0
        self.manuals_needs_review = 0
        self.errors: List[str] = []
        self.top_products: List[str] = []
        self.duration = "0s"
        self.next_run = "Unknown"
        self.started_at = datetime.utcnow()
        self.completed_at: Optional[datetime] = None

    def mark_complete(self):
        """Mark discovery as complete."""
        self.completed_at = datetime.utcnow()
        duration_seconds = (self.completed_at - self.started_at).total_seconds()

        if duration_seconds < 60:
            self.duration = f"{int(duration_seconds)}s"
        else:
            self.duration = f"{int(duration_seconds / 60)}m {int(duration_seconds % 60)}s"

        # Calculate next run (8 hours from now)
        next_run_dt = datetime.utcnow() + timedelta(hours=8)
        self.next_run = next_run_dt.strftime("%Y-%m-%d %H:%M UTC")

        # Determine overall status
        if self.errors and self.manuals_found == 0:
            self.status = "FAILED"
        elif self.errors:
            self.status = "PARTIAL"
        else:
            self.status = "SUCCESS"

    def add_error(self, error: str):
        """Add an error to the results."""
        self.errors.append(error)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "status": self.status,
            "manufacturers": self.manufacturers_processed,
            "found": self.manuals_found,
            "high_quality": self.manuals_high_quality,
            "needs_review": self.manuals_needs_review,
            "top_products": self.top_products,
            "errors": self.errors,
            "duration": self.duration,
            "next_run": self.next_run,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class ManualDiscoveryAgent:
    """
    Agent 1: 24/7 Manual Discovery (Stream 1)

    Autonomously scrapes manufacturer sites for equipment manuals.
    Mobile-controlled via GitHub Actions.
    """

    def __init__(
        self,
        mode: DiscoveryMode = DiscoveryMode.AUTOMATED,
        database_url: Optional[str] = None,
        verbose: bool = False
    ):
        self.mode = mode
        self.database_url = database_url
        self.verbose = verbose
        self.results = DiscoveryResult()

        # Quality thresholds
        self.quality_threshold = 0.5  # Minimum quality score to keep
        self.min_page_count = 5  # Minimum pages for a valid manual

        if self.verbose:
            print(f"[ManualDiscoveryAgent] Initialized in {mode} mode")
            print(f"[ManualDiscoveryAgent] Database: {database_url or 'None (test mode)'}")

    def discover(self, manufacturers: List[str]) -> DiscoveryResult:
        """
        Main discovery method.

        Args:
            manufacturers: List of manufacturer names to scrape

        Returns:
            DiscoveryResult with summary statistics
        """
        if self.verbose:
            print(f"\n{'='*70}")
            print(f"RIVET DISCOVERY - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
            print(f"{'='*70}")
            print(f"Manufacturers: {', '.join(manufacturers)}")
            print(f"Mode: {self.mode}")
            print()

        for manufacturer in manufacturers:
            try:
                self._discover_manufacturer(manufacturer)
            except Exception as e:
                error_msg = f"{manufacturer}: {str(e)}"
                self.results.add_error(error_msg)
                if self.verbose:
                    print(f"[ERROR] {error_msg}")

        self.results.mark_complete()

        if self.verbose:
            self._print_summary()

        return self.results

    def _discover_manufacturer(self, manufacturer: str):
        """
        Discover manuals for a single manufacturer.

        Args:
            manufacturer: Manufacturer name (e.g., "ABB", "Siemens")
        """
        config = ManufacturerConfig.get_config(manufacturer)
        if not config:
            raise ValueError(f"Unknown manufacturer: {manufacturer}")

        if not config.get("enabled", True):
            raise ValueError(f"Manufacturer {manufacturer} is disabled")

        self.results.manufacturers_processed.append(manufacturer)

        if self.verbose:
            print(f"[{manufacturer}] Starting discovery...")
            print(f"[{manufacturer}] Equipment types: {', '.join(config['equipment_types'])}")
            print(f"[{manufacturer}] Base URL: {config['base_url']}")

        # TODO: Import and instantiate manufacturer-specific scraper
        # For now, simulate discovery
        if self.mode == DiscoveryMode.TEST:
            # Test mode - simulate finding manuals
            found = self._simulate_discovery(manufacturer, config)
            if self.verbose:
                print(f"[{manufacturer}] TEST MODE - Simulated {found} manuals")
        else:
            # Real mode - would call actual scraper
            # scraper = self._get_scraper(manufacturer)
            # manuals = scraper.scrape()
            # self._save_manuals(manuals)
            if self.verbose:
                print(f"[{manufacturer}] PRODUCTION MODE - Scraper not yet implemented")
            self.results.add_error(f"{manufacturer}: Scraper not implemented yet")

    def _simulate_discovery(self, manufacturer: str, config: Dict[str, Any]) -> int:
        """Simulate finding manuals (for testing)."""
        import random

        # Simulate finding 5-15 manuals
        found_count = random.randint(5, 15)
        high_quality = int(found_count * 0.7)  # 70% high quality
        needs_review = found_count - high_quality

        self.results.manuals_found += found_count
        self.results.manuals_high_quality += high_quality
        self.results.manuals_needs_review += needs_review

        # Add some sample product names
        sample_products = [
            f"{manufacturer} {config['equipment_types'][0]} Model X100",
            f"{manufacturer} {config['equipment_types'][0]} Model X200",
            f"{manufacturer} {config['equipment_types'][0]} Model X300"
        ]
        self.results.top_products.extend(sample_products[:2])

        return found_count

    def _get_scraper(self, manufacturer: str):
        """Get manufacturer-specific scraper instance."""
        # TODO: Implement scraper factory
        # from agent_factory.tools.scrapers import get_scraper
        # return get_scraper(manufacturer)
        raise NotImplementedError(f"Scraper for {manufacturer} not yet implemented")

    def _save_manuals(self, manuals: List[EquipmentManual]):
        """Save discovered manuals to database."""
        if self.mode == DiscoveryMode.TEST:
            if self.verbose:
                print(f"[TEST MODE] Would save {len(manuals)} manuals to database")
            return

        if not self.database_url:
            raise ValueError("Database URL required for production mode")

        # TODO: Implement database storage
        # from agent_factory.storage import ManualStorage
        # storage = ManualStorage(self.database_url)
        # storage.bulk_insert(manuals)
        raise NotImplementedError("Database storage not yet implemented")

    def _print_summary(self):
        """Print mobile-friendly summary (ASCII-only for Windows compatibility)."""
        status_prefix = {
            "SUCCESS": "[OK]",
            "PARTIAL": "[WARN]",
            "FAILED": "[FAIL]",
            "RUNNING": "[RUN]"
        }.get(self.results.status, "[???]")

        print(f"\n{status_prefix} DISCOVERY COMPLETE ({self.results.duration})")
        print(f"\nRESULTS:")
        print(f"  - Found: {self.results.manuals_found} manuals")
        print(f"  - High Quality: {self.results.manuals_high_quality}")
        print(f"  - Needs Review: {self.results.manuals_needs_review}")

        if self.results.top_products:
            print(f"\nTOP PRODUCTS:")
            for product in self.results.top_products[:3]:
                print(f"  - {product}")

        if self.results.errors:
            print(f"\nERRORS:")
            for error in self.results.errors[:2]:
                print(f"  - {error}")

        print(f"\nNEXT RUN: {self.results.next_run}")
        print()


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Rivet Manual Discovery Agent - 24/7 equipment manual scraper"
    )

    parser.add_argument(
        "--manufacturers",
        type=str,
        default="ABB,Siemens",
        help="Comma-separated list of manufacturers or 'all' (default: ABB,Siemens)"
    )

    parser.add_argument(
        "--mode",
        type=str,
        choices=["automated", "test", "full_scan"],
        default="automated",
        help="Discovery mode (default: automated)"
    )

    parser.add_argument(
        "--output",
        type=str,
        help="Output file for JSON summary (default: summary.json)"
    )

    parser.add_argument(
        "--mobile-optimized",
        action="store_true",
        help="Generate mobile-optimized output"
    )

    parser.add_argument(
        "--database-url",
        type=str,
        help="Database connection URL (reads from DATABASE_URL env var if not provided)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    parser.add_argument(
        "--list-manufacturers",
        action="store_true",
        help="List all configured manufacturers and exit"
    )

    return parser.parse_args()


def main():
    """Main entry point for CLI."""
    args = parse_args()

    # List manufacturers and exit
    if args.list_manufacturers:
        print("Configured Manufacturers:")
        for name in ManufacturerConfig.list_manufacturers():
            config = ManufacturerConfig.get_config(name)
            status = "✓" if config.get("enabled") else "✗"
            print(f"  {status} {name}: {', '.join(config['equipment_types'])}")
        return 0

    # Parse manufacturers
    if args.manufacturers.lower() == "all":
        manufacturers = ManufacturerConfig.get_enabled_manufacturers()
    else:
        manufacturers = [m.strip() for m in args.manufacturers.split(",")]

    # Validate manufacturers
    invalid = [m for m in manufacturers if not ManufacturerConfig.get_config(m)]
    if invalid:
        print(f"ERROR: Unknown manufacturers: {', '.join(invalid)}")
        print(f"Use --list-manufacturers to see available options")
        return 1

    # Get database URL
    import os
    database_url = args.database_url or os.getenv("DATABASE_URL")

    # Create agent
    agent = ManualDiscoveryAgent(
        mode=DiscoveryMode(args.mode),
        database_url=database_url,
        verbose=args.verbose or args.mobile_optimized
    )

    # Run discovery
    try:
        results = agent.discover(manufacturers)
    except Exception as e:
        print(f"FATAL ERROR: {str(e)}")
        return 1

    # Save results to file
    output_file = args.output or "summary.json"
    try:
        with open(output_file, "w") as f:
            json.dump(results.to_dict(), f, indent=2)

        if args.verbose:
            print(f"\n[SUCCESS] Results saved to {output_file}")
    except Exception as e:
        print(f"WARNING: Failed to save results: {str(e)}")

    # Exit code based on status
    exit_codes = {
        "SUCCESS": 0,
        "PARTIAL": 0,  # Partial success still counts as success
        "FAILED": 1,
        "RUNNING": 2  # Shouldn't happen
    }
    return exit_codes.get(results.status, 1)


if __name__ == "__main__":
    sys.exit(main())
