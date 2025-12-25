"""
Agent Templates - Reusable patterns for building specialized agents.

Provides template classes and patterns for common agent types:
- SME (Subject Matter Expert) agents
- PLC agent templates
- Research agent templates
"""

# Lazy imports
def __getattr__(name):
    if name == "SMEAgentTemplate":
        from agent_factory.templates.sme_agent_template import SMEAgentTemplate
        return SMEAgentTemplate
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    "SMEAgentTemplate",
]
