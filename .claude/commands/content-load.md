# content-load

Loads all memory system files to resume work after context clear.

## Prompt

You are resuming work after a context clear. Read and summarize all 5 memory files to restore session context.

**IMPORTANT: Use these exact file paths:**
1. `C:\Users\hharp\OneDrive\Desktop\Agent Factory\PROJECT_CONTEXT.md`
2. `C:\Users\hharp\OneDrive\Desktop\Agent Factory\NEXT_ACTIONS.md`
3. `C:\Users\hharp\OneDrive\Desktop\Agent Factory\DEVELOPMENT_LOG.md`
4. `C:\Users\hharp\OneDrive\Desktop\Agent Factory\ISSUES_LOG.md`
5. `C:\Users\hharp\OneDrive\Desktop\Agent Factory\DECISIONS_LOG.md`

### Files to Read (in order)

1. **PROJECT_CONTEXT.md**
   - Read ONLY the newest entry (first entry after file header)
   - Extract: Project name, current phase, status, recent changes, blockers, next steps

2. **NEXT_ACTIONS.md**
   - Read CRITICAL and HIGH priority sections only
   - Extract: Top 3 immediate actions with their status

3. **DEVELOPMENT_LOG.md**
   - Read ONLY the most recent date section
   - Extract: What was built, what was changed, testing results

4. **ISSUES_LOG.md**
   - Read entries with status [OPEN] only
   - Extract: Active issues that need attention

5. **DECISIONS_LOG.md**
   - Read the 3 most recent decisions
   - Extract: What was decided and why

## Output Format

Provide a concise resume in this exact format:

```
# Session Resume [YYYY-MM-DD]

## Current Status
[From PROJECT_CONTEXT: phase, status, what's working]

## Immediate Tasks
1. [From NEXT_ACTIONS: highest priority task]
2. [From NEXT_ACTIONS: second priority task]
3. [From NEXT_ACTIONS: third priority task]

## Last Session Summary
[From DEVELOPMENT_LOG: brief summary of last activities]

## Open Issues
[From ISSUES_LOG: list of OPEN issues or "None"]

## Recent Decisions
[From DECISIONS_LOG: 1-2 most impactful recent decisions]

## Ready to Continue
[Yes/No - are there blockers?]
```

## Instructions

1. Read the 5 memory files in order using the exact paths above
2. Extract ONLY the most recent/relevant information from each
3. Use the exact output format specified above
4. Be concise - focus on actionable information
5. Identify any blockers that would prevent continuing work
6. Provide clear understanding of what to do next

## Success Criteria

After running this command:
- [ ] All 5 memory files read
- [ ] Context restored without reading entire files
- [ ] Only most recent/relevant information surfaced
- [ ] Clear understanding of what to do next
- [ ] User can immediately continue work

## Usage Notes

- Run this command at the start of a new session after `/content-clear`
- Expected completion time: 30-60 seconds
- Provides complete context to resume work
- Pairs with `/content-clear` for complete session management

## Example Output

```
# Session Resume 2025-12-06

## Current Status
**Project:** Agent Factory
**Phase:** Interactive Agent Creation Wizard (Phase 3 Extension)
**Status:** ✅ Wizard Complete - Ready for Manual Testing

**What's Working:**
- Interactive CLI wizard for agent creation
- 4 pre-built templates (researcher, coder, analyst, file_manager)
- 7-step guided flow with input validation
- Auto-generates spec + agent code + tests

## Immediate Tasks
1. [HIGH] Test /content-clear and /content-load commands manually
2. [MEDIUM] Consider Phase 5 (Project Twin) or Phase 6 (Agent-as-Service)
3. [LOW] Clean up duplicate memory files in docs/memory/

## Last Session Summary
Fixed slash command names (context→content), added explicit file paths to both commands, updated interactive wizard with robust input validation.

## Open Issues
None

## Recent Decisions
- Use explicit file paths in slash commands (prevents ambiguity)
- Rename commands to match invocation format (content-clear/content-load)

## Ready to Continue
Yes - Slash commands fixed, ready for manual testing
```
