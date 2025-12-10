# AI Rules - Agent Factory Development Standards

**Audience:** AI agents (Claude, GPT-4, future autonomous agents) working on this codebase.

**Purpose:** Establish clear patterns, standards, and decision-making authority for AI-driven development.

**Last Updated:** 2025-12-10

---

## 1. Architecture Patterns

### 1.1 Orchestrator Pattern

**Pattern:** GitHub → Webhook → Jobs → Orchestrator → Agents

```python
# GitHub push event triggers webhook
webhook_handler.py  # Receives POST /webhook/github
    ↓
# Creates job in Supabase
agent_jobs table    # job_type, payload, priority
    ↓
# Orchestrator picks up job (60s cycle)
orchestrator.py     # Syncs git, fetches jobs, routes to agents
    ↓
# Agent executes task
agents/{team}/{agent_name}_agent.py
    ↓
# Updates status
agent_status table  # heartbeat, tasks_completed, errors
```

**Key Principles:**
- GitHub is single source of truth (git pull every cycle)
- Supabase is communication layer (not Redis)
- Agents are stateless (no memory between runs)
- Orchestrator handles routing (no direct agent-to-agent calls)

### 1.2 Agent Structure

**Standard Agent Template:**

```python
#!/usr/bin/env python3
"""
{AgentName}Agent - {One-line purpose}

Responsibilities:
- {Responsibility 1}
- {Responsibility 2}
- {Responsibility 3}

Schedule: {When it runs}
Dependencies: {What it needs}
Output: {What it produces}
"""

import os
import logging
from typing import Dict, Any, Optional

from agent_factory.memory.storage import SupabaseMemoryStorage

logger = logging.getLogger(__name__)


class {AgentName}Agent:
    """
    {Detailed description}

    Based on: docs/AGENT_ORGANIZATION.md Section {X}
    """

    def __init__(self):
        """Initialize agent with Supabase connection"""
        self.storage = SupabaseMemoryStorage()
        self.agent_name = "{agent_name}_agent"
        self._register_status()

    def _register_status(self):
        """Register agent in agent_status table"""
        self.storage.client.table("agent_status").upsert({
            "agent_name": self.agent_name,
            "status": "idle",
            "last_heartbeat": datetime.now().isoformat(),
            "tasks_completed_today": 0,
            "tasks_failed_today": 0
        }).execute()

    def _send_heartbeat(self):
        """Update heartbeat in agent_status table"""
        self.storage.client.table("agent_status") \
            .update({"last_heartbeat": datetime.now().isoformat()}) \
            .eq("agent_name", self.agent_name) \
            .execute()

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method.

        Args:
            payload: Job payload from orchestrator

        Returns:
            Result dict with status, output, errors
        """
        try:
            self._send_heartbeat()

            # Agent-specific logic here
            result = self._process(payload)

            self._update_status("completed")
            return {"status": "success", "result": result}

        except Exception as e:
            logger.error(f"{self.agent_name} failed: {e}")
            self._update_status("error", str(e))
            return {"status": "error", "error": str(e)}

    def _process(self, payload: Dict[str, Any]) -> Any:
        """Agent-specific processing logic"""
        raise NotImplementedError("Subclass must implement _process()")

    def _update_status(self, status: str, error_message: Optional[str] = None):
        """Update agent status in database"""
        update_data = {"status": status}
        if error_message:
            update_data["error_message"] = error_message

        self.storage.client.table("agent_status") \
            .update(update_data) \
            .eq("agent_name", self.agent_name) \
            .execute()
```

**Rules:**
- Always inherit structure above (consistency)
- Register in `agent_status` table on init
- Send heartbeat every 5 minutes during execution
- Update status on success/failure
- Log all errors with context

### 1.3 Tool Structure

**Pattern:** Tools are standalone functions or classes that agents use.

