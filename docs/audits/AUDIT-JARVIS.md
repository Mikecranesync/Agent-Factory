# Jarvis Unified Production Patterns Audit

**Date:** December 21, 2025
**Auditor:** Claude (Plan Mode - Knowledge Extraction Phase)
**Source:** `C:\Users\hharp\PAI\jarvis-unified\`
**Version:** v0.1.3.0
**Git Status:** Main branch, 5 recent commits, active development
**Test Suite:** 543 tests, 70% coverage

---

## Executive Summary

**Jarvis Unified is the production deployment of PAI** - a multi-app personal AI operating system combining PAI's orchestration layer with specialized applications for Gmail, Calendar, Tasks, and Voice. It demonstrates **PAI at scale** with production-grade error handling, comprehensive testing infrastructure (543 tests), OAuth integration, and real-world patterns that Agent Factory should adopt.

### Key Finding

**Jarvis Unified proves PAI works in production.** It has patterns that Agent Factory lacks (error handling, testing, OAuth) and validates that PAI's Skills-as-Containers architecture scales. **Recommendation:** Extract Jarvis production patterns into Agent Factory, then merge Agent Factory into PAI using Jarvis as the proven reference implementation.

---

## Architecture Overview

### Multi-App Ecosystem

```
Jarvis Unified
├── .claude/ (PAI Orchestration Layer)
│   ├── skills/jarvis-gmail/ (Gmail as PAI skill)
│   ├── agents/ (Parallel execution workers)
│   └── hooks/ (Event automation)
└── apps/
    ├── jarvis-gmail/ (Tauri desktop email app)
    ├── jarvis-hub/ (Central dashboard)
    ├── jarvis-mobile-expo/ (Mobile app)
    ├── jarvis-voice/ (Voice interface)
    └── JarvisVoiceProto/ (Voice prototype)
```

### Application Details

**1. jarvis-gmail (Primary Production App)**
- **Tech Stack:** Tauri (desktop), React, TypeScript, SQLite, Claude API, Gmail API
- **Purpose:** AI-powered email management with categorization, draft generation, VIP routing
- **Status:** Production-ready, 543 tests, 70% coverage
- **Features:**
  - Email categorization (Tier 1/2/3)
  - AI draft generation (Claude-powered)
  - Style learning (learns your writing style)
  - VIP contact management
  - OAuth integration with Gmail

**2. jarvis-hub (Dashboard)**
- **Tech Stack:** Next.js, React, TypeScript
- **Purpose:** Central dashboard showing all Jarvis apps
- **Status:** Active development
- **Features:** App cards, launch controls, status monitoring

**3. jarvis-mobile-expo (Mobile)**
- **Tech Stack:** React Native, Expo SDK
- **Purpose:** Mobile voice assistant
- **Status:** Active development (5 recent commits)
- **Features:** Material 3 design, safe area insets, foundation complete

**4. jarvis-voice (Voice Server)**
- **Tech Stack:** Bun, TypeScript
- **Purpose:** Voice interface backend
- **Status:** Active

**5. JarvisVoiceProto (Prototype)**
- **Status:** Experimental

---

## Production Pattern #1: Error Handling System

**Location:** `apps/jarvis-gmail/tauri-app/ERROR_HANDLING.md` (comprehensive guide)

**Status:** Production-Ready (Version 1.0, November 16, 2025)

### Error Class Hierarchy

**Base Class:**
```typescript
class JarvisError extends Error {
  constructor(
    message: string,
    code: string,
    statusCode: number = 500,
    details?: unknown
  );
  toJSON(): ErrorJSON;
}
```

**Specialized Error Types (15+ classes):**

1. **Authentication Errors (401)**
   - `AuthenticationError` - Invalid credentials
   - `OAuthError` - OAuth flow failed
   - `TokenExpiredError` - Token refresh needed

2. **Validation Errors (400)**
   - `ValidationError` - Input validation failed
   - Uses Zod schemas for runtime type checking

3. **Rate Limiting (429)**
   - `RateLimitError` - General rate limit
   - `GmailRateLimitError` - Gmail-specific

4. **Network Errors (503)**
   - `NetworkError` - Connection failed

5. **Database Errors (500)**
   - `DatabaseError` - General DB error
   - `SQLiteError` - SQLite-specific

6. **AI Service Errors (503)**
   - `AIServiceError` - Base AI error
   - `ClaudeAPIError` - Claude API unavailable
   - `GeminiAPIError` - Gemini rate limit

7. **Gmail API Errors (503)**
   - `GmailAPIError` - Failed to fetch emails

8. **Not Found Errors (404)**
   - `EmailNotFoundError` - Email not found
   - `DraftNotFoundError` - Draft not found
   - `LabelNotFoundError` - Label not found

9. **Email Processing Errors (500)**
   - `CategorizationError` - Failed to categorize
   - `DraftGenerationError` - AI service unavailable

10. **Security Errors (403)**
    - `SecurityError` - Security violation
    - `InjectionAttemptError` - SQL/XSS attempt detected

### Error Handler Features

**Consistent Structure:**
- ✅ HTTP status codes (401, 403, 404, 429, 500, 503)
- ✅ Error codes for programmatic handling
- ✅ User-friendly messages for UI display
- ✅ Detailed context for debugging
- ✅ Automatic retry logic for transient failures

**Security Features:**
- ✅ XSS prevention through content sanitization
- ✅ SQL injection detection
- ✅ Input validation with Zod
- ✅ Error messages don't leak sensitive data

**Example Usage:**
```typescript
import { handleError, ClaudeAPIError } from './errors';

