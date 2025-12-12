#!/usr/bin/env python3
"""
Atom Builder Demo - Convert PDF extractions to Knowledge Atoms

Demonstrates the complete pipeline:
1. Load PDF extraction JSON (from OEM PDF scraper)
2. Convert sections -> concept/procedure atoms
3. Convert tables -> specification/reference atoms
4. Generate embeddings (OpenAI text-embedding-3-small)
5. Save atoms as JSON (ready for Supabase)

Usage:
    poetry run python examples/atom_builder_demo.py
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.knowledge.atom_builder_from_pdf import AtomBuilderFromPDF, KnowledgeAtom


def create_sample_extraction():
    """
    Create a sample PDF extraction for testing.

    This simulates output from OEM PDF scraper.
    """
    sample_data = {
        "metadata": {
            "manufacturer": "allen_bradley",
            "filename": "1756-um001-sample.pdf",
            "file_size_kb": 1024,
            "title": "ControlLogix System Manual (Sample)",
            "product_family": "ControlLogix",
            "version": "21.0",
            "document_date": "10/2024",
            "page_count": 5,
            "extracted_at": "2025-12-10T15:00:00Z"
        },
        "pages": [
            {
                "page_number": 1,
                "sections": [
                    {
                        "heading": "What is a Programmable Logic Controller?",
                        "content": [
                            "A Programmable Logic Controller (PLC) is an industrial computer designed for automation.",
                            "PLCs monitor inputs, make decisions based on their program, and control outputs.",
                            "They are used in manufacturing, packaging, material handling, and process control.",
                            "Key features include real-time operation, reliability, and ease of programming."
                        ]
                    }
                ],
                "text": "What is a Programmable Logic Controller?\n...",
                "quality_score": 0.95
            },
            {
                "page_number": 2,
                "sections": [
                    {
                        "heading": "How to Create a Basic Ladder Logic Program",
                        "content": [
                            "Step 1: Open Studio 5000 software and create a new project.",
                            "Step 2: Add a new ladder logic routine to the MainProgram.",
                            "Step 3: Drag an XIC (Examine If Closed) instruction onto Rung 0.",
                            "Step 4: Drag an OTE (Output Energize) instruction next to the XIC.",
                            "Step 5: Assign tags to the instructions (e.g., Start_Button, Motor_Run).",
                            "Step 6: Download the program to the controller and test."
                        ]
                    }
                ],
                "text": "How to Create a Basic Ladder Logic Program\n...",
                "quality_score": 0.92
            },
            {
                "page_number": 3,
                "sections": [
                    {
                        "heading": "WARNING: Electrical Safety Precautions",
                        "content": [
                            "WARNING: Always disconnect power before servicing equipment.",
                            "Failure to follow these instructions may result in death or serious injury.",
                            "Only qualified personnel should install, wire, or service this equipment.",
                            "Follow all local electrical codes and safety regulations."
                        ]
                    }
                ],
                "text": "WARNING: Electrical Safety Precautions\n...",
                "quality_score": 0.98
            }
        ],
        "tables": [
            {
                "page_number": 4,
                "table_index": 0,
                "headers": ["Instruction", "Mnemonic", "Type", "Description"],
                "rows": [
                    ["Examine If Closed", "XIC", "Input", "Tests if bit is ON"],
                    ["Examine If Open", "XIO", "Input", "Tests if bit is OFF"],
                    ["Output Energize", "OTE", "Output", "Turns bit ON when rung is true"],
                    ["Output Latch", "OTL", "Output", "Latches bit ON (stays ON)"],
                    ["Output Unlatch", "OTU", "Output", "Unlatches bit OFF"]
                ],
                "row_count": 5,
                "column_count": 4
            }
        ],
        "images": [],
        "stats": {
            "page_count": 5,
            "table_count": 1,
            "image_count": 0,
            "total_text_length": 823,
            "low_quality_pages": 0
        }
    }

    # Save sample extraction
    sample_dir = Path("data/extracted")
    sample_dir.mkdir(parents=True, exist_ok=True)

    sample_file = sample_dir / "sample_allen_bradley_manual.json"
    with open(sample_file, "w", encoding="utf-8") as f:
        json.dump(sample_data, f, indent=2, ensure_ascii=False)

    print(f"[OK] Created sample extraction: {sample_file}")
    return sample_file


def demo_basic_conversion():
    """Demo 1: Basic PDF -> Atoms conversion."""
    print("\n" + "=" * 70)
    print("DEMO 1: BASIC PDF -> ATOMS CONVERSION")
    print("=" * 70)

    # Create sample extraction
    sample_file = create_sample_extraction()

    # Initialize builder
    builder = AtomBuilderFromPDF()

    # Process extraction
    atoms = builder.process_pdf_extraction(
        sample_file,
        output_dir=Path("data/atoms")
    )

    print(f"\n[OK] Generated {len(atoms)} atoms")
    return atoms


def demo_atom_inspection(atoms):
    """Demo 2: Inspect generated atoms."""
    print("\n" + "=" * 70)
    print("DEMO 2: INSPECT GENERATED ATOMS")
    print("=" * 70)

    for idx, atom in enumerate(atoms, 1):
        print(f"\n[ATOM {idx}/{len(atoms)}]")
        print(f"  ID: {atom.atom_id}")
        print(f"  Type: {atom.atom_type}")
        print(f"  Title: {atom.title}")
        print(f"  Summary: {atom.summary[:100]}...")
        print(f"  Difficulty: {atom.difficulty}")
        print(f"  Safety: {atom.safety_level}")
        if atom.safety_notes:
            print(f"  Safety Notes: {atom.safety_notes[:80]}...")
        print(f"  Keywords: {', '.join(atom.keywords[:5])}")
        print(f"  Source: {atom.source_document} (page {atom.source_pages[0]})")
        print(f"  Quality: {atom.quality_score:.2f}")
        print(f"  Embedding: {'Yes (' + str(len(atom.embedding)) + ' dims)' if atom.embedding else 'No'}")


def demo_atom_types():
    """Demo 3: Show different atom types."""
    print("\n" + "=" * 70)
    print("DEMO 3: ATOM TYPES BREAKDOWN")
    print("=" * 70)

    builder = AtomBuilderFromPDF()

    examples = {
        "concept": {
            "heading": "What is Ladder Logic?",
            "content": "Ladder logic is a graphical programming language used in PLCs. It resembles electrical ladder diagrams with rungs, contacts, and coils. Each rung represents a control statement."
        },
        "procedure": {
            "heading": "How to Configure Digital I/O",
            "content": "Step 1: Open the I/O Configuration tree. Step 2: Right-click and select New Module. Step 3: Select your I/O module from the catalog. Step 4: Configure module parameters. Step 5: Click OK to save."
        },
        "specification": {
            "heading": "Input Voltage Specifications",
            "content": "Operating Voltage: 24V DC, Input Impedance: 4.7k ohms, ON Threshold: 15V, OFF Threshold: 5V, Maximum Current: 7mA"
        }
    }

    print("\nAtom Type Detection Examples:\n")

    for atom_type, example in examples.items():
        detected = builder.detect_atom_type(example["heading"], example["content"][:200])
        match = "[OK]" if detected == atom_type else "[MISMATCH]"
        print(f"{match} Expected: {atom_type}, Detected: {detected}")
        print(f"     Heading: {example['heading']}")
        print()


def demo_difficulty_detection():
    """Demo 4: Difficulty level detection."""
    print("\n" + "=" * 70)
    print("DEMO 4: DIFFICULTY LEVEL DETECTION")
    print("=" * 70)

    builder = AtomBuilderFromPDF()

    examples = [
        ("Introduction to PLCs - Getting started with basic concepts", "beginner"),
        ("Advanced PID tuning techniques for optimal performance", "advanced"),
        ("Configuring EtherNet/IP communication parameters", "intermediate"),
    ]

    print()
    for content, expected in examples:
        detected = builder.detect_difficulty(content)
        match = "[OK]" if detected == expected else "[MISMATCH]"
        print(f"{match} Expected: {expected}, Detected: {detected}")
        print(f"     Content: {content[:60]}...")
        print()


def demo_safety_detection():
    """Demo 5: Safety level detection."""
    print("\n" + "=" * 70)
    print("DEMO 5: SAFETY LEVEL DETECTION")
    print("=" * 70)

    builder = AtomBuilderFromPDF()

    examples = [
        "DANGER: Arc flash hazard. Can cause death or serious injury.",
        "WARNING: High voltage present. Risk of electric shock.",
        "CAUTION: Improper wiring may damage the module.",
        "This is a normal operational note with no safety concerns."
    ]

    print()
    for content in examples:
        level, notes = builder.detect_safety_level(content)
        print(f"[{level.upper()}]")
        print(f"  Content: {content}")
        if notes:
            print(f"  Notes: {notes[:80]}...")
        print()


def demo_keyword_extraction():
    """Demo 6: Keyword extraction."""
    print("\n" + "=" * 70)
    print("DEMO 6: KEYWORD EXTRACTION")
    print("=" * 70)

    builder = AtomBuilderFromPDF()

    title = "ControlLogix L7 Programmable Controller Installation"
    content = """
    The ControlLogix L7 controller is a high-performance PLC designed for
    demanding industrial applications. It supports ladder logic, structured
    text, and function block programming. Installation requires proper
    grounding, power supply configuration, and I/O module assignment.
    """

    keywords = builder.extract_keywords(title, content)

    print(f"\nTitle: {title}")
    print(f"Content: {content.strip()[:100]}...")
    print(f"\nExtracted Keywords ({len(keywords)}):")
    print(f"  {', '.join(keywords[:15])}")
    print()


def demo_embedding_generation():
    """Demo 7: Embedding generation."""
    print("\n" + "=" * 70)
    print("DEMO 7: EMBEDDING GENERATION")
    print("=" * 70)

    builder = AtomBuilderFromPDF()

    if not builder.openai_client:
        print("\n[SKIP] OPENAI_API_KEY not set")
        print("       Set in .env to enable embeddings")
        return

    text = "Programmable Logic Controllers are industrial computers used for automation."

    print(f"\nText: {text}")
    print(f"Generating embedding...")

    embedding = builder.generate_embedding(text)

    if embedding:
        print(f"[OK] Generated {len(embedding)}-dimensional embedding")
        print(f"     First 5 values: {embedding[:5]}")
        print(f"     Model: text-embedding-3-small")
        print(f"     Cost: ~$0.000004 per embedding")
    else:
        print("[FAIL] Embedding generation failed")

    print()


def main():
    """Run all demos."""
    print("=" * 70)
    print("ATOM BUILDER FROM PDF - COMPLETE DEMO")
    print("=" * 70)
    print()
    print("This demo shows the complete atom building pipeline:")
    print("  1. Load PDF extraction JSON")
    print("  2. Detect atom types (concept, procedure, specification)")
    print("  3. Generate metadata (difficulty, safety, keywords)")
    print("  4. Generate embeddings (OpenAI)")
    print("  5. Save atoms as JSON (ready for Supabase)")
    print()

    # Run demos
    atoms = demo_basic_conversion()
    demo_atom_inspection(atoms)
    demo_atom_types()
    demo_difficulty_detection()
    demo_safety_detection()
    demo_keyword_extraction()
    demo_embedding_generation()

    # Final summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print("Atom Builder Features:")
    print("  [OK] PDF extraction -> Knowledge atoms")
    print("  [OK] 6 atom types (concept, procedure, specification, pattern, fault, reference)")
    print("  [OK] Automatic type detection")
    print("  [OK] Difficulty level detection (beginner, intermediate, advanced)")
    print("  [OK] Safety level detection (info, caution, warning, danger)")
    print("  [OK] Keyword extraction (top 20 searchable terms)")
    print("  [OK] Vector embeddings (OpenAI text-embedding-3-small)")
    print("  [OK] Citation tracking (source PDF + page numbers)")
    print("  [OK] Quality scoring")
    print()
    print("Output:")
    print("  - Atoms saved to: data/atoms/")
    print("  - Format: JSON (ready for Supabase)")
    print("  - Each atom: ~2KB JSON (~1KB compressed)")
    print()
    print("Next steps:")
    print("  1. Review generated atoms in data/atoms/")
    print("  2. Upload to Supabase knowledge_atoms table")
    print("  3. Test vector search queries")
    print("  4. Build prerequisite detection (analyze atom relationships)")
    print()
    print("Cost estimate (per 100-page manual):")
    print("  - Embeddings: ~500 atoms x $0.000004 = $0.002")
    print("  - Total: < $0.01 per manual")
    print()


if __name__ == "__main__":
    main()
