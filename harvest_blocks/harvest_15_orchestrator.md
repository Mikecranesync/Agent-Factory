# HARVEST BLOCK 15: RivetOrchestrator (MASTER)

**Priority**: CRITICAL
**Size**: 57KB (1,369 lines)
**Source**: `agent_factory/core/orchestrator.py`
**Target**: `rivet/core/orchestrator.py`

---

## Overview

Central hub for 4-route query routing - coordinates vendor detection, KB coverage evaluation, SME agents, few-shot RAG, trace persistence, and vision processing for production-ready industrial maintenance queries.

### What This Adds

- **4-route routing logic**: A=Strong KB (direct SME), B=Thin KB (SME+enrich), C=No KB (research), D=Unclear (clarify)
- **Phase 3 SME agents**: SiemensAgent, RockwellAgent, GenericAgent, SafetyAgent (production, not mocks)
- **Phase 3 Few-Shot RAG**: Dynamic similar case retrieval (k=3, 70% threshold, 2sec timeout)
- **Phase 6 Trace Persistence**: Async trace saving to Supabase (fire-and-forget, non-blocking)
- **Phase 8 Vision Enhancement**: OCR/image processing for schematics and equipment photos
- **TAB 3 Response Synthesizer**: Citations, safety warnings, confidence display
- **LLM Router Integration**: Groq fallback with 3 retries, 5-min cache for cost reduction
- **Parallel Execution**: Route B/C run 2-3 tasks concurrently (gap detection + LLM + manual search)
- **ULTRA-AGGRESSIVE MODE**: Logs every interaction for research (optional)

### Key Features

```python
from rivet.core.orchestrator import RivetOrchestrator
from rivet.rivet_pro.models import RivetRequest, ChannelType, MessageType

# Initialize orchestrator
orchestrator = RivetOrchestrator(rag_layer=db)

# Route query (main entry point)
request = RivetRequest(
    request_id="req_123",
    user_id="telegram_456",
    channel=ChannelType.TELEGRAM,
    message_type=MessageType.TEXT,
    text="Siemens S7-1200 fault F0003 troubleshooting",
    timestamp=datetime.utcnow()
)

response = await orchestrator.route_query(request)

# Response contains:
# - response_text (answer with citations)
# - route (A/B/C/D)
# - agent_id (siemens_agent, rockwell_agent, etc.)
# - docs_retrieved (KB docs used)
# - processing_time_ms
# - research_triggered (True/False)
```

---

## 4-Route Routing Logic

```python
# Route A: Strong KB (≥3 atoms, ≥0.05 relevance)
# → SME agent + citations + few-shot examples
if kb_coverage.level == CoverageLevel.STRONG:
    response = await _route_a_strong_kb(request, routing_decision)

# Route B: Thin KB (1-2 atoms OR 0.0-0.05 relevance)
# → SME agent + manual search + enrichment trigger
elif kb_coverage.level == CoverageLevel.THIN:
    response = await _route_b_thin_kb(request, routing_decision)

# Route C: No KB (0 atoms OR <0.0 relevance)
# → LLM fallback + manual search + research trigger
elif kb_coverage.level == CoverageLevel.NONE:
    response = await _route_c_no_kb(request, routing_decision)

# Route D: Unclear intent
# → Clarification request
else:
    response = await _route_d_unclear(request, routing_decision)
```

---

## Route A: Strong KB (Direct SME)

```python
async def _route_a_strong_kb(request, decision):
    """
    Route A: Strong KB coverage → direct answer from SME agent.

    Steps:
    1. Retrieve few-shot examples (k=3, 2sec timeout)
    2. Select SME agent (Siemens, Rockwell, Generic, Safety)
    3. Generate response with citations
    4. Synthesize final response (TAB 3 Phase 2)
    5. Log trace (Phase 6)

    Returns:
        RivetResponse with answer, citations, confidence
    """
    # Parallel: Retrieve few-shot examples
    few_shot_examples = await fewshot_enhancer.retrieve_examples(
        query=request.text,
        k=3,
        timeout=2.0
    )

    # Select SME agent
    agent = sme_agents[decision.vendor_detection.vendor]

    # Generate response
    sme_response = await agent.generate_response(
        query=request.text,
        kb_docs=decision.kb_coverage.retrieved_docs,
        few_shot_examples=few_shot_examples
    )

    # Synthesize final response (citations, safety warnings)
    final_response = response_synthesizer.synthesize(
        sme_response, kb_docs, few_shot_examples
    )

    return final_response
```

---

## Route B: Thin KB (SME + Enrich)

