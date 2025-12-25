# Agent Execution History

**Tracks all agent executions for performance monitoring and debugging**

---

## Purpose

This log captures every agent execution:
- Which agent ran
- What task it performed
- Success/failure status
- Duration and cost
- Output artifacts

**Use Cases**:
- Debug agent failures
- Monitor performance trends
- Track cost per agent
- Identify slow agents
- Audit agent actions

---

## Log Format

| Timestamp | Agent | Task | Status | Duration | Cost | Output |
|-----------|-------|------|--------|----------|------|--------|
| ISO 8601 | Agent Name | Task Description | success/failure/partial | ms | USD | File/URL/JSON |

---

## Recent Executions

<!-- Auto-logged by .claude/hooks/on_agent_execute.sh and on_agent_finish.sh -->

<!-- Example entries:
| 2025-12-22T14:30:45Z | ScriptwriterAgent | Generate script for "3-Wire Motor Control" | success | 12,450ms | $0.042 | data/scripts/plc-motor-control-001.md |
| 2025-12-22T14:31:12Z | ResearchAgent | Scrape Allen-Bradley manual | success | 8,230ms | $0.018 | 15 atoms extracted |
| 2025-12-22T14:32:00Z | VoiceProductionAgent | Generate narration | failure | 3,100ms | $0.008 | ERROR: ElevenLabs API key invalid |
| 2025-12-22T14:35:20Z | VideoAssemblyAgent | Render video (1080p60) | success | 145,000ms | $0.000 | data/videos/plc-motor-control-001.mp4 |
-->

---

## Agent Performance Summary

### Top Agents by Executions (This Week)
1. **ResearchAgent**: 0 executions
2. **ScriptwriterAgent**: 0 executions
3. **AtomBuilderAgent**: 0 executions

### Top Agents by Cost (This Week)
1. **ResearchAgent**: $0.00
2. **ScriptwriterAgent**: $0.00
3. **VoiceProductionAgent**: $0.00

### Failure Rate (This Week)
- **Total Executions**: 0
- **Failures**: 0 (0%)
- **Partial Successes**: 0 (0%)

---

## Agent Metrics (Cumulative)

**Last Updated**: Session start

| Agent | Executions | Success Rate | Avg Duration | Total Cost |
|-------|------------|--------------|--------------|------------|
| ResearchAgent | 0 | 0% | 0ms | $0.00 |
| ScriptwriterAgent | 0 | 0% | 0ms | $0.00 |
| AtomBuilderAgent | 0 | 0% | 0ms | $0.00 |
| VoiceProductionAgent | 0 | 0% | 0ms | $0.00 |
| VideoAssemblyAgent | 0 | 0% | 0ms | $0.00 |

---

**Note**: Agent executions are auto-logged by hooks. View detailed metrics in `data/logs/hooks/metrics.json`
