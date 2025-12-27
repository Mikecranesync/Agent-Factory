# TAB 1: PRINT INGESTION PIPELINE
# Copy everything below into Claude Code CLI

You are Tab 1 (Ingestion) in a 2-tab sprint to build the Electrical Prints feature for Rivet.

## AUTONOMOUS MODE SETTINGS
- Auto-accept all file edits
- Auto-accept bash commands except: rm -rf, sudo, DROP, DELETE
- Commit after each completed task
- If context reaches 80%, checkpoint and summarize

## YOUR IDENTITY
- Workstream: Prints Ingestion
- Branch: prints-ingestion
- Focus: Upload, OCR, chunking, vectorization, database

## FIRST ACTIONS
```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
git checkout -b prints-ingestion
git push -u origin prints-ingestion

# Install dependencies
pip install chromadb pdfplumber pdf2image pytesseract sentence-transformers --break-system-packages
```

## EXISTING CODE TO BUILD ON
```
agent_factory/integrations/telegram/ocr/
├── pipeline.py           # Extend for PDFs
├── gemini_provider.py    # Reuse for image OCR
└── claude_provider.py    # Reuse for analysis

agent_factory/rivet_pro/
├── database.py           # Add machines/prints tables
└── print_analyzer.py     # Extend for RAG
```

---

## YOUR TASKS

### Phase 1: Database Schema (Day 1)

**Task 1.1: Create Migration**
Create `migrations/002_create_prints_tables.sql`:
```sql
-- Machines table
CREATE TABLE IF NOT EXISTS machines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES rivet_users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    location VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, name)
);

-- Prints metadata
CREATE TABLE IF NOT EXISTS prints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    machine_id UUID REFERENCES machines(id) ON DELETE CASCADE,
    user_id UUID REFERENCES rivet_users(id),
    name VARCHAR(255) NOT NULL,
    file_path VARCHAR(512),
    print_type VARCHAR(100), -- 'wiring', 'hydraulic', 'control', 'p&id'
    description TEXT,
    page_count INTEGER DEFAULT 1,
    chunk_count INTEGER DEFAULT 0,
    vectorized BOOLEAN DEFAULT FALSE,
    collection_name VARCHAR(255),
    uploaded_at TIMESTAMP DEFAULT NOW(),
    vectorized_at TIMESTAMP
);

-- Chat history
CREATE TABLE IF NOT EXISTS print_chat_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES rivet_users(id),
    machine_id UUID REFERENCES machines(id),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    sources TEXT[],
    tokens_used INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_machines_user ON machines(user_id);
CREATE INDEX IF NOT EXISTS idx_prints_machine ON prints(machine_id);
CREATE INDEX IF NOT EXISTS idx_prints_user ON prints(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_user ON print_chat_history(user_id);
```

**Task 1.2: Run Migration**
Use existing `scripts/run_migration.py` pattern to execute.

**Task 1.3: Add Database Methods**
Update `agent_factory/rivet_pro/database.py`:
```python
# Machine CRUD
async def create_machine(self, user_id: str, name: str, description: str = None) -> dict
async def get_machines_by_user(self, user_id: str) -> List[dict]
async def get_machine_by_name(self, user_id: str, name: str) -> dict
async def delete_machine(self, machine_id: str) -> bool

# Print CRUD
async def create_print(self, machine_id: str, user_id: str, name: str, file_path: str, print_type: str) -> dict
async def get_prints_by_machine(self, machine_id: str) -> List[dict]
async def update_print_vectorized(self, print_id: str, collection_name: str, chunk_count: int) -> bool
async def delete_print(self, print_id: str) -> bool

# Chat history
async def save_chat_history(self, user_id: str, machine_id: str, question: str, answer: str, sources: List[str]) -> dict
async def get_chat_history(self, user_id: str, machine_id: str, limit: int = 10) -> List[dict]
```

---

### Phase 2: PDF Extraction (Day 1-2)

**Task 2.1: Create Prints Module**
Create directory structure:
```bash
mkdir -p agent_factory/prints/ingestion
touch agent_factory/prints/__init__.py
touch agent_factory/prints/ingestion/__init__.py
```

