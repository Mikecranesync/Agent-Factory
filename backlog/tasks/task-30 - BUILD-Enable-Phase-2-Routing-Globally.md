---
id: task-30
title: 'BUILD: Enable Phase 2 Routing Globally'
status: In Progress
assignee: []
created_date: '2025-12-19 11:35'
updated_date: '2025-12-19 12:46'
labels:
  - cost-optimization
  - routing
  - quick-win
milestone: Cost-Optimized Model Routing
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Turn on existing Phase 2 routing in AgentFactory by default. Currently exists but disabled.

**Expected Impact**: 30-40% immediate cost reduction

**Acceptance Criteria**:
- `enable_routing=True` set as default in AgentFactory.__init__()
- All create_agent() calls use routing
- Routing decisions logged to cost tracker
- Verify 30-40% cost reduction in autonomous system

**Files**:
- agent_factory/core/agent_factory.py (line 81)
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
✅ Changed enable_routing default from False to True in AgentFactory.__init__ (line 63)

⏳ BLOCKED: Missing langchain_adapter.py - AgentFactory imports create_routed_chat_model() which doesn't exist

📊 Infrastructure Assessment: 80% complete - LLMRouter, UsageTracker, ModelCapability all exist

🔧 Next Step: Build langchain_adapter.py to bridge LLMRouter to LangChain ChatModel interface
<!-- SECTION:NOTES:END -->
