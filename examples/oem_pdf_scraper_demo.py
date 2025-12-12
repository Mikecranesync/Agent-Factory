#!/usr/bin/env python3
"""
OEM PDF Scraper Demo - Test extraction with real manufacturer PDFs

Tests PDF processing pipeline with actual OEM documentation:
- Allen-Bradley ControlLogix Programming Manual
- Siemens S7-1200 System Manual
- Mitsubishi iQ-R Programming Manual
- Omron NJ/NX Programming Manual

Usage:
    poetry run python examples/oem_pdf_scraper_demo.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.research.oem_pdf_scraper_agent import OEMPDFScraperAgent


def demo_allen_bradley():
    """Test with Allen-Bradley documentation."""
    print("\n" + "=" * 70)
    print("DEMO 1: ALLEN-BRADLEY DOCUMENTATION")
    print("=" * 70)

    scraper = OEMPDFScraperAgent()

    # Allen-Bradley PDFs (publicly available technical literature)
    # These are EXAMPLE URLs - you may need to find current/valid links
    ab_pdfs = [
        # ControlLogix Programming Manual
        # https://literature.rockwellautomation.com/idc/groups/literature/documents/um/1756-um001_-en-p.pdf

        # CompactLogix System Overview
        # https://literature.rockwellautomation.com/idc/groups/literature/documents/um/1769-um011_-en-p.pdf
    ]

    print("\nNOTE: Add actual Allen-Bradley PDF URLs to ab_pdfs list above")
    print("Find at: https://literature.rockwellautomation.com")
    print()

    if ab_pdfs and ab_pdfs[0]:  # Check if URLs are provided
        results = scraper.process_manufacturer("allen_bradley", ab_pdfs, extract_images=True)
        return results
    else:
        print("SKIPPED: No URLs provided\n")
        return []


def demo_siemens():
    """Test with Siemens documentation."""
    print("\n" + "=" * 70)
    print("DEMO 2: SIEMENS DOCUMENTATION")
    print("=" * 70)

    scraper = OEMPDFScraperAgent()

    # Siemens PDFs (publicly available technical documentation)
    siemens_pdfs = [
        # S7-1200 System Manual
        # https://support.industry.siemens.com/cs/document/109742705/s7-1200-programmable-controller-system-manual

        # TIA Portal Programming Guide
        # https://support.industry.siemens.com/cs/document/109478047/step-7-basic-tia-portal-getting-started
    ]

    print("\nNOTE: Add actual Siemens PDF URLs to siemens_pdfs list above")
    print("Find at: https://support.industry.siemens.com")
    print()

    if siemens_pdfs and siemens_pdfs[0]:
        results = scraper.process_manufacturer("siemens", siemens_pdfs, extract_images=True)
        return results
    else:
        print("SKIPPED: No URLs provided\n")
        return []


def demo_mitsubishi():
    """Test with Mitsubishi documentation."""
    print("\n" + "=" * 70)
    print("DEMO 3: MITSUBISHI DOCUMENTATION")
    print("=" * 70)

    scraper = OEMPDFScraperAgent()

    # Mitsubishi PDFs
    mitsubishi_pdfs = [
        # MELSEC iQ-R Programming Manual
        # https://www.mitsubishielectric.com/fa/document/manual/plc/sh-081194eng/
    ]

    print("\nNOTE: Add actual Mitsubishi PDF URLs to mitsubishi_pdfs list above")
    print("Find at: https://www.mitsubishielectric.com/fa/products")
    print()

    if mitsubishi_pdfs and mitsubishi_pdfs[0]:
        results = scraper.process_manufacturer("mitsubishi", mitsubishi_pdfs, extract_images=True)
        return results
    else:
        print("SKIPPED: No URLs provided\n")
        return []


def demo_extraction_quality():
    """Demonstrate extraction quality checks."""
    print("\n" + "=" * 70)
    print("DEMO 4: EXTRACTION QUALITY VALIDATION")
    print("=" * 70)

    print("\nQuality checks implemented:")
    print("  1. Text density (< 50 chars/page = warning)")
    print("  2. OCR fallback detection (scanned PDFs)")
    print("  3. Table structure validation")
    print("  4. Image extraction success rate")
    print("  5. Metadata completeness")
    print()

    print("Quality metrics tracked:")
    print("  - Pages extracted")
    print("  - Tables extracted")
    print("  - Images extracted")
    print("  - Low quality warnings")
    print()

    print("Output includes:")
    print("  - quality_score (0.0 - 1.0) per page")
    print("  - warning messages for problematic pages")
    print("  - stats summary in JSON output")
    print()


def demo_file_organization():
    """Show how extracted files are organized."""
    print("\n" + "=" * 70)
    print("DEMO 5: FILE ORGANIZATION")
    print("=" * 70)

    print("\nExtracted content structure:")
    print()
    print("data/")
    print("+-- cache/")
    print("|   +-- pdfs/")
    print("|       +-- allen_bradley/")
    print("|       |   +-- allen_bradley_abc123.pdf")
    print("|       +-- siemens/")
    print("|       +-- mitsubishi/")
    print("+-- extracted/")
    print("|   +-- allen_bradley_manual.json  # Structured extraction")
    print("|   +-- allen_bradley_manual/")
    print("|       +-- images/")
    print("|           +-- page1_img0.png     # Diagrams, schematics")
    print("|           +-- page5_img2.png")
    print()

    print("JSON output structure:")
    print("{")
    print('  "metadata": {')
    print('    "manufacturer": "allen_bradley",')
    print('    "product_family": "ControlLogix",')
    print('    "version": "21.0",')
    print('    "page_count": 350')
    print("  },")
    print('  "pages": [')
    print("    {")
    print('      "page_number": 1,')
    print('      "sections": [')
    print('        {"heading": "Chapter 3: Ladder Logic", "content": [...]}')
    print("      ],")
    print('      "quality_score": 0.95')
    print("    }")
    print("  ],")
    print('  "tables": [...],')
    print('  "images": [...]')
    print("}")
    print()


def demo_next_steps():
    """Show integration with knowledge atom builder."""
    print("\n" + "=" * 70)
    print("NEXT STEPS: INTEGRATION WITH ATOM BUILDER")
    print("=" * 70)

    print("\n1. Convert extracted content -> Knowledge Atoms")
    print("   - Each section becomes a concept/procedure atom")
    print("   - Tables become specification/reference atoms")
    print("   - Images linked as visual aids")
    print()

    print("2. Validate against Knowledge Atom Standard")
    print("   - IEEE LOM compliance")
    print("   - Citation integrity (source PDF + page number)")
    print("   - Safety level classification")
    print()

    print("3. Store in Supabase knowledge_atoms table")
    print("   - Full-text search on content")
    print("   - Vector search on embeddings")
    print("   - Filter by manufacturer, product, version")
    print()

    print("4. Quality control")
    print("   - Human review for low-quality extractions")
    print("   - Accuracy validation against original PDF")
    print("   - Completeness checks")
    print()

    print("Files to create:")
    print("  - agents/knowledge/atom_builder_from_pdf.py")
    print("  - agents/knowledge/quality_validator.py")
    print("  - agents/knowledge/knowledge_librarian.py")
    print()


def main():
    """Run all demos."""
    print("=" * 70)
    print("OEM PDF SCRAPER DEMO")
    print("=" * 70)
    print()
    print("This demo shows the OEM PDF extraction pipeline:")
    print("  1. Download PDF (with caching)")
    print("  2. Extract metadata (product, version, date)")
    print("  3. Extract text with layout preservation")
    print("  4. Extract tables with structure")
    print("  5. Extract images and diagrams")
    print("  6. Quality validation")
    print("  7. Save as structured JSON")
    print()

    # Run demos
    demo_allen_bradley()
    demo_siemens()
    demo_mitsubishi()
    demo_extraction_quality()
    demo_file_organization()
    demo_next_steps()

    # Final summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print("To use the OEM PDF scraper:")
    print()
    print("1. Find OEM documentation URLs:")
    print("   - Allen-Bradley: https://literature.rockwellautomation.com")
    print("   - Siemens: https://support.industry.siemens.com")
    print("   - Mitsubishi: https://www.mitsubishielectric.com/fa/products")
    print("   - Omron: https://industrial.omron.com/en/products")
    print()
    print("2. Update demo script with actual URLs")
    print()
    print("3. Run extraction:")
    print("   poetry run python examples/oem_pdf_scraper_demo.py")
    print()
    print("4. Review extracted content:")
    print("   - JSON files: data/extracted/*.json")
    print("   - Images: data/extracted/*/images/")
    print()
    print("5. Build knowledge atoms:")
    print("   - Run atom builder on extracted JSON")
    print("   - Validate quality and accuracy")
    print("   - Store in Supabase")
    print()
    print("Key features:")
    print("  [OK] Multi-column layout detection")
    print("  [OK] Table structure preservation")
    print("  [OK] Image/diagram extraction")
    print("  [OK] Quality validation")
    print("  [OK] Manufacturer-specific patterns")
    print("  [OK] Caching to avoid re-downloads")
    print()


if __name__ == "__main__":
    main()
