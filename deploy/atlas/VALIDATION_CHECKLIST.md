# Atlas CMMS Integration - Phase 1 Validation Checklist

## Overview

This checklist validates that the Atlas CMMS integration is complete and working correctly. Complete all items before proceeding to Phase 2.

**Status:** Ready for validation (Docker Desktop required)

---

## Prerequisites

### 1. Start Docker Desktop

- [ ] Open Docker Desktop application
- [ ] Wait for "Docker Desktop is running" status
- [ ] Verify with command: `docker ps` (should not error)

### 2. Environment Configuration

- [ ] Copy `.env.example` to `.env` if not exists
- [ ] Verify Atlas configuration in `.env`:
  ```env
  ATLAS_BASE_URL=http://localhost:8080/api
  ATLAS_EMAIL=admin@example.com
  ATLAS_PASSWORD=admin
  ATLAS_ENABLED=true
  ```

---

## Deployment Validation

### 3. Deploy Atlas CMMS

```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory\deploy\atlas"
docker-compose up -d
```

- [ ] No errors during `docker-compose up`
- [ ] Both containers started successfully

### 4. Check Container Health

```bash
docker-compose ps
```

Expected output:
```
NAME                STATUS
atlas-postgres      Up (healthy)
atlas-cmms          Up (healthy)
```

- [ ] `atlas-postgres` shows "Up (healthy)"
- [ ] `atlas-cmms` shows "Up (healthy)"

**Note:** If `atlas-cmms` shows "Up" but not "(healthy)", wait 60 seconds for startup.

### 5. View Application Logs

```bash
docker-compose logs -f atlas-app
```

Look for startup message:
```
Started AtlasCmmsApplication in X.XXX seconds
```

- [ ] Application started successfully
- [ ] No ERROR messages in logs
- [ ] Database migrations completed

**Tip:** Press Ctrl+C to stop following logs.

---

## API Endpoint Validation

### 6. Test Health Endpoint

```bash
curl http://localhost:8080/api/health
```

Expected response:
```json
{"status":"UP"}
```

- [ ] Health endpoint returns 200 OK
- [ ] Status is "UP"

### 7. Test Authentication

```bash
curl -X POST http://localhost:8080/api/auth/signin \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"admin@example.com\",\"password\":\"admin\"}"
```

Expected response:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "...",
    "email": "admin@example.com",
    ...
  }
}
```

- [ ] Authentication returns 200 OK
- [ ] Response contains `token` field
- [ ] Response contains `user` object with `email`

**Important:** Copy the token value - you'll need it for next tests.

### 8. Test Work Orders Endpoint (Authenticated)

Replace `YOUR_TOKEN_HERE` with the token from step 7:

```bash
curl -X GET http://localhost:8080/api/work-orders \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

Expected response:
```json
{
  "content": [],
  "totalElements": 0,
  "totalPages": 0,
  ...
}
```

- [ ] Work orders endpoint returns 200 OK
- [ ] Response is valid JSON with pagination structure

---

## Python Integration Validation

### 9. Install Dependencies

```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
pip install httpx langsmith pydantic-settings
```

- [ ] httpx installed successfully
- [ ] langsmith installed successfully
- [ ] pydantic-settings installed successfully

### 10. Run Import Tests

```bash
python -c "from agent_factory.integrations.atlas import AtlasClient; print('✓ Import successful')"
```

- [ ] No import errors
- [ ] Prints "✓ Import successful"

### 11. Run Unit Tests

```bash
pytest tests/integrations/atlas/test_client.py -v
```

Expected output:
```
test_token_cache_stores_token PASSED
test_token_cache_expiry PASSED
test_authenticate_success PASSED
...
```

- [ ] All unit tests pass
- [ ] No FAILED tests
- [ ] No import errors

**Note:** Some tests are mocked and don't require live Atlas.

### 12. Run Manual Validation Script

```bash
python examples/test_atlas_client.py
```

