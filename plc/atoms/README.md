# PLC Atoms

Validated PLC knowledge atoms conforming to PLC_ATOM_SPEC.md v0.1.

## Subdirectories

- `concepts/` - Fundamental PLC concepts (scan cycle, timers, counters)
- `patterns/` - Reusable code patterns (motor control, state machines, sequencing)
- `faults/` - Error codes and diagnostic procedures
- `procedures/` - Step-by-step guides (commissioning, testing, maintenance)

## File Naming Convention

```
{atom_type}/{vendor}/{slug}.json

Examples:
- patterns/allen_bradley/motor-start-stop-seal.json
- concepts/generic/scan-cycle-fundamentals.json
- faults/siemens/watchdog-timeout-s7-1200.json
- procedures/siemens/s7-1200-initial-startup.json
```

## Atom Lifecycle

1. **Draft** - Created from chunks, not yet validated
2. **Validated** - Passed JSON Schema validation, safety checks
3. **Tested on Hardware** - Verified on actual PLC (Siemens S7-1200, AB ControlLogix)
4. **Certified** - Community-validated, production-ready

## Validation Process

```
chunk → atom extraction → JSON Schema validation → safety check → hardware test → certified
```

Handled by:
- **Agent 3:** Atom Validator (JSON Schema, safety requirements)
- **Agent 4:** Atom Publisher (push to Supabase after validation)
- **Agent 5:** Duplicate Detector (merge near-duplicates)

## Example Atom

See `docs/PLC_ATOM_SPEC.md` for complete examples of all 4 atom types.
