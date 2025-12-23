"""
Production-grade tracing with file logging + admin message output.

Provides RequestTrace class for tracking full request lifecycle:
- JSONL file logging (traces.jsonl, errors.jsonl)
- Admin Telegram messages with formatted trace
- Timing tracking for performance monitoring
- Error isolation for quick triage
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from logging.handlers import RotatingFileHandler
import uuid
import time

# Paths
LOG_DIR = Path("/root/Agent-Factory/logs")
TRACE_FILE = LOG_DIR / "traces.jsonl"
ERROR_FILE = LOG_DIR / "errors.jsonl"
METRICS_FILE = LOG_DIR / "metrics.jsonl"

LOG_DIR.mkdir(exist_ok=True)

# Rotating file handlers (10MB max, 5 backups)
trace_handler = RotatingFileHandler(TRACE_FILE, maxBytes=10_000_000, backupCount=5)
error_handler = RotatingFileHandler(ERROR_FILE, maxBytes=10_000_000, backupCount=5)


class RequestTrace:
    """Context manager for tracing a full request lifecycle."""

    def __init__(self, message_type: str, user_id: str, username: str = None, content: str = ""):
        self.request_id = str(uuid.uuid4())[:8]
        self.message_type = message_type
        self.user_id = user_id
        self.username = username
        self.content = content[:500]  # Truncate to 500 chars
        self.start_time = time.time()
        self.events = []
        self.timings = {}

    def event(self, event_type: str, **data):
        """Log an event in this request's lifecycle."""
        elapsed_ms = int((time.time() - self.start_time) * 1000)
        entry = {
            "request_id": self.request_id,
            "elapsed_ms": elapsed_ms,
            "event": event_type,
            **data
        }
        self.events.append(entry)
        self._write_log(entry)

    def timing(self, step: str, ms: int):
        """Record timing for a step."""
        self.timings[step] = ms

    def error(self, error_type: str, message: str, location: str):
        """Log an error."""
        entry = {
            "request_id": self.request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error_type": error_type,
            "message": message,
            "location": location,
            "user_id": self.user_id,
            "content": self.content
        }
        self._write_error(entry)
        self.events.append({"event": "ERROR", **entry})

    def _write_log(self, entry: dict):
        """Write trace log entry to JSONL file."""
        entry["timestamp"] = datetime.now(timezone.utc).isoformat()
        with open(TRACE_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def _write_error(self, entry: dict):
        """Write error log entry to JSONL file."""
        with open(ERROR_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def summary(self) -> dict:
        """Return summary for admin message."""
        total_ms = int((time.time() - self.start_time) * 1000)
        return {
            "request_id": self.request_id,
            "message_type": self.message_type,
            "user_id": self.user_id,
            "total_ms": total_ms,
            "timings": self.timings,
            "events": [e["event"] for e in self.events]
        }

    def format_admin_message(
        self,
        route: str,
        confidence: float,
        kb_atoms: int,
        llm_model: str = None,
        ocr_result: dict = None,
        kb_coverage: str = "none",
        error: str = None
    ) -> str:
        """Format the second message for admin."""
        total_ms = int((time.time() - self.start_time) * 1000)

        lines = ["```"]
        lines.append(f"TRACE [{self.request_id}]")
        lines.append("=" * 30)

        # Input section
        if self.message_type == "photo" and ocr_result:
            lines.append("PHOTO OCR")
            lines.append(f"  Manufacturer: {ocr_result.get('manufacturer', 'N/A')}")
            lines.append(f"  Model: {ocr_result.get('model', 'N/A')}")
            lines.append(f"  Fault Code: {ocr_result.get('fault_code', 'N/A')}")
            lines.append("")

        # Routing section
        lines.append("ROUTING")
        lines.append(f"  Route: {route}")
        lines.append(f"  Confidence: {confidence:.0%}")
        lines.append(f"  KB Coverage: {kb_coverage}")
        lines.append(f"  KB Atoms: {kb_atoms}")
        lines.append("")

        # LLM section
        if llm_model:
            lines.append("LLM")
            lines.append(f"  Model: {llm_model}")
            lines.append(f"  Cost: ${self.timings.get('llm_cost', 0):.4f}")
            lines.append("")

        # Timing section
        lines.append("TIMING")
        for step, ms in self.timings.items():
            if step != "llm_cost":
                lines.append(f"  {step}: {ms}ms")
        lines.append(f"  TOTAL: {total_ms}ms")
        lines.append("")

        # Error section
        if error:
            lines.append("ERROR")
            lines.append(f"  {error}")
            lines.append("")

        # Footer
        lines.append("=" * 30)
        lines.append(f"User: {self.user_id}")
        lines.append(f"Time: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}")
        lines.append("```")

        return "\n".join(lines)
