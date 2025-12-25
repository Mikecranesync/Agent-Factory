# Claude CLI Prompt: Build OCR Photo Processing Pipeline for RivetCEO Bot

## Context

You are adding a photo processing pipeline to RivetCEO Bot - an industrial maintenance AI assistant on Telegram. Technicians send photos of equipment they're troubleshooting. The system needs to:

1. Extract equipment identification from component photos
2. Extract tag/nameplate data (model, serial, specs) from tag photos
3. Merge context when multiple photos are sent
4. Feed enriched data into the existing 4-route orchestrator

## Tech Stack
- Python 3.11+ (async)
- python-telegram-bot v21+
- Google Gemini Vision API (free tier, use `gemini-1.5-flash`)
- PostgreSQL + pgvector (Neon)
- Existing orchestrator in `agent_factory/core/orchestrator.py`
- Existing Telegram bot in `agent_factory/telegram/telegram_bot.py`

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     PHOTO MESSAGE HANDLER                            │
│  - Receives photo from Telegram                                      │
│  - Downloads image, converts to base64                               │
│  - Checks for recent photos from same user (multi-photo grouping)    │
└──────┬──────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     PHOTO CLASSIFIER                                 │
│  (Gemini Vision - single prompt classification)                      │
├─────────────────────────────────────────────────────────────────────┤
│  Input: base64 image                                                 │
│  Output: {                                                           │
│    "photo_type": "component" | "tag" | "environment" | "unclear",   │
│    "confidence": 0.0-1.0,                                           │
│    "reasoning": "string"                                            │
│  }                                                                   │
└──────┬──────────────────────────────────────────────────────────────┘
       │
       ├─── photo_type == "component" ───┐
       │                                  ▼
       │                 ┌────────────────────────────────────────────┐
       │                 │        EQUIPMENT IDENTIFIER AGENT          │
       │                 │        (Gemini Vision)                     │
       │                 ├────────────────────────────────────────────┤
       │                 │  Extracts:                                 │
       │                 │  • equipment_type (VFD, contactor, motor,  │
       │                 │    pump, PLC, relay, breaker, etc.)        │
       │                 │  • manufacturer_guess (if logo visible)    │
       │                 │  • condition (new, worn, damaged, burnt)   │
       │                 │  • visible_issues (loose wires, corrosion, │
       │                 │    overheating signs, physical damage)     │
       │                 │  • environment (panel, field, outdoor)     │
       │                 └──────────────┬─────────────────────────────┘
       │                                │
       ├─── photo_type == "tag" ────────┼───┐
       │                                │   ▼
       │                                │  ┌──────────────────────────────────┐
       │                                │  │      TAG EXTRACTOR AGENT         │
       │                                │  │      (Gemini Vision + OCR)       │
       │                                │  ├──────────────────────────────────┤
       │                                │  │  Extracts structured data:       │
       │                                │  │  • manufacturer                  │
       │                                │  │  • model_number                  │
       │                                │  │  • serial_number                 │
       │                                │  │  • part_number                   │
       │                                │  │  • voltage_rating                │
       │                                │  │  • current_rating                │
       │                                │  │  • horsepower                    │
       │                                │  │  • phase                         │
       │                                │  │  • frequency                     │
       │                                │  │  • ip_rating                     │
       │                                │  │  • manufacture_date              │
       │                                │  │  • additional_specs (dict)       │
       │                                │  │  • raw_text (full OCR output)    │
       │                                │  └──────────────┬───────────────────┘
       │                                │                 │
       │                                ▼                 ▼
       │                 ┌─────────────────────────────────────────────────────┐
       │                 │              CONTEXT MERGER                          │
       │                 ├─────────────────────────────────────────────────────┤
       │                 │  • Combines component + tag data if both present    │
       │                 │  • Resolves conflicts (tag data wins for specs)     │
       │                 │  • Creates unified equipment profile                │
       │                 └──────────────┬──────────────────────────────────────┘
       │                                │
       ▼                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     LIBRARY AUTO-MATCHER                             │
├─────────────────────────────────────────────────────────────────────┤
│  • Queries user_machines table for matching serial/model            │
│  • If match found: link to existing machine, update last_queried    │
│  • If no match: offer to save as new machine                        │
│  • Fuzzy matching on manufacturer + model for partial matches       │
└──────┬──────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     QUERY ENRICHER                                   │
├─────────────────────────────────────────────────────────────────────┤
│  Builds enriched context for orchestrator:                          │
│  {                                                                   │
│    "original_text": user's caption or "Photo analysis",             │
│    "equipment_context": { ... merged equipment data ... },          │
│    "matched_machine": { ... from library if found ... },            │
│    "photo_observations": ["burnt marks on contactor", ...],         │
│    "suggested_queries": ["contactor replacement", ...]              │
│  }                                                                   │
└──────┬──────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  EXISTING RIVET ORCHESTRATOR                         │
│                    (4-Route Query Router)                            │
├─────────────────────────────────────────────────────────────────────┤
│  Route A: High Coverage → KB answer (now with equipment context)    │
│  Route B: Moderate → KB + SME (SME gets photo observations)         │
│  Route C: No Coverage → LLM + Gap Detector + Ingestion Trigger      │
│  Route D: Escalation → Human expert (photos attached)               │
└─────────────────────────────────────────────────────────────────────┘
```

## Detailed Implementation

### 1. Configuration

```python
# config/ocr_config.py

