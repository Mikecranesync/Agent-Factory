# TAB 2: PRINT QUERY INTERFACE
# Copy everything below into Claude Code CLI

You are Tab 2 (Query) in a 2-tab sprint to build the Electrical Prints feature for Rivet.

## AUTONOMOUS MODE SETTINGS
- Auto-accept all file edits
- Auto-accept bash commands except: rm -rf, sudo, DROP, DELETE
- Commit after each completed task
- If context reaches 80%, checkpoint and summarize

## YOUR IDENTITY
- Workstream: Prints Query
- Branch: prints-query
- Focus: RAG retrieval, Claude Q&A, Telegram commands, citations

## FIRST ACTIONS
```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
git checkout -b prints-query
git push -u origin prints-query
```

## EXISTING CODE TO BUILD ON
```
agent_factory/rivet_pro/
├── print_analyzer.py         # Extend for RAG
└── database.py               # Tab 1 adds print methods

agent_factory/integrations/telegram/
├── bot.py                    # Add query handlers
├── session_manager.py        # Multi-turn context
└── conversation_manager.py   # Reuse patterns
```

## DEPENDENCIES ON TAB 1
- Tab 1 creates: `agent_factory/prints/ingestion/vectorizer.py` (ChromaDB)
- Tab 1 creates: Database methods for prints/machines
- You can mock these initially, then integrate

---

## YOUR TASKS

### Phase 1: RAG Retriever (Day 1)

**Task 1.1: Create Query Module**
```bash
mkdir -p agent_factory/prints/query
touch agent_factory/prints/query/__init__.py
```

**Task 1.2: Print Retriever**
Create `agent_factory/prints/query/retriever.py`:
```python
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
import os

class PrintRetriever:
    """Retrieve relevant print chunks using vector similarity."""
    
    def __init__(self, persist_dir: str = None):
        self.persist_dir = persist_dir or os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        
        self.embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    
    def retrieve(
        self,
        user_id: str,
        machine_id: str,
        query: str,
        top_k: int = 5,
        filter_print_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Retrieve most relevant chunks for a query.
        
        Returns:
            [
                {
                    "text": "chunk content...",
                    "print_name": "Main Panel Wiring",
                    "page_num": 2,
                    "section": "Motor Control",
                    "score": 0.85
                },
                ...
            ]
        """
        collection_name = f"user_{user_id}_machine_{machine_id}"
        
        try:
            collection = self.client.get_collection(collection_name)
        except Exception:
            return []  # No vectors yet
        
        # Embed query
        query_embedding = self.embedder.encode(query).tolist()
        
        # Build where filter
        where_filter = None
        if filter_print_id:
            where_filter = {"print_id": filter_print_id}
        
        # Query
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        chunks = []
        for i, doc in enumerate(results["documents"][0]):
            metadata = results["metadatas"][0][i]
            distance = results["distances"][0][i]
            
            # Convert distance to similarity score (0-1)
            score = 1 / (1 + distance)
            
            chunks.append({
                "text": doc,
                "print_name": metadata.get("print_name", "Unknown"),
                "print_id": metadata.get("print_id"),
                "page_num": metadata.get("page_num", 1),
                "section": metadata.get("section", "General"),
                "chunk_index": metadata.get("chunk_index", 0),
                "score": round(score, 3)
            })
        
        return chunks
    
    def get_collection_stats(self, user_id: str, machine_id: str) -> Dict:
        """Get stats about stored vectors."""
        collection_name = f"user_{user_id}_machine_{machine_id}"
        
        try:
            collection = self.client.get_collection(collection_name)
            return {
                "exists": True,
                "count": collection.count(),
                "name": collection_name
            }
        except Exception:
            return {"exists": False, "count": 0, "name": collection_name}
```

---

### Phase 2: RAG Chain with Claude (Day 1-2)

