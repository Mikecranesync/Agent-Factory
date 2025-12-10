<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Create a md file that tells claude code cli the plan

Here’s a `PLAN.md` you can drop into your repo and point Claude Code CLI at as the high‑level plan.

```markdown
# PLC Tutor & Agentic PLC Programmer – Plan

## Vision

Build a vertical AI system that:

- Teaches Allen‑Bradley and Siemens PLC programming from first principles using a PLC Tutor agent.
- Structures all PLC knowledge into reusable “atoms” (smallest structured units of PLC knowledge).
- Evolves into an autonomous PLC programming assistant that can generate and verify PLC logic via specs and, later, computer-use with vendor IDEs.
- Produces monetizable assets: SaaS tutor/assistant, DAAS knowledge base, and PLC training content (courses + YouTube).

Claude Code CLI should treat this file as the top‑level roadmap.

---

## Phase 0: Groundwork

### Goals

- Pick initial PLC platform and narrow scope.
- Define the PLC Atom Specification v0.1.
- Set up the basic repo structure for knowledge, atoms, and agents.

### Tasks

- Choose initial platform: **Siemens S7‑1200** or **Allen‑Bradley** (one only for v0).
- Create folders:
  - `/sources` – manuals, PDFs, transcripts.
  - `/chunks` – cleaned and tagged text snippets.
  - `/atoms` – JSON/YAML atoms following our schema.
  - `/agents` – configs/specs for our internal agents.
  - `/tutor` – PLC Tutor-specific prompts/configs.
- Add `ATOM_SPEC.md` describing the atom schema (see below).

---

## Phase 1: PLC Atom Specification v0.1

### Goal

Define the schema that all PLC knowledge must conform to. This is our internal “standard model” of PLC knowledge.

### Atom schema (conceptual)

Each atom is a JSON/YAML object with at least:

- `atom_id`: string (unique)
- `type`: enum (`concept`, `pattern`, `fault`, `procedure`)
- `vendor`: enum (`siemens`, `allen_bradley`, `generic`)
- `platform`: string (e.g., `s7-1200`, `control_logix`)
- `title`: short human-readable name
- `summary`: concise explanation

Domain fields:

- `inputs`: list (tags/addresses, conditions, prerequisites)
- `outputs`: list (coils/variables, expected effects)
- `logic_description`: structured description of the logic or concept
- `steps`: ordered steps (for procedures/patterns)
- `constraints`: safety notes, when NOT to use this pattern

Metadata:

- `difficulty`: enum (`beginner`, `intermediate`, `advanced`)
- `prereqs`: list of `atom_id` that should be understood first
- `source`: manual/tutorial/original notes
- `last_reviewed_by`: string
- `last_reviewed_at`: ISO timestamp

### Tasks for Claude

- Generate `ATOM_SPEC.md` with the above schema formalized:
  - Types, required vs optional fields, examples.
- Create a minimal JSON Schema or Pydantic model for atoms in `/atoms/schema`.

---

## Phase 2: KB Ingestion Pipeline (Research & Atom Builder)

### Goal

Ingest a small set of high‑quality PLC docs and turn them into the first atoms.

### Agents (as code/config, not products)

1. **PLC Research & Ingestion Agent**
   - Input: PDFs, HTML, transcripts placed in `/sources`.
   - Output: cleaned, tagged text in `/chunks`.
   - Responsibilities:
     - Chunk into logical sections (concepts, instructions, examples).
     - Tag chunks with `vendor`, `platform`, `topic`, `difficulty`.

2. **PLC Atom Builder Agent**
   - Input: tagged chunks + atom schema.
   - Output: draft atoms in `/atoms`.
   - Responsibilities:
     - Map chunks into the atom schema.
     - Propose `type`, `title`, `summary`, `inputs`, `outputs`, `logic_description`, `steps`, `constraints`.
     - Write initial 5–10 atoms for core basics:
       - PLC basics / scan cycle (concept)
       - Digital input concept (concept)
       - Digital output / coil (concept)
       - Start/stop/seal-in motor pattern (pattern)
       - TON timer basics (concept/pattern)

### Tasks for Claude

- Implement simple ingestion scripts or agent configs to:
  - Convert example PDFs/HTML into cleaned markdown/text in `/chunks`.
  - For 5–10 chunks, generate atoms and write them to `/atoms/*.json` using the schema.

---

## Phase 3: Atom Librarian & Indexing

### Goal

Organize atoms so the tutor can reliably query them.

### Atom Librarian responsibilities

- Maintain an index file (e.g., `/atoms/index.json` or a SQLite DB) with:
  - `atom_id`, `vendor`, `platform`, `topic`, `difficulty`, `type`, `prereqs`.
- Expose query functions:
  - `get_atoms_by_tag(...)`
  - `get_atoms_for_lesson(lesson_id)`
- Enforce versioning:
  - `version` field for each atom.
  - Mark deprecated atoms.

### Tasks for Claude

- Create a simple indexing script and data model:
  - E.g., Python module in `/atoms/indexer.py`.
- Generate initial index from v0 atoms.

---

## Phase 4: PLC Tutor v0.1 (Siemens or AB)

### Goal

Create a minimal PLC Tutor agent that uses the atom KB to teach Lessons 1–2.

### Scope

- Lesson 1: What is a PLC, digital I/O, basic ladder rung.
- Lesson 2: Start/stop/seal-in motor control pattern.

### Tutor behavior

- Uses only the atom KB (no hallucinated external content).
- For each lesson:
  - Explains relevant concepts using `concept` atoms.
  - Walks through one example using a `pattern` atom.
  - Asks 2–3 questions to check understanding.
  - Suggests one hands-on exercise on the real PLC.

### Tasks for Claude

- Create `/tutor/TUTOR_SPEC.md` describing:
  - Tutor goals and constraints.
  - Allowed tools (search atoms, retrieve lessons).
- Implement a simple tutor backend (can be CLI or minimal web):
  - Given `lesson_id`, it:
    - Retrieves mapped atoms.
    - Generates a sequence of messages/prompts for interactive tutoring (front-end-agnostic).
- Draft content for Lessons 1–2 using existing atoms.

---

## Phase 5: Workflow & Orchestration

### Goal

Add a minimal “Chief of Staff” agent to keep work organized.

### Chief of Staff responsibilities

- Maintain a simple roadmap: `ROADMAP.md`.
- Track:
  - Ingestion backlog (docs to ingest).
  - Atom backlog (concepts/patterns to atomize).
  - Tutor backlog (lessons to design).
- Provide short status summaries and next steps.

### Tasks for Claude

- Create `ROADMAP.md` with:
  - Current phase.
  - Open tasks.
  - “Next 7 days” milestones (updateable as we go).
- Optionally, add a small script/agent config that:
  - Scans the repo.
  - Updates lists of TODOs / open atoms / missing lessons.

---

## Immediate Next Actions for Claude Code CLI

1. **Create scaffolding files**
   - `ATOM_SPEC.md`
   - `ROADMAP.md`
   - `/atoms/schema` with a JSON Schema or Pydantic model.
   - `/atoms/indexer.py` (or similar) for indexing.

2. **Ingest initial docs**
   - Assume sample PLC docs will be placed in `/sources` manually.
   - Build a script to chunk and tag them into `/chunks`.

3. **Generate first atoms**
   - From 5–10 representative chunks, generate atoms and store in `/atoms`.

4. **Draft PLC Tutor spec**
   - Write `/tutor/TUTOR_SPEC.md` describing v0.1 tutor behavior and lesson structure for Lesson 1–2.

The overarching intent: always favor small, verifiable steps that convert raw PLC documentation and lab work into structured atoms, and then into a working PLC Tutor v0.1 that can teach the basics on one platform. Subsequent phases (autonomous PLC coder, computer-use integration, full YouTube/media automation) will build on this foundation.
```

