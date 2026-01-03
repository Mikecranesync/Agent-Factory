# HARVEST BLOCK 24: Atlas Client

**Priority**: LOW
**Size**: 32.88KB (total across 4 files: client.py 18.22KB, config.py 4.19KB, exceptions.py 4.01KB, docs 5.37KB)
**Source**: `agent_factory/integrations/atlas/` (client.py, config.py, exceptions.py, __init__.py)
**Target**: `rivet/integrations/atlas/`

---

## Overview

Async HTTP client for Atlas CMMS API integration - handles JWT authentication, token caching, work order management, asset tracking, and user management with automatic retries and comprehensive error handling for B2B CMMS partnerships (ServiceTitan, MaintainX).

### What This Adds

- **JWT Authentication**: Auto-login with token caching (24-hour TTL, 5-min refresh buffer)
- **Token Management**: Automatic token refresh on 401 responses
- **Work Order API**: Create, update, list, complete work orders
- **Asset API**: Search, create, retrieve assets
- **User API**: Create users programmatically
- **Retry Logic**: Exponential backoff for network errors (max 3 retries)
- **Error Handling**: 6 exception types for granular error handling
- **LangSmith Tracing**: Observability for all API calls
- **Pydantic Config**: Environment-based configuration with validation

### Key Features

```python
from rivet.integrations.atlas.client import AtlasClient

# Initialize client (reads from env vars)
async with AtlasClient() as client:
    # Create work order
    work_order = await client.create_work_order({
        "title": "Fix PowerFlex 525 fault F003",
        "description": "Communication error on VFD",
        "priority": "HIGH",
        "status": "PENDING",
        "assignedTo": ["user-123"],
        "dueDate": "2026-01-10T09:00:00Z"
    })

    print(f"Work order created: {work_order['id']}")

    # Search for asset
    assets = await client.search_assets("PowerFlex 525", limit=5)

    # Complete work order
    completed = await client.complete_work_order(work_order['id'])
    print(f"Status: {completed['status']}")  # COMPLETED
```

---

## JWT Authentication & Token Caching

```python
from rivet.integrations.atlas.client import AtlasClient, AtlasTokenCache

# Token cached automatically
async with AtlasClient() as client:
    # First request: Authenticates and caches token
    wo1 = await client.create_work_order({...})

    # Subsequent requests: Uses cached token (no re-auth)
    wo2 = await client.create_work_order({...})

    # If token expired (after 24 hours): Auto-refreshes on 401

# Manual token management (advanced)
cache = AtlasTokenCache()
token = await cache.get_token()  # Returns None if expired
await cache.set_token("eyJhbGci...", ttl_seconds=86400)
await cache.clear()  # Force re-authentication
```

**Token Lifecycle**:
1. First API call → Authenticate via `/auth/signin`
2. Cache token with TTL (default 24 hours)
3. Subsequent calls use cached token
4. Token expires → Auto-refresh on next 401
5. Refresh buffer (5 min) prevents mid-request expiration

---

## Work Order API

```python
# Create work order
work_order = await client.create_work_order({
    "title": "Repair motor",
    "description": "Motor overheating, check bearings",
    "priority": "CRITICAL",  # LOW, MEDIUM, HIGH, CRITICAL
    "status": "IN_PROGRESS",  # PENDING, IN_PROGRESS, COMPLETED, CANCELLED
    "assignedTo": ["tech-456"],
    "assetId": "asset-789",
    "dueDate": "2026-01-05T14:00:00Z"
})

# Get work order by ID
wo = await client.get_work_order("WO-12345")

# Update work order (partial update)
updated = await client.update_work_order("WO-12345", {
    "status": "COMPLETED",
    "notes": "Replaced bearings, motor running normally"
})

# List work orders (paginated)
result = await client.list_work_orders(
    status="PENDING",
    page=0,
    limit=20
)
# Returns: {"content": [...], "totalPages": 5, "totalElements": 97}

# Complete work order (shortcut for update status)
completed = await client.complete_work_order("WO-12345")
```

---

## Asset API

```python
# Search assets by name/description
assets = await client.search_assets("PowerFlex", limit=10)
for asset in assets:
    print(f"{asset['name']} - {asset['model']}")

# Create asset
new_asset = await client.create_asset({
    "name": "PowerFlex 525 VFD",
    "description": "Variable frequency drive for pump motor",
    "area": "Plant 1 - Pump Room",
    "category": "Electrical",
    "model": "25B-D010N104",
    "manufacturer": "Allen-Bradley",
    "serialNumber": "SN12345678"
})

# Get asset by ID
asset = await client.get_asset("asset-789")
```

---

## User API

```python
# Create user
new_user = await client.create_user({
    "email": "tech@example.com",
    "firstName": "John",
    "lastName": "Smith",
    "password": "SecurePass123!",
    "role": "TECHNICIAN"  # USER, TECHNICIAN, ADMIN
})
```

---

## Error Handling

```python
from rivet.integrations.atlas.exceptions import (
    AtlasAuthError,
    AtlasNotFoundError,
    AtlasValidationError,
    AtlasRateLimitError,
    AtlasAPIError,
    AtlasConfigError
)

try:
    async with AtlasClient() as client:
        work_order = await client.create_work_order({
            "title": "Fix issue"  # Missing required fields
        })

except AtlasAuthError as e:
    # 401 - Invalid credentials or expired token
    print(f"Auth failed: {e.message}")

except AtlasValidationError as e:
    # 400 - Missing/invalid fields
    print(f"Validation errors: {e.field_errors}")

except AtlasNotFoundError as e:
    # 404 - Resource doesn't exist
    print(f"Not found: {e.message}")

except AtlasRateLimitError as e:
    # 429 - Rate limit exceeded
    print(f"Rate limited. Retry after {e.retry_after} seconds")

except AtlasAPIError as e:
    # Generic API error (network, timeout, 5xx)
    print(f"API error: {e.message} (status: {e.status_code})")

except AtlasConfigError as e:
    # Missing/invalid configuration
    print(f"Config error: {e.message}")
```