**Task 2.1: RAG Chain**
Create `agent_factory/prints/query/rag_chain.py`:
```python
import anthropic
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class PrintRAGChain:
    """
    RAG chain for answering questions about electrical prints.
    Uses Claude with retrieved context.
    """
    
    SYSTEM_PROMPT = """You are an expert electrical maintenance technician assistant.

Your job is to answer questions about electrical schematics, wiring diagrams, and prints.

IMPORTANT GUIDELINES:
1. Only answer based on the provided print context - don't make up information
2. Always cite which print/page your answer comes from
3. Include SAFETY WARNINGS when relevant (lockout/tagout, voltage hazards, etc.)
4. If the answer isn't in the provided context, say so clearly
5. Be specific about wire colors, gauges, terminal numbers when available
6. Suggest diagnostic steps when troubleshooting

Format your response clearly with:
- Direct answer to the question
- Source citation (Print name, Page #)
- Safety notes if applicable"""

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.model = "claude-sonnet-4-20250514"
    
    async def query(
        self,
        question: str,
        context_chunks: List[Dict],
        chat_history: List[Dict] = None,
        machine_name: str = None
    ) -> Dict:
        """
        Answer a question using retrieved print context.
        
        Returns:
            {
                "answer": "The wire gauge is 12 AWG...",
                "sources": [
                    {"print_name": "Panel A Wiring", "page": 2}
                ],
                "tokens_used": 450
            }
        """
        if not context_chunks:
            return {
                "answer": f"I don't have any prints loaded for this machine. Use `/upload_print {machine_name or '<machine>'}` to add prints first.",
                "sources": [],
                "tokens_used": 0
            }
        
        # Build context string
        context_str = self._build_context(context_chunks)
        
        # Build messages
        messages = []
        
        # Add chat history for multi-turn
        if chat_history:
            for h in chat_history[-4:]:  # Last 4 turns
                messages.append({"role": "user", "content": h["question"]})
                messages.append({"role": "assistant", "content": h["answer"]})
        
        # Current question with context
        user_message = f"""Based on the following electrical print information:

{context_str}

Question: {question}"""
        
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                system=self.SYSTEM_PROMPT,
                messages=messages
            )
            
            answer = response.content[0].text
            tokens = response.usage.input_tokens + response.usage.output_tokens
            
            # Extract unique sources
            sources = self._extract_sources(context_chunks)
            
            return {
                "answer": answer,
                "sources": sources,
                "tokens_used": tokens
            }
            
        except Exception as e:
            logger.error(f"RAG chain error: {e}")
            return {
                "answer": f"Sorry, I encountered an error processing your question. Please try again.",
                "sources": [],
                "tokens_used": 0,
                "error": str(e)
            }
    
    def _build_context(self, chunks: List[Dict]) -> str:
        """Build context string from chunks."""
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            source = f"[{chunk['print_name']}, Page {chunk['page_num']}, {chunk['section']}]"
            context_parts.append(f"--- Source {i}: {source} ---\n{chunk['text']}\n")
        
        return "\n".join(context_parts)
    
    def _extract_sources(self, chunks: List[Dict]) -> List[Dict]:
        """Extract unique source citations."""
        seen = set()
        sources = []
        
        for chunk in chunks:
            key = (chunk["print_name"], chunk["page_num"])
            if key not in seen:
                seen.add(key)
                sources.append({
                    "print_name": chunk["print_name"],
                    "page": chunk["page_num"],
                    "print_id": chunk.get("print_id")
                })
        
        return sources
```

**Task 2.2: Citation Builder**
Create `agent_factory/prints/query/citation_builder.py`:
```python
from typing import List, Dict

class CitationBuilder:
    """Build formatted citations for print sources."""
    
    @staticmethod
    def format_inline(sources: List[Dict]) -> str:
        """Format sources for inline citation."""
        if not sources:
            return ""
        
        citations = []
        for s in sources:
            citations.append(f"{s['print_name']} (p.{s['page']})")
        
        return f"📄 Sources: {', '.join(citations)}"
    
    @staticmethod
    def format_detailed(sources: List[Dict]) -> str:
        """Format detailed source list."""
        if not sources:
            return ""
        
        lines = ["📚 **References:**"]
        for i, s in enumerate(sources, 1):
            lines.append(f"  {i}. {s['print_name']}, Page {s['page']}")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_for_telegram(answer: str, sources: List[Dict]) -> str:
        """Format complete response for Telegram."""
        response = answer
        
        if sources:
            response += f"\n\n{CitationBuilder.format_inline(sources)}"
        
        return response
```

---

### Phase 3: Telegram Query Handlers (Day 2)

