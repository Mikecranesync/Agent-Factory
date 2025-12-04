# Project Context
> Quick reference for what this project is and its current state
> **Format:** Newest updates at top, timestamped entries

---

## [2025-12-04 16:50] Current Status

**Project Name:** Agent Factory
**Type:** Python Framework (Application, not library)
**Purpose:** Dynamic AI agent creation with pluggable tool system
**GitHub:** https://github.com/Mikecranesync/Agent-Factory
**Local Path:** `C:\Users\hharp\OneDrive\Desktop\Agent Factory`

**Status:** ⚠️ **Dependency Issue - Installation Blocked**

---

## [2025-12-04 15:30] Repository Published

Agent Factory successfully published to GitHub:
- Repository created as public
- Initial commit with 22 files
- Topics added: langchain, ai-agents, llm, python, poetry, openai, agent-framework
- Comprehensive documentation included
- All API keys safely excluded from git

---

## [2025-12-04 14:00] Project Created

### What Is Agent Factory?

A scalable framework for creating specialized AI agents with dynamic tool assignment. Instead of hardcoding tools into agents, users can mix and match capabilities on demand.

### Core Features

1. **Dynamic Agent Creation**
   - `create_agent(role, system_prompt, tools_list)` - Main factory method
   - Pre-built agents: Research Agent, Coding Agent
   - Custom agent configurations

2. **Pluggable Tool System**
   - Research Tools: Wikipedia, DuckDuckGo, Tavily
   - Coding Tools: File operations, Git, directory listing
   - Tool Registry for centralized management

3. **Multiple LLM Providers**
   - OpenAI (GPT-4o) - Primary
   - Anthropic (Claude 3)
   - Google (Gemini)

4. **Built-in Memory**
   - Conversation history tracking
   - Multi-turn interactions
   - Context preservation

### Technology Stack

```
Python 3.10-3.11
Poetry 2.x (dependency management)
LangChain 0.2.1 (core framework)
OpenAI, Anthropic, Google APIs
```

### Project Structure

```
agent_factory/
├── core/              # AgentFactory main class
├── tools/             # Research & coding tools
│   ├── research_tools.py
│   ├── coding_tools.py
│   └── tool_registry.py
├── agents/            # Pre-configured agents
├── examples/          # Demo scripts
└── memory/            # Memory management
```

### API Keys Configured

✅ OpenAI (GPT-4o) - Primary provider
✅ Anthropic (Claude 3) - Alternative
✅ Google (Gemini) - Alternative
✅ Firecrawl - Web scraping (optional)
✅ Tavily - AI search (optional)

All keys stored in `.env` (gitignored)

---

## Documentation Files

- `README.md` - Comprehensive documentation
- `QUICKSTART.md` - 5-minute setup guide
- `POETRY_GUIDE.md` - Poetry 2.x changes explained
- `HOW_TO_BUILD_AGENTS.md` - Step-by-step agent creation guide
- `claude.md` - API key analysis and security report
- `LICENSE` - MIT License

---

## Key Design Decisions

1. **Poetry 2.x Configuration**
   - `package-mode = false` - Application, not a library
   - No `--no-root` flag needed

2. **Tool Architecture**
   - BaseTool class pattern for maximum flexibility
   - Tool registry for centralized management
   - Category-based organization

3. **Agent Types**
   - ReAct: For sequential reasoning (coding tasks)
   - Structured Chat: For conversations (research tasks)

4. **No Hardcoded Tools**
   - Tools are variables passed to factory
   - Easy to add/remove capabilities
   - Scalable for multiple agent instances

---

## Original Inspiration

Based on patterns from: https://github.com/Mikecranesync/langchain-crash-course
Licensed under MIT (same as this project)

---

**Last Updated:** 2025-12-04 16:50
**Maintainer:** Mike Crane (Mikecranesync)
