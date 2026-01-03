# HARVEST BLOCK 25: Manus Client

**Priority**: LOW
**Size**: 24.44KB (total across 5 files: client.py 10.74KB, config.py 2.32KB, models.py 2.36KB, exceptions.py 660 bytes, docs 7.54KB)
**Source**: `agent_factory/integrations/manus/` (client.py, config.py, models.py, exceptions.py, __init__.py)
**Target**: `rivet/integrations/manus/`

---

## Overview

Commercial Manus API client for autonomous robotics research - uses OpenAI SDK compatibility layer for task execution, supports 3 agent profiles (lite/standard/max), includes cost tracking, polling mechanism, and file/image inputs for maintenance workflow automation.

### What This Adds

- **3 Agent Profiles**: Lite (~50 credits), Standard (~150 credits), Max (~300 credits)
- **Multi-input Support**: Text prompts, file URLs, image URLs in single task
- **Sync/Async Execution**: Wait for completion or fire-and-forget
- **Conversation Continuity**: Continue existing task with follow-up messages
- **Polling Mechanism**: Auto-poll task status until completion (5s intervals)
- **Timeout Management**: Configurable timeout (30s-1800s, default 300s)
- **Cost Tracking**: Credits → USD conversion (default $0.01/credit)
- **Error Handling**: 6 exception types for granular control
- **OpenAI SDK Compatibility**: Uses OpenAI SDK with custom base URL

### Key Features

```python
from rivet.integrations.manus.client import ManusAPIClient
from rivet.integrations.manus.models import AgentProfile

# Initialize client
client = ManusAPIClient(api_key="manus_...")

# Simple research task (wait for completion)
result = await client.create_task(
    prompt="Research Siemens S7-1200 communication errors",
    profile=AgentProfile.STANDARD,
    wait=True,
    timeout=300
)

print(result.text)  # Research findings
print(f"Credits used: {result.credits_used}")  # ~150
print(f"Cost: ${result.cost_usd:.2f}")  # ~$1.50

# Task with files and images
result = await client.create_task(
    prompt="Analyze this technical manual and schematic",
    files=["https://example.com/manual.pdf"],
    images=["https://example.com/schematic.png"],
    profile=AgentProfile.MAX  # Best quality
)

# Fire-and-forget (async execution)
result = await client.create_task(
    prompt="Long-running research task",
    wait=False
)
print(result.task_id)  # Get ID immediately
# ... later ...
final = await client.get_task_status(result.task_id)
```

---

## Agent Profiles (Cost/Quality Tradeoffs)

```python
from rivet.integrations.manus.models import AgentProfile

# LITE - Fast, lower quality (~50 credits)
result = await client.create_task(
    prompt="Quick classification task",
    profile=AgentProfile.LITE
)
# Cost: ~$0.50

# STANDARD - Balanced (default, ~150 credits)
result = await client.create_task(
    prompt="Research task with moderate depth",
    profile=AgentProfile.STANDARD
)
# Cost: ~$1.50

# MAX - Best quality, slower (~300 credits)
result = await client.create_task(
    prompt="Comprehensive technical analysis",
    profile=AgentProfile.MAX
)
# Cost: ~$3.00
```

**When to Use Each Profile**:
- **LITE**: Quick lookups, simple classifications, speed-critical tasks
- **STANDARD**: General research, troubleshooting, balanced cost/quality
- **MAX**: Complex analysis, safety-critical research, accuracy-critical

---

## Multi-Input Tasks

```python
# Combine text, files, and images
result = await client.create_task(
    prompt="Compare the manual instructions with this schematic and identify discrepancies",
    files=[
        "https://cdn.example.com/powerFlex-manual.pdf",
        "https://cdn.example.com/installation-guide.pdf"
    ],
    images=[
        "https://cdn.example.com/wiring-schematic.jpg",
        "https://cdn.example.com/control-panel.jpg"
    ],
    profile=AgentProfile.MAX,
    timeout=600  # 10 minutes for complex analysis
)

# Access results
print(result.text)  # Analysis text
for file in result.files:
    print(f"Output file: {file.filename} - {file.url}")
```

---

## Conversation Continuity

