"""
RIVET Pro Phase 3 - Subject Matter Expert (SME) Agents

Provides vendor-specific and domain-specific troubleshooting agents:
- SiemensAgent: SIMATIC PLCs, SINAMICS drives, TIA Portal
- RockwellAgent: ControlLogix, PowerFlex, Studio 5000
- GenericPLCAgent: IEC 61131-3 fallback for unknown vendors
- SafetyAgent: IEC 61508/61511 compliance specialist

Usage:
    from agent_factory.rivet_pro.agents import AgentRouter

    router = AgentRouter()
    agent = router.route(intent)
    response = agent.handle(request, intent, route)
"""

from agent_factory.rivet_pro.agents.base_sme_agent import BaseSMEAgent
from agent_factory.rivet_pro.agents.generic_plc_agent import GenericPLCAgent
from agent_factory.rivet_pro.agents.siemens_agent import SiemensAgent
from agent_factory.rivet_pro.agents.rockwell_agent import RockwellAgent
from agent_factory.rivet_pro.agents.safety_agent import SafetyAgent
from agent_factory.rivet_pro.agents.agent_router import AgentRouter
from agent_factory.rivet_pro.agents.response_formatter import (
    extract_urls,
    extract_safety_warnings,
    format_citations_telegram,
    extract_action_lists,
    format_for_telegram,
    highlight_safety_warnings
)

__all__ = [
    # Base class
    "BaseSMEAgent",

    # Concrete agents
    "GenericPLCAgent",
    "SiemensAgent",
    "RockwellAgent",
    "SafetyAgent",

    # Router
    "AgentRouter",

    # Formatters
    "extract_urls",
    "extract_safety_warnings",
    "format_citations_telegram",
    "extract_action_lists",
    "format_for_telegram",
    "highlight_safety_warnings",
]
