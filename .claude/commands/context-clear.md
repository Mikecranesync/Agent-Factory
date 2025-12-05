# context-clear

Updates all memory system files to preserve context before session ends.

## Prompt

You are preparing for a context clear. Update all 5 memory files with current session information:

### 1. PROJECT_CONTEXT.md
- Add new timestamped entry at TOP with current project status
- Include: Current phase, what's working, what's blocked, recent changes
- Format: `## [YYYY-MM-DD HH:MM] Current Status`

### 2. NEXT_ACTIONS.md
- Update CRITICAL section if there are blocking issues
- Add new HIGH priority tasks from current work
- Remove or mark completed any finished tasks
- Format: Maintain priority sections (CRITICAL, HIGH, MEDIUM)

### 3. DEVELOPMENT_LOG.md
- Add new timestamped entry at TOP with today's activities
- Include: What was built, what was fixed, what was changed
- List new files created, modified files, tools added
- Format: `## [YYYY-MM-DD] Session Title` then `### [HH:MM] Activity`

### 4. ISSUES_LOG.md
- Add any new issues discovered (status: [OPEN])
- Update status of existing issues if they were fixed (status: [FIXED])
- Include: Problem, root cause, impact, proposed solution
- Format: `## [YYYY-MM-DD HH:MM] STATUS: Title`

### 5. DECISIONS_LOG.md
- Add any technical decisions made during session
- Include: Decision, rationale, alternatives considered
- Document why choices were made
- Format: `## [YYYY-MM-DD HH:MM] Decision Title`

## Instructions

1. Read current state of all 5 files
2. Analyze the current session:
   - What work was done?
   - What tasks are pending from PROGRESS.md?
   - What issues were encountered or fixed?
   - What decisions were made?
3. Update each file with new timestamped entries at the TOP
4. Use reverse chronological order (newest first)
5. Preserve all existing content
6. Report what was saved to each file

## Format Requirements

- All timestamps: `[YYYY-MM-DD HH:MM]` format
- Use 24-hour time
- Add entries at TOP of each file (reverse chronological)
- Use `---` separator between entries
- Keep entries concise but complete
- No information mixing between files

## Success Criteria

After running this command:
- [ ] All 5 files updated with current session info
- [ ] Timestamps added to new entries
- [ ] Entries added at TOP (newest first)
- [ ] Existing content preserved
- [ ] Summary report provided to user

## Report Template

After updating, report:

```
Context saved for session [YYYY-MM-DD HH:MM]:

PROJECT_CONTEXT.md
- [Brief summary of status update]

NEXT_ACTIONS.md
- [Number] new/updated actions

DEVELOPMENT_LOG.md
- [Summary of activities logged]

ISSUES_LOG.md
- [Number] new issues: [brief list]
- [Number] updated issues: [brief list]

DECISIONS_LOG.md
- [Number] new decisions: [brief list]

All files ready for context reload.
```
