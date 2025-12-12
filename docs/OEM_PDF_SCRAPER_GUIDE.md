# OEM PDF Documentation Scraper - Complete Guide

**Last Updated:** 2025-12-10
**Status:** Production Ready
**Agent:** `agents/research/oem_pdf_scraper_agent.py`

---

## Overview

The OEM PDF Documentation Scraper extracts structured knowledge from manufacturer PDFs (manuals, programming guides, datasheets). It handles the unique challenges of technical documentation:

- **Multi-column layouts** (common in reference manuals)
- **Complex tables** (I/O specifications, instruction sets)
- **Embedded diagrams** (wiring schematics, ladder logic)
- **Hierarchical sections** (chapters, sections, subsections)
- **Mixed content types** (text, code blocks, tables, images)

---

## Key Features

### 1. Intelligent Text Extraction

**Layout Preservation:**
- Detects multi-column layouts by clustering text blocks
- Preserves reading order (top-to-bottom, left-to-right)
- Identifies section headers (larger font, bold, all caps)
- Reconstructs hierarchical structure (Chapter > Section > Subsection)

**Quality Validation:**
- Text density checks (flags scanned/low-quality PDFs)
- OCR fallback detection
- Per-page quality scores (0.0 - 1.0)
- Warning messages for problematic pages

### 2. Table Extraction

**Structure Preservation:**
- Detects table boundaries and cell structure
- Extracts headers and data rows separately
- Handles merged cells and complex layouts
- Validates table completeness (row/column counts)

**Use Cases:**
- I/O specification tables
- Instruction set references
- Error code lookups
- Configuration parameter tables

### 3. Image/Diagram Extraction

**Capabilities:**
- Extracts all embedded images (PNG, JPG, etc.)
- Preserves image quality and format
- Labels by page number and index
- Organizes by manufacturer and document

**Typical Content:**
- Wiring diagrams
- Ladder logic screenshots
- Function block diagrams
- Hardware schematics
- Panel layouts

### 4. Metadata Extraction

**Automatic Detection:**
- Manufacturer (from config)
- Product family (regex pattern matching)
- Document version/revision
- Publication date
- Author and title (from PDF metadata)
- Page count

**Example:**
```json
{
  "manufacturer": "allen_bradley",
  "product_family": "ControlLogix",
  "version": "21.0",
  "document_date": "10/2024",
  "page_count": 350
}
```

### 5. Smart Caching

**Hash-Based Storage:**
- MD5 hash of URL determines cache key
- Organized by manufacturer
- Checks cache before re-downloading
- Reduces bandwidth and processing time

**Cache Structure:**
```
data/cache/pdfs/
+-- allen_bradley/
|   +-- allen_bradley_a1b2c3d4e5f6.pdf
+-- siemens/
|   +-- siemens_f6e5d4c3b2a1.pdf
```

---

## Supported Manufacturers

| Manufacturer | Base URL | Product Families | Manual Types |
|--------------|----------|------------------|--------------|
| **Allen-Bradley** | literature.rockwellautomation.com | CompactLogix, ControlLogix, MicroLogix, PLC-5 | User, Reference, Programming, Installation |
| **Siemens** | support.industry.siemens.com | S7-1200, S7-1500, TIA Portal | Manual, Programming, System, Hardware |
| **Mitsubishi** | mitsubishielectric.com/fa | MELSEC iQ-R, iQ-F | Manual, Programming, Reference |
| **Omron** | industrial.omron.com | CJ2, CP1, NJ, NX | Operation, Programming, Reference |
| **Schneider** | se.com/ww/en/download | Modicon M340, M580 | User Guide, Programming, Reference |
| **ABB** | new.abb.com/products | AC500, IRC5, PM5 | Manual, Programming, Application |

---

## Installation

```bash
# Dependencies
poetry add PyMuPDF pdfplumber Pillow requests

# Verify installation
poetry run python -c "from agents.research.oem_pdf_scraper_agent import OEMPDFScraperAgent; print('[OK]')"
```

---

## Usage

### Basic Example

