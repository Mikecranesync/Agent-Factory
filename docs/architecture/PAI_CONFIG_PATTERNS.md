# PAI-Config-Windows Patterns

**Created**: 2025-12-21
**Phase**: Knowledge Extraction (Week 3)
**Purpose**: Document Windows AI infrastructure patterns from pai-config-windows

---

## Overview

pai-config-windows is a Windows-specific infrastructure layer that enables Personal AI (PAI) workflows with Claude Code. It provides hooks, event capture, context synchronization, and Windows-native integrations that make AI development seamless on Windows platforms.

**Core Insight**: AI agents need OS-level integration (notifications, credential management, persistent configuration) to feel native rather than bolted-on.

**Key Patterns**:
1. **Hook/Event System** - Lifecycle hooks for automation (onSessionStart, onTaskComplete, etc.)
2. **Context Synchronization** - Checkpoint-based state restoration across sessions
3. **Windows Integration** - PowerShell, Credential Manager, environment persistence
4. **Configuration Versioning** - Snapshot + rollback for safe config changes
5. **Multi-App Coordination** - Shared context across Friday, Jarvis, RIVET
6. **Voice Notification System** - ElevenLabs TTS for ambient status updates
7. **Research Workflow** - Cost-optimized multi-model research strategy
8. **Markdown Skills** - Tier-based context loading for skill system

---

## Pattern 1: Hook/Event System

**Problem**: Need to react to AI lifecycle events (session start, tool use, task completion) without hardcoding logic into Claude Code.

**Solution**: TypeScript hook system with standardized event payloads.

### Architecture

```
Claude Code Event
    ↓
Hook Registry (settings.json)
    ↓
Load Hook Module (TypeScript)
    ↓
Execute Hook Handler
    ├── Access event payload
    ├── Execute custom logic
    └── Return (async)
    ↓
Continue Claude Code Execution
```

### Configuration

**settings.json**:
```json
{
  "hooks": {
    "onSessionStart": "hooks/initialize-pai-session.ts",
    "onToolUse": "hooks/capture-all-events.ts",
    "onTaskComplete": "hooks/on-task-complete.ts",
    "onPromptSubmit": "hooks/load-core-context.ts"
  }
}
```

### Hook Implementation

**hooks/initialize-pai-session.ts**:
```typescript
import { HookContext } from './types'

export async function onSessionStart(context: HookContext): Promise<void> {
  // Load user preferences
  const prefs = await loadPreferences()

  // Set environment variables
  process.env.DEFAULT_MODEL = prefs.default_model
  process.env.VOICE_ID = prefs.voice_id

  // Initialize context
  await initializeContext({
    user_id: prefs.user_id,
    session_id: context.session_id,
    start_time: Date.now()
  })

  // Log session start
  console.log(`[PAI] Session started: ${context.session_id}`)
}
```

**hooks/capture-all-events.ts**:
```typescript
import { ToolUseEvent } from './types'

export async function onToolUse(event: ToolUseEvent): Promise<void> {
  // Capture all tool usage for analytics
  await logEvent({
    timestamp: Date.now(),
    tool_name: event.tool_name,
    parameters: event.parameters,
    success: event.success,
    duration_ms: event.duration_ms
  })

  // Track costs for LLM calls
  if (event.tool_name === 'llm.complete') {
    await trackCost({
      model: event.parameters.model,
      tokens: event.result.usage.total_tokens,
      cost_usd: event.result.usage.total_cost_usd
    })
  }
}
```

**hooks/on-task-complete.ts**:
```typescript
import { TaskCompleteEvent } from './types'

export async function onTaskComplete(event: TaskCompleteEvent): Promise<void> {
  // Save checkpoint (context restoration point)
  await saveCheckpoint({
    task_id: event.task_id,
    phase: 'completed',
    progress: 1.0,
    state: event.final_state
  })

  // Update Backlog.md
  await updateTask(event.task_id, {
    status: 'Done',
    completed_at: Date.now(),
    notes: [`Completed in ${event.duration_ms}ms`]
  })

  // Send voice notification
  await notifyVoice(`Task ${event.task_id} completed successfully`)
}
```

### Event Types

```typescript
// Hook context (all hooks receive this)
interface HookContext {
  session_id: string
  user_id: string
  timestamp: number
  event: any  // Event-specific payload
}

// Session events
interface SessionStartEvent {
  session_id: string
  working_directory: string
}

// Tool events
interface ToolUseEvent {
  tool_name: string
  parameters: any
  result: any
  success: boolean
  duration_ms: number
}

// Task events
interface TaskCompleteEvent {
  task_id: string
  duration_ms: number
  final_state: any
}
```