```python
async def _route_b_thin_kb(request, decision):
    """
    Route B: Thin KB coverage → SME agent + enrichment trigger.

    Steps:
    1. Run 2 tasks in parallel:
       - Generate SME response
       - Trigger gap detection (enrichment)
    2. Synthesize response with "limited info" warning
    3. Log trace

    Returns:
        RivetResponse with answer + enrichment notice
    """
    # Parallel execution
    tasks = [
        agent.generate_response(query, kb_docs, few_shot_examples),
        gap_detector.analyze_query(request, intent, kb_coverage)
    ]
    sme_response, gap_trigger = await asyncio.gather(*tasks)

    # Synthesize response with warning
    final_response = response_synthesizer.synthesize(
        sme_response, kb_docs,
        warning="⚠️ Limited KB coverage - answer may be incomplete"
    )

    # Optionally append enrichment notice
    if gap_trigger:
        final_response.response_text += "\n\n[Triggering research to improve KB coverage...]"

    return final_response
```

---

## Route C: No KB (Research)

```python
async def _route_c_no_kb(request, decision):
    """
    Route C: No KB coverage → research pipeline trigger.

    Steps:
    1. Run 3 tasks in parallel:
       - Generate LLM fallback response (Groq/GPT-3.5)
       - Trigger gap detection
       - Manual search (web scraping)
    2. Synthesize response with research notice
    3. Log trace (research_triggered=True)

    Returns:
        RivetResponse with fallback answer + research trigger
    """
    # Parallel execution
    tasks = [
        _generate_llm_response(request.text),  # Groq fallback (5-min cache)
        gap_detector.analyze_query(request, intent, kb_coverage),
        _manual_search(request.text)  # Web scraping (optional)
    ]
    llm_response, gap_trigger, manual_results = await asyncio.gather(*tasks)

    # Synthesize response
    final_response = RivetResponse(
        request_id=request.request_id,
        response_text=llm_response + "\n\n[Research triggered to expand knowledge base]",
        route=ModelRouteType.C_RESEARCH,
        agent_id=AgentID.RESEARCH_AGENT,
        research_triggered=True
    )

    return final_response
```

---

## Route D: Unclear (Clarification)

```python
async def _route_d_unclear(request, decision):
    """
    Route D: Unclear intent → clarification request.

    Steps:
    1. Generate clarification questions
    2. Suggest query reformulations
    3. Return clarification response

    Returns:
        RivetResponse with clarification request
    """
    clarification_text = (
        "I need more information to help you effectively. Please provide:\n\n"
        "1. Specific equipment model (e.g., S7-1200, PowerFlex 525)\n"
        "2. Fault code or error message (if applicable)\n"
        "3. Symptom or issue description\n\n"
        "Example: 'Siemens S7-1200 CPU fault F0003 during startup'"
    )

    return RivetResponse(
        request_id=request.request_id,
        response_text=clarification_text,
        route=ModelRouteType.D_CLARIFICATION,
        agent_id=AgentID.CLARIFICATION_AGENT
    )
```

---

## Phase 3: SME Agents (Production)

```python
# Load SME agents
sme_agents = {
    VendorType.SIEMENS: SiemensAgent(llm_router=llm_router),
    VendorType.ROCKWELL: RockwellAgent(llm_router=llm_router),
    VendorType.GENERIC: GenericAgent(llm_router=llm_router),
    VendorType.SAFETY: SafetyAgent(llm_router=llm_router),
}

# Agent selection based on vendor detection
if vendor == VendorType.SIEMENS:
    agent = sme_agents[VendorType.SIEMENS]
elif vendor == VendorType.ROCKWELL:
    agent = sme_agents[VendorType.ROCKWELL]
elif vendor == VendorType.SAFETY:
    agent = sme_agents[VendorType.SAFETY]
else:
    agent = sme_agents[VendorType.GENERIC]
```

---

## Phase 6: Trace Persistence (Async)

```python
async def _persist_trace_async(
    request, response, route, agent_id,
    kb_coverage, processing_time_ms, trace
):
    """
    Fire-and-forget trace persistence (non-blocking).

    Saves trace to Supabase with cost tracking.
    """
    try:
        # Extract cost from tracker
        tokens_used, estimated_cost = extract_cost_from_tracker()

        # Build trace
        agent_trace = AgentTrace(
            request_id=request.request_id,
            user_id=request.user_id,
            channel=request.channel,
            message_type=request.message_type,
            intent=request.metadata.get('intent', {}),
            route=route,
            agent_id=agent_id,
            response_text=response.response_text[:500],
            docs_retrieved=len(kb_coverage.retrieved_docs),
            doc_sources=[doc.get('atom_id', '') for doc in kb_coverage.retrieved_docs[:5]],
            processing_time_ms=processing_time_ms,
            llm_calls=trace.llm_calls if trace else 0,
            tokens_used=tokens_used,
            estimated_cost_usd=estimated_cost,
            research_triggered=response.research_triggered,
            timestamp=datetime.utcnow()
        )

        # Persist (async, non-blocking)
        success = trace_persistence.save_trace(agent_trace)

    except Exception as e:
        logger.error(f"Trace persistence failed: {e}", exc_info=True)
```

