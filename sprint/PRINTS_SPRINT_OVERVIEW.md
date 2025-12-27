# ELECTRICAL PRINTS FEATURE - 2 TAB SPRINT

## Overview

Build the Electrical Print Ingestion & Query system from `electrical-prints-spec.md`

| Tab | Branch | Focus |
|-----|--------|-------|
| **Tab 1** | `prints-ingestion` | Upload, OCR, chunking, vectorization, database |
| **Tab 2** | `prints-query` | Telegram commands, RAG chain, Claude Q&A, citations |

---

## Integration with Existing Rivet System

### Reuse These Components
```
agent_factory/integrations/telegram/
├── bot.py                    # Add new command handlers
├── session_manager.py        # Extend for machine context
├── ocr/
│   ├── pipeline.py           # Add PDF extraction step
│   ├── gemini_provider.py    # Reuse for image OCR
│   └── claude_provider.py    # Reuse for schematic analysis

agent_factory/rivet_pro/
├── database.py               # Add prints/machines tables
└── print_analyzer.py         # Already created - extend it
```

### New Components to Build
```
agent_factory/prints/
├── __init__.py
├── ingestion/
│   ├── __init__.py
│   ├── pdf_extractor.py      # PDF → text/images
│   ├── chunker.py            # Electrical-aware chunking
│   └── vectorizer.py         # Embed + store in ChromaDB
├── query/
│   ├── __init__.py
│   ├── retriever.py          # Vector similarity search
│   ├── rag_chain.py          # Claude + context
│   └── citation_builder.py   # Source attribution
├── models.py                 # Machine, Print, ChatHistory
└── telegram_handlers.py      # /upload_print, /chat_print, etc.
```

---

## Database Schema (Add to Neon)

```sql
-- Machines table
CREATE TABLE machines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES rivet_users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, name)
);

-- Prints metadata
CREATE TABLE prints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    machine_id UUID REFERENCES machines(id) ON DELETE CASCADE,
    user_id UUID REFERENCES rivet_users(id),
    name VARCHAR(255) NOT NULL,
    file_path VARCHAR(512),
    print_type VARCHAR(100), -- 'wiring', 'hydraulic', 'control', 'p&id'
    description TEXT,
    page_count INTEGER,
    vectorized BOOLEAN DEFAULT FALSE,
    collection_name VARCHAR(255), -- ChromaDB collection
    uploaded_at TIMESTAMP DEFAULT NOW(),
    vectorized_at TIMESTAMP
);

-- Chat history for print queries
CREATE TABLE print_chat_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES rivet_users(id),
    machine_id UUID REFERENCES machines(id),
    question TEXT,
    answer TEXT,
    sources TEXT[], -- Array of print IDs cited
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_machines_user ON machines(user_id);
CREATE INDEX idx_prints_machine ON prints(machine_id);
CREATE INDEX idx_prints_user ON prints(user_id);
CREATE INDEX idx_chat_history_user ON print_chat_history(user_id);
```

---

## Timeline

| Day | Tab 1 (Ingestion) | Tab 2 (Query) |
|-----|-------------------|---------------|
| **1** | PDF extractor + DB schema | Telegram commands scaffold |
| **2** | Chunker + vectorizer | RAG chain + retriever |
| **3** | File storage + integration | Citations + multi-turn |
| **4** | Testing + polish | E2E testing |

---

## Success Criteria

- [ ] `/upload_print <machine>` accepts PDF/photo
- [ ] Print is OCR'd, chunked, and vectorized
- [ ] `/chat_print <machine>` enables Q&A mode
- [ ] Questions return accurate answers with citations
- [ ] `/list_machines` and `/list_prints` work
- [ ] Multi-turn context maintained per session
- [ ] Safety warnings included in electrical responses

---

## Dependencies

```bash
# New packages needed
pip install chromadb pdfplumber pdf2image pytesseract sentence-transformers
```

---

## Environment Variables

```bash
# Already have
ANTHROPIC_API_KEY=xxx
OPENAI_API_KEY=xxx
TELEGRAM_BOT_TOKEN=xxx
NEON_DB_URL=xxx

# New (optional)
CHROMA_PERSIST_DIR=/data/chroma_db
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

---

## Start Commands

**Tab 1:**
```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
git checkout -b prints-ingestion
claude
# Paste sprint/PRINTS_TAB1_INGESTION.md
```

**Tab 2:**
```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
git checkout -b prints-query
claude
# Paste sprint/PRINTS_TAB2_QUERY.md
```

---

## Merge Strategy

After Day 4:
```bash
git checkout main
git merge prints-ingestion
git merge prints-query
git push origin main
```
