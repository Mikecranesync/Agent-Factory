"""
Analytics Committee - Democratic data analysis and optimization assessment system.

5 analytics experts vote on optimization decisions with weighted consensus.
Focus: Metric interpretation, trend analysis, optimization, A/B tests, forecasting.
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


class AnalyticsCommittee:
    """
    Analytics Committee - Assesses optimization decisions from 5 expert perspectives.

    Members:
    - Alex (Data Scientist, 25%) - Statistical analysis and modeling
    - Jordan (Growth Analyst, 25%) - Growth metrics and experimentation
    - Riley (Business Intelligence, 20%) - KPIs and business impact
    - Sam (User Behavior Analyst, 15%) - User patterns and engagement
    - Casey (Predictive Analyst, 15%) - Forecasting and trend prediction

    Focus Areas:
    - Metric interpretation and statistical significance
    - Trend identification and pattern recognition
    - Optimization recommendations and priority
    - A/B test analysis and decision-making
    - Performance forecasting and modeling

    Voting:
    - 8.0+ → Approve
    - 6.0-7.9 → Flag for discussion
    - <6.0 → Reject
    """

    def __init__(self):
        """Initialize committee with 5 analytics experts."""
        self.members = [
            CommitteeMember(
                name="Alex",
                role="Data Scientist",
                weight=0.25,
                background="PhD Statistics, 8 years ML and analytics",
                priorities=["statistical_rigor", "methodology", "significance", "accuracy"]
            ),
            CommitteeMember(
                name="Jordan",
                role="Growth Analyst",
                weight=0.25,
                background="Growth hacking and experimentation expert",
                priorities=["growth_impact", "experiments", "iteration", "velocity"]
            ),
            CommitteeMember(
                name="Riley",
                role="Business Intelligence",
                weight=0.20,
                background="BI and KPI tracking specialist",
                priorities=["business_impact", "KPIs", "ROI", "actionability"]
            ),
            CommitteeMember(
                name="Sam",
                role="User Behavior Analyst",
                weight=0.15,
                background="User analytics and behavioral psychology",
                priorities=["user_patterns", "engagement", "retention", "behavior"]
            ),
            CommitteeMember(
                name="Casey",
                role="Predictive Analyst",
                weight=0.15,
                background="Forecasting and predictive modeling",
                priorities=["trends", "forecasting", "prediction", "modeling"]
            )
        ]

        self.votes: List[Vote] = []

    def vote(self, item: Dict[str, Any]) -> CommitteeDecision:
        """
        Committee votes on analytics/optimization decision.

        Args:
            item: Analytics decision to review (metrics, optimization, tests, etc.)

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
        # Extract analytics attributes
        statistical_rigor = item.get("statistical_rigor", 7.0)
        business_impact = item.get("business_impact", 7.0)
        trend_clarity = item.get("trend_clarity", 7.0)
        actionability = item.get("actionability", 7.0)
        predictive_value = item.get("predictive_value", 7.0)
        user_insight = item.get("user_insight", 7.0)

        # Each member weighs attributes differently
        if member.name == "Alex":
            # Data Scientist - values statistical rigor
            score = (statistical_rigor * 0.5) + (trend_clarity * 0.3) + (actionability * 0.2)
            feedback = self._alex_feedback(score, statistical_rigor, trend_clarity)

        elif member.name == "Jordan":
            # Growth Analyst - values growth impact
            score = (business_impact * 0.4) + (actionability * 0.4) + (statistical_rigor * 0.2)
            feedback = self._jordan_feedback(score, business_impact, actionability)

        elif member.name == "Riley":
            # BI Specialist - values business impact and KPIs
            score = (business_impact * 0.5) + (actionability * 0.3) + (trend_clarity * 0.2)
            feedback = self._riley_feedback(score, business_impact, actionability)

        elif member.name == "Sam":
            # User Behavior Analyst - values user insights
            score = (user_insight * 0.5) + (trend_clarity * 0.3) + (actionability * 0.2)
            feedback = self._sam_feedback(score, user_insight, trend_clarity)

        else:  # Casey
            # Predictive Analyst - values forecasting value
            score = (predictive_value * 0.5) + (trend_clarity * 0.3) + (statistical_rigor * 0.2)
            feedback = self._casey_feedback(score, predictive_value, trend_clarity)

        return round(score, 1), feedback

    def _alex_feedback(self, score: float, rigor: float, clarity: float) -> str:
        """Generate Alex's data science feedback."""
        if score >= 8:
            return "Statistically sound - rigorous methodology, clear signals"
        elif score >= 6:
            return "Decent analysis but needs larger sample or better controls"
        else:
            return "Statistical concerns - insufficient data or flawed methodology"

    def _jordan_feedback(self, score: float, impact: float, action: float) -> str:
        """Generate Jordan's growth analysis feedback."""
        if score >= 8:
            return "High-impact opportunity - actionable and growth-driving"
        elif score >= 6:
            return "Good insight but ROI unclear or execution challenging"
        else:
            return "Low growth potential - resource investment not justified"

    def _riley_feedback(self, score: float, impact: float, action: float) -> str:
        """Generate Riley's business intelligence feedback."""
        if score >= 8:
            return "Clear business value - moves key KPIs, highly actionable"
        elif score >= 6:
            return "Positive KPI impact but implementation complexity high"
        else:
            return "Business case weak - unclear ROI or misaligned KPIs"

    def _sam_feedback(self, score: float, insight: float, clarity: float) -> str:
        """Generate Sam's user behavior feedback."""
        if score >= 8:
            return "Strong user insight - clear patterns, engagement opportunity"
        elif score >= 6:
            return "Interesting behavior pattern but causation unclear"
        else:
            return "User insight lacking - correlation without understanding"

    def _casey_feedback(self, score: float, predictive: float, clarity: float) -> str:
        """Generate Casey's predictive analysis feedback."""
        if score >= 8:
            return "Excellent predictive power - trend clear, forecast reliable"
        elif score >= 6:
            return "Some predictive value but high uncertainty or volatility"
        else:
            return "Forecasting unreliable - trend noise or insufficient history"

    def _identify_concerns(self, votes: Dict, overall_score: float) -> List[str]:
        """Identify analytics concerns requiring attention."""
        concerns = []

        # Check for split votes
        scores = [v["score"] for v in votes.values()]
        if max(scores) - min(scores) > 2:
            concerns.append("Split vote - analytics experts disagree on interpretation")

        # Check for critical low scores
        for name, vote in votes.items():
            if vote["score"] < 5:
                concerns.append(f"{name} flagged critical data issues ({vote['score']}/10)")

        return concerns

    def _generate_recommendations(self, votes: Dict) -> List[str]:
        """Generate actionable analytics recommendations."""
        recommendations = []

        low_scores = {name: v for name, v in votes.items() if v["score"] < 7}

        if "Alex" in low_scores:
            recommendations.append("Improve statistical rigor - larger sample or better controls")

        if "Jordan" in low_scores:
            recommendations.append("Clarify growth impact - quantify ROI and priority")

        if "Riley" in low_scores:
            recommendations.append("Strengthen business case - align with key KPIs")

        if "Sam" in low_scores:
            recommendations.append("Deepen user insights - understand causation not just correlation")

        if "Casey" in low_scores:
            recommendations.append("Enhance forecasting - extend data history or reduce volatility")

        return recommendations

    def generate_report(self) -> str:
        """Generate human-readable analytics committee report."""
        if not self.votes:
            return "No votes recorded. Call vote() first."

        decision = self.vote({})

        report = []
        report.append("=" * 60)
        report.append("ANALYTICS COMMITTEE REPORT")
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
        """Return list of analytics concerns from latest vote."""
        if not self.votes:
            return []

        decision = self.vote({})
        return decision.concerns


