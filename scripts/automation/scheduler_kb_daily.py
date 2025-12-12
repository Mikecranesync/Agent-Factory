#!/usr/bin/env python3
"""
DAILY KB BUILDING SCHEDULER - 24/7 Automation

Runs daily at 2:00 AM to build and maintain knowledge base:
1. Scrape new PDFs from OEM sources
2. Build knowledge atoms from PDFs
3. Upload atoms to Supabase
4. Validate embeddings and quality
5. Generate daily stats report
6. Send Telegram notification

Usage:
    poetry run python scripts/scheduler_kb_daily.py

Logs: data/logs/kb_daily_{date}.log
Notifications: Telegram bot (success/failure)
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.research.oem_pdf_scraper_agent import OEMPDFScraperAgent
from agents.knowledge.atom_builder_from_pdf import AtomBuilderFromPDF
from agents.knowledge.quality_checker_agent import QualityCheckerAgent
from agents.knowledge.citation_validator_agent import CitationValidatorAgent
from supabase import create_client

# ============================================================================
# CONFIGURATION
# ============================================================================

# Logging setup
log_dir = Path("data/logs")
log_dir.mkdir(parents=True, exist_ok=True)

log_file = log_dir / f"kb_daily_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Telegram bot credentials
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID")

# Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

# PDF sources (can expand this list)
PDF_SOURCES = {
    "allen_bradley": [
        "https://literature.rockwellautomation.com/idc/groups/literature/documents/um/1756-um001_-en-p.pdf",
        "https://literature.rockwellautomation.com/idc/groups/literature/documents/pm/1756-pm001_-en-e.pdf",
    ],
    "siemens": [
        "https://support.industry.siemens.com/cs/attachments/109814829/s71200_system_manual_en-US_en-US.pdf",
    ],
}

# ============================================================================
# TELEGRAM NOTIFICATIONS
# ============================================================================

def send_telegram_notification(message: str, parse_mode: str = "Markdown"):
    """Send notification to Telegram bot"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram credentials not configured, skipping notification")
        return

    try:
        import requests
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": parse_mode
        }
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            logger.info("Telegram notification sent")
        else:
            logger.error(f"Telegram notification failed: {response.text}")
    except Exception as e:
        logger.error(f"Failed to send Telegram notification: {e}")


# ============================================================================
# PHASE 1: SCRAPE NEW PDFs
# ============================================================================

def phase_1_scrape_pdfs() -> Dict[str, Any]:
    """
    Scrape new PDFs from OEM sources.
    Returns: Stats dict
    """
    logger.info("=" * 80)
    logger.info("PHASE 1: SCRAPING PDFs")
    logger.info("=" * 80)

    scraper = OEMPDFScraperAgent()

    total_pdfs = 0
    total_pages = 0
    total_tables = 0

    for manufacturer, urls in PDF_SOURCES.items():
        logger.info(f"\n[{manufacturer.upper()}] Processing {len(urls)} PDFs...")

        for url in urls:
            try:
                logger.info(f"\nProcessing: {url}")

                # Download PDF
                pdf_path = scraper.download_pdf(url, manufacturer)
                if not pdf_path:
                    logger.error(f"  Failed to download: {url}")
                    continue

                # Extract content
                result = scraper.extract_pdf_content(pdf_path, manufacturer)

                # Log stats
                logger.info(f"  Pages: {result['metadata']['pages']}")
                logger.info(f"  Tables: {len(result['tables'])}")
                logger.info(f"  Images: {len(result['images'])}")

                total_pdfs += 1
                total_pages += result['metadata']['pages']
                total_tables += len(result['tables'])

            except Exception as e:
                logger.error(f"  Error processing {url}: {e}")

    stats = {
        "pdfs_scraped": total_pdfs,
        "pages_extracted": total_pages,
        "tables_extracted": total_tables,
    }

    logger.info(f"\nPHASE 1 COMPLETE: {stats}")
    return stats


# ============================================================================
# PHASE 2: BUILD KNOWLEDGE ATOMS
# ============================================================================

