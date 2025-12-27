# TAB 2: RESPONSE SYNTHESIS + TELEGRAM INTEGRATION
# Copy everything below into Claude Code CLI

You are Tab 2 in a 2-tab sprint to build Intelligent Context Capture & Manual Retrieval.

## AUTONOMOUS MODE SETTINGS
- Auto-accept all file edits
- Auto-accept bash commands except: rm -rf, sudo, DROP, DELETE
- Commit after each completed task

## YOUR IDENTITY
- Workstream: Response + Integration
- Branch: context-response
- Focus: Synthesize responses with manual content, integrate into Telegram bot

## FIRST ACTIONS
```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
git checkout -b context-response
git push -u origin context-response
```

## DEPENDENCIES ON TAB 1
Tab 1 creates:
- `agent_factory/intake/models.py` - EquipmentContext, ManualReference
- `agent_factory/intake/context_extractor.py` - ContextExtractor class
- `agent_factory/knowledge/manual_search.py` - ManualSearch class

You can mock these initially if Tab 1 isn't ready.

---

## PHASE 1: Response Synthesizer (Day 1-2)

### Task 1.1: Response Synthesizer
Create `agent_factory/intake/response_synthesizer.py`:
```python
"""Synthesize intelligent responses with manual content."""
import anthropic
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

# Import from Tab 1 (or mock if not ready)
try:
    from .models import EquipmentContext, ManualReference
except ImportError:
    # Mock classes if Tab 1 not ready
    from dataclasses import dataclass
    @dataclass
    class EquipmentContext:
        component_name: str = ""
        manufacturer: str = ""
        fault_code: str = ""
    @dataclass
    class ManualReference:
        title: str = ""
        snippet: str = ""
        page_numbers: str = ""


class ResponseSynthesizer:
    """
    Synthesize responses that combine:
    - Direct answers from manuals
    - Troubleshooting steps
    - Safety warnings
    - Source citations
    """
    
    SYSTEM_PROMPT = '''You are an expert industrial maintenance assistant helping field technicians.

Your job is to provide helpful, accurate, and SAFE guidance based on equipment manuals and documentation.

CRITICAL RULES:
1. ALWAYS include safety warnings for electrical, hydraulic, or pneumatic work
2. Cite your sources with page numbers when available
3. If you don't have enough information, say so clearly
4. Prioritize de-energization and lockout/tagout procedures
5. Be specific about wire colors, terminal numbers, and component locations
6. Suggest diagnostic steps in logical order (easiest/safest first)

Response Format:
- Start with a direct answer to their question
- Include relevant manual excerpts
- Add troubleshooting steps if applicable
- End with safety warnings
- Cite sources'''

    RESPONSE_TEMPLATE = '''Based on the technician's question about {component}:

**Equipment Context:**
- Component: {component_name}
- Manufacturer: {manufacturer}
- Issue: {issue_type}
{fault_code_line}

**From Documentation:**
{manual_content}

**Troubleshooting Steps:**
{troubleshooting_steps}

{safety_warnings}

📄 **Sources:** {sources}'''

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.model = "claude-sonnet-4-20250514"
    
    async def synthesize(
        self,
        context: EquipmentContext,
        manual_results: List[ManualReference],
        user_query: str
    ) -> dict:
        """
        Synthesize a response combining context and manual content.
        
        Returns:
            {
                "response": "formatted response text",
                "sources": [...],
                "has_manual_content": bool,
                "safety_warnings": [...]
            }
        """
        # Build manual content section
        manual_content = self._format_manual_content(manual_results)
        has_manual = len(manual_results) > 0
        
        # Generate response with Claude
        response = await self._generate_response(
            context=context,
            manual_content=manual_content,
            user_query=user_query,
            has_manual=has_manual
        )
        
        # Extract safety warnings
        safety_warnings = self._extract_safety_warnings(context)
        
        # Format sources
        sources = self._format_sources(manual_results)
        
        return {
            "response": response,
            "sources": sources,
            "has_manual_content": has_manual,
            "safety_warnings": safety_warnings
        }
    
    def _format_manual_content(self, results: List[ManualReference]) -> str:
        """Format manual search results into readable content."""
        if not results:
            return "No specific manual content found for this equipment."
        
        sections = []
        for i, ref in enumerate(results[:3], 1):
            section = f"**[{ref.title}** (p.{ref.page_numbers})]:\n{ref.snippet}"
            sections.append(section)
        
        return "\n\n".join(sections)
    
    async def _generate_response(
        self,
        context: EquipmentContext,
        manual_content: str,
        user_query: str,
        has_manual: bool
    ) -> str:
        """Generate response using Claude."""
        
        # Build prompt
        prompt = f"""Technician's question: "{user_query}"

Equipment identified:
- Component: {context.component_name or 'Unknown'}
- Manufacturer: {context.manufacturer or 'Unknown'}
- Component Family: {getattr(context, 'component_family', 'Unknown')}
- Fault Code: {context.fault_code or 'None specified'}

Manual content found:
{manual_content}

Provide a helpful response following these guidelines:
1. Answer their specific question first
2. Include relevant troubleshooting steps
3. Add safety warnings appropriate for this equipment
4. Cite the manual sources
5. If manual content is limited, provide general guidance but note limitations"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                system=self.SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude response failed: {e}")
            return self._fallback_response(context, manual_content)
    
    def _fallback_response(self, context: EquipmentContext, manual_content: str) -> str:
        """Generate fallback response if Claude fails."""
        return f"""🔧 **{context.component_name or 'Equipment'} Issue**

{manual_content}

⚠️ **Safety Reminder:** Always follow lockout/tagout procedures before servicing.

I found limited information. Try uploading the equipment manual with `/upload_manual` for better assistance."""
    
    def _extract_safety_warnings(self, context: EquipmentContext) -> List[str]:
        """Extract appropriate safety warnings based on context."""
        warnings = []
        
        component_family = getattr(context, 'component_family', '').lower()
        
        # Electrical warnings
        if any(kw in component_family for kw in ['vfd', 'drive', 'plc', 'motor', 'panel', 'electrical']):
            warnings.append("⚠️ ELECTRICAL HAZARD: De-energize and verify zero energy before servicing")
            warnings.append("⚠️ VFDs can retain dangerous voltage in DC bus capacitors - wait 5+ minutes after power off")
        
        # High voltage
        if context.fault_code and any(kw in str(context.fault_code).lower() for kw in ['over', 'under', 'volt']):
            warnings.append("⚠️ Check incoming power with rated meter before troubleshooting")
        
        # Generic safety
        if not warnings:
            warnings.append("⚠️ Follow facility lockout/tagout procedures before servicing")
        
        return warnings
    
    def _format_sources(self, results: List[ManualReference]) -> List[dict]:
        """Format source citations."""
        return [
            {
                "title": r.title,
                "page": r.page_numbers,
                "manufacturer": r.manufacturer
            }
            for r in results[:3]
        ]


class TelegramResponseFormatter:
    """Format responses for Telegram display."""
    
    MAX_MESSAGE_LENGTH = 4096
    
    @staticmethod
    def format(synthesis_result: dict) -> str:
        """Format synthesis result for Telegram."""
        response = synthesis_result["response"]
        sources = synthesis_result["sources"]
        warnings = synthesis_result.get("safety_warnings", [])
        
        # Add source citations if not in response
        if sources and "Sources:" not in response:
            source_text = "\n\n📄 **Sources:**\n"
            for s in sources:
                source_text += f"• {s['title']} (p.{s['page']})\n"
            response += source_text
        
        # Add safety warnings if not prominent
        if warnings and "⚠️" not in response[:500]:
            response += "\n\n" + "\n".join(warnings)
        
        # Truncate if needed
        if len(response) > TelegramResponseFormatter.MAX_MESSAGE_LENGTH:
            response = response[:TelegramResponseFormatter.MAX_MESSAGE_LENGTH - 100]
            response += "\n\n... (truncated - ask for specific details)"
        
        return response
    
    @staticmethod
    def format_no_results(context) -> str:
        """Format response when no manuals found."""
        component = getattr(context, 'component_name', '') or getattr(context, 'component_family', 'this equipment')
        manufacturer = getattr(context, 'manufacturer', '')
        
        return f"""🔍 I identified **{component}**{f' ({manufacturer})' if manufacturer else ''} but don't have specific manuals for it yet.

**What you can do:**
1. Upload the manual: `/upload_manual`
2. Ask a general question and I'll help with my training knowledge
3. Check manufacturer website for documentation

**General guidance:**
• Always follow lockout/tagout before servicing
• Document the fault code and symptoms
• Check obvious things first (power, connections, fuses)

Would you like general troubleshooting help?"""
```

