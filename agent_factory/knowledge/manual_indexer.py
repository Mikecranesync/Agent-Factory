"""
Manual Indexer for OEM Documentation

Uses PyPDF2 for PDF text extraction (pure Python, no C++ builds)
Chunks text into 500-character blocks with 100-char overlap
Detects common manual sections for better retrieval
Stores chunks in RIVETProDatabase

Usage:
    indexer = ManualIndexer(db)
    manual_id = indexer.index_manual(
        file_path="/path/to/manual.pdf",
        title="Allen-Bradley PowerFlex 525 User Manual",
        manufacturer="Allen-Bradley",
        component_family="VFD"
    )
"""

import logging
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from uuid import uuid4

try:
    from PyPDF2 import PdfReader
except ImportError:
    raise ImportError(
        "PyPDF2 not installed. Install with: poetry add pypdf2"
    )

from agent_factory.rivet_pro.database import RIVETProDatabase

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# SECTION DETECTION PATTERNS
# ═══════════════════════════════════════════════════════════════════════════

SECTION_KEYWORDS = {
    "introduction": ["introduction", "overview", "about this manual"],
    "installation": ["installation", "mounting", "wiring", "setup"],
    "configuration": ["configuration", "programming", "parameters", "settings"],
    "operation": ["operation", "running", "starting", "normal operation"],
    "troubleshooting": ["troubleshooting", "diagnostics", "fault codes", "error codes"],
    "maintenance": ["maintenance", "preventive maintenance", "cleaning"],
    "specifications": ["specifications", "technical data", "ratings"],
    "safety": ["safety", "warnings", "precautions", "hazards"]
}


