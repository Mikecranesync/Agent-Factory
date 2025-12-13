"""
Committees Package - Democratic multi-agent decision-making systems.

5 Committee Systems:
1. QualityReviewCommittee - Video quality assessment
2. DesignCommittee - Visual design evaluation
3. EducationCommittee - Learning effectiveness review
4. ContentStrategyCommittee - Topic selection decisions
5. AnalyticsCommittee - Optimization recommendations

Each committee has 5 diverse members who vote with weighted consensus:
- 8.0+ → Approve
- 6.0-7.9 → Flag for discussion
- <6.0 → Reject

Usage:
    from agents.committees import QualityReviewCommittee

    committee = QualityReviewCommittee()
    decision = committee.vote(item)
    report = committee.generate_report()
"""

from .quality_review_committee import QualityReviewCommittee
from .design_committee import DesignCommittee
from .education_committee import EducationCommittee
from .content_strategy_committee import ContentStrategyCommittee
from .analytics_committee import AnalyticsCommittee

__all__ = [
    "QualityReviewCommittee",
    "DesignCommittee",
    "EducationCommittee",
    "ContentStrategyCommittee",
    "AnalyticsCommittee",
]

__version__ = "1.0.0"
