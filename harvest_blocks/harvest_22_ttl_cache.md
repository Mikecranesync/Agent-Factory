# HARVEST BLOCK 22: TTL Cache

**Priority**: MEDIUM
**Size**: ~8KB (220 lines)
**Source**: `agent_factory/llm/cache.py`
**Target**: `rivet/llm/cache.py`

---

## Overview

Time-to-live caching for LLM responses, tool results, and semantic searches - reduces API costs and latency for repeated queries with configurable expiration per cache key.

### What This Adds

- **TTL-based expiration**: Configurable time-to-live per cache entry (default 5 minutes)
- **LRU eviction**: Least Recently Used eviction when cache full (max 1000 entries)
- **Hash-based keys**: MD5 hash of query + params for consistent keys
- **Hit rate tracking**: Monitor cache performance (hits/misses/evictions)
- **Category support**: Separate caches for LLM, embeddings, tool results
- **Thread-safe**: Mutex locks for concurrent access
- **Manual invalidation**: Clear specific keys or entire categories

### Key Features

```python
from rivet.llm.cache import TTLCache

# Initialize cache
cache = TTLCache(
    max_size=1000,  # Max 1000 entries
    default_ttl=300  # 5 minutes default TTL
)

# Cache LLM response
query = "How to reset S7-1200 fault F0003?"
response = "Check communication cable..."

cache.set(
    key=query,
    value=response,
    ttl=300,  # 5 minutes
    category="llm"
)

# Retrieve from cache
cached_response = cache.get(query, category="llm")
if cached_response is not None:
    print("Cache hit!")
    return cached_response
else:
    print("Cache miss - calling LLM...")
    response = call_llm(query)
    cache.set(query, response, category="llm")
    return response

# Get cache stats
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']:.1%}")
print(f"Hits: {stats['hits']}, Misses: {stats['misses']}")
print(f"Size: {stats['size']}/{stats['max_size']}")
```

---

## TTL-Based Expiration

```python
# Each cache entry has:
# - key: Hash of query + params
# - value: Cached result
# - ttl: Time to live (seconds)
# - timestamp: When entry was created
# - access_count: LRU tracking

# Entry structure
@dataclass
class CacheEntry:
    key: str
    value: Any
    category: str
    timestamp: float
    ttl: int
    access_count: int = 0

# Expiration check
def is_expired(entry):
    age = time.time() - entry.timestamp
    return age > entry.ttl

# Auto-cleanup expired entries
def cleanup():
    for key, entry in cache.items():
        if is_expired(entry):
            del cache[key]
```

---

## Hash-Based Keys

```python
import hashlib
import json

def generate_cache_key(query, params=None):
    """Generate consistent cache key from query + params"""

    # Combine query with params
    cache_input = {
        "query": query,
        "params": params or {}
    }

    # Sort keys for consistency
    cache_str = json.dumps(cache_input, sort_keys=True)

    # MD5 hash
    cache_key = hashlib.md5(cache_str.encode()).hexdigest()

    return cache_key

# Example:
key1 = generate_cache_key("test query", {"temperature": 0.7})
key2 = generate_cache_key("test query", {"temperature": 0.7})
assert key1 == key2  # Same input → same key
```

---

## LRU Eviction

```python
# When cache full → evict least recently used

def evict_lru():
    """Evict least recently used entry"""

    # Find entry with lowest access count
    lru_key = min(
        cache.keys(),
        key=lambda k: cache[k].access_count
    )

    # Remove from cache
    del cache[lru_key]
    stats['evictions'] += 1

# On cache set:
if len(cache) >= max_size:
    evict_lru()

# On cache get:
entry.access_count += 1  # Update LRU tracking
```

---

## Category Support

```python
# Separate caches for different use cases

# LLM responses (5 min TTL)
cache.set("query1", "response1", category="llm", ttl=300)

# Embeddings (1 hour TTL)
cache.set("text1", [0.1, 0.2, ...], category="embeddings", ttl=3600)

# Tool results (10 min TTL)
cache.set("search_query", results, category="tools", ttl=600)

# Semantic search (30 min TTL)
cache.set("vector_query", docs, category="semantic_search", ttl=1800)

# Clear specific category
cache.clear_category("llm")
```

---

## Cache Stats Tracking