try {
  const draft = await generateDraft(email);
} catch (error) {
  const handled = handleError(error, 'draft-generation');
  // Returns: { message, code, statusCode, details, timestamp, retryable }

  if (handled.retryable) {
    // Show retry button to user
  }
}
```

### Integration with Agent Factory

**Agent Factory Gaps:**
- ❌ No standardized error classes
- ❌ No user-friendly error messages
- ❌ No retry logic for transient failures
- ❌ Basic logging only (no structured error handling)

**Recommendation:**
→ **Extract Jarvis error handling system** to Agent Factory
→ Create `agent_factory/core/errors.py` with equivalent Python error classes
→ Add to Settings Service for configuration
→ Use in all Agent Factory modules (LLM router, database, orchestrator)

---

## Production Pattern #2: Testing Infrastructure

**Location:** `apps/jarvis-gmail/tauri-app/src/tests/` (15+ test files)

**Status:** 543 tests, 70% coverage, CI/CD integrated

### Test Suite Breakdown

**Unit Tests (26 tests):**
```typescript
// draft-generator.test.ts
describe('DraftGenerator', () => {
  test('initialization and style profile loading', ...);
  test('draft generation with various email types', ...);
  test('confidence scoring algorithms', ...);
  test('database operations', ...);
  test('error handling', ...);
  test('draft variations and improvement', ...);
});
```

**Integration Tests (26 tests):**
```typescript
// draft-api.test.ts
describe('Draft API', () => {
  test('POST /api/emails/:id/generate-draft', ...);
  test('GET /api/drafts (with filters)', ...);
  test('GET /api/drafts/:id', ...);
  test('PUT /api/drafts/:id (updates)', ...);
  test('POST /api/drafts/:id/approve', ...);
  test('DELETE /api/drafts/:id (soft delete)', ...);
  test('database integrity checks', ...);
  test('edge cases', ...);
});
```

**E2E Tests (5 tests):**
```typescript
// e2e-draft-flow.test.ts
describe('End-to-End Draft Workflow', () => {
  test('complete draft generation workflow (8 steps)', ...);
  test('draft rejection workflow', ...);
  test('draft editing workflow', ...);
  test('timestamp tracking', ...);
  test('referential integrity', ...);
});
```

**Performance Tests (10 tests):**
```typescript
// draft-performance.test.ts
describe('Performance Benchmarks', () => {
  test('draft generation < 10s', ...);
  test('style profile load < 100ms', ...);
  test('database write < 50ms', ...);
  test('database read < 10ms', ...);
  test('API response < 500ms', ...);
  test('memory usage < 100MB increase', ...);
  test('10 concurrent drafts < 30s', ...);
});
```

### Test Helpers & Infrastructure

**Database Helpers (`helpers/test-db.ts`):**
```typescript
setupTestDatabase()      // Create temporary test database
seedTestData()           // Insert mock emails
seedStyleExamples()      // Insert style learning examples
resetDatabase()          // Clean state between tests
cleanupTestDatabase()    // Delete test database
createMockEmail()        // Generate mock objects
```

**Mock Data:**
- `fixtures/mock-sent-emails.json` - 15 example sent emails
- Realistic test data (professional, casual, various tones)
- Different recipient types, lengths

**Coverage Targets:**
| Component | Target | Status |
|-----------|--------|--------|
| DraftGenerator | 80% | ✅ |
| StyleLearner | 70% | ✅ |
| Draft API | 90% | ✅ |
| **Overall** | **60%** | **✅ (70% achieved)** |

### Performance Benchmarks

**Target Metrics:**
- Draft Generation: < 10 seconds ✅
- Style Profile Load: < 100ms ✅
- Database Write: < 50ms ✅
- Database Read: < 10ms ✅
- API Response: < 500ms ✅
- Memory Usage: < 100MB increase ✅

**Load Testing:**
- 10 concurrent drafts: < 30 seconds total ✅
- Sequential drafts: < 10s average latency ✅

### CI/CD Integration

**GitHub Actions:**
```yaml
- name: Run Tests
  run: bun run test:run