**Exception Hierarchy**:
```
AtlasError (base)
├── AtlasAuthError (401 - authentication)
├── AtlasAPIError (network, timeouts, 5xx)
├── AtlasNotFoundError (404 - resource not found)
├── AtlasValidationError (400 - validation)
├── AtlasRateLimitError (429 - rate limit)
└── AtlasConfigError (config issues)
```

---

## Configuration

**Pydantic Settings** (Environment variables):

```bash
# API Connection
export ATLAS_BASE_URL=https://atlas.example.com/api
export ATLAS_EMAIL=admin@example.com
export ATLAS_PASSWORD=admin_password

# Request Settings
export ATLAS_TIMEOUT=30.0  # Request timeout (seconds)
export ATLAS_MAX_RETRIES=3  # Max retry attempts

# Feature Flag
export ATLAS_ENABLED=true  # Enable/disable Atlas integration

# Token Management
export ATLAS_TOKEN_TTL=86400  # 24 hours
export ATLAS_TOKEN_REFRESH_BUFFER=300  # 5 minutes
```

**In Code**:
```python
from rivet.integrations.atlas.config import atlas_config

# Check configuration
errors = atlas_config.validate_config()
if errors:
    print("Config errors:", errors)

# Check if production
if atlas_config.is_production:
    print("Running against production Atlas")

# Manual override
from rivet.integrations.atlas.client import AtlasClient

client = AtlasClient(
    base_url="https://custom-atlas.com/api",
    email="custom@example.com",
    password="custom_pass",
    timeout=60.0,
    max_retries=5
)
```

---

## Dependencies

```bash
# Install required packages
poetry add httpx pydantic-settings langsmith

# Optional: For LangSmith tracing
export LANGSMITH_API_KEY=lsv2_...
export LANGSMITH_TRACING=true
```

---

## Quick Implementation Guide

1. Copy source directory: `cp -r agent_factory/integrations/atlas/ rivet/integrations/atlas/`
2. Install: `poetry add httpx pydantic-settings langsmith`
3. Set env vars: `ATLAS_BASE_URL`, `ATLAS_EMAIL`, `ATLAS_PASSWORD`
4. Validate: `python -c "from rivet.integrations.atlas import AtlasClient; print('OK')"`

---

## Validation

```bash
# Test import
python -c "from rivet.integrations.atlas.client import AtlasClient; print('OK')"

# Test configuration
python -c "
from rivet.integrations.atlas.config import atlas_config

errors = atlas_config.validate_config()
if errors:
    print('Config errors:', errors)
else:
    print(f'Atlas URL: {atlas_config.atlas_base_url}')
    print(f'Enabled: {atlas_config.atlas_enabled}')
"

# Test health check (requires Atlas running)
python -c "
import asyncio
from rivet.integrations.atlas.client import AtlasClient

async def test():
    async with AtlasClient() as client:
        health = await client.health_check()
        print(f'Atlas status: {health[\"status\"]}')

asyncio.run(test())
"
```

---

## Integration Notes

**RIVET Troubleshooting → Atlas Work Order**:
```python
from rivet.integrations.atlas.client import AtlasClient
from rivet.core.orchestrator import RivetOrchestrator

async def handle_troubleshooting_escalation(query, user_id):
    """
    User asks about critical fault → Create work order in Atlas CMMS.
    """
    # Generate response via RIVET
    response = await orchestrator.route_query(query, user_id)

    # If critical issue detected → Create work order
    if response.priority == "CRITICAL":
        async with AtlasClient() as client:
            work_order = await client.create_work_order({
                "title": f"Critical Issue: {query[:100]}",
                "description": f"User query: {query}\n\nRIVET response: {response.response_text}",
                "priority": "CRITICAL",
                "status": "PENDING",
                "assignedTo": [response.recommended_expert_id]
            })

            # Notify user
            return f"{response.response_text}\n\n🔧 Work order created: {work_order['id']}"
```

**B2B Integration Points**:
- **ServiceTitan**: Export work orders to ServiceTitan API
- **MaintainX**: Sync assets and work orders
- **RIVET Knowledge Base**: Tag work orders with KB atom IDs for feedback loop

**Performance**:
- **Auth latency**: <500ms (first request only, then cached)
- **API latency**: <200ms (typical, depends on Atlas deployment)
- **Retry delay**: 1s, 2s, 4s (exponential backoff)

---

## What This Enables

- ✅ B2B CMMS integration (ServiceTitan, MaintainX partnerships)
- ✅ Automated work order creation (AI troubleshooting → field service)
- ✅ Asset tracking (sync equipment database with CMMS)
- ✅ User management (programmatic user provisioning)
- ✅ JWT auth with caching (24-hour token, auto-refresh)
- ✅ Retry resilience (exponential backoff, 3 attempts)
- ✅ Error transparency (6 exception types for granular handling)
- ✅ Observability (LangSmith tracing on all API calls)

---

## Next Steps

After implementing HARVEST 24, proceed to **HARVEST 25: Manus Client** for Manus robotics platform integration.

SEE FULL SOURCE:
- `agent_factory/integrations/atlas/client.py` (529 lines, 18.22KB)
- `agent_factory/integrations/atlas/config.py` (120 lines, 4.19KB)
- `agent_factory/integrations/atlas/exceptions.py` (155 lines, 4.01KB)
- `agent_factory/integrations/atlas/__init__.py`
