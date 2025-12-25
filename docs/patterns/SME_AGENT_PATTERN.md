# SME Agent Pattern

**Pattern Type**: Agent Template
**Status**: Production
**Created**: 2025-12-21
**Use Case**: Building specialized Subject Matter Expert agents for RIVET Pro

---

## Overview

The SME (Subject Matter Expert) Agent Pattern provides a standardized template for building domain-specific question-answering agents. All RIVET SME agents inherit from `SMEAgentTemplate` to ensure consistent behavior, error handling, and observability.

## Problem Solved

Without a template:
- ❌ Each agent implements same boilerplate (query analysis, KB search, answer generation)
- ❌ Inconsistent error handling across agents
- ❌ No standard confidence scoring or escalation logic
- ❌ Hard to add observability/logging to all agents

With template:
- ✅ Reusable structure - focus on domain logic, not boilerplate
- ✅ Consistent error handling and escalation
- ✅ Built-in logging, tracing, confidence scoring
- ✅ Easy to add new SME agents (50 lines vs 200 lines)

## Architecture

```
User Query
    ↓
SMEAgentTemplate.answer()
    ├── 1. analyze_query()     ← Subclass implements domain-specific parsing
    ├── 2. search_kb()          ← Subclass implements KB search with filters
    ├── 3. generate_answer()    ← Subclass implements answer generation
    ├── 4. score_confidence()   ← Subclass implements confidence scoring
    └── 5. Escalate if low confidence
    ↓
SMEAnswer (answer, confidence, sources, escalate)
```

## Template Structure

### Data Classes

**QueryAnalysis**:
- `domain`: Subject domain (e.g., "motor_control")
- `question_type`: Type of question (e.g., "troubleshooting", "how_to")
- `key_entities`: Extracted entities (e.g., ["motor", "overheat"])
- `search_keywords`: Keywords for KB search
- `complexity`: Estimated complexity (simple/moderate/complex)

**SMEAnswer**:
- `answer_text`: Generated answer
- `confidence`: Score 0.0-1.0
- `sources`: List of source document IDs
- `reasoning`: How answer was derived
- `follow_up_questions`: Suggested next questions
- `escalate`: Whether to escalate to human
- `metadata`: Additional data (latency, analysis, etc.)

### Abstract Methods (Must Implement)

1. **`analyze_query(query: str) -> QueryAnalysis`**
   - Parse user question
   - Extract domain, entities, keywords
   - Classify question type

2. **`search_kb(analysis: QueryAnalysis) -> List[Dict]`**
   - Search knowledge base using analysis
   - Apply domain-specific filters
   - Return top-k relevant documents

3. **`generate_answer(query: str, docs: List[Dict]) -> str`**
   - Generate answer from retrieved documents
   - Use domain expertise to craft response
   - Include citations/examples

4. **`score_confidence(query: str, answer: str, docs: List[Dict]) -> float`**
   - Assess answer confidence (0.0-1.0)
   - Check document relevance, coverage, clarity
   - Return score for escalation decision

### Built-In Methods (Template Provides)

1. **`answer(query: str) -> SMEAnswer`**
   - Main entry point
   - Orchestrates full pipeline
   - Handles errors, logging, escalation

2. **`_generate_follow_ups(query: str, analysis: QueryAnalysis) -> List[str]`**
   - Generate follow-up questions
   - Default implementation (can override)

## Implementation Guide

### Step 1: Create SME Agent Class

```python
from agent_factory.templates import SMEAgentTemplate
from agent_factory.templates.sme_agent_template import QueryAnalysis, SMEAnswer

class MotorControlSME(SMEAgentTemplate):
    def __init__(self):
        super().__init__(
            name="Motor Control SME",
            domain="motor_control",
            min_confidence=0.7,  # Escalate if < 0.7
            max_docs=10          # Retrieve up to 10 docs
        )
```

### Step 2: Implement Query Analysis

```python
def analyze_query(self, query: str) -> QueryAnalysis:
    """Parse motor-specific queries"""
    # Use LLM or keyword matching to extract intent
    # Example: "Why is my motor overheating?"

    keywords = extract_keywords(query)  # ["motor", "overheating"]
    entities = extract_entities(query)   # ["motor"]

    # Classify question type
    if "why" in query.lower() or "fault" in query.lower():
        question_type = "troubleshooting"
    elif "how" in query.lower():
        question_type = "how_to"
    else:
        question_type = "concept"

    return QueryAnalysis(
        domain="motor_control",
        question_type=question_type,
        key_entities=entities,
        search_keywords=keywords,
        complexity="moderate"
    )
```

### Step 3: Implement KB Search

```python
def search_kb(self, analysis: QueryAnalysis) -> List[Dict]:
    """Search for motor-related documents"""
    from agent_factory.rivet_pro.rag import search_docs, rerank_search_results
    from agent_factory.rivet_pro.models import RivetIntent, VendorType

    # Build intent from analysis
    intent = RivetIntent(
        vendor=VendorType.ROCKWELL,  # Or extract from query
        equipment_type="motor",
        symptom=" ".join(analysis.search_keywords),
        raw_summary=analysis.search_keywords[0] if analysis.search_keywords else "",
        context_source="text_only",
        confidence=0.9,
        kb_coverage="strong"
    )

    # Search and rerank
    docs = search_docs(intent)
    reranked = rerank_search_results(
        query=" ".join(analysis.search_keywords),
        docs=docs,
        top_k=self.max_docs
    )

    # Convert to dict format
    return [
        {
            "atom_id": doc.atom_id,
            "title": doc.title,
            "content": doc.content,
            "similarity": doc.similarity
        }
        for doc in reranked
    ]
```

### Step 4: Implement Answer Generation