- name: Generate Coverage
  run: bun run test:coverage

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage/lcov.info
```

**Test Commands:**
```bash
bun test              # Run all tests
bun run test:run      # Run tests once
bun run test:coverage # Generate coverage report
bun run test:ui       # Open test UI
```

### Integration with Agent Factory

**Agent Factory Gaps:**
- ❌ No comprehensive test suite (minimal tests)
- ❌ No E2E tests
- ❌ No performance benchmarks
- ❌ No CI/CD integration
- ❌ No test helpers or fixtures

**Agent Factory Has:**
- ✅ Some unit tests (incomplete coverage)
- ✅ Test infrastructure exists (pytest)

**Recommendation:**
→ **Extract Jarvis testing patterns** to Agent Factory
→ Create `tests/` directory with unit/integration/e2e/performance subdirectories
→ Add test helpers (`tests/helpers/`)
→ Set coverage target: 60% minimum, 70% goal
→ Add GitHub Actions CI/CD (`.github/workflows/test.yml`)
→ Performance benchmarks for LLM router, database, orchestrator

---

## Production Pattern #3: OAuth Integration

**Location:** `apps/jarvis-gmail/tauri-app/src/api/` (3 auth implementations)

**Status:** Production-ready, multiple strategies

### OAuth Implementation Files

**1. gmail-auth.ts (Primary)**
- Full OAuth 2.0 flow with Google API
- Token storage and refresh
- Scope management (gmail.readonly, gmail.send)

**2. setup-auth.ts (Setup)**
- Interactive OAuth setup wizard
- Credential configuration
- First-time authorization

**3. simple-auth.ts (Simplified)**
- Streamlined auth flow
- Reduced complexity for testing

### OAuth Flow

```
1. User clicks "Connect Gmail"
    ↓
2. setup-auth.ts initiates OAuth flow
    ↓
3. Browser opens Google consent screen
    ↓
4. User grants permissions
    ↓
5. Google redirects with authorization code
    ↓
6. gmail-auth.ts exchanges code for tokens
    ↓
7. Tokens stored securely (encrypted)
    ↓