import os

OCR_CONFIG = {
    "gemini_api_key": os.getenv("GEMINI_API_KEY"),
    "model": "gemini-1.5-flash",
    
    # Multi-photo grouping
    "photo_group_window_seconds": 30,  # Photos within 30s treated as group
    "max_photos_per_group": 4,
    
    # Confidence thresholds
    "classification_confidence_threshold": 0.7,
    "tag_extraction_confidence_threshold": 0.6,
    
    # Retry settings
    "max_retries": 2,
    "retry_delay_seconds": 1,
}

# Equipment type taxonomy
EQUIPMENT_TYPES = [
    "vfd", "variable_frequency_drive",
    "contactor", 
    "motor", "electric_motor", "servo_motor", "stepper_motor",
    "pump", "hydraulic_pump", "vacuum_pump",
    "plc", "programmable_logic_controller",
    "hmi", "human_machine_interface",
    "relay", "safety_relay", "overload_relay",
    "breaker", "circuit_breaker", "disconnect",
    "transformer",
    "power_supply",
    "encoder",
    "sensor", "proximity_sensor", "photoelectric_sensor",
    "valve", "solenoid_valve", "pneumatic_valve",
    "compressor",
    "conveyor",
    "robot", "robot_arm",
    "welding_equipment",
    "cnc", "cnc_machine",
    "other"
]

# Known manufacturers for matching
KNOWN_MANUFACTURERS = [
    "siemens", "allen-bradley", "rockwell", "ab",
    "mitsubishi", "fanuc", "yaskawa", "omron",
    "schneider", "schneider electric", "square d",
    "abb", "danfoss", "sew", "sew-eurodrive",
    "weg", "baldor", "marathon", "leeson",
    "eaton", "cutler-hammer", "moeller",
    "ge", "general electric",
    "honeywell", "emerson", "fisher",
    "festo", "smc", "parker",
    "keyence", "banner", "sick", "ifm",
    "phoenix contact", "wago", "weidmuller",
    "pilz", "safety", "guardmaster"
]
```

### 2. Photo Classifier Agent

```python
# agents/photo_classifier.py

import google.generativeai as genai
from dataclasses import dataclass
from typing import Literal
import base64

@dataclass
class ClassificationResult:
    photo_type: Literal["component", "tag", "environment", "unclear"]
    confidence: float
    reasoning: str
    
CLASSIFICATION_PROMPT = """Analyze this industrial/maintenance photo and classify it.

CLASSIFICATION TYPES:
- "component": Shows industrial equipment (motor, VFD, contactor, pump, PLC, valve, etc.) - the main subject is a piece of equipment
- "tag": Shows a nameplate, data tag, label, or sticker with text/specs (model numbers, serial numbers, electrical ratings, etc.)
- "environment": Shows a wider view (electrical panel interior, machine room, production line) without focusing on specific equipment
- "unclear": Image is too blurry, dark, or doesn't fit other categories

Respond in this exact JSON format:
{
    "photo_type": "component" | "tag" | "environment" | "unclear",
    "confidence": 0.0 to 1.0,
    "reasoning": "brief explanation"
}

If the image shows BOTH a component AND a visible tag/nameplate on it, classify as "component" - we'll extract the tag data in a follow-up.

Analyze the image now:"""

class PhotoClassifier:
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
    
    async def classify(self, image_base64: str) -> ClassificationResult:
        """Classify a photo as component, tag, environment, or unclear"""
        
        response = await self.model.generate_content_async([
            CLASSIFICATION_PROMPT,
            {"mime_type": "image/jpeg", "data": image_base64}
        ])
        
        # Parse JSON response
        result = self._parse_response(response.text)
        
        return ClassificationResult(
            photo_type=result.get("photo_type", "unclear"),
            confidence=result.get("confidence", 0.0),
            reasoning=result.get("reasoning", "")
        )
    
    def _parse_response(self, text: str) -> dict:
        """Extract JSON from response, handling markdown code blocks"""
        import json
        import re
        
        # Remove markdown code blocks if present
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            return {"photo_type": "unclear", "confidence": 0.0, "reasoning": "Failed to parse"}
```

### 3. Equipment Identifier Agent

```python
# agents/equipment_identifier.py

from dataclasses import dataclass, field
from typing import List, Optional
import google.generativeai as genai

@dataclass
class EquipmentIdentification:
    equipment_type: str
    equipment_subtype: Optional[str] = None
    manufacturer_guess: Optional[str] = None
    manufacturer_confidence: float = 0.0
    condition: str = "unknown"  # new, good, worn, damaged, burnt, corroded
    visible_issues: List[str] = field(default_factory=list)
    environment: str = "unknown"  # panel, field, outdoor, indoor
    additional_observations: List[str] = field(default_factory=list)
    has_visible_tag: bool = False

