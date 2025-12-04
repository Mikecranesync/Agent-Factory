# Decisions Log
> Record of key technical and design decisions
> **Format:** Newest decisions at top, with rationale and alternatives considered

---

## [2025-12-04 16:50] Memory System: Markdown Files Over MCP

**Decision:** Use markdown files with timestamps instead of MCP memory integration

**Rationale:**
- User explicitly concerned about token usage with MCP
- User wants chronological order with clear timestamps
- User wants no information mixing between files
- Markdown files are portable and human-readable
- Can be versioned in git for historical tracking

**Alternatives Considered:**
1. MCP Memory Integration
   - Pro: Native integration with Claude
   - Con: Token usage concerns
   - Con: Less transparent to user
   - **Rejected:** User explicit preference against

2. Single MEMORY.md File
   - Pro: Everything in one place
   - Con: Would become massive and mixed
   - Con: User explicitly wants separation
   - **Rejected:** User wants distinct files

**Files Created:**
- PROJECT_CONTEXT.md - Project state and overview
- ISSUES_LOG.md - Problems and solutions
- DEVELOPMENT_LOG.md - Activity timeline
- DECISIONS_LOG.md - Key choices (this file)
- NEXT_ACTIONS.md - Immediate tasks

**Format Standard:**
- `[YYYY-MM-DD HH:MM]` timestamp on every entry
- Newest entries at top (reverse chronological)
- Clear section separators (`---`)
- No mixing of different types of information

---

## [2025-12-04 15:30] Repository Visibility: Public

**Decision:** Created Agent Factory as a public GitHub repository

**Rationale:**
- Educational framework meant for community use
- MIT license encourages open sharing
- No proprietary code or secrets
- Facilitates collaboration and feedback
- Builds portfolio for creator

**Security Measures:**
- .env file properly gitignored
- .env.example provided as template
- No actual API keys committed
- Documentation warns about secret management

**Repository URL:** https://github.com/Mikecranesync/Agent-Factory

---

## [2025-12-04 14:30] API Key Storage: .env File

**Decision:** Use .env file for API key management

**Rationale:**
- Industry standard for local development
- python-dotenv library well-supported
- Easy to gitignore (security)
- Simple for users to configure
- Matches langchain-crash-course pattern

**Alternatives Considered:**
1. Environment Variables Only
   - Pro: More secure (no file)
   - Con: Harder for beginners to configure
   - Con: Not persistent across sessions on Windows
   - **Rejected:** Less user-friendly

2. Config File (JSON/YAML)
   - Pro: More structured
   - Con: Overkill for simple key storage
   - Con: Still needs gitignore
   - **Rejected:** Unnecessary complexity

**Implementation:**
```python
from dotenv import load_dotenv
load_dotenv()  # Loads .env automatically
```

**Security Documentation:** Created claude.md with API key security checklist

---

## [2025-12-04 14:00] Poetry Configuration: package-mode = false

**Decision:** Set `package-mode = false` in pyproject.toml

**Rationale:**
- Agent Factory is an application/framework, not a library package
- Won't be published to PyPI
- Poetry 2.x requires explicit declaration
- Eliminates need for `--no-root` flag
- Prevents confusion about package vs application

**Poetry 2.x Change:**
```toml
[tool.poetry]
name = "agent-factory"
version = "0.1.0"
package-mode = false  # New in Poetry 2.x
```

**Impact:**
- `poetry sync` installs dependencies only (no local package)
- `poetry run` works correctly
- No need for `poetry install --no-root`

**Documentation:** Created POETRY_GUIDE.md explaining this change

---

## [2025-12-04 13:45] LangGraph Inclusion (Currently Causing Issues)

**Decision:** Added langgraph ^0.0.26 to dependencies for future multi-agent orchestration

**Rationale:**
- Enables advanced agent coordination patterns
- Part of LangChain ecosystem
- Future-proofing for multi-agent workflows
- Seen in langchain-crash-course repository

