# Issues Log
> Chronological record of problems and solutions
> **Format:** Newest issues at top, [STATUS] tagged

---

## [2025-12-05 19:45] FIXED: LangChain BaseTool Pydantic Field Restrictions

**Problem:** File tools couldn't set attributes in __init__ due to Pydantic validation
**Root Cause:** LangChain BaseTool uses Pydantic v1 which doesn't allow arbitrary attributes
**Error:** `ValueError: "ReadFileTool" object has no field "path_validator"`

**Impact:**
- Initial file tool implementation had `__init__` methods setting validators
- All 27 file tool tests failed on instantiation
- Couldn't configure tools with custom allowed_dirs or size limits

**Solution:**
- Removed __init__ methods from all tool classes
- Create validators inside _run() method instead
- Use Path.cwd() as default allowed directory
- Simplified tool API (no config parameters needed)

**Code Change:**
```python
# BEFORE (failed):
class ReadFileTool(BaseTool):
    allowed_dirs: List[Path] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.path_validator = PathValidator(...)  # FAILS

# AFTER (works):
class ReadFileTool(BaseTool):
    def _run(self, file_path: str) -> str:
        path_validator = PathValidator(allowed_dirs=[Path.cwd()])  # Works
```

**Testing:**
- 27 file tool tests: 0 → 27 passing
- All tools now work correctly
- Simplified API (no config needed)

**Status:** [FIXED]

---

## [2025-12-05 18:30] FIXED: Cache Cleanup Test Timing Issue

**Problem:** test_periodic_cleanup failed - expired entries not cleaned up
**Root Cause:** Cleanup interval (1s) longer than wait time (0.6s)
**Error:** `AssertionError: assert 2 == 0` (2 entries still in cache)

**Impact:** 1/19 cache tests failing

**Solution:**
- Reduced cleanup interval: 1s → 0.5s
- Reduced TTL: 0.5s → 0.3s
- Kept wait time: 0.6s (longer than both)

**Code Change:**
```python
# BEFORE:
cache = CacheManager(cleanup_interval=1)
cache.set("key1", "value1", ttl=0.5)
time.sleep(0.6)  # Not long enough for cleanup

# AFTER:
cache = CacheManager(cleanup_interval=0.5)
cache.set("key1", "value1", ttl=0.3)
time.sleep(0.6)  # Now triggers cleanup
```

**Status:** [FIXED]

---

## [2025-12-05 16:00] FIXED: PathValidator Test Working Directory Issue

**Problem:** test_validate_safe_path failed with PathTraversalError
**Root Cause:** Relative path resolved from current directory, not tmp_path
**Error:** Path 'C:\...\Agent Factory\test.txt' not in allowed dirs: [tmp_path]

**Impact:** 1/27 file tool tests failing

**Solution:** Use pytest monkeypatch to change working directory to tmp_path

**Code Change:**
```python
# BEFORE:
def test_validate_safe_path(self, tmp_path):
    validator = PathValidator(allowed_dirs=[tmp_path])
    safe_path = validator.validate("test.txt")  # Resolves from CWD

# AFTER:
def test_validate_safe_path(self, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # Change CWD to tmp_path
    validator = PathValidator(allowed_dirs=[tmp_path])
    safe_path = validator.validate("test.txt")  # Now resolves correctly
```

**Status:** [FIXED]

---

## [2025-12-05 23:45] INFORMATIONAL: All Phase 1 Issues Resolved

**Session:** Phase 1 Testing and Validation
**Status:** All deliverables complete, all tests passing
**Issues Encountered:** Minor only (all resolved immediately)

**Resolved Immediately:**
1. Test import error → Added sys.path modification to test_callbacks.py
2. Class name mismatch → Changed AgentEvent to Event (actual class name)
3. EventType mismatches → Updated TOOL_START to TOOL_CALL to match implementation
4. Demo tool requirement → Added CurrentTimeTool to all agents (empty tools_list not allowed)
5. Test failures → Fixed 6 failing tests by aligning with actual implementation

**Test Results:**
- Initial: 6/13 callback tests failed
- Fixed: All import errors, class name mismatches, EventType corrections
- Final: 24/24 tests passing (13 callbacks + 11 orchestrator)

**No Open Issues from This Session**

---

## [2025-12-05 21:00] INFORMATIONAL: No New Issues This Session

**Session:** Constitutional Code Generation Implementation
**Status:** All tasks completed without blocking issues
**Issues Encountered:** Minor only (all resolved immediately)

**Resolved Immediately:**
1. Windows Unicode encoding → Replaced with ASCII ([OK]/[FAIL])
2. Dependencies not installed → Added jinja2, markdown via poetry
3. File needed reading before writing → Read first

