"""
Design Committee - Democratic visual design assessment system.

5 members vote on visual design quality with weighted consensus.
Focus: Thumbnails, colors, typography, hierarchy, brand alignment.
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


class DesignCommittee:
    """
    Design Committee - Assesses visual design from 5 expert perspectives.

    Members:
    - Sarah (UX Designer, 25%) - User experience and accessibility expert
    - Jake (Brand Director, 25%) - Brand consistency and visual identity
    - Mei (Art Director, 20%) - Visual hierarchy and composition
    - Raj (Typographer, 15%) - Typography and readability
    - Elena (Color Specialist, 15%) - Color theory and psychology

    Focus Areas:
    - Thumbnail clarity and click-through appeal
    - Color scheme consistency and accessibility
    - Typography readability and hierarchy
    - Visual hierarchy and information flow
    - Brand alignment and recognition

    Voting:
    - 8.0+ → Approve
    - 6.0-7.9 → Flag for discussion
    - <6.0 → Reject
    """

    def __init__(self):
        """Initialize committee with 5 design experts."""
        self.members = [
            CommitteeMember(
                name="Sarah",
                role="UX Designer",
                weight=0.25,
                background="10 years UX design, accessibility specialist",
                priorities=["user_experience", "accessibility", "clarity", "conversion"]
            ),
            CommitteeMember(
                name="Jake",
                role="Brand Director",
                weight=0.25,
                background="Brand strategy and visual identity expert",
                priorities=["brand_consistency", "recognition", "differentiation"]
            ),
            CommitteeMember(
                name="Mei",
                role="Art Director",
                weight=0.20,
                background="15 years editorial and digital design",
                priorities=["composition", "visual_hierarchy", "balance", "impact"]
            ),
            CommitteeMember(
                name="Raj",
                role="Typographer",
                weight=0.15,
                background="Typography and editorial design specialist",
                priorities=["readability", "font_pairing", "type_hierarchy"]
            ),
            CommitteeMember(
                name="Elena",
                role="Color Specialist",
                weight=0.15,
                background="Color theory and psychology expert",
                priorities=["color_harmony", "contrast", "emotional_impact"]
            )
        ]

        self.votes: List[Vote] = []

    def vote(self, item: Dict[str, Any]) -> CommitteeDecision:
        """
        Committee votes on design quality.

        Args:
            item: Design elements to review (thumbnail, colors, typography, etc.)

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
        # Extract design attributes
        thumbnail_clarity = item.get("thumbnail_clarity", 7.0)
        color_harmony = item.get("color_harmony", 7.0)
        typography = item.get("typography", 7.0)
        visual_hierarchy = item.get("visual_hierarchy", 7.0)
        brand_alignment = item.get("brand_alignment", 7.0)
        accessibility = item.get("accessibility", 7.0)

        # Each member weighs attributes differently
        if member.name == "Sarah":
            # UX Designer - values clarity and accessibility
            score = (accessibility * 0.4) + (thumbnail_clarity * 0.3) + (visual_hierarchy * 0.3)
            feedback = self._sarah_feedback(score, accessibility, thumbnail_clarity)

        elif member.name == "Jake":
            # Brand Director - values consistency and recognition
            score = (brand_alignment * 0.5) + (color_harmony * 0.3) + (typography * 0.2)
            feedback = self._jake_feedback(score, brand_alignment, color_harmony)

        elif member.name == "Mei":
            # Art Director - values composition and hierarchy
            score = (visual_hierarchy * 0.4) + (thumbnail_clarity * 0.3) + (color_harmony * 0.3)
            feedback = self._mei_feedback(score, visual_hierarchy, thumbnail_clarity)

        elif member.name == "Raj":
            # Typographer - values readability and type choices
            score = (typography * 0.6) + (visual_hierarchy * 0.2) + (accessibility * 0.2)
            feedback = self._raj_feedback(score, typography, accessibility)

        else:  # Elena
            # Color Specialist - values harmony and contrast
            score = (color_harmony * 0.5) + (accessibility * 0.3) + (brand_alignment * 0.2)
            feedback = self._elena_feedback(score, color_harmony, accessibility)

        return round(score, 1), feedback

    def _sarah_feedback(self, score: float, accessibility: float, clarity: float) -> str:
        """Generate Sarah's UX-focused feedback."""
        if score >= 8:
            return "Excellent UX - clear, accessible, high conversion potential"
        elif score >= 6:
            return "Good usability but accessibility could improve"
        else:
            return "UX issues - poor contrast or confusing layout"

    def _jake_feedback(self, score: float, brand: float, color: float) -> str:
        """Generate Jake's brand-focused feedback."""
        if score >= 8:
            return "Strong brand alignment - instantly recognizable"
        elif score >= 6:
            return "On-brand but could be more distinctive"
        else:
            return "Brand inconsistency - doesn't match visual identity"

    def _mei_feedback(self, score: float, hierarchy: float, clarity: float) -> str:
        """Generate Mei's composition-focused feedback."""
        if score >= 8:
            return "Excellent composition - clear hierarchy and balance"
        elif score >= 6:
            return "Good layout but hierarchy could be stronger"
        else:
            return "Composition issues - cluttered or unbalanced"

    def _raj_feedback(self, score: float, typography: float, accessibility: float) -> str:
        """Generate Raj's typography-focused feedback."""
        if score >= 8:
            return "Perfect typography - readable and well-paired"
        elif score >= 6:
            return "Decent type choices but readability suffers"
        else:
            return "Typography problems - poor fonts or spacing"

    def _elena_feedback(self, score: float, color: float, accessibility: float) -> str:
        """Generate Elena's color-focused feedback."""
        if score >= 8:
            return "Beautiful color palette - harmonious and accessible"
        elif score >= 6:
            return "Nice colors but contrast needs adjustment"
        else:
            return "Color issues - poor harmony or accessibility"

    def _identify_concerns(self, votes: Dict, overall_score: float) -> List[str]:
        """Identify design concerns requiring attention."""
        concerns = []

        # Check for split votes
        scores = [v["score"] for v in votes.values()]
        if max(scores) - min(scores) > 2:
            concerns.append("Split vote - design experts disagree significantly")

        # Check for critical low scores
        for name, vote in votes.items():
            if vote["score"] < 5:
                concerns.append(f"{name} flagged critical issues ({vote['score']}/10)")

        return concerns

    def _generate_recommendations(self, votes: Dict) -> List[str]:
        """Generate actionable design recommendations."""
        recommendations = []

        low_scores = {name: v for name, v in votes.items() if v["score"] < 7}

        if "Sarah" in low_scores:
            recommendations.append("Improve accessibility - check contrast ratios (WCAG 2.1)")

        if "Jake" in low_scores:
            recommendations.append("Strengthen brand consistency - align with style guide")

        if "Mei" in low_scores:
            recommendations.append("Refine visual hierarchy - clarify information flow")

        if "Raj" in low_scores:
            recommendations.append("Improve typography - increase readability")

        if "Elena" in low_scores:
            recommendations.append("Adjust color palette - enhance harmony or contrast")

        return recommendations

    def generate_report(self) -> str:
        """Generate human-readable design committee report."""
        if not self.votes:
            return "No votes recorded. Call vote() first."

        # Get latest decision (re-vote to get full decision object)
        decision = self.vote({})

        report = []
        report.append("=" * 60)
        report.append("DESIGN COMMITTEE REPORT")
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
        """Return list of design concerns from latest vote."""
        if not self.votes:
            return []

        decision = self.vote({})
        return decision.concerns