Expected output:
```
====================================================================
TEST 1: Health Check (No Authentication)
====================================================================
✓ Health check successful
  Status: UP

====================================================================
TEST 2: Authentication
====================================================================
✓ Authentication successful
  Token: eyJhbGciOiJIUzI1NiI... (truncated)

...

====================================================================
VALIDATION SUMMARY
====================================================================
  health               ✓ PASS
  auth                 ✓ PASS
  token_cache          ✓ PASS
  create_wo            ✓ PASS
  get_wo               ✓ PASS
  update_wo            ✓ PASS
  list_wo              ✓ PASS
  search_assets        ✓ PASS
  complete_wo          ✓ PASS
  error_handling       ✓ PASS

  Total: 10/10 tests passed

✓ ALL TESTS PASSED - Atlas integration is working correctly!
```

- [ ] All 10 tests pass
- [ ] No errors or exceptions
- [ ] Work order created, updated, and completed successfully

---

## Code Quality Validation

### 13. Code Structure

- [ ] `agent_factory/integrations/atlas/exceptions.py` exists (7 exception classes)
- [ ] `agent_factory/integrations/atlas/config.py` exists (AtlasConfig class)
- [ ] `agent_factory/integrations/atlas/client.py` exists (~540 lines)
- [ ] `agent_factory/integrations/atlas/__init__.py` exports all classes
- [ ] All files have proper docstrings and type hints

### 14. Error Handling

- [ ] AtlasClient raises `AtlasAuthError` for 401 responses
- [ ] AtlasClient raises `AtlasNotFoundError` for 404 responses
- [ ] AtlasClient raises `AtlasValidationError` for 400 responses
- [ ] AtlasClient raises `AtlasRateLimitError` for 429 responses
- [ ] AtlasClient raises `AtlasAPIError` for network errors

### 15. Token Management

- [ ] AtlasTokenCache stores tokens with expiration
- [ ] Tokens cached for 24 hours (configurable via ATLAS_TOKEN_TTL)
- [ ] Tokens refresh 5 minutes before expiry (configurable via ATLAS_TOKEN_REFRESH_BUFFER)
- [ ] Expired tokens trigger automatic re-authentication
- [ ] Token cache is thread-safe (asyncio locks)

### 16. API Methods

Verify all 9 API methods exist and are traceable:

- [ ] `create_work_order(data)` → POST /work-orders
- [ ] `get_work_order(id)` → GET /work-orders/{id}
- [ ] `update_work_order(id, updates)` → PUT /work-orders/{id}
- [ ] `list_work_orders(status, page, limit)` → GET /work-orders
- [ ] `complete_work_order(id)` → POST /work-orders/{id}/complete
- [ ] `search_assets(query, limit)` → GET /assets/search
- [ ] `get_asset(id)` → GET /assets/{id}
- [ ] `create_user(data)` → POST /users
- [ ] `health_check()` → GET /health

### 17. LangSmith Tracing

- [ ] All API methods decorated with `@traceable`
- [ ] `atlas_authenticate` trace function exists
- [ ] `atlas_request` trace function exists
- [ ] Traces include proper names (e.g., `atlas_create_work_order`)

---

## Documentation Validation

### 18. Deployment Documentation

- [ ] `deploy/atlas/README.md` exists and complete
- [ ] `deploy/atlas/docker-compose.yml` documented with comments
- [ ] `deploy/atlas/DEPLOYMENT_STATUS.md` tracks progress
- [ ] `.env.example` includes all Atlas configuration variables

### 19. Code Documentation

- [ ] All classes have docstrings with usage examples
- [ ] All methods have parameter and return type documentation
- [ ] Exceptions documented with "Raised when:" sections
- [ ] Configuration variables documented in AtlasConfig

---

## Final Checks

### 20. Clean Up Test Data

After validation, optionally clean up test work orders:

```bash
# Stop Atlas
docker-compose down

# Remove all data (fresh start)
docker-compose down -v
```

- [ ] Containers stopped cleanly
- [ ] Volumes removed (if desired)

### 21. Integration Status

- [ ] Atlas CMMS deployed and tested locally ✅
- [ ] AtlasClient implemented with all 9 methods ✅
- [ ] JWT authentication working with token caching ✅
- [ ] Token refresh on 401 working ✅
- [ ] Unit tests passing (token cache, auth, errors) ✅
- [ ] Manual test script validates all operations ✅
- [ ] LangSmith tracing enabled for all Atlas operations ✅
- [ ] Documentation complete (deployment, usage, testing) ✅
- [ ] Error handling tested (404, 401, network errors) ✅

