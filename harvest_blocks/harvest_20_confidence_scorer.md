# HARVEST BLOCK 20: Confidence Scorer

**Priority**: MEDIUM
**Size**: 18.88KB (520 lines)
**Source**: `agent_factory/rivet_pro/confidence_scorer.py`
**Target**: `rivet/rivet_pro/confidence_scorer.py`

---

## Overview

Multi-dimensional response confidence scoring - evaluates AI-generated responses for quality, hallucination risk, and reliability to power human-in-the-loop escalation decisions.

### What This Adds

- **Multi-dimensional scoring**: 5 dimensions (relevance, completeness, accuracy, safety, clarity)
- **Hallucination detection**: Checks citations, verifies against KB, detects unsupported claims
- **Safety analysis**: Identifies safety-critical advice, warns about dangerous procedures
- **Weighted scoring**: Customizable weights per dimension (default: accuracy 30%, relevance 25%, completeness 20%, safety 15%, clarity 10%)
- **Threshold-based escalation**: Auto-escalate to human if confidence <0.7
- **Detailed feedback**: Per-dimension scores with explanations

### Key Features

```python
from rivet.rivet_pro.confidence_scorer import ConfidenceScorer

# Initialize scorer
scorer = ConfidenceScorer(
    weights={
        "relevance": 0.25,
        "completeness": 0.20,
        "accuracy": 0.30,
        "safety": 0.15,
        "clarity": 0.10
    },
    escalation_threshold=0.7  # Escalate if confidence <0.7
)

# Score response
result = scorer.score(
    query="How to reset Siemens S7-1200 fault F0003?",
    response="Check communication cable, verify IP address...",
    kb_docs=[doc1, doc2, doc3],  # KB docs used for response
    citations=["Manual: S7-1200 Troubleshooting p.45"]
)

# Result contains:
print(result.overall_confidence)  # 0.85
print(result.should_escalate)  # False (0.85 >= 0.7)
print(result.scores)  # {"relevance": 0.9, "completeness": 0.8, ...}
print(result.feedback)  # {"relevance": "Response directly addresses...", ...}
print(result.warnings)  # ["Recommendation may void warranty"]
```

---

## 5-Dimension Scoring

```python
# Dimension definitions

1. RELEVANCE (25%): Does response address the query?
   - High: Direct answer to exact question
   - Medium: Related but tangential
   - Low: Off-topic or generic

2. COMPLETENESS (20%): Are all aspects covered?
   - High: All troubleshooting steps included
   - Medium: Partial answer, missing some steps
   - Low: Incomplete or vague

3. ACCURACY (30%): Is information correct?
   - High: Verified against KB docs, citations present
   - Medium: Plausible but unverified
   - Low: Contradicts KB or lacks evidence

4. SAFETY (15%): Are safety concerns addressed?
   - High: Safety warnings present, lockout/tagout mentioned
   - Medium: Basic safety mentioned
   - Low: No safety considerations or dangerous advice

5. CLARITY (10%): Is response clear and actionable?
   - High: Step-by-step, specific instructions
   - Medium: General guidance
   - Low: Vague or confusing
```

---

## Hallucination Detection

```python
def detect_hallucinations(response, kb_docs, citations):
    """
    Detect potential hallucinations by checking:
    1. Citation validity (are citations real?)
    2. KB alignment (does response match KB docs?)
    3. Unsupported claims (specific facts without sources)
    """
    hallucination_score = 0.0

    # Check citations
    if citations:
        for citation in citations:
            if not verify_citation_exists(citation, kb_docs):
                hallucination_score += 0.2  # Fake citation

    # Check KB alignment
    response_claims = extract_claims(response)
    for claim in response_claims:
        if not supported_by_kb(claim, kb_docs):
            hallucination_score += 0.1  # Unsupported claim

    # Penalty for hallucinations
    accuracy_penalty = min(hallucination_score, 0.5)
    return 1.0 - accuracy_penalty
```

---

## Safety Analysis

