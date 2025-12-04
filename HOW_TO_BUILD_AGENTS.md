# How to Build Agents with Agent Factory

A step-by-step guide to creating your own AI agents using Agent Factory.

---

## Quick Start: Your First Agent in 3 Minutes

### 1. Install and Setup

```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
poetry sync
```

### 2. Create a Simple Agent

Create a file called `my_first_agent.py`:

```python
from dotenv import load_dotenv
from agent_factory.core.agent_factory import AgentFactory
from agent_factory.tools.research_tools import get_research_tools

# Load API keys
load_dotenv()

# Create the factory
factory = AgentFactory()

# Get tools
tools = get_research_tools()

# Create agent
agent = factory.create_research_agent(tools)

# Use it!
response = agent.invoke({"input": "What is machine learning?"})
print(response['output'])
```

### 3. Run It

```bash
poetry run python my_first_agent.py
```

**That's it! You just created an AI agent.**

---

## The Three Ways to Build Agents

### Method 1: Pre-Built Agents (Easiest)

Use ready-made agents for common tasks.

#### Research Agent

```python
from agent_factory.core.agent_factory import AgentFactory
from agent_factory.tools.research_tools import get_research_tools

factory = AgentFactory()
tools = get_research_tools(
    include_wikipedia=True,
    include_duckduckgo=True,
    include_tavily=True  # If you have API key
)

agent = factory.create_research_agent(tools)

# Ask questions
response = agent.invoke({"input": "What is LangChain?"})
print(response['output'])
```

#### Coding Agent

```python
from agent_factory.tools.coding_tools import get_coding_tools

tools = get_coding_tools(base_dir=".")
agent = factory.create_coding_agent(tools)

# File operations
response = agent.invoke({"input": "List all Python files"})
print(response['output'])
```

---

### Method 2: Custom Agent with create_agent()

Build agents with specific configurations.

```python
from agent_factory.core.agent_factory import AgentFactory
from agent_factory.tools.research_tools import WikipediaSearchTool, CurrentTimeTool
from agent_factory.tools.coding_tools import ReadFileTool

# Create factory
factory = AgentFactory()

# Mix different tools
tools = [
    WikipediaSearchTool(),
    CurrentTimeTool(),
    ReadFileTool()
]

# Create custom agent
agent = factory.create_agent(
    role="Documentation Assistant",
    tools_list=tools,
    system_prompt="You help write and update documentation by researching topics and reading existing files.",
    agent_type=AgentFactory.AGENT_TYPE_STRUCTURED_CHAT,
    enable_memory=True
)

# Use it
response = agent.invoke({
    "input": "Read the README.md file and tell me what this project does"
})
print(response['output'])
```

---

### Method 3: Build Your Own Tool (Advanced)

Create custom tools for specific needs.

```python
from typing import Type
from langchain_core.tools import BaseTool
from langchain.pydantic_v1 import BaseModel, Field

# Step 1: Define input schema
class WeatherInput(BaseModel):
    city: str = Field(description="City name to get weather for")

# Step 2: Create tool class
class WeatherTool(BaseTool):
    name = "get_weather"
    description = "Get current weather for a city"
    args_schema: Type[BaseModel] = WeatherInput

    def _run(self, city: str) -> str:
        # Your logic here (could call weather API)
        return f"Weather in {city}: Sunny, 72°F"

# Step 3: Use your custom tool
from agent_factory.core.agent_factory import AgentFactory

factory = AgentFactory()
tools = [WeatherTool()]

agent = factory.create_agent(
    role="Weather Assistant",
    tools_list=tools,
    system_prompt="You help users check weather conditions."
)

response = agent.invoke({"input": "What's the weather in New York?"})
print(response['output'])
```

---

## Real-World Examples

### Example 1: Blog Writer Agent

```python
from dotenv import load_dotenv
from agent_factory.core.agent_factory import AgentFactory
from agent_factory.tools.research_tools import (
    WikipediaSearchTool,
    DuckDuckGoSearchTool
)
from agent_factory.tools.coding_tools import WriteFileTool

load_dotenv()

# Create tools
search_tool = DuckDuckGoSearchTool()
wiki_tool = WikipediaSearchTool()
write_tool = WriteFileTool()
write_tool.base_dir = "./blog_posts"

# Create agent
factory = AgentFactory()
agent = factory.create_agent(
    role="Blog Writer",
    tools_list=[search_tool, wiki_tool, write_tool],
    system_prompt="""You are a professional blog writer.
    Research topics thoroughly using web search and Wikipedia,
    then write engaging blog posts and save them to files.""",
    agent_type=AgentFactory.AGENT_TYPE_STRUCTURED_CHAT
)

# Use it
response = agent.invoke({
    "input": "Write a 500-word blog post about Python decorators and save it to python_decorators.md"
})
print(response['output'])
```

### Example 2: Code Review Agent

```python
from agent_factory.core.agent_factory import AgentFactory
from agent_factory.tools.coding_tools import (
    ReadFileTool,
    ListDirectoryTool,
    GitStatusTool
)

factory = AgentFactory()

# Code analysis tools
tools = [
    ReadFileTool(),
    ListDirectoryTool(),
    GitStatusTool()
]

agent = factory.create_agent(
    role="Code Reviewer",
    tools_list=tools,
    system_prompt="""You are an expert code reviewer.
    Analyze code for:
    - Best practices
    - Potential bugs
    - Performance issues
    - Security vulnerabilities
    Provide constructive feedback.""",
    agent_type=AgentFactory.AGENT_TYPE_REACT
)

# Review a file
response = agent.invoke({
    "input": "Review the code in agent_factory/core/agent_factory.py and provide feedback"
})
print(response['output'])
```