```python
# tools/web_scraper.py

from typing import Dict, Any
import requests
from bs4 import BeautifulSoup

def scrape_url(url: str, selector: Optional[str] = None) -> Dict[str, Any]:
    """
    Scrape content from URL.

    Args:
        url: Target URL
        selector: CSS selector for content extraction

    Returns:
        Dict with text, html, metadata

    Raises:
        requests.HTTPError: If request fails
        ValueError: If selector invalid
    """
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    if selector:
        content = soup.select(selector)
    else:
        content = soup.get_text()

    return {
        "text": content,
        "url": url,
        "status_code": response.status_code,
        "timestamp": datetime.now().isoformat()
    }
```

**Rules:**
- Pure functions (no side effects)
- Type hints on all parameters
- Docstrings with examples
- Raise specific exceptions (not generic Exception)
- Return structured data (dict or Pydantic model)

---

## 2. Code Standards

### 2.1 Python Style

**Follow PEP 8 with these specifics:**

```python
# Good: Type hints, docstrings, clear names
def generate_script(atom_id: str, target_length_minutes: int = 7) -> VideoScript:
    """
    Generate video script from knowledge atom.

    Args:
        atom_id: Knowledge atom UUID
        target_length_minutes: Target video length (default 7)

    Returns:
        VideoScript with narration, visual cues, metadata

    Raises:
        ValueError: If atom not found
        ValidationError: If script generation fails
    """
    atom = fetch_atom(atom_id)

    if not atom:
        raise ValueError(f"Atom {atom_id} not found")

    script_text = _generate_narration(atom, target_length_minutes)
    visual_cues = _extract_visual_cues(atom)

    return VideoScript(
        script_text=script_text,
        visual_cues=visual_cues,
        atom_ids=[atom_id],
        estimated_duration_seconds=target_length_minutes * 60
    )


# Bad: No types, unclear names, no docs
def gen(id, len=7):
    a = get(id)
    s = make(a, len)
    v = get_vis(a)
    return {"s": s, "v": v}
```

**Naming Conventions:**
- `snake_case` for functions, variables, modules
- `PascalCase` for classes
- `UPPER_CASE` for constants
- Prefix private with `_` (e.g., `_internal_method`)

### 2.2 Pydantic Models

**Always use Pydantic v2 for data models:**

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime

class VideoScript(BaseModel):
    """Video script metadata and content"""

    script_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    script_text: str = Field(..., min_length=100, description="Full narration text")
    atom_ids: List[str] = Field(..., description="Source knowledge atoms")
    visual_cues: List[str] = Field(default_factory=list)
    personality_markers: List[str] = Field(default_factory=list)
    estimated_duration_seconds: int = Field(..., gt=0)
    status: Literal["draft", "approved", "in_production", "published"] = "draft"
    created_at: datetime = Field(default_factory=datetime.now)

    @field_validator('script_text')
    @classmethod
    def validate_script_length(cls, v: str) -> str:
        """Ensure script is reasonable length (100-10000 words)"""
        word_count = len(v.split())
        if word_count < 100:
            raise ValueError("Script too short (< 100 words)")
        if word_count > 10000:
            raise ValueError("Script too long (> 10000 words)")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "script_text": "Welcome to today's lesson on Ohm's Law...",
                "atom_ids": ["plc:generic:ohms-law"],
                "estimated_duration_seconds": 420
            }]
        }
    }
```

**Rules:**
- All data structures use Pydantic (no plain dicts for complex data)
- Use `Field()` for validation and documentation
- Add `@field_validator` for complex validation
- Include `model_config` with examples
- Use `Literal` for enums (not string unions)

### 2.3 Error Handling

**Pattern: Try-catch with specific exceptions, logging, and recovery**

```python
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def fetch_and_process(url: str, retries: int = 3) -> Optional[Dict[str, Any]]:
    """
    Fetch URL and process content with retry logic.

    Args:
        url: Target URL
        retries: Number of retry attempts (default 3)

    Returns:
        Processed data or None if all retries failed
    """
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()
            processed = process_data(data)

            return processed

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                logger.error(f"URL not found: {url}")
                return None  # Don't retry 404s

            logger.warning(f"HTTP error (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff

        except requests.Timeout:
            logger.warning(f"Timeout (attempt {attempt + 1}/{retries})")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)

        except ValueError as e:
            logger.error(f"Invalid data format: {e}")
            return None  # Don't retry validation errors

    logger.error(f"All {retries} attempts failed for {url}")
    return None
