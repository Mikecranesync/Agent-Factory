summarize these last few things that we talked about about GitHub and the importance of this automation loop into a document that either a human could code myself. I don't have any damn experience. definitely Clark could figure this out if I give it to him in a markdown file

GitHub and the Automation Loop – Design Notes for Agent Factory  
===============================================================

\## 1. GitHub’s role in the system

\- GitHub is the \*\*single external source of truth\*\* for:  
- All code (agents, orchestrator, media pipeline).  
- All schemas (`models.py` with `PLCAtom`, `VideoScript`, `UploadJob`, etc.).  
- All KB artifacts (`kb/atoms/\*.json`, `kb/courses/\*.json`).  
- All automation configs (`.github/workflows`, docs, scripts).\[1]\[2]\[3]  
- Any machine (you, Claude, CI, orchestrator server) can `git clone` / `git pull` and have the current architecture and knowledge available.

\## 2. Repo structure as the “factory layout”

Example layout Claude should assume and preserve:

```text  
agent-factory/  
├── models.py              # Pydantic models: PLCAtom, VideoScript, UploadJob, etc.  
├── kb/  
│   ├── atoms/             # JSON/YAML knowledge atoms  
│   └── courses/           # Module/Course definitions  
├── agents/  
│   ├── learning\_agent.py  # Factory I/O loop, codegen/refinement  
│   ├── content\_agent.py   # Turns atoms into lessons/scripts  
│   └── uploader\_agent.py  # Turns UploadJob into YouTube uploads  
├── media/  
│   ├── tts.py             # Voice clone / TTS  
│   └── video.py           # Faceless video assembly  
├── publish/  
│   └── youtube.py         # YouTube Data API client  
├── orchestrator.py        # Long-running loop that drives everything  
├── .github/  
│   └── workflows/         # (Optional) CI definitions  
└── docs/  
└── ai-rules.md        # Rules for AI collaborators  
```

Claude and humans should treat this layout as stable contracts. Changes to structure or models should be explicit and documented.\[4]\[5]\[3]

\## 3. Token minimization: external memory pattern

Goal: \*\*keep Claude prompts small\*\* by storing context in files/DB instead of in the prompt itself.\[6]\[7]\[8]\[9]

Rules:

\- All long-term state lives on disk / DB:  
- KB atoms, logs, design docs, to-do lists.  
- For each Claude call:  
- Only pass a short task description.  
- Include \*\*paths/IDs\*\* to relevant files, not the full file contents.  
- When necessary, load one file at a time into the prompt (e.g., `models.py`, a specific atom file).  
- For large artifacts (manuals, large logs):  
- Store full content in a file.  
- Maintain a short “summary + path” object (reversible summary) that Claude can read quickly and then open the full file when needed.\[6]\[10]\[8]

This treats the repo and DB as the system’s memory; Claude is only a \*\*stateless compute unit\*\* reading/writing those files.

\## 4. Automation without expensive GitHub Actions

Goal: \*\*use GitHub for code + events, but run compute on your own machine or cheap server\*\*.\[11]\[12]\[13]

Two layers:

\### 4.1 Trigger layer (GitHub / third-party)

\- GitHub sends webhooks on:  
- `push` (code changes merged).  
- Optionally `release`, `issue` events.  
- Webhook target:  
- A small HTTP service (FastAPI, Flask, etc.) on a VPS or local box with tunneling.  
- Alternatively, a third-party relay that forwards to your orchestrator endpoint.\[12]\[11]  
- The webhook handler:  
- Verifies signature.  
- Writes a simple job into a queue / DB / file, e.g.:  
```json  
{"type": "sync\_and\_generate\_content", "count": 3}  
```

GitHub itself does almost no work; it just tells your system “something changed” or “run now.”\[12]\[13]

\### 4.2 Orchestrator (24/7 Agent Factory loop)

\- A \*\*long-running Python process\*\* (e.g., `orchestrator.py`) on your own box or VPS.  
- Responsibilities:  
- Regularly `git pull` the repo (`main` branch) to stay current.  
- Read pending jobs from a queue/DB/file (written by webhooks or a timer).  
- For each job:  
- Run KB maintenance (new atoms, updates).  
- Run learning agent if needed (sim tasks, code refinement).  
- Run content agent (generate `VideoScript`).  
- Run media pipeline (generate `MediaAssets`).  
- Create `UploadJob` and call uploader agent (YouTube API).  
- Simple loop sketch:

```python  
# orchestrator.py  
import time  
from tasks import fetch\_new\_tasks, run\_task\_batch  
from git\_utils import sync\_repo

def main\_loop():  
while True:  
sync\_repo()              # git pull origin/main  
tasks = fetch\_new\_tasks()  
if tasks:  
run\_task\_batch(tasks)  # call agents and pipelines  
time.sleep(60)           # tick every 60s

if \_\_name\_\_ == "\_\_main\_\_":  
main\_loop()  
```

\- Keep it running via `systemd`, `supervisord`, or tmux. This gives you a \*\*24/7 Agent Factory\*\* without paying GitHub Actions minutes.\[12]\[13]\[14]

\## 5. Manual workflow a human can follow

If everything breaks and you have to operate it yourself:

1\. `git clone` the repo (or `git pull` to update).  
2. Edit KB atoms and code locally using the models in `models.py`.  
3. Run tests: `pytest` (or similar).  
4. Run orchestrator once: `python orchestrator.py` (or a smaller script like `python runner.py generate\_content`).  
5. Commit and push changes back to GitHub with clear messages.  
6. Let the always-on orchestrator box keep pulling and executing, or manually rerun as needed.

This is the same loop Claude should follow, just automated.

\## 6. Instructions for Claude Code CLI (to embed in docs)

You can paste something like this into `docs/ai-rules.md`:

\- Work only within the existing repo structure shown above.  
- Treat `models.py` and `kb/atoms/\*.json` as \*\*contracts\*\*; do not change them without updating docs and creating a clear commit/PR.  
- Never paste huge files into prompts. Instead:  
- Ask to open specific files (e.g., `models.py`, `kb/atoms/atom\_ohms\_law\_basic.json`).  
- Read, modify, and write back those files.  
- Keep prompts focused:  
- One task at a time (“implement orchestrator loop”, “add new PLCAtom”, etc.).  
- Use file paths and IDs instead of raw content where possible.  
- For automation:  
- Assume GitHub webhooks trigger lightweight events.  
- Assume a long-running `orchestrator.py` will process jobs regularly.  
- Write code so that `run\_task\_batch()` and `fetch\_new\_tasks()` are idempotent and safe to run often.

With this markdown, a human or Claude can reconstruct the GitHub-centric automation loop and the always-on Agent Factory orchestration without needing you to re-explain it.

Citations:  
\[1] Is Git a system designed for single source of truth? - Bojan Nikolic https://www.bnikolic.co.uk/blog/git/2024/03/04/git-truth.html  
\[2] Implementing single source of truth in an enterprise architecture https://www.redhat.com/en/blog/single-source-truth-architecture  
\[3] What are code repositories? - GitHub https://github.com/resources/articles/what-are-code-repositories  
\[4] Monorepo vs Multi-Repo AI: Architecture-based AI Tool Selection https://www.augmentcode.com/guides/monorepo-vs-multi-repo-ai-architecture-based-ai-tool-selection  
\[5] Document best practices for a monorepo · Issue #10960 · astral-sh/uv https://github.com/astral-sh/uv/issues/10960  
\[6] Token Budgeting Strategies for Long-Context LLM Apps https://dev.co/ai/token-budgeting-strategies-for-long-context-llm-apps  
\[7] Augmenting LLM Agents with Long-Term Memory - Rohan's Bytes https://www.rohan-paul.com/p/augmenting-llm-agents-with-long-term  
\[8] Deep Dive into Context Engineering for Agents - Galileo AI https://galileo.ai/blog/context-engineering-for-agents  
\[9] Memory-augmented agents - AWS Prescriptive Guidance https://docs.aws.amazon.com/prescriptive-guidance/latest/agentic-ai-patterns/memory-augmented-agents.html  
\[10] Reduce LLM Token Usage in RAG | Cost Savings https://apxml.com/courses/optimizing-rag-for-production/chapter-5-cost-optimization-production-rag/minimize-llm-token-usage-rag  
\[11] What is the best way to connect Github Actions to your own server to ... https://www.reddit.com/r/selfhosted/comments/1c5ic50/what\_is\_the\_best\_way\_to\_connect\_github\_actions\_to/  
\[12] Build and deploy locally using GitHub actions and Webhooks https://theawesomegarage.com/blog/build-and-deploy-locally-using-github-actions-and-webhooks  
\[13] How I deploy private GitHub projects to local self-hosted servers (CI ... https://blog.tymscar.com/posts/privategithubcicd/  
\[14] Continuous integration - GitHub Docs [https://docs.github.com/en/actions/get-started/continuous-integration](https://docs.github.com/en/actions/get-started/continuous-integration)