---

## PHASE 2: Intake Handler Integration (Day 2-3)

### Task 2.1: Create Integrated Intake Handler
Create `agent_factory/intake/telegram_intake.py`:
```python
"""Intelligent intake handler for Telegram messages."""
import logging
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# Import from Tab 1
try:
    from .context_extractor import ContextExtractor
    from .models import EquipmentContext
except ImportError:
    ContextExtractor = None
    EquipmentContext = None

try:
    from agent_factory.knowledge.manual_search import ManualSearch
except ImportError:
    ManualSearch = None

from .response_synthesizer import ResponseSynthesizer, TelegramResponseFormatter


class IntelligentIntakeHandler:
    """
    Handles every incoming message with intelligent context extraction.
    
    Flow:
    1. Extract equipment context from message
    2. Search for relevant manuals
    3. Synthesize response with manual content
    4. Return enriched response
    """
    
    def __init__(self):
        self.extractor = ContextExtractor() if ContextExtractor else None
        self.manual_search = ManualSearch() if ManualSearch else None
        self.synthesizer = ResponseSynthesizer()
        self.formatter = TelegramResponseFormatter()
    
    async def process_message(
        self,
        message: str,
        user_id: str,
        telegram_id: int
    ) -> dict:
        """
        Process incoming message with full context extraction.
        
        Returns:
            {
                "response": str,
                "context": EquipmentContext,
                "manual_results": [...],
                "needs_clarification": bool,
                "clarification_prompt": str
            }
        """
        # 1. Extract context
        if self.extractor:
            context = await self.extractor.extract(message)
        else:
            # Fallback mock context
            context = self._mock_context(message)
        
        logger.info(f"Extracted context: {context.component_name}, {context.manufacturer}, {context.fault_code}")
        
        # 2. Check if clarification needed
        if context.needs_clarification and context.clarification_prompt:
            return {
                "response": context.clarification_prompt,
                "context": context,
                "manual_results": [],
                "needs_clarification": True,
                "clarification_prompt": context.clarification_prompt
            }
        
        # 3. Search manuals
        manual_results = []
        if self.manual_search and context.confidence > 0.3:
            manual_results = await self.manual_search.search(context)
        
        logger.info(f"Found {len(manual_results)} manual results")
        
        # 4. Synthesize response
        synthesis = await self.synthesizer.synthesize(
            context=context,
            manual_results=manual_results,
            user_query=message
        )
        
        # 5. Format for Telegram
        if manual_results:
            formatted_response = self.formatter.format(synthesis)
        else:
            formatted_response = self.formatter.format_no_results(context)
        
        return {
            "response": formatted_response,
            "context": context,
            "manual_results": manual_results,
            "needs_clarification": False,
            "clarification_prompt": None
        }
    
    def _mock_context(self, message: str):
        """Create mock context for testing without Tab 1."""
        from dataclasses import dataclass
        
        @dataclass
        class MockContext:
            raw_message: str = ""
            component_name: str = ""
            component_family: str = ""
            manufacturer: str = ""
            fault_code: str = ""
            confidence: float = 0.5
            needs_clarification: bool = False
            clarification_prompt: str = ""
            manual_search_queries: list = None
            
            def __post_init__(self):
                self.manual_search_queries = self.manual_search_queries or []
        
        # Basic keyword extraction
        message_lower = message.lower()
        
        component = ""
        manufacturer = ""
        fault_code = ""
        
        # Detect VFD
        if any(kw in message_lower for kw in ["vfd", "drive", "powerflex", "sinamics"]):
            component = "VFD"
            if "powerflex" in message_lower:
                manufacturer = "Allen-Bradley"
                component = "PowerFlex"
            elif "sinamics" in message_lower:
                manufacturer = "Siemens"
        
        # Detect PLC
        if any(kw in message_lower for kw in ["plc", "controllogix", "s7"]):
            component = "PLC"
            if "controllogix" in message_lower:
                manufacturer = "Allen-Bradley"
            elif "s7" in message_lower:
                manufacturer = "Siemens"
        
        # Detect fault code
        import re
        fault_match = re.search(r'\b[fFeE]\d{1,4}\b', message)
        if fault_match:
            fault_code = fault_match.group(0).upper()
        
        return MockContext(
            raw_message=message,
            component_name=component,
            manufacturer=manufacturer,
            fault_code=fault_code,
            manual_search_queries=[f"{component} {fault_code}".strip()]
        )


# Telegram handler function
async def intelligent_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Main message handler with intelligent context extraction.
    Wire this into your bot.py
    """
    message = update.message.text
    user_id = str(update.effective_user.id)
    telegram_id = update.effective_user.id
    
    # Get or create intake handler
    if "intake_handler" not in context.bot_data:
        context.bot_data["intake_handler"] = IntelligentIntakeHandler()
    
    handler = context.bot_data["intake_handler"]
    
    # Show typing
    await update.message.chat.send_action("typing")
    
    # Process message
    result = await handler.process_message(message, user_id, telegram_id)
    
    # Send response
    response = result["response"]
    
    # Split if too long
    if len(response) > 4096:
        for i in range(0, len(response), 4096):
            await update.message.reply_text(response[i:i+4096])
    else:
        await update.message.reply_text(response)
    
    # Store context for follow-up
    context.user_data["last_equipment_context"] = result["context"]
```

