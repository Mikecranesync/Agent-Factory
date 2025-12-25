# Claude CLI Prompt: Integrate OCR Pipeline into Telegram Bot + E2E Testing

## Objective

Integrate photo/OCR processing into the existing RivetCEO Telegram bot. When a technician sends a photo, the system should:
1. Classify the photo (component vs tag/nameplate)
2. Extract relevant data
3. Feed enriched context to the orchestrator
4. Return a useful response

Then validate with end-to-end tests.

## Current System Context

- Existing bot: `agent_factory/telegram/telegram_bot.py`
- Existing orchestrator: `agent_factory/core/orchestrator.py`
- Database: PostgreSQL + pgvector on Neon
- LLM: Groq (no vision) for text, need Gemini for vision
- Queue: Redis on VPS

## Tech Stack for This Integration

- `google-generativeai` - Gemini Vision API (free tier)
- `python-telegram-bot` v21+ (async)
- Existing project structure

## File Structure to Create

```
agent_factory/
├── ocr/
│   ├── __init__.py
│   ├── classifier.py        # Photo type classification
│   ├── extractor.py         # Equipment + Tag extraction (combined)
│   └── pipeline.py          # Main orchestration
├── telegram/
│   ├── photo_handler.py     # NEW - handles photo messages
│   └── telegram_bot.py      # MODIFY - register photo handler
└── tests/
    └── test_ocr_e2e.py      # End-to-end test
```

## Implementation

### 1. Install Dependencies

```bash
pip install google-generativeai pillow
```

### 2. Environment Variable

```bash
# Add to .env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. OCR Classifier + Extractor (Combined for Simplicity)

```python
# agent_factory/ocr/__init__.py
from .pipeline import OCRPipeline
from .extractor import PhotoAnalyzer

__all__ = ["OCRPipeline", "PhotoAnalyzer"]
```

```python
# agent_factory/ocr/extractor.py
"""
Combined photo analyzer - classifies and extracts in one call for efficiency.
Uses Gemini 1.5 Flash (free tier: 15 RPM, 1M tokens/day)
"""

import os
import json
import re
import google.generativeai as genai
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class PhotoAnalysisResult:
    # Classification
    photo_type: str  # "component", "tag", "both", "environment", "unclear"
    
    # Equipment identification
    equipment_type: Optional[str] = None
    equipment_subtype: Optional[str] = None
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    serial_number: Optional[str] = None
    
    # Condition assessment
    condition: str = "unknown"
    visible_issues: List[str] = field(default_factory=list)
    
    # Electrical specs (from tag)
    voltage: Optional[str] = None
    current: Optional[str] = None
    horsepower: Optional[str] = None
    phase: Optional[str] = None
    
    # All other specs
    additional_specs: Dict[str, Any] = field(default_factory=dict)
    
    # Raw OCR text
    raw_text: Optional[str] = None
    
    # Confidence
    confidence: float = 0.0
    
    # Suggested next steps
    suggested_queries: List[str] = field(default_factory=list)


ANALYSIS_PROMPT = """You are an industrial maintenance expert analyzing a photo sent by a field technician.

Analyze this image and extract ALL relevant information.

RESPOND IN THIS EXACT JSON FORMAT:
{
    "photo_type": "component" | "tag" | "both" | "environment" | "unclear",
    
    "equipment_type": "vfd | motor | contactor | pump | plc | relay | breaker | sensor | valve | compressor | robot | conveyor | transformer | other | null",
    "equipment_subtype": "more specific type if identifiable, e.g., 'servo motor', 'safety relay'",
    
    "manufacturer": "company name if visible (logo, text)",
    "model_number": "exact model/catalog number if visible",
    "serial_number": "serial number if visible",
    
    "condition": "new | good | worn | damaged | burnt | corroded | unknown",
    "visible_issues": [
        "specific observable problems",
        "e.g., 'burnt terminal on T1'",
        "e.g., 'loose wire connection'",
        "e.g., 'corrosion on contacts'"
    ],
    
    "voltage": "voltage rating if visible, e.g., '480V', '208-230/460V'",
    "current": "current rating if visible, e.g., '15A'",
    "horsepower": "HP rating if visible, e.g., '5HP'",
    "phase": "phase if visible, e.g., '3', '1'",
    
    "additional_specs": {
        "any_other_specs": "values",
        "frequency": "60Hz",
        "rpm": "1750",
        "frame": "256T",
        "ip_rating": "IP65"
    },
    
    "raw_text": "ALL visible text transcribed, preserving what you can read",
    
    "confidence": 0.0 to 1.0,
    
    "suggested_queries": [
        "what the tech might want to know",
        "e.g., 'Allen-Bradley 100-C09D10 fault codes'",
        "e.g., 'contactor replacement procedure'"
    ]
}

IMPORTANT:
- For photo_type "both": image shows equipment WITH a visible nameplate/tag
- Be specific about visible_issues - techs need actionable observations
- Extract ALL text you can read into raw_text
- If you can't determine something, use null
- Suggest 2-3 relevant troubleshooting queries based on what you see

Analyze this industrial equipment photo:"""


