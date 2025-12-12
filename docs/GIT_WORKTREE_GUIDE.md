# Git Worktree Guide for Agent Factory

## Table of Contents

1. [Why Worktrees?](#why-worktrees)
2. [Quick Start](#quick-start)
3. [Creating Worktrees](#creating-worktrees)
4. [Development Workflow](#development-workflow)
5. [Parallel Development](#parallel-development)
6. [Managing Worktrees](#managing-worktrees)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)
9. [Advanced Usage](#advanced-usage)

---

## Why Worktrees?

**Problem:** Agent Factory is built BY autonomous agents FOR autonomous agents. Multiple AI agents need to work on the same codebase simultaneously without conflicts.

**Traditional Approach (Broken):**
```bash
# Agent 1 working in main directory
cd Agent-Factory/
git checkout -b research-agent
# ... making changes ...

# Agent 2 tries to work simultaneously
cd Agent-Factory/
git checkout -b scriptwriter-agent  # ERROR: Conflicts with Agent 1's work
```

**Worktree Approach (Works):**
```bash
# Agent 1 works in dedicated directory
cd agent-factory-research/
git checkout -b research-agent
# ... making changes ...

# Agent 2 works in separate directory (no conflicts!)
cd agent-factory-scriptwriter/
git checkout -b scriptwriter-agent
# ... making changes ...
```

**Benefits:**
- ✅ **Multiple agents work in parallel** - No file conflicts
- ✅ **Each feature isolated** - Changes don't interfere
- ✅ **Clean testing** - Test features independently
- ✅ **Easy PR reviews** - Each worktree = one PR
- ✅ **Same git history** - All worktrees share .git database

---

## Quick Start

### Option 1: Create All 18 Worktrees at Once (Recommended)

```bash
# From main Agent Factory directory
bash scripts/create_all_worktrees.sh
```

This creates:
- `agent-factory-executive-ai-ceo/`
- `agent-factory-research/`
- `agent-factory-scriptwriter/`
- ... (18 total)

### Option 2: Create Individual Worktrees

```bash
# Create worktree for specific agent
git worktree add ../agent-factory-research -b research/research-agent

# Change to worktree
cd ../agent-factory-research

# Start coding
code .
```

---

## Creating Worktrees

### Basic Syntax

```bash
git worktree add <path> -b <branch>
```

**Parameters:**
- `<path>`: Directory for worktree (usually `../agent-factory-<name>`)
- `-b <branch>`: New branch name (format: `<team>/<agent>-agent`)

### Examples

**Research Agent:**
```bash
git worktree add ../agent-factory-research -b research/research-agent
```

**Scriptwriter Agent:**
```bash
git worktree add ../agent-factory-scriptwriter -b content/scriptwriter-agent
```

**Voice Production Agent:**
```bash
git worktree add ../agent-factory-voice -b media/voice-production-agent
```

### Naming Conventions

**Worktree Directory:** `agent-factory-<agent-name>`
- `agent-factory-research`
- `agent-factory-scriptwriter`
- `agent-factory-analytics`

**Branch Name:** `<team>/<agent>-agent`
- `research/research-agent`
- `content/scriptwriter-agent`
- `engagement/analytics-agent`

**Teams:**
- `executive/` - AI CEO, Chief of Staff
- `research/` - Research, Atom Builder, Librarian, Quality Checker
- `content/` - Curriculum, Strategy, Scriptwriter, SEO, Thumbnail
- `media/` - Voice, Video, Publishing Strategy, YouTube Uploader
- `engagement/` - Community, Analytics, Social Amplifier

---

## Development Workflow

### 1. Create Worktree

```bash
# From main Agent Factory directory
git worktree add ../agent-factory-research -b research/research-agent
```

### 2. Work in Worktree

```bash
# Change to worktree
cd ../agent-factory-research

# Open in editor
code .

# Make changes to files
# ...
```

### 3. Commit Changes

```bash
# Stage files
git add .

# Commit with conventional commits
git commit -m "feat: Add Research Agent web scraping (Issue #47)"
```

**Commit Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Add/update tests
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

### 4. Push to Remote

```bash
# Push branch to origin
git push origin research/research-agent
```

### 5. Create Pull Request

```bash
# Option 1: GitHub CLI
gh pr create --title "Add Research Agent" --body "Implements Issue #47"

# Option 2: Web UI
# Visit: https://github.com/your-username/agent-factory
# Click "New Pull Request"
```

### 6. After PR is Merged

```bash
# Go back to main directory
cd ../Agent-Factory

# Pull latest main
git pull origin main

# Remove worktree
git worktree remove ../agent-factory-research

# Delete local branch
git branch -d research/research-agent
```

**Or use automated cleanup:**
```bash
bash scripts/cleanup_merged_worktrees.sh
```

---

## Parallel Development

### Example: 3 Agents Working Simultaneously

**Terminal 1 (Research Agent):**
```bash
cd agent-factory-research/
# Working on web scraping...
git commit -m "feat: Add PDF scraper"
```

**Terminal 2 (Scriptwriter Agent):**
```bash
cd agent-factory-scriptwriter/
# Working on script generation...
git commit -m "feat: Add script template"
```

**Terminal 3 (Voice Production Agent):**
```bash
cd agent-factory-voice/
# Working on ElevenLabs integration...
git commit -m "feat: Add voice cloning"
```

**All working independently, no conflicts!**

### Opening Multiple Claude Code Instances

**Windows:**
```powershell
# Terminal 1
cd ..\agent-factory-research
code .

# Terminal 2
cd ..\agent-factory-scriptwriter
code .

# Terminal 3
cd ..\agent-factory-voice
code .
```

**macOS/Linux:**
```bash
# Terminal 1
cd ../agent-factory-research
code .

# Terminal 2
cd ../agent-factory-scriptwriter
code .

# Terminal 3
cd ../agent-factory-voice
code .
```

---

## Managing Worktrees

### List All Worktrees

```bash
git worktree list
```

**Output:**
```
C:/Users/user/Agent Factory           abc1234 [main]
C:/Users/user/agent-factory-research  def5678 [research/research-agent]
C:/Users/user/agent-factory-scriptwriter ghi9012 [content/scriptwriter-agent]
```

### Remove Worktree

```bash
# Option 1: From main directory
cd Agent-Factory/
git worktree remove ../agent-factory-research

# Option 2: From inside worktree
cd ../agent-factory-research
git worktree remove .
```

### Prune Deleted Worktrees

If you manually deleted a worktree directory (not recommended), clean up:

```bash
git worktree prune
```

### Check Worktree Status

```bash
# From any worktree
git status

# From main directory (see all branches)
git branch -a
```

---

## Best Practices

### DO ✅

1. **Always work in worktrees** (pre-commit hook enforces this)
2. **One worktree = one agent** - Keep scope focused
3. **Descriptive branch names** - Use team/agent-agent format
4. **Commit frequently** - Small, focused commits
5. **Update TASK.md** - Mark tasks "In Progress" and "Completed"
6. **Clean up after merge** - Remove worktrees when PRs are merged

### DON'T ❌

1. **Don't commit in main directory** - Pre-commit hook will block you
2. **Don't create worktrees inside Agent Factory/** - Create outside (sibling directories)
3. **Don't manually delete worktree directories** - Use `git worktree remove`
4. **Don't work on multiple features in one worktree** - Create separate worktrees
5. **Don't forget to push branches** - Worktrees aren't backed up automatically

### Pre-Commit Hook Enforcement

Agent Factory has a pre-commit hook that **blocks commits in the main directory**:

```bash
# This will FAIL:
cd Agent-Factory/
git commit -m "feat: something"
# ERROR: Direct commits to main directory are forbidden.
# Use git worktrees for development.
```

```bash
# This will WORK:
cd ../agent-factory-research/
git commit -m "feat: Add Research Agent"
# SUCCESS: Commit allowed in worktree.
```

---

## Troubleshooting

### Error: "fatal: 'path' already exists"

**Problem:** Worktree directory already exists.

**Solution:**
```bash
# Option 1: Remove existing directory
rm -rf ../agent-factory-research

# Option 2: Choose different path
git worktree add ../agent-factory-research-v2 -b research/research-agent
```

### Error: "fatal: invalid reference: branch-name"

**Problem:** Branch name contains invalid characters.

**Solution:** Use valid branch names (letters, numbers, slashes, hyphens):
```bash
# Bad:
git worktree add ../worktree -b "my branch"  # Spaces not allowed

# Good:
git worktree add ../worktree -b "research/my-branch"
```

### Error: "cannot force update the branch 'branch-name' checked out at 'path'"

**Problem:** Trying to checkout a branch that's already checked out in another worktree.

**Solution:**
```bash
# List all worktrees to find where branch is checked out
git worktree list

# Remove that worktree first
git worktree remove <path>

# Then create new worktree
git worktree add <path> <branch>
```

### Worktree is "locked"

**Problem:** Git thinks worktree is in use (usually after crash).

**Solution:**
```bash
# Unlock worktree
git worktree unlock <path>

# Or force remove
git worktree remove <path> --force
```

### Orphaned Worktree (manually deleted)

**Problem:** You deleted worktree directory without using `git worktree remove`.

**Solution:**
```bash
# Clean up git's worktree tracking
git worktree prune

# Verify cleanup
git worktree list
```

---

## Advanced Usage

### Create Worktree from Existing Branch

```bash
# If branch already exists remotely
git fetch origin
git worktree add ../agent-factory-research origin/research/research-agent
```

### Move Worktree to Different Directory

```bash
# Move worktree (Git 2.36+)
git worktree move ../agent-factory-research ../new-location

# Or manually:
# 1. Remove worktree
git worktree remove ../agent-factory-research

# 2. Recreate in new location
git worktree add ../new-location research/research-agent
```

### Lock Worktree (Prevent Removal)

```bash
# Lock worktree (e.g., long-running work)
git worktree lock ../agent-factory-research --reason "In progress, do not remove"

# Unlock when done
git worktree unlock ../agent-factory-research
```

### Repair Corrupted Worktree

```bash
# Repair worktree links
git worktree repair

# Repair specific worktree
git worktree repair ../agent-factory-research
```

---

## Integration with Agent Factory

### Directory Structure

```
Desktop/
├── Agent Factory/              # Main repo (DO NOT COMMIT HERE)
│   ├── .git/                   # Shared git database
│   ├── agent_factory/
│   ├── docs/
│   ├── scripts/
│   └── pyproject.toml
│
├── agent-factory-research/     # Worktree 1
│   ├── agent_factory/
│   ├── agents/
│   │   └── research_agent.py   # New file
│   └── tests/
│
├── agent-factory-scriptwriter/ # Worktree 2
│   ├── agent_factory/
│   ├── agents/
│   │   └── scriptwriter_agent.py  # New file
│   └── tests/
│
└── agent-factory-voice/        # Worktree 3
    ├── agent_factory/
    ├── agents/
    │   └── voice_agent.py      # New file
    └── tests/
```

### Recommended Build Order

Build agents in dependency order:

**Week 2-3 (Foundation):**
1. Research Agent (no dependencies)
2. Atom Builder Agent (depends on: Research)
3. Librarian Agent (depends on: Atom Builder)

**Week 4-5 (Content):**
4. Scriptwriter Agent (depends on: Librarian)
5. Curriculum Agent (depends on: Librarian)
6. SEO Agent (depends on: Curriculum)

**Week 6-7 (Media):**
7. Voice Production Agent (depends on: Scriptwriter)
8. Video Assembly Agent (depends on: Voice)
9. YouTube Uploader Agent (depends on: Video)

**Week 8-10 (Engagement):**
10. Analytics Agent (depends on: YouTube Uploader)
11. Community Agent (depends on: YouTube Uploader)
12. Social Amplifier Agent (depends on: Analytics)

**Week 11-12 (Executive):**
13. Quality Checker Agent (depends on: all research agents)
14. AI Chief of Staff Agent (depends on: all agents)
15. AI CEO Agent (depends on: AI Chief of Staff)

### Automation Scripts

**Create all worktrees:**
```bash
bash scripts/create_all_worktrees.sh
```

**Clean up merged worktrees:**
```bash
bash scripts/cleanup_merged_worktrees.sh
```

---

## Quick Reference

### Common Commands

```bash
# Create worktree
git worktree add <path> -b <branch>

# List worktrees
git worktree list

# Remove worktree
git worktree remove <path>

# Prune deleted worktrees
git worktree prune

# Lock/unlock worktree
git worktree lock <path>
git worktree unlock <path>

# Repair worktree
git worktree repair
```

### Workflow Checklist

- [ ] Create worktree: `git worktree add ../agent-factory-<name> -b <team>/<agent>-agent`
- [ ] Change directory: `cd ../agent-factory-<name>`
- [ ] Update TASK.md: Mark task "In Progress"
- [ ] Make changes, commit frequently
- [ ] Push branch: `git push origin <branch>`
- [ ] Create PR on GitHub
- [ ] After merge: Remove worktree with `git worktree remove <path>`
- [ ] Update TASK.md: Mark task "Completed"

---

## Additional Resources

- **Git Worktree Documentation:** https://git-scm.com/docs/git-worktree
- **Agent Organization:** [docs/AGENT_ORGANIZATION.md](AGENT_ORGANIZATION.md)
- **Implementation Roadmap:** [docs/IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md)
- **Contributing Guide:** [CONTRIBUTING.md](../CONTRIBUTING.md)
- **Task Tracking:** [TASK.md](../TASK.md)

---

## Summary

**Worktrees enable parallel agent development:**
- 18 agents → 18 worktrees → 18 simultaneous developers
- Each agent isolated in its own directory
- Shared git history (one `.git/` database)
- Pre-commit hook enforces worktree usage
- Automation scripts simplify management

**Next Steps:**
1. Run `bash scripts/create_all_worktrees.sh`
2. Start with Research Agent: `cd ../agent-factory-research`
3. Open multiple Claude Code instances for parallel work
4. Build agents according to dependency order

**"One worktree per agent. No conflicts. Pure parallelism."**