**Task 2.2: PDF Extractor**
Create `agent_factory/prints/ingestion/pdf_extractor.py`:
```python
import pdfplumber
from pdf2image import convert_from_path
from pathlib import Path
from typing import List, Dict
import tempfile

class PDFExtractor:
    """Extract text and images from electrical print PDFs."""
    
    def extract(self, pdf_path: Path) -> Dict:
        """
        Extract content from PDF.
        
        Returns:
            {
                "pages": [
                    {"page_num": 1, "text": "...", "has_images": True},
                    ...
                ],
                "total_pages": 5,
                "images": [Path, Path, ...]  # Extracted images for OCR
            }
        """
        pages = []
        images = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                
                # Check if page has images/diagrams
                has_images = len(page.images) > 0 if hasattr(page, 'images') else False
                
                pages.append({
                    "page_num": i + 1,
                    "text": text,
                    "has_images": has_images,
                    "tables": page.extract_tables()
                })
        
        # Convert pages with diagrams to images for OCR
        if any(p["has_images"] or len(p["text"]) < 100 for p in pages):
            pdf_images = convert_from_path(str(pdf_path), dpi=200)
            for i, img in enumerate(pdf_images):
                img_path = Path(tempfile.mktemp(suffix=f"_page{i+1}.png"))
                img.save(img_path)
                images.append(img_path)
        
        return {
            "pages": pages,
            "total_pages": len(pages),
            "images": images
        }
```

**Task 2.3: Image OCR Integration**
Create `agent_factory/prints/ingestion/ocr_processor.py`:
```python
from pathlib import Path
from typing import List
import pytesseract
from PIL import Image

# Reuse existing providers
from agent_factory.integrations.telegram.ocr.gemini_provider import GeminiVisionProvider

class PrintOCRProcessor:
    """OCR processor optimized for electrical prints."""
    
    def __init__(self):
        self.gemini = GeminiVisionProvider()
    
    async def process_image(self, image_path: Path) -> str:
        """
        Extract text from electrical print image.
        Uses Gemini for diagram understanding, falls back to Tesseract.
        """
        try:
            # Use Gemini for better diagram understanding
            result = await self.gemini.analyze_image(
                image_path,
                prompt="""Extract ALL text from this electrical schematic including:
                - Wire labels and numbers
                - Component names and values
                - Terminal designations
                - Voltage ratings
                - Circuit breaker labels
                - Any handwritten notes
                
                Preserve the spatial relationship (e.g., "LEFT SIDE:", "PANEL A:")"""
            )
            return result.get("text", "")
        except Exception:
            # Fallback to Tesseract
            image = Image.open(image_path)
            return pytesseract.image_to_string(image)
    
    async def process_pdf_pages(self, image_paths: List[Path]) -> List[dict]:
        """Process multiple PDF page images."""
        results = []
        for i, path in enumerate(image_paths):
            text = await self.process_image(path)
            results.append({
                "page_num": i + 1,
                "ocr_text": text,
                "source": str(path)
            })
        return results
```

---

### Phase 3: Chunking & Vectorization (Day 2)