8. Automatic token refresh on expiry
```

### OAuth Features

**Security:**
- ✅ Tokens encrypted at rest
- ✅ Secure storage (OS keychain integration)
- ✅ Automatic token refresh
- ✅ Scope limitation (least privilege)

**Error Handling:**
- ✅ `OAuthError` for flow failures
- ✅ `TokenExpiredError` for refresh needed
- ✅ Graceful degradation (retry logic)

**Testing:**
- ✅ `gmail-auth.test.ts` - OAuth flow tests
- ✅ Mock OAuth responses
- ✅ Token refresh testing

### Integration with Agent Factory

**Agent Factory Has:**
- ✅ Basic auth patterns (Clerk in Nexus, RevenueCat in Friday)
- ❌ No Gmail OAuth
- ❌ No Google Calendar OAuth
- ❌ No standardized OAuth library

**Agent Factory Needs:**
- Gmail integration for RIVET Pro (email notifications)
- Google Calendar for scheduling (PLC Tutor course enrollment)

**Recommendation:**
→ **Extract Jarvis OAuth patterns** to Agent Factory
→ Create `agent_factory/integrations/google/` module
→ Reusable OAuth client for Gmail, Calendar, Drive
→ Use Settings Service for OAuth config (client_id, client_secret)

---

## Production Pattern #4: Multi-App Coordination

**Architecture:** Hub-and-Spoke pattern

### Hub (jarvis-hub)

**Purpose:** Central dashboard for all Jarvis apps

**Features:**
- App cards (Gmail, Calendar, Tasks)
- Launch controls
- Status monitoring (running/stopped)
- Inter-app communication

**Tech Stack:**
- Next.js (React framework)
- Server-side rendering
- API routes for app coordination

### Spoke Apps (jarvis-gmail, jarvis-mobile, etc.)

**Communication Pattern:**
```
Hub (localhost:3000)
  ├── REST API → Gmail App (localhost:1420)
  ├── WebSocket → Mobile App (expo)
  └── IPC → Voice Server (bun)
```

**Shared State:**
- Settings synchronized via PAI hooks
- User preferences stored in SQLite
- Real-time updates via WebSocket/IPC

### Integration with Agent Factory

**Agent Factory Has:**
- ✅ Telegram bot (separate interface)
- ✅ SCAFFOLD (autonomous execution)
- ❌ No multi-app coordination
- ❌ No central dashboard

**Recommendation:**
→ **Extract hub-and-spoke pattern** for Agent Factory
→ Create dashboard for RIVET Pro agents
→ Monitor: RedditMonitor, KnowledgeAnswerer, YouTubePublisher
→ Control: Start/stop agents, view metrics, adjust settings

---

## Production Pattern #5: Database Design

**Database:** SQLite (local-first)

**Schema (jarvis-gmail):**
```sql
CREATE TABLE emails (
  id TEXT PRIMARY KEY,
  thread_id TEXT,
  subject TEXT,
  sender TEXT,
  snippet TEXT,
  tier INTEGER,  -- 1 (Urgent), 2 (Important), 3 (Low Priority)
  labels TEXT,
  timestamp INTEGER,
  body TEXT,
  has_draft BOOLEAN
);

CREATE TABLE drafts (
  id TEXT PRIMARY KEY,
  email_id TEXT REFERENCES emails(id),
  content TEXT,
  confidence REAL,  -- 0.0-1.0
  status TEXT,      -- 'pending', 'approved', 'rejected', 'sent'
  created_at INTEGER,
  updated_at INTEGER,
  approved_at INTEGER,
  sent_at INTEGER
);

CREATE TABLE style_examples (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  subject TEXT,
  content TEXT,
  tone TEXT,
  length TEXT,
  recipient_type TEXT
);

CREATE TABLE settings (
  key TEXT PRIMARY KEY,
  value TEXT,
  category TEXT
);
```

**Indexes:**
```sql
CREATE INDEX idx_emails_tier ON emails(tier);
CREATE INDEX idx_emails_timestamp ON emails(timestamp);
CREATE INDEX idx_drafts_email_id ON drafts(email_id);
CREATE INDEX idx_drafts_status ON drafts(status);
```

**Features:**
- ✅ Foreign key constraints (referential integrity)
- ✅ Indexes for performance
- ✅ Soft deletes (status field instead of DELETE)
- ✅ Timestamp tracking (created_at, updated_at)

### Integration with Agent Factory

**Agent Factory Database:**
- ✅ PostgreSQL (multi-provider: Supabase/Railway/Neon)
- ✅ RLS (Row-Level Security)
- ✅ pgvector (vector embeddings)
- ❌ No indexes documented
- ❌ No soft deletes

**Recommendation:**
→ **Extract Jarvis database patterns:**
→ Add indexes to Agent Factory schema (knowledge_atoms, agents, sessions)
→ Implement soft deletes for audit trail
→ Add timestamp tracking (created_at, updated_at, deleted_at)

---

## Production Pattern #6: Style Learning

**Feature:** AI learns your writing style from sent emails

**Location:** `apps/jarvis-gmail/tauri-app/src/api/style-learner.ts`

**Algorithm:**
```
1. Analyze 15+ sent emails
    ↓
