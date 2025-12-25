#!/usr/bin/env python3
"""
Test Research Pipeline End-to-End with Real Ingestion

This script tests the complete flow:
1. Route C triggers research pipeline
2. Research pipeline finds forum sources
3. Sources are queued for ingestion
4. Ingestion chain processes sources (7 stages)
5. Atoms are created and searchable in knowledge_atoms table

Success criteria:
- Research pipeline finds 3-10 forum sources
- At least 1 source queued for ingestion
- After 5 minutes, new atoms appear in knowledge_atoms table
- Atoms are searchable (keywords include model number)
- Next Route C query returns Route A/B (KB coverage improved)
"""

import asyncio
import time
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent_factory.rivet_pro.models import RivetIntent, VendorType, EquipmentType, ContextSource, KBCoverage
from agent_factory.rivet_pro.research.research_pipeline import ResearchPipeline
from agent_factory.core.database_manager import DatabaseManager


async def test_research_pipeline():
    """Test research pipeline with real Siemens G120C query."""

    print("=" * 80)
    print("RESEARCH PIPELINE END-TO-END TEST")
    print("=" * 80)
    print()

    # Step 1: Create realistic intent (Siemens G120C fault)
    print("[Step 1] Creating test intent...")
    intent = RivetIntent(
        vendor=VendorType.SIEMENS,
        equipment_type=EquipmentType.VFD,
        symptom="F0003 overvoltage fault",
        raw_summary="Siemens G120C showing F0003 fault",
        confidence=0.85,
        detected_model="G120C",
        kb_coverage=KBCoverage.NONE,
        context_source=ContextSource.TEXT_ONLY
    )
    print(f"   Intent: {intent.vendor} {intent.equipment_type} - {intent.symptom}")
    print(f"   Model: {intent.detected_model}")
    print()

    # Step 2: Check initial KB state (baseline)
    print("[Step 2] Checking baseline KB state...")
    db = DatabaseManager()

    try:
        initial_count_result = db.execute_query(
            "SELECT COUNT(*) FROM knowledge_atoms WHERE keywords @> ARRAY['G120C']"
        )
        initial_count = initial_count_result[0][0] if initial_count_result else 0
        print(f"   Initial atoms mentioning G120C: {initial_count}")
    except Exception as e:
        print(f"   [ERROR] Could not query database: {e}")
        print(f"   [INFO] Continuing anyway - will check total atoms instead")
        initial_count = None
    print()

    # Step 3: Run research pipeline
    print("[Step 3] Running research pipeline...")
    start_time = time.time()

    pipeline = ResearchPipeline()
    result = pipeline.run(intent)

    elapsed = time.time() - start_time
    print(f"   Pipeline completed in {elapsed:.2f}s")
    print(f"   Status: {result.status}")
    print(f"   Sources found: {len(result.sources_found)}")
    print(f"   Sources queued: {result.sources_queued}")
    print(f"   Estimated completion: {result.estimated_completion}")

    if result.error_message:
        print(f"   [ERROR] {result.error_message}")
    print()

    # Step 4: Check immediate results
    print("[Step 4] Validating immediate results...")

    if result.status == "failed":
        print("   [FAIL] Research pipeline failed")
        print("   [INFO] This may be due to:")
        print("          - No forum sources found (rare topic)")
        print("          - Network issues")
        print("          - Rate limiting")
        return False

    if result.sources_queued == 0:
        print("   [FAIL] No sources queued for ingestion")
        print("   [INFO] Possible causes:")
        print("          - All sources already processed (duplicates)")
        print("          - Database connection issues")
        return False

    print(f"   [PASS] {result.sources_queued} sources queued successfully")

    if result.sources_found:
        print(f"   [INFO] Sample URLs found:")
        for url in result.sources_found[:3]:
            print(f"          - {url}")
    print()

    # Step 5: Wait for ingestion (5 minutes)
    wait_time = 300  # 5 minutes
    print(f"[Step 5] Waiting {wait_time}s ({wait_time//60} minutes) for ingestion...")
    print("   [INFO] The 7-stage ingestion pipeline is processing sources:")
    print("          Stage 1: Source Acquisition (download/scrape)")
    print("          Stage 2: Content Extraction (parse text)")
    print("          Stage 3: Semantic Chunking (split into atoms)")
    print("          Stage 4: Atom Generation (LLM extraction)")
    print("          Stage 5: Quality Validation (score 0-100)")
    print("          Stage 6: Embedding Generation (OpenAI)")
    print("          Stage 7: Storage & Indexing (Supabase)")
    print()

    # Progress indicator
    for remaining in range(wait_time, 0, -30):
        print(f"   {remaining}s remaining... ", end="", flush=True)
        await asyncio.sleep(30)
        print("[OK]")

    print()

    # Step 6: Check KB for new atoms
    print("[Step 6] Checking for new atoms in KB...")

    try:
        if initial_count is not None:
            # Check G120C-specific atoms
            final_count_result = db.execute_query(
                "SELECT COUNT(*) FROM knowledge_atoms WHERE keywords @> ARRAY['G120C']"
            )
            final_count = final_count_result[0][0] if final_count_result else 0

            new_atoms = final_count - initial_count
            print(f"   Initial: {initial_count} atoms")
            print(f"   Final:   {final_count} atoms")
            print(f"   Delta:   +{new_atoms} atoms")

            if new_atoms > 0:
                print(f"   [PASS] {new_atoms} new atoms created!")
                success = True
            else:
                print("   [FAIL] No new atoms created")
                print("   [INFO] Possible causes:")
                print("          - Sources were low quality (failed validation)")
                print("          - Ingestion errors (check logs)")
                print("          - Processing still ongoing (try waiting longer)")
                success = False

        else:
            # Fallback: check recent atoms
            recent_result = db.execute_query(
                """
                SELECT COUNT(*) FROM knowledge_atoms
                WHERE created_at > NOW() - INTERVAL '10 minutes'
                """
            )
            recent_count = recent_result[0][0] if recent_result else 0

            print(f"   Recent atoms (last 10 min): {recent_count}")

            if recent_count > 0:
                print(f"   [PASS] {recent_count} atoms created recently!")
                success = True
            else:
                print("   [FAIL] No recent atoms found")
                success = False

    except Exception as e:
        print(f"   [ERROR] Database query failed: {e}")
        success = False

    print()

    # Step 7: Test searchability (if atoms were created)
    if success:
        print("[Step 7] Testing atom searchability...")

        try:
            # Search for G120C atoms
            search_result = db.execute_query(
                """
                SELECT title, keywords, source_url
                FROM knowledge_atoms
                WHERE keywords @> ARRAY['G120C']
                ORDER BY created_at DESC
                LIMIT 3
                """
            )

            if search_result:
                print(f"   [PASS] Found {len(search_result)} searchable atoms:")
                for i, row in enumerate(search_result, 1):
                    title = row[0]
                    keywords = row[1] if len(row) > 1 else []
                    source = row[2] if len(row) > 2 else "Unknown"
                    print(f"   {i}. {title}")
                    print(f"      Keywords: {', '.join(keywords[:5])}")
                    print(f"      Source: {source}")
            else:
                print("   [WARN] No atoms returned from search")
                success = False

        except Exception as e:
            print(f"   [ERROR] Search query failed: {e}")
            success = False

    print()
    print("=" * 80)

    if success:
        print("[SUCCESS] Research pipeline test PASSED!")
        print()
        print("Next steps:")
        print("1. Send a G120C query to the RivetCEO Telegram bot")
        print("2. Verify it returns Route A/B (KB-sourced answer)")
        print("3. Check answer quality and confidence score")
    else:
        print("[FAILED] Research pipeline test FAILED")
        print()
        print("Troubleshooting:")
        print("1. Check logs for ingestion errors")
        print("2. Verify database connection (Neon/Supabase)")
        print("3. Verify OpenAI API key is set")
        print("4. Try running again (sources may have been slow)")

    print("=" * 80)

    return success


if __name__ == "__main__":
    # Run async test
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    success = asyncio.run(test_research_pipeline())

    # Exit with appropriate code
    sys.exit(0 if success else 1)