**Current Status:** ⚠️ **CAUSING CRITICAL DEPENDENCY CONFLICT**

**Problem:**
```
langgraph (0.0.26) requires langchain-core (>=0.1.25,<0.2.0)
langchain (0.2.1) requires langchain-core (>=0.2.0,<0.3.0)
```

**Proposed Resolution:** Remove langgraph temporarily
- Not currently used in any code
- Can be added back when versions align
- Unblocks user installation

**Status:** Awaiting implementation of fix

---

## [2025-12-04 13:30] Tool Pattern: BaseTool Class

**Decision:** Use BaseTool class pattern for all tools

**Rationale:**
- Most flexible for factory pattern
- Type-safe input validation with Pydantic
- Consistent interface across all tools
- Easy to extend and customize
- Supports complex tool logic

**Pattern:**
```python
from langchain_core.tools import BaseTool
from langchain.pydantic_v1 import BaseModel, Field

class ToolInput(BaseModel):
    param: str = Field(description="Parameter description")

class CustomTool(BaseTool):
    name = "tool_name"
    description = "Tool description for LLM"
    args_schema: Type[BaseModel] = ToolInput

    def _run(self, param: str) -> str:
        # Tool logic here
        return result
```

**Alternatives Considered:**
1. Tool Constructor Pattern
   ```python
   Tool(name="tool_name", func=function, description="desc")
   ```
   - Pro: Simpler for basic tools
   - Con: Less type safety
   - Con: Harder to add configuration
   - **Rejected:** Less scalable

2. @tool() Decorator Pattern
   ```python
   @tool
   def my_tool(input: str) -> str:
       return result
   ```
   - Pro: Very concise
   - Con: Limited customization
   - Con: No instance variables
   - **Rejected:** Not flexible enough for factory

**Implementation:** All 10 tools use BaseTool class

---

## [2025-12-04 13:15] Agent Types: ReAct vs Structured Chat

**Decision:** Support both ReAct and Structured Chat agent types

**Rationale:**
- Different tasks need different patterns
- ReAct: Better for sequential reasoning (coding tasks)
- Structured Chat: Better for conversations (research tasks)
- User can choose based on use case

**Implementation:**
```python
AgentFactory.AGENT_TYPE_REACT = "react"
AgentFactory.AGENT_TYPE_STRUCTURED_CHAT = "structured_chat"
```

**Prompts:**
- ReAct: `hub.pull("hwchase17/react")`
- Structured Chat: `hub.pull("hwchase17/structured-chat-agent")`

**Pre-configured Agents:**
- Research Agent: Uses Structured Chat (conversations)
- Coding Agent: Uses ReAct (sequential file operations)

**Why Not OpenAI Functions?**
- Not provider-agnostic (OpenAI-specific)
- ReAct and Structured Chat work with all LLM providers
- More flexibility for future expansion

---

## [2025-12-04 13:00] LLM Provider Abstraction

**Decision:** Support multiple LLM providers (OpenAI, Anthropic, Google) with unified interface

**Rationale:**
- Provider-agnostic design
- Users can choose based on cost/features
- Fallback options if one provider is down
- Educational: Shows how to work with multiple LLMs

**Implementation:**
```python
def _create_llm(self, provider, model, temperature):
    if provider == "openai":
        return ChatOpenAI(model=model, temperature=temperature)
    elif provider == "anthropic":
        return ChatAnthropic(model=model, temperature=temperature)
    elif provider == "google":
        return ChatGoogleGenerativeAI(model=model, temperature=temperature)
```

**Default:** OpenAI GPT-4o
- Most accessible (widely available)
- Best documented
- Used in langchain-crash-course examples
- Good balance of cost/performance

**API Keys Required:** All 3 providers configured in .env

---

## [2025-12-04 12:30] Memory Management: Optional with Default Enabled

**Decision:** Make memory optional but enable by default

**Rationale:**
- Most use cases benefit from conversation history
- Users can disable for stateless agents
- Explicit control via `enable_memory` parameter
- System prompt stored in memory for context