**Task 3.1: Electrical-Aware Chunker**
Create `agent_factory/prints/ingestion/chunker.py`:
```python
from typing import List, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter
import re

class ElectricalPrintChunker:
    """
    Chunk electrical prints while preserving:
    - Circuit boundaries
    - Component groupings
    - Wire run continuity
    """
    
    def __init__(self, chunk_size: int = 400, overlap: int = 100):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=[
                "\n\n",  # Paragraph breaks
                "\n---",  # Section dividers
                "\nCIRCUIT",  # Circuit headers
                "\nPANEL",  # Panel sections
                "\n",
                " "
            ]
        )
    
    def chunk(self, pages: List[Dict], print_name: str) -> List[Dict]:
        """
        Chunk extracted pages into vector-ready documents.
        
        Returns list of:
            {
                "text": "chunk content...",
                "metadata": {
                    "print_name": "Main Panel Wiring",
                    "page_num": 2,
                    "section": "Motor Control",
                    "chunk_index": 5
                }
            }
        """
        chunks = []
        chunk_index = 0
        
        for page in pages:
            page_text = page.get("text", "") + "\n" + page.get("ocr_text", "")
            
            # Detect section headers
            section = self._detect_section(page_text)
            
            # Split into chunks
            page_chunks = self.splitter.split_text(page_text)
            
            for chunk_text in page_chunks:
                if len(chunk_text.strip()) < 20:
                    continue  # Skip tiny chunks
                
                chunks.append({
                    "text": chunk_text,
                    "metadata": {
                        "print_name": print_name,
                        "page_num": page.get("page_num", 1),
                        "section": section,
                        "chunk_index": chunk_index,
                        "has_circuit_ref": bool(re.search(r'circuit|breaker|fuse', chunk_text.lower())),
                        "has_voltage_ref": bool(re.search(r'\d+\s*[vV]|volt', chunk_text.lower()))
                    }
                })
                chunk_index += 1
        
        return chunks
    
    def _detect_section(self, text: str) -> str:
        """Detect section type from text content."""
        text_lower = text.lower()
        
        if "motor" in text_lower:
            return "Motor Control"
        elif "panel" in text_lower or "breaker" in text_lower:
            return "Panel/Distribution"
        elif "plc" in text_lower or "input" in text_lower or "output" in text_lower:
            return "PLC I/O"
        elif "safety" in text_lower or "e-stop" in text_lower:
            return "Safety Circuit"
        elif "sensor" in text_lower or "switch" in text_lower:
            return "Sensors/Switches"
        else:
            return "General"
```

**Task 3.2: ChromaDB Vectorizer**
Create `agent_factory/prints/ingestion/vectorizer.py`:
```python
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict
from pathlib import Path
import os

class PrintVectorizer:
    """Embed and store print chunks in ChromaDB."""
    
    def __init__(self, persist_dir: str = None):
        self.persist_dir = persist_dir or os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Embedding model
        self.embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    
    def vectorize_print(
        self,
        user_id: str,
        machine_id: str,
        print_id: str,
        chunks: List[Dict]
    ) -> str:
        """
        Embed chunks and store in ChromaDB.
        
        Returns: collection_name
        """
        collection_name = f"user_{user_id}_machine_{machine_id}"
        
        # Get or create collection
        collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"user_id": user_id, "machine_id": machine_id}
        )
        
        # Prepare documents
        texts = [c["text"] for c in chunks]
        metadatas = [
            {**c["metadata"], "print_id": print_id}
            for c in chunks
        ]
        ids = [f"{print_id}_{i}" for i in range(len(chunks))]
        
        # Embed
        embeddings = self.embedder.encode(texts).tolist()
        
        # Store
        collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        return collection_name
    
    def delete_print_vectors(self, collection_name: str, print_id: str):
        """Remove all vectors for a specific print."""
        try:
            collection = self.client.get_collection(collection_name)
            # Get all IDs for this print
            results = collection.get(where={"print_id": print_id})
            if results["ids"]:
                collection.delete(ids=results["ids"])
        except Exception:
            pass  # Collection might not exist
```

---

### Phase 4: Integration Pipeline (Day 3)

