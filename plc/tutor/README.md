# PLC Tutor Chatbot

User-facing chatbot for PLC learning and code generation.

## Features

- **Learning Assistant:** Answers questions about PLC concepts
- **Code Generator:** LLM4PLC pattern (spec → code → verify)
- **Troubleshooting Helper:** Diagnoses faults, suggests solutions
- **Learning Path Builder:** Constructs prerequisite chains

## Architecture

```
User Query → Query Router → Relevant Agent → Response Generator → User
```

### Query Router
- Classifies query intent (learning, code generation, troubleshooting)
- Routes to appropriate agent (Agent 6 for tutorials, Agent 7 for code gen)
- Returns confidence score

### Response Generator
- Combines atom content with LLM-generated explanation
- Adds citations to source atoms
- Formats code examples with syntax highlighting
- Includes safety warnings where applicable

## Deployment

- **Web:** Flask/FastAPI backend, React frontend
- **Discord:** Discord bot integration
- **Telegram:** Telegram bot integration
- **API:** REST API for B2B integrations

## Example Interaction

**User:** "How do I make a start/stop motor control in Allen-Bradley?"

**Chatbot:**
```
The standard pattern is a 3-wire start/stop/seal-in control:

[Shows ladder logic diagram from atom plc:ab:motor-start-stop-seal]

Key points:
- Start button (NO) in parallel with seal-in contact
- Stop button (NC) in series for fail-safe operation
- Auxiliary contact seals in after start button released

⚠️ Safety: Stop button MUST be normally-closed (NC) for fail-safe operation

Source: [Allen-Bradley ControlLogix Manual Chapter 3]
```

## LLM4PLC Code Generation

**User:** "Generate code for a conveyor with start/stop buttons and e-stop"

**Chatbot:**
```
[Agent 7: Code Generator runs spec → code → verify loop]

Generated Ladder Logic (Allen-Bradley ControlLogix):

[Shows complete ladder logic]

✅ Verified in Studio 5000 Emulate
✅ Tested I/O mapping
✅ Safety interlocks validated

Download: conveyor-control-v1.ACD
```