class PhotoAnalyzer:
    """Analyzes industrial equipment photos using Gemini Vision"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
    
    async def analyze(self, image_bytes: bytes) -> PhotoAnalysisResult:
        """
        Analyze a photo and extract all relevant information.
        
        Args:
            image_bytes: Raw image bytes (JPEG/PNG)
            
        Returns:
            PhotoAnalysisResult with all extracted data
        """
        import base64
        
        # Convert to base64
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Call Gemini
        try:
            response = await self.model.generate_content_async([
                ANALYSIS_PROMPT,
                {"mime_type": "image/jpeg", "data": image_b64}
            ])
            
            result = self._parse_response(response.text)
            return self._to_dataclass(result)
            
        except Exception as e:
            print(f"[OCR] Gemini error: {e}")
            return PhotoAnalysisResult(
                photo_type="unclear",
                confidence=0.0,
                visible_issues=[f"Analysis failed: {str(e)}"]
            )
    
    def _parse_response(self, text: str) -> dict:
        """Extract JSON from Gemini response"""
        # Remove markdown code blocks
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError as e:
            print(f"[OCR] JSON parse error: {e}")
            print(f"[OCR] Raw response: {text[:500]}")
            return {"photo_type": "unclear", "confidence": 0.0}
    
    def _to_dataclass(self, data: dict) -> PhotoAnalysisResult:
        """Convert dict to PhotoAnalysisResult"""
        return PhotoAnalysisResult(
            photo_type=data.get("photo_type", "unclear"),
            equipment_type=data.get("equipment_type"),
            equipment_subtype=data.get("equipment_subtype"),
            manufacturer=data.get("manufacturer"),
            model_number=data.get("model_number"),
            serial_number=data.get("serial_number"),
            condition=data.get("condition", "unknown"),
            visible_issues=data.get("visible_issues", []),
            voltage=data.get("voltage"),
            current=data.get("current"),
            horsepower=data.get("horsepower"),
            phase=data.get("phase"),
            additional_specs=data.get("additional_specs", {}),
            raw_text=data.get("raw_text"),
            confidence=data.get("confidence", 0.0),
            suggested_queries=data.get("suggested_queries", [])
        )
```

```python
# agent_factory/ocr/pipeline.py
"""
OCR Pipeline - orchestrates photo analysis and context building
"""

from dataclasses import dataclass
from typing import Optional, List
from .extractor import PhotoAnalyzer, PhotoAnalysisResult


@dataclass
class OCRContext:
    """Context to pass to orchestrator"""
    equipment_description: str
    manufacturer: Optional[str]
    model_number: Optional[str]
    serial_number: Optional[str]
    condition: str
    visible_issues: List[str]
    specs_summary: str
    raw_analysis: PhotoAnalysisResult
    suggested_queries: List[str]


class OCRPipeline:
    """Main pipeline for processing equipment photos"""
    
    def __init__(self, api_key: str = None):
        self.analyzer = PhotoAnalyzer(api_key)
    
    async def process_photo(self, image_bytes: bytes) -> OCRContext:
        """
        Process a photo and return context for the orchestrator.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            OCRContext ready for orchestrator
        """
        # Analyze the photo
        analysis = await self.analyzer.analyze(image_bytes)
        
        # Build equipment description
        equipment_parts = []
        if analysis.manufacturer:
            equipment_parts.append(analysis.manufacturer)
        if analysis.model_number:
            equipment_parts.append(analysis.model_number)
        if analysis.equipment_type:
            equipment_parts.append(analysis.equipment_type.upper())
        
        equipment_description = " ".join(equipment_parts) if equipment_parts else "Unknown equipment"
        
        # Build specs summary
        specs = []
        if analysis.voltage:
            specs.append(analysis.voltage)
        if analysis.horsepower:
            specs.append(analysis.horsepower)
        if analysis.phase:
            specs.append(f"{analysis.phase}Ø")
        if analysis.current:
            specs.append(analysis.current)
        
        specs_summary = " / ".join(specs) if specs else "No specs visible"
        
        return OCRContext(
            equipment_description=equipment_description,
            manufacturer=analysis.manufacturer,
            model_number=analysis.model_number,
            serial_number=analysis.serial_number,
            condition=analysis.condition,
            visible_issues=analysis.visible_issues,
            specs_summary=specs_summary,
            raw_analysis=analysis,
            suggested_queries=analysis.suggested_queries
        )
    
    def build_enriched_query(self, ocr_context: OCRContext, user_text: str = None) -> str:
        """
        Build an enriched query string for the orchestrator.
        
        Args:
            ocr_context: Context from process_photo
            user_text: Optional text/caption from user
            
        Returns:
            Enriched query string
        """
        parts = []
        
        # Equipment info
        parts.append(f"Equipment: {ocr_context.equipment_description}")
        
        if ocr_context.specs_summary != "No specs visible":
            parts.append(f"Specs: {ocr_context.specs_summary}")
        
        if ocr_context.serial_number:
            parts.append(f"Serial: {ocr_context.serial_number}")
        
        # Condition and issues
        if ocr_context.condition != "unknown":
            parts.append(f"Condition: {ocr_context.condition}")
        
        if ocr_context.visible_issues:
            parts.append(f"Observed issues: {', '.join(ocr_context.visible_issues)}")
        
        # User's question/caption
        if user_text:
            parts.append(f"Technician's question: {user_text}")
        else:
            parts.append("Technician sent photo for analysis - provide troubleshooting guidance")
        
        return "\n".join(parts)
```

### 4. Telegram Photo Handler

```python
# agent_factory/telegram/photo_handler.py
"""
Telegram photo message handler - processes equipment photos through OCR pipeline
"""

import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from agent_factory.ocr import OCRPipeline

# Initialize pipeline
ocr_pipeline = OCRPipeline()


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle incoming photo messages.
    
    Flow:
    1. Download photo
    2. Run through OCR pipeline
    3. Display analysis results
    4. Offer troubleshooting options
    """
    user_id = str(update.effective_user.id)
    caption = update.message.caption  # User's text with the photo
    
    # Get highest resolution photo
    photo = update.message.photo[-1]
    
    # Send "analyzing" message
    status_msg = await update.message.reply_text(
        "📸 Analyzing your photo...",
        reply_to_message_id=update.message.message_id
    )
    
    try:
        # Download photo
        file = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()
        
        # Process through OCR pipeline
        ocr_context = await ocr_pipeline.process_photo(bytes(image_bytes))
        
        # Store context for follow-up
        context.user_data['ocr_context'] = ocr_context
        context.user_data['photo_file_id'] = photo.file_id
        
        # Build response message
        response_text = format_ocr_response(ocr_context)
        
        # Build keyboard
        keyboard = build_ocr_keyboard(ocr_context)
        
        # Update status message with results
        await status_msg.edit_text(
            response_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        print(f"[PhotoHandler] Error: {e}")
        await status_msg.edit_text(
            f"❌ Error analyzing photo: {str(e)}\n\n"
            "Please try again or describe the issue in text."
        )


def format_ocr_response(ocr_context) -> str:
    """Format OCR results for Telegram message"""
    
    lines = ["🔍 **Photo Analysis**\n"]
    
    # Equipment identification
    lines.append(f"**Equipment:** {ocr_context.equipment_description}")
    
    # Specs
    if ocr_context.specs_summary != "No specs visible":
        lines.append(f"**Specs:** {ocr_context.specs_summary}")
    
    # Serial number
    if ocr_context.serial_number:
        lines.append(f"**Serial:** {ocr_context.serial_number}")
    
    # Condition with emoji
    condition_emoji = {
        "new": "✨",
        "good": "✅", 
        "worn": "⚠️",
        "damaged": "🔴",
        "burnt": "🔥",
        "corroded": "🟠",
        "unknown": "❓"
    }
    emoji = condition_emoji.get(ocr_context.condition, "❓")
    lines.append(f"\n**Condition:** {emoji} {ocr_context.condition.title()}")
    
    # Visible issues
    if ocr_context.visible_issues:
        lines.append("\n**⚠️ Issues Detected:**")
        for issue in ocr_context.visible_issues[:4]:  # Limit to 4
            lines.append(f"• {issue}")
    
    # Confidence indicator
    conf = ocr_context.raw_analysis.confidence
    if conf >= 0.8:
        conf_text = "High confidence"
    elif conf >= 0.5:
        conf_text = "Medium confidence"
    else:
        conf_text = "Low confidence - image may be unclear"
    lines.append(f"\n_{conf_text}_")
    
    return "\n".join(lines)


def build_ocr_keyboard(ocr_context) -> InlineKeyboardMarkup:
    """Build inline keyboard for OCR results"""
    
    keyboard = []
    
    # Main action - troubleshoot
    keyboard.append([
        InlineKeyboardButton(
            "🔧 Troubleshoot This",
            callback_data="ocr_troubleshoot"
        )
    ])
    
    # Suggested queries (show top 2)
    if ocr_context.suggested_queries:
        for i, query in enumerate(ocr_context.suggested_queries[:2]):
            # Truncate long queries
            display_text = query[:28] + "..." if len(query) > 28 else query
            keyboard.append([
                InlineKeyboardButton(
                    f"💡 {display_text}",
                    callback_data=f"ocr_suggest_{i}"
                )
            ])
    
    # Save to library option (if we have model info)
    if ocr_context.model_number or ocr_context.manufacturer:
        keyboard.append([
            InlineKeyboardButton(
                "💾 Save to My Library",
                callback_data="ocr_save"
            )
        ])
    
    return InlineKeyboardMarkup(keyboard)


async def handle_ocr_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callbacks from OCR result buttons"""
    
    query = update.callback_query
    await query.answer()
    
    ocr_context = context.user_data.get('ocr_context')
    
    if not ocr_context:
        await query.edit_message_text(
            "⏰ Session expired. Please send the photo again."
        )
        return
    
    callback_data = query.data
    
    if callback_data == "ocr_troubleshoot":
        await handle_troubleshoot(query, context, ocr_context)
    
    elif callback_data.startswith("ocr_suggest_"):
        idx = int(callback_data.replace("ocr_suggest_", ""))
        await handle_suggested_query(query, context, ocr_context, idx)
    
    elif callback_data == "ocr_save":
        await handle_save_to_library(query, context, ocr_context)


async def handle_troubleshoot(query, context, ocr_context) -> None:
    """Prompt user to describe the issue"""
    
    # Set flag so next text message goes to orchestrator with context
    context.user_data['awaiting_issue_description'] = True
    
    await query.edit_message_text(
        f"🔧 **Troubleshooting: {ocr_context.equipment_description}**\n\n"
        f"_I've captured the equipment details._\n\n"
        "**What issue are you experiencing?**\n"
        "Describe the problem, symptoms, or error codes:",
        parse_mode="Markdown"
    )


async def handle_suggested_query(query, context, ocr_context, idx: int) -> None:
    """Execute a suggested query"""
    
    if idx < len(ocr_context.suggested_queries):
        suggested = ocr_context.suggested_queries[idx]
        
        # Build enriched query
        enriched_query = ocr_pipeline.build_enriched_query(
            ocr_context, 
            user_text=suggested
        )
        
        # TODO: Send to orchestrator
        # For now, show what would be sent
        await query.edit_message_text(
            f"🔍 **Searching for:** {suggested}\n\n"
            f"_Equipment context: {ocr_context.equipment_description}_\n\n"
            "⏳ Processing query...",
            parse_mode="Markdown"
        )
        
        # Here you would call:
        # response = await orchestrator.route_query(enriched_query, user_id)
        # await query.edit_message_text(response.text)


async def handle_save_to_library(query, context, ocr_context) -> None:
    """Start flow to save equipment to user's library"""
    
    # Pre-fill from OCR data
    context.user_data['new_machine'] = {
        'manufacturer': ocr_context.manufacturer,
        'model_number': ocr_context.model_number,
        'serial_number': ocr_context.serial_number,
    }
    
    await query.edit_message_text(
        f"💾 **Save to Library**\n\n"
        f"**Detected:**\n"
        f"• Manufacturer: {ocr_context.manufacturer or 'Unknown'}\n"
        f"• Model: {ocr_context.model_number or 'Unknown'}\n"
        f"• Serial: {ocr_context.serial_number or 'Unknown'}\n\n"
        "**What nickname do you want to give this machine?**\n"
        "_(e.g., 'Line 3 Robot', 'Basement Compressor')_",
        parse_mode="Markdown"
    )
    
    context.user_data['awaiting_machine_nickname'] = True


# Message handler for follow-up text after OCR
async def handle_post_ocr_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Handle text messages that follow OCR analysis.
    Returns True if handled, False to pass to other handlers.
    """
    
    # Check if awaiting issue description
    if context.user_data.get('awaiting_issue_description'):
        ocr_context = context.user_data.get('ocr_context')
        
        if ocr_context:
            context.user_data['awaiting_issue_description'] = False
            
            # Build enriched query with user's issue
            enriched_query = ocr_pipeline.build_enriched_query(
                ocr_context,
                user_text=update.message.text
            )
            
            # Send processing message
            await update.message.reply_text(
                f"🔧 Analyzing issue for **{ocr_context.equipment_description}**...",
                parse_mode="Markdown"
            )
            
            # TODO: Route to orchestrator
            # response = await orchestrator.route_query(enriched_query, user_id)
            
            # For now, show the enriched query
            await update.message.reply_text(
                f"**Enriched Query (Debug):**\n```\n{enriched_query}\n```\n\n"
                "_This would be sent to the orchestrator_",
                parse_mode="Markdown"
            )
            
            return True
    
    # Check if awaiting machine nickname
    if context.user_data.get('awaiting_machine_nickname'):
        context.user_data['awaiting_machine_nickname'] = False
        nickname = update.message.text
        
        machine_data = context.user_data.get('new_machine', {})
        machine_data['nickname'] = nickname
        
        # TODO: Save to database
        # await db.create_machine(user_id, machine_data)
        
        await update.message.reply_text(
            f"✅ **{nickname}** saved to your library!\n\n"
            f"• Manufacturer: {machine_data.get('manufacturer', 'Unknown')}\n"
            f"• Model: {machine_data.get('model_number', 'Unknown')}\n\n"
            "Use /library to view your saved machines.",
            parse_mode="Markdown"
        )
        
        return True
    
    return False  # Not handled, pass to other handlers
```

### 5. Register Handlers in Main Bot

```python
# agent_factory/telegram/telegram_bot.py
# ADD these imports and handlers to your existing bot

from telegram.ext import MessageHandler, CallbackQueryHandler, filters
from agent_factory.telegram.photo_handler import (
    handle_photo,
    handle_ocr_callback,
    handle_post_ocr_text
)

def setup_handlers(application):
    """Register all handlers"""
    
    # ... existing handlers ...
    
    # Photo handler - processes equipment photos
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # OCR callback handler - handles button presses on OCR results
    application.add_handler(CallbackQueryHandler(
        handle_ocr_callback, 
        pattern="^ocr_"
    ))
    
    # Text handler for post-OCR follow-up
    # This should come BEFORE your main text handler
    # It returns False if not handled, allowing fallthrough
    async def text_handler(update, context):
        handled = await handle_post_ocr_text(update, context)
        if not handled:
            # Pass to your existing message handler
            await handle_message(update, context)
    
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        text_handler
    ))
```

### 6. End-to-End Test Script

```python
# tests/test_ocr_e2e.py
"""
End-to-end test for OCR pipeline.
Run with: python -m pytest tests/test_ocr_e2e.py -v -s
Or standalone: python tests/test_ocr_e2e.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_factory.ocr import OCRPipeline
from agent_factory.ocr.extractor import PhotoAnalyzer


# Test images - you can use URLs or local files
TEST_IMAGES = {
    "contactor": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64",  # Replace with real industrial image
    "nameplate": None,  # Add URL to nameplate image
}


async def test_analyzer_basic():
    """Test basic photo analysis"""
    print("\n" + "="*60)
    print("TEST: Basic Photo Analyzer")
    print("="*60)
    
    analyzer = PhotoAnalyzer()
    
    # Create a simple test image (gray square)
    # In real tests, use actual equipment photos
    from PIL import Image
    import io
    
    img = Image.new('RGB', (400, 400), color='gray')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes = img_bytes.getvalue()
    
    print("Analyzing test image...")
    result = await analyzer.analyze(img_bytes)
    
    print(f"\nResults:")
    print(f"  Photo type: {result.photo_type}")
    print(f"  Equipment type: {result.equipment_type}")
    print(f"  Confidence: {result.confidence}")
    
    assert result is not None
    assert result.photo_type in ["component", "tag", "both", "environment", "unclear"]
    print("✅ Basic analyzer test passed")


async def test_pipeline_with_local_image(image_path: str = None):
    """Test full pipeline with a local image"""
    print("\n" + "="*60)
    print("TEST: Full Pipeline with Local Image")
    print("="*60)
    
    if not image_path:
        print("⚠️  No image path provided. Skipping...")
        print("   Run with: python test_ocr_e2e.py /path/to/equipment/photo.jpg")
        return
    
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return
    
    pipeline = OCRPipeline()
    
    # Load image
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    print(f"Processing image: {image_path}")
    print(f"Image size: {len(image_bytes)} bytes")
    
    # Process through pipeline
    ocr_context = await pipeline.process_photo(image_bytes)
    
    print(f"\n📊 OCR Results:")
    print(f"  Equipment: {ocr_context.equipment_description}")
    print(f"  Manufacturer: {ocr_context.manufacturer}")
    print(f"  Model: {ocr_context.model_number}")
    print(f"  Serial: {ocr_context.serial_number}")
    print(f"  Condition: {ocr_context.condition}")
    print(f"  Specs: {ocr_context.specs_summary}")
    
    if ocr_context.visible_issues:
        print(f"  Issues:")
        for issue in ocr_context.visible_issues:
            print(f"    • {issue}")
    
    if ocr_context.suggested_queries:
        print(f"  Suggested queries:")
        for q in ocr_context.suggested_queries:
            print(f"    • {q}")
    
    # Test enriched query building
    print(f"\n📝 Enriched Query (user asks 'why won't it start'):")
    enriched = pipeline.build_enriched_query(ocr_context, "why won't it start")
    print(enriched)
    
    # Raw analysis
    print(f"\n🔬 Raw Analysis:")
    print(f"  Photo type: {ocr_context.raw_analysis.photo_type}")
    print(f"  Confidence: {ocr_context.raw_analysis.confidence}")
    if ocr_context.raw_analysis.raw_text:
        print(f"  Raw OCR text: {ocr_context.raw_analysis.raw_text[:200]}...")
    
    print("\n✅ Pipeline test completed")


async def test_telegram_integration():
    """Test that photo handler formats correctly"""
    print("\n" + "="*60)
    print("TEST: Telegram Response Formatting")
    print("="*60)
    
    from agent_factory.telegram.photo_handler import format_ocr_response, build_ocr_keyboard
    from agent_factory.ocr.pipeline import OCRContext
    from agent_factory.ocr.extractor import PhotoAnalysisResult
    
    # Create mock OCR context
    mock_analysis = PhotoAnalysisResult(
        photo_type="component",
        equipment_type="contactor",
        manufacturer="Allen-Bradley",
        model_number="100-C09D10",
        serial_number="AB12345678",
        condition="burnt",
        visible_issues=["Burnt terminals on T1", "Discoloration on coil"],
        voltage="480V",
        phase="3",
        confidence=0.85,
        suggested_queries=[
            "Allen-Bradley 100-C09D10 replacement",
            "contactor burnt terminals troubleshooting"
        ]
    )
    
    mock_context = OCRContext(
        equipment_description="Allen-Bradley 100-C09D10 CONTACTOR",
        manufacturer="Allen-Bradley",
        model_number="100-C09D10",
        serial_number="AB12345678",
        condition="burnt",
        visible_issues=["Burnt terminals on T1", "Discoloration on coil"],
        specs_summary="480V / 3Ø",
        raw_analysis=mock_analysis,
        suggested_queries=[
            "Allen-Bradley 100-C09D10 replacement",
            "contactor burnt terminals troubleshooting"
        ]
    )
    
    # Test formatting
    response = format_ocr_response(mock_context)
    print("Formatted Response:")
    print("-" * 40)
    print(response)
    print("-" * 40)
    
    # Test keyboard
    keyboard = build_ocr_keyboard(mock_context)
    print("\nKeyboard Buttons:")
    for row in keyboard.inline_keyboard:
        for btn in row:
            print(f"  [{btn.text}] -> {btn.callback_data}")
    
    print("\n✅ Telegram formatting test passed")


async def run_all_tests(image_path: str = None):
    """Run all tests"""
    print("\n🧪 OCR PIPELINE END-TO-END TESTS")
    print("="*60)
    
    # Check for API key
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY not set!")
        print("   Set it with: export GEMINI_API_KEY=your_key")
        return
    
    print(f"✓ GEMINI_API_KEY is set")
    
    try:
        await test_analyzer_basic()
        await test_telegram_integration()
        await test_pipeline_with_local_image(image_path)
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test OCR Pipeline")
    parser.add_argument("image", nargs="?", help="Path to test image")
    args = parser.parse_args()
    
    asyncio.run(run_all_tests(args.image))


if __name__ == "__main__":
    main()
```

### 7. Quick Manual Test

```bash
# 1. Set API key
export GEMINI_API_KEY=your_key_here

# 2. Run basic test (no image needed)
python tests/test_ocr_e2e.py

# 3. Run with real equipment photo
python tests/test_ocr_e2e.py /path/to/your/equipment_photo.jpg

# 4. Run full bot and send photo via Telegram
python -m agent_factory.telegram.telegram_bot
```

### 8. Integration Test via Telegram

Once the bot is running, test manually:

```
1. Send photo of equipment to bot
   → Should respond with analysis

2. Send photo of nameplate/tag
   → Should extract model, serial, specs

3. Send photo + caption "won't start"
   → Should combine analysis with question

4. Tap "Troubleshoot This"
   → Should prompt for issue description

5. Type issue description
   → Should show enriched query (debug mode)
   → In production: routes to orchestrator

6. Tap "Save to My Library"
   → Should prompt for nickname
```

## Deliverables

1. `agent_factory/ocr/__init__.py`
2. `agent_factory/ocr/extractor.py` - Photo analyzer using Gemini
3. `agent_factory/ocr/pipeline.py` - Pipeline orchestration
4. `agent_factory/telegram/photo_handler.py` - Telegram integration
5. `tests/test_ocr_e2e.py` - End-to-end tests
6. Updated `telegram_bot.py` with handler registration

## Testing Checklist

- [ ] `GEMINI_API_KEY` set in environment
- [ ] Basic analyzer test passes
- [ ] Telegram formatting test passes
- [ ] Local image test works with real equipment photo
- [ ] Bot responds to photo messages
- [ ] Bot shows equipment analysis
- [ ] "Troubleshoot" button works
- [ ] Suggested queries appear
- [ ] "Save to Library" flow works
- [ ] Enriched query contains equipment context

## Next Steps After Validation

1. Connect `handle_suggested_query` to real orchestrator
2. Connect `handle_post_ocr_text` to real orchestrator  
3. Connect `handle_save_to_library` to database
4. Add queue job when unknown equipment detected
5. Add photo to ingestion trigger metadata
