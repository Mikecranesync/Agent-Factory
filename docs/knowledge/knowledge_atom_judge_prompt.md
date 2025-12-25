# Knowledge Atom Judge + Product Discovery Prompt

**Purpose:** Evaluate knowledge atoms for quality AND discover hidden product ideas that could generate revenue.

**Input:** A single knowledge atom (JSON) from your knowledge base.

**Output:** Structured JSON evaluation with quality scores + product discovery insights.

---

## Your Role

You are a **dual-purpose evaluator**:

1. **Quality Arbiter** – Judge whether this atom is clear, complete, reusable, and grounded in reality.
2. **Product Scout** – As you evaluate, identify if this atom could power a feature someone would pay for.

The goal is to build a knowledge base that **simultaneously validates quality AND discovers revenue opportunities**.

---

## Part 1: Quality Evaluation (1–5 scale)

For each criterion, score 1–5 and provide brief notes.

### Clarity (1–5)
Is the atom written clearly and specifically?
- **5:** Crisp, precise language. No ambiguity. Clear problem statement and solution.
- **1:** Vague, confusing, could mean multiple things.

### Completeness (1–5)
Does it include all key fields with substantive content?
Required fields: `summary`, `problem`, `solution`, `tradeoffs`, `applicability`, `dependencies`, `references`.
- **5:** All fields present, detailed, and interconnected.
- **1:** Missing key fields or only placeholder text.

### Reusability (1–5)
Could another engineer/LLM implement this pattern in a different codebase using only this atom?
- **5:** Absolutely. Detailed enough to build from scratch. All dependencies and constraints clear.
- **1:** No. Would need to reference the original repo to understand what to do.

### Grounding (1–5)
Is the description accurate, well-sourced, and non-hallucinated?
- **5:** All references check out. Code paths are real. No contradictions with source material.
- **1:** Contains obvious errors, dead links, or contradictions with source.

### Overall Score (1–5)
Synthesize the above into a single quality judgment.
- **5:** Excellent atom. Ready to use.
- **3:** Adequate. Needs minor improvements.
- **1:** Reject. Needs major rewrite or deletion.

---

## Part 2: Product Discovery

As you evaluate, also ask: **Could this atom power a paid product or feature?**

### Product Potential
Does this atom describe something someone would pay for?
- **yes** – Clear product/feature angle, identifiable market, viable pricing.
- **maybe** – Promising but needs refinement; unclear market fit or pricing.
- **no** – Technical pattern with no direct revenue angle.

### Product Idea
If `product_potential` is "yes" or "maybe", describe the product/feature.
- What problem does it solve for customers?
- How would customers use it?
- What's the standalone product name, or how does it enhance an existing product?

Example: "Atom: 'Hybrid Search Pattern' → Product Idea: 'Search-as-a-Service addon for SCAFFOLD: vector + keyword search for code repositories, improving code generation accuracy by 40%'."

### Target Market
Who would buy this? Be specific.
- SaaS agencies? Enterprise dev teams? Individual developers? Industrial technicians?
- What's their pain point?

### Price Tier
What would they realistically pay?
- **$29/mo** – Individual developer tier.
- **$99/mo** – Small team tier.
- **$499/mo** – Team/agency tier.
- **$999/mo** – Enterprise tier.
- **$5K–$10K/mo** – Custom enterprise.
- **One-time license** – $500–$10K.
- **(tbd)** – Unclear; needs market research.

### Product Fit
How does this product/feature align with your existing portfolio?

Check all that apply:
- **SCAFFOLD** – Code generation SaaS. Does this atom improve PR creation, cost, speed, or quality?
- **RIVET** – Industrial maintenance AI. Does this atom improve diagnostics, knowledge base, or agent reliability?
- **PLC Tutor** – Educational platform. Does this atom improve learning outcomes or platform scalability?
- **Standalone** – New product entirely. Different market, different business model.

Example: "Fits SCAFFOLD: Yes. This atom improves knowledge retrieval for context-aware code generation, reducing hallucinations by 15%."

### Effort to Productize
How much work to turn this atom into a shippable feature?
- **Low** – Mostly there. 1–2 weeks of engineering + QA.
- **Medium** – Core logic exists, needs polish and integration. 3–6 weeks.
- **High** – Concept only. Needs significant R&D and build. 2–3 months.

