# HARVEST BLOCK 12: Feedback Handler

**Priority**: HIGH
**Size**: 10KB (300 lines)
**Source**: `agent_factory/rivet_pro/feedback_handler.py`
**Target**: `rivet/rivet_pro/feedback_handler.py`

---

## Overview

User feedback processing and quality loop - automatically triggers research for low-quality knowledge atoms based on thumbs up/down feedback.

### What This Adds

- Thumbs up/down feedback processing
- Feedback counter incrementation (positive/negative)
- Success rate calculation (positive / total)
- Automatic research triggering for low-quality atoms (<30% success rate)
- Minimum sample threshold (3+ feedback required before triggering)
- Low-quality atom queries for admin dashboard
- Singleton pattern with global convenience function

### Key Features

```python
from rivet.rivet_pro.feedback_handler import process_feedback, get_feedback_handler

# Process feedback (global function)
triggered = await process_feedback(
    atom_ids=["allen_bradley:controllogix:motor-control"],
    feedback_type="positive"  # or "negative"
)
# Returns: ["atom_id1", ...] - list of atoms that triggered research

# Or use handler directly
from rivet.core.database_manager import DatabaseManager
db = DatabaseManager()
handler = get_feedback_handler(db)

# Process feedback batch
triggered = await handler.process_feedback(
    atom_ids=["atom1", "atom2", "atom3"],
    feedback_type="negative"
)

# Get low-quality atoms for admin review
low_quality = await handler.get_low_quality_atoms(limit=10)
# Returns: [{"atom_id": "...", "title": "...", "success_rate": 0.25, ...}, ...]
```

---

## Quick Implementation Guide

1. Copy source file: `cp agent_factory/rivet_pro/feedback_handler.py rivet/rivet_pro/feedback_handler.py`
2. Dependencies already installed (database_manager, kb_gap_logger)
3. Validate: `python -c "from rivet.rivet_pro.feedback_handler import process_feedback; print('OK')"`

---

## Validation

```bash
# Test import
python -c "from rivet.rivet_pro.feedback_handler import process_feedback, get_feedback_handler; print('OK')"

# Test with database (async)
python -c "
import asyncio
from rivet.rivet_pro.feedback_handler import process_feedback

async def test():
    result = await process_feedback(['test_atom'], 'positive')
    print(f'Triggered research: {result}')

asyncio.run(test())
"
```

---

## Integration Notes

**Telegram Bot Integration**:
```python
# In Telegram message handler after response sent
from rivet.rivet_pro.feedback_handler import process_feedback

async def handle_feedback_callback(callback_query):
    atom_ids = extract_atom_ids_from_response(response_text)
    feedback_type = "positive" if callback_query.data == "👍" else "negative"

    triggered = await process_feedback(atom_ids, feedback_type)

    if triggered:
        await callback_query.answer(f"Thanks! Triggered research for {len(triggered)} atoms.")
    else:
        await callback_query.answer("Thanks for your feedback!")
```

**Thresholds**:
- `LOW_QUALITY_THRESHOLD = 0.3` (30% success rate)
- `MIN_FEEDBACK_SAMPLES = 3` (minimum 3 feedback before triggering research)

**Atom ID Format**:
- Expected: `"vendor:equipment_type:topic"` (e.g., `"allen_bradley:controllogix:motor-control"`)
- Parsed to extract vendor, equipment_type, topic for gap request

**Research Trigger**:
- Priority score: 80 (HIGH)
- Route: "FEEDBACK_TRIGGERED"
- Enrichment type: "feedback_improvement"
- Weakness type: "low_user_satisfaction"

**Async Operations**:
- All database operations wrapped in `asyncio.to_thread()` for thread safety
- Returns list of atom IDs that triggered research

---

## What This Enables

- ✅ Self-improving knowledge base (user feedback → automatic research)
- ✅ Automatic quality monitoring (track success_rate per atom)
- ✅ User satisfaction tracking (positive/negative counters)
- ✅ Admin dashboard for low-quality atoms (prioritize improvements)
- ✅ Intelligent research triggering (only after 3+ feedback samples)
- ✅ Atom usage analytics (usage_count increment on every feedback)
- ✅ Graceful error handling (failed feedback doesn't crash system)

---

## Next Steps

After implementing HARVEST 12, proceed to **HARVEST 13: Response Gap Filler** for autonomous gap detection and KB enrichment.

SEE FULL SOURCE: `agent_factory/rivet_pro/feedback_handler.py` (300 lines - copy as-is)
