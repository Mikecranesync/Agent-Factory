"""Knowledge Atom Judges

Dual-purpose evaluation system for knowledge atoms:
1. Quality assessment (clarity, completeness, reusability, grounding)
2. Product discovery (monetization potential, confidence, effort estimation)
"""

from .gemini_judge import GeminiJudge, JudgmentResult

__all__ = ["GeminiJudge", "JudgmentResult"]
