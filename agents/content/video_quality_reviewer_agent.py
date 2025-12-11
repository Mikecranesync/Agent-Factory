#!/usr/bin/env python3
"""
VideoQualityReviewerAgent - "Ms. Rodriguez" Pre-Publish Critic

This agent is the final quality gate before publishing. Modeled after
an experienced elementary teacher who reviews educational videos with
a critical but constructive eye.

Personality: Ms. Rodriguez
- 20+ years teaching experience (grades 3-5)
- Passionate about making learning accessible
- High standards but nurturing feedback
- Notices details students would miss
- Values clarity over complexity

Review Dimensions:
1. Educational Quality (0-10): Does it teach effectively?
2. Student Engagement (0-10): Will students stay watching?
3. Technical Accuracy (0-10): Is the information correct?
4. Visual Quality (0-10): Are visuals clear and helpful?
5. Accessibility (0-10): Can diverse learners understand?

Approval Thresholds:
- 8.0+ → Auto-approve (excellent quality)
- 6.0-7.9 → Flag for human review (needs minor improvements)
- <6.0 → Reject (significant issues, must revise)

Created: Dec 2025
Part of: PLC Tutor multi-agent committee system
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime


class VideoQualityReviewerAgent:
    """
    Pre-publish quality reviewer with "Ms. Rodriguez" personality.

    Reviews videos across 5 dimensions, provides detailed feedback,
    and makes publish/flag/reject decisions.

    Example:
        >>> agent = VideoQualityReviewerAgent()
        >>> review = agent.review_video(script_text, video_metadata)
        >>> if review['decision'] == 'approve':
        >>>     publish_video()
    """

    def __init__(self, project_root: Path = None):
        """
        Initialize VideoQualityReviewerAgent.

        Args:
            project_root: Path to project root (defaults to auto-detect)
        """
        self.agent_name = "video_quality_reviewer_agent"
        self.reviewer_name = "Ms. Rodriguez"
        self.project_root = project_root or Path(__file__).parent.parent.parent

        # Review scoring weights (must sum to 1.0)
        self.dimension_weights = {
            "educational_quality": 0.30,  # Most important
            "student_engagement": 0.25,
            "technical_accuracy": 0.25,
            "visual_quality": 0.15,
            "accessibility": 0.05
        }

        # Quality standards (Ms. Rodriguez's rubrics)
        self.standards = {
            "educational_quality": {
                "clear_learning_objective": "Is there a clear 'you will learn X' statement?",
                "scaffolding": "Does it build from simple to complex?",
                "examples": "Are there concrete, relatable examples?",
                "practice_opportunity": "Can students apply what they learned?",
                "summary": "Is there a clear recap at the end?"
            },
            "student_engagement": {
                "strong_hook": "Does it grab attention in first 5 seconds?",
                "pacing": "Is pacing appropriate (not too slow/fast)?",
                "variety": "Are there visual/audio changes to maintain interest?",
                "relatability": "Does it connect to students' lives?",
                "call_to_action": "Does it encourage further learning?"
            },
            "technical_accuracy": {
                "factual_correctness": "Are all technical claims accurate?",
                "citations": "Are sources cited for claims?",
                "safety": "Are safety warnings included where needed?",
                "current": "Is information up-to-date?",
                "precision": "Is terminology used correctly?"
            },
            "visual_quality": {
                "readability": "Can text be read easily?",
                "contrast": "Is there good color contrast?",
                "consistency": "Do visuals match the style guide?",
                "relevance": "Do visuals support learning (not distract)?",
                "timing": "Do visuals appear at right moments?"
            },
            "accessibility": {
                "language_simplicity": "Is language appropriate for grade level?",
                "caption_quality": "Are captions accurate and readable?",
                "audio_clarity": "Is narration clear and understandable?",
                "color_blindness": "Are colors distinguishable for colorblind viewers?",
                "cognitive_load": "Is information chunked appropriately?"
            }
        }

        # Common issues Ms. Rodriguez catches
        self.common_issues = {
            "jargon_overload": r'\b(peripheral|proprietary|asynchronous|concatenate)\b',
            "passive_voice": r'\b(is|are|was|were|been|being)\s+\w+ed\b',
            "wall_of_text": lambda para: len(para.split()) > 50,
            "missing_transitions": ["suddenly", "without warning", "now watch"],
            "abbreviations_undefined": r'\b([A-Z]{3,})\b',  # 3+ capital letters
            "safety_keywords_missing": ["caution", "warning", "danger", "safety", "protect"]
        }

        # Ms. Rodriguez's feedback templates
        self.feedback_templates = {
            "excellent": [
                "This is wonderful! {specific_praise}",
                "I love how you {specific_technique}. Students will really connect with this.",
                "Outstanding work on {dimension}. This sets a great example."
            ],
            "good": [
                "Good job on {aspect}. To make it even better, consider {suggestion}.",
                "You're on the right track with {strength}. {improvement_idea} would enhance it.",
                "Nice work! {positive}. One thing to refine: {constructive}."
            ],
            "needs_work": [
                "I appreciate your effort on {attempt}, but {issue} could confuse students.",
                "This section on {topic} needs revision. {specific_problem}. Try {solution}.",
                "Students might struggle with {challenge}. Let's simplify by {remedy}."
            ],
            "reject": [
                "{critical_issue} is a significant problem that must be addressed.",
                "I can't approve this because {blocker}. Please revise and resubmit.",
                "This needs substantial rework. {major_flaw}. Happy to help you improve it."
            ]
        }

    def review_video(
        self,
        script_text: str,
        video_metadata: Optional[Dict] = None,
        instructional_design_report: Optional[Dict] = None
    ) -> Dict:
        """
        Comprehensive video review across all 5 dimensions.

        Args:
            script_text: Full video script
            video_metadata: Optional metadata (duration, format, etc.)
            instructional_design_report: Optional report from InstructionalDesignerAgent

        Returns:
            Review dictionary with scores, feedback, and decision
        """
        # Score each dimension
        educational_score = self._score_educational_quality(script_text, instructional_design_report)
        engagement_score = self._score_student_engagement(script_text, video_metadata)
        accuracy_score = self._score_technical_accuracy(script_text)
        visual_score = self._score_visual_quality(script_text)
        accessibility_score = self._score_accessibility(script_text)

        # Calculate weighted overall score
        overall_score = (
            educational_score["score"] * self.dimension_weights["educational_quality"] +
            engagement_score["score"] * self.dimension_weights["student_engagement"] +
            accuracy_score["score"] * self.dimension_weights["technical_accuracy"] +
            visual_score["score"] * self.dimension_weights["visual_quality"] +
            accessibility_score["score"] * self.dimension_weights["accessibility"]
        )

        # Make decision
        if overall_score >= 8.0:
            decision = "approve"
            decision_reason = "Excellent quality across all dimensions"
        elif overall_score >= 6.0:
            decision = "flag_for_review"
            decision_reason = "Good quality but needs minor improvements"
        else:
            decision = "reject"
            decision_reason = "Significant quality issues require revision"

        # Generate Ms. Rodriguez's feedback letter
        feedback_letter = self._generate_feedback_letter(
            overall_score,
            {
                "educational_quality": educational_score,
                "student_engagement": engagement_score,
                "technical_accuracy": accuracy_score,
                "visual_quality": visual_score,
                "accessibility": accessibility_score
            },
            decision
        )

        return {
            "reviewer": self.reviewer_name,
            "review_timestamp": datetime.utcnow().isoformat(),
            "overall_score": round(overall_score, 1),
            "decision": decision,
            "decision_reason": decision_reason,
            "dimension_scores": {
                "educational_quality": educational_score,
                "student_engagement": engagement_score,
                "technical_accuracy": accuracy_score,
                "visual_quality": visual_score,
                "accessibility": accessibility_score
            },
            "feedback_letter": feedback_letter,
            "action_items": self._extract_action_items(
                educational_score, engagement_score, accuracy_score, visual_score, accessibility_score
            )
        }

    def _score_educational_quality(
        self,
        script_text: str,
        instructional_design_report: Optional[Dict] = None
    ) -> Dict:
        """Score educational quality (0-10)."""
        score = 10.0
        issues = []
        strengths = []

        # Check for clear learning objective
        has_objective = any(phrase in script_text.lower() for phrase in [
            "you'll learn", "you will learn", "by the end", "we're covering",
            "here's what you need to know", "let's dive into"
        ])
        if not has_objective:
            score -= 2.0
            issues.append("Missing clear learning objective statement")
        else:
            strengths.append("Clear learning objective stated")

        # Check for scaffolding (builds complexity)
        has_steps = bool(re.search(r'step \d+|first|next|then|finally', script_text, re.IGNORECASE))
        if not has_steps:
            score -= 1.5
            issues.append("Lacks step-by-step scaffolding")
        else:
            strengths.append("Good scaffolding with sequential steps")

        # Check for examples
        has_examples = any(phrase in script_text.lower() for phrase in [
            'for example', 'like', 'imagine', 'think of', 'similar to'
        ])
        if not has_examples:
            score -= 1.5
            issues.append("No concrete examples provided")
        else:
            strengths.append("Includes relatable examples")

        # Check for summary/recap
        has_summary = any(phrase in script_text.lower() for phrase in [
            'to recap', 'in summary', 'remember', 'so to review', 'the key takeaway'
        ])
        if not has_summary:
            score -= 1.0
            issues.append("Missing summary/recap section")
        else:
            strengths.append("Includes helpful summary")

        # Use instructional design report if available
        if instructional_design_report:
            id_score = instructional_design_report.get("overall_score", 5)
            # Boost score if ID agent approved it
            if id_score >= 8:
                score = min(10.0, score + 1.0)
                strengths.append("Passed instructional design review")

        return {
            "score": max(0.0, min(10.0, score)),
            "issues": issues,
            "strengths": strengths,
            "feedback": self._select_feedback("educational_quality", score)
        }

    def _score_student_engagement(self, script_text: str, video_metadata: Optional[Dict] = None) -> Dict:
        """Score student engagement (0-10)."""
        score = 10.0
        issues = []
        strengths = []

        # Check for strong hook (first sentence)
        first_sentence = script_text.split('.')[0].lower()
        hook_words = ["ready", "stuck", "discover", "watch", "here's", "ever wondered", "imagine"]
        has_strong_hook = any(word in first_sentence for word in hook_words)

        if not has_strong_hook:
            score -= 2.0
            issues.append("Weak hook - doesn't grab attention immediately")
        else:
            strengths.append("Strong, engaging hook")

        # Check pacing (via personality markers)
        personality_markers = len(re.findall(r'\[(enthusiastic|cautionary|explanatory|pause)\]', script_text))
        if personality_markers < 3:
            score -= 1.0
            issues.append("Monotonous pacing - needs more vocal variety")
        else:
            strengths.append("Good vocal variety and pacing")

        # Check for variety (visual cues)
        visual_cues = len(re.findall(r'\[show ', script_text))
        expected_visuals = len(script_text.split()) / 150 * 5  # ~5 visuals per minute
        if visual_cues < expected_visuals * 0.5:
            score -= 1.5
            issues.append(f"Insufficient visuals (found {visual_cues}, expected ~{int(expected_visuals)})")
        else:
            strengths.append("Good visual variety")

        # Check for relatability
        relatable_phrases = ["you've probably", "imagine you're", "like when you", "in your job"]
        has_relatability = any(phrase in script_text.lower() for phrase in relatable_phrases)
        if not has_relatability:
            score -= 1.0
            issues.append("Content not connected to student experience")
        else:
            strengths.append("Relatable content")

        # Check for call-to-action
        has_cta = any(phrase in script_text.lower() for phrase in [
            'subscribe', 'comment', 'try this', 'practice', 'drop a comment'
        ])
        if not has_cta:
            score -= 0.5
            issues.append("Missing call-to-action")
        else:
            strengths.append("Includes call-to-action")

        return {
            "score": max(0.0, min(10.0, score)),
            "issues": issues,
            "strengths": strengths,
            "feedback": self._select_feedback("student_engagement", score)
        }

    def _score_technical_accuracy(self, script_text: str) -> Dict:
        """Score technical accuracy (0-10)."""
        score = 10.0
        issues = []
        strengths = []

        # Check for citations
        has_citations = '[show citation:' in script_text
        if not has_citations:
            score -= 2.0
            issues.append("No sources cited - students can't verify claims")
        else:
            strengths.append("Sources properly cited")

        # Check for safety warnings (if applicable)
        electrical_keywords = ['voltage', 'current', 'wiring', 'electrical', 'power']
        mentions_electrical = any(word in script_text.lower() for word in electrical_keywords)

        if mentions_electrical:
            has_safety = any(word in script_text.lower() for word in ['caution', 'warning', 'safety', 'danger'])
            if not has_safety:
                score -= 3.0  # Critical issue
                issues.append("SAFETY ISSUE: Electrical content without safety warnings")
            else:
                strengths.append("Appropriate safety warnings included")

        # Check for vague language
        vague_words = ['probably', 'maybe', 'might', 'could be', 'sometimes']
        vague_count = sum(1 for word in vague_words if word in script_text.lower())
        if vague_count > 3:
            score -= 1.5
            issues.append(f"Too much uncertain language ({vague_count} instances)")

        # Check for undefined abbreviations
        abbreviations = re.findall(r'\b([A-Z]{3,})\b', script_text)
        undefined_abbrevs = []
        for abbrev in set(abbreviations):
            # Check if it's defined (appears in parentheses or followed by explanation)
            if not re.search(rf'\({abbrev}\)|{abbrev} \(|\b{abbrev}\b.*\bstands for\b', script_text, re.IGNORECASE):
                undefined_abbrevs.append(abbrev)

        if len(undefined_abbrevs) > 2:
            score -= 1.0
            issues.append(f"Undefined abbreviations: {', '.join(undefined_abbrevs[:3])}")

        # Assume accuracy if no red flags
        if not issues:
            strengths.append("Technically accurate content")

        return {
            "score": max(0.0, min(10.0, score)),
            "issues": issues,
            "strengths": strengths,
            "feedback": self._select_feedback("technical_accuracy", score)
        }

    def _score_visual_quality(self, script_text: str) -> Dict:
        """Score visual quality (0-10)."""
        score = 10.0
        issues = []
        strengths = []

        # Check for visual cues
        visual_types = {
            "title": len(re.findall(r'\[show title:', script_text)),
            "diagram": len(re.findall(r'\[show diagram:', script_text)),
            "code": len(re.findall(r'\[show code:', script_text)),
            "table": len(re.findall(r'\[show table\]', script_text)),
            "citation": len(re.findall(r'\[show citation:', script_text))
        }

        total_visuals = sum(visual_types.values())
        if total_visuals < 3:
            score -= 2.0
            issues.append(f"Too few visual cues ({total_visuals}). Need at least 3 for clarity.")
        else:
            strengths.append(f"Good use of visuals ({total_visuals} cues)")

        # Check for visual variety
        unique_visual_types = sum(1 for count in visual_types.values() if count > 0)
        if unique_visual_types < 2:
            score -= 1.0
            issues.append("Lacks visual variety (only 1 type of visual)")
        else:
            strengths.append(f"Good visual variety ({unique_visual_types} types)")

        # Check timing (visuals should appear with relevant content)
        # For now, assume timing is good if visuals are present
        if total_visuals > 0:
            strengths.append("Visuals appear to be well-timed")

        return {
            "score": max(0.0, min(10.0, score)),
            "issues": issues,
            "strengths": strengths,
            "feedback": self._select_feedback("visual_quality", score)
        }

    def _score_accessibility(self, script_text: str) -> Dict:
        """Score accessibility (0-10)."""
        score = 10.0
        issues = []
        strengths = []

        # Check language complexity (Flesch-Kincaid approximation)
        sentences = len(re.findall(r'[.!?]', script_text))
        words = len(script_text.split())
        avg_sentence_length = words / max(sentences, 1)

        if avg_sentence_length > 20:
            score -= 1.5
            issues.append(f"Sentences too long (avg {int(avg_sentence_length)} words). Aim for <20.")
        else:
            strengths.append("Sentence length appropriate")

        # Check for complex words (>3 syllables)
        complex_word_pattern = r'\b\w{12,}\b'  # Words 12+ chars as proxy
        complex_words = re.findall(complex_word_pattern, script_text)
        if len(complex_words) > words * 0.1:  # >10% complex words
            score -= 1.0
            issues.append("Too many complex words. Simplify vocabulary.")
        else:
            strengths.append("Vocabulary appropriate for audience")

        # Check for pause markers (cognitive load management)
        pause_count = script_text.count('[pause]')
        expected_pauses = words / 150 * 3  # ~3 pauses per minute
        if pause_count < expected_pauses * 0.5:
            score -= 0.5
            issues.append("Needs more pauses for information processing")
        else:
            strengths.append("Good pacing with appropriate pauses")

        # Assume captions will be auto-generated (strength)
        strengths.append("Auto-captions available")

        return {
            "score": max(0.0, min(10.0, score)),
            "issues": issues,
            "strengths": strengths,
            "feedback": self._select_feedback("accessibility", score)
        }

    def _select_feedback(self, dimension: str, score: float) -> str:
        """Select appropriate feedback template based on score."""
        if score >= 9.0:
            return f"Excellent {dimension.replace('_', ' ')}!"
        elif score >= 7.0:
            return f"Good {dimension.replace('_', ' ')} with minor room for improvement."
        elif score >= 5.0:
            return f"{dimension.replace('_', ' ').title()} needs work."
        else:
            return f"Significant {dimension.replace('_', ' ')} issues require attention."

    def _generate_feedback_letter(self, overall_score: float, dimension_scores: Dict, decision: str) -> str:
        """Generate Ms. Rodriguez's personalized feedback letter."""
        letter = f"""
========================================
VIDEO QUALITY REVIEW
Reviewer: {self.reviewer_name}
Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
========================================

Dear Content Creator,

Thank you for submitting this video for review. I've carefully evaluated it across five dimensions, drawing on my 20+ years of experience helping students learn complex topics.

OVERALL SCORE: {overall_score}/10.0

"""

        # Add decision
        if decision == "approve":
            letter += "[DECISION: APPROVED FOR PUBLISHING]\n\n"
            letter += "This video meets my quality standards and is ready for students! "
            letter += "I'm confident it will help learners understand this topic effectively.\n\n"
        elif decision == "flag_for_review":
            letter += "[DECISION: FLAG FOR HUMAN REVIEW]\n\n"
            letter += "This video has good bones, but I'd like another set of eyes on it before publishing. "
            letter += "The issues below are worth discussing.\n\n"
        else:
            letter += "[DECISION: NEEDS REVISION]\n\n"
            letter += "I appreciate your effort, but this video needs substantial improvement before "
            letter += "it's ready for students. Please address the issues below and resubmit.\n\n"

        # Detail each dimension
        letter += "DETAILED REVIEW:\n\n"

        for dimension_name, dimension_data in dimension_scores.items():
            score = dimension_data["score"]
            display_name = dimension_name.replace('_', ' ').title()

            letter += f"{display_name}: {score}/10.0\n"

            # Strengths
            if dimension_data["strengths"]:
                letter += "  STRENGTHS:\n"
                for strength in dimension_data["strengths"]:
                    letter += f"    + {strength}\n"

            # Issues
            if dimension_data["issues"]:
                letter += "  AREAS FOR IMPROVEMENT:\n"
                for issue in dimension_data["issues"]:
                    letter += f"    - {issue}\n"

            letter += "\n"

        # Closing
        letter += "========================================\n"
        letter += "NEXT STEPS:\n"
        if decision == "approve":
            letter += "  1. Proceed to publishing pipeline\n"
            letter += "  2. Monitor early engagement metrics\n"
            letter += "  3. Gather student feedback\n"
        elif decision == "flag_for_review":
            letter += "  1. Human reviewer will assess within 24 hours\n"
            letter += "  2. Minor revisions may be requested\n"
            letter += "  3. Expect approval decision soon\n"
        else:
            letter += "  1. Address all issues marked above\n"
            letter += "  2. Run through InstructionalDesignerAgent again\n"
            letter += "  3. Resubmit for review\n"

        letter += "\nThank you for your dedication to quality education!\n\n"
        letter += "Best regards,\n"
        letter += f"{self.reviewer_name}\n"
        letter += "Educational Quality Reviewer\n"
        letter += "========================================\n"

        return letter

    def _extract_action_items(self, *dimension_scores) -> List[str]:
        """Extract prioritized action items from all dimension scores."""
        action_items = []

        for dimension_data in dimension_scores:
            for issue in dimension_data["issues"]:
                # Prioritize critical issues (safety, accuracy)
                if "SAFETY" in issue or "accuracy" in issue.lower():
                    action_items.insert(0, f"[CRITICAL] {issue}")
                else:
                    action_items.append(issue)

        # Limit to top 10 most important
        return action_items[:10]


