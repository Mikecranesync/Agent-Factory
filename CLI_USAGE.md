# Agent Factory CLI Usage Guide

## ✨ Quick Start

The Agent Factory CLI (`agentcli`) makes it super easy to test and interact with your AI agents!

### Installation (Already Done!)

The CLI is already installed. You can use it immediately:

```bash
poetry run agentcli chat
```

## 📋 Available Commands

### 1. Interactive Chat (Main Feature!)

**Start chatting with the Research Agent:**
```bash
poetry run agentcli chat
```

**Start with the Coding Agent:**
```bash
poetry run agentcli chat --agent coding
```

**Enable verbose mode (see detailed output):**
```bash
poetry run agentcli chat --verbose
```

### 2. List Available Agents

```bash
poetry run agentcli list-agents
```

### 3. Show Version

```bash
poetry run agentcli version
```

## 🎮 Interactive Mode Commands

Once you're in interactive mode (`agentcli chat`), you can use these commands:

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/exit` | Exit the CLI |
| `/agent <name>` | Switch to different agent (research, coding) |
| `/info` | Show current agent configuration |
| `/clear` | Clear the screen |
| `/tools` | List available tools for current agent |
| `/history` | Show command history |

## 💡 Example Session

```bash
$ poetry run agentcli chat

╭────────────────────────────────╮
│ Agent Factory Interactive CLI  │
│ Current Agent: Research Agent  │
╰────────────────────────────────╯

[Research Agent] You: What is LangChain?
> Agent is thinking...

Agent: LangChain is a framework for developing applications powered by language models...

[Research Agent] You: /agent coding
✓ Switched to Coding Agent

[Coding Agent] You: List Python files in the current directory
> Agent is thinking...

Agent: Found 15 Python files:
- agent_factory/core/agent_factory.py
- agent_factory/tools/research_tools.py
...

[Coding Agent] You: /exit
Goodbye! Thanks for using Agent Factory.
```

## 🔧 Tips & Tricks

### 1. Quick Agent Switching
You can switch agents mid-conversation without losing context:
```
/agent research
/agent coding
```

### 2. See What Tools Are Available
```
/tools
```

### 3. Check Your Configuration
```
/info
```

### 4. Clear the Screen
```
/clear
```

### 5. Exit Anytime
- Type `/exit`
- Or press `Ctrl+D`
- Or press `Ctrl+C` twice

## 🎯 What Each Agent Does

### Research Agent (`research`)
- **Tools**: Wikipedia search, DuckDuckGo search, Current time
- **Best for**: Information gathering, web research, answering questions
- **Example queries**:
  - "What is machine learning?"
  - "Who invented Python?"
  - "Explain quantum computing"

### Coding Agent (`coding`)
- **Tools**: Read files, Write files, List directory, Git status, File search
- **Best for**: Code analysis, file operations, project navigation
- **Example queries**:
  - "List all Python files"
  - "What's in the README?"
  - "Show me the git status"
  - "Search for 'AgentFactory' in Python files"

## ⚙️ Configuration

The CLI uses your `.env` file for API keys. Make sure you have:
```env
OPENAI_API_KEY=sk-proj-...
```

If the key is missing, the CLI will show a helpful error message.

## 🐛 Troubleshooting

### "OPENAI_API_KEY not found"
Make sure your `.env` file exists and contains your OpenAI API key.

### "Unknown agent"
Use one of the available agents: `research` or `coding`

### Command not recognized
Make sure to use `poetry run agentcli` from the project directory.

## 🚀 Advanced Usage

### Run from Anywhere (Optional)

If you want to use `agentcli` without `poetry run`, activate the virtual environment first:

**PowerShell:**
```powershell
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
poetry shell
agentcli chat
```

**Or directly:**
```powershell
& "C:\Users\hharp\AppData\Local\pypoetry\Cache\virtualenvs\agent-factory-VqfS_2lG-py3.11\Scripts\agentcli.exe" chat
```

### VSCode Integration

Create a task in `.vscode/tasks.json`:
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Start Agent Chat",
      "type": "shell",
      "command": "poetry run agentcli chat",
      "problemMatcher": []
    }
  ]
}
```

Then press `Ctrl+Shift+P` → "Tasks: Run Task" → "Start Agent Chat"

## 📝 Notes

- The CLI automatically saves conversation history within each session
- Agent memory is preserved during the session
- Streaming responses show thinking process in real-time
- All output is color-coded for easy reading
- Works on Windows, macOS, and Linux

## 🎉 That's It!

You're all set! Just run:
```bash
poetry run agentcli chat
```

And start chatting with your agents! 🤖