def main():
    """Demo: Analytics Committee voting on sample optimization."""
    print("\n" + "=" * 60)
    print("ANALYTICS COMMITTEE DEMO")
    print("=" * 60 + "\n")

    committee = AnalyticsCommittee()

    # Sample optimization decision for review
    test_optimization = {
        "title": "Increase video thumbnail brightness for higher CTR",
        "statistical_rigor": 8.0,
        "business_impact": 9.0,  # High impact on CTR
        "trend_clarity": 8.5,
        "actionability": 9.0,
        "predictive_value": 7.5,
        "user_insight": 8.0
    }

    print("Reviewing optimization: {}".format(test_optimization["title"]))
    print("\nAttributes:")
    for key, val in test_optimization.items():
        if key != "title":
            print(f"  {key}: {val}/10")
    print("\n" + "-" * 60 + "\n")

    # Vote
    decision = committee.vote(test_optimization)

    # Generate report
    print(committee.generate_report())

    # Show consensus analysis
    print("\nCONSENSUS ANALYSIS:")
    print(f"Agreement Level: {int(decision.consensus_level * 100)}%")
    if decision.consensus_level >= 0.8:
        print("[OK] Strong consensus - proceed with optimization")
    elif decision.consensus_level >= 0.6:
        print("[~] Moderate consensus - gather more data")
    else:
        print("[X] Weak consensus - reconsider approach")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