2. Extract patterns:
   - Tone (formal, casual, friendly)
   - Length (brief, moderate, detailed)
   - Recipient type (VIP, colleague, external)
   - Common phrases
   - Signature style
    ↓
3. Build style profile
    ↓
4. Store in settings table
    ↓
5. Use profile for draft generation
```

**Profile Schema:**
```json
{
  "tone": "professional_friendly",
  "average_length": 150,
  "common_phrases": [
    "Thanks for reaching out",
    "Let me know if you have questions",
    "Looking forward to hearing from you"
  ],
  "signature": "Best,\nYour Name",
  "greeting_style": "Hi {name},"
}
```

**Draft Generation:**
```typescript
async generateDraft(email: Email): Promise<Draft> {
  const profile = await loadStyleProfile();
  const prompt = `
    Generate email reply in this style:
    - Tone: ${profile.tone}
    - Length: ${profile.average_length} words
    - Use phrases like: ${profile.common_phrases.join(', ')}

    Original email: ${email.body}
  `;

  const response = await claude.complete(prompt);
  return { content: response, confidence: calculateConfidence(response) };
}
```

### Integration with Agent Factory

**Agent Factory Has:**
- ✅ Knowledge Atom Standard (learning structure)
- ❌ No style learning
- ❌ No personalization

**Recommendation:**
→ **Extract style learning** for Agent Factory
→ RIVET Pro: Learn technician communication style
→ PLC Tutor: Adapt teaching style to student level
→ Use Knowledge Atoms to store style profiles

---

## Production Pattern #7: Confidence Scoring

**Feature:** AI self-assesses draft quality (0.0-1.0)

**Algorithm:**
```typescript
function calculateConfidence(draft: string, email: Email): number {
  let score = 1.0;

  // Deduct for unclear context
  if (!hasContextClues(email)) score -= 0.2;

  // Deduct for length mismatch
  if (draft.length < 50 || draft.length > 500) score -= 0.1;

  // Deduct for generic phrases
  if (hasGenericPhrases(draft)) score -= 0.15;

  // Bonus for specific references
  if (hasSpecificReferences(draft, email)) score += 0.1;

  return Math.max(0, Math.min(1, score));
}
```

**Thresholds:**
- **High (0.9-1.0):** Auto-approve candidate
- **Medium (0.7-0.89):** Show to user for review
- **Low (0.0-0.69):** Flag for manual drafting

**UI Integration:**
```typescript
<DraftCard confidence={draft.confidence}>
  {draft.confidence >= 0.9 && <Badge>High Confidence</Badge>}
  {draft.confidence < 0.7 && <Badge color="red">Review Needed</Badge>}
