# Perplexity Integration Guide

**Date:** 2025-12-12
**Purpose:** Integrate Perplexity-style citation format throughout Agent Factory ISH swarm
**Reference:** `CLAUDEUPDATE.md` (5S methodology example)

---

## 🎯 Why This Matters

The `CLAUDEUPDATE.md` file shows the **EXACT format** that all knowledge atoms should use:

✅ Question-driven structure
✅ Professional citations with footnotes [^1][^2]
✅ Source URLs at bottom
✅ Markdown formatting with sections
✅ Multiple authoritative sources (8-10+)

**This format ensures:**
- **Citation integrity** - Every claim has a source
- **No hallucinations** - Grounded in authoritative references
- **YouTube credibility** - Viewers can verify claims
- **Script quality** - ScriptwriterAgent gets clean, cited input
- **Legal safety** - Attribution prevents copyright issues

---

## 📋 Example Format (from CLAUDEUPDATE.md)

```markdown
<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px"/>

# what does 5S mean when it comes to industrial maintenance and cleaning?

5S is a lean workplace-organization system from Japan that structures how industrial sites keep areas clean, safe, and efficient to support maintenance and production reliability.[^1][^6]

## What 5S stands for

In industrial maintenance and cleaning, 5S usually means:[^5][^6][^9]

- **Sort**: Remove items that are not needed...
- **Set in Order**: Arrange what's left...
- **Shine**: Clean equipment, floors...
- **Standardize**: Create simple, visual standards...
- **Sustain**: Build habits, audits, culture...

## Why it matters for maintenance and cleaning

- A good 5S program reduces time wasted hunting for tools...[^2][^4]
- Clean, organized areas make it easier to see abnormal conditions...[^3][^5]

[^1]: https://worktrek.com/blog/what-is-5s-principal-for-maintenance/
[^2]: https://www.milliken.com/en-us/businesses/performance-solutions-by-milliken/blogs/what-is-5s-and-how-does-it-apply-in-maintenance
[^3]: https://www.epa.gov/sustainability/lean-thinking-and-methods-5s
...
```

---

## 🔄 Integration Points

### 1. ResearchAgent (agents/research/research_agent.py)

**Current:** Scrapes Reddit for trending topics
**New:** Also uses Perplexity API for deep research on topics

**Changes Needed:**
```python
class ResearchAgent:
    def research_topic_perplexity(self, topic: str) -> Dict[str, Any]:
        """
        Use Perplexity API to generate cited research on topic.

        Returns:
            {
                "question": "What is PLC ladder logic?",
                "answer": "Markdown with [^1][^2] citations",
                "sources": [
                    {"id": 1, "url": "https://...", "title": "..."},
                    {"id": 2, "url": "https://...", "title": "..."}
                ]
            }
        """
        # TODO: Implement Perplexity API call
        pass
```

**Why:** Perplexity provides pre-cited, high-quality research vs manual scraping

---

### 2. AtomBuilderAgent (agents/knowledge/atom_builder_agent.py)

**Current:** Converts PDFs → Knowledge Atoms
**New:** Also parses Perplexity-format markdown → Knowledge Atoms

**Changes Needed:**
```python
class AtomBuilderAgent:
    def parse_perplexity_output(self, markdown: str) -> KnowledgeAtom:
        """
        Parse Perplexity-formatted markdown into structured atom.

        Extracts:
        - Question/title
        - Structured content (sections, bullet points)
        - Footnote citations [^1][^2]
        - Source URLs from bottom

        Returns:
            KnowledgeAtom with citations field populated
        """
        # TODO: Implement footnote parser
        pass
```

**Why:** Enables ingestion of Perplexity research directly into knowledge base

---

### 3. ScriptwriterAgent (agents/content/scriptwriter_agent.py)

**Current:** Queries Supabase atoms for script generation
**New:** Consumes atoms with citation metadata, includes citations in scripts

**Changes Needed:**
```python
class ScriptwriterAgent:
    def generate_script(self, topic: str, atoms: List[KnowledgeAtom]) -> VideoScript:
        """
        Generate script with inline citations.

        Example output:
        "According to Allen-Bradley's official documentation [citation: AB-ControlLogix-Manual, page 42],
        ladder logic uses three main elements..."

        Citations shown on-screen as:
        [show citation: AB ControlLogix Programming Manual, Chapter 3]
        """
        pass
```

**Why:** Builds credibility, allows viewers to verify claims

---

### 4. Knowledge Atom Schema Update

**Current Schema** (Supabase `knowledge_atoms` table):
```sql
CREATE TABLE knowledge_atoms (
    atom_id TEXT PRIMARY KEY,
    title TEXT,
    content TEXT,
    vendor TEXT,
    ...
);
```