EQUIPMENT_ID_PROMPT = """You are an industrial maintenance expert analyzing a photo of equipment.

Identify and analyze this equipment in detail.

Respond in this exact JSON format:
{
    "equipment_type": "primary type (vfd, motor, contactor, pump, plc, relay, breaker, sensor, valve, etc.)",
    "equipment_subtype": "more specific type if identifiable (e.g., 'servo motor', 'safety relay', 'proximity sensor')",
    "manufacturer_guess": "manufacturer name if logo/branding visible, otherwise null",
    "manufacturer_confidence": 0.0 to 1.0,
    "condition": "new | good | worn | damaged | burnt | corroded",
    "visible_issues": [
        "list of specific issues observed",
        "e.g., 'burnt/discolored terminals'",
        "e.g., 'loose wiring connection'",
        "e.g., 'physical damage to housing'",
        "e.g., 'corrosion on contacts'"
    ],
    "environment": "panel | field | outdoor | cleanroom | washdown | hazardous | unknown",
    "additional_observations": [
        "any other relevant observations",
        "e.g., 'appears to be 480V based on wire gauge'",
        "e.g., 'part of a larger motor control center'"
    ],
    "has_visible_tag": true if there's a nameplate/tag visible that could be photographed separately
}

Be specific about visible issues - technicians need actionable observations.

Analyze this equipment:"""

class EquipmentIdentifier:
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
    
    async def identify(self, image_base64: str) -> EquipmentIdentification:
        """Identify equipment type and condition from photo"""
        
        response = await self.model.generate_content_async([
            EQUIPMENT_ID_PROMPT,
            {"mime_type": "image/jpeg", "data": image_base64}
        ])
        
        result = self._parse_response(response.text)
        
        return EquipmentIdentification(
            equipment_type=result.get("equipment_type", "unknown"),
            equipment_subtype=result.get("equipment_subtype"),
            manufacturer_guess=result.get("manufacturer_guess"),
            manufacturer_confidence=result.get("manufacturer_confidence", 0.0),
            condition=result.get("condition", "unknown"),
            visible_issues=result.get("visible_issues", []),
            environment=result.get("environment", "unknown"),
            additional_observations=result.get("additional_observations", []),
            has_visible_tag=result.get("has_visible_tag", False)
        )
    
    def _parse_response(self, text: str) -> dict:
        import json
        import re
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            return {}
```

### 4. Tag Extractor Agent

```python
# agents/tag_extractor.py

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import google.generativeai as genai

@dataclass
class TagData:
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    serial_number: Optional[str] = None
    part_number: Optional[str] = None
    catalog_number: Optional[str] = None
    
    # Electrical specs
    voltage_rating: Optional[str] = None
    current_rating: Optional[str] = None
    horsepower: Optional[str] = None
    kilowatts: Optional[str] = None
    phase: Optional[str] = None
    frequency: Optional[str] = None
    rpm: Optional[str] = None
    
    # Physical/environmental
    ip_rating: Optional[str] = None
    enclosure_type: Optional[str] = None
    
    # Dates
    manufacture_date: Optional[str] = None
    
    # Catch-all for other specs
    additional_specs: Dict[str, Any] = field(default_factory=dict)
    
    # Raw OCR output
    raw_text: str = ""
    
    # Confidence
    extraction_confidence: float = 0.0

TAG_EXTRACTION_PROMPT = """You are an expert at reading industrial equipment nameplates and data tags.

Extract ALL text and data from this nameplate/tag image. Be thorough - capture every piece of information visible.

Respond in this exact JSON format:
{
    "manufacturer": "company name",
    "model_number": "exact model/type as shown",
    "serial_number": "exact serial number",
    "part_number": "part number if shown",
    "catalog_number": "catalog number if shown (common on Allen-Bradley)",
    
    "voltage_rating": "e.g., '480V', '208-230/460V'",
    "current_rating": "e.g., '15A', '10.5/5.25A'",
    "horsepower": "e.g., '5HP', '3/4HP'",
    "kilowatts": "e.g., '3.7kW'",
    "phase": "e.g., '3', '1', '3-phase'",
    "frequency": "e.g., '60Hz', '50/60Hz'",
    "rpm": "e.g., '1750', '1140/950'",
    
    "ip_rating": "e.g., 'IP65', 'IP54'",
    "enclosure_type": "e.g., 'NEMA 4X', 'NEMA 12'",
    
    "manufacture_date": "date if shown, any format",
    
    "additional_specs": {
        "any_other_field": "value",
        "efficiency": "95%",
        "frame": "256T",
        "insulation_class": "F",
        "service_factor": "1.15"
    },
    
    "raw_text": "complete OCR of all visible text, preserving layout where possible",
    
    "extraction_confidence": 0.0 to 1.0 based on image clarity
}

Use null for fields you cannot read or that aren't present.
For raw_text, include EVERYTHING visible, even partial text.

Extract all data from this tag:"""

