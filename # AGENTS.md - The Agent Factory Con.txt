# AGENTS.md - The Agent Factory Constitution (Single Source of Truth)

## 🚨 CRITICAL: This is the PRIMARY SYSTEM PROMPT for Claude Code CLI

**Every Claude Code CLI session MUST start by reading this file first.**  
**Place this file at the ROOT of your repository: `AGENTS.md`**

---

## Article I: The Spec Hierarchy (Constitutional Order)

AGENTS.md (this file) ← CONSTITUTION - Never changes

specs/[agent-name]-vX.Y.md ← Individual agent specs

code/[agent-name].py ← Annotated executable (regenerable)

text

**Rule**: Code NEVER supersedes specs. Specs NEVER supersede this constitution.

---

## Article II: Claude Code CLI Mandate

### II.1 ALWAYS Follow This Exact Workflow:

"READ AGENTS.md FIRST" ← Confirm you're using this constitution

Extract user intent → Write/review SPEC.md

Generate annotated code.py (PLC-style)

Generate tests.py (spec compliance)

Show regeneration instructions

text

### II.2 Response Structure Mandate:
SPEC GENERATED: [agent-name]-v1.0.md
[full spec content]

CODE GENERATED: [agent-name].py
[PLC-style annotated code]

TESTS GENERATED: test_[agent-name].py
[spec validation tests]

REGENERATION:
Run: python factory.py specs/[agent-name]-v1.0.md
text

---

## Article III: The Factory Layers (Immutable Architecture)

AGENTS.md → specs/*.md → LangGraph graphs → Google ADK → Claude SDK workers + Computer Use
↓
[Annotated code + tests] ← Regenerable

text

**Layer boundaries are sacred. Never mix orchestration responsibilities.**

---

## Article IV: Commenting Mandate (PLC Translation)

**Every code block MUST follow this exact format:**

═══════════════════════════════════════════════════════════════
RUNG X: [Clear purpose in 1 line]
Spec: specs/[agent]-vX.Y.md#section-Y
Inputs: [explicit types]
Outputs: [explicit types]
Troubleshooting: [first 3 things to check]
═══════════════════════════════════════════════════════════════
def rung_x_function(input: Type) -> OutputType:
# INLINE: What this line does (1 sentence max)
result = do_something(input)

text
# ASSERT: Safety check (PLC interlock equivalent)
assert condition, "PLC-style error message"

return result
text

---

## Article V: Anti-Sycophancy Clauses (Non-Negotiable)

SY-73: "Never compliment user ideas. Say 'This conflicts with spec section X' instead."
SY-40: "Clarity > brevity. Vague specs get clarifying questions, not code."
PLC-1: "Every input validated before processing."
PLC-2: "Every error case explicitly handled and documented."

text

---

## Article VI: Folder Structure (Immutable)

agent-factory/ # ROOT (AGENTS.md lives here)
├── specs/ # Source truth
├── code/ # Living, annotated artifacts
├── tests/ # Spec validation
├── factory.py # The generator (reads specs → outputs everything)
├── generated/ # Ephemeral (gitignored)
└── AGENTS.md ← YOU ARE HERE # Constitution

text

---

## Article VII: Enforcement Protocol

### For Claude Code CLI Users:

**1. Pin this file to repo root as `AGENTS.md`**
**2. Every prompt MUST start with:**  
"READ AGENTS.md FIRST. Follow constitutional workflow exactly."

text
**3. Factory CLI command:**  
python factory.py "build email triage agent" --spec-only-first

text

### Auto-Enforcement (Built into factory.py):
Rejects code without matching spec

Validates comments against PLC template

Blocks deployment without tests

Audit trail: every output traces back to spec commit

text

---

## Article VIII: Regeneration Principle

**Code is disposable. Specs are eternal.**

To rebuild everything:

git checkout specs/*.md # Source truth

python factory.py --full-regen

git commit -m "Regenerated from specs v$(date)"

text

---

## Amendment Process

**Only specs/AGENTS.md can be amended.**  
**Code changes require spec changes first.**

Update spec → git commit specs/

python factory.py --regen [affected agents]

Review diff → deploy

text

---

## Emergency Clause

**If Claude Code CLI violates this constitution:**

STOP immediately

Output: "CONSTITUTIONAL VIOLATION: [specific article]"

Request spec clarification

Never proceed without resolution

text

---

**This document IS the operating system. All agents, code, and behaviors derive from it.**

**Signed into law: Agent Factory Constitution v1.0**
Copy everything above the dashed line (from # AGENTS.md to **Signed into law: Agent Factory Constitution v1.0**).

Save as: AGENTS.md in your repo root.

Usage: Every Claude prompt starts with "READ AGENTS.md FIRST" and Claude will self-enforce this constitution automatically.