---

## PHASE 3: Bot Integration (Day 3)

### Task 3.1: Update Bot to Use Intelligent Intake
Create `agent_factory/intake/bot_integration.py`:
```python
"""Integration with existing Telegram bot."""
from telegram.ext import MessageHandler, CommandHandler, filters

from .telegram_intake import intelligent_message_handler, IntelligentIntakeHandler


def register_intelligent_intake(application):
    """
    Register intelligent intake as the primary message handler.
    
    Call this in your bot.py setup.
    """
    # Initialize handler in bot_data
    application.bot_data["intake_handler"] = IntelligentIntakeHandler()
    
    # Add message handler (should be lower priority than commands)
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            intelligent_message_handler
        ),
        group=5  # Lower priority - runs after command handlers
    )


def get_integration_code() -> str:
    """Return code snippet to add to bot.py"""
    return '''
# Add to your bot.py imports:
from agent_factory.intake.bot_integration import register_intelligent_intake

# Add to your bot setup, AFTER other handlers:
register_intelligent_intake(application)

# This will make EVERY text message go through intelligent extraction
# It runs AFTER command handlers, so /commands still work
'''
```

### Task 3.2: Manual Upload Command
Add to intake telegram handlers:
```python
async def upload_manual_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /upload_manual command."""
    await update.message.reply_text(
        "📚 **Upload Equipment Manual**\n\n"
        "Send me a PDF of an equipment manual and I'll index it for future reference.\n\n"
        "Best results with:\n"
        "• Official OEM manuals\n"
        "• Troubleshooting guides\n"
        "• Fault code references\n\n"
        "Send the PDF now, or /cancel to abort."
    )
    context.user_data["awaiting_manual_upload"] = True


async def handle_manual_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle uploaded manual PDF."""
    if not context.user_data.get("awaiting_manual_upload"):
        return
    
    context.user_data["awaiting_manual_upload"] = False
    
    document = update.message.document
    if not document.file_name.lower().endswith('.pdf'):
        await update.message.reply_text("Please send a PDF file.")
        return
    
    await update.message.reply_text("📥 Received! Processing manual...")
    
    # Download file
    file = await context.bot.get_file(document.file_id)
    
    import tempfile
    from pathlib import Path
    
    temp_path = Path(tempfile.mktemp(suffix=".pdf"))
    await file.download_to_drive(temp_path)
    
    # Index manual (requires Tab 1's ManualIndexer)
    try:
        from agent_factory.knowledge.manual_indexer import ManualIndexer
        indexer = ManualIndexer()
        
        result = indexer.index_manual(
            pdf_path=temp_path,
            manual_id=str(document.file_id),
            title=document.file_name,
            manufacturer="Unknown",  # Could ask user
            component_family="Unknown"
        )
        
        if result["success"]:
            await update.message.reply_text(
                f"✅ **Manual Indexed!**\n\n"
                f"📄 {document.file_name}\n"
                f"📑 Pages: {result['page_count']}\n"
                f"🧩 Chunks: {result['chunk_count']}\n\n"
                "I'll now reference this when you ask about this equipment!"
            )
        else:
            await update.message.reply_text(f"❌ Failed to index: {result.get('error')}")
    
    except ImportError:
        await update.message.reply_text(
            "⚠️ Manual indexing not available yet.\n"
            "File saved for future processing."
        )
    
    finally:
        temp_path.unlink(missing_ok=True)
```

