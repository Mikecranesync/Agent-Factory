---
id: task-86.5
title: 'DOCUMENT: Add Inline Documentation to Critical Files'
status: To Do
assignee: []
created_date: '2025-12-21 16:39'
labels:
  - document
  - docstrings
  - comments
  - phase-3
dependencies:
  - task-86.1
parent_task_id: task-86
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
# DOCUMENT: Add Inline Documentation to Critical Files

Part of EPIC: Knowledge Extraction from CORE Repositories (task-86)

## Goal
Add comprehensive inline documentation (docstrings, comments) to critical source files.

**Target**: 5-10 critical files (from Subtask 1 inventory)

## Target Files
1. `agent_factory/llm/router.py` - Add class/method docstrings
2. `agent_factory/core/database_manager.py` - Document failover logic
3. `agent_factory/core/settings_service.py` - Usage examples in docstrings
4. `agent_factory/templates/sme_agent_template.py` - Already documented ✅
5. `agent_factory/memory/storage.py` - Add parameter descriptions
6. `backlog/lib/task-manager.ts` - MCP task management
7. `backlog/lib/yaml-parser.ts` - YAML frontmatter parsing
8. `pai-config-windows/hooks/capture-all-events.ts` - Event capture logic

## Documentation Standards
- **Module-level docstrings**: Purpose, usage, examples
- **Class docstrings**: Responsibility, attributes, example usage
- **Method docstrings**: Args, Returns, Raises, Examples (Google style)
- **Inline comments**: Complex logic only (don't state obvious)

## Example Docstring
```python
def route_by_capability(
    self,
    messages: List[Dict[str, str]],
    capability: ModelCapability
) -> LLMResponse:
    """
    Route request to cheapest model for capability.

    Selects the most cost-effective model that meets the
    required capability level.

    Args:
        messages: List of message dicts (role, content)
        capability: Required capability level (SIMPLE, MODERATE, COMPLEX)

    Returns:
        LLMResponse from selected model

    Raises:
        ModelNotFoundError: If no models available for capability

    Example:
        >>> response = router.route_by_capability(
        ...     messages=[{"role": "user", "content": "Simple task"}],
        ...     capability=ModelCapability.SIMPLE
        ... )
        >>> print(f"Used: {response.model}")
        gpt-3.5-turbo
    """
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 5-10 critical files documented
- [ ] #2 All modules have module-level docstrings
- [ ] #3 All public classes have docstrings
- [ ] #4 All public methods have Args/Returns/Examples
- [ ] #5 Complex logic has inline comments
- [ ] #6 Help system works: help(module) returns documentation
<!-- AC:END -->