### Example 3: Research Assistant with Memory

```python
from agent_factory.core.agent_factory import AgentFactory
from agent_factory.tools.research_tools import get_research_tools

factory = AgentFactory()
tools = get_research_tools()

agent = factory.create_research_agent(
    tools_list=tools,
    enable_memory=True  # Remembers conversation
)

# Have a conversation
queries = [
    "What is quantum computing?",
    "Who are the leading researchers in this field?",
    "What did you tell me about quantum computing earlier?"  # Uses memory
]

for query in queries:
    print(f"\nUser: {query}")
    response = agent.invoke({"input": query})
    print(f"Agent: {response['output']}")
```

---

## Understanding Agent Configuration

### Agent Types

```python
# ReAct Agent (Reasoning + Action)
# Best for: Sequential tasks, file operations
agent = factory.create_agent(
    role="Task Executor",
    tools_list=tools,
    agent_type=AgentFactory.AGENT_TYPE_REACT
)

# Structured Chat Agent
# Best for: Conversations, complex tool usage
agent = factory.create_agent(
    role="Assistant",
    tools_list=tools,
    agent_type=AgentFactory.AGENT_TYPE_STRUCTURED_CHAT
)
```

### LLM Providers

```python
# Use OpenAI (default)
agent = factory.create_agent(
    role="Assistant",
    tools_list=tools,
    llm_provider="openai",
    model="gpt-4o"
)

# Use Claude
agent = factory.create_agent(
    role="Assistant",
    tools_list=tools,
    llm_provider="anthropic",
    model="claude-3-opus-20240229"
)

# Use Gemini
agent = factory.create_agent(
    role="Assistant",
    tools_list=tools,
    llm_provider="google",
    model="gemini-pro"
)
```

### Temperature Control

```python
# More creative (0.0 - 1.0)
agent = factory.create_agent(
    role="Creative Writer",
    tools_list=tools,
    temperature=0.9  # More random/creative
)

# More focused
agent = factory.create_agent(
    role="Code Analyzer",
    tools_list=tools,
    temperature=0.1  # More deterministic
)
```

---

## Interactive Chat Mode

Create a chatbot that remembers conversation:

```python
from dotenv import load_dotenv
from agent_factory.core.agent_factory import AgentFactory
from agent_factory.tools.research_tools import get_research_tools

load_dotenv()

# Setup
factory = AgentFactory(verbose=False)
tools = get_research_tools()
agent = factory.create_research_agent(tools, enable_memory=True)

# Chat loop
print("Chat with your agent (type 'exit' to quit):")
while True:
    user_input = input("\nYou: ").strip()

    if user_input.lower() == 'exit':
        break

    if not user_input:
        continue

    response = agent.invoke({"input": user_input})
    print(f"Agent: {response['output']}")
```

---

## Troubleshooting

### "No module named 'agent_factory'"

```bash
# Make sure you're using poetry run
poetry run python your_script.py

# Or activate the environment
source $(poetry env info --path)/bin/activate  # Unix/Mac
# Then run: python your_script.py
```

### "Invalid API key"

Check your `.env` file:
```bash
# Make sure this line exists without "ADD_KEY_HERE"
OPENAI_API_KEY=sk-proj-your-actual-key-here
```

### "Rate limit exceeded"

Add retry logic:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def call_agent(agent, input_text):
    return agent.invoke({"input": input_text})

# Use it
response = call_agent(agent, "Your question here")
```

### Agent not using tools

Make sure tools are appropriate for the task:
```python
# Bad: Asking about files with only search tools
tools = [WikipediaSearchTool()]  # No file tools!
agent = factory.create_agent(role="Assistant", tools_list=tools)
agent.invoke({"input": "Read my file.txt"})  # Won't work

# Good: Provide file tools
tools = [ReadFileTool()]
agent = factory.create_agent(role="Assistant", tools_list=tools)
agent.invoke({"input": "Read my file.txt"})  # Will work
```

---

## Best Practices

### 1. Start Simple

```python
# Good: Start with one task
tools = [WikipediaSearchTool()]
agent = factory.create_research_agent(tools)

# Less good: Too many tools at once
tools = get_research_tools() + get_coding_tools()  # Overwhelming
```

### 2. Clear System Prompts

```python
# Good: Specific instructions
system_prompt = "You are a Python expert. When reviewing code, focus on PEP 8 compliance and performance."

# Less good: Vague
system_prompt = "You help with code."
```

### 3. Test with Simple Queries First

```python
# Test basic functionality
response = agent.invoke({"input": "What is 2+2?"})
print(response['output'])

# Then try complex tasks
response = agent.invoke({"input": "Analyze this codebase..."})
```

### 4. Enable Memory for Multi-Turn Tasks

```python
agent = factory.create_agent(
    role="Assistant",
    tools_list=tools,
    enable_memory=True  # Remembers context
)
```

### 5. Handle Errors Gracefully

```python
try:
    response = agent.invoke({"input": user_input})
    print(response['output'])
except Exception as e:
    print(f"Error: {e}")
    # Log, retry, or fallback
```

---

## Next Steps

1. **Run the demo**: `poetry run python agent_factory/examples/demo.py`
2. **Try the examples above**
3. **Create your own custom tool**
4. **Build a multi-agent system**
5. **Share your creations!**

---

## Need Help?

- Check [README.md](README.md) for full documentation
- See [claude.md](claude.md) for API key setup
- Review [examples/demo.py](agent_factory/examples/demo.py) for working code
- Open an issue on GitHub

**Happy Agent Building! 🤖**
