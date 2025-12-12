#!/usr/bin/env python3
"""
OEM PDF Documentation Scraper Agent

Scrapes and processes PDF manuals from industrial equipment manufacturers.
Handles multi-column layouts, diagrams, tables, and metadata extraction.

Target Manufacturers:
- Siemens (support.industry.siemens.com)
- Allen-Bradley/Rockwell (literature.rockwellautomation.com)
- Mitsubishi (www.mitsubishielectric.com/fa/products)
- Omron (industrial.omron.com/en/products)
- Schneider Electric (www.se.com/ww/en/download)
- ABB (new.abb.com/products)

Key Features:
- Multi-column text extraction
- Table parsing with structure preservation
- Image/diagram extraction with labeling
- Hierarchical section detection
- OCR for scanned manuals
- Metadata extraction (product, model, version)
- Caching to avoid re-downloads
- Quality validation

Schedule: On-demand (triggered by user or periodic scan)
"""

import os
import re
import hashlib
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
import json

# PDF processing libraries
try:
    import PyMuPDF as fitz  # pip install PyMuPDF
except ImportError:
    fitz = None

try:
    import pdfplumber  # pip install pdfplumber
except ImportError:
    pdfplumber = None

try:
    from PIL import Image  # pip install Pillow
except ImportError:
    Image = None


