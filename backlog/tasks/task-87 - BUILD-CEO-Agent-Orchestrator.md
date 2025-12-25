---
id: task-87
title: BUILD CEO Agent Orchestrator
status: To Do
assignee: []
created_date: '2025-12-22 06:03'
labels:
  - build
  - ceo-agent
  - orchestration
  - automation
  - product-discovery
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement autonomous master orchestrator that reads backlog tasks, extracts atoms, calls Gemini judge for quality + product discovery, generates product specs, creates BUILD tasks, and sends Telegram notifications.

**What It Does:**
Extract atoms → Judge quality + discover products → Parse top products → Generate specs → Create BUILD tasks → Send Telegram → Loop

**Architecture:**
- Backlog Reader (parse YAML task metadata)
- Extraction Trigger (check if atoms-{task-id}.json exists)
- Judge Caller (Gemini API with dual-purpose prompt)
- Product Parser (extract fastest_monetization_pick, filter confidence ≥4)
- Spec Generator (create docs/products/{slug}.md)
- Task Creator (generate BUILD tasks in backlog)
- Reporter (Telegram notifications + logging)
- Loop Controller (continuous 5min interval)

**Outputs:**
- data/atoms-*-eval.json (judge evaluations)
- docs/products/*.md (auto-generated product specs)
- backlog/tasks/task-* - BUILD-*.md (new BUILD tasks)
- Telegram messages (progress summaries)
- logs/ceo-agent.log (execution trace)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Backlog Reader: Reads YAML frontmatter from backlog/tasks/*.md, filters by status (To Do) and priority (high, medium)
- [ ] #2 Extraction Trigger: Checks if data/atoms-{task-id}.json exists, skips if missing
- [ ] #3 Judge Caller: Calls Gemini API with judge prompt + task context + atoms, parses JSON response
- [ ] #4 Quality Scores: Extracts clarity, completeness, reusability, grounding, overall_score (1-5 each)
- [ ] #5 Product Discovery: Extracts product_potential, product_idea, target_market, price_tier, effort_to_productize, product_confidence (1-5)
- [ ] #6 Eval Output: Writes data/atoms-{task-id}-eval.json with quality + product discovery fields
- [ ] #7 Product Parser: Extracts fastest_monetization_pick from eval JSON, filters by product_confidence ≥4
- [ ] #8 Spec Generator: Creates docs/products/{slug}.md with summary, target market, pricing, effort, next steps
- [ ] #9 Task Creator: Generates backlog/tasks/task-{id} - BUILD-{slug}.md with acceptance criteria from spec
- [ ] #10 Telegram Reporter: Sends notification with task processed, quality median, top product pick, next steps
- [ ] #11 Logger: Writes execution trace to logs/ceo-agent.log (timestamp, task, status, errors)
- [ ] #12 Loop Controller: Implements continuous loop (5min interval), processes high/medium priority tasks in sequence
- [ ] #13 Error Handling: Gracefully handles missing files, API failures, logs errors and continues to next task
<!-- AC:END -->
