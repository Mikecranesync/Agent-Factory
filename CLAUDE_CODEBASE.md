# Agent Factory - Technical Documentation

**Last Updated:** 2025-12-04
**Version:** 0.1.0
**Purpose:** Comprehensive codebase documentation for AI assistants and developers

---

## Table of Contents

1. [What This Project Does](#what-this-project-does)
2. [Architecture & File Structure](#architecture--file-structure)
3. [Code Patterns & Standards](#code-patterns--standards)
4. [How to Run & Test](#how-to-run--test)
5. [Key Implementation Details](#key-implementation-details)
6. [Development Workflow](#development-workflow)

---

## What This Project Does

### Overview

**Agent Factory** is a production-ready Python framework for creating specialized AI agents with dynamic tool assignment. Built on LangChain, it provides a flexible factory pattern that allows developers to create agents with custom capabilities without hardcoding tool assignments.

### Core Value Proposition

- **Dynamic Agent Creation**: Create agents programmatically with custom roles, system prompts, and tool sets
- **Tool Flexibility**: Mix and match tools from different categories (research, coding, custom)
- **Multi-LLM Support**: Switch between OpenAI, Anthropic (Claude), and Google (Gemini) seamlessly
- **Developer-First**: Includes interactive CLI for easy agent testing
- **Production Ready**: Proper error handling, memory management, and extensibility

### Target Use Cases

1. **Research Assistants**: Agents that search the web, access Wikipedia, gather information
2. **Coding Assistants**: Agents that read/write files, analyze code, perform Git operations
3. **Hybrid Agents**: Mix research and coding tools for versatile capabilities
4. **Custom Workflows**: Build domain-specific agents with custom tools

### Key Features

- **Factory Pattern**: Centralized agent creation with sensible defaults
- **Tool Registry**: Centralized tool management and categorization
- **Memory Management**: Built-in conversation history for multi-turn interactions
- **Interactive CLI**: Test agents conversationally with `agentcli chat`
- **Multiple Agent Types**: ReAct (sequential reasoning) and Structured Chat (conversations)

---

## Architecture & File Structure

### Project Layout

```
agent_factory/
├── core/
│   ├── __init__.py
│   └── agent_factory.py          # Main factory class (270 lines)
│
├── tools/
│   ├── __init__.py
│   ├── tool_registry.py          # Tool registration system (294 lines)
│   ├── research_tools.py         # Web search, Wikipedia tools (256 lines)
│   └── coding_tools.py           # File system, Git tools (411 lines)
│
├── agents/                       # Pre-configured agents (placeholder)
│   └── __init__.py
│
├── memory/                       # Memory management (placeholder)
│   └── __init__.py
│
├── config/                       # Configuration (placeholder)
│   └── __init__.py
│
├── examples/
│   ├── __init__.py
│   └── demo.py                   # Demonstration scripts (273 lines)
│
└── cli.py                        # Interactive CLI (450+ lines)
```

### Core Module Breakdown

#### 1. `core/agent_factory.py` - Agent Factory

**Purpose**: Centralized factory for creating agents with different configurations

**Key Classes**:
- `AgentFactory`: Main factory class with methods for agent creation

**Key Methods**:
```python
AgentFactory.__init__(default_llm_provider, default_model, default_temperature, verbose)
AgentFactory.create_agent(role, tools_list, system_prompt, agent_type, enable_memory, ...)
AgentFactory.create_research_agent(tools_list, system_prompt, **kwargs)
AgentFactory.create_coding_agent(tools_list, system_prompt, **kwargs)
AgentFactory._create_llm(provider, model, temperature, **kwargs)  # Private helper
```

**Agent Types Supported**:
- `AGENT_TYPE_REACT` = "react" - Sequential reasoning (for coding tasks)
- `AGENT_TYPE_STRUCTURED_CHAT` = "structured_chat" - Conversational (for research)

**LLM Providers Supported**:
- `LLM_OPENAI` = "openai" (default: gpt-4o)
- `LLM_ANTHROPIC` = "anthropic" (Claude models)
- `LLM_GOOGLE` = "google" (Gemini models)

**Dependencies**:
- LangChain Hub (for prompt templates)
- LangChain Agents (create_react_agent, create_structured_chat_agent)
- LangChain Memory (ConversationBufferMemory)
- Provider-specific imports (ChatOpenAI, ChatAnthropic, ChatGoogleGenerativeAI)

#### 2. `tools/research_tools.py` - Research Tools

**Purpose**: Web search, knowledge retrieval, and information gathering tools

**Tools Implemented** (all extend `BaseTool`):
1. **WikipediaSearchTool**: Search Wikipedia articles (no API key required)
2. **DuckDuckGoSearchTool**: Web search via DuckDuckGo (no API key required)
3. **TavilySearchTool**: AI-optimized web search (requires TAVILY_API_KEY)
4. **CurrentTimeTool**: Get current time in specified format

**Utility Functions**:
```python
get_research_tools(include_wikipedia, include_duckduckgo, include_tavily, include_time)
register_research_tools(registry)
```

**Error Handling**: Each tool gracefully handles missing packages and API keys

#### 3. `tools/coding_tools.py` - Coding Tools

**Purpose**: File system operations, code analysis, and version control

**Tools Implemented** (all extend `BaseTool`):
1. **ReadFileTool**: Read file contents with encoding handling
2. **WriteFileTool**: Write or append to files (creates directories as needed)
3. **ListDirectoryTool**: List directory contents with file/folder indicators
4. **GitStatusTool**: Check Git repository status (requires GitPython)
5. **FileSearchTool**: Search files by pattern with wildcard support

**Configuration**: All file tools accept `base_dir` parameter for path resolution

**Utility Functions**:
```python
get_coding_tools(include_read, include_write, include_list, include_git, include_search, base_dir)
register_coding_tools(registry, base_dir)
```

#### 4. `tools/tool_registry.py` - Tool Registry

**Purpose**: Centralized tool management, categorization, and discovery

**Key Classes**:
- `ToolRegistry`: Registry for managing LangChain tools

**Key Methods**:
```python
ToolRegistry.register(name, tool, category, description, requires_api_key, api_key_env_var)
ToolRegistry.register_class(name, tool_class, category, **init_kwargs)
ToolRegistry.get(name)
ToolRegistry.get_many(names)
ToolRegistry.get_by_category(category)
ToolRegistry.list_tools()
ToolRegistry.list_categories()
ToolRegistry.get_metadata(name)
```

**Global Functions**:
```python
get_global_registry()
register_tool(name, tool, category, **kwargs)
get_tool(name)
get_tools(names)
```

**Storage**: Uses three internal dictionaries:
- `_tools`: name → BaseTool instance
- `_categories`: category → list of tool names
- `_tool_metadata`: name → metadata dict

#### 5. `cli.py` - Interactive CLI

**Purpose**: User-friendly command-line interface for testing agents

**Key Classes**:
- `AgentREPL`: Interactive REPL for agent conversations

**Commands Available**:
- `agentcli chat [--agent research|coding] [--verbose]` - Start interactive session
- `agentcli list-agents` - List available agents
- `agentcli version` - Show version information

**REPL Commands** (inside interactive mode):
- `/help` - Show commands
- `/exit` - Exit CLI
- `/agent <name>` - Switch agent
- `/info` - Show agent configuration
- `/clear` - Clear screen
- `/tools` - List available tools
- `/history` - Show command history

**Technologies**:
- **Typer**: Modern CLI framework with type hints
- **Rich**: Terminal formatting and styling
- **prompt_toolkit**: Advanced REPL features (auto-completion, history)

#### 6. `examples/demo.py` - Demonstration Scripts

**Purpose**: Example usage of Agent Factory

**Functions**:
- `demo_research_agent()` - Demonstrates research capabilities
- `demo_coding_agent()` - Demonstrates file operations
- `demo_custom_agent()` - Shows mixed-tool agent
- `interactive_mode()` - Basic interactive loop
- `main()` - Entry point

**Features**:
- Shows tool loading
- Displays agent metadata
- Runs example queries
- Includes error handling
- ASCII-only output (Windows compatible)

---

## Code Patterns & Standards

### 1. Factory Pattern

**Implementation**: `AgentFactory` class provides factory methods for agent creation

**Benefits**:
- Encapsulates complex agent initialization
- Provides sensible defaults
- Allows configuration overrides
- Single source of truth for agent creation

**Example**:
```python
factory = AgentFactory(default_llm_provider="openai", verbose=True)
agent = factory.create_agent(role="Custom Agent", tools_list=[...], ...)
```

### 2. BaseTool Pattern

**All tools extend `BaseTool` from LangChain**:
```python
from langchain_core.tools import BaseTool
from langchain.pydantic_v1 import BaseModel, Field

class ToolInput(BaseModel):
    """Input schema with Pydantic validation"""
    param: str = Field(description="Parameter description")

class CustomTool(BaseTool):
    name = "tool_name"
    description = "What this tool does (for LLM to understand)"
    args_schema: Type[BaseModel] = ToolInput

    def _run(self, param: str) -> str:
        """Tool implementation"""
        return result
```

**Why This Pattern**:
- Type-safe input validation
- Consistent interface
- LangChain compatibility
- Easy to extend

### 3. LangChain Integration Patterns

**Agent Creation**:
```python
# 1. Pull prompt from LangChain Hub
prompt = hub.pull("hwchase17/react")

# 2. Create agent with prompt
agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)

# 3. Wrap in AgentExecutor
agent_executor = AgentExecutor.from_agent_and_tools(
    agent=agent,
    tools=tools,
    memory=memory,  # Optional
    verbose=True,
    handle_parsing_errors=True
)

# 4. Store metadata
agent_executor.metadata = {...}
```

**Memory Management**:
```python
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

# Add initial system message
memory.chat_memory.add_message(SystemMessage(content=system_prompt))
```

**Agent Invocation**:
```python
response = agent.invoke({"input": user_query})
output = response['output']
```

### 4. Error Handling Patterns

**Tool Error Handling** (try-except with graceful degradation):
```python
def _run(self, query: str) -> str:
    try:
        # Tool logic
        return result
    except ImportError:
        return "Package not installed. Install with: pip install package-name"
    except SpecificError as e:
        return f"Specific error occurred: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"
```

**Factory Error Handling** (validation + exceptions):
```python
# Validate inputs
if not tools_list:
    raise ValueError("tools_list cannot be empty")

# Validate agent type
if agent_type not in [self.AGENT_TYPE_REACT, self.AGENT_TYPE_STRUCTURED_CHAT]:
    raise ValueError(f"Unsupported agent type: {agent_type}")
```

### 5. Type Hints

**Comprehensive type annotations throughout**:
```python
from typing import List, Dict, Optional, Type, Union, Any

def create_agent(
    self,
    role: str,
    tools_list: List[Union[BaseTool, Any]],
    system_prompt: Optional[str] = None,
    agent_type: str = AGENT_TYPE_REACT,
    enable_memory: bool = True,
    **kwargs
) -> AgentExecutor:
    ...
```

**Benefits**:
- IDE auto-completion
- Type checking with mypy/pyright
- Self-documenting code
- Catch errors early

### 6. Documentation Standards

**Module Docstrings** (at file start):
```python
"""
Module Name: Purpose and functionality

This module provides X for Y purpose.
Additional details...
"""
```

**Class Docstrings**:
```python
class AgentFactory:
    """
    Brief description.

    Detailed explanation of what this class does,
    when to use it, and key capabilities.
    """
```

**Method Docstrings**:
```python
def create_agent(self, role: str, ...) -> AgentExecutor:
    """
    Brief description.

    Args:
        role: Description
        tools_list: Description
        ...

    Returns:
        AgentExecutor: Description

    Example:
        >>> factory = AgentFactory()
        >>> agent = factory.create_agent(...)
    """
```

### 7. Code Formatting Standards

**Configuration** (from `pyproject.toml`):

**Black** (code formatter):
```toml
[tool.black]
line-length = 100
target-version = ['py310']
```

**isort** (import sorting):
```toml
[tool.isort]
profile = "black"
line_length = 100
```

**Ruff** (linter):
```toml
[tool.ruff]
select = ['E', 'W', 'F', 'I', 'B', 'C4', 'ARG', 'SIM']
ignore = ['W291', 'W292', 'W293']
line-length = 100
```

**Pyright** (type checker):
```toml
[tool.pyright]
useLibraryCodeForTypes = true
exclude = [".cache", ".venv", "**/__pycache__"]
```

### 8. Import Organization

**Standard order**:
```python
# 1. Standard library imports
import os
from pathlib import Path
from typing import List, Optional

# 2. Third-party imports
from dotenv import load_dotenv
from langchain_core.tools import BaseTool

# 3. Local imports
from agent_factory.core.agent_factory import AgentFactory
```

### 9. Path Handling

**Always use `pathlib.Path`** (cross-platform):
```python
from pathlib import Path

# Resolve paths
full_path = Path(base_dir) / file_path
full_path = full_path.resolve()

# Check existence
if not full_path.exists():
    return "Error: File not found"
```

**sys.path modification** (for imports):
```python
# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
```

---

## How to Run & Test

### Installation

**Prerequisites**:
- Python 3.10 or 3.11 (3.12+ not supported)
- Poetry 2.x installed

**Steps**:
```bash
# 1. Clone repository
git clone https://github.com/Mikecranesync/Agent-Factory.git
cd Agent-Factory

# 2. Install dependencies
poetry sync

# 3. Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 4. Verify installation
poetry run agentcli version
```

### Running the Demo

**Full demo script**:
```bash
poetry run python agent_factory/examples/demo.py
```

**What it demonstrates**:
1. Research Agent with Wikipedia and DuckDuckGo
2. Coding Agent with file operations
3. Custom agent with mixed tools
4. Interactive chat mode (optional)

### Using the Interactive CLI

**Start chatting** (easiest way to test agents):
```bash
# Research agent (default)
poetry run agentcli chat

# Coding agent
poetry run agentcli chat --agent coding

# Verbose mode (see agent reasoning)
poetry run agentcli chat --verbose
```

**CLI Commands**:
```bash
# List available agents
poetry run agentcli list-agents

# Show version
poetry run agentcli version
```

**Inside interactive mode**:
- Type naturally to chat with the agent
- Use `/agent research` or `/agent coding` to switch
- Use `/tools` to see what the agent can do
- Use `/info` to see current configuration
- Use `/exit` or Ctrl+D to quit

### Testing Individual Components

**Test factory creation**:
```python
from agent_factory.core.agent_factory import AgentFactory

factory = AgentFactory()
print(factory)  # Should show default configuration
```

**Test tool loading**:
```python
from agent_factory.tools.research_tools import get_research_tools
from agent_factory.tools.coding_tools import get_coding_tools

research_tools = get_research_tools()
coding_tools = get_coding_tools()

print(f"Research tools: {len(research_tools)}")
print(f"Coding tools: {len(coding_tools)}")
```

**Test agent creation**:
```python
from dotenv import load_dotenv
load_dotenv()

factory = AgentFactory()
tools = get_research_tools()
agent = factory.create_research_agent(tools)

response = agent.invoke({"input": "What is 2+2?"})
print(response['output'])
```

### Development Workflow

**Format code**:
```bash
poetry run black agent_factory/
poetry run isort agent_factory/
```

**Lint code**:
```bash
poetry run ruff agent_factory/
```

**Run type checking** (requires mypy or pyright):
```bash
pyright agent_factory/
```

**Run tests** (when implemented):
```bash
poetry run pytest
```

---

## Key Implementation Details

### 1. Agent Types

**ReAct (Reasoning + Acting)**:
- **Use for**: Sequential tasks, file operations, code analysis
- **Prompt**: `hub.pull("hwchase17/react")`
- **Pattern**: Think → Act → Observe → Repeat
- **Best for**: Coding Agent

**Structured Chat**:
- **Use for**: Conversational tasks, research, Q&A
- **Prompt**: `hub.pull("hwchase17/structured-chat-agent")`
- **Pattern**: Natural conversation flow with tool access
- **Best for**: Research Agent

### 2. LLM Provider Abstraction

**Factory method handles provider switching**:
```python
def _create_llm(self, provider, model, temperature, **kwargs):
    if provider == "openai":
        return ChatOpenAI(model=model, temperature=temperature, **kwargs)
    elif provider == "anthropic":
        return ChatAnthropic(model=model, temperature=temperature, **kwargs)
    elif provider == "google":
        return ChatGoogleGenerativeAI(model=model, temperature=temperature, **kwargs)
```

**Default models**:
- OpenAI: `gpt-4o`
- Anthropic: `claude-3-opus-20240229`
- Google: `gemini-pro`

**API Keys** (from environment):
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GOOGLE_API_KEY`

### 3. Memory Management

**ConversationBufferMemory** (simple buffer):
```python
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)
```

**How it works**:
1. Stores all messages in memory
2. Passes full history to agent on each turn
3. Agent has context of entire conversation
4. Memory persists for agent executor lifetime

**Limitations**:
- No persistence between sessions
- Token usage grows with conversation length
- No summarization or compression

**Future improvements** (not yet implemented):
- ConversationSummaryMemory (compress long conversations)
- ConversationBufferWindowMemory (sliding window)
- VectorStore memory (semantic similarity)
- SQLite persistence (save/load sessions)

### 4. Tool Categories

**Research** (information gathering):
- Wikipedia search
- Web search (DuckDuckGo, Tavily)
- Current time

**Coding** (file operations):
- Read/write files
- List directories
- Search files by pattern
- Git status

**Utility** (general purpose):
- Current time
- (Extensible for more)

**Custom** (user-defined):
- Extend BaseTool
- Implement _run() method
- Register with factory

### 5. Environment Configuration

**Required**:
```env
OPENAI_API_KEY=sk-proj-...
```

**Optional**:
```env
ANTHROPIC_API_KEY=sk-ant-api03-...
GOOGLE_API_KEY=AIzaSy...
TAVILY_API_KEY=tvly-dev-...
FIRECRAWL_API_KEY=fc-...
```

**Loading**:
```python
from dotenv import load_dotenv
load_dotenv()  # Loads from .env file
```

### 6. Dependencies

**Core** (required):
- `langchain ^0.2.1` - Framework foundation
- `langchain-openai ^0.1.8` - OpenAI integration
- `langchain-community ^0.2.1` - Community tools
- `langchainhub ^0.1.18` - Prompt templates
- `python-dotenv ^1.0.1` - Environment variables

**LLM Providers**:
- `langchain-anthropic ^0.1.15` - Claude models
- `langchain-google-genai ^1.0.5` - Gemini models
- `tiktoken ^0.7.0` - Token counting

**Tools**:
- `wikipedia ^1.4.0` - Wikipedia search
- `duckduckgo-search ^4.1.0` - Web search
- `tavily-python ^0.3.3` - AI search (optional)
- `gitpython ^3.1.40` - Git operations

**CLI**:
- `typer ^0.12.0` - CLI framework
- `prompt-toolkit ^3.0.43` - REPL features
- `rich ^13.7.0` - Terminal formatting

**Utilities**:
- `tenacity ^8.2.3` - Retry logic
- `pydantic ^2.5.0` - Data validation

**Development**:
- `pytest ^7.4.3` - Testing
- `black ^23.12.0` - Code formatting
- `isort ^5.13.0` - Import sorting
- `ruff ^0.1.8` - Linting

### 7. Poetry 2.x Configuration

**Key setting** (in `pyproject.toml`):
```toml
[tool.poetry]
package-mode = false  # This is an application, not a library
```

**Why this matters**:
- No longer need `--no-root` flag
- `poetry sync` just installs dependencies
- `poetry run` works correctly
- CLI scripts registered via `[tool.poetry.scripts]`

**CLI registration**:
```toml
[tool.poetry.scripts]
agentcli = "agent_factory.cli:app"
```

### 8. Windows Compatibility

**All Unicode characters replaced with ASCII**:
- `╔╗╚` → `+` (box drawing)
- `✓` → `[OK]` (checkmarks)
- `❌` → `[ERROR]` (errors)
- `⚠️` → `[WARNING]` (warnings)

**Path handling** (cross-platform):
```python
from pathlib import Path
path = Path("folder") / "file.txt"  # Works on Windows and Unix
```

**sys.path modification** (for imports):
```python
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
```

---

## Development Workflow

### Adding a New Tool

**1. Define input schema**:
```python
from langchain.pydantic_v1 import BaseModel, Field

class MyToolInput(BaseModel):
    param: str = Field(description="Description for LLM")
```

**2. Implement tool class**:
```python
from langchain_core.tools import BaseTool
from typing import Type

class MyCustomTool(BaseTool):
    name = "my_tool"
    description = "What this tool does (for LLM)"
    args_schema: Type[BaseModel] = MyToolInput

    def _run(self, param: str) -> str:
        try:
            # Tool logic here
            result = do_something(param)
            return f"Result: {result}"
        except Exception as e:
            return f"Error: {str(e)}"
```

**3. Register tool** (optional):
```python
def register_my_tools(registry):
    registry.register(
        "my_tool",
        MyCustomTool(),
        category="custom",
        description="Extended description"
    )
```

**4. Use tool**:
```python
tools = [MyCustomTool()]
agent = factory.create_agent(role="Custom Agent", tools_list=tools)
```

### Adding a New Agent Type

**1. Define agent configuration**:
```python
def create_my_agent(
    self,
    tools_list: List[BaseTool],
    system_prompt: Optional[str] = None,
    **kwargs
) -> AgentExecutor:
    """Create my specialized agent."""
    default_prompt = "You are a specialized agent that..."

    return self.create_agent(
        role="My Agent",
        tools_list=tools_list,
        system_prompt=system_prompt or default_prompt,
        agent_type=self.AGENT_TYPE_REACT,  # or STRUCTURED_CHAT
        **kwargs
    )
```

**2. Add to CLI** (optional):
```python
# In cli.py AgentREPL.AGENTS dict
AGENTS = {
    ...
    "myagent": {
        "name": "My Agent",
        "description": "What it does",
        "type": AgentFactory.AGENT_TYPE_REACT,
    }
}

# In load_agent() method
elif name == "myagent":
    tools = get_my_tools()
    self.current_agent = self.factory.create_my_agent(tools)
```

### Adding a New LLM Provider

**1. Install provider package**:
```bash
poetry add langchain-newprovider
```

**2. Add to factory constants**:
```python
class AgentFactory:
    LLM_NEWPROVIDER = "newprovider"
```

**3. Add to _create_llm() method**:
```python
def _create_llm(self, provider, model, temperature, **kwargs):
    ...
    elif provider == self.LLM_NEWPROVIDER:
        from langchain_newprovider import ChatNewProvider
        return ChatNewProvider(
            model=model,
            temperature=temperature,
            **kwargs
        )
```

**4. Set API key** (in `.env`):
```env
NEWPROVIDER_API_KEY=...
```

### Testing Changes

**1. Test locally**:
```bash
# Format code
poetry run black agent_factory/
poetry run isort agent_factory/

# Test CLI
poetry run agentcli chat

# Test demo
poetry run python agent_factory/examples/demo.py
```

**2. Add tests** (when test suite exists):
```python
# tests/test_my_feature.py
def test_my_tool():
    tool = MyCustomTool()
    result = tool._run("test input")
    assert "expected" in result
```

**3. Update documentation**:
- Add to README.md if user-facing
- Add to this CLAUDE_CODEBASE.md if technical
- Update CLI_USAGE.md if CLI-related

### Committing Changes

**Commit message format**:
```
type: brief description

Detailed explanation if needed.

- Bullet points for multiple changes
- Keep it concise but informative
```

**Types**:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation only
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance

**Example**:
```bash
git add agent_factory/tools/my_tool.py
git commit -m "feat: add custom tool for X

Implements MyCustomTool that does Y.
Includes error handling and documentation."
```

---

## Appendix

### File Line Counts

- `agent_factory/core/agent_factory.py`: 270 lines
- `agent_factory/tools/tool_registry.py`: 294 lines
- `agent_factory/tools/research_tools.py`: 256 lines
- `agent_factory/tools/coding_tools.py`: 411 lines
- `agent_factory/cli.py`: 450+ lines
- `agent_factory/examples/demo.py`: 273 lines

**Total Core Code**: ~1,954 lines

### Related Documentation

- `README.md` - User-facing documentation
- `QUICKSTART.md` - 5-minute setup guide
- `POETRY_GUIDE.md` - Poetry 2.x changes
- `HOW_TO_BUILD_AGENTS.md` - Step-by-step agent creation
- `CLI_USAGE.md` - Interactive CLI guide
- `CLAUDE.md` - API key analysis and security report
- `PROJECT_CONTEXT.md` - Project state and decisions
- `ISSUES_LOG.md` - Known issues and resolutions
- `DEVELOPMENT_LOG.md` - Development timeline
- `DECISIONS_LOG.md` - Technical decisions with rationale
- `NEXT_ACTIONS.md` - Roadmap and future tasks

### External References

- **LangChain Documentation**: https://docs.langchain.com/
- **LangChain Hub**: https://smith.langchain.com/hub
- **Original Inspiration**: https://github.com/Mikecranesync/langchain-crash-course
- **GitHub Repository**: https://github.com/Mikecranesync/Agent-Factory

---

**This document is intended for AI assistants (like Claude) and developers to quickly understand the codebase architecture, patterns, and how to work with the project.**