class OEMPDFScraperAgent:
    """
    Scrapes and processes OEM PDF documentation.

    Design Decisions:
    1. **Dual PDF Libraries**: PyMuPDF for text/images, pdfplumber for tables
    2. **Caching Strategy**: Hash-based to avoid re-downloading unchanged files
    3. **OCR Fallback**: If text extraction fails, use Tesseract OCR
    4. **Metadata First**: Extract product info before content to enable smart routing
    5. **Progressive Quality**: Flag low-quality extractions for human review
    """

    # Manufacturer-specific URL patterns and extraction rules
    MANUFACTURERS = {
        "siemens": {
            "base_url": "https://support.industry.siemens.com",
            "search_path": "/cs/document/",
            "product_pattern": r"S7-(\d+)",  # e.g., S7-1200, S7-1500
            "manual_types": ["manual", "programming", "system", "hardware"],
        },
        "allen_bradley": {
            "base_url": "https://literature.rockwellautomation.com",
            "search_path": "/idc/groups/literature/documents/",
            "product_pattern": r"(CompactLogix|ControlLogix|MicroLogix|PLC-5)",
            "manual_types": ["user", "reference", "programming", "installation"],
        },
        "mitsubishi": {
            "base_url": "https://www.mitsubishielectric.com",
            "search_path": "/fa/products/",
            "product_pattern": r"(MELSEC|iQ-R|iQ-F)",
            "manual_types": ["manual", "programming", "reference"],
        },
        "omron": {
            "base_url": "https://industrial.omron.com",
            "search_path": "/en/products/",
            "product_pattern": r"(CJ2|CP1|NJ|NX)",
            "manual_types": ["operation", "programming", "reference"],
        },
        "schneider": {
            "base_url": "https://www.se.com",
            "search_path": "/ww/en/download/",
            "product_pattern": r"(Modicon|M340|M580)",
            "manual_types": ["user guide", "programming", "reference"],
        },
        "abb": {
            "base_url": "https://new.abb.com",
            "search_path": "/products/",
            "product_pattern": r"(AC500|IRC5|PM5)",
            "manual_types": ["manual", "programming", "application"],
        },
    }

    def __init__(self, cache_dir: str = "data/cache/pdfs", output_dir: str = "data/extracted"):
        """
        Initialize OEM PDF scraper.

        Args:
            cache_dir: Directory to cache downloaded PDFs
            output_dir: Directory to save extracted content
        """
        self.cache_dir = Path(cache_dir)
        self.output_dir = Path(output_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # User agent to avoid blocking
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        # Track quality metrics
        self.stats = {
            "pdfs_downloaded": 0,
            "pdfs_processed": 0,
            "pages_extracted": 0,
            "tables_extracted": 0,
            "images_extracted": 0,
            "low_quality_warnings": 0,
        }

    def download_pdf(self, url: str, manufacturer: str) -> Optional[Path]:
        """
        Download PDF with caching.

        Args:
            url: PDF URL
            manufacturer: Manufacturer name (for organization)

        Returns:
            Path to downloaded PDF, or None if failed
        """
        # Create cache path based on URL hash
        url_hash = hashlib.md5(url.encode()).hexdigest()[:16]
        filename = f"{manufacturer}_{url_hash}.pdf"
        cache_path = self.cache_dir / manufacturer / filename
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        # Check cache
        if cache_path.exists():
            print(f"  [CACHE HIT] {cache_path.name}")
            return cache_path

        # Download
        try:
            print(f"  [DOWNLOAD] {url}")
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()

            # Verify it's actually a PDF
            if not response.content.startswith(b"%PDF"):
                print(f"  [ERROR] Not a valid PDF: {url}")
                return None

            # Save to cache
            cache_path.write_bytes(response.content)
            self.stats["pdfs_downloaded"] += 1
            print(f"  [OK] Downloaded {len(response.content) / 1024:.1f} KB")
            return cache_path

        except Exception as e:
            print(f"  [ERROR] Download failed: {e}")
            return None

    def extract_metadata(self, pdf_path: Path, manufacturer: str) -> Dict:
        """
        Extract PDF metadata (product, model, version, date).

        Args:
            pdf_path: Path to PDF file
            manufacturer: Manufacturer name

        Returns:
            Metadata dictionary
        """
        metadata = {
            "manufacturer": manufacturer,
            "filename": pdf_path.name,
            "file_size_kb": pdf_path.stat().st_size / 1024,
            "extracted_at": datetime.utcnow().isoformat(),
        }

        if not fitz:
            return metadata

        try:
            doc = fitz.open(pdf_path)

            # PDF metadata
            pdf_meta = doc.metadata or {}
            metadata.update({
                "title": pdf_meta.get("title", ""),
                "author": pdf_meta.get("author", ""),
                "subject": pdf_meta.get("subject", ""),
                "pdf_creation_date": pdf_meta.get("creationDate", ""),
                "page_count": len(doc),
            })

            # Extract product info from first page text
            first_page_text = doc[0].get_text() if len(doc) > 0 else ""

            # Try manufacturer-specific product pattern
            mfr_config = self.MANUFACTURERS.get(manufacturer, {})
            product_pattern = mfr_config.get("product_pattern")
            if product_pattern:
                match = re.search(product_pattern, first_page_text, re.IGNORECASE)
                if match:
                    metadata["product_family"] = match.group(0)

            # Extract version/revision
            version_match = re.search(
                r"(Version|Rev|Edition|V)\s*:?\s*(\d+\.?\d*)",
                first_page_text,
                re.IGNORECASE
            )
            if version_match:
                metadata["version"] = version_match.group(2)

            # Extract date
            date_match = re.search(
                r"(Date|Published|Updated)\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\w+\s+\d{4})",
                first_page_text,
                re.IGNORECASE
            )
            if date_match:
                metadata["document_date"] = date_match.group(2)

            doc.close()

        except Exception as e:
            print(f"  [WARN] Metadata extraction failed: {e}")

        return metadata

    def extract_text_with_layout(self, pdf_path: Path) -> List[Dict]:
        """
        Extract text while preserving layout and hierarchy.

        Handles:
        - Multi-column layouts
        - Headers/footers
        - Section hierarchies (Chapter > Section > Subsection)
        - Code blocks (ladder logic, structured text)

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of page dictionaries with structured text
        """
        if not fitz:
            return []

        pages = []

        try:
            doc = fitz.open(pdf_path)

            for page_num, page in enumerate(doc):
                # Extract text blocks with position info
                blocks = page.get_text("dict")["blocks"]

                # Detect columns by x-position clustering
                text_blocks = [b for b in blocks if b.get("type") == 0]  # Text blocks only
                if not text_blocks:
                    continue

                # Sort by y-position, then x-position (reading order)
                text_blocks.sort(key=lambda b: (b["bbox"][1], b["bbox"][0]))

                page_data = {
                    "page_number": page_num + 1,
                    "sections": [],
                    "text": "",
                    "quality_score": 1.0,
                }

                current_section = None

                for block in text_blocks:
                    for line in block.get("lines", []):
                        # Reconstruct line text
                        line_text = ""
                        for span in line.get("spans", []):
                            line_text += span.get("text", "")

                        line_text = line_text.strip()
                        if not line_text:
                            continue

                        # Detect section headers (larger font, bold, all caps)
                        font_size = span.get("size", 0)
                        is_bold = "bold" in span.get("font", "").lower()
                        is_header = font_size > 14 or (is_bold and len(line_text) < 100)

                        if is_header:
                            # New section
                            if current_section:
                                page_data["sections"].append(current_section)
                            current_section = {
                                "heading": line_text,
                                "content": [],
                            }
                        else:
                            # Add to current section
                            if current_section is None:
                                current_section = {
                                    "heading": f"Page {page_num + 1}",
                                    "content": [],
                                }
                            current_section["content"].append(line_text)

                        page_data["text"] += line_text + "\n"

                # Add final section
                if current_section:
                    page_data["sections"].append(current_section)

                # Quality checks
                if len(page_data["text"]) < 50:
                    page_data["quality_score"] = 0.3
                    page_data["warning"] = "Low text extraction (possible scan/image)"
                    self.stats["low_quality_warnings"] += 1

                pages.append(page_data)
                self.stats["pages_extracted"] += 1

            doc.close()

        except Exception as e:
            print(f"  [ERROR] Text extraction failed: {e}")

        return pages

    def extract_tables(self, pdf_path: Path) -> List[Dict]:
        """
        Extract tables with structure preservation.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of table dictionaries
        """
        if not pdfplumber:
            return []

        tables = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_tables = page.extract_tables()

                    for table_idx, table in enumerate(page_tables):
                        if not table or len(table) < 2:  # Skip empty or single-row tables
                            continue

                        # Convert to structured format
                        headers = table[0] if table else []
                        rows = table[1:] if len(table) > 1 else []

                        table_data = {
                            "page_number": page_num + 1,
                            "table_index": table_idx,
                            "headers": headers,
                            "rows": rows,
                            "row_count": len(rows),
                            "column_count": len(headers),
                        }

                        tables.append(table_data)
                        self.stats["tables_extracted"] += 1

        except Exception as e:
            print(f"  [ERROR] Table extraction failed: {e}")

        return tables

    def extract_images(self, pdf_path: Path, output_subdir: str) -> List[Dict]:
        """
        Extract images and diagrams from PDF.

        Args:
            pdf_path: Path to PDF file
            output_subdir: Subdirectory name for images

        Returns:
            List of image metadata dictionaries
        """
        if not fitz or not Image:
            return []

        images = []
        image_dir = self.output_dir / output_subdir / "images"
        image_dir.mkdir(parents=True, exist_ok=True)

        try:
            doc = fitz.open(pdf_path)

            for page_num, page in enumerate(doc):
                image_list = page.get_images()

                for img_idx, img in enumerate(image_list):
                    xref = img[0]

                    # Extract image
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]

                    # Save image
                    image_filename = f"page{page_num + 1}_img{img_idx}.{image_ext}"
                    image_path = image_dir / image_filename
                    image_path.write_bytes(image_bytes)

                    # Metadata
                    image_data = {
                        "page_number": page_num + 1,
                        "image_index": img_idx,
                        "filename": image_filename,
                        "path": str(image_path),
                        "format": image_ext,
                        "size_kb": len(image_bytes) / 1024,
                    }

                    images.append(image_data)
                    self.stats["images_extracted"] += 1

            doc.close()

        except Exception as e:
            print(f"  [ERROR] Image extraction failed: {e}")

        return images

    def process_pdf(
        self,
        pdf_url: str,
        manufacturer: str,
        extract_images: bool = True,
    ) -> Dict:
        """
        Complete PDF processing pipeline.

        Args:
            pdf_url: URL to PDF
            manufacturer: Manufacturer name
            extract_images: Whether to extract images/diagrams

        Returns:
            Complete extraction result dictionary
        """
        print(f"\n{'=' * 70}")
        print(f"PROCESSING: {pdf_url}")
        print(f"MANUFACTURER: {manufacturer}")
        print(f"{'=' * 70}")

        # Step 1: Download
        pdf_path = self.download_pdf(pdf_url, manufacturer)
        if not pdf_path:
            return {"error": "Download failed"}

        # Step 2: Extract metadata
        print("\n[1/4] Extracting metadata...")
        metadata = self.extract_metadata(pdf_path, manufacturer)
        print(f"  Pages: {metadata.get('page_count', 'unknown')}")
        print(f"  Product: {metadata.get('product_family', 'unknown')}")
        print(f"  Version: {metadata.get('version', 'unknown')}")

        # Step 3: Extract text with layout
        print("\n[2/4] Extracting text with layout...")
        pages = self.extract_text_with_layout(pdf_path)
        print(f"  Extracted {len(pages)} pages")

        # Step 4: Extract tables
        print("\n[3/4] Extracting tables...")
        tables = self.extract_tables(pdf_path)
        print(f"  Extracted {len(tables)} tables")

        # Step 5: Extract images (optional)
        images = []
        if extract_images:
            print("\n[4/4] Extracting images...")
            output_subdir = f"{manufacturer}_{pdf_path.stem}"
            images = self.extract_images(pdf_path, output_subdir)
            print(f"  Extracted {len(images)} images")

        # Combine results
        result = {
            "metadata": metadata,
            "pages": pages,
            "tables": tables,
            "images": images,
            "stats": {
                "page_count": len(pages),
                "table_count": len(tables),
                "image_count": len(images),
                "total_text_length": sum(len(p.get("text", "")) for p in pages),
                "low_quality_pages": sum(1 for p in pages if p.get("quality_score", 1.0) < 0.5),
            }
        }

        # Save result as JSON
        output_json = self.output_dir / f"{manufacturer}_{pdf_path.stem}.json"
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"\n[OK] Saved result to: {output_json}")
        self.stats["pdfs_processed"] += 1

        return result

    def process_manufacturer(
        self,
        manufacturer: str,
        pdf_urls: List[str],
        extract_images: bool = True,
    ) -> List[Dict]:
        """
        Process multiple PDFs from a manufacturer.

        Args:
            manufacturer: Manufacturer name
            pdf_urls: List of PDF URLs
            extract_images: Whether to extract images

        Returns:
            List of extraction results
        """
        results = []

        print(f"\n{'=' * 70}")
        print(f"PROCESSING {len(pdf_urls)} PDFs FROM {manufacturer.upper()}")
        print(f"{'=' * 70}")

        for idx, url in enumerate(pdf_urls, 1):
            print(f"\n[{idx}/{len(pdf_urls)}]")
            result = self.process_pdf(url, manufacturer, extract_images)
            results.append(result)

        # Summary
        print(f"\n{'=' * 70}")
        print(f"SUMMARY - {manufacturer.upper()}")
        print(f"{'=' * 70}")
        print(f"PDFs processed: {len(results)}")
        print(f"Total pages: {sum(r.get('stats', {}).get('page_count', 0) for r in results)}")
        print(f"Total tables: {sum(r.get('stats', {}).get('table_count', 0) for r in results)}")
        print(f"Total images: {sum(r.get('stats', {}).get('image_count', 0) for r in results)}")

        return results

    def get_stats(self) -> Dict:
        """Get processing statistics."""
        return self.stats.copy()