```python
def generate_answer(self, query: str, docs: List[Dict]) -> str:
    """Generate motor-specific answer"""
    from agent_factory.llm import LLMRouter, LLMConfig, LLMProvider

    # Build context from documents
    context = "\n\n".join([
        f"Document {i+1} ({doc['title']}):\n{doc['content'][:500]}"
        for i, doc in enumerate(docs[:3])  # Top 3 docs
    ])

    # Generate answer using LLM
    router = LLMRouter()
    config = LLMConfig(
        provider=LLMProvider.OPENAI,
        model="gpt-4o-mini",
        temperature=0.3  # Lower for factual answers
    )

    prompt = f"""You are a motor control expert. Answer the user's question based ONLY on the provided documents.

Documents:
{context}

User Question: {query}

Answer (be specific, cite document numbers):"""

    messages = [{"role": "user", "content": prompt}]
    response = router.complete(messages, config)

    return response.content
```

### Step 5: Implement Confidence Scoring

```python
def score_confidence(self, query: str, answer: str, docs: List[Dict]) -> float:
    """Score answer confidence"""
    # Factor 1: Document relevance (avg similarity)
    avg_similarity = sum(doc["similarity"] for doc in docs) / len(docs) if docs else 0.0

    # Factor 2: Answer length (too short = low confidence)
    length_score = min(len(answer) / 200, 1.0)  # 200+ chars = 1.0

    # Factor 3: Document coverage (did we find enough?)
    coverage_score = min(len(docs) / 3, 1.0)  # 3+ docs = 1.0

    # Weighted combination
    confidence = (
        avg_similarity * 0.5 +
        length_score * 0.3 +
        coverage_score * 0.2
    )

    return min(confidence, 1.0)
```

### Step 6: Use the Agent

```python
# Create agent
sme = MotorControlSME()

# Answer question
result = sme.answer("Why is my ControlLogix motor overheating?")

print(f"Answer: {result.answer_text}")
print(f"Confidence: {result.confidence:.2f}")
print(f"Sources: {result.sources}")
print(f"Escalate: {result.escalate}")

if result.escalate:
    print("LOW CONFIDENCE - Escalating to human expert")
```

## Best Practices

### 1. Domain-Specific Analysis
- Use domain knowledge to extract entities (vendor, equipment, fault codes)
- Classify questions accurately (troubleshooting vs how-to vs concept)
- Extract search keywords that match KB terminology

### 2. Reranking for Quality
- Always use `rerank_search_results()` after initial retrieval
- Cross-encoder scores are more accurate than pure keyword match
- Example: "motor fails" ranks higher than "drive malfunction" for motor queries

### 3. Confidence Scoring
- Combine multiple factors: document relevance, answer length, coverage
- Set domain-appropriate thresholds (0.7 for high-stakes, 0.5 for exploratory)
- Log confidence scores for analysis

### 4. Escalation Strategy
- Escalate if confidence < threshold
- Escalate if no documents found
- Escalate on errors (don't hide failures)

### 5. Observability
- Template includes logging by default
- Add domain-specific metrics to `metadata`
- Track latency, doc count, escalation rate

## Example Agents

### Motor Control SME
- **Domain**: `motor_control`
- **Question Types**: Troubleshooting (faults, vibration), How-to (wiring, setup)
- **KB Coverage**: 500+ motor-related atoms
- **Confidence Threshold**: 0.7 (high-stakes - motor failures can be dangerous)

### PLC Programming SME
- **Domain**: `plc_programming`
- **Question Types**: How-to (ladder logic), Concept (scan cycle, tags)
- **KB Coverage**: 300+ PLC programming atoms
- **Confidence Threshold**: 0.6 (educational context)

### Networking SME
- **Domain**: `industrial_networking`
- **Question Types**: Troubleshooting (EtherNet/IP, Profinet), Configuration
- **KB Coverage**: 200+ networking atoms
- **Confidence Threshold**: 0.7 (network issues affect entire systems)

## Performance Metrics

### Latency Targets
- Query analysis: <100ms
- KB search + reranking: <500ms
- Answer generation (LLM): <2000ms
- **Total**: <2.5 seconds (median), <5 seconds (p95)

### Quality Metrics
- **Accuracy**: >85% (answers match ground truth)
- **Coverage**: >90% (can answer questions in domain)
- **Escalation Rate**: 10-20% (not too high, not too low)

## Testing

```python
def test_motor_sme():
    sme = MotorControlSME()

    # Test 1: Troubleshooting question
    result = sme.answer("Why does my motor vibrate excessively?")
    assert result.confidence > 0.7
    assert len(result.sources) > 0
    assert not result.escalate

    # Test 2: Out-of-domain question (should escalate)
    result = sme.answer("How do I configure a firewall?")
    assert result.escalate  # Not motor-related

    # Test 3: Check latency
    import time
    start = time.time()
    result = sme.answer("Motor overheating troubleshooting")
    latency = time.time() - start
    assert latency < 5.0  # p95 target
```

## Migration Path

### Before (No Template)
Each agent had 200+ lines of boilerplate:
- ❌ Duplicate error handling
- ❌ Inconsistent confidence scoring
- ❌ Manual escalation logic
- ❌ Hard to add tracing

### After (With Template)
Agents are 50 lines of domain logic:
- ✅ Inherit error handling, logging, escalation
- ✅ Consistent across all SME agents
- ✅ Easy to add new agents (copy pattern)
- ✅ Built-in observability

## See Also

- **`agent_factory/templates/sme_agent_template.py`** - Template source
- **`examples/sme_agent_example.py`** - Example implementation
- **`agent_factory/rivet_pro/agents/motor_control_sme.py`** - Production SME
- **`docs/REFACTOR_PLAN.md`** - Steps 7-9 (SME agent implementation)
