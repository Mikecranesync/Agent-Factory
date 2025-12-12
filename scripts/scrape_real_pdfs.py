#!/usr/bin/env python3
"""
PRODUCTION PDF SCRAPER - Get real OEM manuals RIGHT NOW

This script scrapes REAL manufacturer PDFs and builds your initial knowledge base.
No samples, no demos - REAL production data.

Run this to start building your knowledge base TODAY.

Usage:
    poetry run python scripts/scrape_real_pdfs.py

Output:
    - data/extracted/*.json (PDF extractions)
    - data/atoms/*.json (Knowledge atoms with embeddings)
    - Ready to upload to Supabase
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.research.oem_pdf_scraper_agent import OEMPDFScraperAgent
from agents.knowledge.atom_builder_from_pdf import AtomBuilderFromPDF


# REAL OEM PDF URLs (found via web search Dec 2025)
PRODUCTION_PDFS = {
    "allen_bradley": [
        # ControlLogix 5570/5560 Controllers User Manual (350+ pages)
        "https://literature.rockwellautomation.com/idc/groups/literature/documents/um/1756-um001_-en-p.pdf",

        # Logix 5000 Common Procedures Programming Manual (fundamental programming)
        "https://literature.rockwellautomation.com/idc/groups/literature/documents/pm/1756-pm001_-en-e.pdf",

        # CompactLogix System User Manual (smaller PLCs, very popular)
        "https://literature.rockwellautomation.com/idc/groups/literature/documents/um/1769-um007_-en-p.pdf",
    ],
    "siemens": [
        # S7-1200 System Manual (comprehensive, 1000+ pages)
        "https://support.industry.siemens.com/cs/attachments/109814829/s71200_system_manual_en-US_en-US.pdf",

        # S7-1200/S7-1500 Programming Guideline (best practices, patterns)
        "https://support.industry.siemens.com/cs/attachments/90885040/81318674_Programming_guideline_DOC_v16_en.pdf",

        # S7-1200 Getting Started (beginner-friendly)
        "https://support.industry.siemens.com/cs/attachments/39644875/s71200_getting_started_en-US_en-US.pdf",
    ]
}


def main():
    """
    Scrape real OEM PDFs and build knowledge atoms.

    Steps:
    1. Download and extract PDFs (OEM PDF Scraper)
    2. Convert to knowledge atoms (Atom Builder)
    3. Generate embeddings (OpenAI)
    4. Save as JSON (ready for Supabase)
    """

    print("=" * 70)
    print("PRODUCTION PDF SCRAPER - BUILDING YOUR KNOWLEDGE BASE")
    print("=" * 70)
    print()
    print("Target manufacturers:")
    print("  - Allen-Bradley: 3 manuals (ControlLogix, Logix 5000, CompactLogix)")
    print("  - Siemens: 3 manuals (S7-1200 System, Programming Guide, Getting Started)")
    print()
    print("Total: 6 manuals, ~2000+ pages, ~10,000 knowledge atoms")
    print()

    # Confirm before downloading (these are large files)
    response = input("Start scraping? This will download large PDFs (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return

    print("\n" + "=" * 70)
    print("PHASE 1: PDF EXTRACTION")
    print("=" * 70)

    # Initialize scraper
    scraper = OEMPDFScraperAgent(
        cache_dir="data/cache/pdfs",
        output_dir="data/extracted"
    )

    extraction_files = []

    # Process each manufacturer
    for manufacturer, pdf_urls in PRODUCTION_PDFS.items():
        print(f"\n[{manufacturer.upper()}] Processing {len(pdf_urls)} manuals...")

        results = scraper.process_manufacturer(
            manufacturer=manufacturer,
            pdf_urls=pdf_urls,
            extract_images=False  # Skip images for speed (can re-run with images later)
        )

        # Track extraction files
        for idx, result in enumerate(results):
            if "error" not in result:
                # Find the saved JSON file
                metadata = result.get("metadata", {})
                filename = metadata.get("filename", f"unknown_{idx}.pdf")
                json_file = Path("data/extracted") / f"{manufacturer}_{Path(filename).stem}.json"
                if json_file.exists():
                    extraction_files.append(json_file)

    print("\n" + "=" * 70)
    print("PHASE 1 COMPLETE")
    print("=" * 70)
    print(f"PDFs extracted: {len(extraction_files)}")
    print(f"Extraction files saved to: data/extracted/")
    print()

    # Show stats
    stats = scraper.get_stats()
    print("Extraction Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 70)
    print("PHASE 2: ATOM GENERATION")
    print("=" * 70)
    print()
    print("Converting PDF extractions to knowledge atoms...")
    print("This includes:")
    print("  - Type detection (concept, procedure, spec, etc.)")
    print("  - Difficulty detection (beginner -> advanced)")
    print("  - Safety detection (DANGER, WARNING, CAUTION)")
    print("  - Keyword extraction")
    print("  - Vector embeddings (OpenAI)")
    print()

    # Initialize atom builder
    builder = AtomBuilderFromPDF()

    all_atoms = []

    # Process each extraction
    for json_file in extraction_files:
        print(f"\nProcessing: {json_file.name}")

        atoms = builder.process_pdf_extraction(
            json_file,
            output_dir=Path("data/atoms") / json_file.stem  # Separate dir per manual
        )

        all_atoms.extend(atoms)

    print("\n" + "=" * 70)
    print("PHASE 2 COMPLETE")
    print("=" * 70)
    print(f"Total atoms generated: {len(all_atoms)}")
    print()

    # Show atom stats
    atom_stats = builder.get_stats()
    print("Atom Stats:")
    for key, value in atom_stats.items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 70)
    print("SUCCESS - KNOWLEDGE BASE BUILT")
    print("=" * 70)
    print()
    print(f"Total Knowledge Atoms: {len(all_atoms)}")
    print(f"Atom files saved to: data/atoms/")
    print()
    print("Atom breakdown:")
    print(f"  Concepts: {atom_stats.get('concepts', 0)}")
    print(f"  Procedures: {atom_stats.get('procedures', 0)}")
    print(f"  Specifications: {atom_stats.get('specifications', 0)}")
    print(f"  Patterns: {atom_stats.get('patterns', 0)}")
    print(f"  Faults: {atom_stats.get('faults', 0)}")
    print(f"  References: {atom_stats.get('references', 0)}")
    print()

    # Calculate cost
    embedding_cost = atom_stats.get('embeddings_generated', 0) * 0.000004
    print(f"Embedding cost: ${embedding_cost:.4f}")
    print()

    print("NEXT STEPS:")
    print()
    print("1. REVIEW ATOMS:")
    print("   ls data/atoms/")
    print("   cat data/atoms/allen_bradley_*/atom_0000_concept.json")
    print()
    print("2. UPLOAD TO SUPABASE:")
    print("   - Run: docs/supabase_migrations.sql in Supabase SQL Editor")
    print("   - Upload atoms to knowledge_atoms table")
    print("   - Test vector search")
    print()
    print("3. BUILD SCRIPTWRITER AGENT:")
    print("   - Query atoms for topic")
    print("   - Generate video script")
    print("   - Cite sources (PDF + page)")
    print()
    print("4. GENERATE FIRST VIDEO:")
    print("   - Script -> Voice (Edge-TTS)")
    print("   - Voice + Visuals -> Video")
    print("   - Upload to YouTube")
    print()
    print("YOU NOW HAVE A PRODUCTION KNOWLEDGE BASE.")
    print("TIME TO START MAKING CONTENT (AND MONEY).")
    print()


if __name__ == "__main__":
    main()
