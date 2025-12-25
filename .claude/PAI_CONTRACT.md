# PAI Contract - Agent Factory

## Core Guarantees

### What PAI Controls
- `.claude/` directory structure
- Skill routing and loading
- Hook system for automation
- History/UOCS documentation

### What Products Control
- `products/plc-tutor/` - PLC Tutor owns this
- `products/rivet-industrial/` - RIVET owns this
- `products/scaffold/` - Scaffold owns this
- `agent_factory/` - Core Python framework

### Protected Files (Never Auto-Modify)
- `.claude/settings.json`
- `.env` files
- `products/*/config/`

### Merge Rules
- Skills can be updated from upstream
- Product code requires explicit approval
- Hooks can be extended, not replaced