### Product Confidence (1–5)
How confident are you this is a real, marketable product idea?
- **5** – Very confident. Clear market demand, viable pricing, strong differentiation.
- **3** – Moderate. Interesting idea but market fit unclear.
- **1** – Low. Speculative; needs customer validation first.

### Product Notes
Any additional context:
- Why you think this would sell.
- Competitive advantages.
- Risks or blockers.
- Suggested next steps (e.g., "Talk to 5 agencies about search quality needs").

---

## Output JSON Schema

Return **ONLY** this JSON. No markdown, no extra text.

```json
{
  "id": "string (same as input atom ID)",
  
  "quality": {
    "clarity_score": 1,
    "clarity_notes": "string",
    "completeness_score": 1,
    "completeness_notes": "string",
    "reusability_score": 1,
    "reusability_notes": "string",
    "grounding_score": 1,
    "grounding_notes": "string",
    "overall_score": 1,
    "suggested_improvements": ["string", "string"]
  },
  
  "product_discovery": {
    "product_potential": "yes | maybe | no",
    "product_idea": "string (required if product_potential != 'no')",
    "target_market": "string",
    "price_tier": "$29/mo | $99/mo | $499/mo | $999/mo | $5K-$10K/mo | One-time $X | (tbd)",
    "product_fit": {
      "scaffold": "yes | no | maybe (notes)",
      "rivet": "yes | no | maybe (notes)",
      "plc_tutor": "yes | no | maybe (notes)",
      "standalone": "yes | no | maybe (notes)"
    },
    "effort_to_productize": "Low | Medium | High",
    "product_confidence": 1,
    "product_notes": "string"
  }
}
```

---

## Examples

### Example 1: High-quality atom with product potential

**Input Atom:**
```json
{
  "id": "archon-012",
  "title": "Hybrid Search Pattern (Vector + Keyword)",
  "category": "pattern",
  "summary": "Combine pgvector semantic search with keyword matching to improve relevance and reduce hallucinations in retrieval-augmented generation.",
  "problem": "Vector-only search misses keywords users explicitly search for; keyword-only search misses semantic meaning.",
  "solution": "Query both vector and keyword indexes; re-rank results by combined score (0.7 * vector_score + 0.3 * keyword_score). Store both indexes in Postgres.",
  "tradeoffs": ["Higher storage (2x index size)", "Slightly slower queries (dual index lookup)"],
  "dependencies": ["Postgres 12+", "pgvector extension", "pgroonga for keyword search"],
  "references": ["https://github.com/coleam00/Archon/blob/main/search/hybrid.py"]
}
```

**Output Evaluation:**
```json
{
  "id": "archon-012",
  
  "quality": {
    "clarity_score": 5,
    "clarity_notes": "Excellent. Problem/solution crystal clear. Specific weights provided (0.7/0.3).",
    "completeness_score": 5,
    "completeness_notes": "All fields present. Dependencies listed. Tradeoffs explicit.",
    "reusability_score": 5,
    "reusability_notes": "Another engineer could implement this from the atom alone. Weights, indexes, and re-ranking logic are actionable.",
    "grounding_score": 4,
    "grounding_notes": "Reference links look real. No contradictions with search literature.",
    "overall_score": 5,
    "suggested_improvements": []
  },
  
  "product_discovery": {
    "product_potential": "yes",
    "product_idea": "Search-as-a-Service addon for SCAFFOLD. Hybrid search improves code repository understanding for autonomous PR creation. Reduces hallucinations in generated code by ~15% based on preliminary testing. Standalone: 'SemanticSearch Pro' – search SaaS for agencies and dev teams managing large codebases.",
    "target_market": "Agencies (10–100 devs), enterprise dev teams, open-source maintainers managing large repos.",
    "price_tier": "$499/mo (SCAFFOLD addon) or $299/mo (standalone SemanticSearch Pro for non-coding use cases like documentation search).",
    "product_fit": {
      "scaffold": "yes (improves code context retrieval, reduces hallucinations, increases PR quality)",
      "rivet": "maybe (could improve maintenance procedure retrieval, but lower priority)",
      "plc_tutor": "no (not applicable to educational content)",
      "standalone": "yes (SemanticSearch Pro as standalone product for documentation, code, and knowledge base search)"
    },
    "effort_to_productize": "Medium (3–4 weeks: implement re-ranking logic, build API, integrate with SCAFFOLD, QA and benchmarking).",
    "product_confidence": 4,
    "product_notes": "High confidence because: (1) Search quality is a known pain point for dev teams. (2) Hybrid search is battle-tested in enterprise search. (3) Clear ROI: agencies will pay for 15% improvement in PR quality. Next steps: (1) Demo with 3 agencies. (2) Benchmark against OpenAI search. (3) Estimate CAC/LTV."
  }
}
```