```

**Rules:**
- Catch specific exceptions (not bare `except:`)
- Log at appropriate levels (DEBUG, INFO, WARNING, ERROR)
- Retry transient failures (network, timeout)
- Don't retry permanent failures (404, validation errors)
- Use exponential backoff (2^attempt seconds)
- Return `None` or raise for unrecoverable errors

---

## 3. Security Rules

### 3.1 Never Hardcode Secrets

**Bad:**
```python
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
OPENAI_API_KEY = "sk-proj-abc123..."
```

**Good:**
```python
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not SUPABASE_KEY:
    raise ValueError("SUPABASE_KEY not set in .env")
```

**Rules:**
- All secrets in `.env` file (never committed)
- Use `os.getenv()` with clear names
- Validate secrets exist at startup (fail fast)
- Never log secrets (even partially)
- Never include secrets in error messages

### 3.2 Input Validation

**Always validate and sanitize user input:**

```python
from pydantic import BaseModel, Field, field_validator

class ApprovalRequest(BaseModel):
    """User approval request"""

    item_id: str = Field(..., pattern=r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
    feedback: Optional[str] = Field(None, max_length=1000)

    @field_validator('feedback')
    @classmethod
    def sanitize_feedback(cls, v: Optional[str]) -> Optional[str]:
        """Remove potentially dangerous characters"""
        if v is None:
            return None

        # Remove HTML tags
        import re
        v = re.sub(r'<[^>]+>', '', v)

        # Remove SQL-like patterns (basic XSS/SQLi prevention)
        dangerous_patterns = ['--', ';', 'DROP', 'DELETE', 'UPDATE', '<script']
        for pattern in dangerous_patterns:
            if pattern.lower() in v.lower():
                raise ValueError(f"Feedback contains disallowed pattern: {pattern}")

        return v.strip()
```

**Rules:**
- Use Pydantic validators for all input
- Whitelist allowed characters (don't blacklist)
- Validate format (UUIDs, emails, URLs)
- Sanitize text (remove HTML, SQL patterns)
- Limit string lengths (prevent DoS)

### 3.3 Audit Logging

**Log all privileged operations:**

```python
def approve_video(video_id: str, approved_by: str) -> bool:
    """Approve video for publication"""

    # Log the approval (audit trail)
    storage.client.table("audit_log").insert({
        "action": "approve_video",
        "resource_type": "video",
        "resource_id": video_id,
        "user_id": approved_by,
        "timestamp": datetime.now().isoformat(),
        "metadata": {
            "ip_address": get_client_ip(),
            "user_agent": get_user_agent()
        }
    }).execute()

    # Update video status
    storage.client.table("published_videos") \
        .update({"status": "approved", "approved_by": approved_by}) \
        .eq("id", video_id) \
        .execute()

    return True
```

**What to log:**
- Approvals (videos, atoms, posts)
- Configuration changes
- Failed authentication attempts
- Agent errors
- External API calls (with rate limits)

**What NOT to log:**
- Passwords or API keys
- Full user data (PII)
- Large payloads (>1KB)

---

## 4. Testing Requirements

### 4.1 Test Coverage

**Target: 80% coverage minimum**

```bash
# Run tests with coverage
poetry run pytest --cov=agent_factory --cov-report=html

# Coverage must be ≥ 80%
```

### 4.2 Test Structure

**Pattern: Arrange-Act-Assert**

```python
# tests/agents/test_scriptwriter_agent.py

import pytest
from agents.content.scriptwriter_agent import ScriptwriterAgent
from core.models import PLCAtom, VideoScript

def test_scriptwriter_generates_valid_script():
    """Test that ScriptwriterAgent generates valid video script from atom"""

    # Arrange: Create test atom
    atom = PLCAtom(
        id="test-atom-1",
        title="Ohm's Law",
        summary="Relationship between voltage, current, and resistance",
        domain="electricity",
        vendor="generic",
        educational_level="beginner",
        prerequisites=[],
        relations=[]
    )

    agent = ScriptwriterAgent()

    # Act: Generate script
    script = agent.generate_script(atom, target_length_minutes=5)

    # Assert: Validate script
    assert isinstance(script, VideoScript)
    assert len(script.script_text) > 100  # Reasonable length
    assert atom.id in script.atom_ids
    assert script.estimated_duration_seconds == 300  # 5 minutes
    assert script.status == "draft"


@pytest.fixture
def mock_supabase(monkeypatch):
    """Mock Supabase for testing"""
    class MockSupabase:
        def table(self, name):
            return self

        def select(self, *args):
            return self

        def execute(self):
            return type('obj', (object,), {'data': []})

    monkeypatch.setattr(
        "agent_factory.memory.storage.SupabaseMemoryStorage.client",
        MockSupabase()
    )
```

**Rules:**
- One test per behavior (not per method)
- Use descriptive test names (`test_scriptwriter_generates_valid_script`)
- Mock external dependencies (Supabase, APIs)
- Test edge cases (empty input, invalid data)
- Test error handling (exceptions, retries)

### 4.3 Integration Tests

**Test full workflows:**

```python
# tests/integration/test_video_pipeline.py

def test_full_video_production_pipeline(temp_db):
    """Test complete pipeline: atom → script → audio → video"""

    # Step 1: Create atom
    atom = create_test_atom("ohms-law")
    storage.save_atom(atom)

    # Step 2: Generate script
    scriptwriter = ScriptwriterAgent()
    script = scriptwriter.run({"atom_id": atom.id})
    assert script["status"] == "success"

    # Step 3: Generate audio
    voice_agent = VoiceProductionAgent()
    audio = voice_agent.run({"script_id": script["result"]["script_id"]})
    assert audio["status"] == "success"

    # Step 4: Assemble video
    video_agent = VideoAssemblyAgent()
    video = video_agent.run({"audio_id": audio["result"]["audio_id"]})
    assert video["status"] == "success"

    # Verify final video exists
    assert os.path.exists(video["result"]["video_path"])
```

---

## 5. Git Workflow

### 5.1 Worktree Pattern (REQUIRED)

**Always use worktrees for multi-agent work:**

```bash
# Create worktree for feature
git worktree add ../agent-factory-feature-name -b feature-name

# Work in worktree
cd ../agent-factory-feature-name

# Commit and push
git add .
git commit -m "feat: Add feature"
git push origin feature-name

# Create PR
gh pr create --title "Feature Name" --body "Description"

# After merge, cleanup
cd ../agent-factory
git worktree remove ../agent-factory-feature-name
git branch -d feature-name
```

**Why:**
- Prevents file conflicts between agents
- Isolates changes per feature
- Allows parallel development
- Pre-commit hook enforces this (blocks commits to main directory)

### 5.2 Commit Messages

**Pattern: Conventional Commits**

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Tests
- `refactor:` Code restructure (no behavior change)
- `chore:` Maintenance (dependencies, config)

**Examples:**

```
feat(agents): Add ScriptwriterAgent for video script generation

Implements agent that converts knowledge atoms into video scripts
with hooks, personality markers, and visual cues.

Features:
- Script structure: Hook → Explanation → Example → Recap
- Personality markers ([enthusiastic], [cautionary])
- Visual cue integration (show diagram, highlight code)
- Citation validation (all claims backed by atoms)

Based on: docs/AGENT_ORGANIZATION.md Section 9

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

**Rules:**
- Subject line ≤ 72 characters
- Body explains WHY (not WHAT - code shows that)
- Reference docs/issues where relevant
- Include Co-Authored-By for AI commits

---

## 6. Decision-Making Authority

### 6.1 Autonomous Decisions (No Approval Needed)

**You can decide these without asking:**

1. **File Structure**
   - Follow existing patterns (agents/, docs/, tests/)
   - Use team folders (executive/, research/, content/, media/, engagement/)

2. **Code Style**
   - Follow PEP 8 + standards above
   - Use Pydantic for all data models
   - Type hints on all functions

3. **Naming**
   - Follow AGENT_ORGANIZATION.md specs
   - Use descriptive names (not abbreviations)
   - Match domain language (atom, script, video, etc.)

4. **Error Handling**
   - Retry transient failures (3x exponential backoff)
   - Log all errors with context
   - Return `None` or raise for unrecoverable errors

5. **Testing**
   - Write tests for all new features
   - Mock external dependencies
   - Target 80% coverage

### 6.2 User Approval Required

**Stop and ask for approval:**

1. **Security**
   - Exposing new API endpoints
   - Changing authentication logic
   - Accessing sensitive data

2. **Architecture**
   - Adding new dependencies (pyproject.toml)
   - Changing database schema (migrations)
   - Introducing new patterns not in docs

3. **Branding/UX**
   - Bot message tone/personality
   - User-facing error messages
   - Command names/structure

4. **Budget**
   - Adding paid services (>$10/mo)
   - Increasing API usage significantly
   - New infrastructure costs

5. **Data**
   - Deleting production data
   - Changing data retention policies
   - Exporting user data

### 6.3 Document and Proceed

**Make decision, document, continue:**

1. **Implementation Details**
   - Algorithm choice (as long as correct)
   - Helper function structure
   - Internal variable names

2. **Optimization**
   - Query optimization
   - Caching strategies
   - Performance tuning

3. **Refactoring**
   - Extract functions
   - Rename internal methods
   - Reorganize modules (same interface)

**Log in DECISION_LOG.md:**

```markdown
## Decision: Use SQLAlchemy ORM vs Raw SQL
**Date:** 2025-12-10
**Context:** Building Research Agent database queries
**Options:**
1. SQLAlchemy ORM (more Pythonic, safer)
2. Raw SQL (more control, potentially faster)
**Decision:** Stick with Supabase client (existing pattern)
**Rationale:** Already using Supabase client in other agents, consistency matters
**Impact:** All agents use same query interface, easier maintenance
```

---

## 7. Quick Reference

### Do's ✅

- Use type hints everywhere
- Write docstrings with examples
- Log errors with context
- Validate all input (Pydantic)
- Test before committing (80% coverage)
- Use worktrees for features
- Follow conventional commits
- Update docs when changing behavior

### Don'ts ❌

- Never hardcode secrets
- Never commit to main directory (use worktrees)
- Never use bare `except:` (catch specific exceptions)
- Never log secrets or PII
- Never skip tests
- Never refactor without tests
- Never change public interfaces without discussion
- Never guess at ambiguous requirements (escalate)

### When in Doubt

1. Check existing code for patterns
2. Read relevant docs (AGENT_ORGANIZATION.md, PATTERNS.md)
3. Follow principle of least surprise
4. Document decision in DECISION_LOG.md
5. If still unclear, escalate (don't guess)

---

## References

- **CLAUDE.md** - Overall project context
- **CONTRIBUTING.md** - Contribution guidelines (for humans)
- **docs/AGENT_ORGANIZATION.md** - 18-agent specifications
- **docs/PATTERNS.md** - Google ADK patterns
- **docs/ARCHITECTURE.md** - System architecture
- **docs/SECURITY_STANDARDS.md** - Security checklists

---

**Last Updated:** 2025-12-10
**Maintained By:** AI agents + human oversight
**Review Cycle:** Monthly or when major patterns change