class TagExtractor:
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
    
    async def extract(self, image_base64: str) -> TagData:
        """Extract structured data from equipment tag/nameplate"""
        
        response = await self.model.generate_content_async([
            TAG_EXTRACTION_PROMPT,
            {"mime_type": "image/jpeg", "data": image_base64}
        ])
        
        result = self._parse_response(response.text)
        
        return TagData(
            manufacturer=result.get("manufacturer"),
            model_number=result.get("model_number"),
            serial_number=result.get("serial_number"),
            part_number=result.get("part_number"),
            catalog_number=result.get("catalog_number"),
            voltage_rating=result.get("voltage_rating"),
            current_rating=result.get("current_rating"),
            horsepower=result.get("horsepower"),
            kilowatts=result.get("kilowatts"),
            phase=result.get("phase"),
            frequency=result.get("frequency"),
            rpm=result.get("rpm"),
            ip_rating=result.get("ip_rating"),
            enclosure_type=result.get("enclosure_type"),
            manufacture_date=result.get("manufacture_date"),
            additional_specs=result.get("additional_specs", {}),
            raw_text=result.get("raw_text", ""),
            extraction_confidence=result.get("extraction_confidence", 0.0)
        )
    
    def _parse_response(self, text: str) -> dict:
        import json
        import re
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            return {}
```

### 5. Photo Group Manager

```python
# services/photo_group_manager.py

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import uuid

@dataclass
class PhotoInGroup:
    photo_id: str
    file_id: str  # Telegram file_id
    base64_data: str
    photo_type: str  # from classifier
    timestamp: datetime
    classification_result: Optional[dict] = None
    extraction_result: Optional[dict] = None

@dataclass
class PhotoGroup:
    group_id: str
    user_id: str
    photos: List[PhotoInGroup] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    processed: bool = False
    caption: Optional[str] = None

class PhotoGroupManager:
    """Manages grouping of multiple photos sent within a time window"""
    
    def __init__(self, group_window_seconds: int = 30, max_photos: int = 4):
        self.group_window = timedelta(seconds=group_window_seconds)
        self.max_photos = max_photos
        self.active_groups: Dict[str, PhotoGroup] = {}  # user_id -> group
        self._cleanup_task = None
    
    async def add_photo(
        self, 
        user_id: str, 
        file_id: str, 
        base64_data: str,
        caption: Optional[str] = None
    ) -> PhotoGroup:
        """Add photo to user's active group, creating new group if needed"""
        
        now = datetime.utcnow()
        
        # Check for existing active group
        existing_group = self.active_groups.get(user_id)
        
        if existing_group and (now - existing_group.created_at) < self.group_window:
            # Add to existing group
            if len(existing_group.photos) < self.max_photos:
                photo = PhotoInGroup(
                    photo_id=str(uuid.uuid4()),
                    file_id=file_id,
                    base64_data=base64_data,
                    photo_type="pending",
                    timestamp=now
                )
                existing_group.photos.append(photo)
                if caption and not existing_group.caption:
                    existing_group.caption = caption
                return existing_group
        
        # Create new group
        new_group = PhotoGroup(
            group_id=str(uuid.uuid4()),
            user_id=user_id,
            photos=[PhotoInGroup(
                photo_id=str(uuid.uuid4()),
                file_id=file_id,
                base64_data=base64_data,
                photo_type="pending",
                timestamp=now
            )],
            caption=caption
        )
        self.active_groups[user_id] = new_group
        
        return new_group
    
    async def finalize_group(self, user_id: str) -> Optional[PhotoGroup]:
        """Mark group as ready for processing"""
        group = self.active_groups.pop(user_id, None)
        if group:
            group.processed = True
        return group
    
    async def wait_for_more_photos(self, user_id: str, wait_seconds: float = 3.0) -> bool:
        """Wait briefly to see if more photos are coming"""
        await asyncio.sleep(wait_seconds)
        group = self.active_groups.get(user_id)
        return group is not None and len(group.photos) > 1
```

### 6. Context Merger

```python
# services/context_merger.py

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from agents.equipment_identifier import EquipmentIdentification
from agents.tag_extractor import TagData

@dataclass
class MergedEquipmentContext:
    # Core identification
    equipment_type: str
    equipment_subtype: Optional[str] = None
    
    # From tag (authoritative if present)
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    serial_number: Optional[str] = None
    
    # Electrical specs
    voltage_rating: Optional[str] = None
    current_rating: Optional[str] = None
    horsepower: Optional[str] = None
    phase: Optional[str] = None
    frequency: Optional[str] = None
    
    # Condition from component photo
    condition: str = "unknown"
    visible_issues: List[str] = field(default_factory=list)
    environment: str = "unknown"
    
    # All specs
    all_specs: Dict[str, Any] = field(default_factory=dict)
    
    # Observations
    observations: List[str] = field(default_factory=list)
    
    # Confidence
    overall_confidence: float = 0.0
    
    # Raw data for reference
    raw_tag_text: Optional[str] = None

