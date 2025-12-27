# Electrical Print Ingestion & Telegram Query System

## Quick Summary

**What it does:**
- Maintenance technicians upload PDF or photos of electrical/wiring prints.
- System chunks, vectorizes, and stores them in a database organized by user + machine.
- Technician queries the prints via Telegram chat.
- Claude answers questions about the wiring/schematics and can suggest troubleshooting steps.

**Why it matters:**
- Technicians don't need to carry paper prints or search files—they ask Telegram directly.
- Reduces downtime by providing instant schema lookups during maintenance.
- Builds institutional knowledge base of machine diagrams per location.

---

## Reference Implementations to Fork

| Component | Repo | Use Case | Fork Notes |
|-----------|------|----------|-----------|
| **PDF/Image → Vector DB pipeline** | https://github.com/alejandro-ao/ask-multiple-pdfs | Ingest PDFs, chunk, embed, store in ChromaDB. | Adapt to accept photos + PDFs; add OCR for handwritten labels on prints. |
| **Telegram bot + LLM** | https://github.com/BotoX/homeassistant-telegram-bot | Telegram webhook integration to FastAPI. | Replace HA logic with electrical print RAG queries. |
| **Claude with Tools/Skills** | https://github.com/ComposioHQ/awesome-claude-skills | Template for structured Claude function calls. | Build skill to query print vector DB; return diagram analysis + troubleshooting tips. |
| **Vector DB + embeddings** | https://github.com/chroma-core/chroma | Fast retrieval of relevant print sections by semantic search. | Use ChromaDB or Pinecone for scalability. Organize collections by `{user_id}/{machine_id}`. |
| **Document parsing (OCR + PDFs)** | https://github.com/Unstructured-IO/unstructured | Extract text, tables, images from electrical prints. | Better than pdfplumber for diagrams with labels. |

---

## Stack

**Backend:**
- Python FastAPI (Telegram webhook + API endpoints)
- Claude API (chat completion + structured function calls)
- LangChain (chunking, embedding, retrieval chains)
- ChromaDB or Pinecone (vector storage, organized by user/machine)
- PostgreSQL (metadata: user, machine ID, print name, upload date, file path)
- Telegram Bot API (webhook-based, not polling)

**Document Processing:**
- `pdfplumber` or `pdf2image` (PDF extraction)
- `pytesseract` or `paddleocr` (OCR for photos + handwritten labels)
- `unstructured` library (intelligent chunking of technical diagrams)

**Deployment:**
- Docker container on your VPS or AKS
- Telegram webhook listener (FastAPI)
- Cron job or async task queue (for print ingestion on upload)

---

## Feature Breakdown

### Epic 1: Print Upload & Ingestion

