<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# reiterate in .md

Here’s a concise `.md` version you can drop into your repo as `docs/KNOWLEDGE_ATOM_EVAL_WORKFLOW.md` (then adapt paths as needed). Content and structure follow common LLM‑eval patterns and CLI workflows used in current tooling.[^1][^2]

```markdown
# Knowledge Atom Evaluation Workflow (CLI)

Purpose: Run a second LLM in the terminal as a **judge** over knowledge atoms, producing JSON scores and feedback so quality is measurable over time. [web:79]

---

## File Layout

Add these files:

- `docs/knowledge_atom_judge_prompt.md`  
- `scripts/knowledge/eval_atoms.py`  
- `scripts/knowledge/eval_atoms.sh`  
- Outputs (examples):  
  - `data/atoms-archon.json` → `data/atoms-archon-eval.json`  
  - `data/atoms-langchain.json` → `data/atoms-langchain-eval.json`  

This mirrors common LLM-evaluation setups that keep prompts, evaluators, and results versioned together. [web:81]

---

## Judge Prompt (`docs/knowledge_atom_judge_prompt.md`)

Describe the judge task and rubric:

- **Goal:** Evaluate a single “knowledge atom” JSON for reuse in future systems. [web:79]  
- **Criteria (1–5 each):**
  - Clarity  
  - Completeness  
  - Reusability  
  - Grounding/Correctness  

### Expected Judge Output (JSON)

```

{
"id": "archon-001",
"clarity_score": 1,
"clarity_notes": "",
"completeness_score": 1,
"completeness_notes": "",
"reusability_score": 1,
"reusability_notes": "",
"grounding_score": 1,
"grounding_notes": "",
"overall_score": 1,
"suggested_improvements": []
}

```

The judge LLM is instructed to respond **only** in this JSON format. [web:84]

---

## Core Evaluator Script (`scripts/knowledge/eval_atoms.py`)

Responsibilities:

1. Accept `--input` and `--output` paths.  
2. Load a list of atoms from the input JSON.  
3. For each atom:
   - Build a prompt using `knowledge_atom_judge_prompt.md` + the atom JSON.  
   - Call the chosen judge LLM (remote or local).  
   - Parse the JSON response.  
4. Write all evaluations as a JSON list to the output path. [web:85]

High-level structure:

```

import argparse, json, os
from typing import List, Dict

def call_judge_llm(atom: Dict) -> Dict:
\# 1) Compose prompt with rubric + atom JSON
\# 2) Call LLM API / local endpoint
\# 3) Parse JSON response and return it
raise NotImplementedError

def main():
parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        atoms: List[Dict] = json.load(f)
    
    evals: List[Dict] = []
    for atom in atoms:
        result = call_judge_llm(atom)
        evals.append(result)
    
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(evals, f, indent=2, ensure_ascii=False)
    if __name__ == "__main__":
main()

```

This pattern (loop + judge call + JSON outputs) is consistent with modern LLM evaluation frameworks. [web:81][web:79]

---

## Shell Wrapper and Make Targets

Wrapper script: `scripts/knowledge/eval_atoms.sh`

```

\#!/usr/bin/env bash
set -euo pipefail

INPUT="\$1"
OUTPUT="\$2"

python scripts/knowledge/eval_atoms.py --input "$INPUT" --output "$OUTPUT"

```

Make it executable:

```

chmod +x scripts/knowledge/eval_atoms.sh

```

`Makefile` targets:

```

eval-archon:
./scripts/knowledge/eval_atoms.sh data/atoms-archon.json data/atoms-archon-eval.json

eval-langchain:
./scripts/knowledge/eval_atoms.sh data/atoms-langchain.json data/atoms-langchain-eval.json

```

Usage:

- `make eval-archon`  
- `make eval-langchain`  

This gives a one-command way to re-run LLM quality checks as the atoms evolve. [web:75]

---

## Interpreting Results

From each `atoms-*-eval.json`:

- Track **overall_score** distribution per repo and over time.  
- Use `suggested_improvements` as a to-do list for rewriting weak atoms.  
- Consider your extraction process “healthy” when most new atoms land at 4–5 overall with only minor wording tweaks suggested. [web:84][web:79]
```

<div align="center">⁂</div>

[^1]: https://orq.ai/blog/multi-agent-llm-eval-system

[^2]: https://github.com/confident-ai/deepeval