---

## PHASE 4: Gap Tracking (Day 4)

### Task 4.1: Gap Tracker
Create `agent_factory/knowledge/gap_tracker.py`:
```python
"""Track missing manuals to guide acquisition."""
import logging
from typing import List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ManualGap:
    manufacturer: str
    component_family: str
    model_pattern: str
    request_count: int
    

class GapTracker:
    """Track when users ask about equipment we don't have manuals for."""
    
    def __init__(self, db=None):
        self.db = db
        self._local_gaps = {}  # Fallback if no DB
    
    async def log_gap(
        self,
        manufacturer: str,
        component_family: str,
        model_pattern: str = None
    ):
        """Log a manual gap when search returns no results."""
        key = f"{manufacturer}:{component_family}"
        
        if self.db:
            try:
                await self.db.log_manual_gap(manufacturer, component_family, model_pattern or "")
            except Exception as e:
                logger.warning(f"Failed to log gap to DB: {e}")
        
        # Also track locally
        if key in self._local_gaps:
            self._local_gaps[key]["count"] += 1
        else:
            self._local_gaps[key] = {
                "manufacturer": manufacturer,
                "component_family": component_family,
                "count": 1
            }
    
    async def get_top_gaps(self, limit: int = 10) -> List[ManualGap]:
        """Get most requested missing manuals."""
        if self.db:
            try:
                rows = await self.db.get_top_manual_gaps(limit)
                return [
                    ManualGap(
                        manufacturer=r["manufacturer"],
                        component_family=r["component_family"],
                        model_pattern=r.get("model_pattern", ""),
                        request_count=r["request_count"]
                    )
                    for r in rows
                ]
            except Exception as e:
                logger.warning(f"Failed to get gaps from DB: {e}")
        
        # Fallback to local
        sorted_gaps = sorted(
            self._local_gaps.values(),
            key=lambda x: x["count"],
            reverse=True
        )[:limit]
        
        return [
            ManualGap(
                manufacturer=g["manufacturer"],
                component_family=g["component_family"],
                model_pattern="",
                request_count=g["count"]
            )
            for g in sorted_gaps
        ]
    
    def format_gap_report(self, gaps: List[ManualGap]) -> str:
        """Format gaps for display."""
        if not gaps:
            return "No manual gaps tracked yet."
        
        lines = ["📊 **Most Requested Missing Manuals:**\n"]
        for i, gap in enumerate(gaps, 1):
            lines.append(
                f"{i}. **{gap.manufacturer} {gap.component_family}** - {gap.request_count} requests"
            )
        
        lines.append("\nUpload these manuals to improve assistance!")
        return "\n".join(lines)
```