class ContextMerger:
    """Merges data from component and tag photos into unified context"""
    
    def merge(
        self,
        component_data: Optional[EquipmentIdentification],
        tag_data: Optional[TagData]
    ) -> MergedEquipmentContext:
        """Merge component identification with tag extraction data"""
        
        context = MergedEquipmentContext(
            equipment_type=self._get_equipment_type(component_data, tag_data)
        )
        
        # Component photo data
        if component_data:
            context.equipment_subtype = component_data.equipment_subtype
            context.condition = component_data.condition
            context.visible_issues = component_data.visible_issues
            context.environment = component_data.environment
            context.observations.extend(component_data.additional_observations)
            
            # Use manufacturer guess if no tag data
            if component_data.manufacturer_guess and not tag_data:
                context.manufacturer = component_data.manufacturer_guess
        
        # Tag data (authoritative for specs)
        if tag_data:
            context.manufacturer = tag_data.manufacturer or context.manufacturer
            context.model_number = tag_data.model_number
            context.serial_number = tag_data.serial_number
            context.voltage_rating = tag_data.voltage_rating
            context.current_rating = tag_data.current_rating
            context.horsepower = tag_data.horsepower
            context.phase = tag_data.phase
            context.frequency = tag_data.frequency
            context.all_specs = {
                "part_number": tag_data.part_number,
                "catalog_number": tag_data.catalog_number,
                "kilowatts": tag_data.kilowatts,
                "rpm": tag_data.rpm,
                "ip_rating": tag_data.ip_rating,
                "enclosure_type": tag_data.enclosure_type,
                "manufacture_date": tag_data.manufacture_date,
                **tag_data.additional_specs
            }
            context.raw_tag_text = tag_data.raw_text
            context.overall_confidence = tag_data.extraction_confidence
        
        return context
    
    def _get_equipment_type(
        self,
        component_data: Optional[EquipmentIdentification],
        tag_data: Optional[TagData]
    ) -> str:
        """Determine equipment type from available data"""
        
        if component_data and component_data.equipment_type != "unknown":
            return component_data.equipment_type
        
        # Try to infer from tag data
        if tag_data and tag_data.model_number:
            model = tag_data.model_number.lower()
            if any(x in model for x in ["vfd", "drive", "inverter"]):
                return "vfd"
            if any(x in model for x in ["motor", "mtr"]):
                return "motor"
            # ... add more patterns
        
        return "unknown"
```

### 7. Library Auto-Matcher

```python
# services/library_matcher.py

from dataclasses import dataclass
from typing import Optional, List
from services.context_merger import MergedEquipmentContext
from rapidfuzz import fuzz  # pip install rapidfuzz

@dataclass 
class LibraryMatch:
    machine_id: str
    nickname: str
    match_type: str  # "exact_serial", "model_match", "fuzzy_match"
    confidence: float
    matched_fields: List[str]

class LibraryMatcher:
    def __init__(self, db):
        self.db = db
    
    async def find_match(
        self, 
        user_id: str, 
        context: MergedEquipmentContext
    ) -> Optional[LibraryMatch]:
        """Find matching machine in user's library"""
        
        user_machines = await self.db.get_user_machines(user_id)
        
        if not user_machines:
            return None
        
        best_match = None
        best_score = 0
        
        for machine in user_machines:
            score, match_type, matched_fields = self._score_match(machine, context)
            
            if score > best_score and score >= 0.6:  # 60% threshold
                best_score = score
                best_match = LibraryMatch(
                    machine_id=machine['id'],
                    nickname=machine['nickname'],
                    match_type=match_type,
                    confidence=score,
                    matched_fields=matched_fields
                )
        
        return best_match
    
    def _score_match(
        self, 
        machine: dict, 
        context: MergedEquipmentContext
    ) -> tuple[float, str, List[str]]:
        """Score how well context matches a library machine"""
        
        matched_fields = []
        
        # Exact serial match = definite match
        if (context.serial_number and machine.get('serial_number') and
            context.serial_number.lower() == machine['serial_number'].lower()):
            return 1.0, "exact_serial", ["serial_number"]
        
        score = 0.0
        
        # Model number match
        if context.model_number and machine.get('model_number'):
            model_similarity = fuzz.ratio(
                context.model_number.lower(),
                machine['model_number'].lower()
            ) / 100
            if model_similarity > 0.8:
                score += 0.5
                matched_fields.append("model_number")
        
        # Manufacturer match
        if context.manufacturer and machine.get('manufacturer'):
            mfr_similarity = fuzz.ratio(
                context.manufacturer.lower(),
                machine['manufacturer'].lower()
            ) / 100
            if mfr_similarity > 0.7:
                score += 0.3
                matched_fields.append("manufacturer")
        
        # Serial number partial match
        if context.serial_number and machine.get('serial_number'):
            serial_similarity = fuzz.ratio(
                context.serial_number.lower(),
                machine['serial_number'].lower()
            ) / 100
            if serial_similarity > 0.8:
                score += 0.2
                matched_fields.append("serial_number")
        
        match_type = "model_match" if "model_number" in matched_fields else "fuzzy_match"
        
        return score, match_type, matched_fields