**New Fields Needed:**
```sql
ALTER TABLE knowledge_atoms
ADD COLUMN citations JSONB DEFAULT '[]'::jsonb,
ADD COLUMN source_format TEXT DEFAULT 'manual'; -- 'manual', 'perplexity', 'reddit', 'pdf'

-- Example citations JSONB:
-- [
--   {"id": 1, "url": "https://...", "title": "Source Name", "accessed_at": "2025-12-12"},
--   {"id": 2, "url": "https://...", "title": "Source Name", "accessed_at": "2025-12-12"}
-- ]
```

**Why:** Preserves citation chain from research → atom → script → video

---

## 🔑 Perplexity API Integration

### Setup Steps

1. **Get API Key:**
   - Sign up at https://www.perplexity.ai/
   - Navigate to Settings → API
   - Generate API key

2. **Add to `.env.example`:**
```bash
# Perplexity API (for high-quality cited research)
# Get your API key at: https://www.perplexity.ai/settings/api
# PERPLEXITY_API_KEY=pplx-your-api-key-here
```

3. **Install SDK:**
```bash
poetry add openai  # Perplexity uses OpenAI-compatible API
```

4. **Usage Example:**
```python
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("PERPLEXITY_API_KEY"),
    base_url="https://api.perplexity.ai"
)

response = client.chat.completions.create(
    model="llama-3.1-sonar-large-128k-online",  # Latest model
    messages=[
        {"role": "system", "content": "You are a helpful assistant that provides cited research."},
        {"role": "user", "content": "What is PLC ladder logic? Provide citations."}
    ]
)

# Response includes inline citations
print(response.choices[0].message.content)
```

---

## 📊 Implementation Priority

### Phase 1: Foundation (Week 3, Day 1-2)
- [ ] Add `PERPLEXITY_API_KEY` to `.env.example`
- [ ] Update knowledge atom schema (add `citations` JSONB field)
- [ ] Create `AtomBuilderAgent.parse_perplexity_output()` method
- [ ] Test parsing `CLAUDEUPDATE.md` → Knowledge Atom

### Phase 2: Research Integration (Week 3, Day 3-4)
- [ ] Add Perplexity API to `ResearchAgent`
- [ ] Implement `ResearchAgent.research_topic_perplexity()`
- [ ] Create hybrid workflow: Reddit finds trends → Perplexity researches details

### Phase 3: Script Integration (Week 3, Day 5-6)
- [ ] Update `ScriptwriterAgent` to consume citation metadata
- [ ] Add inline citations to scripts (e.g., "[citation: Source Name, page 42]")
- [ ] Add visual cues for citations: `[show citation: ...]`

### Phase 4: Validation (Week 3, Day 7)
- [ ] Generate test script with citations from Perplexity atom
- [ ] Validate citation chain: Perplexity → Atom → Script → Video
- [ ] Ensure YouTube description includes "Sources:" section

---

## 🎬 End-to-End Flow (After Integration)

```
1. ResearchAgent finds trending topic on Reddit
   ↓
2. ResearchAgent uses Perplexity API to deep-dive research
   → Returns markdown with [^1][^2] citations
   ↓
3. AtomBuilderAgent parses Perplexity output
   → Creates KnowledgeAtom with citations JSONB field
   ↓
4. ScriptwriterAgent queries atom from Supabase
   → Generates script with inline citations
   → Example: "[citation: AB Manual Chapter 3, page 42]"
   ↓
5. VideoAssemblyAgent renders video
   → Shows citation on screen when mentioned
   ↓
6. YouTubeUploaderAgent publishes
   → Description includes "Sources:" section with all URLs
```

---

## ✅ Success Criteria

**For Research:**
- Every knowledge atom has 5+ authoritative sources
- Citations include URLs, titles, access dates
- No claims without attribution

**For Scripts:**
- Scripts include 3-5 citations per minute of video
- Citations shown visually: `[show citation: Source Name]`
- Viewers can verify claims via YouTube description

**For YouTube:**
- Every video description has "Sources:" section
- All citation URLs are clickable
- Attribution prevents copyright claims

---

## 🚨 Critical Reminders

1. **Never lose citation chain** - Every atom must preserve source URLs
2. **Test with CLAUDEUPDATE.md** - Use as reference template
3. **Perplexity API has costs** - ~$5/1000 requests (budget accordingly)
4. **Fallback to Reddit** - If Perplexity fails, use manual research
5. **Legal safety** - Citations prevent copyright violations

---

## 📚 References

- **Example Format:** `CLAUDEUPDATE.md` (5S methodology)
- **Tech Stack:** `docs/00_tech_stack.md` (Perplexity mentioned)
- **Knowledge Base:** `Knowledge.md` (Perplexity research strategy)
- **Niche Dominator:** Uses Perplexity for market research validation

---

**Generated:** 2025-12-12
**Next Steps:** Implement Phase 1 (Foundation) in Week 3