```python
from agents.research.oem_pdf_scraper_agent import OEMPDFScraperAgent

# Initialize scraper
scraper = OEMPDFScraperAgent()

# Process single PDF
result = scraper.process_pdf(
    pdf_url="https://literature.rockwellautomation.com/.../manual.pdf",
    manufacturer="allen_bradley",
    extract_images=True
)

# Access extracted content
print(f"Pages: {result['stats']['page_count']}")
print(f"Tables: {result['stats']['table_count']}")
print(f"Images: {result['stats']['image_count']}")

# Result saved to: data/extracted/allen_bradley_manual.json
```

### Batch Processing

```python
# Process multiple PDFs from same manufacturer
pdf_urls = [
    "https://literature.rockwellautomation.com/.../manual1.pdf",
    "https://literature.rockwellautomation.com/.../manual2.pdf",
    "https://literature.rockwellautomation.com/.../manual3.pdf",
]

results = scraper.process_manufacturer(
    manufacturer="allen_bradley",
    pdf_urls=pdf_urls,
    extract_images=True
)

# Get overall statistics
stats = scraper.get_stats()
print(f"Total PDFs processed: {stats['pdfs_processed']}")
print(f"Total pages extracted: {stats['pages_extracted']}")
```

---

## Output Format

### JSON Structure

```json
{
  "metadata": {
    "manufacturer": "allen_bradley",
    "filename": "1756-um001_-en-p.pdf",
    "file_size_kb": 8420.5,
    "title": "ControlLogix System User Manual",
    "product_family": "ControlLogix",
    "version": "21.0",
    "document_date": "10/2024",
    "page_count": 350,
    "extracted_at": "2025-12-10T15:30:45Z"
  },
  "pages": [
    {
      "page_number": 1,
      "sections": [
        {
          "heading": "Chapter 3: Programming with Ladder Logic",
          "content": [
            "Ladder logic is the most common programming language...",
            "Each rung represents a control circuit..."
          ]
        }
      ],
      "text": "Chapter 3: Programming with Ladder Logic\nLadder logic is...",
      "quality_score": 0.95
    }
  ],
  "tables": [
    {
      "page_number": 45,
      "table_index": 0,
      "headers": ["Instruction", "Mnemonic", "Description"],
      "rows": [
        ["Examine If Closed", "XIC", "Tests if bit is ON"],
        ["Examine If Open", "XIO", "Tests if bit is OFF"]
      ],
      "row_count": 2,
      "column_count": 3
    }
  ],
  "images": [
    {
      "page_number": 12,
      "image_index": 0,
      "filename": "page12_img0.png",
      "path": "data/extracted/allen_bradley_manual/images/page12_img0.png",
      "format": "png",
      "size_kb": 45.2
    }
  ],
  "stats": {
    "page_count": 350,
    "table_count": 28,
    "image_count": 142,
    "total_text_length": 456789,
    "low_quality_pages": 3
  }
}
```

### File Organization

```
data/
+-- cache/
|   +-- pdfs/
|       +-- allen_bradley/
|       |   +-- allen_bradley_a1b2c3d4.pdf
|       +-- siemens/
|           +-- siemens_f6e5d4c3.pdf
+-- extracted/
    +-- allen_bradley_manual.json
    +-- allen_bradley_manual/
    |   +-- images/
    |       +-- page12_img0.png
    |       +-- page45_img1.png
    +-- siemens_s7-1200.json
    +-- siemens_s7-1200/
        +-- images/
            +-- page23_img0.png
```

---

## Quality Checks

### Text Extraction Quality

**Flags set when:**
- Page has < 50 characters (likely scanned/image-only)
- Very low text-to-page ratio
- Extraction returned empty

**Quality Score:**
- `1.0` = Perfect extraction
- `0.5-0.9` = Good quality, minor issues
- `< 0.5` = Low quality, human review needed

**Example Warning:**
```json
{
  "page_number": 127,
  "quality_score": 0.3,
  "warning": "Low text extraction (possible scan/image)"
}
```

### Table Extraction Quality

**Validates:**
- Minimum 2 rows (header + data)
- Consistent column count across rows
- Non-empty cells

**Skips:**
- Single-row tables (likely formatting artifacts)
- Empty tables

### Image Extraction Quality

**Tracks:**
- Successful extractions
- Failed extractions (corrupted images)
- Image format support

---

## Integration with Knowledge Atoms

### Step 1: Extract Content

```python
scraper = OEMPDFScraperAgent()
result = scraper.process_pdf(pdf_url, manufacturer)

# Result contains structured content ready for atom building
```