def phase_2_build_atoms() -> Dict[str, Any]:
    """
    Build knowledge atoms from extracted PDFs.
    Returns: Stats dict
    """
    logger.info("=" * 80)
    logger.info("PHASE 2: BUILDING KNOWLEDGE ATOMS")
    logger.info("=" * 80)

    builder = AtomBuilderFromPDF()

    extracted_dir = Path("data/extracted")
    extraction_files = list(extracted_dir.glob("*.json"))

    # Skip sample files
    extraction_files = [f for f in extraction_files if "sample" not in f.name]

    logger.info(f"Found {len(extraction_files)} extraction files")

    all_atoms = []

    for idx, json_file in enumerate(extraction_files, 1):
        try:
            logger.info(f"\n[{idx}/{len(extraction_files)}] Processing: {json_file.name}")

            atoms = builder.process_pdf_extraction(
                json_file,
                output_dir=Path("data/atoms") / json_file.stem
            )

            all_atoms.extend(atoms)
            logger.info(f"  Generated {len(atoms)} atoms")

        except Exception as e:
            logger.error(f"  Error: {e}")

    stats = builder.get_stats()
    stats["total_atoms"] = len(all_atoms)

    logger.info(f"\nPHASE 2 COMPLETE: {stats}")
    return stats, all_atoms


# ============================================================================
# PHASE 3: UPLOAD TO SUPABASE
# ============================================================================

def phase_3_upload_atoms(atoms: List[Any]) -> Dict[str, Any]:
    """
    Upload atoms to Supabase.
    Returns: Stats dict
    """
    logger.info("=" * 80)
    logger.info("PHASE 3: UPLOADING TO SUPABASE")
    logger.info("=" * 80)

    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("Supabase credentials not found in .env")
        return {"uploaded": 0, "failed": len(atoms), "skipped": 0}

    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info(f"Connected to Supabase: {SUPABASE_URL}")
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {e}")
        return {"uploaded": 0, "failed": len(atoms), "skipped": 0}

    uploaded = 0
    failed = 0
    skipped = 0

    for idx, atom in enumerate(atoms, 1):
        try:
            # Check if atom already exists
            existing = supabase.table("knowledge_atoms").select("id").eq("atom_id", atom.atom_id).execute()

            if existing.data:
                skipped += 1
                if skipped % 100 == 0:
                    logger.info(f"  Skipped {skipped}/{len(atoms)} (already exist)...")
                continue

            # Upload new atom
            atom_dict = atom.to_dict()
            supabase.table("knowledge_atoms").insert(atom_dict).execute()

            uploaded += 1

            if uploaded % 100 == 0:
                logger.info(f"  Uploaded {uploaded}/{len(atoms)}...")

        except Exception as e:
            logger.error(f"  Failed to upload {atom.atom_id}: {e}")
            failed += 1

    stats = {
        "uploaded": uploaded,
        "failed": failed,
        "skipped": skipped,
        "total": len(atoms)
    }

    logger.info(f"\nPHASE 3 COMPLETE: {stats}")
    return stats


# ============================================================================
# PHASE 4: VALIDATE & QUALITY CHECK
# ============================================================================