**Feature 1.1: Upload prints via Telegram or web**
- *Story 1.1.1:* Technician sends `/upload_print` command in Telegram DM bot.
  - AC: Bot prompts for machine name (autocomplete from user's machines).
  - AC: Technician uploads PDF or photo of electrical print.
  - AC: System validates file (size < 50MB, is image/PDF).
  - AC: Print stored in PostgreSQL with metadata (user_id, machine_id, file_path, upload_date, description).

**Feature 1.2: Parse & chunk electrical prints**
- *Story 1.2.1:* Backend extracts text, tables, and circuit labels from prints.
  - AC: PDFs extracted using `pdfplumber` + `pdf2image` pipeline.
  - AC: Photos run through OCR (`pytesseract` or `paddleocr`) to capture handwritten labels.
  - AC: Chunks preserve spatial context (e.g., "Circuit breaker panel, left side, labeled 'Motor Feeder'").
  - AC: Chunks are ~300–500 tokens (tuned for electrical diagram context).
  - AC: Metadata includes page #, section name, circuit ID if present.

**Feature 1.3: Vectorize & store**
- *Story 1.3.1:* Chunks are embedded and stored in ChromaDB, organized by user + machine.
  - AC: Embedding model: `sentence-transformers/all-MiniLM-L6-v2` or specialized engineering model.
  - AC: Collection name: `{user_id}_{machine_id}_{print_type}` (e.g., `user123_lathe1_wiring`).
  - AC: Each chunk stores: text, embedding, metadata (page, circuit ID, upload date).
  - AC: Searchable by circuit name, voltage, component type, etc.

---

### Epic 2: Telegram Query Interface

**Feature 2.1: Query prints via Telegram**
- *Story 2.1.1:* Technician asks questions about prints in Telegram chat.
  - AC: `/chat_print <machine>` selects a machine's prints for the session.
  - AC: Technician types natural language questions: "What's the wire gauge for the main feeder?"
  - AC: System retrieves relevant print chunks using vector similarity search.
  - AC: Claude answers based on print context + optionally provides safety notes (voltage, lockout procedures).
  - AC: Response is streamed in Telegram (shows as typing indicator).

**Feature 2.2: Multi-turn context per machine**
- *Story 2.2.1:* Conversation stays scoped to selected machine's prints.
  - AC: Session remembers selected machine for the user.
  - AC: Follow-up questions ("And what about the backup circuit?") retrieve from same machine's prints.
  - AC: User can switch machines with `/chat_print <new_machine>` and reset context.

**Feature 2.3: Source citations**
- *Story 2.3.1:* Claude cites which print/page answered the question.
  - AC: Response includes "Source: Wiring Diagram (Page 2)" or "Source: Control Panel Layout (uploaded 2025-12-20)".
  - AC: Technician can request `/view_print <source>` to pull up the referenced section.

---

### Epic 3: Troubleshooting & Analysis

**Feature 3.1: Troubleshooting guidance from prints**
- *Story 3.1.1:* Technician describes a symptom; Claude suggests diagnostics based on machine's prints.
  - AC: "Motor won't start" → Claude retrieves motor control circuit, suggests checking:
    - Voltage at contactor coil (from print)
    - Circuit breaker status
    - Overload relay state
  - AC: Responses are safety-conscious (e.g., "De-energize before testing").

**Feature 3.2: Parts & component lookup**
- *Story 3.2.1:* Technician asks for component details from print labels.
  - AC: "What's the model of VFD on Panel A?" → Claude extracts from print labels.
  - AC: If not found, Claude suggests where to check on the machine (physical location from diagram).

---

### Epic 4: Database Management

**Feature 4.1: Organize prints by machine**
- *Story 4.1.1:* User can create machines and assign prints to them.
  - AC: `/add_machine <name>` creates a new machine (e.g., "Lathe 1", "Drill Press 2").
  - AC: `/list_machines` shows all machines and print count.
  - AC: `/delete_print <machine> <print_name>` removes a print from the DB.

**Feature 4.2: Print library management**
- *Story 4.2.1:* User can tag, version, and retrieve print history.
  - AC: Prints auto-versioned (e.g., "Wiring_v1", "Wiring_v2") if same name uploaded twice.
  - AC: `/list_prints <machine>` shows all prints for that machine with upload dates.
  - AC: Can attach description: "Updated after 2025-10 maintenance" to track changes.

**Feature 4.3: Sharing prints (optional)**
- *Story 4.3.1:* User can share machine + prints with team members.
  - AC: `/share_machine <machine> <technician_telegram_id>` grants read access.
  - AC: Shared technician can query but not upload/delete.
  - AC: Logging tracks who accessed what and when.

---

## Architecture Diagram

```text
┌─────────────────────────────────────────────────────────────┐
│                      Technician (Telegram)                  │
│                                                              │
│  "What's the wire gauge?"                                   │
│  [sends photo of print]                                     │
│  "/upload_print lathe1"                                     │
└──────────────────────────┬──────────────────────────────────┘
                           │ Telegram API
                           ▼
        ┌──────────────────────────────────┐
        │  FastAPI Backend                 │
        │  (Telegram Webhook Listener)     │
        │                                  │
        │  - Parse commands                │
        │  - Validate files                │
        │  - Route to chat/upload handlers │
        └──────────────┬───────────────────┘
                       │
        ┌──────────────┴──────────────┐
        ▼                             ▼
    ┌──────────────────┐      ┌──────────────────────┐
    │  Upload Handler  │      │  Query Handler       │
    │                  │      │                      │
    │  1. Validate PDF │      │  1. Retrieve chunks  │
    │  2. OCR if photo │      │  2. Send to Claude   │
    │  3. Chunk text   │      │  3. Stream response  │
    │  4. Embed chunks │      │  4. Add citations    │
    │  5. Store in DB  │      │  5. Send to Telegram │
    └──────────────────┘      └──────────────────────┘
        │                             │
        └──────────────┬──────────────┘
                       ▼
        ┌──────────────────────────────────┐
        │  PostgreSQL Metadata             │
        │  - user_id, machine_id, print_id │
        │  - file paths, upload dates      │
        │  - collection names              │
        └──────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────┐
        │  ChromaDB Vector Store           │
        │  Collections per machine:        │
        │  - user123_lathe1_wiring         │
        │  - user123_lathe1_hydraulic      │
        │  - user456_drill_electrical      │
        └──────────────┬───────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────┐
        │  Claude API                      │
        │  (with vector retrieval tool)    │
        │  - RAG chain                     │
        │  - Troubleshooting logic         │
        │  - Safety guidelines             │
        └──────────────────────────────────┘
```

---

## Implementation Skeleton

### 1. Telegram Webhook Setup (FastAPI)

```python
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import asyncio

app = FastAPI()

# Initialize Telegram bot
bot_token = "YOUR_TELEGRAM_BOT_TOKEN"
application = Application.builder().token(bot_token).build()

# Add command handlers
async def start(update: Update, context):
    await update.message.reply_text(
        "📋 Electrical Print Query Bot\n\n"
        "/upload_print <machine> - Upload a wiring diagram\n"
        "/chat_print <machine> - Query prints for a machine\n"
        "/list_machines - View all your machines\n"
        "/add_machine <name> - Create new machine"
    )

async def upload_print(update: Update, context):
    """Handle print upload."""
    user_id = update.effective_user.id
    machine_name = " ".join(context.args) if context.args else None
    
    if not machine_name:
        await update.message.reply_text("Usage: /upload_print <machine_name>")
        return
    
    # Store machine context for next file upload
    context.user_data["pending_machine"] = machine_name
    await update.message.reply_text(f"Ready to upload print for {machine_name}. Send a PDF or photo.")

async def handle_file(update: Update, context):
    """Handle incoming print file."""
    user_id = update.effective_user.id
    machine_name = context.user_data.get("pending_machine", "unknown")
    
    file = await context.bot.get_file(update.message.document.file_id or update.message.photo[-1].file_id)
    file_path = f"/tmp/{user_id}_{machine_name}_{file.file_id}.pdf"
    
    await file.download_to_drive(file_path)
    
    # Queue ingestion task
    await ingest_print_async(user_id, machine_name, file_path)
    await update.message.reply_text(f"✅ Print uploaded for {machine_name}. Processing...")

# Register handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("upload_print", upload_print))
application.add_handler(MessageHandler(filters.Document.PDF | filters.PHOTO, handle_file))

@app.post("/webhook")
async def webhook(request: Request):
    """Telegram webhook endpoint."""
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}
```

### 2. Print Ingestion Pipeline

```python
from langchain.document_loaders import PDFPlumberLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
import pytesseract
from PIL import Image
import asyncio

async def ingest_print_async(user_id: str, machine_name: str, file_path: str):
    """Chunk, embed, and store print in vector DB."""
    
    # 1. Extract text (PDF or image)
    if file_path.endswith(".pdf"):
        loader = PDFPlumberLoader(file_path)
        docs = loader.load()
        text = "\n".join([d.page_content for d in docs])
    else:
        # OCR for photos
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
        docs = [{"page_content": text, "metadata": {"source": file_path}}]
    
    # 2. Chunk with spatial awareness
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=100,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = splitter.split_documents(docs)
    
    # 3. Embed and store
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    collection_name = f"{user_id}_{machine_name}"
    vector_db = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory="./chroma_db"
    )
    
    vector_db.add_documents(chunks)
    
    # 4. Store metadata in PostgreSQL
    db = get_db_session()
    print_record = PrintMetadata(
        user_id=user_id,
        machine_id=machine_name,
        file_path=file_path,
        description="",
        upload_date=datetime.now()
    )
    db.add(print_record)
    db.commit()
    
    print(f"✅ Ingested print for {user_id}/{machine_name}")
```

### 3. Query Handler with Claude

```python
from langchain.chat_models import ChatAnthropic
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

async def query_prints(user_id: str, machine_name: str, question: str):
    """Retrieve print chunks and answer via Claude."""
    
    collection_name = f"{user_id}_{machine_name}"
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    vector_db = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory="./chroma_db"
    )
    
    retriever = vector_db.as_retriever(search_kwargs={"k": 3})
    
    # Claude model
    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")
    
    # Prompt tailored for electrical diagnostics
    prompt_template = """You are an expert electrical maintenance technician.
    
Using the electrical print information below, answer the technician's question.
Include safety warnings if relevant (e.g., "De-energize before testing").
Cite which print/section you're referencing.

Print Context:
{context}

Question: {question}

Answer:"""
    
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    
    # Build RAG chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )
    
    result = qa_chain({"query": question})
    
    return {
        "answer": result["result"],
        "sources": [doc.metadata.get("source", "Unknown") for doc in result.get("source_documents", [])]
    }
```

### 4. Telegram Response with Streaming

```python
async def chat_print_command(update: Update, context):
    """Chat with prints for a specific machine."""
    user_id = update.effective_user.id
    machine_name = " ".join(context.args) if context.args else None
    
    if not machine_name:
        await update.message.reply_text("Usage: /chat_print <machine_name>")
        return
    
    context.user_data["chat_machine"] = machine_name
    await update.message.reply_text(f"🔍 Querying {machine_name}'s prints. Ask your question:")

async def handle_query(update: Update, context):
    """Handle user question about prints."""
    user_id = update.effective_user.id
    machine_name = context.user_data.get("chat_machine")
    question = update.message.text
    
    if not machine_name:
        await update.message.reply_text("Select a machine first: /chat_print <machine_name>")
        return
    
    # Show typing indicator
    await update.message.chat.send_action("typing")
    
    # Query prints
    result = await query_prints(user_id, machine_name, question)
    
    # Format response with sources
    response = result["answer"]
    if result["sources"]:
        response += f"\n\n📄 Source: {', '.join(set(result['sources']))}"
    
    # Send response (split if >4096 chars for Telegram limit)
    for chunk in [response[i:i+4096] for i in range(0, len(response), 4096)]:
        await update.message.reply_text(chunk)

# Register query handler
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_query))
```

---

## Database Schema (PostgreSQL)

```sql
CREATE TABLE users (
    user_id VARCHAR(255) PRIMARY KEY,
    telegram_id BIGINT UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE machines (
    machine_id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(user_id),
    machine_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, machine_name)
);

CREATE TABLE print_metadata (
    print_id SERIAL PRIMARY KEY,
    machine_id INTEGER REFERENCES machines(machine_id),
    user_id VARCHAR(255) REFERENCES users(user_id),
    file_path VARCHAR(512),
    description TEXT,
    print_type VARCHAR(100), -- "wiring", "hydraulic", "control", etc.
    uploaded_at TIMESTAMP DEFAULT NOW(),
    vectorized_at TIMESTAMP
);

CREATE TABLE chat_history (
    chat_id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(user_id),
    machine_id INTEGER REFERENCES machines(machine_id),
    question TEXT,
    answer TEXT,
    sources TEXT[], -- array of print IDs cited
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Deployment Checklist

- [ ] Clone and adapt: https://github.com/alejandro-ao/ask-multiple-pdfs (ingestion pipeline)
- [ ] Clone and adapt: https://github.com/python-telegram-bot/python-telegram-bot (Telegram integration)
- [ ] Set up PostgreSQL database with schema above
- [ ] Set up ChromaDB persistence (`./chroma_db` directory)
- [ ] Configure Telegram webhook: `POST https://your-vps.com/webhook`
- [ ] Docker image: `python:3.11 + fastapi + chromadb + langchain`
- [ ] Environment variables: `TELEGRAM_BOT_TOKEN`, `ANTHROPIC_API_KEY`, `DATABASE_URL`
- [ ] Deploy to your VPS (docker-compose or systemd)

---

## Claude CLI Invocation

```bash
claude-code \
  --file electrical-prints-spec.md \
  --context "ask-multiple-pdfs:https://github.com/alejandro-ao/ask-multiple-pdfs" \
  --context "telegram-bot:https://github.com/python-telegram-bot/python-telegram-bot" \
  --context "claude-skills:https://github.com/ComposioHQ/awesome-claude-skills" \
  --context "chroma:https://github.com/chroma-core/chroma" \
  --output "SPRINT_BACKLOG_ELECTRICAL.md"
```

This now reflects **industrial maintenance + electrical diagrams + Telegram query bot** properly. Ready? 🔧