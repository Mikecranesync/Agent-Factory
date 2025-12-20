# MCP Session Optimization Guide

**Purpose:** Reduce context token usage by selectively enabling/disabling MCP servers based on task requirements

**Token Impact:** Save up to 67k tokens (33% of context budget) by disabling unused servers

---

## Quick Reference

### Current MCP Server Inventory

| Server | Tools | Token Cost | Always Needed? |
|--------|-------|------------|----------------|
| `backlog` | 13 | ~10k | ✅ YES (task management) |
| `filesystem` | 14 | ~12k | ✅ YES (file operations) |
| `memory` | 9 | ~8k | ✅ YES (knowledge graph) |
| `github` | 26 | ~22k | ⚠️ CONDITIONAL (PR creation only) |
| `playwright` | 18 | ~15k | ⚠️ CONDITIONAL (browser automation only) |
| **TOTAL** | **80** | **~67k** | - |

**Core Servers (Always Enabled - 37 tools, ~30k tokens):**
- backlog, filesystem, memory

**Conditional Servers (Enable as Needed - 44 tools, ~37k tokens):**
- github, playwright

---

## Usage Patterns

### Scenario 1: Focused Development Work
**Tasks:** Writing code, running tests, refactoring, debugging
**MCP Config:**
```bash
# Keep enabled: backlog, filesystem, memory
# Disable: github, playwright

/mcp disable github
/mcp disable playwright
```
**Token Savings:** ~37k tokens (18.5% of budget)

---

### Scenario 2: PR Creation & GitHub Operations
**Tasks:** Creating pull requests, reviewing code, managing issues
**MCP Config:**
```bash
# Keep enabled: backlog, filesystem, memory, github
# Disable: playwright

/mcp enable github
/mcp disable playwright
```
**Token Savings:** ~15k tokens (7.5% of budget)

---

### Scenario 3: Browser Automation
**Tasks:** Web scraping, UI testing, automation workflows
**MCP Config:**
```bash
# Keep enabled: backlog, filesystem, memory, playwright
# Disable: github

/mcp disable github
/mcp enable playwright
```
**Token Savings:** ~22k tokens (11% of budget)

---

### Scenario 4: Maximum Context Availability
**Tasks:** Long planning sessions, complex analysis, extensive exploration
**MCP Config:**
```bash
# Disable all conditional servers
/mcp disable github
/mcp disable playwright

# Consider also running /compact
/compact
```
**Token Savings:** ~37k tokens + compaction savings

---

## MCP Management Commands

### List Active Servers
```bash
/mcp
```
**Output:** Shows all currently enabled MCP servers

### Disable Server
```bash
/mcp disable <server-name>
```
**Example:**
```bash
/mcp disable playwright
```

### Enable Server
```bash
/mcp enable <server-name>
```
**Example:**
```bash
/mcp enable github
```

---

## Recommended Workflows

### Daily Development Workflow
1. **Start session** - Disable github and playwright by default
   ```bash
   /mcp disable github
   /mcp disable playwright
   ```
2. **Check context usage**
   ```bash
   /context
   ```
   Should show ~30k tokens for core MCP servers

3. **Enable conditionally** - Only when needed for specific tasks

### PR Creation Workflow
1. **Finish feature work** in minimal MCP mode
2. **Enable github** when ready to create PR
   ```bash
   /mcp enable github
   ```
3. **Create PR** using github MCP tools
4. **Disable github** after PR created
   ```bash
   /mcp disable github
   ```

---

## Context Budget Examples

### Before Optimization (All Servers Enabled)
```
MCP Tools: 67k tokens (33.5%)
Extended Thinking: 50k tokens (25%)
CLAUDE.md: 10k tokens (5%)
Conversation: 30k tokens (15%)
Available: 43k tokens (21.5%)
---
Total: 200k tokens
```

### After Optimization (Core Servers Only)
```
MCP Tools: 30k tokens (15%)
Extended Thinking: 0k tokens (DISABLED)
CLAUDE.md: 6k tokens (RESTRUCTURED)
Conversation: 30k tokens (15%)
Available: 134k tokens (67%)
---
Total: 200k tokens
```

**Improvement:** 91k more tokens available for work (212% increase)

---

## Server-Specific Details

### backlog (13 tools, ~10k tokens)
**Always Enable:** ✅ YES
**Why:** Core task management, used in every session
**Tools include:**
- task_create, task_list, task_edit, task_view
- document_create, document_search
- milestone_add, milestone_list

### filesystem (14 tools, ~12k tokens)
**Always Enable:** ✅ YES
**Why:** Essential file operations
**Tools include:**
- read_text_file, write_file, edit_file
- create_directory, list_directory
- search_files, get_file_info

### memory (9 tools, ~8k tokens)
**Always Enable:** ✅ YES
**Why:** Knowledge graph for context persistence
**Tools include:**
- create_entities, create_relations
- add_observations, search_nodes
- read_graph, open_nodes

### github (26 tools, ~22k tokens)
**Enable When:** Creating PRs, managing issues, code reviews
**Disable When:** General development work
**Tools include:**
- create_pull_request, create_issue
- search_repositories, fork_repository
- create_branch, merge_pull_request

### playwright (18 tools, ~15k tokens)
**Enable When:** Browser automation, web scraping, UI testing
**Disable When:** All other work (95% of sessions)
**Tools include:**
- browser_navigate, browser_click
- browser_snapshot, browser_screenshot
- browser_evaluate, browser_fill_form

---

## Pro Tips

1. **Start minimal** - Begin every session with only core servers enabled
2. **Check before enabling** - Use `/context` to verify you have enough tokens before adding servers
3. **Disable after use** - Immediately disable conditional servers after completing specific tasks
4. **Use slash commands** - Create custom commands for common configurations (see below)
5. **Monitor token usage** - Run `/context` periodically to track consumption

---

## Custom Slash Commands (Optional)

Create these in `.claude/commands/` for one-command optimization:

### /context-minimal.md
```markdown
Optimize for focused development:
1. Disable github and playwright MCP servers
2. Run /compact to compress conversation
3. Report token savings
```

### /context-pr.md
```markdown
Optimize for PR creation:
1. Enable github MCP server
2. Disable playwright MCP server
3. Run /compact
```

### /context-status.md
```markdown
Show current context breakdown:
1. Run /context command
2. Show active MCP servers
3. Recommend optimizations
```

---

## Troubleshooting

### Problem: Command not found when MCP server disabled
**Solution:** Re-enable the server temporarily, complete task, then disable again

### Problem: Not sure which server provides a tool
**Solution:** Check this guide or use `/mcp` to see server descriptions

### Problem: Token usage still high after disabling servers
**Solution:**
1. Check `/context` for other sources (conversation history, extended thinking)
2. Run `/compact` to compress conversation
3. Verify settings.json has `alwaysThinkingEnabled: false`

---

## References

- **Context Optimization Plan:** `C:\Users\hharp\.claude\plans\graceful-booping-walrus.md`
- **Settings File:** `C:\Users\hharp\.claude\settings.json`
- **Main Instructions:** `CLAUDE.md` (see Context Optimization section)