```python
# Initial task
result1 = await client.create_task(
    prompt="Research Allen-Bradley fault code F003",
    profile=AgentProfile.STANDARD
)

print(result1.text)  # Initial research

# Follow-up question
result2 = await client.continue_task(
    task_id=result1.task_id,
    followup="What are the most common causes of F003 in ControlLogix systems?"
)

print(result2.text)  # Follow-up answer
# New task_id, but maintains conversation context
```

---

## Sync vs Async Execution

```python
# SYNC: Wait for completion (blocking)
result = await client.create_task(
    prompt="Research task",
    wait=True,  # Default
    timeout=300
)
# Returns completed TaskResult

# ASYNC: Fire-and-forget (non-blocking)
result = await client.create_task(
    prompt="Long-running research",
    wait=False
)
print(result.task_id)  # Returns immediately with task_id
print(result.status)  # TaskStatus.RUNNING

# ... do other work ...

# Check status later
final = await client.get_task_status(result.task_id)
if final.status == TaskStatus.COMPLETED:
    print(final.text)
```

---

## Polling Mechanism

```python
# Automatic polling when wait=True
result = await client.create_task(
    prompt="Research task",
    wait=True,
    timeout=300  # Max 5 minutes
)

# Polling behavior:
# - Checks status every 5 seconds (configurable)
# - Raises TaskTimeoutError if timeout exceeded
# - Raises TaskFailedError if task errors
# - Returns TaskResult when completed

# Configure polling interval
from rivet.integrations.manus.config import ManusConfig

config = ManusConfig.from_env()
config.poll_interval = 10  # Poll every 10 seconds
client = ManusAPIClient(config=config)
```

---

## Cost Tracking

```python
# Automatic cost calculation
result = await client.create_task(
    prompt="Research Siemens S7-1200 diagnostics",
    profile=AgentProfile.STANDARD
)

print(f"Credits used: {result.credits_used}")  # 150
print(f"Cost: ${result.cost_usd:.2f}")  # $1.50
print(f"Duration: {result.duration_seconds:.1f}s")  # 45.2

# Configure cost per credit (default $0.01)
config = ManusConfig.from_env()
config.cost_per_credit = 0.012  # $0.012/credit
client = ManusAPIClient(config=config)

result = await client.create_task(...)
# Now cost_usd = credits_used * 0.012
```

---

## Error Handling

```python
from rivet.integrations.manus.exceptions import (
    InvalidAPIKeyError,
    TaskTimeoutError,
    TaskFailedError,
    RateLimitError,
    NetworkError,
    ManusAPIError
)

try:
    result = await client.create_task(
        prompt="Research task",
        timeout=60
    )

except InvalidAPIKeyError as e:
    # Invalid or missing API key
    print(f"Auth error: {e}")

except TaskTimeoutError as e:
    # Task exceeded timeout duration
    print(f"Timeout after {e}")

except TaskFailedError as e:
    # Task completed with error status
    print(f"Task failed: {e}")

except RateLimitError as e:
    # Rate limit exceeded
    print(f"Rate limited: {e}")

except NetworkError as e:
    # Network communication failed
    print(f"Network error: {e}")

except ManusAPIError as e:
    # Catch-all for any Manus error
    print(f"Manus error: {e}")
```

**Exception Hierarchy**:
```
ManusAPIError (base)
├── InvalidAPIKeyError (401 auth)
├── TaskTimeoutError (timeout exceeded)
├── TaskFailedError (task error status)
├── RateLimitError (429 rate limit)
└── NetworkError (network issues)
```

---

## Configuration

**Environment Variables**:
```bash
# Required
export MANUS_API_KEY=manus_...

# Optional
export MANUS_BASE_URL=https://api.manus.im  # Default
export MANUS_DEFAULT_PROFILE=manus-1.6  # standard (default)
export MANUS_DEFAULT_TIMEOUT=300  # 5 minutes (default)
```

**In Code**:
```python
from rivet.integrations.manus.config import ManusConfig
from rivet.integrations.manus.models import AgentProfile

# From environment variables
config = ManusConfig.from_env()

# Manual configuration
config = ManusConfig(
    api_key="manus_...",
    base_url="https://api.manus.im",
    default_profile=AgentProfile.MAX,
    default_timeout=600,  # 10 minutes
    poll_interval=5,  # Poll every 5 seconds
    max_retries=3,  # Network error retries
    cost_per_credit=0.01  # $0.01/credit
)

client = ManusAPIClient(config=config)
```