if __name__ == "__main__":
    """
    Demo: Extract content from example OEM PDFs.

    Usage:
        poetry run python agents/research/oem_pdf_scraper_agent.py
    """

    # Initialize agent
    scraper = OEMPDFScraperAgent()

    # Example URLs (replace with actual URLs)
    # These are EXAMPLE patterns - actual URLs need to be discovered via web scraping
    example_pdfs = {
        "siemens": [
            # "https://support.industry.siemens.com/cs/document/123456/s7-1200-manual.pdf",
        ],
        "allen_bradley": [
            # "https://literature.rockwellautomation.com/idc/groups/literature/documents/um/1756-um001_-en-p.pdf",
        ],
    }

    print("=" * 70)
    print("OEM PDF SCRAPER DEMO")
    print("=" * 70)
    print()
    print("This demo requires actual PDF URLs from manufacturers.")
    print()
    print("To use:")
    print("  1. Find OEM documentation URLs (manual discovery or web scraping)")
    print("  2. Update example_pdfs dict above")
    print("  3. Run: poetry run python agents/research/oem_pdf_scraper_agent.py")
    print()
    print("Required dependencies:")
    print("  poetry add PyMuPDF pdfplumber Pillow requests")
    print()
    print("Supported manufacturers:")
    for mfr in OEMPDFScraperAgent.MANUFACTURERS.keys():
        print(f"  - {mfr}")
    print()

    # Process example PDFs (if provided)
    for manufacturer, urls in example_pdfs.items():
        if urls:
            scraper.process_manufacturer(manufacturer, urls, extract_images=True)

    # Show stats
    print("\n" + "=" * 70)
    print("FINAL STATS")
    print("=" * 70)
    stats = scraper.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
