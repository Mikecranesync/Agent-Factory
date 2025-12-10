# PLC Utilities

Shared utility functions used across all PLC agents.

## Modules

### validation.py
Atom validation against PLC_ATOM_SPEC.md JSON Schema.

```python
from plc.utils.validation import validate_plc_atom

result = validate_plc_atom(atom)
if not result.valid:
    print(f"Validation errors: {result.errors}")
```

### embeddings.py
Vector embedding generation for semantic search.

```python
from plc.utils.embeddings import generate_embedding

embedding = generate_embedding(atom_text)  # Returns 3072-dim vector
```

### computer_use.py
PLC software automation (Cole Medin pattern).

```python
from plc.utils.computer_use import verify_ladder_logic

result = verify_ladder_logic(
    code=ladder_logic,
    platform="studio_5000",
    test_cases=[...]
)
# Returns: compilation status, I/O verification, screenshots
```

### safety.py
Safety requirement checking and validation.

```python
from plc.utils.safety import check_safety_requirements

issues = check_safety_requirements(atom)
if issues:
    print(f"Safety violations: {issues}")
```

## Installation

All utilities require dependencies from main `pyproject.toml`:
- openai (embeddings)
- playwright (computer-use)
- jsonschema (validation)
- supabase (database)