**Task 3.1: Query Handlers**
Add to `agent_factory/prints/telegram_handlers.py` (query part):
```python
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

from agent_factory.prints.query.retriever import PrintRetriever
from agent_factory.prints.query.rag_chain import PrintRAGChain
from agent_factory.prints.query.citation_builder import CitationBuilder
from agent_factory.rivet_pro.database import RIVETProDatabase

retriever = PrintRetriever()
rag_chain = PrintRAGChain()
db = RIVETProDatabase()

async def chat_print_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /chat_print <machine> command - start Q&A session."""
    user_id = str(update.effective_user.id)
    args = context.args
    
    if not args:
        # Show available machines
        machines = await db.get_machines_by_user(user_id)
        if machines:
            machine_list = "\n".join([f"• {m['name']}" for m in machines])
            await update.message.reply_text(
                f"🔍 **Chat with Prints**\n\n"
                f"Usage: `/chat_print <machine_name>`\n\n"
                f"Your machines:\n{machine_list}"
            )
        else:
            await update.message.reply_text(
                "No machines found. Upload a print first:\n"
                "`/upload_print <machine_name>`"
            )
        return
    
    machine_name = " ".join(args)
    
    # Verify machine exists
    machine = await db.get_machine_by_name(user_id, machine_name)
    if not machine:
        await update.message.reply_text(
            f"❌ Machine '{machine_name}' not found.\n\n"
            "Use `/list_machines` to see your machines."
        )
        return
    
    # Check if prints exist
    prints = await db.get_prints_by_machine(machine["id"])
    if not prints:
        await update.message.reply_text(
            f"📋 No prints uploaded for **{machine_name}** yet.\n\n"
            f"Upload one with: `/upload_print {machine_name}`"
        )
        return
    
    # Set session context
    context.user_data["print_chat_session"] = {
        "machine_id": machine["id"],
        "machine_name": machine_name,
        "user_id": user_id
    }
    
    # Clear old chat history for fresh session
    context.user_data["print_chat_history"] = []
    
    await update.message.reply_text(
        f"🔍 **Chat with {machine_name} Prints**\n\n"
        f"📄 {len(prints)} print(s) loaded\n\n"
        "Ask me anything about the wiring, components, or troubleshooting!\n\n"
        "Examples:\n"
        "• 'What's the wire gauge for the main feeder?'\n"
        "• 'Show me the motor control circuit'\n"
        "• 'What fuse protects the VFD?'\n\n"
        "Type `/end_chat` when done."
    )

async def handle_print_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle questions during a print chat session."""
    session = context.user_data.get("print_chat_session")
    
    if not session:
        return  # Not in a chat session
    
    question = update.message.text
    user_id = session["user_id"]
    machine_id = session["machine_id"]
    machine_name = session["machine_name"]
    
    # Show typing indicator
    await update.message.chat.send_action("typing")
    
    # Retrieve relevant chunks
    chunks = retriever.retrieve(
        user_id=user_id,
        machine_id=machine_id,
        query=question,
        top_k=5
    )
    
    # Get chat history
    chat_history = context.user_data.get("print_chat_history", [])
    
    # Query RAG chain
    result = await rag_chain.query(
        question=question,
        context_chunks=chunks,
        chat_history=chat_history,
        machine_name=machine_name
    )
    
    # Format response with citations
    response = CitationBuilder.format_for_telegram(
        result["answer"],
        result["sources"]
    )
    
    # Save to chat history
    chat_history.append({
        "question": question,
        "answer": result["answer"]
    })
    context.user_data["print_chat_history"] = chat_history
    
    # Save to database
    await db.save_chat_history(
        user_id=user_id,
        machine_id=machine_id,
        question=question,
        answer=result["answer"],
        sources=[s["print_id"] for s in result["sources"] if s.get("print_id")]
    )
    
    # Send response (split if too long)
    if len(response) > 4096:
        for i in range(0, len(response), 4096):
            await update.message.reply_text(response[i:i+4096])
    else:
        await update.message.reply_text(response)

async def end_chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /end_chat command."""
    session = context.user_data.get("print_chat_session")
    
    if session:
        machine_name = session["machine_name"]
        history_len = len(context.user_data.get("print_chat_history", []))
        
        del context.user_data["print_chat_session"]
        context.user_data["print_chat_history"] = []
        
        await update.message.reply_text(
            f"✅ Ended chat with **{machine_name}**\n\n"
            f"Asked {history_len} question(s) this session.\n\n"
            "Start a new session with `/chat_print <machine>`"
        )
    else:
        await update.message.reply_text("No active chat session.")

async def add_machine_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /add_machine <name> command."""
    user_id = str(update.effective_user.id)
    args = context.args
    
    if not args:
        await update.message.reply_text("Usage: `/add_machine <machine_name>`")
        return
    
    machine_name = " ".join(args)
    
    # Check if exists
    existing = await db.get_machine_by_name(user_id, machine_name)
    if existing:
        await update.message.reply_text(f"Machine '{machine_name}' already exists.")
        return
    
    # Create
    machine = await db.create_machine(user_id, machine_name)
    
    await update.message.reply_text(
        f"✅ Created machine: **{machine_name}**\n\n"
        f"Now upload prints with: `/upload_print {machine_name}`"
    )

# Register all query handlers
def register_query_handlers(application):
    """Register query-related handlers."""
    application.add_handler(CommandHandler("chat_print", chat_print_command))
    application.add_handler(CommandHandler("end_chat", end_chat_command))
    application.add_handler(CommandHandler("add_machine", add_machine_command))
    
    # Text handler for questions (only when in chat session)
    # This should be registered with lower priority than commands
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_print_question
        ),
        group=1  # Lower priority than upload handlers
    )
```

