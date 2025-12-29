"""Research & Knowledge Base Team

Short-term research agents (<10s response):
- ManualFinder: Find equipment manuals
- QuickTroubleshoot: Instant troubleshooting from KB
- FieldFixRetriever: Historical fixes from CMMS/logs
- ShortTermOrchestrator: Coordinate all agents in parallel
"""

from agents.research.research_agent import ResearchAgent
from agents.research.atom_builder_agent import AtomBuilderAgent
from agents.research.atom_librarian_agent import AtomLibrarianAgent
from agents.research.quality_checker_agent import QualityCheckerAgent

# Short-term research agents
from agents.research.manual_finder import ManualFinder, ManualResult
from agents.research.quick_troubleshoot import QuickTroubleshoot, QuickFix
from agents.research.field_fix_retriever import FieldFixRetriever, FieldFix
from agents.research.short_term_orchestrator import ShortTermResearch, ShortTermResult

__all__ = [
    # Original agents
    "ResearchAgent",
    "AtomBuilderAgent",
    "AtomLibrarianAgent",
    "QualityCheckerAgent",
    # Short-term research agents
    "ManualFinder",
    "ManualResult",
    "QuickTroubleshoot",
    "QuickFix",
    "FieldFixRetriever",
    "FieldFix",
    "ShortTermResearch",
    "ShortTermResult",
]