**No Open Issues from This Session**

---

## [2025-12-04 16:45] OPEN: Dependency Conflict - LangChain vs LangGraph

**Problem:**
```
poetry sync fails with dependency resolution error
langgraph 0.0.26 requires langchain-core (>=0.1.25,<0.2.0)
langchain 0.2.1 requires langchain-core (>=0.2.0,<0.3.0)
These requirements are mutually exclusive
```

**Impact:**
- ❌ Cannot install dependencies
- ❌ Cannot run demo
- ❌ Fresh clones won't work
- ❌ Blocks all development

**Root Cause:**
LangGraph was added to `pyproject.toml` for future multi-agent orchestration but:
1. Not currently used in any code
2. Latest LangGraph version (0.0.26) requires old LangChain core (<0.2.0)
3. Current LangChain (0.2.1) requires new core (>=0.2.0)

**Proposed Solution:**
```toml
# Remove from pyproject.toml:
langgraph = "^0.0.26"
```

**Alternative Solution:**
Upgrade entire LangChain ecosystem to latest versions (more risk of breaking changes)

**Status:** OPEN - Awaiting fix
**Priority:** CRITICAL - Blocks installation
**Discovered By:** User attempting first installation

---

## [2025-12-04 16:30] FIXED: PowerShell Path with Spaces

**Problem:**
```powershell
cd C:\Users\hharp\OneDrive\Desktop\Agent Factory
# Error: A positional parameter cannot be found that accepts argument 'Factory'
```

**Root Cause:**
PowerShell interprets space as argument separator without quotes

**Solution:**
```powershell
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
```

**Status:** FIXED - Documented in troubleshooting
**Impact:** Documentation issue
**Lessons:**
- Folder names with spaces need quotes in PowerShell
- Should update docs with proper Windows examples

---

## [2025-12-04 15:45] FIXED: README Placeholder URL

**Problem:**
README.md contains `<your-repo-url>` placeholder which:
1. Causes PowerShell error (< is reserved operator)
2. Doesn't tell users the actual clone URL

**Original:**
```bash
git clone <your-repo-url>
```

**Fixed:**
```bash
git clone https://github.com/Mikecranesync/Agent-Factory.git
```

**Status:** FIXED - Updated in docs
**Impact:** User confusion during installation

---

## [2025-12-04 15:00] FIXED: API Key Format Issues

**Problem:**
Four API keys in `.env` had "ADD_KEY_HERE" prefixes:
```env
ANTHROPIC_API_KEY=ADD_KEY_HERE sk-ant-api03-...
GOOGLE_API_KEY=ADD_KEY_HERE=AIzaSy...
FIRECRAWL_API_KEY=ADD_KEY_HERE= fc-fb46...
TAVILY_API_KEY=ADD_KEY_HERE= tvly-dev-...
```

**Impact:**
- Keys would not load correctly
- API calls would fail with authentication errors

**Solution:**
Removed all "ADD_KEY_HERE" prefixes, leaving only actual keys

**Status:** FIXED
**Verification:** All keys validated in `claude.md`

---

## Known Issues (Not Yet Encountered)

### Potential: Poetry Version Mismatch
**Risk:** Users with Poetry 1.x may have issues
**Prevention:** Documentation specifies Poetry 2.x requirement
**Mitigation:** POETRY_GUIDE.md explains version differences

### Potential: Missing Python Version
**Risk:** Python 3.12+ not compatible
**Prevention:** pyproject.toml specifies `python = ">=3.10.0,<3.13"`
**Mitigation:** Clear error message from Poetry

### Potential: API Rate Limits
**Risk:** Free tiers may hit limits during testing
**Prevention:** Documentation includes rate limit information
**Mitigation:** claude.md documents all provider limits

---

## Issue Tracking Guidelines

### When Adding New Issues:
1. Add at TOP of file
2. Include timestamp: `[YYYY-MM-DD HH:MM]`
3. Use status tag: [OPEN], [INVESTIGATING], [FIXED], [WONTFIX]
4. Include:
   - Problem description
   - Root cause (if known)
   - Impact assessment
   - Proposed solution
   - Current status

### When Updating Issues:
1. Add status update as new subsection under issue
2. Include timestamp of update
3. DO NOT remove old information
4. Mark as [FIXED] or [CLOSED] when resolved

### When Issue is Fixed:
1. Change status to FIXED
2. Add solution details
3. Document verification steps
4. Keep entry for historical reference

---

**Last Updated:** 2025-12-04 16:50