### Benefits

**1. Decoupled Logic**:
- Hooks are separate TypeScript modules
- Easy to add/remove/modify hooks
- No core code changes needed

**2. Async Execution**:
- Hooks run asynchronously (don't block main flow)
- Errors in hooks logged but don't crash session

**3. Composable**:
- Multiple hooks can respond to same event
- Execution order controlled via priority

---

## Pattern 2: Context Synchronization

**Problem**: AI sessions lose context when interrupted (power loss, crash, manual restart).

**Solution**: Checkpoint-based state restoration with CHECKPOINT.md protocol.

### Architecture

```
AI Session (In Progress)
    ↓
Periodic Checkpoint (every 5 minutes)
    ├── Save state: {phase, progress, context}
    ├── Write CHECKPOINT.md
    └── Persist to disk
    ↓
Session Interrupted (crash, restart)
    ↓
New Session Starts
    ↓
Detect CHECKPOINT.md
    ├── Read last checkpoint
    ├── Restore state
    └── Continue from saved progress
    ↓
AI Resumes Work (no lost context)
```

### Checkpoint Structure

**CHECKPOINT.md**:
```markdown
---
checkpoint_id: ckpt-1234567890
session_id: sess-abc123
phase: implementation
progress: 0.75
task_id: task-56
created_at: 2025-12-21T15:30:00Z
---

# Checkpoint: LRU Cache Implementation

## Current Phase
Implementation (75% complete)

## What's Done
- [x] Created cache.py module
- [x] Implemented LRU eviction
- [x] Added TTL support

## What's Next
- [ ] Integrate with LLMRouter
- [ ] Add tests
- [ ] Validate imports

## Context
Working on task-56 (LRU cache with TTL). Implemented core caching logic, now integrating with router. Next step: write tests in `tests/test_cache.py`.

## State
```json
{
  "current_file": "agent_factory/llm/cache.py",
  "test_file": "tests/test_cache.py",
  "files_modified": ["cache.py", "router.py"],
  "validation_pending": true
}
```
```

### Implementation

**Save Checkpoint**:
```typescript
interface Checkpoint {
  checkpoint_id: string
  session_id: string
  phase: string  // "planning", "implementation", "testing", "done"
  progress: number  // 0.0-1.0
  task_id: string
  created_at: string
  context: string  // Markdown description
  state: any  // JSON state
}

async function saveCheckpoint(checkpoint: Checkpoint): Promise<void> {
  // Write CHECKPOINT.md
  const content = buildCheckpointMarkdown(checkpoint)
  await fs.writeFile('CHECKPOINT.md', content)

  // Also save JSON for programmatic access
  await fs.writeFile('.checkpoint.json', JSON.stringify(checkpoint, null, 2))

  console.log(`[PAI] Checkpoint saved: ${checkpoint.phase} (${checkpoint.progress * 100}%)`)
}
```

**Restore Checkpoint**:
```typescript
async function restoreCheckpoint(): Promise<Checkpoint | null> {
  // Check if checkpoint exists
  if (!await fs.exists('CHECKPOINT.md')) {
    return null
  }

  // Load checkpoint
  const content = await fs.readFile('CHECKPOINT.md', 'utf-8')
  const checkpoint = parseCheckpointMarkdown(content)

  // Restore state
  console.log(`[PAI] Restoring checkpoint: ${checkpoint.phase} (${checkpoint.progress * 100}%)`)

  return checkpoint
}
```

**Auto-Checkpoint Hook**:
```typescript
// Automatically checkpoint every 5 minutes during work
let checkpointInterval: NodeJS.Timeout

export async function onSessionStart(context: HookContext): Promise<void> {
  // Restore previous checkpoint if exists
  const checkpoint = await restoreCheckpoint()
  if (checkpoint) {
    console.log(`[PAI] Resuming from checkpoint: ${checkpoint.phase}`)
    // Inject context into session
    await injectContext(checkpoint.context)
  }

  // Start auto-checkpoint timer
  checkpointInterval = setInterval(async () => {
    await autoCheckpoint(context.session_id)
  }, 5 * 60 * 1000)  // Every 5 minutes
}

export async function onSessionEnd(): Promise<void> {
  clearInterval(checkpointInterval)
}
```

### Benefits

**1. Fault Tolerance**:
- Power loss → resume from last checkpoint (max 5 min lost)
- Crash → restore state automatically

**2. Context Preservation**:
- Long-running tasks don't lose progress
- Multi-day tasks resume seamlessly

**3. Human Visibility**:
- CHECKPOINT.md is human-readable
- Easy to see what was being worked on

---

## Pattern 3: Windows Integration

**Problem**: AI tools need native Windows integration (env vars, credentials, PowerShell).

**Solution**: PowerShell automation + Credential Manager + registry persistence.

### PowerShell Profile Integration

**Microsoft.PowerShell_profile.ps1**:
```powershell
# Load PAI environment variables
if (Test-Path "$env:USERPROFILE\.pai\env.ps1") {
    . "$env:USERPROFILE\.pai\env.ps1"
}

# Initialize PAI context
function Initialize-PAI {
    $config = Get-Content "$env:USERPROFILE\.pai\config.json" | ConvertFrom-Json

    # Set environment variables
    $env:DEFAULT_MODEL = $config.default_model
    $env:VOICE_ID = $config.voice_id

    # Load credentials from Windows Credential Manager
    $openai_key = Get-StoredCredential -Target "pai:openai"
    $env:OPENAI_API_KEY = $openai_key.GetNetworkCredential().Password

    Write-Host "[PAI] Environment initialized"
}

# Auto-initialize on shell start
Initialize-PAI
```

### Credential Manager Integration

**Store Credentials**:
```typescript
import { execSync } from 'child_process'

function storeCredential(target: string, username: string, password: string): void {
  // Use PowerShell to store in Windows Credential Manager
  const ps = `
    $securePassword = ConvertTo-SecureString "${password}" -AsPlainText -Force
    $credential = New-Object System.Management.Automation.PSCredential("${username}", $securePassword)
    $credential.Password | ConvertFrom-SecureString | Set-Content "$env:USERPROFILE\\.pai\\creds\\${target}.txt"
  `

  execSync(`powershell -Command "${ps}"`, { encoding: 'utf-8' })
  console.log(`[PAI] Credential stored: ${target}`)
}
```

**Retrieve Credentials**:
```typescript
function getCredential(target: string): string {
  const ps = `
    $encrypted = Get-Content "$env:USERPROFILE\\.pai\\creds\\${target}.txt"
    $secureString = ConvertTo-SecureString $encrypted
    $credential = New-Object System.Management.Automation.PSCredential("user", $secureString)
    $credential.GetNetworkCredential().Password
  `

  const password = execSync(`powershell -Command "${ps}"`, { encoding: 'utf-8' }).trim()
  return password
}
```

### Persistent Environment Variables

**Set Persistent Env Var**:
```typescript
function setEnvPersistent(name: string, value: string, scope: 'User' | 'Machine' = 'User'): void {
  const ps = `
    [System.Environment]::SetEnvironmentVariable("${name}", "${value}", "${scope}")
  `

  execSync(`powershell -Command "${ps}"`, { encoding: 'utf-8' })
  console.log(`[PAI] Environment variable set: ${name}=${value} (${scope})`)
}
```

**Get Env Var**:
```typescript
function getEnvPersistent(name: string): string | null {
  const ps = `
    [System.Environment]::GetEnvironmentVariable("${name}", "User")
  `

  const value = execSync(`powershell -Command "${ps}"`, { encoding: 'utf-8' }).trim()
  return value || null
}
```

---

## Pattern 4: Configuration Versioning

**Problem**: Config changes can break workflows, need rollback mechanism.

**Solution**: Snapshot config before changes, enable one-click rollback.

### Architecture

```
Current Config: config.json
    ↓
User Makes Change
    ↓
Snapshot Current Config
    ├── Timestamp: 2025-12-21T15:30:00Z
    ├── Description: "Changed default model"
    └── File: .pai/snapshots/config-1234567890.json
    ↓
Apply New Config
    ├── config.json updated
    └── .pai/current-version.txt → snapshot ID
    ↓
If Breaks:
    ↓
Rollback to Snapshot
    └── Restore config-1234567890.json → config.json
```

### Implementation

**Snapshot Config**:
```typescript
interface ConfigSnapshot {
  snapshot_id: string
  timestamp: string
  description: string
  config: any
}

async function snapshotConfig(description: string): Promise<string> {
  const snapshot_id = `config-${Date.now()}`

  // Read current config
  const config = await fs.readJSON('config.json')

  // Create snapshot
  const snapshot: ConfigSnapshot = {
    snapshot_id,
    timestamp: new Date().toISOString(),
    description,
    config
  }

  // Save snapshot
  await fs.writeJSON(`.pai/snapshots/${snapshot_id}.json`, snapshot, { spaces: 2 })

  console.log(`[PAI] Config snapshot created: ${snapshot_id}`)
  return snapshot_id
}
```

**Rollback Config**:
```typescript
async function rollbackConfig(snapshot_id?: string): Promise<void> {
  // If no ID provided, use last snapshot
  if (!snapshot_id) {
    const snapshots = await fs.readdir('.pai/snapshots')
    snapshots.sort().reverse()  // Most recent first
    snapshot_id = snapshots[0].replace('.json', '')
  }

  // Load snapshot
  const snapshot = await fs.readJSON(`.pai/snapshots/${snapshot_id}.json`)

  // Restore config
  await fs.writeJSON('config.json', snapshot.config, { spaces: 2 })

  console.log(`[PAI] Config rolled back to: ${snapshot.description} (${snapshot.timestamp})`)
}
```

**Usage**:
```typescript
// Before changing config
await snapshotConfig("Changing default model to GPT-4o")

// Change config
const config = await fs.readJSON('config.json')
config.default_model = "gpt-4o"
await fs.writeJSON('config.json', config, { spaces: 2 })

// If something breaks
await rollbackConfig()  // Restore previous config
```

---

## Pattern 5: Multi-App Coordination

**Problem**: Multiple AI apps (Friday, Jarvis, RIVET) need shared context and coordination.

**Solution**: Shared session registry + context synchronization.

### Architecture

```
Friday (Voice AI)
    ↓
Register Session
    ├── Session ID: sess-friday-123
    ├── App Name: "Friday"
    └── Shared Context: {user_prefs, current_task}
    ↓
Jarvis (Workflow Manager)
    ↓
Read Shared Context
    ├── Get Friday's session data
    └── Continue user's workflow
    ↓
Update Shared Context
    └── Task status → shared with Friday
```

### Implementation

**Session Registry**:
```typescript
interface AppSession {
  session_id: string
  app_name: string
  started_at: string
  last_active: string
  context: any
}

class MultiAppCoordinator {
  private registry: Map<string, AppSession> = new Map()

  registerSession(app_name: string, session_id: string): void {
    const session: AppSession = {
      session_id,
      app_name,
      started_at: new Date().toISOString(),
      last_active: new Date().toISOString(),
      context: {}
    }

    this.registry.set(session_id, session)
    console.log(`[PAI] Session registered: ${app_name} (${session_id})`)
  }

  setSharedContext(session_id: string, key: string, value: any): void {
    const session = this.registry.get(session_id)
    if (session) {
      session.context[key] = value
      session.last_active = new Date().toISOString()
    }
  }

  getSharedContext(app_name: string, key: string): any | null {
    // Find most recent session for app
    for (const session of this.registry.values()) {
      if (session.app_name === app_name) {
        return session.context[key] || null
      }
    }
    return null
  }
}
```

**Usage**:
```typescript
const coordinator = new MultiAppCoordinator()

// Friday registers session
coordinator.registerSession("Friday", "sess-friday-123")

// Friday sets user preference
coordinator.setSharedContext("sess-friday-123", "user_prefs", {
  voice_speed: 1.2,
  preferred_model: "gpt-4o-mini"
})

// Jarvis reads Friday's context
const prefs = coordinator.getSharedContext("Friday", "user_prefs")
console.log(`Using model: ${prefs.preferred_model}`)
```

---

## Pattern 6: Voice Notification System

**Problem**: Long-running tasks need ambient status updates (user not watching screen).

**Solution**: ElevenLabs TTS integration for voice notifications.

### Implementation

**Voice Notification**:
```typescript
import { ElevenLabsClient } from 'elevenlabs'

async function notifyVoice(message: string): Promise<void> {
  // Get voice ID from config
  const voice_id = process.env.VOICE_ID || 'default_voice'

  // Generate TTS
  const client = new ElevenLabsClient({ apiKey: process.env.ELEVENLABS_API_KEY })

  const audio = await client.textToSpeech.convert(voice_id, {
    text: message,
    model_id: 'eleven_monolingual_v1',
    voice_settings: {
      stability: 0.5,
      similarity_boost: 0.75
    }
  })

  // Play audio via Windows
  const tempFile = `${os.tmpdir()}/pai-notify-${Date.now()}.mp3`
  await fs.writeFile(tempFile, Buffer.from(await audio.arrayBuffer()))

  // Play using PowerShell
  execSync(`powershell -Command "Add-Type -AssemblyName presentationCore; (New-Object Media.SoundPlayer '${tempFile}').PlaySync()"`)
}
```

**Usage in Hooks**:
```typescript
export async function onTaskComplete(event: TaskCompleteEvent): Promise<void> {
  await notifyVoice(`Task ${event.task_id} completed successfully`)
}

export async function onError(event: ErrorEvent): Promise<void> {
  await notifyVoice(`Error occurred: ${event.error_message}`)
}
```

---

## Pattern 7: Research Workflow Optimization

**Problem**: Research tasks are expensive (multiple LLM calls, web searches).

**Solution**: Cost-optimized multi-model strategy with result caching.

### Strategy

```
Research Query: "How do I implement LRU cache?"
    ↓
Phase 1: Quick Search (gpt-3.5-turbo, $0.0005)
    ├── Generate search queries
    ├── Web search (free)
    └── Extract key URLs
    ↓
Phase 2: Deep Analysis (gpt-4o-mini, $0.00015)
    ├── Scrape URLs (free)
    ├── Extract code snippets
    └── Summarize findings
    ↓
Phase 3: Synthesis (gpt-4o, $0.005) - only if needed
    ├── Combine all findings
    ├── Generate implementation plan
    └── Create code examples
    ↓
Total Cost: $0.006 (vs $0.05 with all GPT-4o)
```

### Implementation

```typescript
interface ResearchConfig {
  quick_model: string    // "gpt-3.5-turbo"
  deep_model: string     // "gpt-4o-mini"
  synthesis_model: string  // "gpt-4o"
}

async function executeResearch(query: string, config: ResearchConfig): Promise<ResearchResult> {
  // Phase 1: Quick search (cheap model)
  const searchQueries = await generateSearchQueries(query, config.quick_model)

  // Phase 2: Deep analysis (moderate model)
  const findings = await analyzeResults(searchQueries, config.deep_model)

  // Phase 3: Synthesis (expensive model, only if confidence < 0.8)
  if (findings.confidence < 0.8) {
    return await synthesize(findings, config.synthesis_model)
  }

  return findings
}
```

---

## Pattern 8: Markdown Skills (Tier-Based Loading)

**Problem**: Skills are large markdown files, loading all skills wastes context.

**Solution**: Tier-based skill loading (core, frequently-used, on-demand).

### Skill Tiers

**Tier 1: Core** (always loaded):
- `CORE.md` - Project overview
- `agent-observability.md` - Logging, tracing
- `create-skill.md` - Skill creation guide

**Tier 2: Frequent** (loaded if relevant keywords):
- `prompting.md` - Prompt engineering
- `research.md` - Research workflows
- `fabric.md` - Fabric CLI integration

**Tier 3: On-Demand** (loaded explicitly):
- `alex-hormozi-pitch.md` - Sales pitches
- `ffuf.md` - Web fuzzing (pentesting)

### Implementation

```typescript
interface Skill {
  name: string
  tier: 1 | 2 | 3
  keywords: string[]
  content: string
}

async function loadSkills(query: string): Promise<Skill[]> {
  const skills: Skill[] = []

  // Always load Tier 1
  skills.push(...await loadTier1Skills())

  // Load Tier 2 if keywords match
  const tier2 = await loadTier2Skills()
  for (const skill of tier2) {
    if (skill.keywords.some(kw => query.toLowerCase().includes(kw))) {
      skills.push(skill)
    }
  }

  // Tier 3 loaded only if explicitly requested
  // (e.g., "use alex-hormozi-pitch skill")

  return skills
}
```

---

## Summary

| Pattern | Problem | Solution | Benefit |
|---------|---------|----------|---------|
| Hook/Event System | Hard-coded event logic | TypeScript hooks | Decoupled automation |
| Context Sync | Lost context on restart | Checkpoint-based restoration | Fault tolerance |
| Windows Integration | No OS-level features | PowerShell + Credential Manager | Native feel |
| Config Versioning | Config changes risky | Snapshot + rollback | Safe experimentation |
| Multi-App Coordination | Isolated AI apps | Shared session registry | Cross-app workflows |
| Voice Notifications | No ambient updates | ElevenLabs TTS | Hands-free status |
| Research Workflow | Expensive research | Multi-model cost optimization | 90% cost reduction |
| Markdown Skills | Wasted context on skills | Tier-based loading | Efficient context |

**Production Status**: Proven in Friday (voice AI), Jarvis (workflow manager), RIVET (industrial AI) - 3 production apps.

---

**See Also**:
- `docs/architecture/AGENT_FACTORY_PATTERNS.md` - Agent orchestration patterns
- `docs/architecture/BACKLOG_MCP_PATTERNS.md` - Task management patterns
- `docs/patterns/CROSS_REPO_INTEGRATION.md` - Cross-system integration