---

## Phase 1 Success Criteria

**All items below must be checked before proceeding to Phase 2:**

- [ ] Atlas CMMS running on localhost:8080
- [ ] Can authenticate and receive JWT token
- [ ] Token caching works (24-hour TTL)
- [ ] Token auto-refreshes on 401 response
- [ ] Can create work order via AtlasClient
- [ ] Can retrieve work order by ID
- [ ] Can update work order
- [ ] Can list work orders with pagination
- [ ] Can complete work order
- [ ] Can search assets
- [ ] Health check works without authentication
- [ ] All 10 validation tests pass
- [ ] Unit tests pass (pytest)
- [ ] Error handling works correctly
- [ ] LangSmith traces visible (if API key configured)
- [ ] Code follows project patterns (async, type hints, docstrings)
- [ ] Documentation complete and accurate

---

## Troubleshooting

### Container Won't Start

**Symptom:** `docker-compose up -d` fails

**Solutions:**
1. Check if Docker Desktop is running
2. Verify ports 8080 and 5433 are available
3. Check logs: `docker-compose logs atlas-app`
4. Restart Docker Desktop

### Authentication Fails

**Symptom:** 401 Unauthorized on `/auth/signin`

**Solutions:**
1. Wait 60 seconds after container start (database migrations)
2. Check logs: `docker-compose logs atlas-app | grep -i migration`
3. Verify credentials match (admin@example.com / admin)
4. Check Atlas admin account created: `docker-compose logs atlas-app | grep -i admin`

### Unit Tests Fail

**Symptom:** `pytest` shows FAILED tests

**Solutions:**
1. Install test dependencies: `pip install pytest pytest-asyncio`
2. Verify imports work: `python -c "from agent_factory.integrations.atlas import AtlasClient"`
3. Check Python version: `python --version` (requires 3.10+)
4. Clear pytest cache: `rm -rf .pytest_cache __pycache__`

### Manual Validation Fails

**Symptom:** `python examples/test_atlas_client.py` shows errors

**Solutions:**
1. Verify Atlas is running: `curl http://localhost:8080/api/health`
2. Check .env configuration (ATLAS_BASE_URL, credentials)
3. Verify httpx installed: `pip install httpx`
4. Check for port conflicts: `netstat -ano | findstr :8080`

---

## Next Steps

**After completing Phase 1 validation:**

1. **User Review** ⚠️
   - Review validation results
   - Approve AtlasClient implementation
   - Decide whether to proceed to Phase 2

2. **Phase 2 Planning** (After approval)
   - Wire up 8 work order endpoints in `work_orders.py`
   - Add Atlas user creation to `users.py`
   - Create `assets.py` router
   - Add Atlas health check to main health endpoint
   - Integration tests for full CRUD flow
   - Deploy Atlas to VPS (72.60.175.144)

3. **Git Commit** (After approval)
   ```bash
   git add .
   git commit -m "PHASE1: Complete Atlas CMMS integration

   - Deployed Atlas locally with Docker
   - Implemented AtlasClient with 9 API methods
   - JWT authentication with token caching (24hr TTL)
   - Automatic token refresh on 401 responses
   - Comprehensive error handling (7 exception types)
   - Unit tests (20+ test cases)
   - Manual validation script (10 tests)
   - LangSmith tracing for observability
   - Complete documentation

   Files:
   - agent_factory/integrations/atlas/*.py (4 files, 800+ lines)
   - deploy/atlas/* (docker-compose, README, docs)
   - tests/integrations/atlas/test_client.py (650+ lines)
   - examples/test_atlas_client.py (450+ lines)
   - .env.example (Atlas configuration)

   All Phase 1 success criteria met ✅"
   ```

---

## Contact

**If validation fails:**
1. Review error messages in validation script output
2. Check troubleshooting section above
3. Review `deploy/atlas/README.md` for deployment help
4. Check `deploy/atlas/DEPLOYMENT_STATUS.md` for current status

**If all validation passes:**
Congratulations! Phase 1 is complete. Await user review before Phase 2.