### Step 2: Convert to Atoms

```python
# Pseudo-code (to be implemented in atom_builder_from_pdf.py)
from agents.knowledge.atom_builder_from_pdf import AtomBuilderFromPDF

atom_builder = AtomBuilderFromPDF()

# Convert each section to a concept atom
for page in result['pages']:
    for section in page['sections']:
        atom = atom_builder.create_concept_atom(
            heading=section['heading'],
            content=section['content'],
            source_pdf=result['metadata']['filename'],
            page_number=page['page_number'],
            manufacturer=result['metadata']['manufacturer'],
            product_family=result['metadata']['product_family']
        )
        # Store atom in Supabase

# Convert tables to specification atoms
for table in result['tables']:
    atom = atom_builder.create_specification_atom(
        headers=table['headers'],
        rows=table['rows'],
        source_pdf=result['metadata']['filename'],
        page_number=table['page_number']
    )
    # Store atom in Supabase

# Link images to atoms
for image in result['images']:
    atom_builder.attach_visual_aid(
        atom_id=...,  # Find relevant atom
        image_path=image['path'],
        page_number=image['page_number']
    )
```

### Step 3: Validate Quality

```python
# Quality validation pipeline
for page in result['pages']:
    if page['quality_score'] < 0.5:
        # Flag for human review
        queue_for_human_review(page)
```

---

## Finding OEM Documentation URLs

### Allen-Bradley / Rockwell Automation

**Base URL:** https://literature.rockwellautomation.com

**How to Find:**
1. Go to https://literature.rockwellautomation.com
2. Search for product (e.g., "ControlLogix programming")
3. Filter by document type (User Manual, Reference Manual)
4. Right-click PDF link → Copy Link Address

**Example URL Pattern:**
```
https://literature.rockwellautomation.com/idc/groups/literature/documents/um/1756-um001_-en-p.pdf
```

### Siemens

**Base URL:** https://support.industry.siemens.com

**How to Find:**
1. Go to https://support.industry.siemens.com/cs/
2. Search product (e.g., "S7-1200 programming")
3. Click document → Download PDF

**Example URL Pattern:**
```
https://support.industry.siemens.com/cs/document/109742705/...
```

### Mitsubishi

**Base URL:** https://www.mitsubishielectric.com/fa/products

**How to Find:**
1. Navigate to product page (e.g., MELSEC iQ-R)
2. Click "Technical Documents" or "Manuals"
3. Download PDF

### Omron

**Base URL:** https://industrial.omron.com/en/products

**Process:**
1. Find product family (NJ, NX, CJ2, CP1)
2. Go to "Downloads" → "Manuals"
3. Download PDF

---

## Troubleshooting

### Problem: Download Fails

**Symptom:** `[ERROR] Download failed: 404`

**Solutions:**
1. Verify URL is correct (test in browser)
2. Check if PDF requires authentication
3. Check manufacturer's robots.txt (may block automated downloads)
4. Try manual download, then process local file

### Problem: Low Text Extraction

**Symptom:** `quality_score < 0.5`, "Low text extraction" warning

**Causes:**
- Scanned PDF (image-based, not text)
- Password-protected PDF
- Corrupted PDF

**Solutions:**
1. Use OCR tool (Tesseract) on scanned PDFs
2. Remove password protection
3. Re-download PDF

### Problem: Tables Not Detected

**Symptom:** `table_count: 0` but PDF has tables

**Causes:**
- Tables are images (not structured)
- Complex table formatting (merged cells, nested tables)

**Solutions:**
1. Use OCR for image-based tables
2. Manual extraction for complex tables
3. Report issue for future enhancement

### Problem: Images Not Extracted

**Symptom:** `image_count: 0` but PDF has diagrams

**Causes:**
- Images are vector graphics (not raster)
- Images are external references

**Solutions:**
1. Screenshot relevant pages
2. Use PDF editing tool to export images
3. Manual extraction as needed

---

## Performance Metrics

**Typical Processing Time:**
- Small PDF (50 pages): 5-10 seconds
- Medium PDF (200 pages): 20-40 seconds
- Large PDF (500 pages): 60-120 seconds

**Cache Performance:**
- First download: Full processing time
- Subsequent runs: < 1 second (cache hit)

