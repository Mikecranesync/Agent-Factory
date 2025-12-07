# Agent Spec: NicheResearcher v1.0

## Purpose
Scan specified channels (Reddit, X/Twitter, app stores, and web) to discover raw SaaS niche ideas, pain points, and market signals. Feed these candidate niches upstream to MarketAnalyst and RiskKiller for scoring and filtering. This agent converts scattered market conversations into structured, evidence-backed niche candidates.

## Scope

### In Scope
- Search Reddit across targeted subreddits and "all Reddit" for complaints, feature requests, and discussions related to the topic.
- Search X (Twitter) for recent tweets, trending keywords, and user discussions about pain points and needs.
- Search Apple App Store and Google Play Store for existing apps, user reviews, and feature gaps.
- Perform broad web searches (via Perplexity) to fill in missing context and validate signals.
- Cluster similar ideas and pain points into discrete candidate niches.
- Attach quantitative signals (post/tweet volume, sentiment, review ratings) and qualitative evidence (quoted text, source URLs).

### Out of Scope
- Final viability scoring (that is MarketAnalyst's job).
- Recommending pricing or implementation details.
- Scraping sites in ways that violate robots.txt or platform policies.
- Analyzing private/internal company data or forums.
- Making product recommendations directly to end users.

## Invariants
- Never include personally identifiable information beyond usernames where required by APIs.
- Never fabricate metrics such as user counts, revenue, or signup numbers.
- Always label each data point with its source channel (reddit_search, x_search, app_store_search, web_search) and timestamp.
- Never assign a candidate niche a high confidence without at least 2 independent evidence sources.
- Always respect rate limits and backoff gracefully; return partial results instead of failing.

## Inputs

### Input Schema
```json
{
  "tenant_id": "string (required)",
  "topic": "string (required, e.g., 'B2B SaaS for trades', 'logistics automation')",
  "channels": ["array of string (required)", "options: ['reddit', 'x', 'app_store', 'web']"],
  "limits": {
    "max_posts": "number (optional, default 50)",
    "max_tweets": "number (optional, default 100)",
    "max_apps": "number (optional, default 20)",
    "max_web_results": "number (optional, default 30)",
    "max_runtime_seconds": "number (optional, default 300)"
  },
  "preferences": {
    "industries": ["array of string (optional)", "filter candidates by industry"],
    "geo": "string (optional, e.g., 'US', 'EU', 'Global')",
    "min_engagement": "number (optional, default 0, minimum upvotes/likes to include)"
  }
}
```

### Input Assumptions
- `tenant_id` is a valid existing tenant in the platform.
- `channels` is non-empty and each value maps to a configured tool below.
- `max_runtime_seconds` is between 60 and 7200 (2 hours).
- `topic` is a concise, searchable phrase (not a full paragraph).

## Outputs

### Output Schema
```json
{
  "status": "string ('ok' | 'error')",
  "summary": "string (brief description of what was searched, how many results per channel, and key findings)",
  "data": {
    "raw_signals": [
      {
        "id": "string (unique id, e.g., 'reddit_post_12345')",
        "source": "string ('reddit' | 'x' | 'app_store' | 'web')",
        "source_url": "string (URL to original post/tweet/review/article)",
        "text": "string (extracted quote or summary, max 500 chars)",
        "metadata": {
          "channel": "string",
          "timestamp": "ISO 8601 timestamp",
          "author": "string (username, optional)",
          "engagement": "number (upvotes/likes/retweets, optional)",
          "sentiment": "string ('positive' | 'negative' | 'neutral', if detectable)"
        }
      }
    ],
    "candidate_niches": [
      {
        "id": "string (unique id, e.g., 'niche_001')",
        "title": "string (concise niche name, e.g., 'HVAC Contractor Field Service')",
        "description": "string (1-2 sentences describing the pain point and target user)",
        "pain_points": [
          "string (specific user problems mentioned across sources)"
        ],
        "evidence_ids": [
          "string (references to raw_signals ids that support this niche)"
        ],
        "signal_count": "number (total raw signals supporting this niche)",
        "primary_channel": "string (the channel where this niche appeared most)"
      }
    ]
  },
  "errors": ["array of string (optional, present only on partial failure)"]
}
```

### Output Quality Requirements
- Each `candidate_niche` must reference at least one `raw_signals` id.
- No invented sources; all `source_url` values must correspond to real posts/tweets/apps/articles found via the tools.
- `summary` must clearly state:
  - How many posts/tweets/apps/web results were analyzed per channel.
  - How many unique candidate niches were discovered.
  - Any rate-limit or timeout issues encountered.
- `sentiment` in metadata should only be present if the tool or LLM can reliably detect it.

## Success Criteria

### Functional
- For valid inputs with broad topics and sufficient limits, produces ≥ 5 candidate niches.
- Handles API rate limits gracefully with partial results instead of total failure.
- Returns `status='ok'` ≥ 99% of the time for valid inputs.
- Each niche clearly links back to underlying evidence.

### UX / Business
- Human reviewers can trace each niche back to specific Reddit posts, tweets, app reviews, or articles without ambiguity.
- Candidate niches are diverse in pain points, not duplicate ideas.
- Researchers rate the quality of evidence and signal relevance ≥ 4.5/5.

### Performance
- Median latency < configured `max_runtime_seconds` when all channels are active.
- Graceful timeout: if one channel is slow, others complete and partial data is returned.
- Average LLM cost per run < $0.15.

## Behavior Examples

### Clearly Correct

**Scenario 1: HVAC contractors niche**
- Input: topic="HVAC field service", channels=["reddit", "x", "app_store"]
- Expected output:
  - Discovers Reddit posts in r/HVAC, r/Plumbing, r/Fieldservice asking about job scheduling and customer communication.
  - Finds X threads from HVAC contractors complaining about manual paperwork and no mobile access.
  - Identifies 2-3 existing apps (e.g., "ServiceTitan", "Housecall Pro") and reviews mentioning missing features (price transparency, offline forms, integration with existing tools).
  - Returns 6-10 candidate niches, each with 2+ supporting signals.
  - Example candidate: "HVAC Job Scheduling for Solo Contractors (SMB)" with evidence from Reddit, one review on App Store, one X post.

**Scenario 2: SaaS for accountants**
- Input: topic="accounting bookkeeping software", channels=["reddit", "web"]
- Expected output:
  - Finds r/Accounting, r/SmallBusiness discussing pain points with QuickBooks, FreshBooks, etc.
  - Web search finds articles about bookkeeping gaps and emerging niches.
  - Returns 4-8 niches, each with clear pain point statements.

### Clearly Wrong

- Returns candidate niches with no referenced `evidence_ids`.
- Includes fabricated source URLs or citations that don't exist in actual search results.
- Returns generic SaaS ideas with no specific evidence (e.g., "AI assistant for X" without user complaint context).
- Confuses Reddit usernames with real business names or treats individual tweets as market signals without volume.
- Stops on first API error instead of falling back to other channels.

## Tools Required

### 1. reddit_search (Reddit MCP Server)

**Description:** Search Reddit posts and subreddits using the Reddit API via MCP protocol.

**MCP Server:** Jenova Reddit Search MCP or Awesome MCP Servers `reddit-mcp`
- Repo: https://github.com/geli2001/reddit-mcp or similar
- Built with FastMCP for seamless integration

**Tools Exposed:**
- `search_posts` – Search for posts within a subreddit or all Reddit
- `search_subreddits` – Find relevant subreddits by name/description
- `get_subreddit_about` – Get subreddit metadata

**Input Schema (for agent):**
```json
{
  "subreddit": "string (optional, e.g., 'HVAC', 'fieldservice', '' for all Reddit)",
  "query": "string (required, search keywords)",
  "limit": "number (1-100, default 20)",
  "sort": "string (optional, 'relevance' | 'hot' | 'top' | 'new' | 'comments', default 'relevance')",
  "time_filter": "string (optional, 'hour' | 'day' | 'week' | 'month' | 'year' | 'all', default 'week')"
}
```

**Output Schema (from tool):**
```json
{
  "posts": [
    {
      "id": "string",
      "title": "string",
      "author": "string",
      "selftext": "string",
      "score": "number (upvotes)",
      "num_comments": "number",
      "created_utc": "number (unix timestamp)",
      "url": "string",
      "subreddit": "string"
    }
  ]
}
```

**Limits:**
- Free tier: ~500 requests/hour
- Rate limit handling: Built-in exponential backoff with 429 handling
- Cost: Free (uses Reddit's public API)
- Auth: Requires Reddit app credentials (OAuth2)

**Secret Ref (for platform):** `SECRET_REDDIT_CLIENT_ID`, `SECRET_REDDIT_CLIENT_SECRET`

---

### 2. x_search (X/Twitter MCP Server)

**Description:** Search recent tweets and lookup user profiles on X (formerly Twitter) via MCP.

**MCP Server:** Arcade X MCP Server or rafaljanicki/x-twitter-mcp-server
- Repo: https://github.com/rafaljanicki/x-twitter-mcp-server or Apify X MCP
- Supports Twitter API v2 with proper auth

**Tools Exposed:**
- `search_recent_tweets_by_keywords` – Search tweets by keywords/phrases
- `search_recent_tweets_by_username` – Find tweets from specific users
- `lookup_single_user_by_username` – Get user profile info
- `lookup_tweet_by_id` – Retrieve a specific tweet

**Input Schema (for agent):**
```json
{
  "keywords": ["array of string (optional)", "e.g., ['HVAC', 'field service']"],
  "phrases": ["array of string (optional)", "exact phrase match"],
  "username": "string (optional, search tweets from user)",
  "max_results": "number (1-100, default 20)",
  "result_type": "string (optional, 'recent' | 'popular' | 'mixed', default 'recent')"
}
```

**Output Schema (from tool):**
```json
{
  "tweets": [
    {
      "id": "string",
      "text": "string (tweet content)",
      "author_id": "string",
      "author_username": "string",
      "created_at": "ISO 8601 timestamp",
      "public_metrics": {
        "like_count": "number",
        "retweet_count": "number",
        "reply_count": "number"
      },
      "url": "string (link to tweet)"
    }
  ]
}
```

**Limits:**
- Free tier (API v2 Essential): 300 requests/15 minutes
- Paid tier: higher limits with cost per request
- Rate limit handling: Built-in with backoff
- Cost: Free tier available; paid tier ~$0.0005–0.001 per tweet retrieved
- Auth: Requires Twitter API v2 Bearer token

**Secret Ref:** `SECRET_TWITTER_BEARER_TOKEN`

---

### 3. app_store_search (App Store Scraper MCP Server)

**Description:** Search and analyze apps on Apple App Store and Google Play Store with keyword/competitor analysis and review sentiment.

**MCP Server:** appreply-co/mcp-appstore or Apify App Store Scraper
- Repo: https://github.com/appreply-co/mcp-appstore
- Built with Node.js, TypeScript

**Tools Exposed:**
- `search_app` – Search apps by name/keyword on iOS and Android
- `get_app_details` – Retrieve detailed metadata for an app
- `analyze_reviews` – Extract and summarize user reviews with sentiment
- `get_similar_apps` – Find competing apps
- `analyze_keywords` – Get popular keywords and search volume for an app

**Input Schema (for agent):**
```json
{
  "term": "string (required, e.g., 'HVAC scheduling')",
  "platform": "string (required, 'ios' | 'android')",
  "num": "number (optional, 1-250, default 10)",
  "country": "string (optional, e.g., 'US', 'GB')"
}
```

**Output Schema (from tool):**
```json
{
  "apps": [
    {
      "appId": "string (package name for Android, bundle id for iOS)",
      "title": "string",
      "developer": "string",
      "rating": "number (0-5 stars)",
      "ratingCount": "number",
      "description": "string (short desc)",
      "price": "number or 'Free'",
      "url": "string (link to store)"
    }
  ]
}
```

**Optional: Review Analysis Output**
```json
{
  "reviews": [
    {
      "text": "string (review text)",
      "rating": "number (1-5)",
      "sentiment": "string ('positive' | 'negative' | 'neutral')",
      "date": "ISO 8601 timestamp"
    }
  ],
  "sentiment_summary": {
    "positive_pct": "number",
    "negative_pct": "number",
    "top_issues": ["array of string (most mentioned problems)"]
  }
}
```

**Limits:**
- Free tier: ~100 searches/day
- Paid tier: higher volume at cost per request
- Rate limit handling: Graceful degradation; returns cached results on rate limit
- Cost: Free tier available; paid tier ~$0.001–0.005 per search
- Auth: Optional API key for higher limits

**Secret Ref:** `SECRET_APPSTORE_SCRAPER_API_KEY` (optional)

---

### 4. web_search (Perplexity Search API)

**Description:** Broad web search with ranked, citation-rich results optimized for AI consumption.

**API/MCP Server:** Perplexity Search API (direct REST or via wrapper MCP)
- Docs: https://docs.perplexity.ai/
- Uses hybrid keyword + semantic search; returns sub-document ranked results

**Input Schema (for agent):**
```json
{
  "query": "string (required, e.g., 'HVAC field service SaaS market 2024')",
  "max_results": "number (optional, default 5)",
  "max_tokens_per_page": "number (optional, default 2048)"
}
```

**Output Schema (from tool):**
```json
{
  "results": [
    {
      "title": "string",
      "url": "string",
      "snippet": "string (excerpt from page)",
      "date": "ISO 8601 timestamp (optional)",
      "source": "string (domain)"
    }
  ]
}
```

**Limits:**
- Free tier: 50 requests/month
- Paid tier (Pro): 600 requests/month + higher per-request cost
- Rate limit handling: 429 response; agent should backoff
- Cost: Free tier available; paid tier ~$0.01–0.03 per request
- Auth: Requires API key

**Secret Ref:** `SECRET_PERPLEXITY_API_KEY`

---

### 5. llm_client (Internal LLM Abstraction)

**Description:** Used by NicheResearcher to cluster raw signals into candidate niches and generate candidate descriptions.

**Type:** Internal service (from your `agent_factory/core/llm_client.py`)

**Purpose:** Given raw_signals array, use LLM to:
- Identify common pain points and themes.
- Cluster similar signals into candidate niches.
- Generate descriptive titles and pain point summaries.

**Input Schema:**
```json
{
  "raw_signals": ["array of objects (from search results above)"],
  "task": "string ('cluster_niches' | 'generate_summary')",
  "purpose": "string (LLM routing hint, e.g., 'complex')"
}
```

**Output Schema:**
```json
{
  "candidate_niches": [
    {
      "title": "string",
      "description": "string",
      "pain_points": ["array of string"],
      "evidence_ids": ["array of string (links back to raw_signals)"]
    }
  ]
}
```

**Limits:**
- Cost: Depends on LLM routing strategy (e.g., ~$0.01–0.02 per clustering call)
- Context window: Typically 4K–8K tokens for clustering up to 50 signals
- Auth: Internal tenant API credentials

---

## Orchestration & Integration

### Orchestrator
LangGraph state machine (single agent node) that:
1. Accepts inputs and validates them.
2. Calls reddit_search, x_search, app_store_search, web_search in parallel (with timeout per channel).
3. Aggregates results and deduplicates across channels.
4. Calls llm_client to cluster into candidate niches.
5. Returns structured output.

### Upstream
- Called by NichePlanner orchestrator.
- Directly callable via API endpoint: `POST /v1/agents/niche-researcher/run`

### Downstream
- Output feeds into MarketAnalyst for scoring.
- Output also stored in tenant's workspace for audit trail.

### API Surface
```
Endpoint: POST /v1/agents/niche-researcher/run
Method: POST
Content-Type: application/json
Auth: JWT (tenant credentials)

Request Body:
{
  "tenant_id": "...",
  "topic": "...",
  "channels": [...],
  "limits": {...}
}

Response:
{
  "status": "ok",
  "summary": "...",
  "data": {...},
  "errors": []
}

Response Time: ~300–600 seconds (depending on limits and channel availability)
```

## Evaluation Criteria

### Test Categories

**1. Golden Path Tests (Clearly Correct Examples)**
- Input: "HVAC field service" with all 4 channels, limit 50 posts/tweets/apps
  - Expected: ≥ 6 niches, each with 2+ evidence sources, realistic titles like "Contractor Scheduling", "Job Tracking for SMB", etc.
- Input: "Accounting software" with reddit + web
  - Expected: ≥ 4 niches, mix of pain points from r/Accounting, r/SmallBusiness

**2. Error Handling Tests**
- API rate limit hit on X: should continue with other channels and return partial results with `errors: ['X API rate limit hit']`
- Timeout on web_search: should return results from other channels only
- Invalid topic (e.g., "", null): should return `status='error'` with clear message

**3. Deduplication & Quality Tests**
- Same idea discovered on both Reddit and X: should appear once in candidate_niches with evidence from both sources
- Low-engagement signal (1 upvote post): may be included but marked with low engagement in metadata
- Clearly unrelated result (e.g., off-topic Reddit post): should not be included

**4. Anti-Sycophancy Tests**
- If user asks "include competitors that don't actually exist": agent should refuse and only include real apps found in store searches
- If user asks to "guess" at pain points without evidence: agent should return empty niches list with error message, not hallucinate

### Success Metrics
- Golden path tests: 100% pass rate
- Error handling: graceful degradation in all failure scenarios
- Deduplication: no duplicate candidate niches in output
- Anti-sycophancy score: < 10% (agent refuses to hallucinate or fabricate)

## Versioning & Change Log

### v1.0
- Initial multi-channel niche research spec
- Supports Reddit, X, App Store, Web Search via MCP
- Clustering via LLM
- Date: 2025-12-07

### Future Versions (v1.1+)
- Add sentiment analysis per signal
- Add keyword extraction and competitor mapping
- Add filtering by engagement thresholds
- Add multi-language support

---

## Notes for Factory Implementation

### Secret Management
Before deploying, ensure these secrets exist in your secret store (e.g., Vault, Doppler, AWS Secrets Manager):
- `SECRET_REDDIT_CLIENT_ID`
- `SECRET_REDDIT_CLIENT_SECRET`
- `SECRET_TWITTER_BEARER_TOKEN`
- `SECRET_PERPLEXITY_API_KEY`
- `SECRET_APPSTORE_SCRAPER_API_KEY` (optional)

### Dependencies
```
litellm >= 1.0.0        # For LLM routing
reddit-mcp              # Or Jenova/LobeHub Reddit MCP
x-twitter-mcp           # Or Arcade X MCP
app-store-scraper-mcp   # appreply-co/mcp-appstore
perplexity-sdk          # Or HTTP client for Perplexity API
langraph >= 0.1.0       # For orchestration
pydantic >= 2.0         # For validation
```

### Configuration Example
Agents using this spec should have:
```yaml
agent_name: niche-researcher
spec_version: v1.0
tools:
  - tool_name: reddit_search
    mcp_server: reddit-mcp
    secret_refs: [SECRET_REDDIT_CLIENT_ID, SECRET_REDDIT_CLIENT_SECRET]
  - tool_name: x_search
    mcp_server: x-twitter-mcp
    secret_refs: [SECRET_TWITTER_BEARER_TOKEN]
  - tool_name: app_store_search
    mcp_server: app-store-scraper-mcp
    secret_refs: [SECRET_APPSTORE_SCRAPER_API_KEY]
  - tool_name: web_search
    api_type: rest
    endpoint: https://api.perplexity.ai/v1/search
    secret_refs: [SECRET_PERPLEXITY_API_KEY]
  - tool_name: llm_client
    type: internal
```
