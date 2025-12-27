# WORKSTREAM 3: BOT + AI FEATURES
# Tab 3 of 3
# Copy everything below this line into Claude Code CLI

You are WS-3 (Bot + AI) in a 3-tab parallel development sprint for Rivet MVP.

## AUTONOMOUS MODE SETTINGS
- Auto-accept all file edits
- Auto-accept bash commands except: rm -rf, sudo, DROP, DELETE
- Commit after each completed task
- If context reaches 80%, checkpoint and summarize

## YOUR IDENTITY
- Workstream: WS-3 (Bot + AI Features)
- Branch: rivet-bot
- Focus: Telegram voice, intent parsing, Chat with Print, testing

## FIRST ACTIONS
```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
git checkout -b rivet-bot
git push -u origin rivet-bot
```

## EXISTING CODE (You're Building On This!)
```
agent_factory/integrations/telegram/
├── bot.py                      # Main bot (WORKING)
├── handlers.py                 # Base handlers (WORKING)
├── rivet_pro_handlers.py       # Rivet handlers (WORKING)
├── intent_detector.py          # Intent detection (WORKING)
├── conversation_manager.py     # Multi-turn (WORKING)
├── session_manager.py          # Sessions (WORKING)
└── ocr/
    ├── pipeline.py             # OCR pipeline (WORKING)
    ├── gemini_provider.py      # Gemini vision (WORKING)
    └── gpt4o_provider.py       # GPT-4O vision (WORKING)

agent_factory/rivet_pro/
├── intent_detector.py          # Full intent detection (WORKING)
├── confidence_scorer.py        # Confidence scoring (WORKING)
└── agents/                     # SME agents (WORKING)
```

**The bot works. You're adding: Voice + Claude Vision + Clarification flow.**

## YOUR TASKS

### Phase 1: Voice Message Handling (Day 1)

**Task 1.1: Create Voice Module**
Create `/agent_factory/integrations/telegram/voice/`:
```
voice/
├── __init__.py
├── handler.py          # Voice message handler
├── transcriber.py      # Whisper integration
└── audio_utils.py      # OGG → WAV conversion
```

**Task 1.2: Whisper Transcriber**
```python
# voice/transcriber.py
from openai import OpenAI

class WhisperTranscriber:
    def __init__(self):
        self.client = OpenAI()
    
    async def transcribe(self, audio_path: Path) -> str:
        with open(audio_path, "rb") as f:
            response = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="text"
            )
        return response
```

**Task 1.3: Voice Handler**
```python
# voice/handler.py
from telegram import Update
from telegram.ext import ContextTypes
import tempfile

class VoiceHandler:
    def __init__(self, transcriber, intent_detector, orchestrator):
        self.transcriber = transcriber
        self.intent_detector = intent_detector
        self.orchestrator = orchestrator
    
    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        voice = update.message.voice
        
        # Download voice file
        file = await context.bot.get_file(voice.file_id)
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            await file.download_to_drive(tmp.name)
            audio_path = Path(tmp.name)
        
        # Transcribe
        text = await self.transcriber.transcribe(audio_path)
        
        # Acknowledge
        await update.message.reply_text(f"🎤 I heard: \"{text}\"\n\nProcessing...")
        
        # Pass to existing intent detector + orchestrator
        intent = await self.intent_detector.detect(text)
        response = await self.orchestrator.route(text, intent, update.effective_user.id)
        
        await update.message.reply_text(response.message)
        
        # Cleanup
        audio_path.unlink(missing_ok=True)
```

**Task 1.4: Register Handler in Bot**
Add to `/agent_factory/integrations/telegram/bot.py`:
```python
from telegram.ext import MessageHandler, filters
from agent_factory.integrations.telegram.voice.handler import VoiceHandler

# In setup:
voice_handler = VoiceHandler(transcriber, intent_detector, orchestrator)
application.add_handler(MessageHandler(filters.VOICE, voice_handler.handle_voice))
```

### Phase 2: Claude Vision for Prints (Day 2)

**Task 2.1: Create Claude Provider**
Create `/agent_factory/integrations/telegram/ocr/claude_provider.py`:
```python
import anthropic
import base64
from pathlib import Path

class ClaudeVisionProvider:
    def __init__(self):
        self.client = anthropic.Anthropic()
        self.model = "claude-sonnet-4-20250514"
    
    async def analyze_image(self, image_path: Path, query: str = None) -> dict:
        with open(image_path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode()
        
        prompt = query or """Analyze this technical schematic and extract:
        1. Components (relays, motors, etc.)
        2. Connections between components
        3. Voltage/current ratings
        4. Circuit function"""
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image_data}},
                    {"type": "text", "text": prompt}
                ]
            }]
        )
        
        return {"text": response.content[0].text, "provider": "claude"}
```