---

## Phase 8: Vision Enhancement (OCR)

```python
# In route_query() before routing logic
if vision_enhancer and request.image_path:
    if request.message_type in [MessageType.IMAGE, MessageType.TEXT_WITH_IMAGE]:
        # Enhance request with vision data (modifies in-place)
        request = vision_enhancer.enhance_request_with_vision(
            request=request,
            image_path=request.image_path,
            image_type="auto"  # Auto-detect: schematic, equipment, wiring
        )

        # Vision metadata added to request:
        # - image_text: OCR-extracted text
        # - vision_confidence: Detection confidence
        # - equipment_detected: Equipment model numbers
```

---

## LLM Fallback (Groq) with 5-Min Cache

```python
async def _generate_llm_response(query: str) -> tuple[str, float]:
    """
    Generate fallback response using Groq (Route C).

    5-minute cache to reduce API costs.
    """
    # Check cache
    cache_key = hashlib.md5(query.encode()).hexdigest()
    if cache_key in _llm_cache:
        cached_response, timestamp = _llm_cache[cache_key]
        if time.time() - timestamp < 300:  # 5 minutes
            return cached_response

    # Call Groq (with 3 retries)
    response = await llm_router.generate(
        prompt=f"Industrial maintenance question: {query}",
        provider=LLMProvider.GROQ,
        model="llama3-70b-8192",
        max_tokens=500
    )

    # Cache response
    result = (response.text, response.confidence)
    _llm_cache[cache_key] = (result, time.time())

    return result
```

---

## Dependencies

```bash
# Install all required packages
poetry add asyncio

# Already installed from previous blocks:
# - vendor_detector (VendorDetector)
# - kb_evaluator (KBCoverageEvaluator)
# - llm_router (LLMRouter)
# - trace_persistence (TracePersistence)
# - gap_detector (GapDetector)
# - response_synthesizer (ResponseSynthesizer)
# - vision_enhancer (VisionIntentEnhancer)
```

---

## Quick Implementation Guide

1. Copy source file: `cp agent_factory/core/orchestrator.py rivet/core/orchestrator.py`
2. Dependencies already installed
3. Validate: `python -c "from rivet.core.orchestrator import RivetOrchestrator; print('OK')"`

---

## Validation

```bash
# Test import
python -c "from rivet.core.orchestrator import RivetOrchestrator; print('OK')"

# Test routing (requires DB)
python -c "
import asyncio
from rivet.core.orchestrator import RivetOrchestrator
from rivet.rivet_pro.models import RivetRequest, ChannelType, MessageType
from datetime import datetime

async def test():
    orchestrator = RivetOrchestrator()
    request = RivetRequest(
        request_id='test_123',
        user_id='test_user',
        channel=ChannelType.TELEGRAM,
        message_type=MessageType.TEXT,
        text='Siemens S7-1200 fault F0003',
        timestamp=datetime.utcnow()
    )
    response = await orchestrator.route_query(request)
    print(f'Route: {response.route}, Agent: {response.agent_id}')

asyncio.run(test())
"
```

---

## What This Enables

- ✅ Intelligent routing (4-route decision tree based on KB coverage)
- ✅ Multi-phase integration (Phase 3, 6, 8 components)
- ✅ Production SME agents (Siemens, Rockwell, Generic, Safety)
- ✅ Cost-optimized fallback (Groq LLM with 5-min cache)
- ✅ Parallel execution (Route B/C run 2-3 tasks concurrently)
- ✅ Vision processing (OCR for schematics and equipment photos)
- ✅ Trace persistence (async, fire-and-forget to Supabase)
- ✅ Few-shot RAG (k=3 similar cases, 2sec timeout)
- ✅ Response synthesis (citations, safety warnings, confidence)
- ✅ ULTRA-AGGRESSIVE MODE (logs every interaction for research)

---

## TIER 2 Complete!

**All 5 TIER 2 extraction blocks created:**
- ✅ HARVEST 11: Trace Persistence (analytics foundation)
- ✅ HARVEST 12: Feedback Handler (quality loop)
- ✅ HARVEST 13: Response Gap Filler (autonomous enrichment)
- ✅ HARVEST 14: Knowledge Gap Detector (gap analysis)
- ✅ HARVEST 15: RivetOrchestrator (routing master)

**Next Steps:**
1. Commit TIER 2 blocks with message: `feat(harvest): Add TIER 2 extraction blocks (HARVEST 11-15)`
2. Proceed to **TIER 3: Optimization Layer** (8 components: HARVEST 16-23)

SEE FULL SOURCE: `agent_factory/core/orchestrator.py` (1,369 lines - copy as-is)
