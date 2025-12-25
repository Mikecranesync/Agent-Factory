# Claude CLI Prompt: LangSmith Integration + Custom Dashboard + E2E Testing

## Objective

Integrate LangSmith tracing throughout the RivetCEO Bot system to capture:
- Route decisions (A, B, C, D) with confidence scores
- KB evaluator results and coverage metrics
- Gap detections and ingestion triggers
- OCR processing results
- SME agent calls and responses
- Latency per component
- Token usage and costs
- User interactions and feedback

Then build custom dashboards that visualize this data and validate with end-to-end tests.

## Current System Context

Based on the system map, we're tracing these components:

```
User Query
    ↓
Message Handler ←──────────────── TRACE: input, user_id, channel
    ↓
Orchestrator
    ├── KB Evaluator ←─────────── TRACE: coverage, confidence, route_decision
    ├── Route A (High) ←───────── TRACE: kb_results, citations
    ├── Route B (Moderate) ←───── TRACE: kb_results, sme_agent, augmentation
    ├── Route C (No Coverage) ←── TRACE: llm_fallback, gap_trigger, ingestion_job
    └── Route D (Escalation) ←─── TRACE: escalation_reason
    ↓
Response ←─────────────────────── TRACE: output, latency, tokens, cost
```

Additional flows to trace:
- OCR Pipeline: photo_type, equipment_extracted, tag_data
- SME Agents: vendor, query, response_quality
- Ingestion Worker: job_type, source, atoms_created
- Library Matcher: match_found, confidence

## Tech Stack

- `langsmith` SDK (Python)
- `@traceable` decorator for function-level tracing
- Metadata tags for filtering/grouping
- Custom dashboards via LangSmith UI

## Implementation

### 1. Install Dependencies

```bash
pip install langsmith
```

### 2. Environment Configuration

```bash
# Add to .env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=rivetceo-bot
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

```python
# agent_factory/config/langsmith_config.py
"""LangSmith configuration and initialization"""

import os
from functools import wraps