**Task 2.2: Print Analyzer Service**
Create `/agent_factory/rivet_pro/print_analyzer.py`:
```python
class PrintAnalyzer:
    def __init__(self):
        self.provider = ClaudeVisionProvider()
    
    async def analyze(self, image_path: Path) -> str:
        result = await self.provider.analyze_image(image_path)
        return result["text"]
    
    async def answer_question(self, image_path: Path, question: str) -> str:
        result = await self.provider.analyze_image(image_path, query=question)
        return result["text"]
```

**Task 2.3: Print Handler in Bot**
Add photo handler that triggers print analysis:
```python
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Download photo
    photo = update.message.photo[-1]  # Highest resolution
    file = await context.bot.get_file(photo.file_id)
    
    # Save and analyze
    analyzer = PrintAnalyzer()
    result = await analyzer.analyze(photo_path)
    
    await update.message.reply_text(
        f"📊 **Print Analysis:**\n\n{result}\n\n"
        "Ask me anything about this schematic!"
    )
    
    # Store in session for follow-up questions
    context.user_data["current_print"] = str(photo_path)
```

### Phase 3: Intent Clarification Flow (Day 2-3)

**Task 3.1: Clarification Models**
Create `/agent_factory/rivet_pro/clarification.py`:
```python
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional

class ClarificationType(Enum):
    EQUIPMENT_AMBIGUOUS = "equipment_ambiguous"
    INTENT_UNCLEAR = "intent_unclear"
    MISSING_DETAILS = "missing_details"

@dataclass
class ClarificationRequest:
    type: ClarificationType
    prompt: str
    options: List[str]
    context: dict
```

**Task 3.2: Clarifier Logic**
```python
class IntentClarifier:
    CONFIDENCE_THRESHOLD = 0.7
    
    def needs_clarification(self, intent) -> bool:
        if intent.confidence < self.CONFIDENCE_THRESHOLD:
            return True
        if len(intent.equipment_candidates) > 1:
            return True
        if intent.intent_type == "create_work_order" and not intent.equipment_id:
            return True
        return False
    
    def generate_clarification(self, intent) -> ClarificationRequest:
        if len(intent.equipment_candidates) > 1:
            options = [c["name"] for c in intent.equipment_candidates[:5]]
            return ClarificationRequest(
                type=ClarificationType.EQUIPMENT_AMBIGUOUS,
                prompt="Which equipment?\n" + "\n".join(f"{i+1}. {o}" for i, o in enumerate(options)),
                options=options,
                context={"candidates": intent.equipment_candidates}
            )
        # ... other clarification types
```

**Task 3.3: Wire Into Orchestrator**
Modify flow so clarification happens before work order creation:
```python
# In orchestrator or handler
if clarifier.needs_clarification(intent):
    clarification = clarifier.generate_clarification(intent)
    await update.message.reply_text(clarification.prompt)
    context.user_data["pending_clarification"] = clarification
    return  # Wait for user response
```

### Phase 4: Integration Testing (Day 3)

**Task 4.1: Test Fixtures**
Create `/tests/fixtures/`:
- Sample voice file (OGG)
- Sample schematic image
- Mock API responses

**Task 4.2: E2E Test: Voice → Work Order**
```python
@pytest.mark.asyncio
async def test_voice_creates_work_order():
    # Simulate voice message
    # Verify transcription
    # Verify intent detection
    # Verify work order created
```

**Task 4.3: E2E Test: Print → Q&A**
```python
@pytest.mark.asyncio
async def test_print_qa():
    # Upload schematic
    # Ask question
    # Verify accurate answer
```

**Task 4.4: E2E Test: Clarification Flow**
```python
@pytest.mark.asyncio
async def test_ambiguous_equipment_asks_clarification():
    # Send "the pump is broken" (ambiguous)
    # Verify bot asks "which pump?"
    # Respond with selection
    # Verify work order for correct equipment
```

## COMMIT PROTOCOL
After EACH task:
```bash
git add -A
git commit -m "WS-3: [component] description"
git push origin rivet-bot
```

## SUCCESS CRITERIA
- [ ] Voice message → transcription → work order
- [ ] Photo upload → Claude analysis → Q&A works
- [ ] Ambiguous input triggers clarification
- [ ] All E2E tests pass
- [ ] Bot runs: `python telegram_bot.py`

## DEPENDENCIES
- WS-1 API for work order creation (can mock initially)
- OpenAI API key for Whisper
- Anthropic API key for Claude Vision

## ENV VARS NEEDED
```
OPENAI_API_KEY=sk-xxx          # For Whisper
ANTHROPIC_API_KEY=sk-ant-xxx   # For Claude Vision
TELEGRAM_BOT_TOKEN=xxx         # Already exists
```

## UPDATE STATUS
After each phase, update: `/sprint/STATUS_WS3.md`

## START NOW
Begin with Task 1.1 - Create the voice module structure.
