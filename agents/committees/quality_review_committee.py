"""
Quality Review Committee - Democratic video quality assessment system.

5 diverse members vote on video quality with weighted consensus.
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
    consensus_level: float  # 0-1 (percentage agreement)
    votes: Dict[str, Dict[str, Any]]
    concerns: List[str]
    recommendations: List[str]
    timestamp: datetime


class QualityReviewCommittee:
    """
    Quality Review Committee - Assesses video quality from 5 diverse perspectives.

    Members:
    - Marcus (Technician, 25%) - Veteran field tech, values practical accuracy
    - Aisha (Apprentice, 25%) - New to industry, needs clear explanations
    - Tom (Supervisor, 20%) - Manages teams, values efficiency
    - Priya (Student, 15%) - Learning fundamentals, needs basics
    - Carlos (Hobbyist, 15%) - Weekend warrior, values entertainment

    Voting:
    - 8.0+ → Approve
    - 6.0-7.9 → Flag for discussion
    - <6.0 → Reject
    """

    def __init__(self):
        """Initialize committee with 5 diverse members."""
        self.members = [
            CommitteeMember(
                name="Marcus",
                role="Veteran Technician",
                weight=0.25,
                background="25 years field experience, industrial maintenance",
                priorities=["practical_accuracy", "real_world_applicability", "safety"]
            ),
            CommitteeMember(
                name="Aisha",
                role="Apprentice",
                weight=0.25,
                background="6 months in industry, eager learner",
                priorities=["clarity", "step_by_step", "terminology_explained"]
            ),
            CommitteeMember(
                name="Tom",
                role="Maintenance Supervisor",
                weight=0.20,
                background="Manages 12-person team, budget responsibility",
                priorities=["efficiency", "team_training", "time_to_value"]
            ),
            CommitteeMember(
                name="Priya",
                role="Trade School Student",
                weight=0.15,
                background="First-year student, no prior experience",
                priorities=["fundamentals", "examples", "practice_opportunities"]
            ),
            CommitteeMember(
                name="Carlos",
                role="Hobbyist",
                weight=0.15,
                background="Weekend DIY enthusiast, home automation projects",
                priorities=["entertainment", "engagement", "accessibility"]
            )
        ]

        self.votes: List[Vote] = []

    def vote(self, item: Dict[str, Any]) -> CommitteeDecision:
        """
        Committee votes on video quality.

        Args:
            item: Video content to review (script, visuals, pacing, etc.)

        Returns:
            CommitteeDecision with weighted consensus
        """
        self.votes = []
        member_votes = {}

        # Each member evaluates based on their priorities
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

        # Calculate consensus (how close are the scores?)
        scores = [v.score for v in self.votes]
        avg_score = sum(scores) / len(scores)
        variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
        std_dev = variance ** 0.5
        consensus_level = max(0, 1 - (std_dev / 5))  # Normalize to 0-1

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
        """
        Simulate individual member evaluation.

        In production, this would use LLM to evaluate based on member's perspective.
        For demo, uses heuristics.
        """
        # Extract video attributes
        script_quality = item.get("script_quality", 7.0)
        visual_quality = item.get("visual_quality", 7.0)
        pacing = item.get("pacing", 7.0)
        clarity = item.get("clarity", 7.0)
        accuracy = item.get("accuracy", 7.0)
        engagement = item.get("engagement", 7.0)

        # Each member weighs attributes differently
        if member.name == "Marcus":
            # Values accuracy and real-world applicability
            score = (accuracy * 0.5) + (script_quality * 0.3) + (visual_quality * 0.2)
            feedback = self._marcus_feedback(score, accuracy, script_quality)

        elif member.name == "Aisha":
            # Values clarity and step-by-step explanations
            score = (clarity * 0.5) + (pacing * 0.3) + (script_quality * 0.2)
            feedback = self._aisha_feedback(score, clarity, pacing)

        elif member.name == "Tom":
            # Values efficiency and training effectiveness
            score = (script_quality * 0.4) + (pacing * 0.3) + (clarity * 0.3)
            feedback = self._tom_feedback(score, pacing, script_quality)

        elif member.name == "Priya":
            # Values fundamentals and examples
            score = (clarity * 0.4) + (script_quality * 0.4) + (visual_quality * 0.2)
            feedback = self._priya_feedback(score, clarity, script_quality)

        else:  # Carlos
            # Values entertainment and accessibility
            score = (engagement * 0.5) + (visual_quality * 0.3) + (clarity * 0.2)
            feedback = self._carlos_feedback(score, engagement, visual_quality)

        return round(score, 1), feedback

    def _marcus_feedback(self, score: float, accuracy: float, script: float) -> str:
        """Generate Marcus's feedback based on his priorities."""
        if score >= 8:
            return "Practical and accurate. Field techs will appreciate this."
        elif score >= 6:
            return "Good technical content but could use more real-world examples."
        else:
            return "Missing critical safety information. Needs field-tested procedures."

    def _aisha_feedback(self, score: float, clarity: float, pacing: float) -> str:
        """Generate Aisha's feedback based on her priorities."""
        if score >= 8:
            return "Clear explanations. I understood every step."
        elif score >= 6:
            return "Good but a bit fast. Could benefit from slower pacing."
        else:
            return "Too many assumptions about prior knowledge. Need more basics."

    def _tom_feedback(self, score: float, pacing: float, script: float) -> str:
        """Generate Tom's feedback based on his priorities."""
        if score >= 8:
            return "Efficient presentation. Good for team training."
        elif score >= 6:
            return "Solid content but could be more concise for shop floor."
        else:
            return "Too theoretical. Need actionable steps for busy technicians."

    def _priya_feedback(self, score: float, clarity: float, script: float) -> str:
        """Generate Priya's feedback based on her priorities."""
        if score >= 8:
            return "Clear fundamentals. Great learning resource."
        elif score >= 6:
            return "Good basics but examples could be simpler."
        else:
            return "Assumes too much background. Need prerequisite review."

    def _carlos_feedback(self, score: float, engagement: float, visual: float) -> str:
        """Generate Carlos's feedback based on his priorities."""
        if score >= 8:
            return "Engaging and fun! Would share with friends."
        elif score >= 6:
            return "Informative but could be more entertaining."
        else:
            return "Too dry. Needs more visual interest and storytelling."

    def _identify_concerns(self, votes: Dict, overall_score: float) -> List[str]:
        """Identify split votes or low scores requiring attention."""
        concerns = []

        # Check for split votes (variance > 2 points)
        scores = [v["score"] for v in votes.values()]
        if max(scores) - min(scores) > 2:
            concerns.append("Split vote - significant disagreement among members")

        # Check for any member scoring below 5
        for name, vote in votes.items():
            if vote["score"] < 5:
                concerns.append(f"{name} scored very low ({vote['score']}) - critical issues")

        return concerns

    def _generate_recommendations(self, votes: Dict) -> List[str]:
        """Generate actionable recommendations based on feedback."""
        recommendations = []

        # Analyze common themes
        low_scores = {name: v for name, v in votes.items() if v["score"] < 7}

        if "Aisha" in low_scores:
            recommendations.append("Consider slower pacing for beginners")

        if "Marcus" in low_scores:
            recommendations.append("Add more real-world field examples")

        if "Tom" in low_scores:
            recommendations.append("Tighten presentation for efficiency")

        if "Priya" in low_scores:
            recommendations.append("Review prerequisites and add fundamentals")

        if "Carlos" in low_scores:
            recommendations.append("Increase visual engagement and storytelling")

        return recommendations

    def generate_report(self) -> str:
        """Generate human-readable committee report."""
        if not self.votes:
            return "No votes recorded. Call vote() first."

        decision = self.vote({})  # Get latest decision

        report = []
        report.append("=" * 60)
        report.append("QUALITY REVIEW COMMITTEE REPORT")
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
        """Return list of concerns from latest vote."""
        if not self.votes:
            return []

        decision = self.vote({})
        return decision.concerns


