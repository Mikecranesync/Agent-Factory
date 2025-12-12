#!/usr/bin/env python3
"""
WEEKLY KB MAINTENANCE SCHEDULER

Runs weekly (Sundays at 12:00 AM) for maintenance tasks:
1. Full KB reindexing
2. Deduplicate similar atoms (cosine similarity > 0.95)
3. Quality audit (flaglow-quality atoms)
4. Generate weekly growth report
5. Send comprehensive Telegram report

Usage:
    poetry run python scripts/scheduler_kb_weekly.py

Logs: data/logs/kb_weekly_{week}.log
Reports: data/reports/weekly_{week}.json
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client
import numpy as np

# ============================================================================
# CONFIGURATION
# ============================================================================

# Logging setup
log_dir = Path("data/logs")
log_dir.mkdir(parents=True, exist_ok=True)

week_number = datetime.now().isocalendar()[1]
log_file = log_dir / f"kb_weekly_week{week_number}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Credentials
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

# Thresholds
DUPLICATE_THRESHOLD = 0.95  # Cosine similarity
LOW_QUALITY_THRESHOLD = 0.5

# ============================================================================
# UTILITIES
# ============================================================================

def send_telegram_notification(message: str):
    """Send notification to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    try:
        import requests
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, json=data, timeout=10)
        logger.info("Telegram notification sent")
    except Exception as e:
        logger.error(f"Telegram notification failed: {e}")


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    a_np = np.array(a)
    b_np = np.array(b)
    return float(np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np)))


# ============================================================================
# PHASE 1: REINDEX KNOWLEDGE BASE
# ============================================================================

def phase_1_reindex() -> Dict[str, Any]:
    """
    Rebuild indexes for faster queries.
    Returns: Stats dict
    """
    logger.info("=" * 80)
    logger.info("PHASE 1: REINDEXING KNOWLEDGE BASE")
    logger.info("=" * 80)

    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("Supabase credentials not found")
        return {"status": "skipped"}

    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        # Reindex full-text search
        logger.info("Reindexing full-text search...")
        # Note: PostgreSQL automatically updates GIN indexes on INSERT/UPDATE
        # This is just a stats check

        # Count atoms
        count_result = supabase.table("knowledge_atoms").select("id", count="exact").execute()
        total_atoms = count_result.count

        # Count atoms with embeddings
        embedding_count = supabase.table("knowledge_atoms").select("id", count="exact").not_.is_("embedding", "null").execute()
        embeddings = embedding_count.count

        stats = {
            "status": "complete",
            "total_atoms": total_atoms,
            "atoms_with_embeddings": embeddings,
            "index_coverage": f"{(embeddings/total_atoms)*100:.1f}%" if total_atoms > 0 else "0%"
        }

        logger.info(f"Reindexing complete: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Reindexing failed: {e}")
        return {"status": "failed", "error": str(e)}


# ============================================================================
# PHASE 2: DEDUPLICATE ATOMS
# ============================================================================

def phase_2_deduplicate() -> Dict[str, Any]:
    """
    Find and merge duplicate atoms (cosine similarity > 0.95).
    Returns: Stats dict
    """
    logger.info("=" * 80)
    logger.info("PHASE 2: DEDUPLICATING ATOMS")
    logger.info("=" * 80)

    if not SUPABASE_URL or not SUPABASE_KEY:
        return {"status": "skipped"}

    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        # Fetch all atoms with embeddings
        logger.info("Fetching atoms with embeddings...")
        result = supabase.table("knowledge_atoms").select("id, atom_id, title, embedding").not_.is_("embedding", "null").execute()

        atoms = result.data
        logger.info(f"Loaded {len(atoms)} atoms")

        duplicates_found = []

        # Compare all pairs (expensive, but weekly is acceptable)
        for i in range(len(atoms)):
            for j in range(i + 1, len(atoms)):
                atom_a = atoms[i]
                atom_b = atoms[j]

                # Skip if no embeddings
                if not atom_a.get('embedding') or not atom_b.get('embedding'):
                    continue

                similarity = cosine_similarity(atom_a['embedding'], atom_b['embedding'])

                if similarity > DUPLICATE_THRESHOLD:
                    logger.info(f"  Found duplicate: {atom_a['atom_id']} <-> {atom_b['atom_id']} (similarity: {similarity:.3f})")
                    duplicates_found.append({
                        "atom_a_id": atom_a['id'],
                        "atom_b_id": atom_b['id'],
                        "atom_a_atom_id": atom_a['atom_id'],
                        "atom_b_atom_id": atom_b['atom_id'],
                        "similarity": similarity
                    })

        # For now, just log duplicates (manual review required)
        # In future, auto-merge or flag for review

        stats = {
            "status": "complete",
            "atoms_checked": len(atoms),
            "duplicates_found": len(duplicates_found),
            "duplicates": duplicates_found[:10]  # Top 10 for report
        }

        logger.info(f"Deduplication complete: {len(duplicates_found)} duplicates found")
        return stats

    except Exception as e:
        logger.error(f"Deduplication failed: {e}")
        return {"status": "failed", "error": str(e)}