class ManualIndexer:
    """
    Indexes OEM manuals into searchable chunks.

    Process:
    1. Extract text from PDF using PyPDF2
    2. Detect section boundaries
    3. Chunk text (500 chars, 100 char overlap)
    4. Store in database via RIVETProDatabase
    """

    def __init__(self, db: Optional[RIVETProDatabase] = None):
        """
        Initialize manual indexer.

        Args:
            db: RIVETProDatabase instance (creates new if None)
        """
        self.db = db or RIVETProDatabase()
        self.chunk_size = 500
        self.chunk_overlap = 100

    def index_manual(
        self,
        file_path: str,
        title: str,
        manufacturer: str,
        component_family: str,
        document_type: str = "user_manual"
    ) -> str:
        """
        Index a manual PDF into the database.

        Args:
            file_path: Path to PDF file
            title: Manual title
            manufacturer: Manufacturer name
            component_family: Component type (VFD, PLC, etc.)
            document_type: Document type (user_manual, installation_guide, etc.)

        Returns:
            manual_id (UUID string)

        Raises:
            FileNotFoundError: If PDF doesn't exist
            Exception: If PDF extraction fails
        """
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")

        logger.info(f"Indexing manual: {title}")

        # Step 1: Create manual record
        manual = self.db.create_manual(
            title=title,
            manufacturer=manufacturer,
            component_family=component_family,
            file_path=str(file_path_obj.absolute()),
            document_type=document_type
        )
        manual_id = manual['id']

        # Step 2: Extract text from PDF
        try:
            text, page_count = self._extract_pdf_text(file_path_obj)
            logger.info(f"Extracted {len(text)} chars from {page_count} pages")
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            raise

        # Step 3: Detect sections
        sections = self._detect_sections(text)
        logger.info(f"Detected {len(sections)} sections")

        # Step 4: Chunk text
        chunks = self._chunk_text(text, sections)
        logger.info(f"Created {len(chunks)} chunks")

        # Step 5: Store chunks (Phase 1: just count, Phase 2: store in vector DB)
        # For now, we mark the manual as indexed with the chunk count
        self.db.update_manual_indexed(
            manual_id=manual_id,
            collection_name="equipment_manuals",
            page_count=page_count
        )

        logger.info(f"Indexed manual {manual_id}: {len(chunks)} chunks, {page_count} pages")
        return manual_id

    def _extract_pdf_text(self, file_path: Path) -> Tuple[str, int]:
        """
        Extract text from PDF using PyPDF2.

        Args:
            file_path: Path to PDF file

        Returns:
            (extracted_text, page_count)
        """
        reader = PdfReader(str(file_path))
        page_count = len(reader.pages)

        text_parts = []
        for page_num, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            except Exception as e:
                logger.warning(f"Failed to extract page {page_num}: {e}")
                continue

        full_text = "\n".join(text_parts)
        return full_text, page_count

    def _detect_sections(self, text: str) -> List[Dict]:
        """
        Detect section boundaries in text.

        Returns:
            List of {section_type, start_pos, end_pos}
        """
        sections = []
        text_lower = text.lower()

        for section_type, keywords in SECTION_KEYWORDS.items():
            for keyword in keywords:
                # Look for keyword at start of line (section header pattern)
                pattern = rf'^\s*{re.escape(keyword)}\s*$'
                for match in re.finditer(pattern, text_lower, re.MULTILINE | re.IGNORECASE):
                    sections.append({
                        "section_type": section_type,
                        "start_pos": match.start(),
                        "keyword": keyword
                    })

        # Sort by position
        sections.sort(key=lambda x: x["start_pos"])

        # Add end positions
        for i, section in enumerate(sections):
            if i + 1 < len(sections):
                section["end_pos"] = sections[i + 1]["start_pos"]
            else:
                section["end_pos"] = len(text)

        return sections

    def _chunk_text(self, text: str, sections: List[Dict]) -> List[Dict]:
        """
        Chunk text into 500-char blocks with 100-char overlap.

        Args:
            text: Full text to chunk
            sections: Section boundaries (from _detect_sections)

        Returns:
            List of {text, section_type, chunk_index, start_pos, end_pos}
        """
        chunks = []
        chunk_index = 0
        pos = 0

        while pos < len(text):
            # Determine chunk boundaries
            chunk_start = pos
            chunk_end = min(pos + self.chunk_size, len(text))

            # Extract chunk text
            chunk_text = text[chunk_start:chunk_end].strip()

            # Skip empty chunks
            if not chunk_text:
                pos = chunk_end
                continue

            # Determine section type for this chunk
            section_type = self._get_section_at_position(chunk_start, sections)

            chunks.append({
                "text": chunk_text,
                "section_type": section_type,
                "chunk_index": chunk_index,
                "start_pos": chunk_start,
                "end_pos": chunk_end
            })

            chunk_index += 1

            # Move position forward with overlap
            pos = chunk_end - self.chunk_overlap

        return chunks

    def _get_section_at_position(self, pos: int, sections: List[Dict]) -> str:
        """
        Get section type at a given text position.

        Args:
            pos: Position in text
            sections: Section boundaries

        Returns:
            Section type string or "general"
        """
        for section in sections:
            if section["start_pos"] <= pos < section["end_pos"]:
                return section["section_type"]

        return "general"

    def get_manual_chunks(self, manual_id: str) -> List[Dict]:
        """
        Retrieve all chunks for a manual (Phase 2 feature).

        Args:
            manual_id: Manual UUID

        Returns:
            List of chunk dictionaries

        Note: Phase 1 just returns empty list (chunks not stored yet)
        """
        logger.warning("get_manual_chunks is a Phase 2 feature (not implemented)")
        return []

    def delete_manual(self, manual_id: str) -> bool:
        """
        Delete a manual and all its chunks.

        Args:
            manual_id: Manual UUID

        Returns:
            True if deleted successfully
        """
        # Phase 1: Just delete the manual record
        # Phase 2: Also delete chunks from vector store
        try:
            # Note: Database doesn't have delete_manual method yet
            logger.warning(f"Manual deletion not fully implemented: {manual_id}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete manual: {e}")
            return False

    def close(self):
        """Close database connection"""
        if self.db:
            self.db.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