```python
# Safety keyword detection
SAFETY_KEYWORDS = [
    "lockout", "tagout", "loto", "safety", "hazard",
    "electrical shock", "arc flash", "emergency stop",
    "ppe", "personal protective equipment"
]

DANGEROUS_KEYWORDS = [
    "bypass safety", "disable interlock", "ignore warning",
    "work live", "energized", "hot work"
]

def analyze_safety(response):
    """
    Analyze response for safety considerations.

    Returns:
        safety_score (0.0-1.0): Higher if safety addressed
        warnings (list): Safety warnings to display
    """
    safety_score = 0.5  # Default neutral

    # Positive: Safety keywords mentioned
    if any(kw in response.lower() for kw in SAFETY_KEYWORDS):
        safety_score += 0.3

    # Negative: Dangerous advice
    if any(kw in response.lower() for kw in DANGEROUS_KEYWORDS):
        safety_score -= 0.5
        warnings.append("⚠️ DANGEROUS: Response suggests unsafe practice")

    return max(0.0, min(1.0, safety_score)), warnings
```

---

## Weighted Scoring

```python
# Calculate overall confidence
def calculate_overall_confidence(scores, weights):
    """
    Weighted average of dimension scores.

    Default weights:
    - accuracy: 30% (most important)
    - relevance: 25%
    - completeness: 20%
    - safety: 15%
    - clarity: 10%
    """
    total = 0.0
    for dimension, score in scores.items():
        weight = weights.get(dimension, 0.0)
        total += score * weight

    return total  # 0.0-1.0

# Example:
scores = {
    "relevance": 0.9,
    "completeness": 0.8,
    "accuracy": 0.85,
    "safety": 0.7,
    "clarity": 0.9
}
overall = calculate_overall_confidence(scores, weights)
# = (0.9*0.25 + 0.8*0.20 + 0.85*0.30 + 0.7*0.15 + 0.9*0.10)
# = 0.225 + 0.16 + 0.255 + 0.105 + 0.09
# = 0.835
```

---

## Escalation Logic

```python
# Threshold-based escalation
if overall_confidence < 0.7:
    escalate_to_human = True
    reason = "Low confidence response"

# Safety-based escalation
if safety_score < 0.5:
    escalate_to_human = True
    reason = "Safety concerns detected"

# Hallucination-based escalation
if accuracy_score < 0.6:
    escalate_to_human = True
    reason = "Potential hallucinations detected"
```

---

## Dependencies

```bash
# No additional dependencies (stdlib only)
```

---

## Quick Implementation Guide

1. Copy source file: `cp agent_factory/rivet_pro/confidence_scorer.py rivet/rivet_pro/confidence_scorer.py`
2. No dependencies needed (stdlib only)
3. Validate: `python -c "from rivet.rivet_pro.confidence_scorer import ConfidenceScorer; print('OK')"`

---

## Validation

```bash
# Test import
python -c "from rivet.rivet_pro.confidence_scorer import ConfidenceScorer; print('OK')"

# Test scoring
python -c "
from rivet.rivet_pro.confidence_scorer import ConfidenceScorer

scorer = ConfidenceScorer()
result = scorer.score(
    query='Test query',
    response='Test response',
    kb_docs=[],
    citations=[]
)
print(f'Confidence: {result.overall_confidence:.2f}')
print(f'Should escalate: {result.should_escalate}')
"
```

---

## Integration Notes

**RivetOrchestrator Integration**:
```python
# After generating response from SME agent
response_text = agent.generate_response(query, kb_docs)

# Score response
score_result = confidence_scorer.score(
    query=query,
    response=response_text,
    kb_docs=kb_docs,
    citations=extract_citations(response_text)
)

# Check if escalation needed
if score_result.should_escalate:
    # Notify human expert
    await notify_human_expert(query, response_text, score_result)

    # Add warning to response
    response_text += "\n\n⚠️ This response has been escalated to a human expert for verification."

# Add confidence display to response
response_text += f"\n\nConfidence: {score_result.overall_confidence:.0%}"
```

---

## What This Enables

- ✅ Multi-dimensional quality evaluation (5 dimensions)
- ✅ Hallucination detection (citation verification, KB alignment)
- ✅ Safety analysis (keyword detection, dangerous advice warnings)
- ✅ Human-in-the-loop escalation (threshold-based)
- ✅ Detailed feedback (per-dimension scores and explanations)
- ✅ Customizable weights (adjust importance of each dimension)

---

## Next Steps

After implementing HARVEST 20, proceed to **HARVEST 21: Settings Service** for database-backed runtime configuration.

SEE FULL SOURCE: `agent_factory/rivet_pro/confidence_scorer.py` (520 lines - copy as-is)