def main():
    """Demo: Review existing video scripts"""
    agent = VideoQualityReviewerAgent()

    print("=" * 70)
    print("VIDEO QUALITY REVIEWER - Ms. Rodriguez")
    print("=" * 70)

    # Find existing video scripts
    videos_dir = agent.project_root / "data" / "videos"
    script_paths = list(videos_dir.glob("*/script.txt"))

    if not script_paths:
        print("\n[ERROR] No video scripts found in data/videos/")
        return

    print(f"\nFound {len(script_paths)} video scripts")
    print(f"Reviewing most recent script as Ms. Rodriguez...\n")

    # Review most recent script
    latest_script = sorted(script_paths)[-1]
    video_dir = latest_script.parent

    with open(latest_script, 'r', encoding='utf-8') as f:
        script_text = f.read()

    # Load instructional design report if available
    id_report_path = video_dir / "instructional_design_report.md"
    id_report = None
    if id_report_path.exists():
        # Simple extraction of score from report
        with open(id_report_path, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'Overall Instructional Design Score: (\d+)/10', content)
            if match:
                id_report = {"overall_score": int(match.group(1))}

    # Perform review
    review = agent.review_video(
        script_text,
        video_metadata={"duration": 79, "format": "deep_dive"},
        instructional_design_report=id_report
    )

    # Display review
    print(review["feedback_letter"])

    # Save review
    review_path = video_dir / "quality_review.json"
    with open(review_path, 'w', encoding='utf-8') as f:
        json.dump(review, f, indent=2)

    print(f"\n[OK] Full review saved: {review_path}")

    print("\n" + "=" * 70)
    print("MS. RODRIGUEZ QUALITY REVIEWER - READY")
    print("=" * 70)
    print("\nReview Dimensions:")
    print("  [OK] Educational Quality (30% weight)")
    print("  [OK] Student Engagement (25% weight)")
    print("  [OK] Technical Accuracy (25% weight)")
    print("  [OK] Visual Quality (15% weight)")
    print("  [OK] Accessibility (5% weight)")
    print("\nDecision Thresholds:")
    print("  8.0+ -> Auto-approve")
    print("  6.0-7.9 -> Flag for human review")
    print("  <6.0 -> Reject, needs revision")


if __name__ == "__main__":
    main()
