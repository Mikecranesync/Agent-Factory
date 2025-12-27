"""
Print Indexer for Electrical Schematics & Engineering Drawings

Similar to ManualIndexer but optimized for electrical prints:
- Smaller chunks (400 chars vs 500) for denser technical content
- Print-specific metadata (wiring, schematic, mechanical, P&ID)
- User-namespaced storage (per machine)

Usage:
    indexer = PrintIndexer(db)
    print_id = indexer.index_print(
        file_path="/path/to/schematic.pdf",
        machine_id="uuid",
        user_id="uuid",
        name="Motor Control Circuit - Page 1",
        print_type="wiring"
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
# PRINT TYPE DETECTION PATTERNS
# ═══════════════════════════════════════════════════════════════════════════

PRINT_TYPE_KEYWORDS = {
    "wiring": ["wiring", "wire", "cable", "terminal", "junction"],
    "schematic": ["schematic", "ladder", "logic", "circuit"],
    "mechanical": ["mechanical", "assembly", "dimension", "bom", "bill of materials"],
    "pid": ["p&id", "piping", "instrument", "flow diagram"],
    "layout": ["layout", "floor plan", "panel layout"],
    "loop": ["loop", "instrument loop", "control loop"]
}


class PrintIndexer:
    """
    Indexes electrical prints and engineering drawings.

    Differences from ManualIndexer:
    - Smaller chunks (400 chars) for denser content
    - Print-specific type detection
    - User-namespaced storage (each machine has own prints)
    """

    def __init__(self, db: Optional[RIVETProDatabase] = None):
        """
        Initialize print indexer.

        Args:
            db: RIVETProDatabase instance (creates new if None)
        """
        self.db = db or RIVETProDatabase()
        self.chunk_size = 400  # Smaller than manuals (400 vs 500)
        self.chunk_overlap = 80  # Proportional overlap

    def index_print(
        self,
        file_path: str,
        machine_id: str,
        user_id: str,
        name: str,
        print_type: Optional[str] = None
    ) -> str:
        """
        Index a print PDF into the database.

        Args:
            file_path: Path to PDF file
            machine_id: Machine UUID
            user_id: User UUID
            name: Print name (e.g., "Electrical Schematic Page 1")
            print_type: Print type (wiring, schematic, mechanical, pid, layout, loop)
                       Auto-detected if None

        Returns:
            print_id (UUID string)

        Raises:
            FileNotFoundError: If PDF doesn't exist
            Exception: If PDF extraction fails
        """
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")

        logger.info(f"Indexing print: {name}")

        # Step 1: Extract text from PDF
        try:
            text, page_count = self._extract_pdf_text(file_path_obj)
            logger.info(f"Extracted {len(text)} chars from {page_count} pages")
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            raise

        # Step 2: Auto-detect print type if not specified
        if not print_type:
            print_type = self._detect_print_type(text, name)
            logger.info(f"Auto-detected print type: {print_type}")

        # Step 3: Create print record
        print_record = self.db.create_print(
            machine_id=machine_id,
            user_id=user_id,
            name=name,
            file_path=str(file_path_obj.absolute()),
            print_type=print_type
        )
        print_id = print_record['id']

        # Step 4: Chunk text
        chunks = self._chunk_text(text)
        logger.info(f"Created {len(chunks)} chunks")

        # Step 5: Mark print as vectorized (Phase 1: just count, Phase 2: store chunks)
        collection_name = f"user_{user_id[:8]}_machine_{machine_id[:8]}"
        self.db.update_print_vectorized(
            print_id=print_id,
            chunk_count=len(chunks),
            collection_name=collection_name
        )

        logger.info(f"Indexed print {print_id}: {len(chunks)} chunks, type={print_type}")
        return print_id

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

    def _detect_print_type(self, text: str, name: str) -> str:
        """
        Auto-detect print type from text and filename.

        Args:
            text: Extracted PDF text
            name: Print name/filename

        Returns:
            Print type (wiring, schematic, mechanical, pid, layout, loop, or unknown)
        """
        text_lower = (text + " " + name).lower()

        # Check keywords in order of specificity
        for print_type, keywords in PRINT_TYPE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return print_type

        return "unknown"

    def _chunk_text(self, text: str) -> List[Dict]:
        """
        Chunk text into 400-char blocks with 80-char overlap.

        Args:
            text: Full text to chunk

        Returns:
            List of {text, chunk_index, start_pos, end_pos}
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

            chunks.append({
                "text": chunk_text,
                "chunk_index": chunk_index,
                "start_pos": chunk_start,
                "end_pos": chunk_end
            })

            chunk_index += 1

            # Move position forward with overlap
            pos = chunk_end - self.chunk_overlap

        return chunks

    def get_print_chunks(self, print_id: str) -> List[Dict]:
        """
        Retrieve all chunks for a print (Phase 2 feature).

        Args:
            print_id: Print UUID

        Returns:
            List of chunk dictionaries

        Note: Phase 1 just returns empty list (chunks not stored yet)
        """
        logger.warning("get_print_chunks is a Phase 2 feature (not implemented)")
        return []

    def delete_print(self, print_id: str) -> bool:
        """
        Delete a print and all its chunks.

        Args:
            print_id: Print UUID

        Returns:
            True if deleted successfully
        """
        # Phase 1: Just delete the print record
        # Phase 2: Also delete chunks from vector store
        try:
            # Note: Database doesn't have delete_print method yet
            logger.warning(f"Print deletion not fully implemented: {print_id}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete print: {e}")
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