---

## Dependencies

```bash
# Install required packages
poetry add openai pydantic

# OpenAI SDK is used for API compatibility layer
```

---

## Quick Implementation Guide

1. Copy source directory: `cp -r agent_factory/integrations/manus/ rivet/integrations/manus/`
2. Install: `poetry add openai pydantic`
3. Set env var: `export MANUS_API_KEY=manus_...`
4. Validate: `python -c "from rivet.integrations.manus import ManusAPIClient; print('OK')"`

---

## Validation

```bash
# Test import
python -c "from rivet.integrations.manus.client import ManusAPIClient; print('OK')"

# Test configuration
python -c "
from rivet.integrations.manus.config import ManusConfig

config = ManusConfig.from_env()
print(f'Base URL: {config.base_url}')
print(f'Default profile: {config.default_profile.value}')
"

# Test client initialization
python -c "
from rivet.integrations.manus.client import ManusAPIClient

client = ManusAPIClient()  # Uses MANUS_API_KEY env var
print('Client initialized OK')
"

# Test task creation (requires valid API key)
python -c "
import asyncio
from rivet.integrations.manus.client import ManusAPIClient

async def test():
    client = ManusAPIClient()
    result = await client.create_task(
        prompt='Test task',
        wait=True,
        timeout=60
    )
    print(f'Task completed: {result.task_id}')
    print(f'Credits used: {result.credits_used}')

asyncio.run(test())
"
```

---

## Integration Notes

**RIVET Research Pipeline**:
```python
from rivet.integrations.manus.client import ManusAPIClient
from rivet.tools.unified_research_tool import UnifiedResearchTool

# Use Manus for complex research via UnifiedResearchTool
async def research_with_manus(query: str):
    """
    Autonomous research using Manus API (premium tier).
    """
    client = ManusAPIClient()

    result = await client.create_task(
        prompt=f"Research the following question and provide a comprehensive answer: {query}",
        profile=AgentProfile.MAX,  # Best quality for research
        timeout=600
    )

    return {
        "text": result.text,
        "files": result.files,
        "cost_usd": result.cost_usd,
        "credits_used": result.credits_used
    }
```

**Cost Optimization**:
```python
# Use cheaper profile for simple queries
def select_profile(query_complexity):
    if query_complexity == "simple":
        return AgentProfile.LITE  # ~$0.50
    elif query_complexity == "moderate":
        return AgentProfile.STANDARD  # ~$1.50
    else:
        return AgentProfile.MAX  # ~$3.00

result = await client.create_task(
    prompt=query,
    profile=select_profile(complexity)
)
```

**Performance**:
- **Latency**: Task-dependent (30s - 10min)
- **Polling**: 5s intervals (configurable)
- **Timeout**: 30s - 1800s (default 300s)

---

## What This Enables

- ✅ Autonomous robotics research (Manus API integration)
- ✅ 3 quality tiers (lite/standard/max for cost optimization)
- ✅ Multi-input tasks (text + files + images)
- ✅ Conversation continuity (follow-up questions)
- ✅ Cost tracking (credits → USD conversion)
- ✅ Sync/async execution (wait or fire-and-forget)
- ✅ Timeout management (30s - 1800s configurable)
- ✅ Error handling (6 exception types)
- ✅ OpenAI SDK compatibility (familiar interface)

---

## Next Steps

After implementing HARVEST 25, proceed to **HARVEST 26: Performance Tracker** for production observability suite (final TIER 4 block).

SEE FULL SOURCE:
- `agent_factory/integrations/manus/client.py` (356 lines, 10.74KB)
- `agent_factory/integrations/manus/config.py` (89 lines, 2.32KB)
- `agent_factory/integrations/manus/models.py` (82 lines, 2.36KB)
- `agent_factory/integrations/manus/exceptions.py` (34 lines, 660 bytes)
- `agent_factory/integrations/manus/__init__.py`
