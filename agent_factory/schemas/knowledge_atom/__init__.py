"""
Industrial Maintenance Knowledge Atom Standard v1.0

This package contains the schema files for Knowledge Atoms:
- schema.json: JSON Schema (Draft 7) for validation
- context.jsonld: JSON-LD context for semantic meaning

Based on industry standards:
- Schema.org (45M+ domains)
- JSON-LD 1.1 (W3C Recommendation)
- JSON Schema Draft 7 (IETF)
- OpenAPI 3.1.0 (Linux Foundation)
"""

import json
import pathlib

# Package metadata
__version__ = "1.0.0"
__author__ = "Agent Factory"
__description__ = "Knowledge Atom Standard for Industrial Maintenance"

# Load schema and context
_SCHEMA_PATH = pathlib.Path(__file__).parent / "schema.json"
_CONTEXT_PATH = pathlib.Path(__file__).parent / "context.jsonld"

with open(_SCHEMA_PATH, "r") as f:
    KNOWLEDGE_ATOM_SCHEMA = json.load(f)

with open(_CONTEXT_PATH, "r") as f:
    KNOWLEDGE_ATOM_CONTEXT = json.load(f)

__all__ = [
    "KNOWLEDGE_ATOM_SCHEMA",
    "KNOWLEDGE_ATOM_CONTEXT",
    "__version__"
]