def phase_4_validate() -> Dict[str, Any]:
    """
    Validate uploaded atoms and check quality.
    Returns: Stats dict
    """
    logger.info("=" * 80)
    logger.info("PHASE 4: VALIDATION & QUALITY CHECK")
    logger.info("=" * 80)

    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("Supabase credentials not found")
        return {"total_atoms": 0, "valid_embeddings": 0, "quality_issues": 0}

    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        # Count total atoms
        count_result = supabase.table("knowledge_atoms").select("id", count="exact").execute()
        total_atoms = count_result.count

        # Count atoms with embeddings
        embedding_result = supabase.table("knowledge_atoms").select("id", count="exact").not_.is_("embedding", "null").execute()
        valid_embeddings = embedding_result.count

        # Count low quality atoms (quality_score < 0.5)
        quality_result = supabase.table("knowledge_atoms").select("id", count="exact").lt("quality_score", 0.5).execute()
        quality_issues = quality_result.count

        stats = {
            "total_atoms": total_atoms,
            "valid_embeddings": valid_embeddings,
            "quality_issues": quality_issues,
            "embedding_rate": f"{(valid_embeddings/total_atoms)*100:.1f}%" if total_atoms > 0 else "0%"
        }

        logger.info(f"Total atoms: {total_atoms}")
        logger.info(f"Valid embeddings: {valid_embeddings} ({stats['embedding_rate']})")
        logger.info(f"Quality issues: {quality_issues}")

        logger.info(f"\nPHASE 4 COMPLETE: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return {"total_atoms": 0, "valid_embeddings": 0, "quality_issues": 0}


# ============================================================================
# PHASE 6: QUALITY CHECK (NEW AGENTS)
# ============================================================================

def phase_6_quality_check(uploaded_count: int) -> Dict[str, Any]:
    """
    Run Quality Checker and Citation Validator on recently uploaded atoms.
    Returns: Stats dict with quality and citation metrics
    """
    logger.info("=" * 80)
    logger.info("PHASE 6: QUALITY CHECK")
    logger.info("=" * 80)

    if uploaded_count == 0:
        logger.info("No atoms uploaded today, skipping quality check")
        return {
            "quality_checked": 0,
            "quality_passed": 0,
            "quality_warnings": 0,
            "quality_failed": 0,
            "citations_checked": 0,
            "citations_valid": 0,
            "citations_broken": 0
        }

    try:
        # Initialize agents
        quality_checker = QualityCheckerAgent()
        citation_validator = CitationValidatorAgent()

        # Validate recent atoms (last 24 hours)
        logger.info("Running quality validation on recent atoms...")
        quality_report = quality_checker.validate_recent_atoms(hours=24)

        logger.info("Running citation validation on recent atoms...")
        citation_report = citation_validator.validate_all_citations()

        stats = {
            "quality_checked": quality_report.total_atoms,
            "quality_passed": quality_report.passed,
            "quality_warnings": quality_report.warnings,
            "quality_failed": quality_report.failed,
            "quality_flagged": quality_report.flagged_for_review,
            "avg_confidence": quality_report.average_confidence,
            "citations_checked": citation_report.total_urls_checked,
            "citations_valid": citation_report.valid_urls,
            "citations_broken": citation_report.broken_urls,
            "citations_archived": citation_report.archived_urls,
            "avg_citation_score": citation_report.average_citation_score
        }

        logger.info(f"\nQuality Check Results:")
        logger.info(f"  Passed: {stats['quality_passed']}/{stats['quality_checked']}")
        logger.info(f"  Warnings: {stats['quality_warnings']}")
        logger.info(f"  Failed: {stats['quality_failed']}")
        logger.info(f"  Flagged for Review: {stats['quality_flagged']}")
        logger.info(f"  Avg Confidence: {stats['avg_confidence']}")

        logger.info(f"\nCitation Check Results:")
        logger.info(f"  Valid URLs: {stats['citations_valid']}/{stats['citations_checked']}")
        logger.info(f"  Broken URLs: {stats['citations_broken']}")
        logger.info(f"  Wayback Archives: {stats['citations_archived']}")
        logger.info(f"  Avg Citation Score: {stats['avg_citation_score']}")

        # Alert if too many quality issues
        if stats['quality_failed'] > stats['quality_checked'] * 0.2:
            logger.warning(f"HIGH FAILURE RATE: {stats['quality_failed']}/{stats['quality_checked']} atoms failed quality check")

        if stats['citations_broken'] > stats['citations_checked'] * 0.3:
            logger.warning(f"HIGH BROKEN CITATION RATE: {stats['citations_broken']}/{stats['citations_checked']} URLs broken")

        logger.info(f"\nPHASE 6 COMPLETE: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Quality check failed: {e}", exc_info=True)
        return {
            "quality_checked": 0,
            "quality_passed": 0,
            "quality_warnings": 0,
            "quality_failed": 0,
            "citations_checked": 0,
            "citations_valid": 0,
            "citations_broken": 0
        }


# ============================================================================
# PHASE 5: GENERATE DAILY REPORT
# ============================================================================

def phase_5_generate_report(all_stats: Dict[str, Any]) -> str:
    """
    Generate daily KB building report.
    Returns: Report string (Markdown)
    """
    logger.info("=" * 80)
    logger.info("PHASE 5: GENERATING DAILY REPORT")
    logger.info("=" * 80)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report = f"""
📊 **Daily KB Building Report**
🕐 **Timestamp:** {timestamp}

**PHASE 1: PDF Scraping**
- PDFs Scraped: {all_stats['scrape']['pdfs_scraped']}
- Pages Extracted: {all_stats['scrape']['pages_extracted']}
- Tables Extracted: {all_stats['scrape']['tables_extracted']}

**PHASE 2: Atom Building**
- Total Atoms Generated: {all_stats['build']['total_atoms']}
- Concepts: {all_stats['build'].get('concepts', 0)}
- Procedures: {all_stats['build'].get('procedures', 0)}
- Specifications: {all_stats['build'].get('specifications', 0)}
- Embeddings Generated: {all_stats['build'].get('embeddings_generated', 0)}

**PHASE 3: Supabase Upload**
- Uploaded: {all_stats['upload']['uploaded']}
- Failed: {all_stats['upload']['failed']}
- Skipped (duplicates): {all_stats['upload']['skipped']}

**PHASE 4: Validation**
- Total Atoms in DB: {all_stats['validate']['total_atoms']}
- Valid Embeddings: {all_stats['validate']['valid_embeddings']}
- Quality Issues: {all_stats['validate']['quality_issues']}

**PHASE 6: Quality Check**
- Quality Checked: {all_stats['quality']['quality_checked']}
- Passed: {all_stats['quality']['quality_passed']}
- Warnings: {all_stats['quality']['quality_warnings']}
- Failed: {all_stats['quality']['quality_failed']}
- Flagged for Review: {all_stats['quality'].get('quality_flagged', 0)}
- Avg Confidence: {all_stats['quality'].get('avg_confidence', 0.0)}
- Citations Valid: {all_stats['quality']['citations_valid']}/{all_stats['quality']['citations_checked']}
- Citations Broken: {all_stats['quality']['citations_broken']}
- Wayback Archives: {all_stats['quality'].get('citations_archived', 0)}

✅ **Daily KB building complete!**
    """

    # Save report to file
    report_dir = Path("data/reports")
    report_dir.mkdir(parents=True, exist_ok=True)

    report_file = report_dir / f"kb_daily_{datetime.now().strftime('%Y%m%d')}.md"
    report_file.write_text(report)

    logger.info(f"Report saved to: {report_file}")
    return report


# ============================================================================
# MAIN ORCHESTRATOR
# ============================================================================

def main():
    """Main daily KB building orchestrator"""
    start_time = datetime.now()

    logger.info("")
    logger.info("=" * 80)
    logger.info("DAILY KB BUILDING SCHEDULER - STARTING")
    logger.info("=" * 80)
    logger.info(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")

    all_stats = {}

    try:
        # Phase 1: Scrape PDFs
        scrape_stats = phase_1_scrape_pdfs()
        all_stats['scrape'] = scrape_stats

        # Phase 2: Build atoms
        build_stats, atoms = phase_2_build_atoms()
        all_stats['build'] = build_stats

        # Phase 3: Upload to Supabase
        upload_stats = phase_3_upload_atoms(atoms)
        all_stats['upload'] = upload_stats

        # Phase 4: Validate
        validate_stats = phase_4_validate()
        all_stats['validate'] = validate_stats

        # Phase 6: Quality check (NEW)
        quality_stats = phase_6_quality_check(upload_stats['uploaded'])
        all_stats['quality'] = quality_stats

        # Phase 5: Generate report
        report = phase_5_generate_report(all_stats)

        # Send success notification
        send_telegram_notification(f"✅ Daily KB Building Complete\n\n{report}")

        # Log completion
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info("")
        logger.info("=" * 80)
        logger.info("DAILY KB BUILDING SCHEDULER - COMPLETE")
        logger.info("=" * 80)
        logger.info(f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Duration: {duration:.1f} seconds")
        logger.info("")

        return 0

    except Exception as e:
        logger.error(f"CRITICAL ERROR: {e}", exc_info=True)

        # Send failure notification
        send_telegram_notification(f"❌ Daily KB Building FAILED\n\nError: {str(e)}")

        return 1


if __name__ == "__main__":
    sys.exit(main())