### Task 4.2: Gap Report Command
```python
async def manual_gaps_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /manual_gaps command - show most requested missing manuals."""
    from agent_factory.knowledge.gap_tracker import GapTracker
    
    tracker = GapTracker()
    gaps = await tracker.get_top_gaps(10)
    report = tracker.format_gap_report(gaps)
    
    await update.message.reply_text(report)
```

---

## PHASE 5: Testing (Day 4-5)

### Task 5.1: Test Cases
Create `tests/test_intake.py`:
```python
import pytest
from agent_factory.intake.response_synthesizer import ResponseSynthesizer
from agent_factory.intake.telegram_intake import IntelligentIntakeHandler

@pytest.mark.asyncio
async def test_vfd_fault_extraction():
    """Test that VFD fault codes are extracted correctly."""
    handler = IntelligentIntakeHandler()
    
    result = await handler.process_message(
        message="PowerFlex 525 showing fault F004",
        user_id="test",
        telegram_id=12345
    )
    
    assert result["context"].component_name == "PowerFlex"
    assert result["context"].manufacturer == "Allen-Bradley"
    assert result["context"].fault_code == "F004"

@pytest.mark.asyncio
async def test_safety_warnings_included():
    """Test that safety warnings are in VFD responses."""
    synthesizer = ResponseSynthesizer()
    
    # Mock context
    class MockContext:
        component_name = "PowerFlex 525"
        component_family = "VFD"
        manufacturer = "Allen-Bradley"
        fault_code = "F004"
    
    result = await synthesizer.synthesize(
        context=MockContext(),
        manual_results=[],
        user_query="VFD fault"
    )
    
    assert "⚠️" in result["response"]
    assert len(result["safety_warnings"]) > 0

@pytest.mark.asyncio
async def test_no_manual_response():
    """Test response when no manuals found."""
    handler = IntelligentIntakeHandler()
    
    result = await handler.process_message(
        message="The xyz-9000 is broken",
        user_id="test",
        telegram_id=12345
    )
    
    # Should still get a helpful response
    assert "response" in result
    assert len(result["response"]) > 50
```

---

## COMMIT PROTOCOL
After EACH task:
```bash
git add -A
git commit -m "context-response: [component] description"
git push origin context-response
```

## SUCCESS CRITERIA
- [ ] ResponseSynthesizer combines context + manuals
- [ ] Safety warnings included for electrical equipment
- [ ] TelegramResponseFormatter handles long messages
- [ ] IntelligentIntakeHandler processes every message
- [ ] /upload_manual accepts PDFs
- [ ] /manual_gaps shows missing manuals
- [ ] Integration code provided for bot.py

## INTEGRATION CHECKLIST
After both tabs complete, merge and:
1. Add to bot.py: `from agent_factory.intake.bot_integration import register_intelligent_intake`
2. Call `register_intelligent_intake(application)` after other handlers
3. Test with real messages

## START NOW
Begin with Task 1.1 - Create ResponseSynthesizer.