**Task 4.1: Main Ingestion Pipeline**
Create `agent_factory/prints/ingestion/pipeline.py`:
```python
from pathlib import Path
from typing import Optional
import asyncio
import logging

from .pdf_extractor import PDFExtractor
from .ocr_processor import PrintOCRProcessor
from .chunker import ElectricalPrintChunker
from .vectorizer import PrintVectorizer
from agent_factory.rivet_pro.database import RIVETProDatabase

logger = logging.getLogger(__name__)

class PrintIngestionPipeline:
    """
    Complete pipeline: Upload → Extract → OCR → Chunk → Vectorize → Store
    """
    
    def __init__(self):
        self.pdf_extractor = PDFExtractor()
        self.ocr = PrintOCRProcessor()
        self.chunker = ElectricalPrintChunker()
        self.vectorizer = PrintVectorizer()
        self.db = RIVETProDatabase()
    
    async def ingest(
        self,
        file_path: Path,
        user_id: str,
        machine_id: str,
        print_name: str,
        print_type: str = "wiring",
        description: str = None
    ) -> dict:
        """
        Full ingestion pipeline.
        
        Returns:
            {
                "success": True,
                "print_id": "uuid",
                "chunk_count": 25,
                "collection_name": "user_xxx_machine_yyy"
            }
        """
        logger.info(f"Starting ingestion: {print_name} for machine {machine_id}")
        
        try:
            # 1. Create print record
            print_record = await self.db.create_print(
                machine_id=machine_id,
                user_id=user_id,
                name=print_name,
                file_path=str(file_path),
                print_type=print_type
            )
            print_id = print_record["id"]
            
            # 2. Extract from PDF
            if file_path.suffix.lower() == ".pdf":
                extracted = self.pdf_extractor.extract(file_path)
                pages = extracted["pages"]
                
                # 3. OCR images if needed
                if extracted["images"]:
                    ocr_results = await self.ocr.process_pdf_pages(extracted["images"])
                    # Merge OCR with extracted text
                    for i, ocr_result in enumerate(ocr_results):
                        if i < len(pages):
                            pages[i]["ocr_text"] = ocr_result["ocr_text"]
            else:
                # Direct image upload
                ocr_text = await self.ocr.process_image(file_path)
                pages = [{"page_num": 1, "text": "", "ocr_text": ocr_text}]
            
            # 4. Chunk
            chunks = self.chunker.chunk(pages, print_name)
            logger.info(f"Created {len(chunks)} chunks")
            
            # 5. Vectorize
            collection_name = self.vectorizer.vectorize_print(
                user_id=user_id,
                machine_id=machine_id,
                print_id=print_id,
                chunks=chunks
            )
            
            # 6. Update print record
            await self.db.update_print_vectorized(
                print_id=print_id,
                collection_name=collection_name,
                chunk_count=len(chunks)
            )
            
            logger.info(f"✅ Ingestion complete: {print_name}")
            
            return {
                "success": True,
                "print_id": print_id,
                "chunk_count": len(chunks),
                "collection_name": collection_name,
                "page_count": len(pages)
            }
            
        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
```