</DraftCard>
```

### Integration with Agent Factory

**Agent Factory Has:**
- ❌ No confidence scoring
- ❌ No quality thresholds

**Recommendation:**
→ **Extract confidence scoring** for Agent Factory
→ RIVET Pro: Confidence in troubleshooting answers (route to human if <0.9)
→ SCAFFOLD: Confidence in autonomous PR (pause if <0.8)
→ LLM Router: Confidence calibration per model

---

## Comparison with Agent Factory

### Where Jarvis Excels (Agent Factory Should Adopt)

| Pattern | Jarvis Implementation | Agent Factory Gap | Recommendation |
|---------|----------------------|-------------------|----------------|
| **Error Handling** | 15+ error classes, structured | ❌ Basic logging only | → Extract to `agent_factory/core/errors.py` |
| **Testing** | 543 tests, 70% coverage | ❌ Minimal tests | → Create `tests/` with unit/integration/e2e |
| **OAuth Integration** | Gmail OAuth, token refresh | ❌ No Gmail/Calendar OAuth | → Extract to `agent_factory/integrations/google/` |
| **Multi-App Coordination** | Hub-and-spoke pattern | ❌ No coordination | → Dashboard for agent monitoring |
| **Database Design** | Indexes, soft deletes, timestamps | ❌ No indexes documented | → Add indexes, soft deletes |
| **Style Learning** | Learns writing style | ❌ No personalization | → Adapt for RIVET/PLC Tutor |
| **Confidence Scoring** | 0.0-1.0 quality assessment | ❌ No confidence scoring | → Add to all agents |
| **Performance Benchmarks** | <10s draft, <100ms load | ❌ No benchmarks | → LLM router, database, orchestrator |
| **CI/CD** | GitHub Actions, 543 tests | ❌ No CI/CD | → Add `.github/workflows/test.yml` |
| **User-Friendly Errors** | Retryable, actionable | ❌ Technical errors only | → Error messages for UI |

### Where Agent Factory Excels (Jarvis Should Adopt)

| Pattern | Agent Factory Implementation | Jarvis Gap | Recommendation |
|---------|----------------------------|-----------|----------------|
| **LLM Routing** | 73% cost reduction | ❌ Single model (Claude) | ← Adopt LLM router for cost optimization |
| **Vector Search** | pgvector, <100ms latency | ❌ No semantic search | ← Add pgvector to SQLite |
| **Knowledge Atoms** | 1,965 atoms, 100% citations | ❌ No structured KB | ← Adopt for email knowledge |
| **Multi-Provider DB** | Supabase/Railway/Neon failover | ❌ SQLite only | ← Add cloud DB option |
| **RLS Isolation** | Multi-tenant security | ❌ Single-user | ← For shared Jarvis instances |
| **Autonomous Execution** | SCAFFOLD PR creation | ❌ Manual workflows | ← Autonomous email processing |
| **Monitoring** | Cost tracking, safety rails | ❌ Basic logging | ← Track API costs, set budgets |

---

## Integration Recommendations

### Extract Jarvis Patterns to Agent Factory

**Priority 1 (High Value, Low Effort):**
1. **Error Handling System** (4 hours)
   - Create `agent_factory/core/errors.py`
   - 15+ error classes (Authentication, Validation, RateLimit, etc.)
   - Structured error handling with retry logic

2. **Testing Infrastructure** (8 hours)
   - Create `tests/` directory (unit/integration/e2e/performance)
   - Test helpers, fixtures, mock data
   - Set coverage target: 60% minimum

3. **Confidence Scoring** (2 hours)
   - Add to LLM Router (per-response confidence)
   - Add to RIVET Pro (answer quality)
   - Thresholds: <0.7 flag, 0.7-0.89 review, 0.9+ auto-approve

**Priority 2 (High Value, Moderate Effort):**
4. **OAuth Integration** (6 hours)
   - Create `agent_factory/integrations/google/`
   - Gmail OAuth, Calendar OAuth
   - Token storage, refresh logic

5. **Database Indexes** (3 hours)
   - Add indexes to knowledge_atoms, agents, sessions
   - Soft deletes (status field)
   - Timestamp tracking (created_at, updated_at)

6. **Performance Benchmarks** (4 hours)
   - LLM router: <10ms routing overhead
   - Database: <100ms queries
   - Orchestrator: <500ms routing

**Priority 3 (Nice to Have):**
7. **Multi-App Dashboard** (12 hours)
   - Hub-and-spoke pattern
   - Monitor RIVET agents
   - Real-time metrics

8. **Style Learning** (8 hours)
   - Adapt for RIVET Pro (technician communication)
   - Adapt for PLC Tutor (teaching style)

### Enhance Jarvis with Agent Factory Patterns

**Priority 1:**
1. **LLM Router** (6 hours)
   - Replace direct Claude API calls with router
   - 73% cost reduction potential
   - Fallback chains (Claude → Gemini → GPT)

2. **Vector Search** (8 hours)
   - Add pgvector to SQLite (requires extension)
   - Semantic email search
   - Related email suggestions

**Priority 2:**
3. **Knowledge Atoms** (4 hours)
   - Store email knowledge (common responses, patterns)
   - Improve draft quality
   - Reduce hallucinations

---

## Gaps & Incomplete Work

### HIGH PRIORITY (Jarvis Specific)

1. **Calendar App Not Built**
   - Status: Planned, not implemented
   - Impact: Can't schedule meetings
   - Fix Effort: 20-30 hours

2. **Tasks App Not Built**
   - Status: Planned, not implemented
   - Impact: Can't manage todos
   - Fix Effort: 15-20 hours

3. **Mobile App Incomplete**
   - Status: Foundation complete (Day 1), features pending
   - Impact: Limited mobile functionality
   - Fix Effort: 10-15 hours

### MEDIUM PRIORITY

4. **No Vector Search**
   - Status: SQLite only (no pgvector)
   - Impact: Can't do semantic email search
   - Fix Effort: 8 hours

5. **No LLM Routing**
   - Status: Uses Claude only
   - Impact: High costs, no fallback
   - Fix Effort: 6 hours

6. **No Cost Tracking**
   - Status: No monitoring of API spend
   - Impact: Can't budget AI costs
   - Fix Effort: 4 hours

### LOW PRIORITY

7. **No Multi-Tenant Support**
   - Status: Single-user only
   - Impact: Can't share with family/team
   - Fix Effort: 12 hours (add RLS)

---

## Appendix: File Inventory

### Jarvis Unified Structure
```
C:/Users/hharp/PAI/jarvis-unified/
├── .claude/ (PAI orchestration)
│   ├── skills/jarvis-gmail/
│   ├── agents/
│   └── hooks/
├── apps/
│   ├── jarvis-gmail/
│   │   └── tauri-app/
│   │       ├── src/
│   │       │   ├── api/
│   │       │   │   ├── gmail-auth.ts (OAuth)
│   │       │   │   ├── setup-auth.ts (OAuth setup)
│   │       │   │   └── simple-auth.ts (Simple OAuth)
│   │       │   ├── tests/ (543 tests)
│   │       │   │   ├── action-executor.test.ts
│   │       │   │   ├── categorizer.test.ts
│   │       │   │   ├── database.test.ts
│   │       │   │   ├── draft-api.test.ts
│   │       │   │   ├── draft-generator.test.ts
│   │       │   │   ├── draft-performance.test.ts
│   │       │   │   ├── e2e-draft-flow.test.ts
│   │       │   │   ├── email-processing.test.ts
│   │       │   │   ├── gmail-auth.test.ts
│   │       │   │   └── rag/gemini-client.test.ts
│   │       │   └── errors/ (error handling)
│   │       ├── ERROR_HANDLING.md (guide)
│   │       └── GMAIL-SETUP-GUIDE.md
│   ├── jarvis-hub/ (Next.js dashboard)
│   ├── jarvis-mobile-expo/ (React Native)
│   ├── jarvis-voice/ (Bun/TypeScript)
│   └── JarvisVoiceProto/ (Prototype)
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DEMO-SCRIPT.md
│   └── CI_CD_SETUP.md
└── .github/
    └── workflows/test.yml (CI/CD)
```

### Total: ~9,186 files (32 commits in 6 months)

---

## References

1. **Jarvis Unified Repo:** `C:\Users\hharp\PAI\jarvis-unified\`
2. **Error Handling Guide:** `apps/jarvis-gmail/tauri-app/ERROR_HANDLING.md`
3. **Testing README:** `apps/jarvis-gmail/tauri-app/src/tests/README.md`
4. **CI/CD Setup:** `.github/CI_CD_SETUP.md`
5. **GitHub Actions:** https://github.com/Mikecranesync/jarvis-unified/actions/workflows/test.yml
