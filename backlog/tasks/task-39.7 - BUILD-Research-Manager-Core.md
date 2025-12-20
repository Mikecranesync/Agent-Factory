---
id: task-39.7
title: 'BUILD: Research Manager Core'
status: To Do
assignee: []
created_date: '2025-12-19 23:30'
labels:
  - build
  - tier-1
  - research
  - orchestration
dependencies: []
parent_task_id: task-39
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Build Research Manager to orchestrate 5 explorers, filter discoveries, score quality, and publish breaking news to Telegram.

**Purpose:** Central coordinator for the Research Department that receives discoveries from 5 specialist explorers, applies relevance filtering, quality scoring, and generates breaking news articles with citations for Telegram publication.

**Integration Points:**
- Receives discovery objects from 5 Explorer agents (task-39.1 to task-39.5)
- Applies project-specific keyword filtering
- Quality scoring algorithm (source credibility + recency)
- Breaking news article generation with citations
- Publishing pipeline to Telegram
- Duplicate detection (hash-based)

**Success Criteria:** Research team operational with automated discovery pipeline.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Research Manager receives discoveries from 5 explorers
- [ ] #2 Relevance filtering (project-specific keywords)
- [ ] #3 Quality scoring algorithm (source credibility + recency)
- [ ] #4 Breaking news article generation with citations
- [ ] #5 Publishing pipeline to Telegram
- [ ] #6 Duplicate detection (hash-based)
<!-- AC:END -->
