#!/usr/bin/env python3
"""
Export Golden Dataset from Neon PostgreSQL

Extracts knowledge atoms from your Neon database and formats them
as a Phoenix-compatible evaluation dataset.

Usage:
    python export_golden_dataset.py
    
    # Or with options:
    python export_golden_dataset.py --limit 100 --output datasets/golden.jsonl

Requires:
    - DATABASE_URL in .env file
    - psycopg2-binary installed
"""

import os
import json
import argparse
from datetime import datetime
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    logger.error("psycopg2 not installed. Run: pip install psycopg2-binary")
    exit(1)

from dotenv import load_dotenv
load_dotenv()


def get_database_url() -> str:
    """Get database URL from environment."""
    url = os.getenv("DATABASE_URL") or os.getenv("NEON_DATABASE_URL")
    if not url:
        raise ValueError(
            "DATABASE_URL not found in environment. "
            "Set it in .env file or export DATABASE_URL=..."
        )
    return url


def connect_to_neon():
    """Establish connection to Neon PostgreSQL."""
    url = get_database_url()
    logger.info("Connecting to Neon PostgreSQL...")
    
    conn = psycopg2.connect(url, cursor_factory=RealDictCursor)
    logger.info("✅ Connected to database")
    return conn


def extract_fault_knowledge(
    conn,
    limit: Optional[int] = None,
    manufacturer_filter: Optional[str] = None
) -> list[dict]:
    """
    Extract fault-related knowledge atoms from database.
    
    This query should be adapted to YOUR actual schema.
    The example assumes a knowledge_atoms table with relevant fields.
    """
    
    # Adjust this query to match YOUR Neon schema
    query = """
    SELECT 
        id,
        atom_id,
        content,
        metadata,
        manufacturer,
        equipment_type,
        fault_code,
        created_at,
        updated_at
    FROM knowledge_atoms
    WHERE 
        fault_code IS NOT NULL
        AND content IS NOT NULL
    """
    
    params = []
    
    if manufacturer_filter:
        query += " AND LOWER(manufacturer) = LOWER(%s)"
        params.append(manufacturer_filter)
    
    query += " ORDER BY created_at DESC"
    
    if limit:
        query += " LIMIT %s"
        params.append(limit)
    
    with conn.cursor() as cur:
        cur.execute(query, params if params else None)
        rows = cur.fetchall()
    
    logger.info(f"Retrieved {len(rows)} knowledge atoms")
    return [dict(row) for row in rows]


def transform_to_golden_format(atom: dict) -> dict:
    """
    Transform a knowledge atom into Phoenix golden dataset format.
    
    Adapt this to YOUR actual data structure.
    """
    
    # Parse metadata if it's stored as JSON string
    metadata = atom.get("metadata", {})
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except:
            metadata = {}
    
    # Extract fields - adapt these to YOUR schema
    content = atom.get("content", "")
    
    # Try to extract structured info from content/metadata
    # This is a template - you'll need to adapt to your actual data
    root_cause = metadata.get("root_cause") or extract_root_cause(content)
    safety_warnings = metadata.get("safety_warnings") or extract_safety_warnings(content)
    repair_steps = metadata.get("repair_steps") or extract_repair_steps(content)
    manual_citations = metadata.get("manual_citations") or extract_citations(content)
    
    return {
        "test_case_id": atom.get("atom_id") or f"atom_{atom.get('id')}",
        "equipment": {
            "manufacturer": atom.get("manufacturer", "Unknown"),
            "model": atom.get("equipment_type", "Unknown"),
            "subsystem": metadata.get("subsystem", "Unknown")
        },
        "input": {
            "fault_code": atom.get("fault_code", "Unknown"),
            "fault_description": metadata.get("fault_description", ""),
            "sensor_data": metadata.get("sensor_data", {}),
            "context": metadata.get("context", "")
        },
        "expected_output": {
            "root_cause": root_cause,
            "diagnosis_confidence": metadata.get("confidence", "Medium"),
            "repair_steps": repair_steps,
            "safety_critical_warnings": safety_warnings,
            "manual_citations": manual_citations,
            "estimated_downtime_hours": metadata.get("estimated_downtime", 0),
            "business_impact": {
                "downtime_cost_per_hour_usd": metadata.get("downtime_cost", 0),
                "safety_critical": "safety" in content.lower() or len(safety_warnings) > 0
            }
        },
        "source": {
            "atom_id": atom.get("atom_id"),
            "created_at": str(atom.get("created_at", "")),
            "updated_at": str(atom.get("updated_at", ""))
        }
    }