def main():
    """Demo: Design Committee voting on sample thumbnail."""
    print("\n" + "=" * 60)
    print("DESIGN COMMITTEE DEMO")
    print("=" * 60 + "\n")

    committee = DesignCommittee()

    # Sample thumbnail design for review
    test_design = {
        "title": "PLC Basics - Motor Control Thumbnail",
        "thumbnail_clarity": 8.5,
        "color_harmony": 7.0,  # Slightly off-brand
        "typography": 9.0,
        "visual_hierarchy": 8.0,
        "brand_alignment": 6.5,  # Needs improvement
        "accessibility": 8.5
    }

    print("Reviewing design: {}".format(test_design["title"]))
    print("\nAttributes:")
    for key, val in test_design.items():
        if key != "title":
            print(f"  {key}: {val}/10")
    print("\n" + "-" * 60 + "\n")

    # Vote
    decision = committee.vote(test_design)

    # Generate report
    print(committee.generate_report())

    # Show consensus analysis
    print("\nCONSENSUS ANALYSIS:")
    print(f"Agreement Level: {int(decision.consensus_level * 100)}%")
    if decision.consensus_level >= 0.8:
        print("[OK] Strong consensus - design approved")
    elif decision.consensus_level >= 0.6:
        print("[~] Moderate consensus - minor refinements needed")
    else:
        print("[X] Weak consensus - major design revision required")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
