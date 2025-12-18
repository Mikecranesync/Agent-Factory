"""
Content Strategy Committee - Democratic content selection assessment system.

5 strategy experts vote on topic selection with weighted consensus.
Focus: Relevance, SEO, audience fit, timing, gap coverage.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CommitteeMember:
    """Represents a committee member with their profile and voting weight."""
    name: str
    role: str
    weight: float
    background: str
    priorities: List[str]


@dataclass
class Vote:
    """Individual member's vote with score and feedback."""
    member_name: str
    score: float  # 0-10
    feedback: str
    timestamp: datetime


@dataclass
class CommitteeDecision:
    """Final committee decision with all member votes."""
    decision: str  # "approve", "flag", "reject"
    overall_score: float
    consensus_level: float  # 0-1
    votes: Dict[str, Dict[str, Any]]
    concerns: List[str]
    recommendations: List[str]
    timestamp: datetime


class ContentStrategyCommittee:
    """
    Content Strategy Committee - Assesses content topic selection from 5 expert perspectives.

    Members:
    - Amanda (Content Strategist, 25%) - Overall content strategy and planning
    - Zack (SEO Specialist, 25%) - Search optimization and keyword targeting
    - Morgan (Audience Analyst, 20%) - Audience needs and engagement
    - Taylor (Editorial Director, 15%) - Editorial quality and voice
    - Chris (Competitive Analyst, 15%) - Market gaps and differentiation

    Focus Areas:
    - Topic relevance to target audience
    - SEO potential and keyword opportunities
    - Audience fit and engagement likelihood
    - Strategic timing and seasonality
    - Gap coverage in existing content

    Voting:
    - 8.0+ → Approve
    - 6.0-7.9 → Flag for discussion
    - <6.0 → Reject
    """

    def __init__(self):
        """Initialize committee with 5 content strategy experts."""
        self.members = [
            CommitteeMember(
                name="Amanda",
                role="Content Strategist",
                weight=0.25,
                background="10 years content strategy, editorial planning",
                priorities=["strategic_alignment", "content_gaps", "planning", "ROI"]
            ),
            CommitteeMember(
                name="Zack",
                role="SEO Specialist",
                weight=0.25,
                background="Technical SEO and keyword research expert",
                priorities=["search_volume", "keyword_difficulty", "intent", "ranking"]
            ),
            CommitteeMember(
                name="Morgan",
                role="Audience Analyst",
                weight=0.20,
                background="Audience research and engagement analytics",
                priorities=["audience_need", "engagement", "relevance", "retention"]
            ),
            CommitteeMember(
                name="Taylor",
                role="Editorial Director",
                weight=0.15,
                background="Editorial quality and brand voice expert",
                priorities=["quality", "voice", "storytelling", "uniqueness"]
            ),
            CommitteeMember(
                name="Chris",
                role="Competitive Analyst",
                weight=0.15,
                background="Competitive intelligence and market analysis",
                priorities=["differentiation", "gaps", "opportunity", "positioning"]
            )
        ]

        self.votes: List[Vote] = []

    def vote(self, item: Dict[str, Any]) -> CommitteeDecision:
        """
        Committee votes on content topic selection.

        Args:
            item: Content topic to review (relevance, SEO, audience fit, etc.)

        Returns:
            CommitteeDecision with weighted consensus
        """
        self.votes = []
        member_votes = {}

        # Each member evaluates based on their expertise
        for member in self.members:
            score, feedback = self._member_evaluate(member, item)

            vote = Vote(
                member_name=member.name,
                score=score,
                feedback=feedback,
                timestamp=datetime.now()
            )
            self.votes.append(vote)

            member_votes[member.name] = {
                "score": score,
                "feedback": feedback,
                "weight": member.weight
            }

        # Calculate weighted average
        weighted_sum = sum(
            member_votes[m.name]["score"] * m.weight
            for m in self.members
        )
        overall_score = weighted_sum

        # Determine decision
        if overall_score >= 8.0:
            decision = "approve"
        elif overall_score >= 6.0:
            decision = "flag"
        else:
            decision = "reject"

        # Calculate consensus
        scores = [v.score for v in self.votes]
        avg_score = sum(scores) / len(scores)
        variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
        std_dev = variance ** 0.5
        consensus_level = max(0, 1 - (std_dev / 5))

        # Identify concerns and recommendations
        concerns = self._identify_concerns(member_votes, overall_score)
        recommendations = self._generate_recommendations(member_votes)

        return CommitteeDecision(
            decision=decision,
            overall_score=round(overall_score, 2),
            consensus_level=round(consensus_level, 2),
            votes=member_votes,
            concerns=concerns,
            recommendations=recommendations,
            timestamp=datetime.now()
        )

    def _member_evaluate(self, member: CommitteeMember, item: Dict[str, Any]) -> tuple:
        """Simulate individual member evaluation based on expertise."""
        # Extract content strategy attributes
        topic_relevance = item.get("topic_relevance", 7.0)
        seo_potential = item.get("seo_potential", 7.0)
        audience_fit = item.get("audience_fit", 7.0)
        strategic_timing = item.get("strategic_timing", 7.0)
        gap_coverage = item.get("gap_coverage", 7.0)
        differentiation = item.get("differentiation", 7.0)

        # Each member weighs attributes differently
        if member.name == "Amanda":
            # Content Strategist - values alignment and gaps
            score = (topic_relevance * 0.3) + (gap_coverage * 0.3) + (strategic_timing * 0.4)
            feedback = self._amanda_feedback(score, topic_relevance, gap_coverage)

        elif member.name == "Zack":
            # SEO Specialist - values search potential
            score = (seo_potential * 0.6) + (topic_relevance * 0.2) + (differentiation * 0.2)
            feedback = self._zack_feedback(score, seo_potential, topic_relevance)

        elif member.name == "Morgan":
            # Audience Analyst - values audience fit
            score = (audience_fit * 0.5) + (topic_relevance * 0.3) + (gap_coverage * 0.2)
            feedback = self._morgan_feedback(score, audience_fit, topic_relevance)

        elif member.name == "Taylor":
            # Editorial Director - values quality and uniqueness
            score = (topic_relevance * 0.3) + (differentiation * 0.4) + (audience_fit * 0.3)
            feedback = self._taylor_feedback(score, differentiation, topic_relevance)

        else:  # Chris
            # Competitive Analyst - values gaps and positioning
            score = (gap_coverage * 0.4) + (differentiation * 0.4) + (seo_potential * 0.2)
            feedback = self._chris_feedback(score, gap_coverage, differentiation)

        return round(score, 1), feedback

    def _amanda_feedback(self, score: float, relevance: float, gaps: float) -> str:
        """Generate Amanda's content strategy feedback."""
        if score >= 8:
            return "Strategic fit - fills content gap, timely and relevant"
        elif score >= 6:
            return "Good topic but timing or gap-filling could improve"
        else:
            return "Strategy misalignment - doesn't fit content roadmap"

    def _zack_feedback(self, score: float, seo: float, relevance: float) -> str:
        """Generate Zack's SEO feedback."""
        if score >= 8:
            return "Excellent SEO - high volume, low competition keywords"
        elif score >= 6:
            return "Decent SEO potential but competitive landscape tough"
        else:
            return "Poor SEO - low search volume or too competitive"

    def _morgan_feedback(self, score: float, fit: float, relevance: float) -> str:
        """Generate Morgan's audience analysis feedback."""
        if score >= 8:
            return "Perfect audience fit - high engagement expected"
        elif score >= 6:
            return "Good match but not core audience priority"
        else:
            return "Audience mismatch - low engagement likely"

    def _taylor_feedback(self, score: float, diff: float, relevance: float) -> str:
        """Generate Taylor's editorial feedback."""
        if score >= 8:
            return "Unique angle - fresh perspective on important topic"
        elif score >= 6:
            return "Solid topic but needs more unique storytelling"
        else:
            return "Editorial concerns - overdone or lacking uniqueness"

    def _chris_feedback(self, score: float, gaps: float, diff: float) -> str:
        """Generate Chris's competitive analysis feedback."""
        if score >= 8:
            return "Market opportunity - clear gap, strong differentiation"
        elif score >= 6:
            return "Some competitive advantage but crowded space"
        else:
            return "Competitive issues - saturated or no differentiation"

    def _identify_concerns(self, votes: Dict, overall_score: float) -> List[str]:
        """Identify content strategy concerns requiring attention."""
        concerns = []

        # Check for split votes
        scores = [v["score"] for v in votes.values()]
        if max(scores) - min(scores) > 2:
            concerns.append("Split vote - strategy experts disagree on topic value")

        # Check for critical low scores
        for name, vote in votes.items():
            if vote["score"] < 5:
                concerns.append(f"{name} flagged critical issues ({vote['score']}/10)")

        return concerns

    def _generate_recommendations(self, votes: Dict) -> List[str]:
        """Generate actionable content strategy recommendations."""
        recommendations = []

        low_scores = {name: v for name, v in votes.items() if v["score"] < 7}

        if "Amanda" in low_scores:
            recommendations.append("Adjust timing or align better with content roadmap")

        if "Zack" in low_scores:
            recommendations.append("Target better keywords - lower competition, higher volume")

        if "Morgan" in low_scores:
            recommendations.append("Refocus on core audience pain points")

        if "Taylor" in low_scores:
            recommendations.append("Find unique angle - differentiate from existing content")

        if "Chris" in low_scores:
            recommendations.append("Identify competitive gaps - strengthen positioning")

        return recommendations

    def generate_report(self) -> str:
        """Generate human-readable content strategy report."""
        if not self.votes:
            return "No votes recorded. Call vote() first."

        decision = self.vote({})

        report = []
        report.append("=" * 60)
        report.append("CONTENT STRATEGY COMMITTEE REPORT")
        report.append("=" * 60)
        report.append(f"Timestamp: {decision.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Overall Score: {decision.overall_score}/10")
        report.append(f"Decision: {decision.decision.upper()}")
        report.append(f"Consensus Level: {int(decision.consensus_level * 100)}%")
        report.append("")
        report.append("MEMBER VOTES:")
        report.append("-" * 60)

        for name, vote in decision.votes.items():
            report.append(f"{name} ({int(vote['weight']*100)}% weight): {vote['score']}/10")
            report.append(f"  Feedback: {vote['feedback']}")
            report.append("")

        if decision.concerns:
            report.append("CONCERNS:")
            report.append("-" * 60)
            for concern in decision.concerns:
                report.append(f"[!] {concern}")
            report.append("")

        if decision.recommendations:
            report.append("RECOMMENDATIONS:")
            report.append("-" * 60)
            for rec in decision.recommendations:
                report.append(f"[>] {rec}")
            report.append("")

        report.append("=" * 60)

        return "\n".join(report)

    def get_consensus(self) -> float:
        """Return consensus level (0-1) from latest vote."""
        if not self.votes:
            return 0.0

        scores = [v.score for v in self.votes]
        avg_score = sum(scores) / len(scores)
        variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
        std_dev = variance ** 0.5

        return max(0, 1 - (std_dev / 5))

    def flag_concerns(self) -> List[str]:
        """Return list of content concerns from latest vote."""
        if not self.votes:
            return []

        decision = self.vote({})
        return decision.concerns