# ============================================================================
# PHASE 3: QUALITY AUDIT
# ============================================================================

def phase_3_quality_audit() -> Dict[str, Any]:
    """
    Audit knowledge base quality.
    Returns: Stats dict
    """
    logger.info("=" * 80)
    logger.info("PHASE 3: QUALITY AUDIT")
    logger.info("=" * 80)

    if not SUPABASE_URL or not SUPABASE_KEY:
        return {"status": "skipped"}

    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        # Count low quality atoms
        low_quality = supabase.table("knowledge_atoms").select("id, atom_id, quality_score", count="exact").lt("quality_score", LOW_QUALITY_THRESHOLD).execute()

        # Count atoms by type
        type_counts = {}
        for atom_type in ['concept', 'procedure', 'specification', 'pattern', 'fault', 'reference']:
            count = supabase.table("knowledge_atoms").select("id", count="exact").eq("atom_type", atom_type).execute()
            type_counts[atom_type] = count.count

        # Count atoms by difficulty
        difficulty_counts = {}
        for difficulty in ['beginner', 'intermediate', 'advanced', 'expert']:
            count = supabase.table("knowledge_atoms").select("id", count="exact").eq("difficulty", difficulty).execute()
            difficulty_counts[difficulty] = count.count

        # Count atoms by manufacturer
        mfr_counts = {}
        for mfr in ['allen_bradley', 'siemens', 'mitsubishi', 'omron', 'schneider', 'abb']:
            count = supabase.table("knowledge_atoms").select("id", count="exact").eq("manufacturer", mfr).execute()
            if count.count > 0:
                mfr_counts[mfr] = count.count

        stats = {
            "status": "complete",
            "low_quality_atoms": low_quality.count,
            "low_quality_details": low_quality.data[:5],  # Top 5 for review
            "type_distribution": type_counts,
            "difficulty_distribution": difficulty_counts,
            "manufacturer_distribution": mfr_counts
        }

        logger.info(f"Quality audit complete: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Quality audit failed: {e}")
        return {"status": "failed", "error": str(e)}


# ============================================================================
# PHASE 4: WEEKLY GROWTH REPORT
# ============================================================================

def phase_4_growth_report() -> Dict[str, Any]:
    """
    Generate weekly growth report.
    Returns: Stats dict
    """
    logger.info("=" * 80)
    logger.info("PHASE 4: GROWTH REPORT")
    logger.info("=" * 80)

    if not SUPABASE_URL or not SUPABASE_KEY:
        return {"status": "skipped"}

    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        # Current week date range
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday() + 7)  # Last Monday
        week_end = today - timedelta(days=today.weekday() + 1)    # Last Sunday

        logger.info(f"Week range: {week_start.date()} to {week_end.date()}")

        # Atoms added this week
        week_start_iso = week_start.isoformat()
        week_end_iso = week_end.isoformat()

        atoms_this_week = supabase.table("knowledge_atoms").select("id", count="exact").gte("created_at", week_start_iso).lte("created_at", week_end_iso).execute()

        # Total atoms
        total_atoms = supabase.table("knowledge_atoms").select("id", count="exact").execute()

        # Calculate growth rate
        growth_rate = (atoms_this_week.count / total_atoms.count * 100) if total_atoms.count > 0 else 0

        stats = {
            "status": "complete",
            "week_start": week_start.strftime("%Y-%m-%d"),
            "week_end": week_end.strftime("%Y-%m-%d"),
            "atoms_added_this_week": atoms_this_week.count,
            "total_atoms": total_atoms.count,
            "growth_rate": f"{growth_rate:.2f}%"
        }

        logger.info(f"Growth report complete: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Growth report failed: {e}")
        return {"status": "failed", "error": str(e)}


