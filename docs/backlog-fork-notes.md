# Backlog.md Fork Documentation

## Fork Details

**Fork URL:** https://github.com/Mikecranesync/Backlog.md
**Upstream:** https://github.com/MrLesk/Backlog.md
**Created:** 2025-12-18
**Purpose:** Ensure Agent Factory has control over Backlog.md dependency (independence from upstream changes)

## Why We Forked

1. **Dependency Stability** - Upstream repo could change breaking APIs or disappear entirely
2. **Custom Modifications** - May need Agent Factory-specific features in the future
3. **Long-term Support** - Can maintain our own version if upstream becomes unmaintained
4. **Build Reproducibility** - Control exact version used in production

## Fork Synchronization Strategy

**Policy:** We synchronize with upstream periodically, but always test before merging.

**Sync Process:**
```bash
# 1. Add upstream remote (one-time setup)
cd /path/to/backlog-fork
git remote add upstream https://github.com/MrLesk/Backlog.md.git

# 2. Fetch upstream changes
git fetch upstream

# 3. Review changes before merging
git log HEAD..upstream/main --oneline

# 4. Merge upstream into fork (create PR for review)
git checkout -b sync-upstream-$(date +%Y%m%d)
git merge upstream/main
git push origin sync-upstream-$(date +%Y%m%d)

# 5. Open PR on GitHub, test in staging, then merge
gh pr create --title "chore: Sync with upstream Backlog.md" --body "Syncs changes from MrLesk/Backlog.md as of $(date)"
```

**Sync Frequency:** Every 3-6 months, or when critical upstream fixes are released

## Building Backlog CLI from Fork

### Prerequisites

- Node.js 18+ (LTS recommended)
- npm or pnpm
- Git

### Build Instructions

**Option 1: Build from Source (Recommended for Development)**

```bash
# 1. Clone the fork
git clone https://github.com/Mikecranesync/Backlog.md.git
cd Backlog.md

# 2. Install dependencies
npm install

# 3. Build the CLI
npm run build

# 4. Link globally for local testing
npm link

# 5. Verify installation
backlog --version
# Should output: backlog/1.28.0 or similar
```

**Option 2: Install from GitHub Release (Recommended for Production)**

```bash
# Install specific release from fork
npm install -g https://github.com/Mikecranesync/Backlog.md/releases/download/v1.28.0/backlog-1.28.0.tgz

# Or install latest main branch
npm install -g git+https://github.com/Mikecranesync/Backlog.md.git
```

**Option 3: Install from Local Tarball (Air-gapped/Offline)**

```bash
# Create tarball archive (do this once)
cd Backlog.md
npm pack
# Output: backlog-1.28.0.tgz

# Copy tarball to long-term storage
cp backlog-1.28.0.tgz ~/backups/vendor/backlog/

# Install from tarball
npm install -g ~/backups/vendor/backlog/backlog-1.28.0.tgz
```

### Verifying Fork Installation

**Test Basic Commands:**
```bash
# 1. Check version
backlog --version

# 2. Test task operations
cd /path/to/Agent-Factory
backlog task list --status "To Do"

# 3. Test task view
backlog task view task-23.1

# 4. Test task board
backlog board

# 5. Test task creation
backlog task create --title "TEST: Verify fork works" --priority low
backlog task list | grep "TEST: Verify fork works"
# Clean up test task
backlog task edit <test-task-id> --status "Done"
```

**Expected Output:**
- All commands should work identically to upstream Backlog.md
- No errors or warnings about missing dependencies
- Task operations should sync correctly with `backlog/tasks/*.md` files

### Troubleshooting

**Error: "backlog: command not found" after install**
```bash
# Check npm global bin directory is in PATH
npm config get prefix
# Should be in your PATH (usually /usr/local or ~/.npm-global)

# Add to PATH if missing (Linux/Mac)
echo 'export PATH="$(npm config get prefix)/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Windows: Add npm global directory to PATH via System Environment Variables
```

**Error: "Cannot find module '@oclif/core'" during build**
```bash
# Clean install dependencies
rm -rf node_modules package-lock.json
npm install
npm run build
```

**Error: Tests fail after syncing upstream**
```bash
# Run test suite to identify breaking changes
npm test

# If tests fail, review upstream changes
git log upstream/main --oneline

# Consider reverting problematic commits
git revert <commit-hash>
```

## Custom Modifications (Future)

**Current Status:** Fork is 1:1 with upstream (no modifications yet)

**Planned Modifications:**
- [ ] Add Agent Factory-specific commands (`backlog ai-loop status`)
- [ ] Integrate with headless orchestrator (webhook triggers)
- [ ] Add cost/time tracking fields to task schema
- [ ] Export tasks to JSON for dashboard API consumption

**Modification Workflow:**
1. Create feature branch from fork main
2. Implement changes
3. Add tests for new functionality
4. Document in this file under "Custom Modifications"
5. Merge to fork main (separate from upstream syncs)

## Long-term Archival

**Tarball Mirror Location:**
```
~/backups/vendor/backlog/
├── backlog-1.28.0.tgz          # Initial fork version
├── backlog-1.29.0-custom.tgz   # Future custom release
└── README.txt                   # Archive index
```

**GitHub Release Strategy:**
- Tag fork releases as `v1.28.0-agent-factory` (suffix distinguishes from upstream)
- Attach tarball to GitHub release
- Document changes in release notes

**Disaster Recovery:**
If GitHub goes down or fork is deleted:
1. Extract tarball from `~/backups/vendor/backlog/`
2. Install from tarball: `npm install -g ./backlog-1.28.0.tgz`
3. Restore fork from local git clone (if needed)

## Integration with Agent Factory

**Current Setup:**
- Agent Factory uses globally installed `backlog` CLI
- MCP server provides `backlog` tools to Claude
- Tasks managed in `backlog/tasks/*.md` files
- TASK.md synced via `scripts/backlog/sync_tasks.py`

**Fork Integration Points:**
1. **CLI Commands:** All `backlog task *` commands use fork
2. **MCP Tools:** `mcp__backlog__*` tools call fork's Node.js API
3. **Sync Script:** Reads/writes fork's task file format
4. **Future:** Headless orchestrator will invoke fork programmatically

**Testing Fork Integration:**
```bash
# 1. Verify backlog CLI is from fork
which backlog
# Should point to npm global bin

# 2. Test MCP tools
poetry run python -c "from mcp import get_mcp_servers; print('backlog' in get_mcp_servers())"

# 3. Test sync script
poetry run python scripts/backlog/sync_tasks.py --dry-run

# 4. Verify tasks are readable
backlog task list --status "In Progress"
```

## References

**Upstream Documentation:**
- https://github.com/MrLesk/Backlog.md/blob/main/README.md - Original README
- https://github.com/MrLesk/Backlog.md/blob/main/docs/ - Full documentation

**Fork Specific:**
- https://github.com/Mikecranesync/Backlog.md - Our fork
- https://github.com/Mikecranesync/Backlog.md/releases - Our releases

**Related Agent Factory Docs:**
- `backlog/README.md` - Backlog.md workflow guide
- `docs/ai-dev-loop-architecture.md` - How fork fits into AI Dev Loop
- `scripts/backlog/sync_tasks.py` - Task synchronization script

---

**Status:** Fork operational as of 2025-12-18
**Next Review:** 2026-03-18 (sync with upstream if needed)
**Maintainer:** Agent Factory team (Mikecranesync)
