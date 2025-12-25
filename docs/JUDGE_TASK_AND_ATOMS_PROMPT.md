# Gemini Judge Prompt: Quality + Product Discovery

## Purpose

Evaluate knowledge atoms for both:
1. **Quality scores** (1-5 scale): clarity, completeness, reusability, grounding
2. **Product potential**: yes/maybe/no + product idea + confidence score

This dual-purpose evaluation helps identify:
- High-quality atoms worth publishing to the knowledge base
- Product opportunities worth building into revenue-generating SaaS

## Input Format

You will receive:
- **Task context**: The backlog task these atoms were extracted from
- **Atoms**: A list of knowledge atom JSON objects

Each atom contains:
- `atom_id`: Unique identifier
- `title`: Pattern/concept name
- `problem`: What problem does this solve?
- `solution`: How does it solve the problem?
- `content`: Detailed implementation notes
- `keywords`: Searchable tags
- `source_document`: Where was this extracted from?

## Evaluation Criteria

### Part 1: Quality Scores (1-5 each)

For each atom, evaluate:

**1. Clarity (1-5)**
- Is the title clear and specific?
- Is the problem well-defined?
- Is the solution easy to understand?
- Are there ambiguous terms or unclear explanations?

**2. Completeness (1-5)**
- Does it include problem + solution + implementation details?
- Are all key fields populated with substance (not placeholders)?
- Is there enough context to understand the pattern?
- Are edge cases or limitations mentioned?

**3. Reusability (1-5)**
- Could another engineer implement this without additional research?
- Is it abstracted enough to apply to multiple contexts?
- Are there code examples or concrete steps?
- Is the pattern generalizable beyond the source repo?

**4. Grounding (1-5)**
- Is it based on real, working code (not theoretical)?
- Are sources cited accurately?
- Is the pattern proven/validated?
- Are there hallucinations or speculative claims?

**5. Overall Score (1-5)**
- Synthesis of the above
- Would you publish this to a knowledge base?
- Is this production-quality documentation?

**Scoring Rubric:**
- **5**: Excellent - Publish-ready, comprehensive, actionable
- **4**: Good - Usable with minor refinements
- **3**: Fair - Needs significant editing
- **2**: Poor - Major gaps or errors
- **1**: Unusable - Confusing, incorrect, or incomplete

### Part 2: Product Discovery

For each atom, evaluate:

**1. Product Potential (yes / maybe / no)**
- Does this pattern suggest a product or service?
- Is there a clear market need?
- Could this be monetized as SaaS?

**2. Product Idea (if potential: yes/maybe)**
- What product emerges from this atom?
- 1-2 sentence product pitch
- Example: "Search-as-a-Service addon that combines vector + keyword search with re-ranking"

**3. Target Market**
- Who would buy this?
- Examples: "Dev agencies", "Enterprise teams", "Technical founders", "Industrial maintenance teams"

**4. Price Tier**
- What pricing makes sense?
- Options: $29/mo, $99/mo, $499/mo, $999/mo, $5K-$10K/mo (enterprise)

**5. Effort to Productize**
- How much work to ship a beta?
- **Low (1-2 weeks)**: Pattern is 80% complete, minor UI/packaging needed
- **Medium (3-6 weeks)**: Core logic exists, needs significant integration work
- **High (2-3 months)**: Complex feature, multiple components, infrastructure work

**6. Product Confidence (1-5)**
- How sure are you this would sell?
- **5**: Slam dunk - Solves known pain, clear demand
- **4**: High confidence - Good market fit, proven pattern
- **3**: Moderate - Needs validation, niche market
- **2**: Uncertain - Speculative, unclear demand
- **1**: Low - Unlikely to succeed

## Output Format

Return a JSON object with this structure:

```json
{
  "task_id": "<task-id from input>",
  "atoms_evaluated": <number of atoms>,
  "median_quality_score": <median of overall_score across all atoms>,
  "quality_distribution": {
    "excellent": <count of atoms with score 5>,
    "good": <count with score 4>,
    "fair": <count with score 3>,
    "poor": <count with score 2>,
    "unusable": <count with score 1>
  },
  "fastest_monetization_pick": {
    "chosen_product_atom_id": "<atom_id>",
    "chosen_product_name": "<product name>",
    "product_idea": "<1-2 sentence pitch>",
    "target_market": "<who would buy this>",
    "price_tier": "<$XX/mo>",
    "effort_to_productize": "Low | Medium | High",
    "product_confidence": <1-5>,
    "next_steps": [
      "<actionable step 1>",
      "<actionable step 2>",
      "<actionable step 3>"
    ]
  },
  "all_product_candidates": [
    {
      "atom_id": "<atom_id>",
      "product_name": "<name>",
      "product_idea": "<pitch>",
      "product_confidence": <1-5>,
      "effort_to_productize": "Low | Medium | High"
    }
  ],
  "atoms_with_scores": [
    {
      "atom_id": "<atom_id>",
      "title": "<atom title>",
      "clarity": <1-5>,
      "completeness": <1-5>,
      "reusability": <1-5>,
      "grounding": <1-5>,
      "overall_score": <1-5>,
      "product_potential": "yes | maybe | no",
      "product_notes": "<brief explanation>"
    }
  ]
}
```

## Selection Logic for "Fastest Monetization Pick"

Choose the atom that:
1. Has `product_potential: "yes"`
2. Has highest `product_confidence` (4-5/5)
3. Has lowest `effort_to_productize` (prefer "Low" > "Medium" > "High")
4. Has highest `overall_score` (quality matters)

**If no atoms meet criteria:** Set `fastest_monetization_pick: null`

## Example Evaluation

**Input Atom:**
```json
{
  "atom_id": "pattern:hybrid-search-001",
  "title": "Hybrid Search (Vector + Keyword)",
  "problem": "Vector-only search misses exact keyword matches; keyword-only misses semantic meaning",
  "solution": "Query both indexes; re-rank results with weighted scoring (0.7 * vector + 0.3 * keyword)",
  "content": "Implementation uses pgvector for embeddings + GIN indexes for keywords. Re-ranking in application layer using RRF (Reciprocal Rank Fusion).",
  "keywords": ["search", "vector", "keyword", "hybrid", "pgvector"],
  "source_document": "archon/memory/hybrid_search.py"
}
```

**Output:**
```json
{
  "atom_id": "pattern:hybrid-search-001",
  "title": "Hybrid Search (Vector + Keyword)",
  "clarity": 5,
  "completeness": 4,
  "reusability": 5,
  "grounding": 5,
  "overall_score": 5,
  "product_potential": "yes",
  "product_notes": "Clear SaaS opportunity - many companies struggle with search quality. Could package as API or managed service."
}
```

**Product Discovery:**
```json
{
  "chosen_product_atom_id": "pattern:hybrid-search-001",
  "chosen_product_name": "Search-as-a-Service Hybrid Engine",
  "product_idea": "Managed search API that combines vector embeddings + keyword matching with intelligent re-ranking. Drop-in replacement for Algolia/Elasticsearch.",
  "target_market": "SaaS companies, dev agencies, technical founders building search features",
  "price_tier": "$499/mo",
  "effort_to_productize": "Medium",
  "product_confidence": 4,
  "next_steps": [
    "Package hybrid_search.py as standalone API service",
    "Add usage tracking + billing integration",
    "Create client SDKs (Python, JS, Ruby)",
    "Build demo app showing vector + keyword comparison",
    "Test with 3-5 beta customers"
  ]
}
```

## Important Notes

- **Be honest about quality**: Don't inflate scores. A score of 3/5 is fine.
- **Be specific about products**: Generic ideas like "tool for developers" are not actionable.
- **Focus on fast monetization**: Prefer products that can ship in 1-2 months over ambitious 6-month projects.
- **Check your work**: Median quality score should match the distribution. Product confidence should align with market reality.
- **Return valid JSON**: No trailing commas, no comments, proper escaping.

## Prompt Template for CEO Agent

When calling Gemini, use this prompt structure:

```
You are a dual-purpose judge evaluating knowledge atoms extracted from GitHub repositories.

TASK CONTEXT:
{task_description}

ATOMS TO EVALUATE:
{atoms_json}

Please evaluate these atoms using the criteria in docs/JUDGE_TASK_AND_ATOMS_PROMPT.md.

Return a JSON object with:
1. Quality scores for each atom (clarity, completeness, reusability, grounding, overall)
2. Product potential assessment (yes/maybe/no)
3. The single fastest monetization pick (highest confidence + lowest effort)
4. All product candidates (confidence >= 4)

Focus on finding products that can ship in 1-2 months and generate $1K-$5K MRR.

Output only valid JSON matching the schema in the prompt document. No markdown, no code blocks, just raw JSON.
```