def main():
    """Demo: Quality Review Committee voting on sample video."""
    print("\n" + "=" * 60)
    print("QUALITY REVIEW COMMITTEE DEMO")
    print("=" * 60 + "\n")

    committee = QualityReviewCommittee()

    # Sample video for review
    test_video = {
        "title": "Basic Motor Control - Start/Stop Circuit",
        "script_quality": 8.0,
        "visual_quality": 7.5,
        "pacing": 7.0,  # Slightly fast
        "clarity": 8.5,
        "accuracy": 9.0,
        "engagement": 7.0
    }

    print("Reviewing video: {}".format(test_video["title"]))
    print("\nAttributes:")
    for key, val in test_video.items():
        if key != "title":
            print(f"  {key}: {val}/10")
    print("\n" + "-" * 60 + "\n")

    # Vote
    decision = committee.vote(test_video)

    # Generate report
    print(committee.generate_report())

    # Show consensus analysis
    print("\nCONSENSUS ANALYSIS:")
    print(f"Agreement Level: {int(decision.consensus_level * 100)}%")
    if decision.consensus_level >= 0.8:
        print("[OK] Strong consensus - committee aligned")
    elif decision.consensus_level >= 0.6:
        print("[~] Moderate consensus - some disagreement")
    else:
        print("[X] Weak consensus - significant split")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