```python
# Track cache performance
stats = {
    "hits": 0,
    "misses": 0,
    "evictions": 0,
    "size": 0,
    "max_size": 1000,
    "hit_rate": 0.0
}

# On cache hit
def get(key):
    if key in cache and not is_expired(cache[key]):
        stats['hits'] += 1
        stats['hit_rate'] = stats['hits'] / (stats['hits'] + stats['misses'])
        return cache[key].value
    else:
        stats['misses'] += 1
        stats['hit_rate'] = stats['hits'] / (stats['hits'] + stats['misses'])
        return None

# Example stats:
{
    "hits": 450,
    "misses": 550,
    "evictions": 25,
    "size": 1000,
    "max_size": 1000,
    "hit_rate": 0.45  # 45% hit rate
}
```

---

## Thread Safety

```python
import threading

class TTLCache:
    def __init__(self):
        self._cache = {}
        self._lock = threading.Lock()

    def get(self, key):
        with self._lock:
            # Thread-safe read
            return self._cache.get(key)

    def set(self, key, value, ttl=300):
        with self._lock:
            # Thread-safe write
            self._cache[key] = CacheEntry(key, value, ttl, time.time())
```

---

## Dependencies

```bash
# No dependencies (stdlib only)
```

---

## Quick Implementation Guide

1. Copy source file: `cp agent_factory/llm/cache.py rivet/llm/cache.py`
2. No dependencies needed (stdlib only)
3. Validate: `python -c "from rivet.llm.cache import TTLCache; print('OK')"`

---

## Validation

```bash
# Test import
python -c "from rivet.llm.cache import TTLCache; print('OK')"

# Test caching
python -c "
from rivet.llm.cache import TTLCache

cache = TTLCache(max_size=100, default_ttl=60)

# Set value
cache.set('key1', 'value1', category='test')

# Get value (cache hit)
value = cache.get('key1', category='test')
print(f'Cached value: {value}')

# Get stats
stats = cache.get_stats()
print(f'Hit rate: {stats[\"hit_rate\"]:.1%}')
"
```

---

## Integration Notes

**LLMRouter Integration** (5-min cache for expensive calls):
```python
from rivet.llm.cache import TTLCache

# Initialize cache
llm_cache = TTLCache(max_size=1000, default_ttl=300)  # 5 minutes

# In generate() method
def generate(prompt, model="gpt-4o", temperature=0.7):
    # Generate cache key
    cache_key = generate_cache_key(prompt, {
        "model": model,
        "temperature": temperature
    })

    # Check cache
    cached = llm_cache.get(cache_key, category="llm")
    if cached is not None:
        logger.info("LLM cache hit")
        return cached

    # Cache miss - call LLM
    logger.info("LLM cache miss - calling API")
    response = openai.chat.completions.create(...)

    # Cache response
    llm_cache.set(cache_key, response, category="llm", ttl=300)

    return response
```

**Cost Savings**:
- **Without cache**: 1000 requests × $0.002/req = $2.00
- **With cache (50% hit rate)**: 500 requests × $0.002/req = $1.00
- **Savings**: 50% cost reduction

---

## What This Enables

- ✅ Cost reduction (avoid repeated LLM API calls)
- ✅ Latency optimization (instant cache hits <1ms vs 500ms API call)
- ✅ TTL-based expiration (configurable per entry)
- ✅ LRU eviction (automatic memory management)
- ✅ Thread-safe access (concurrent requests supported)
- ✅ Hit rate tracking (monitor cache performance)
- ✅ Category support (separate caches for different use cases)

---

## TIER 3 COMPLETE! ✅

**All 7 TIER 3 extraction blocks created:**
- ✅ HARVEST 16: Context Extractor (deep equipment extraction)
- ✅ HARVEST 17: Unified Research Tool (multi-backend research)
- ✅ HARVEST 18: Conversation Manager (multi-turn state)
- ✅ HARVEST 19: RAG Retriever (vector similarity search)
- ✅ HARVEST 20: Confidence Scorer (multi-dimensional scoring)
- ✅ HARVEST 21: Settings Service (runtime configuration)
- ✅ HARVEST 22: TTL Cache (LLM response caching)

**Next Steps:**
1. Commit TIER 3 blocks
2. Proceed to **TIER 4: Integration & Monitoring Layer** (4 components: HARVEST 23-26)

SEE FULL SOURCE: `agent_factory/llm/cache.py` (220 lines - copy as-is)