**Task 4.2: Telegram Upload Handler**
Create `agent_factory/prints/telegram_handlers.py` (upload part):
```python
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from pathlib import Path
import tempfile

from agent_factory.prints.ingestion.pipeline import PrintIngestionPipeline
from agent_factory.rivet_pro.database import RIVETProDatabase

pipeline = PrintIngestionPipeline()
db = RIVETProDatabase()

async def upload_print_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /upload_print <machine> command."""
    user_id = str(update.effective_user.id)
    args = context.args
    
    if not args:
        await update.message.reply_text(
            "📋 **Upload Electrical Print**\n\n"
            "Usage: `/upload_print <machine_name>`\n\n"
            "Example: `/upload_print Lathe_1`\n\n"
            "Then send a PDF or photo of the print."
        )
        return
    
    machine_name = " ".join(args)
    
    # Check if machine exists, create if not
    machine = await db.get_machine_by_name(user_id, machine_name)
    if not machine:
        machine = await db.create_machine(user_id, machine_name)
        await update.message.reply_text(f"✅ Created new machine: **{machine_name}**")
    
    # Store context for file upload
    context.user_data["pending_print_upload"] = {
        "machine_id": machine["id"],
        "machine_name": machine_name
    }
    
    await update.message.reply_text(
        f"📤 Ready to upload print for **{machine_name}**\n\n"
        "Send a PDF or photo of the electrical print now."
    )

async def handle_print_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle uploaded print file (PDF or photo)."""
    pending = context.user_data.get("pending_print_upload")
    
    if not pending:
        return  # Not expecting a print upload
    
    user_id = str(update.effective_user.id)
    machine_id = pending["machine_id"]
    machine_name = pending["machine_name"]
    
    # Clear pending state
    del context.user_data["pending_print_upload"]
    
    await update.message.reply_text("📥 Received! Processing print...")
    
    # Download file
    if update.message.document:
        file = await context.bot.get_file(update.message.document.file_id)
        file_name = update.message.document.file_name or "print.pdf"
        suffix = Path(file_name).suffix or ".pdf"
    else:
        file = await context.bot.get_file(update.message.photo[-1].file_id)
        file_name = "print.png"
        suffix = ".png"
    
    # Save to temp file
    temp_path = Path(tempfile.mktemp(suffix=suffix))
    await file.download_to_drive(temp_path)
    
    # Run ingestion
    result = await pipeline.ingest(
        file_path=temp_path,
        user_id=user_id,
        machine_id=machine_id,
        print_name=file_name.rsplit(".", 1)[0],
        print_type="wiring"
    )
    
    # Cleanup
    temp_path.unlink(missing_ok=True)
    
    if result["success"]:
        await update.message.reply_text(
            f"✅ **Print Uploaded Successfully!**\n\n"
            f"📄 **{file_name}**\n"
            f"🔧 Machine: {machine_name}\n"
            f"📊 Pages: {result.get('page_count', 1)}\n"
            f"🧩 Chunks: {result['chunk_count']}\n\n"
            f"Use `/chat_print {machine_name}` to ask questions!"
        )
    else:
        await update.message.reply_text(
            f"❌ Upload failed: {result.get('error', 'Unknown error')}\n\n"
            "Please try again or contact support."
        )

async def list_machines_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /list_machines command."""
    user_id = str(update.effective_user.id)
    
    machines = await db.get_machines_by_user(user_id)
    
    if not machines:
        await update.message.reply_text(
            "📋 No machines found.\n\n"
            "Create one with: `/upload_print <machine_name>`"
        )
        return
    
    msg = "🔧 **Your Machines:**\n\n"
    for m in machines:
        prints = await db.get_prints_by_machine(m["id"])
        msg += f"• **{m['name']}** - {len(prints)} print(s)\n"
    
    msg += "\nUse `/list_prints <machine>` to see prints for a machine."
    await update.message.reply_text(msg)

async def list_prints_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /list_prints <machine> command."""
    user_id = str(update.effective_user.id)
    args = context.args
    
    if not args:
        await update.message.reply_text("Usage: `/list_prints <machine_name>`")
        return
    
    machine_name = " ".join(args)
    machine = await db.get_machine_by_name(user_id, machine_name)
    
    if not machine:
        await update.message.reply_text(f"❌ Machine '{machine_name}' not found.")
        return
    
    prints = await db.get_prints_by_machine(machine["id"])
    
    if not prints:
        await update.message.reply_text(f"📋 No prints for **{machine_name}** yet.")
        return
    
    msg = f"📄 **Prints for {machine_name}:**\n\n"
    for p in prints:
        status = "✅" if p["vectorized"] else "⏳"
        msg += f"{status} **{p['name']}** ({p['print_type']})\n"
        msg += f"   Chunks: {p.get('chunk_count', 0)} | Uploaded: {p['uploaded_at'][:10]}\n\n"
    
    await update.message.reply_text(msg)

# Handler registrations (add to bot.py)
def register_print_handlers(application):
    """Register all print-related handlers."""
    application.add_handler(CommandHandler("upload_print", upload_print_command))
    application.add_handler(CommandHandler("list_machines", list_machines_command))
    application.add_handler(CommandHandler("list_prints", list_prints_command))
    
    # File handler for print uploads
    application.add_handler(MessageHandler(
        filters.Document.PDF | filters.PHOTO,
        handle_print_file,
        block=False
    ))
```

---

## COMMIT PROTOCOL
After EACH task:
```bash
git add -A
git commit -m "prints-ingestion: [component] description"
git push origin prints-ingestion
```

## SUCCESS CRITERIA
- [ ] Migration creates machines, prints, print_chat_history tables
- [ ] PDF extraction works (text + images)
- [ ] OCR captures electrical labels from images
- [ ] Chunking produces ~400 token chunks with metadata
- [ ] ChromaDB stores vectors organized by user/machine
- [ ] `/upload_print <machine>` accepts files
- [ ] `/list_machines` and `/list_prints` work

## UPDATE STATUS
After each phase, create: `/sprint/STATUS_PRINTS_TAB1.md`

## START NOW
Begin with Task 1.1 - Create the migration file.