def extract_root_cause(content: str) -> str:
    """
    Extract root cause from content.
    Simple heuristic - adapt to your data.
    """
    content_lower = content.lower()
    
    # Look for common root cause indicators
    indicators = ["root cause:", "caused by:", "due to:", "reason:"]
    for indicator in indicators:
        if indicator in content_lower:
            idx = content_lower.index(indicator) + len(indicator)
            # Get the rest of the sentence
            end_idx = content.find(".", idx)
            if end_idx > idx:
                return content[idx:end_idx].strip()
    
    # Fallback: return first sentence
    first_period = content.find(".")
    if first_period > 0:
        return content[:first_period].strip()
    
    return content[:200].strip()


def extract_safety_warnings(content: str) -> list[str]:
    """
    Extract safety warnings from content.
    Simple heuristic - adapt to your data.
    """
    warnings = []
    content_lower = content.lower()
    
    # Common safety keywords
    safety_keywords = [
        "lockout", "tagout", "loto",
        "voltage", "energized", "zero energy",
        "ppe", "gloves", "safety glasses",
        "rotating", "pinch point", "crush",
        "hot surface", "burn",
        "arc flash", "electrical hazard"
    ]
    
    sentences = content.split(".")
    for sentence in sentences:
        sentence_lower = sentence.lower()
        for keyword in safety_keywords:
            if keyword in sentence_lower:
                warnings.append(sentence.strip())
                break
    
    # Deduplicate while preserving order
    seen = set()
    unique_warnings = []
    for w in warnings:
        if w not in seen and len(w) > 10:
            seen.add(w)
            unique_warnings.append(w)
    
    return unique_warnings[:5]  # Max 5 warnings


def extract_repair_steps(content: str) -> list[str]:
    """
    Extract repair steps from content.
    Simple heuristic - adapt to your data.
    """
    steps = []
    
    # Look for numbered steps
    lines = content.split("\n")
    for line in lines:
        line = line.strip()
        # Match patterns like "1.", "1)", "Step 1:", etc.
        if (
            line and 
            len(line) > 5 and
            (line[0].isdigit() or line.lower().startswith("step"))
        ):
            steps.append(line)
    
    if not steps:
        # Fallback: split into sentences and return first 5
        sentences = [s.strip() for s in content.split(".") if len(s.strip()) > 20]
        steps = sentences[:5]
    
    return steps


def extract_citations(content: str) -> list[str]:
    """
    Extract manual citations from content.
    Simple heuristic - adapt to your data.
    """
    citations = []
    content_lower = content.lower()
    
    # Look for common citation patterns
    citation_keywords = ["manual", "section", "chapter", "page", "guide", "documentation"]
    
    sentences = content.split(".")
    for sentence in sentences:
        sentence_lower = sentence.lower()
        for keyword in citation_keywords:
            if keyword in sentence_lower:
                citations.append(sentence.strip())
                break
    
    return citations[:3]  # Max 3 citations


def export_to_jsonl(data: list[dict], output_path: str) -> None:
    """Export data to JSONL file."""
    
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    
    with open(output_path, "w") as f:
        for item in data:
            f.write(json.dumps(item) + "\n")
    
    logger.info(f"✅ Exported {len(data)} cases to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Export golden dataset from Neon PostgreSQL"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of atoms to export"
    )
    parser.add_argument(
        "--manufacturer",
        type=str,
        default=None,
        help="Filter by manufacturer (e.g., 'Siemens')"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="datasets/golden_dataset.jsonl",
        help="Output file path"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be exported without writing file"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("GOLDEN DATASET EXPORT")
    print("=" * 60)
    print(f"  Limit: {args.limit or 'None (all)'}")
    print(f"  Manufacturer: {args.manufacturer or 'All'}")
    print(f"  Output: {args.output}")
    print(f"  Dry run: {args.dry_run}")
    print("=" * 60)
    
    try:
        # Connect to database
        conn = connect_to_neon()
        
        # Extract knowledge atoms
        atoms = extract_fault_knowledge(
            conn,
            limit=args.limit,
            manufacturer_filter=args.manufacturer
        )
        
        if not atoms:
            logger.warning("No knowledge atoms found matching criteria")
            return
        
        # Transform to golden format
        golden_cases = []
        for atom in atoms:
            try:
                case = transform_to_golden_format(atom)
                golden_cases.append(case)
            except Exception as e:
                logger.warning(f"Failed to transform atom {atom.get('id')}: {e}")
        
        logger.info(f"Transformed {len(golden_cases)} cases")
        
        # Preview first case
        if golden_cases:
            print("\n📋 Sample case preview:")
            print(json.dumps(golden_cases[0], indent=2)[:1000])
            print("...")
        
        # Export
        if args.dry_run:
            print(f"\n🔍 DRY RUN: Would export {len(golden_cases)} cases to {args.output}")
        else:
            export_to_jsonl(golden_cases, args.output)
            print(f"\n✅ SUCCESS: Exported {len(golden_cases)} golden cases")
            print(f"   Next step: Run evals with Phoenix")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise


if __name__ == "__main__":
    main()
