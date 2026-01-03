# HARVEST BLOCK 21: Settings Service

**Priority**: MEDIUM
**Size**: 10.40KB (285 lines)
**Source**: `agent_factory/core/settings_service.py`
**Target**: `rivet/core/settings_service.py`

---

## Overview

Database-backed runtime configuration with environment variable fallback - enables zero-downtime config changes without service restarts (production pattern from Archon 13.4k⭐).

### What This Adds

- **Database-backed settings**: Store config in Supabase PostgreSQL
- **Environment fallback**: Falls back to .env if database unavailable
- **Category organization**: Settings grouped by category (llm, memory, orchestration)
- **Typed getters**: get_int(), get_bool(), get_float() for type-safe retrieval
- **5-minute cache**: Reduces database load with auto-reload
- **Runtime changes**: Update settings without restarting service
- **Graceful degradation**: Works without database (env vars only)

### Key Features

```python
from rivet.core.settings_service import settings

# Get string settings
model = settings.get("DEFAULT_MODEL", category="llm")
# Returns: "gpt-4o" or env var or default

# Get typed settings
batch_size = settings.get_int("BATCH_SIZE", default=50, category="memory")
use_hybrid = settings.get_bool("USE_HYBRID_SEARCH", category="memory")
temperature = settings.get_float("DEFAULT_TEMPERATURE", default=0.7, category="llm")

# Set values programmatically (if database available)
settings.set("DEBUG_MODE", "true", category="general")

# Reload from database (picks up runtime changes)
settings.reload()

# Check if setting exists
if settings.has("CUSTOM_SETTING"):
    value = settings.get("CUSTOM_SETTING")
```

---

## Category Organization

```python
# Settings grouped by functional category

LLM_SETTINGS = {
    "DEFAULT_MODEL": "gpt-4o",
    "DEFAULT_TEMPERATURE": "0.7",
    "MAX_TOKENS": "2000",
    "ENABLE_STREAMING": "false"
}

MEMORY_SETTINGS = {
    "BATCH_SIZE": "50",
    "USE_HYBRID_SEARCH": "true",
    "SIMILARITY_THRESHOLD": "0.5"
}

ORCHESTRATION_SETTINGS = {
    "ENABLE_ROUTE_A": "true",
    "ENABLE_ROUTE_B": "true",
    "ENABLE_ROUTE_C": "true",
    "ENABLE_ROUTE_D": "true"
}

# Usage:
model = settings.get("DEFAULT_MODEL", category="llm")
batch = settings.get_int("BATCH_SIZE", category="memory")
```

---

## Typed Getters

```python
# Type-safe setting retrieval

# get_int() - Parse as integer
batch_size = settings.get_int("BATCH_SIZE", default=50)
# Returns: int (50)

# get_bool() - Parse as boolean
use_cache = settings.get_bool("ENABLE_CACHE", default=True)
# Returns: bool (True)
# Accepts: "true", "True", "1", "yes", "on" → True
#          "false", "False", "0", "no", "off" → False

# get_float() - Parse as float
temperature = settings.get_float("TEMPERATURE", default=0.7)
# Returns: float (0.7)

# get() - Return as string (default)
model = settings.get("DEFAULT_MODEL", default="gpt-4o")
# Returns: str ("gpt-4o")
```

---

## 5-Minute Cache with Auto-Reload

```python
class SettingsService:
    def __init__(self):
        self._cache = {}
        self._cache_timestamp = 0
        self._cache_ttl = 300  # 5 minutes

    def get(self, key, default=None, category=None):
        """Get setting with 5-minute cache"""

        # Check if cache expired
        if time.time() - self._cache_timestamp > self._cache_ttl:
            self.reload()  # Auto-reload from database

        # Return cached value
        cache_key = f"{category}:{key}" if category else key
        return self._cache.get(cache_key, default)

    def reload(self):
        """Force reload from database"""
        self._cache = self._load_from_db()
        self._cache_timestamp = time.time()
```

---

## Runtime Configuration Changes