---

### Phase 4: Multi-Turn Context & Polish (Day 3)

**Task 4.1: Session Manager Updates**
Update session handling to support print chat sessions properly.

**Task 4.2: Help Command**
Add print-specific help:
```python
async def print_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /print_help command."""
    await update.message.reply_text(
        "📋 **Electrical Print Commands**\n\n"
        "**Upload & Manage:**\n"
        "• `/add_machine <name>` - Create a machine\n"
        "• `/upload_print <machine>` - Upload a print\n"
        "• `/list_machines` - View your machines\n"
        "• `/list_prints <machine>` - View prints for a machine\n\n"
        "**Query Prints:**\n"
        "• `/chat_print <machine>` - Start Q&A session\n"
        "• `/end_chat` - End current session\n\n"
        "**Tips:**\n"
        "• Upload PDFs or photos of wiring diagrams\n"
        "• Ask specific questions: 'What fuse protects motor M1?'\n"
        "• Ask troubleshooting: 'Motor won't start, what should I check?'\n"
        "• I'll always cite which print/page I'm referencing"
    )
```

**Task 4.3: Safety Wrapper**
Create `agent_factory/prints/query/safety.py`:
```python
SAFETY_KEYWORDS = {
    "voltage": "⚠️ SAFETY: Verify equipment is de-energized before testing.",
    "live": "⚠️ SAFETY: Use appropriate PPE for live work.",
    "arc flash": "⚠️ SAFETY: Follow arc flash safety procedures.",
    "480v": "⚠️ SAFETY: 480V circuits require qualified personnel only.",
    "lockout": "⚠️ SAFETY: Follow LOTO procedures before servicing.",
    "breaker": "⚠️ SAFETY: Verify breaker is locked out before work.",
}

def add_safety_warnings(answer: str, question: str) -> str:
    """Add safety warnings based on question content."""
    question_lower = question.lower()
    answer_lower = answer.lower()
    
    warnings = set()
    
    for keyword, warning in SAFETY_KEYWORDS.items():
        if keyword in question_lower or keyword in answer_lower:
            warnings.add(warning)
    
    if warnings:
        return answer + "\n\n" + "\n".join(warnings)
    
    return answer
```

---

### Phase 5: Integration & Testing (Day 4)

**Task 5.1: Register All Handlers in Bot**
Update `agent_factory/integrations/telegram/bot.py`:
```python
# Add imports
from agent_factory.prints.telegram_handlers import (
    register_print_handlers,
    register_query_handlers
)

# In setup function, add:
register_print_handlers(application)
register_query_handlers(application)
```

**Task 5.2: E2E Tests**
Create `tests/test_prints_e2e.py`:
```python
import pytest
from pathlib import Path

@pytest.mark.asyncio
async def test_upload_flow():
    """Test complete upload → vectorize flow."""
    # 1. Create machine
    # 2. Upload PDF
    # 3. Verify vectorized
    # 4. Check chunk count
    pass

@pytest.mark.asyncio
async def test_query_flow():
    """Test complete query → answer flow."""
    # 1. Set up machine with prints
    # 2. Start chat session
    # 3. Ask question
    # 4. Verify answer has sources
    # 5. Verify multi-turn context
    pass

@pytest.mark.asyncio
async def test_safety_warnings():
    """Test safety warnings are added."""
    # 1. Ask about voltage
    # 2. Verify safety warning in response
    pass
```

---

## COMMIT PROTOCOL
After EACH task:
```bash
git add -A
git commit -m "prints-query: [component] description"
git push origin prints-query
```

## SUCCESS CRITERIA
- [ ] PrintRetriever finds relevant chunks
- [ ] RAG chain returns accurate answers
- [ ] `/chat_print <machine>` starts Q&A session
- [ ] Answers include source citations
- [ ] Multi-turn context works (follow-up questions)
- [ ] Safety warnings appear for hazardous topics
- [ ] `/end_chat` clears session
- [ ] `/print_help` shows all commands

## DEPENDENCIES ON TAB 1
- ChromaDB collections must exist (Tab 1 vectorizer)
- Database methods for prints/machines (Tab 1)
- If Tab 1 not ready, mock with hardcoded test data

## UPDATE STATUS
After each phase, create: `/sprint/STATUS_PRINTS_TAB2.md`

## START NOW
Begin with Task 1.1 - Create the query module structure.
