---
id: task-38.6
title: 'BUILD: Intent Decoder - Ollama Mistral'
status: To Do
assignee: []
created_date: '2025-12-19 23:11'
labels:
  - build
  - tier-0
  - scaffold
  - intent
  - ollama
dependencies: []
parent_task_id: task-38
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Intent classification engine using Ollama Mistral to decode natural language commands into structured intents with confidence scoring. Enables CEO to communicate in rambling natural language without formal command syntax.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Ollama Mistral integration for intent classification
- [ ] #2 Intent types defined: code, architecture, test, docs, backlog, research
- [ ] #3 Confidence scoring (0.0-1.0) for each intent
- [ ] #4 Fallback to human-in-loop when confidence < 0.8
- [ ] #5 Natural language parsing handles rambling/incomplete commands
- [ ] #6 Unit tests with 10+ test cases covering edge cases
<!-- AC:END -->