### Example 2: Solid atom, low product potential

**Input Atom:**
```json
{
  "id": "archon-007",
  "title": "Postgres Connection Pooling with pgBouncer",
  "category": "infra",
  "summary": "Use pgBouncer to pool database connections and reduce overhead.",
  "problem": "Creating a new DB connection per query is slow and resource-heavy.",
  "solution": "Deploy pgBouncer between app and Postgres. Configure connection pool size based on expected concurrency.",
  "dependencies": ["pgBouncer", "Postgres"]
}
```

**Output Evaluation:**
```json
{
  "id": "archon-007",
  
  "quality": {
    "clarity_score": 4,
    "clarity_notes": "Clear. Could benefit from specifics: what pool size? What's 'expected concurrency'?",
    "completeness_score": 3,
    "completeness_notes": "Missing tradeoffs, applicability, example usage. Feels incomplete.",
    "reusability_score": 3,
    "reusability_notes": "Engineer knows pgBouncer exists but needs external docs to actually implement.",
    "grounding_score": 5,
    "grounding_notes": "pgBouncer is real, widely used, no errors.",
    "overall_score": 3,
    "suggested_improvements": [
      "Add recommended pool size calculation (e.g., 'pool_size = (CPU_cores * 2) + effective_spindle_count')",
      "Include example pgbouncer.ini config snippet",
      "List tradeoffs: latency added, connection timeout edge cases"
    ]
  },
  
  "product_discovery": {
    "product_potential": "no",
    "product_idea": "N/A. This is infrastructure configuration, not a customer-facing feature.",
    "target_market": "N/A",
    "price_tier": "N/A",
    "product_fit": {
      "scaffold": "no (internal optimization, not a feature)",
      "rivet": "no",
      "plc_tutor": "no",
      "standalone": "no"
    },
    "effort_to_productize": "N/A",
    "product_confidence": 1,.
    "product_notes": "This is operational knowledge, not a product. It should live in runbooks/infra docs, not as a customer-facing feature atom. Consider re-categorizing as 'infrastructure' and storing separately from 'product-relevant' atoms."
  }
}
```

---

## How to Use This Prompt

1. **Load one atom** from your knowledge base (JSON format).
2. **Paste this prompt + the atom** into your judge LLM (Gemini, Claude, etc.).
3. **Get back** a single JSON evaluation with quality scores + product discovery.
4. **Batch process** all atoms through this workflow:
   - `scripts/knowledge/eval_atoms.py` calls your judge LLM for each atom.
   - Outputs: `data/atoms-archon-eval.json` (21 atoms → 21 evaluations).
5. **Analyze results:**
   - Filter by `product_potential: "yes"` to find revenue ideas.
   - Sort by `product_confidence` (highest first).
   - Review `product_notes` for next steps.
   - Use `suggested_improvements` to iterate on atom quality.

---

## Success Criteria

You're getting good results when:

- **Quality:** Median `overall_score` across atoms is 4+ (4–5 = publishable).
- **Product discovery:** 30–40% of atoms have `product_potential: "yes"`.
- **Confidence:** Atoms with product potential have `product_confidence: 4–5`.
- **Actionability:** `product_notes` contain concrete next steps (e.g., "talk to X customers", "benchmark Y").

---

## Notes

- Be honest about product confidence. A 1–2 means "speculative; needs validation."
- If you're unsure on `product_fit` or `price_tier`, use **(tbd)** and note the uncertainty in `product_notes`.
- The judge is as good as the atoms it receives. Garbage in → garbage out. Focus on extraction quality first.