```

### 8. OCR Pipeline Orchestrator

```python
# services/ocr_pipeline.py

import asyncio
from dataclasses import dataclass
from typing import Optional, List
import base64

from agents.photo_classifier import PhotoClassifier, ClassificationResult
from agents.equipment_identifier import EquipmentIdentifier, EquipmentIdentification
from agents.tag_extractor import TagExtractor, TagData
from services.context_merger import ContextMerger, MergedEquipmentContext
from services.library_matcher import LibraryMatcher, LibraryMatch
from services.photo_group_manager import PhotoGroup

@dataclass
class OCRPipelineResult:
    equipment_context: MergedEquipmentContext
    library_match: Optional[LibraryMatch]
    suggested_queries: List[str]
    should_prompt_save: bool  # Offer to save to library
    classification_results: List[ClassificationResult]

class OCRPipeline:
    def __init__(self, api_key: str, db, model: str = "gemini-1.5-flash"):
        self.classifier = PhotoClassifier(api_key, model)
        self.equipment_identifier = EquipmentIdentifier(api_key, model)
        self.tag_extractor = TagExtractor(api_key, model)
        self.context_merger = ContextMerger()
        self.library_matcher = LibraryMatcher(db)
    
    async def process_photo_group(
        self, 
        photo_group: PhotoGroup
    ) -> OCRPipelineResult:
        """Process a group of photos through the OCR pipeline"""
        
        # Step 1: Classify all photos in parallel
        classification_tasks = [
            self.classifier.classify(photo.base64_data)
            for photo in photo_group.photos
        ]
        classifications = await asyncio.gather(*classification_tasks)
        
        # Update photo types
        for photo, classification in zip(photo_group.photos, classifications):
            photo.photo_type = classification.photo_type
            photo.classification_result = classification
        
        # Step 2: Route to appropriate extractors
        component_data: Optional[EquipmentIdentification] = None
        tag_data: Optional[TagData] = None
        
        extraction_tasks = []
        task_types = []
        
        for photo in photo_group.photos:
            if photo.photo_type == "component":
                extraction_tasks.append(
                    self.equipment_identifier.identify(photo.base64_data)
                )
                task_types.append("component")
            elif photo.photo_type == "tag":
                extraction_tasks.append(
                    self.tag_extractor.extract(photo.base64_data)
                )
                task_types.append("tag")
        
        # Run extractions in parallel
        if extraction_tasks:
            results = await asyncio.gather(*extraction_tasks)
            
            for result, task_type in zip(results, task_types):
                if task_type == "component" and component_data is None:
                    component_data = result
                elif task_type == "tag" and tag_data is None:
                    tag_data = result
        
        # Step 3: Merge context
        merged_context = self.context_merger.merge(component_data, tag_data)
        
        # Step 4: Check library for match
        library_match = await self.library_matcher.find_match(
            photo_group.user_id,
            merged_context
        )
        
        # Step 5: Generate suggested queries
        suggested_queries = self._generate_suggested_queries(
            merged_context,
            photo_group.caption
        )
        
        # Step 6: Determine if we should prompt to save
        should_prompt_save = (
            library_match is None and
            merged_context.model_number is not None and
            merged_context.manufacturer is not None
        )
        
        return OCRPipelineResult(
            equipment_context=merged_context,
            library_match=library_match,
            suggested_queries=suggested_queries,
            should_prompt_save=should_prompt_save,
            classification_results=classifications
        )
    
    def _generate_suggested_queries(
        self,
        context: MergedEquipmentContext,
        caption: Optional[str]
    ) -> List[str]:
        """Generate suggested troubleshooting queries based on extracted data"""
        
        queries = []
        
        # Issue-based suggestions
        for issue in context.visible_issues:
            if "burnt" in issue.lower() or "burn" in issue.lower():
                queries.append(f"{context.equipment_type} burnt terminals troubleshooting")
            if "loose" in issue.lower():
                queries.append(f"{context.equipment_type} connection issues")
            if "corrosion" in issue.lower():
                queries.append(f"{context.equipment_type} corrosion repair")
        
        # Equipment-specific suggestions
        if context.manufacturer and context.model_number:
            queries.append(f"{context.manufacturer} {context.model_number} manual")
            queries.append(f"{context.manufacturer} {context.model_number} fault codes")
        
        # Condition-based suggestions
        if context.condition == "damaged":
            queries.append(f"{context.equipment_type} replacement procedure")
        
        return queries[:5]  # Limit to 5 suggestions
```

### 9. Telegram Integration

```python
# telegram/photo_handler.py

import base64
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.ocr_pipeline import OCRPipeline, OCRPipelineResult
from services.photo_group_manager import PhotoGroupManager