```python
# Update setting at runtime (no service restart)

# 1. Update in database (via Supabase admin panel)
# 2. Settings service auto-reloads within 5 minutes
# 3. Or force immediate reload

settings.set("DEBUG_MODE", "true")
# Writes to database, updates cache

# Force reload across all instances
settings.reload()
# All instances pick up new settings within 5 minutes
```

---

## Database Schema

```sql
-- Supabase table schema
CREATE TABLE IF NOT EXISTS settings (
    id SERIAL PRIMARY KEY,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    category TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(key, category)
);

-- Example rows:
INSERT INTO settings (key, value, category, description) VALUES
    ('DEFAULT_MODEL', 'gpt-4o', 'llm', 'Default LLM model'),
    ('BATCH_SIZE', '50', 'memory', 'Batch size for vector search'),
    ('ENABLE_CACHE', 'true', 'general', 'Enable response caching');
```

---

## Environment Variable Fallback

```python
# Fallback order:
# 1. Database (if available)
# 2. Environment variable
# 3. Default value

def get(self, key, default=None, category=None):
    # Try database first
    if self.db_available:
        db_value = self._get_from_db(key, category)
        if db_value is not None:
            return db_value

    # Fallback to environment variable
    env_value = os.getenv(key)
    if env_value is not None:
        return env_value

    # Use default
    return default
```

---

## Dependencies

```bash
# Install required packages
poetry add supabase

# Or use stdlib only (env vars fallback)
# No dependencies needed if database disabled
```

## Environment Variables

```bash
# Database connection (optional)
export SUPABASE_URL=https://your-project.supabase.co
export SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Fallback settings (if database unavailable)
export DEFAULT_MODEL=gpt-4o
export BATCH_SIZE=50
export ENABLE_CACHE=true
```

---

## Quick Implementation Guide

1. Copy source file: `cp agent_factory/core/settings_service.py rivet/core/settings_service.py`
2. Install: `poetry add supabase` (optional)
3. Run migration: Execute SQL from `docs/supabase_migrations.sql` in Supabase SQL Editor
4. Validate: `python -c "from rivet.core.settings_service import settings; print(settings)"`

---

## Validation

```bash
# Test import
python -c "from rivet.core.settings_service import settings; print('OK')"

# Test retrieval
python -c "
from rivet.core.settings_service import settings

# Get with default
model = settings.get('DEFAULT_MODEL', default='gpt-4o')
print(f'Model: {model}')

# Get typed
batch = settings.get_int('BATCH_SIZE', default=50)
print(f'Batch size: {batch}')
"
```

---

## Integration Notes

**Usage Throughout Codebase**:
```python
# In LLM Router
from rivet.core.settings_service import settings

model = settings.get("DEFAULT_MODEL", category="llm")
temperature = settings.get_float("DEFAULT_TEMPERATURE", default=0.7, category="llm")

# In Memory Layer
batch_size = settings.get_int("BATCH_SIZE", default=50, category="memory")
use_hybrid = settings.get_bool("USE_HYBRID_SEARCH", category="memory")

# In Orchestrator
enable_route_a = settings.get_bool("ENABLE_ROUTE_A", default=True, category="orchestration")
```

**Runtime Configuration Example**:
```python
# Update setting at runtime (admin panel)
# 1. Login to Supabase admin
# 2. Open settings table
# 3. Update value for key="DEFAULT_MODEL"
# 4. Settings service auto-reloads within 5 minutes

# Or programmatically:
settings.set("DEFAULT_MODEL", "gpt-4-turbo")
settings.reload()  # Force immediate reload
```

---

## What This Enables

- ✅ Zero-downtime configuration changes (no service restart)
- ✅ Database-backed settings (Supabase PostgreSQL)
- ✅ Environment variable fallback (works without database)
- ✅ Category organization (llm, memory, orchestration)
- ✅ Type-safe retrieval (int, bool, float)
- ✅ 5-minute cache (reduces database load)
- ✅ Runtime changes (update settings while service running)

---

## Next Steps

After implementing HARVEST 21, proceed to **HARVEST 22: TTL Cache** for time-to-live caching of LLM responses.

SEE FULL SOURCE: `agent_factory/core/settings_service.py` (285 lines - copy as-is)

SEE ALSO: `examples/settings_demo.py` for usage examples