**Implementation:**
```python
if enable_memory:
    memory = ConversationBufferMemory(
        memory_key=memory_key,
        return_messages=True
    )
    if system_prompt:
        memory.chat_memory.add_message(
            SystemMessage(content=f"{system_prompt}\n\nRole: {role}")
        )
```

**Memory Type:** ConversationBufferMemory
- Simplest to understand
- Stores full conversation
- Good for demos and learning

**Future Expansion:** Could add ConversationSummaryMemory, ConversationBufferWindowMemory

---

## [2025-12-04 12:00] Tool Organization: Category-Based Registry

**Decision:** Implement ToolRegistry with category-based organization

**Rationale:**
- Centralized tool management
- Easy to query tools by category
- Supports dynamic tool discovery
- Scalable for large tool collections
- Clear separation of concerns

**Categories Implemented:**
- "research": Wikipedia, DuckDuckGo, Tavily, CurrentTime
- "coding": ReadFile, WriteFile, ListDirectory, GitStatus, FileSearch

**Helper Functions:**
```python
get_research_tools(include_wikipedia=True, include_duckduckgo=True, include_tavily=False)
get_coding_tools(base_dir=".")
```

**Why Not Flat List?**
- Harder to manage as tools grow
- No logical grouping
- Difficult to enable/disable sets of tools
- **Rejected:** Not scalable

---

## [2025-12-04 11:30] Project Structure: Package-Based Architecture

**Decision:** Organize as Python package with clear module separation

**Structure:**
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

**Rationale:**
- Clear separation of concerns
- Easy to navigate for beginners
- Matches langchain-crash-course structure
- Scalable for future additions
- Standard Python package layout

**Alternatives Considered:**
1. Flat Structure (all files in root)
   - Pro: Simpler for tiny projects
   - Con: Becomes messy quickly
   - **Rejected:** Not scalable

2. Feature-Based (by agent type)
   - Pro: Groups related code
   - Con: Duplicates common components
   - **Rejected:** Less reusable

---

## [2025-12-04 11:00] Core Design: Factory Pattern

**Decision:** Use Factory Pattern for agent creation

**Rationale:**
- User explicitly requested "AgentFactory" class
- Factory pattern perfect for dynamic object creation
- Encapsulates complex initialization logic
- Single point of configuration
- Easy to extend with new agent types

**Signature:**
```python
def create_agent(
    role: str,
    tools_list: List[Union[BaseTool, Any]],
    system_prompt: Optional[str] = None,
    agent_type: str = AGENT_TYPE_REACT,
    enable_memory: bool = True,
    llm_provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    **kwargs
) -> AgentExecutor:
```

**Key Features:**
- Tools as parameters (not hardcoded)
- Flexible configuration
- Sensible defaults
- Type hints for clarity

**Alternatives Considered:**
1. Builder Pattern
   - Pro: More explicit configuration
   - Con: More verbose
   - **Rejected:** Overkill for this use case

2. Direct Construction
   - Pro: No abstraction
   - Con: Repeats boilerplate
   - Con: Harder for beginners
   - **Rejected:** User requested factory

---

## Design Principles Established

### 1. Abstraction Over Hardcoding
**Principle:** Tools are variables, not hardcoded into agents
**Benefit:** Maximum flexibility, easy to reconfigure

### 2. Scalability First
**Principle:** Design for multiple agents and tools from day one
**Benefit:** Can loop through agent definitions, grow without refactoring

### 3. Provider Agnostic
**Principle:** Work with any LLM provider
**Benefit:** No vendor lock-in, cost optimization

### 4. Educational Focus
**Principle:** Code should be readable and well-documented
**Benefit:** Users learn patterns, not just use library

### 5. Sensible Defaults
**Principle:** Works out of the box, configurable when needed
**Benefit:** Beginner-friendly, expert-capable

---

**Last Updated:** 2025-12-04 16:50
**Next Entry:** Will be added above this line