def main():
    """Demo: Content Strategy Committee voting on sample topic."""
    print("\n" + "=" * 60)
    print("CONTENT STRATEGY COMMITTEE DEMO")
    print("=" * 60 + "\n")

    committee = ContentStrategyCommittee()

    # Sample topic for review
    test_topic = {
        "title": "How to Troubleshoot Motor Overload Conditions",
        "topic_relevance": 9.0,
        "seo_potential": 7.5,  # Good but competitive
        "audience_fit": 9.0,
        "strategic_timing": 8.0,
        "gap_coverage": 7.0,
        "differentiation": 6.5  # Common topic, needs unique angle
    }

    print("Reviewing topic: {}".format(test_topic["title"]))
    print("\nAttributes:")
    for key, val in test_topic.items():
        if key != "title":
            print(f"  {key}: {val}/10")
    print("\n" + "-" * 60 + "\n")

    # Vote
    decision = committee.vote(test_topic)

    # Generate report
    print(committee.generate_report())

    # Show consensus analysis
    print("\nCONSENSUS ANALYSIS:")
    print(f"Agreement Level: {int(decision.consensus_level * 100)}%")
    if decision.consensus_level >= 0.8:
        print("[OK] Strong consensus - topic approved")
    elif decision.consensus_level >= 0.6:
        print("[~] Moderate consensus - refinement recommended")
    else:
        print("[X] Weak consensus - reconsider topic")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