# Initialize
photo_group_manager = PhotoGroupManager(group_window_seconds=30)
ocr_pipeline = OCRPipeline(api_key=GEMINI_API_KEY, db=db)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming photo messages"""
    
    user_id = str(update.effective_user.id)
    photo = update.message.photo[-1]  # Highest resolution
    caption = update.message.caption
    
    # Download and convert to base64
    file = await context.bot.get_file(photo.file_id)
    photo_bytes = await file.download_as_bytearray()
    base64_data = base64.b64encode(photo_bytes).decode('utf-8')
    
    # Add to group
    group = await photo_group_manager.add_photo(
        user_id=user_id,
        file_id=photo.file_id,
        base64_data=base64_data,
        caption=caption
    )
    
    # Check if this is first photo in group
    if len(group.photos) == 1:
        # Send "processing" message and wait for potential additional photos
        processing_msg = await update.message.reply_text(
            "📸 Got it! Analyzing your photo...\n"
            "_Send more photos of tags/labels within 30 seconds for better results_",
            parse_mode="Markdown"
        )
        
        # Wait briefly for more photos
        await asyncio.sleep(3)
        
        # Check if more photos arrived
        current_group = photo_group_manager.active_groups.get(user_id)
        if current_group and len(current_group.photos) > 1:
            await processing_msg.edit_text(
                f"📸 Processing {len(current_group.photos)} photos..."
            )
    
    # After brief wait, process the group
    await asyncio.sleep(2)  # Small additional wait
    
    final_group = await photo_group_manager.finalize_group(user_id)
    if not final_group:
        return  # Already processed
    
    # Process through OCR pipeline
    try:
        result = await ocr_pipeline.process_photo_group(final_group)
        await send_ocr_results(update, context, result, final_group)
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error analyzing photo: {str(e)}\n"
            "Please try again or describe the issue in text."
        )


async def send_ocr_results(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    result: OCRPipelineResult,
    photo_group
) -> None:
    """Format and send OCR results to user"""
    
    ctx = result.equipment_context
    
    # Build response message
    lines = ["🔍 **Photo Analysis Complete**\n"]
    
    # Equipment identification
    lines.append(f"**Equipment:** {ctx.equipment_type.upper()}")
    if ctx.equipment_subtype:
        lines.append(f"**Type:** {ctx.equipment_subtype}")
    
    # Manufacturer/model from tag
    if ctx.manufacturer:
        lines.append(f"**Manufacturer:** {ctx.manufacturer}")
    if ctx.model_number:
        lines.append(f"**Model:** {ctx.model_number}")
    if ctx.serial_number:
        lines.append(f"**Serial:** {ctx.serial_number}")
    
    # Specs
    specs = []
    if ctx.voltage_rating:
        specs.append(f"{ctx.voltage_rating}")
    if ctx.horsepower:
        specs.append(f"{ctx.horsepower}")
    if ctx.phase:
        specs.append(f"{ctx.phase}Ø")
    if specs:
        lines.append(f"**Specs:** {' / '.join(specs)}")
    
    # Condition
    if ctx.condition != "unknown":
        emoji = {"new": "✨", "good": "✅", "worn": "⚠️", "damaged": "🔴", "burnt": "🔥", "corroded": "🟠"}
        lines.append(f"\n**Condition:** {emoji.get(ctx.condition, '❓')} {ctx.condition.title()}")
    
    # Visible issues
    if ctx.visible_issues:
        lines.append("\n**⚠️ Issues Detected:**")
        for issue in ctx.visible_issues[:3]:
            lines.append(f"• {issue}")
    
    # Library match
    if result.library_match:
        lines.append(f"\n📚 **Matched to:** {result.library_match.nickname}")
        lines.append(f"_({result.library_match.match_type}, {result.library_match.confidence:.0%} confidence)_")
    
    text = "\n".join(lines)
    
    # Build keyboard
    keyboard = []
    
    # Troubleshoot button
    keyboard.append([
        InlineKeyboardButton(
            "🔧 Troubleshoot This",
            callback_data=f"ocr_troubleshoot_{photo_group.group_id}"
        )
    ])
    
    # Suggested queries
    if result.suggested_queries:
        keyboard.append([
            InlineKeyboardButton(
                f"💡 {result.suggested_queries[0][:30]}...",
                callback_data=f"ocr_query_0_{photo_group.group_id}"
            )
        ])
    
    # Save to library option
    if result.should_prompt_save:
        keyboard.append([
            InlineKeyboardButton(
                "💾 Save to My Library",
                callback_data=f"ocr_save_{photo_group.group_id}"
            )
        ])
    
    # Store result in context for callbacks
    context.user_data[f"ocr_result_{photo_group.group_id}"] = result
    context.user_data['active_equipment_context'] = ctx
    
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_ocr_troubleshoot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle troubleshoot callback - prompts for issue description"""
    
    query = update.callback_query
    await query.answer()
    
    # Extract group_id from callback data
    group_id = query.data.replace("ocr_troubleshoot_", "")
    result = context.user_data.get(f"ocr_result_{group_id}")
    
    if not result:
        await query.edit_message_text("Session expired. Please send the photo again.")
        return
    
    ctx = result.equipment_context
    
    await query.edit_message_text(
        f"🔧 **Troubleshooting: {ctx.manufacturer or ''} {ctx.model_number or ctx.equipment_type}**\n\n"
        f"_I've captured the equipment details. What issue are you experiencing?_\n\n"
        "Describe the problem:",
        parse_mode="Markdown"
    )
    
    # Next text message will go to orchestrator with equipment context