# Ensure env vars are set
def init_langsmith():
    """Initialize LangSmith tracing"""
    required_vars = ["LANGCHAIN_API_KEY"]
    missing = [v for v in required_vars if not os.getenv(v)]
    
    if missing:
        print(f"[LangSmith] Warning: Missing env vars: {missing}")
        print("[LangSmith] Tracing disabled")
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        return False
    
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGCHAIN_PROJECT", "rivetceo-bot")
    os.environ.setdefault("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    
    print(f"[LangSmith] Tracing enabled for project: {os.getenv('LANGCHAIN_PROJECT')}")
    return True

# Standard metadata tags
def get_base_metadata(user_id: str = None, channel: str = "telegram"):
    """Get standard metadata for all traces"""
    return {
        "channel": channel,
        "user_id": user_id,
        "environment": os.getenv("ENVIRONMENT", "development"),
        "version": os.getenv("APP_VERSION", "1.0.0"),
    }

# Standard tags
ROUTE_TAGS = {
    "A": ["route:A", "coverage:high"],
    "B": ["route:B", "coverage:moderate"],
    "C": ["route:C", "coverage:none", "gap:detected"],
    "D": ["route:D", "escalation"],
}
```

### 3. Tracing the Orchestrator (Core)

```python
# agent_factory/core/orchestrator.py
"""
Main orchestrator with LangSmith tracing
"""

import os
from datetime import datetime
from typing import Optional
from langsmith import traceable
from langsmith.run_helpers import get_current_run_tree

from agent_factory.config.langsmith_config import get_base_metadata, ROUTE_TAGS


class RivetOrchestrator:
    """4-route query orchestrator with full tracing"""
    
    def __init__(self, rag_layer, kb_evaluator, llm_router):
        self.rag_layer = rag_layer
        self.kb_evaluator = kb_evaluator
        self.llm_router = llm_router
    
    @traceable(
        run_type="chain",
        name="RivetOrchestrator.route_query",
        tags=["orchestrator", "main-flow"]
    )
    async def route_query(
        self,
        query: str,
        user_id: str,
        channel: str = "telegram",
        equipment_context: dict = None
    ) -> dict:
        """
        Main entry point - routes query through appropriate pipeline.
        
        Traced data:
        - Input query and context
        - Route decision with confidence
        - KB coverage metrics
        - Final response and latency
        """
        start_time = datetime.utcnow()
        
        # Add metadata to current trace
        run_tree = get_current_run_tree()
        if run_tree:
            run_tree.metadata.update({
                **get_base_metadata(user_id, channel),
                "has_equipment_context": equipment_context is not None,
                "query_length": len(query),
            })
        
        # Step 1: Evaluate KB coverage
        kb_decision = await self._evaluate_coverage(query, equipment_context)
        
        # Step 2: Route based on coverage
        route = kb_decision["route"]
        
        # Add route-specific tags
        if run_tree:
            run_tree.tags.extend(ROUTE_TAGS.get(route, []))
            run_tree.metadata["route"] = route
            run_tree.metadata["confidence"] = kb_decision["confidence"]
            run_tree.metadata["coverage_level"] = kb_decision["coverage_level"]
        
        # Step 3: Execute route
        if route == "A":
            response = await self._route_a_high_coverage(query, kb_decision, user_id)
        elif route == "B":
            response = await self._route_b_moderate_coverage(query, kb_decision, user_id)
        elif route == "C":
            response = await self._route_c_no_coverage(query, kb_decision, user_id)
        else:  # Route D
            response = await self._route_d_escalation(query, kb_decision, user_id)
        
        # Calculate latency
        end_time = datetime.utcnow()
        latency_ms = (end_time - start_time).total_seconds() * 1000
        
        # Final metadata
        if run_tree:
            run_tree.metadata["latency_ms"] = latency_ms
            run_tree.metadata["response_length"] = len(response.get("text", ""))
        
        response["latency_ms"] = latency_ms
        response["route"] = route
        
        return response
    
    @traceable(
        run_type="retriever",
        name="KB.evaluate_coverage",
        tags=["kb-evaluator"]
    )
    async def _evaluate_coverage(self, query: str, equipment_context: dict = None) -> dict:
        """
        Evaluate KB coverage for query.
        
        Traced data:
        - Query text
        - Equipment context if present
        - Coverage score and level
        - Route decision
        """
        # Enrich query with equipment context
        enriched_query = query
        if equipment_context:
            enriched_query = self._enrich_query(query, equipment_context)
        
        # Get KB decision
        decision = await self.kb_evaluator.evaluate(enriched_query)
        
        # Add to trace
        run_tree = get_current_run_tree()
        if run_tree:
            run_tree.metadata.update({
                "enriched_query": enriched_query[:500],  # Truncate for storage
                "top_k_results": decision.get("result_count", 0),
                "avg_relevance_score": decision.get("avg_score", 0),
            })
        
        return decision
    
    @traceable(
        run_type="chain",
        name="Route_A.high_coverage",
        tags=["route:A", "kb-only"]
    )
    async def _route_a_high_coverage(self, query: str, kb_decision: dict, user_id: str) -> dict:
        """
        High coverage route - KB answer with citations.
        
        Traced data:
        - KB results used
        - Citations generated
        - Response quality
        """
        # Get KB results
        kb_results = kb_decision.get("results", [])
        
        # Generate response from KB
        response = await self._generate_kb_response(query, kb_results)
        
        # Add trace metadata
        run_tree = get_current_run_tree()
        if run_tree:
            run_tree.metadata.update({
                "kb_atoms_used": len(kb_results),
                "citations_count": len(response.get("citations", [])),
                "source_vendors": list(set(r.get("vendor") for r in kb_results if r.get("vendor"))),
            })
        
        return response
    
    @traceable(
        run_type="chain",
        name="Route_B.moderate_coverage",
        tags=["route:B", "kb-plus-sme"]
    )
    async def _route_b_moderate_coverage(self, query: str, kb_decision: dict, user_id: str) -> dict:
        """
        Moderate coverage route - KB + SME augmentation.
        
        Traced data:
        - KB results
        - SME agent selected
        - Augmentation quality
        """
        kb_results = kb_decision.get("results", [])
        
        # Determine which SME to use
        vendor = self._detect_vendor(query, kb_results)
        
        # Get SME augmentation
        sme_response = await self._get_sme_augmentation(query, vendor, kb_results)
        
        # Merge responses
        response = await self._merge_kb_and_sme(kb_results, sme_response)
        
        # Trace
        run_tree = get_current_run_tree()
        if run_tree:
            run_tree.metadata.update({
                "kb_atoms_used": len(kb_results),
                "sme_vendor": vendor,
                "sme_augmented": True,
            })
        
        return response
    
    @traceable(
        run_type="chain",
        name="Route_C.no_coverage",
        tags=["route:C", "llm-fallback", "gap-detection"]
    )
    async def _route_c_no_coverage(self, query: str, kb_decision: dict, user_id: str) -> dict:
        """
        No coverage route - LLM fallback + gap detection + ingestion trigger.
        
        Traced data:
        - LLM model used
        - Gap detection result
        - Ingestion job queued
        - Token usage
        """
        # LLM fallback
        llm_response = await self._llm_fallback(query)
        
        # Gap detection
        gap_result = await self._detect_and_log_gap(query, user_id)
        
        # Queue ingestion if gap detected
        ingestion_job_id = None
        if gap_result.get("should_ingest"):
            ingestion_job_id = await self._queue_ingestion(gap_result)
        
        # Trace
        run_tree = get_current_run_tree()
        if run_tree:
            run_tree.metadata.update({
                "llm_model": llm_response.get("model"),
                "tokens_used": llm_response.get("tokens", 0),
                "gap_detected": gap_result.get("gap_detected", False),
                "gap_equipment": gap_result.get("equipment"),
                "gap_manufacturer": gap_result.get("manufacturer"),
                "ingestion_job_id": ingestion_job_id,
            })
        
        return {
            "text": llm_response["text"],
            "source": "llm_fallback",
            "gap_logged": gap_result.get("gap_id"),
            "ingestion_queued": ingestion_job_id is not None,
        }
    
    @traceable(
        run_type="chain",
        name="Route_D.escalation",
        tags=["route:D", "escalation", "human-required"]
    )
    async def _route_d_escalation(self, query: str, kb_decision: dict, user_id: str) -> dict:
        """
        Escalation route - flag for human expert.
        
        Traced data:
        - Escalation reason
        - Safety flag if applicable
        """
        escalation_reason = kb_decision.get("escalation_reason", "complex_query")
        
        # Log escalation
        escalation_id = await self._log_escalation(query, user_id, escalation_reason)
        
        # Trace
        run_tree = get_current_run_tree()
        if run_tree:
            run_tree.metadata.update({
                "escalation_reason": escalation_reason,
                "escalation_id": escalation_id,
                "is_safety_critical": "safety" in escalation_reason.lower(),
            })
        
        return {
            "text": "This query requires expert review. It has been flagged for a human specialist.",
            "source": "escalation",
            "escalation_id": escalation_id,
        }
    
    @traceable(run_type="llm", name="LLM.fallback", tags=["llm", "fallback"])
    async def _llm_fallback(self, query: str) -> dict:
        """LLM fallback when KB has no coverage"""
        # Use LLM router to get response
        model, response = await self.llm_router.route_and_call(query, task_type="complex")
        
        run_tree = get_current_run_tree()
        if run_tree:
            run_tree.metadata.update({
                "model": model,
                "prompt_tokens": response.get("usage", {}).get("prompt_tokens", 0),
                "completion_tokens": response.get("usage", {}).get("completion_tokens", 0),
            })
        
        return {
            "text": response["content"],
            "model": model,
            "tokens": response.get("usage", {}).get("total_tokens", 0),
        }
    
    @traceable(run_type="tool", name="Gap.detect_and_log", tags=["gap-detector"])
    async def _detect_and_log_gap(self, query: str, user_id: str) -> dict:
        """Detect knowledge gap and log for ingestion"""
        from agent_factory.core.gap_detector import GapDetector
        
        detector = GapDetector()
        gap_result = detector.analyze_query(query)
        
        if gap_result.get("gap_detected"):
            gap_id = await self.rag_layer.log_gap(
                query=query,
                equipment=gap_result.get("equipment"),
                manufacturer=gap_result.get("manufacturer"),
                user_id=user_id
            )
            gap_result["gap_id"] = gap_id
            gap_result["should_ingest"] = True
        
        return gap_result


### 4. Tracing SME Agents

```python
# agent_factory/agents/sme_agent.py
"""SME Agent with LangSmith tracing"""

from langsmith import traceable
from langsmith.run_helpers import get_current_run_tree


class SMEAgent:
    """Vendor-specific Subject Matter Expert agent"""
    
    def __init__(self, vendor: str, llm_client):
        self.vendor = vendor
        self.llm = llm_client
    
    @traceable(
        run_type="chain",
        name="SME.augment",
        tags=["sme-agent"]
    )
    async def augment(self, query: str, kb_context: list) -> dict:
        """
        Augment KB results with SME expertise.
        
        Traced data:
        - Vendor
        - Query
        - KB context provided
        - Augmentation response
        """
        # Build SME prompt
        prompt = self._build_sme_prompt(query, kb_context)
        
        # Call LLM
        response = await self.llm.acomplete(prompt)
        
        # Trace
        run_tree = get_current_run_tree()
        if run_tree:
            run_tree.tags.append(f"vendor:{self.vendor}")
            run_tree.metadata.update({
                "vendor": self.vendor,
                "kb_context_items": len(kb_context),
                "response_length": len(response.get("content", "")),
            })
        
        return {
            "vendor": self.vendor,
            "augmentation": response["content"],
            "model": response.get("model"),
        }
```

### 5. Tracing OCR Pipeline

```python
# agent_factory/ocr/pipeline.py (add tracing)
"""OCR Pipeline with LangSmith tracing"""

from langsmith import traceable
from langsmith.run_helpers import get_current_run_tree


class OCRPipeline:
    
    @traceable(
        run_type="chain",
        name="OCR.process_photo",
        tags=["ocr", "photo-analysis"]
    )
    async def process_photo(self, image_bytes: bytes, user_id: str = None) -> dict:
        """
        Process equipment photo.
        
        Traced data:
        - Photo size
        - Classification result
        - Equipment extracted
        - Tag data extracted
        - Processing time
        """
        from datetime import datetime
        start = datetime.utcnow()
        
        # Analyze photo
        analysis = await self.analyzer.analyze(image_bytes)
        
        # Build context
        context = self._build_context(analysis)
        
        # Calculate processing time
        processing_ms = (datetime.utcnow() - start).total_seconds() * 1000
        
        # Trace
        run_tree = get_current_run_tree()
        if run_tree:
            run_tree.metadata.update({
                "user_id": user_id,
                "image_size_bytes": len(image_bytes),
                "photo_type": analysis.photo_type,
                "equipment_type": analysis.equipment_type,
                "manufacturer": analysis.manufacturer,
                "model_number": analysis.model_number,
                "condition": analysis.condition,
                "issues_count": len(analysis.visible_issues),
                "confidence": analysis.confidence,
                "processing_ms": processing_ms,
                "has_tag_data": analysis.serial_number is not None,
            })
            
            # Add equipment-specific tags
            if analysis.equipment_type:
                run_tree.tags.append(f"equipment:{analysis.equipment_type}")
            if analysis.manufacturer:
                run_tree.tags.append(f"manufacturer:{analysis.manufacturer.lower().replace(' ', '-')}")
        
        return context
```

### 6. Tracing Ingestion Worker

```python
# worker/ingestion_worker.py (add tracing)
"""Ingestion worker with LangSmith tracing"""

from langsmith import traceable
from langsmith.run_helpers import get_current_run_tree


class IngestionWorker:
    
    @traceable(
        run_type="chain",
        name="Ingestion.process_job",
        tags=["ingestion", "kb-building"]
    )
    async def _process_job(self, job: dict):
        """
        Process a single ingestion job.
        
        Traced data:
        - Job type (url, pdf, search)
        - Trigger source
        - Atoms created
        - Processing time
        """
        job_type = job["data"].get("type")
        trigger = job["data"].get("trigger")
        
        # Add metadata
        run_tree = get_current_run_tree()
        if run_tree:
            run_tree.tags.extend([
                f"job-type:{job_type}",
                f"trigger:{trigger}",
                f"queue:{job['queue']}",
            ])
            run_tree.metadata.update({
                "job_id": job["data"].get("id"),
                "trigger": trigger,
                "job_type": job_type,
                "priority": job["queue"].split(":")[-1],
            })
        
        # Process based on type
        if job_type == "url":
            result = await self._ingest_url(job["data"])
        elif job_type == "pdf":
            result = await self._ingest_pdf(job["data"])
        elif job_type == "search_and_ingest":
            result = await self._search_and_ingest(job["data"])
        else:
            result = {"success": False, "error": "Unknown job type"}
        
        # Final metadata
        if run_tree:
            run_tree.metadata.update({
                "success": result.get("success", False),
                "atoms_created": result.get("atoms_created", 0),
                "chunks_processed": result.get("chunks_processed", 0),
                "gap_resolved": result.get("gap_resolved", False),
            })
        
        return result
    
    @traceable(run_type="tool", name="Ingestion.url", tags=["ingestion", "url"])
    async def _ingest_url(self, job_data: dict):
        """Ingest content from URL"""
        url = job_data.get("url")
        
        run_tree = get_current_run_tree()
        if run_tree:
            run_tree.metadata["url"] = url
            run_tree.metadata["domain"] = url.split("/")[2] if url else None
        
        # ... ingestion logic ...
        
        return {"success": True, "atoms_created": 5}
    
    @traceable(run_type="tool", name="Ingestion.pdf", tags=["ingestion", "pdf"])
    async def _ingest_pdf(self, job_data: dict):
        """Ingest content from PDF"""
        file_path = job_data.get("file_path")
        
        run_tree = get_current_run_tree()
        if run_tree:
            run_tree.metadata["file_name"] = job_data.get("file_name")
        
        # ... PDF processing logic ...
        
        return {"success": True, "atoms_created": 12}
```

### 7. Tracing Telegram Handler

```python
# agent_factory/telegram/telegram_bot.py (add tracing wrapper)
"""Telegram handler with LangSmith tracing"""

from langsmith import traceable
from langsmith.run_helpers import get_current_run_tree
from telegram import Update
from telegram.ext import ContextTypes


@traceable(
    run_type="chain",
    name="Telegram.handle_message",
    tags=["telegram", "user-interaction"]
)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Main message handler with tracing.
    
    Traced data:
    - User ID
    - Message type (text, photo)
    - Query text
    - Response time
    """
    user_id = str(update.effective_user.id)
    message_text = update.message.text or ""
    has_photo = bool(update.message.photo)
    
    # Add trace metadata
    run_tree = get_current_run_tree()
    if run_tree:
        run_tree.metadata.update({
            "user_id": user_id,
            "message_type": "photo" if has_photo else "text",
            "query_length": len(message_text),
            "has_caption": bool(update.message.caption),
            "chat_type": update.effective_chat.type,
        })
        run_tree.tags.append(f"user:{user_id[:8]}")  # Shortened for grouping
    
    # Route to appropriate handler
    if has_photo:
        response = await handle_photo(update, context)
    else:
        response = await process_text_query(update, context)
    
    return response


@traceable(
    run_type="chain",
    name="Telegram.process_query",
    tags=["telegram", "query"]
)
async def process_text_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process text query through orchestrator"""
    user_id = str(update.effective_user.id)
    query = update.message.text
    
    # Check for equipment context
    equipment_context = context.user_data.get("ocr_context")
    
    # Route through orchestrator
    from agent_factory.core.orchestrator import RivetOrchestrator
    orchestrator = RivetOrchestrator(...)
    
    response = await orchestrator.route_query(
        query=query,
        user_id=user_id,
        channel="telegram",
        equipment_context=equipment_context
    )
    
    # Send response
    await update.message.reply_text(response["text"])
    
    # Add final metadata
    run_tree = get_current_run_tree()
    if run_tree:
        run_tree.metadata["route_taken"] = response.get("route")
        run_tree.metadata["response_length"] = len(response.get("text", ""))
    
    return response
```

### 8. Custom Dashboard Configuration

After running traces, configure these dashboards in LangSmith UI:

#### Dashboard 1: Route Distribution

**Purpose:** See how queries are being routed

**Charts:**
1. **Route Distribution (Pie/Bar)**
   - Metric: Run count
   - Group by: metadata.route
   - Filter: name = "RivetOrchestrator.route_query"

2. **Route Distribution Over Time (Line)**
   - Metric: Run count
   - Group by: metadata.route
   - Time: Last 7 days

3. **Confidence Distribution (Histogram)**
   - Metric: metadata.confidence
   - Filter: Is Root = true

#### Dashboard 2: Performance

**Purpose:** Monitor latency and throughput

**Charts:**
1. **P50/P95 Latency by Route**
   - Metric: Latency (P50, P95)
   - Group by: metadata.route
   - Filter: name = "RivetOrchestrator.route_query"

2. **Component Latency Breakdown**
   - Metric: Latency (P50)
   - Filter by name: KB.evaluate_coverage, SME.augment, LLM.fallback

3. **Requests per Minute**
   - Metric: Run count
   - Time granularity: 1 minute
   - Filter: Is Root = true

#### Dashboard 3: Knowledge Gaps

**Purpose:** Track gap detection and resolution

**Charts:**
1. **Gaps Detected Over Time**
   - Metric: Run count
   - Filter: tags contains "gap:detected"

2. **Gap by Equipment Type**
   - Metric: Run count
   - Group by: metadata.gap_equipment
   - Filter: tags contains "gap-detector"

3. **Gap by Manufacturer**
   - Metric: Run count
   - Group by: metadata.gap_manufacturer
   - Filter: tags contains "gap-detector"

4. **Ingestion Jobs Queued**
   - Metric: Run count
   - Filter: metadata.ingestion_job_id exists

#### Dashboard 4: OCR Performance

**Purpose:** Monitor photo analysis

**Charts:**
1. **Photos Processed**
   - Metric: Run count
   - Filter: tags contains "ocr"

2. **Equipment Types Detected**
   - Metric: Run count
   - Group by: metadata.equipment_type
   - Filter: name = "OCR.process_photo"

3. **Manufacturer Distribution**
   - Metric: Run count
   - Group by: metadata.manufacturer
   - Filter: name = "OCR.process_photo"

4. **OCR Confidence Distribution**
   - Metric: metadata.confidence (avg)
   - Time: Last 24 hours

#### Dashboard 5: LLM Costs

**Purpose:** Track token usage and costs

**Charts:**
1. **Tokens by Model**
   - Metric: Sum of metadata.tokens_used
   - Group by: metadata.model

2. **Daily Token Usage**
   - Metric: Sum of metadata.tokens_used
   - Time granularity: 1 day

3. **Prompt vs Completion Tokens**
   - Metric: Sum (prompt_tokens, completion_tokens)
   - Group by: metadata.model

#### Dashboard 6: User Activity

**Purpose:** Understand usage patterns

**Charts:**
1. **Unique Users per Day**
   - Metric: Distinct count of metadata.user_id

2. **Queries per User (Top 10)**
   - Metric: Run count
   - Group by: metadata.user_id
   - Limit: 10

3. **Message Types**
   - Metric: Run count
   - Group by: metadata.message_type
   - Filter: tags contains "telegram"


### 9. End-to-End Test Script

```python
# tests/test_langsmith_e2e.py
"""
End-to-end test for LangSmith tracing integration.
Validates that traces are being captured correctly.

Run with: python tests/test_langsmith_e2e.py
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from langsmith import Client
from agent_factory.config.langsmith_config import init_langsmith


# Test configuration
TEST_PROJECT = "rivetceo-bot-test"
TEST_QUERIES = [
    {
        "query": "How do I reset a Siemens S7-1200 PLC?",
        "expected_tags": ["orchestrator"],
        "expected_metadata": ["route", "confidence"],
    },
    {
        "query": "What is the meaning of life?",  # Should hit Route C
        "expected_tags": ["route:C", "gap-detection"],
        "expected_metadata": ["gap_detected"],
    },
    {
        "query": "EMERGENCY: Safety relay not responding",  # Should hit Route D
        "expected_tags": ["route:D", "escalation"],
        "expected_metadata": ["escalation_reason"],
    },
]


async def test_langsmith_connection():
    """Test 1: Verify LangSmith connection"""
    print("\n" + "="*60)
    print("TEST 1: LangSmith Connection")
    print("="*60)
    
    client = Client()
    
    try:
        # Try to list projects
        projects = list(client.list_projects(limit=5))
        print(f"✅ Connected to LangSmith")
        print(f"   Found {len(projects)} projects")
        
        for p in projects[:3]:
            print(f"   - {p.name}")
        
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


async def test_trace_creation():
    """Test 2: Create a test trace and verify it appears"""
    print("\n" + "="*60)
    print("TEST 2: Trace Creation")
    print("="*60)
    
    from langsmith import traceable
    
    @traceable(
        run_type="chain",
        name="Test.trace_creation",
        tags=["test", "e2e-validation"],
        project_name=TEST_PROJECT
    )
    def test_function(input_text: str) -> str:
        return f"Processed: {input_text}"
    
    # Create trace
    test_input = f"Test input at {datetime.utcnow().isoformat()}"
    result = test_function(test_input)
    
    print(f"   Created trace with input: {test_input[:50]}...")
    
    # Wait for trace to be indexed
    await asyncio.sleep(3)
    
    # Verify trace exists
    client = Client()
    runs = list(client.list_runs(
        project_name=TEST_PROJECT,
        filter='eq(name, "Test.trace_creation")',
        limit=1
    ))
    
    if runs:
        print(f"✅ Trace found in LangSmith")
        print(f"   Run ID: {runs[0].id}")
        print(f"   Latency: {runs[0].total_ms}ms")
        return True
    else:
        print("❌ Trace not found")
        return False


async def test_metadata_and_tags():
    """Test 3: Verify metadata and tags are captured"""
    print("\n" + "="*60)
    print("TEST 3: Metadata and Tags")
    print("="*60)
    
    from langsmith import traceable
    from langsmith.run_helpers import get_current_run_tree
    
    @traceable(
        run_type="chain",
        name="Test.metadata_test",
        tags=["test", "metadata-validation"],
        project_name=TEST_PROJECT
    )
    def test_with_metadata(query: str) -> dict:
        run_tree = get_current_run_tree()
        if run_tree:
            run_tree.metadata.update({
                "test_route": "B",
                "test_confidence": 0.75,
                "test_user_id": "test_user_123",
            })
            run_tree.tags.extend(["route:B", "test-specific-tag"])
        
        return {"result": "success", "query": query}
    
    # Create trace with metadata
    result = test_with_metadata("Test query for metadata")
    
    # Wait for indexing
    await asyncio.sleep(3)
    
    # Verify
    client = Client()
    runs = list(client.list_runs(
        project_name=TEST_PROJECT,
        filter='eq(name, "Test.metadata_test")',
        limit=1
    ))
    
    if runs:
        run = runs[0]
        metadata = run.extra.get("metadata", {}) if run.extra else {}
        tags = run.tags or []
        
        print(f"   Run ID: {run.id}")
        print(f"   Metadata: {metadata}")
        print(f"   Tags: {tags}")
        
        # Validate
        checks = [
            ("route in metadata", "test_route" in metadata),
            ("confidence in metadata", "test_confidence" in metadata),
            ("route tag present", "route:B" in tags),
        ]
        
        all_passed = True
        for name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"   {status} {name}")
            all_passed = all_passed and passed
        
        return all_passed
    else:
        print("❌ Trace not found")
        return False


async def test_nested_traces():
    """Test 4: Verify parent-child trace relationships"""
    print("\n" + "="*60)
    print("TEST 4: Nested Traces")
    print("="*60)
    
    from langsmith import traceable
    
    @traceable(run_type="tool", name="Test.child_operation", project_name=TEST_PROJECT)
    def child_operation(x: int) -> int:
        return x * 2
    
    @traceable(run_type="chain", name="Test.parent_operation", tags=["nested-test"], project_name=TEST_PROJECT)
    def parent_operation(value: int) -> int:
        result1 = child_operation(value)
        result2 = child_operation(result1)
        return result2
    
    # Create nested trace
    result = parent_operation(5)
    print(f"   Result: {result}")
    
    # Wait for indexing
    await asyncio.sleep(3)
    
    # Verify parent
    client = Client()
    parent_runs = list(client.list_runs(
        project_name=TEST_PROJECT,
        filter='eq(name, "Test.parent_operation")',
        limit=1
    ))
    
    if parent_runs:
        parent = parent_runs[0]
        
        # Get children
        child_runs = list(client.list_runs(
            project_name=TEST_PROJECT,
            filter=f'eq(parent_run_id, "{parent.id}")',
        ))
        
        print(f"   Parent ID: {parent.id}")
        print(f"   Children found: {len(child_runs)}")
        
        if len(child_runs) == 2:
            print("✅ Nested traces working correctly")
            return True
        else:
            print(f"❌ Expected 2 children, found {len(child_runs)}")
            return False
    else:
        print("❌ Parent trace not found")
        return False


async def test_orchestrator_integration():
    """Test 5: Test actual orchestrator tracing (mock)"""
    print("\n" + "="*60)
    print("TEST 5: Orchestrator Integration (Mock)")
    print("="*60)
    
    from langsmith import traceable
    from langsmith.run_helpers import get_current_run_tree
    
    # Mock orchestrator methods
    @traceable(run_type="retriever", name="KB.evaluate_coverage", project_name=TEST_PROJECT)
    async def mock_kb_evaluate(query: str) -> dict:
        await asyncio.sleep(0.1)  # Simulate latency
        return {"route": "B", "confidence": 0.75, "coverage_level": "moderate"}
    
    @traceable(run_type="chain", name="SME.augment", tags=["sme-agent"], project_name=TEST_PROJECT)
    async def mock_sme_augment(query: str, vendor: str) -> dict:
        run_tree = get_current_run_tree()
        if run_tree:
            run_tree.tags.append(f"vendor:{vendor}")
            run_tree.metadata["vendor"] = vendor
        await asyncio.sleep(0.2)
        return {"augmentation": "SME response here"}
    
    @traceable(
        run_type="chain",
        name="RivetOrchestrator.route_query",
        tags=["orchestrator", "integration-test"],
        project_name=TEST_PROJECT
    )
    async def mock_route_query(query: str, user_id: str) -> dict:
        run_tree = get_current_run_tree()
        
        # KB evaluation
        kb_decision = await mock_kb_evaluate(query)
        
        # Update trace
        if run_tree:
            run_tree.metadata.update({
                "user_id": user_id,
                "route": kb_decision["route"],
                "confidence": kb_decision["confidence"],
            })
            run_tree.tags.append(f"route:{kb_decision['route']}")
        
        # SME augmentation
        sme_result = await mock_sme_augment(query, "siemens")
        
        return {
            "text": "Response from Route B",
            "route": kb_decision["route"],
            "confidence": kb_decision["confidence"],
        }
    
    # Run mock orchestrator
    response = await mock_route_query(
        query="How do I configure a Siemens VFD?",
        user_id="test_user_456"
    )
    
    print(f"   Response: {response}")
    
    # Wait and verify
    await asyncio.sleep(3)
    
    client = Client()
    runs = list(client.list_runs(
        project_name=TEST_PROJECT,
        filter='and(eq(name, "RivetOrchestrator.route_query"), has(tags, "integration-test"))',
        limit=1
    ))
    
    if runs:
        run = runs[0]
        metadata = run.extra.get("metadata", {}) if run.extra else {}
        
        print(f"   Run ID: {run.id}")
        print(f"   Route: {metadata.get('route')}")
        print(f"   Confidence: {metadata.get('confidence')}")
        print(f"   Children: {run.child_run_count}")
        
        if run.child_run_count >= 2:
            print("✅ Orchestrator tracing working")
            return True
        else:
            print("❌ Missing child traces")
            return False
    else:
        print("❌ Orchestrator trace not found")
        return False


async def verify_dashboard_data():
    """Test 6: Verify data is queryable for dashboards"""
    print("\n" + "="*60)
    print("TEST 6: Dashboard Data Availability")
    print("="*60)
    
    client = Client()
    
    # Query runs from last hour
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    
    runs = list(client.list_runs(
        project_name=TEST_PROJECT,
        start_time=one_hour_ago,
    ))
    
    print(f"   Runs in last hour: {len(runs)}")
    
    if not runs:
        print("⚠️  No runs found - run other tests first")
        return True  # Not a failure, just no data
    
    # Check for route distribution
    routes = {}
    for run in runs:
        if run.extra and run.extra.get("metadata"):
            route = run.extra["metadata"].get("route")
            if route:
                routes[route] = routes.get(route, 0) + 1
    
    print(f"   Route distribution: {routes}")
    
    # Check for tag distribution
    all_tags = []
    for run in runs:
        all_tags.extend(run.tags or [])
    
    unique_tags = list(set(all_tags))
    print(f"   Unique tags: {len(unique_tags)}")
    print(f"   Sample tags: {unique_tags[:5]}")
    
    print("✅ Dashboard data is queryable")
    return True


async def run_all_tests():
    """Run all E2E tests"""
    print("\n" + "="*60)
    print("🧪 LANGSMITH INTEGRATION E2E TESTS")
    print("="*60)
    
    # Check environment
    if not os.getenv("LANGCHAIN_API_KEY"):
        print("❌ LANGCHAIN_API_KEY not set!")
        print("   Set it with: export LANGCHAIN_API_KEY=your_key")
        return
    
    # Initialize
    init_langsmith()
    os.environ["LANGCHAIN_PROJECT"] = TEST_PROJECT
    
    print(f"\nUsing project: {TEST_PROJECT}")
    print(f"API Key: {os.getenv('LANGCHAIN_API_KEY')[:10]}...")
    
    results = []
    
    # Run tests
    tests = [
        ("Connection", test_langsmith_connection),
        ("Trace Creation", test_trace_creation),
        ("Metadata & Tags", test_metadata_and_tags),
        ("Nested Traces", test_nested_traces),
        ("Orchestrator Integration", test_orchestrator_integration),
        ("Dashboard Data", verify_dashboard_data),
    ]
    
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {name}")
    
    print(f"\n   {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED")
        print(f"\n📊 View your traces at:")
        print(f"   https://smith.langchain.com/o/default/projects/p/{TEST_PROJECT}")
    else:
        print("\n⚠️  Some tests failed - check output above")


def main():
    asyncio.run(run_all_tests())


if __name__ == "__main__":
    main()
```

### 10. Quick Start Commands

```bash
# 1. Set environment
export LANGCHAIN_API_KEY=your_key_here
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_PROJECT=rivetceo-bot

# 2. Run E2E tests
python tests/test_langsmith_e2e.py

# 3. Check LangSmith UI
# https://smith.langchain.com/o/default/projects

# 4. Run bot with tracing
python -m agent_factory.telegram.telegram_bot

# 5. Send test queries via Telegram and watch traces appear
```

## Deliverables

1. `agent_factory/config/langsmith_config.py` - Configuration
2. Updated `orchestrator.py` with `@traceable` decorators
3. Updated `sme_agent.py` with tracing
4. Updated `ocr/pipeline.py` with tracing
5. Updated `worker/ingestion_worker.py` with tracing
6. Updated `telegram_bot.py` with tracing wrapper
7. `tests/test_langsmith_e2e.py` - E2E validation
8. Dashboard configurations (manual in LangSmith UI)

## Testing Checklist

- [ ] `LANGCHAIN_API_KEY` set
- [ ] Connection test passes
- [ ] Traces appear in LangSmith UI
- [ ] Metadata is captured correctly
- [ ] Tags are captured correctly
- [ ] Nested traces show parent-child relationships
- [ ] Route distribution visible in UI
- [ ] Can filter by route, confidence, user
- [ ] Latency metrics available
- [ ] Token usage tracked

## Dashboard Setup Steps (Manual in LangSmith UI)

1. Go to https://smith.langchain.com
2. Navigate to Monitor → Dashboards
3. Create new dashboard: "RivetCEO - Route Distribution"
4. Add charts as specified in section 8
5. Repeat for other dashboards
6. Set up alerts for:
   - Error rate > 5%
   - P95 latency > 5s
   - Gap detection spike

## Next Steps After Validation

1. Add feedback collection (thumbs up/down from users)
2. Set up automations for:
   - Positive feedback → Add to training dataset
   - Errors → Add to annotation queue
3. Create weekly performance reports
4. Set up alerts for anomalies
