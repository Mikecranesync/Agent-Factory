"""CEO Agent Orchestration

Master orchestrator for autonomous agent ecosystem that:
- Reads backlog tasks
- Evaluates knowledge atoms
- Discovers product opportunities
- Auto-generates product specs and BUILD tasks
- Sends Telegram notifications
"""

from .ceo_agent import CEOAgentOrchestrator

__all__ = ["CEOAgentOrchestrator"]
