---
id: task-86.6
title: 'DEPLOY: Ingest Atoms to Database & Validate Search Quality'
status: To Do
assignee: []
created_date: '2025-12-21 16:39'
labels:
  - deploy
  - database
  - validation
  - phase-5
dependencies:
  - task-86.6
parent_task_id: task-86
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
# DEPLOY: Ingest Atoms to Database & Validate Search Quality

Part of EPIC: Knowledge Extraction from CORE Repositories (task-86)

## Goal
Insert knowledge atoms into PostgreSQL database and validate semantic search quality.

## Steps

### Day 13: Database Ingestion
1. **Run Ingestion Pipeline**:
   ```python
   from agent_factory.workflows.ingestion_chain import ingest_atoms

   atoms = load_atoms_from_json("atoms-core-repos.json")
   ingest_atoms(atoms, generate_embeddings=True)
   ```

2. **Create Indexes**:
   ```sql
   CREATE INDEX idx_atoms_vendor ON knowledge_atoms(vendor);
   CREATE INDEX idx_atoms_type ON knowledge_atoms(atom_type);
   CREATE INDEX idx_atoms_keywords ON knowledge_atoms USING GIN(keywords);
   ```

3. **Verify Insertions**:
   ```sql
   SELECT COUNT(*) FROM knowledge_atoms WHERE vendor IN ('agent-factory', 'backlog-md', 'pai-config');
   ```

### Day 14: Search Validation
1. **Benchmark Queries** (10 test queries):
   - Query 1: "How to implement LLM routing?" → Should return LLM Router atom
   - Query 2: "Database failover patterns" → Should return Database Manager atom
   - Query 3: "Best practices for MCP servers" → Should return Backlog.md atoms
   - Query 4-10: Domain-specific queries

2. **Measure Precision**:
   ```python
   precision = relevant_results / total_results
   # Target: >85% precision
   ```

3. **Integrate with RAG Pipeline**:
   ```python
   from agent_factory.rivet_pro.rag import search_docs

   docs = search_docs("agent orchestration patterns")
   assert len(docs) > 0
   assert docs[0].similarity > 0.8
   ```

## Validation Commands
```bash
# Check atom count
poetry run python -c "from agent_factory.core.database_manager import DatabaseManager; db = DatabaseManager(); print(db.execute_query('SELECT COUNT(*) FROM knowledge_atoms', fetch_mode='one'))"

# Test semantic search
poetry run python scripts/test_knowledge_search.py --query "llm routing patterns"
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 All atoms ingested into knowledge_atoms table
- [ ] #2 Embeddings indexed for vector search
- [ ] #3 Database indexes created (vendor, type, keywords)
- [ ] #4 10 benchmark queries tested
- [ ] #5 Precision >85% (relevant results / total results)
- [ ] #6 RAG pipeline integration validated
- [ ] #7 Performance acceptable (<500ms for semantic search)
<!-- AC:END -->