```

### 10. Integration with Existing Orchestrator

```python
# In orchestrator.py - modify route_query to accept equipment context

async def route_query(self, request: RivetRequest) -> RivetResponse:
    """Route query through appropriate pipeline"""
    
    # Check for equipment context from OCR
    equipment_context = request.metadata.get("equipment_context")
    
    if equipment_context:
        # Enrich the query with equipment data
        enriched_query = self._build_enriched_query(request.text, equipment_context)
        request.text = enriched_query
        
        # Boost KB search with manufacturer/model
        if equipment_context.manufacturer:
            request.search_filters["manufacturer"] = equipment_context.manufacturer
        if equipment_context.model_number:
            request.search_filters["model"] = equipment_context.model_number
    
    # Continue with normal routing...
    decision = await self.kb_evaluator.evaluate(query=request.text, ...)


def _build_enriched_query(self, user_text: str, ctx: MergedEquipmentContext) -> str:
    """Build enriched query with equipment context"""
    
    parts = []
    
    # Equipment identification
    equipment_desc = f"{ctx.manufacturer or ''} {ctx.model_number or ''} {ctx.equipment_type}".strip()
    parts.append(f"Equipment: {equipment_desc}")
    
    # Specs if relevant
    if ctx.voltage_rating:
        parts.append(f"Voltage: {ctx.voltage_rating}")
    
    # Condition/issues
    if ctx.visible_issues:
        parts.append(f"Observed issues: {', '.join(ctx.visible_issues)}")
    
    # User's question
    parts.append(f"User's question: {user_text}")
    
    return "\n".join(parts)
```

## Database Migration

```sql
-- migrations/add_ocr_tables.sql

-- Store processed photo groups for reference/debugging
CREATE TABLE ocr_photo_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    photo_count INT NOT NULL,
    caption TEXT,
    equipment_type VARCHAR(50),
    manufacturer VARCHAR(100),
    model_number VARCHAR(100),
    serial_number VARCHAR(100),
    raw_extraction JSONB,  -- Full extraction result
    processing_time_ms INT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Track OCR-triggered ingestion for gap analysis
CREATE TABLE ocr_ingestion_triggers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    photo_group_id UUID REFERENCES ocr_photo_groups(id),
    manufacturer VARCHAR(100),
    model_number VARCHAR(100),
    search_terms TEXT[],
    resolved BOOLEAN DEFAULT FALSE,
    resolved_atom_ids TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_ocr_groups_user ON ocr_photo_groups(user_id);
CREATE INDEX idx_ocr_groups_manufacturer ON ocr_photo_groups(manufacturer);
CREATE INDEX idx_ocr_triggers_resolved ON ocr_ingestion_triggers(resolved);
```

## Handler Registration

```python
# In main bot setup
from telegram.ext import MessageHandler, CallbackQueryHandler, filters

# Photo handler
application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

# OCR callback handlers  
application.add_handler(CallbackQueryHandler(handle_ocr_troubleshoot, pattern="^ocr_troubleshoot_"))
application.add_handler(CallbackQueryHandler(handle_ocr_save, pattern="^ocr_save_"))
application.add_handler(CallbackQueryHandler(handle_ocr_query, pattern="^ocr_query_"))
```

## Environment Variables

```bash
GEMINI_API_KEY=your_gemini_api_key
```

## Deliverables

1. `agents/photo_classifier.py` - Photo classification agent
2. `agents/equipment_identifier.py` - Component photo analyzer
3. `agents/tag_extractor.py` - Tag/nameplate OCR extractor
4. `services/photo_group_manager.py` - Multi-photo grouping
5. `services/context_merger.py` - Merge component + tag data
6. `services/library_matcher.py` - Match to user's saved machines
7. `services/ocr_pipeline.py` - Main orchestration pipeline
8. `telegram/photo_handler.py` - Telegram integration
9. `migrations/add_ocr_tables.sql` - Database migration
10. Updated `orchestrator.py` with equipment context handling

## Testing Flow

```
1. Send single component photo → Should identify equipment type + condition
2. Send tag photo → Should extract all specs
3. Send component + tag (2 photos within 30s) → Should merge data
4. Send photo matching saved machine → Should show library match
5. Send photo of unknown equipment → Should offer to save to library
6. Tap "Troubleshoot" → Should prompt for issue, route with context
```

Build this pipeline. Start with the agents, then the services, then Telegram integration.