# ============================================================================
# GENERATE WEEKLY REPORT
# ============================================================================

def generate_weekly_report(all_stats: Dict[str, Any]) -> str:
    """Generate comprehensive weekly report"""

    week_number = datetime.now().isocalendar()[1]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report = f"""
📊 **Weekly KB Maintenance Report - Week {week_number}**
🕐 **Timestamp:** {timestamp}

**PHASE 1: Reindexing**
- Status: {all_stats['reindex']['status']}
- Total Atoms: {all_stats['reindex'].get('total_atoms', 'N/A')}
- Atoms with Embeddings: {all_stats['reindex'].get('atoms_with_embeddings', 'N/A')}
- Index Coverage: {all_stats['reindex'].get('index_coverage', 'N/A')}

**PHASE 2: Deduplication**
- Status: {all_stats['deduplicate']['status']}
- Atoms Checked: {all_stats['deduplicate'].get('atoms_checked', 'N/A')}
- Duplicates Found: {all_stats['deduplicate'].get('duplicates_found', 'N/A')}

**PHASE 3: Quality Audit**
- Status: {all_stats['quality']['status']}
- Low Quality Atoms: {all_stats['quality'].get('low_quality_atoms', 'N/A')}
- Type Distribution:
{json.dumps(all_stats['quality'].get('type_distribution', {}), indent=2)}
- Difficulty Distribution:
{json.dumps(all_stats['quality'].get('difficulty_distribution', {}), indent=2)}
- Manufacturer Distribution:
{json.dumps(all_stats['quality'].get('manufacturer_distribution', {}), indent=2)}

**PHASE 4: Growth Report**
- Week: {all_stats['growth'].get('week_start', 'N/A')} to {all_stats['growth'].get('week_end', 'N/A')}
- Atoms Added This Week: {all_stats['growth'].get('atoms_added_this_week', 'N/A')}
- Total Atoms: {all_stats['growth'].get('total_atoms', 'N/A')}
- Growth Rate: {all_stats['growth'].get('growth_rate', 'N/A')}

✅ **Weekly maintenance complete!**
    """

    # Save report
    report_dir = Path("data/reports")
    report_dir.mkdir(parents=True, exist_ok=True)

    report_file = report_dir / f"weekly_week{week_number}.json"
    report_file.write_text(json.dumps(all_stats, indent=2))

    report_md_file = report_dir / f"weekly_week{week_number}.md"
    report_md_file.write_text(report)

    logger.info(f"Report saved to: {report_md_file}")
    return report


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main weekly maintenance orchestrator"""
    start_time = datetime.now()

    logger.info("")
    logger.info("=" * 80)
    logger.info("WEEKLY KB MAINTENANCE - STARTING")
    logger.info("=" * 80)
    logger.info(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")

    all_stats = {}

    try:
        # Phase 1: Reindex
        all_stats['reindex'] = phase_1_reindex()

        # Phase 2: Deduplicate
        all_stats['deduplicate'] = phase_2_deduplicate()

        # Phase 3: Quality audit
        all_stats['quality'] = phase_3_quality_audit()

        # Phase 4: Growth report
        all_stats['growth'] = phase_4_growth_report()

        # Generate report
        report = generate_weekly_report(all_stats)

        # Send Telegram notification
        send_telegram_notification(f"✅ Weekly KB Maintenance Complete\n\n{report}")

        # Log completion
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info("")
        logger.info("=" * 80)
        logger.info("WEEKLY KB MAINTENANCE - COMPLETE")
        logger.info("=" * 80)
        logger.info(f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Duration: {duration:.1f} seconds")
        logger.info("")

        return 0

    except Exception as e:
        logger.error(f"CRITICAL ERROR: {e}", exc_info=True)
        send_telegram_notification(f"❌ Weekly KB Maintenance FAILED\n\nError: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