**Memory Usage:**
- Small PDF: ~50 MB
- Large PDF: ~200-300 MB (peak during image extraction)

---

## Next Steps

### 1. Build Atom Builder

Create `agents/knowledge/atom_builder_from_pdf.py` to convert extracted JSON → knowledge atoms.

**Features:**
- Section → Concept Atom
- Table → Specification Atom
- Procedure → Procedure Atom
- Error Code → Fault Atom

### 2. Create Quality Validator

Create `agents/knowledge/quality_validator.py` to validate extracted content.

**Checks:**
- Accuracy (compare against original PDF)
- Completeness (all sections extracted)
- Citation integrity (page numbers correct)
- Safety compliance (warnings detected)

### 3. Build Knowledge Librarian

Create `agents/knowledge/knowledge_librarian.py` to organize atoms.

**Features:**
- Detect prerequisite chains (basic → advanced)
- Build topic hierarchies (electricity → PLCs → advanced)
- Identify knowledge gaps
- Recommend next topics to cover

---

## Example Workflow

```bash
# 1. Find OEM PDF URLs (user task)
# Visit https://literature.rockwellautomation.com
# Search "ControlLogix programming manual"
# Copy PDF URL

# 2. Run scraper
poetry run python -c "
from agents.research.oem_pdf_scraper_agent import OEMPDFScraperAgent

scraper = OEMPDFScraperAgent()
result = scraper.process_pdf(
    'https://literature.rockwellautomation.com/.../manual.pdf',
    'allen_bradley'
)
print(f'Extracted {result['stats']['page_count']} pages')
"

# 3. Review extracted JSON
cat data/extracted/allen_bradley_*.json

# 4. Build knowledge atoms (future step)
# poetry run python agents/knowledge/atom_builder_from_pdf.py --input data/extracted/allen_bradley_*.json

# 5. Store in Supabase (future step)
# Atoms automatically inserted into knowledge_atoms table with embeddings
```

---

## Resources

**Code:**
- Agent: `agents/research/oem_pdf_scraper_agent.py`
- Demo: `examples/oem_pdf_scraper_demo.py`

**Dependencies:**
- PyMuPDF (text/image extraction)
- pdfplumber (table extraction)
- Pillow (image processing)
- requests (HTTP downloads)

**Documentation:**
- This guide: `docs/OEM_PDF_SCRAPER_GUIDE.md`
- Knowledge Atom Standard: `docs/ATOM_SPEC_UNIVERSAL.md`
- Implementation Roadmap: `docs/IMPLEMENTATION_ROADMAP.md`

**Manufacturer Sites:**
- Allen-Bradley: https://literature.rockwellautomation.com
- Siemens: https://support.industry.siemens.com
- Mitsubishi: https://www.mitsubishielectric.com/fa
- Omron: https://industrial.omron.com

---

## FAQ

**Q: Can I process local PDFs?**

A: Yes! Modify the agent to accept file paths instead of URLs:

```python
# In oem_pdf_scraper_agent.py, add method:
def process_local_pdf(self, pdf_path: Path, manufacturer: str) -> Dict:
    """Process PDF from local file system."""
    metadata = self.extract_metadata(pdf_path, manufacturer)
    pages = self.extract_text_with_layout(pdf_path)
    # ... rest of processing
```

**Q: Does it work with password-protected PDFs?**

A: No. Remove password protection first using a PDF tool.

**Q: Can it handle OCR (scanned PDFs)?**

A: Partially. It will extract embedded text but won't OCR images. For scanned PDFs, use Tesseract OCR first, then process the OCR'd PDF.

**Q: How do I add a new manufacturer?**

A: Update the `MANUFACTURERS` dict in `oem_pdf_scraper_agent.py`:

```python
MANUFACTURERS = {
    "your_manufacturer": {
        "base_url": "https://docs.yourmanufacturer.com",
        "search_path": "/manuals/",
        "product_pattern": r"(YourProduct\d+)",
        "manual_types": ["user", "programming"],
    },
    # ... existing manufacturers
}
```

**Q: Can I extract code samples (ladder logic, structured text)?**

A: Yes! Code blocks are extracted as text within sections. Future enhancement: syntax highlighting and validation.

---

**Last Updated:** 2025-12-10
**Agent Version:** 1.0.0
**Status:** Production Ready
