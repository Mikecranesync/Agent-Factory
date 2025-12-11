#!/usr/bin/env python3
"""
InstructionalDesignerAgent - Adult Learning Frameworks + Content Formatting

This agent applies adult learning principles to industrial education content.
Based on ADDIE model, Malcolm Knowles' adult learning theory, and Bloom's Taxonomy.

Key Responsibilities:
1. Apply ADDIE framework (Analysis, Design, Development, Implementation, Evaluation)
2. Content format selector (Shorts <60s, Series 3-5 parts, Deep Dive 10-15min)
3. "3rd grader test" - script simplification for comprehension
4. Jargon elimination/definition engine
5. Analogy injection system
6. Engagement optimizer (hook timing, visual cadence, pacing)

Adult Learning Principles (Knowles):
- Self-directed learning (technicians solve problems autonomously)
- Experience-based (relate to on-the-job scenarios)
- Readiness to learn (content must be immediately applicable)
- Task-centered (focus on practical solutions, not theory)
- Internal motivation (career advancement, efficiency)

Created: Dec 2025
Part of: PLC Tutor multi-agent committee system
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime


class InstructionalDesignerAgent:
    """
    Adult learning expert for industrial education content.

    Applies ADDIE model, simplifies complex technical content,
    and optimizes for different formats (Shorts/Series/Deep Dive).

    Example:
        >>> agent = InstructionalDesignerAgent()
        >>> analysis = agent.analyze_script(script_text)
        >>> format_rec = agent.recommend_format(analysis)
        >>> improved = agent.improve_script(script_text, format_rec)
    """

    def __init__(self, project_root: Path = None):
        """
        Initialize InstructionalDesignerAgent.

        Args:
            project_root: Path to project root (defaults to auto-detect)
        """
        self.agent_name = "instructional_designer_agent"
        self.project_root = project_root or Path(__file__).parent.parent.parent

        # ADDIE phase tracking
        self.current_phase = "Analysis"

        # Content format thresholds
        self.format_rules = {
            "short": {
                "max_duration": 60,  # seconds
                "max_concepts": 1,
                "max_steps": 3,
                "complexity": "beginner",
                "examples": ["Single error code lookup", "Quick tip", "Tool demonstration"]
            },
            "series": {
                "max_duration": 300,  # 5 minutes per episode
                "max_concepts": 3,
                "max_steps": 10,
                "complexity": "intermediate",
                "num_episodes": (3, 5),
                "examples": ["PLC programming basics", "Motor control fundamentals", "Troubleshooting workflow"]
            },
            "deep_dive": {
                "max_duration": 900,  # 15 minutes
                "max_concepts": 5,
                "max_steps": 20,
                "complexity": "advanced",
                "examples": ["Complete PID tuning guide", "Network protocol deep dive", "Safety system design"]
            }
        }

        # Jargon database (technical term → plain English)
        self.jargon_map = {
            # PLC terms
            "scan cycle": "the time it takes for the PLC to read inputs, execute logic, and update outputs",
            "ladder logic": "a visual programming language that looks like electrical relay diagrams",
            "rung": "one line of ladder logic code",
            "XIC": "Examine If Closed - checks if an input is ON",
            "XIO": "Examine If Open - checks if an input is OFF",
            "OTE": "Output Energize - turns an output ON",
            "seal-in": "a circuit that keeps itself running after you release the start button",

            # Motor control
            "contactor": "an electrical switch controlled by the PLC",
            "overload": "protection that shuts off a motor if it draws too much current",
            "auxiliary contact": "an extra switch on a contactor that signals its status",
            "DOL starter": "Direct-On-Line starter - the simplest way to start a motor",

            # Instrumentation
            "4-20mA": "a standard signal where 4 milliamps means zero and 20 milliamps means full scale",
            "analog input": "a signal that can have any value within a range, like temperature or pressure",
            "digital input": "a signal that is either ON or OFF",

            # General automation
            "HMI": "Human Machine Interface - the touchscreen or panel where operators control equipment",
            "SCADA": "Supervisory Control And Data Acquisition - software that monitors large systems",
            "register": "a memory location in the PLC that stores a number",
            "tag": "a named variable in modern PLCs (like 'Motor_1_Speed')"
        }

        # Analogy database (complex concept → relatable analogy)
        self.analogy_bank = {
            "scan_cycle": "Like a security guard doing rounds: check all doors (inputs), decide what to do (logic), take actions (outputs), then start the next round.",

            "ladder_logic": "Imagine a flowchart made of light switches and lightbulbs. If THIS switch is on AND THAT switch is on, THEN turn on THIS light.",

            "seal_in": "Like a lamp with a switch that locks in place. You press it once to turn on, and it stays on until you press the OFF button.",

            "pid_control": "Like cruise control in your car. It constantly adjusts the throttle to maintain your set speed, whether you're going uphill or downhill.",

            "analog_signal": "Like a dimmer switch for lights. Instead of just ON or OFF, you can have any brightness level in between.",

            "network_protocol": "Like the rules for a polite conversation. One person talks while the other listens, then they switch. Everyone knows when it's their turn.",

            "timer": "Like a stopwatch that triggers an action when time runs out. For example, 'wait 5 seconds, then turn on the fan.'",

            "counter": "Like counting cars entering a parking garage. When you reach 100 cars, turn on the 'FULL' sign."
        }

        # Bloom's Taxonomy levels (for learning objective classification)
        self.blooms_levels = {
            "remember": ["define", "list", "identify", "recall", "name"],
            "understand": ["explain", "describe", "summarize", "interpret", "compare"],
            "apply": ["use", "demonstrate", "execute", "implement", "solve"],
            "analyze": ["examine", "diagnose", "troubleshoot", "categorize", "differentiate"],
            "evaluate": ["assess", "justify", "critique", "validate", "test"],
            "create": ["design", "build", "develop", "generate", "plan"]
        }

    def analyze_script(self, script_text: str) -> Dict:
        """
        ADDIE Phase 1: Analysis

        Analyze script for complexity, learning objectives, and readability.

        Args:
            script_text: Full script text

        Returns:
            Analysis dictionary with metrics and recommendations
        """
        self.current_phase = "Analysis"

        # Count concepts (approximate by technical terms)
        jargon_found = [term for term in self.jargon_map.keys() if term.lower() in script_text.lower()]
        concept_count = len(set(jargon_found))

        # Count steps (look for step markers)
        step_pattern = r'Step \d+:|^\d+\.|First,|Second,|Next,|Then,|Finally,'
        steps = re.findall(step_pattern, script_text, re.MULTILINE | re.IGNORECASE)
        step_count = len(steps)

        # Estimate duration (150 words per minute average speaking rate)
        word_count = len(script_text.split())
        estimated_duration = (word_count / 150) * 60  # seconds

        # Calculate readability (Flesch-Kincaid Grade Level approximation)
        sentences = script_text.count('.') + script_text.count('!') + script_text.count('?')
        sentences = max(sentences, 1)
        syllables = self._count_syllables(script_text)

        # Flesch-Kincaid Grade Level = 0.39 * (words/sentences) + 11.8 * (syllables/words) - 15.59
        fk_grade = 0.39 * (word_count / sentences) + 11.8 * (syllables / word_count) - 15.59

        # Detect learning objectives (action verbs)
        learning_objectives = []
        for level, verbs in self.blooms_levels.items():
            for verb in verbs:
                if re.search(rf'\b{verb}\b', script_text, re.IGNORECASE):
                    learning_objectives.append((verb, level))

        # Identify jargon that needs definition
        undefined_jargon = []
        for term in jargon_found:
            definition = self.jargon_map.get(term.lower())
            # Check if term is used but not defined
            if definition and definition not in script_text.lower():
                undefined_jargon.append(term)

        # Detect missing analogies (complex concepts without relatable examples)
        missing_analogies = []
        for concept, analogy in self.analogy_bank.items():
            concept_keywords = concept.replace('_', ' ')
            if concept_keywords in script_text.lower() and analogy not in script_text:
                missing_analogies.append(concept)

        # Check hook timing (should engage within first 5 seconds / ~12 words)
        first_sentence = script_text.split('.')[0]
        hook_words = len(first_sentence.split())
        has_strong_hook = any(phrase in first_sentence.lower() for phrase in [
            'ready to', 'here\'s', 'watch', 'discover', 'learn how',
            'stuck', 'frustrated', 'problem', 'solution'
        ])

        return {
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "word_count": word_count,
                "estimated_duration_seconds": int(estimated_duration),
                "concept_count": concept_count,
                "step_count": step_count,
                "flesch_kincaid_grade": round(fk_grade, 1),
                "jargon_density": round(len(jargon_found) / word_count * 100, 1) if word_count > 0 else 0
            },
            "learning_objectives": learning_objectives,
            "jargon_found": jargon_found,
            "undefined_jargon": undefined_jargon,
            "missing_analogies": missing_analogies,
            "hook_quality": {
                "hook_word_count": hook_words,
                "has_strong_hook": has_strong_hook,
                "passes_5_second_test": hook_words <= 12 and has_strong_hook
            },
            "readability_level": self._interpret_fk_grade(fk_grade)
        }

    def recommend_format(self, analysis: Dict) -> str:
        """
        ADDIE Phase 2: Design (Format Selection)

        Recommend content format based on analysis.

        Args:
            analysis: Output from analyze_script()

        Returns:
            Format recommendation ("short", "series", or "deep_dive")
        """
        self.current_phase = "Design"

        duration = analysis["metrics"]["estimated_duration_seconds"]
        concepts = analysis["metrics"]["concept_count"]
        steps = analysis["metrics"]["step_count"]

        # Decision logic
        if duration <= 60 and concepts <= 1 and steps <= 3:
            return "short"
        elif duration <= 300 and concepts <= 3 and steps <= 10:
            # Check if content is naturally serial (builds on previous knowledge)
            if concepts > 2 or steps > 7:
                return "series"
            else:
                return "short"  # Could be a longer short
        else:
            return "deep_dive"

    def improve_script(self, script_text: str, target_format: str = None) -> Dict:
        """
        ADDIE Phase 3: Development (Script Improvement)

        Apply "3rd grader test" simplification, add analogies, define jargon.

        Args:
            script_text: Original script
            target_format: Target format ("short", "series", "deep_dive")

        Returns:
            Improved script with explanations of changes
        """
        self.current_phase = "Development"

        # First analyze to identify issues
        analysis = self.analyze_script(script_text)

        if target_format is None:
            target_format = self.recommend_format(analysis)

        improved = script_text
        changes_made = []

        # 1. Define undefined jargon
        for term in analysis["undefined_jargon"]:
            definition = self.jargon_map.get(term.lower())
            if definition:
                # Find first occurrence and add definition
                pattern = re.compile(rf'\b{re.escape(term)}\b', re.IGNORECASE)
                match = pattern.search(improved)
                if match:
                    replacement = f"{match.group()} ({definition})"
                    improved = pattern.sub(replacement, improved, count=1)
                    changes_made.append(f"Defined jargon: '{term}'")

        # 2. Add missing analogies
        for concept in analysis["missing_analogies"][:2]:  # Max 2 analogies to avoid clutter
            analogy = self.analogy_bank.get(concept)
            concept_keywords = concept.replace('_', ' ')

            # Find paragraph with concept and add analogy after it
            paragraphs = improved.split('\n\n')
            for i, para in enumerate(paragraphs):
                if concept_keywords in para.lower() and analogy not in para:
                    # Add analogy as new sentence
                    paragraphs[i] = para + f" Think of it like this: {analogy}"
                    improved = '\n\n'.join(paragraphs)
                    changes_made.append(f"Added analogy for: '{concept_keywords}'")
                    break

        # 3. Strengthen hook if needed
        if not analysis["hook_quality"]["passes_5_second_test"]:
            first_sentence = improved.split('.')[0]

            # Generate stronger hook based on content
            if 'error' in improved.lower() or 'fault' in improved.lower():
                new_hook = "[enthusiastic] Stuck with an error code? Here's how to fix it fast."
            elif 'step' in improved.lower():
                new_hook = "[enthusiastic] Ready to master this skill? Here's what you need to know."
            else:
                new_hook = "[enthusiastic] Let's dive into a practical solution you can use right now."

            improved = improved.replace(first_sentence, new_hook, 1)
            changes_made.append("Improved hook for 5-second engagement test")

        # 4. Break long paragraphs (>50 words) into chunks
        paragraphs = improved.split('\n\n')
        new_paragraphs = []
        for para in paragraphs:
            words = para.split()
            if len(words) > 50:
                # Split at midpoint sentence
                mid = len(words) // 2
                split_point = para.find('.', len(' '.join(words[:mid])))
                if split_point > 0:
                    new_paragraphs.append(para[:split_point + 1])
                    new_paragraphs.append(para[split_point + 1:].strip())
                    changes_made.append("Broke long paragraph for readability")
                else:
                    new_paragraphs.append(para)
            else:
                new_paragraphs.append(para)
        improved = '\n\n'.join(new_paragraphs)

        # 5. Add [pause] markers after complex concepts
        for term in analysis["jargon_found"][:3]:  # Top 3 most complex
            pattern = re.compile(rf'\b{re.escape(term)}\b[^.]*\.', re.IGNORECASE)
            match = pattern.search(improved)
            if match and '[pause]' not in match.group():
                improved = pattern.sub(match.group() + ' [pause]', improved, count=1)
                changes_made.append(f"Added pause after complex term: '{term}'")

        # 6. Format-specific optimizations
        if target_format == "short":
            # Remove any series-style "Step X" markers, use bullet flow
            improved = re.sub(r'Step \d+:', '→', improved)
            changes_made.append("Converted to bullet-style flow for Short format")

        elif target_format == "series":
            # Add episode markers
            if "Episode" not in improved:
                improved = f"[Episode 1 of {self.format_rules['series']['num_episodes'][0]}]\n\n" + improved
                changes_made.append("Added episode marker for Series format")

        # Calculate improvement metrics
        original_fk = analysis["metrics"]["flesch_kincaid_grade"]
        new_analysis = self.analyze_script(improved)
        new_fk = new_analysis["metrics"]["flesch_kincaid_grade"]

        return {
            "improved_script": improved,
            "changes_made": changes_made,
            "target_format": target_format,
            "readability_improvement": {
                "original_grade_level": original_fk,
                "improved_grade_level": new_fk,
                "improvement": round(original_fk - new_fk, 1)
            },
            "format_compliance": self._check_format_compliance(new_analysis, target_format),
            "third_grader_test": self._third_grader_test(improved)
        }

    def optimize_engagement(self, script_text: str) -> Dict:
        """
        Optimize script for engagement (hook timing, pacing, visual cadence).

        Args:
            script_text: Script to optimize

        Returns:
            Engagement analysis with recommendations
        """
        # Hook timing (first 5 seconds)
        first_sentence = script_text.split('.')[0]
        hook_seconds = (len(first_sentence.split()) / 150) * 60

        # Pacing (words per minute over time)
        paragraphs = script_text.split('\n\n')
        pacing = []
        for para in paragraphs:
            wpm = len(para.split()) / ((len(para.split()) / 150) * 60) * 60
            pacing.append(wpm)

        avg_pacing = sum(pacing) / len(pacing) if pacing else 0

        # Visual cadence (how often visual cues appear)
        visual_markers = len(re.findall(r'\[show ', script_text))
        script_duration = (len(script_text.split()) / 150) * 60
        visuals_per_minute = (visual_markers / script_duration) * 60 if script_duration > 0 else 0

        # Pause frequency
        pause_count = script_text.count('[pause]')
        pauses_per_minute = (pause_count / script_duration) * 60 if script_duration > 0 else 0

        return {
            "hook_timing": {
                "hook_duration_seconds": round(hook_seconds, 1),
                "passes_5_second_rule": hook_seconds <= 5,
                "recommendation": "Hook is engaging" if hook_seconds <= 5 else "Shorten hook to <5 seconds"
            },
            "pacing": {
                "average_wpm": round(avg_pacing),
                "target_wpm": 150,
                "variance": round(max(pacing) - min(pacing)) if len(pacing) > 1 else 0,
                "recommendation": "Pacing is good" if 140 <= avg_pacing <= 160 else "Adjust pacing to 140-160 WPM"
            },
            "visual_cadence": {
                "visuals_per_minute": round(visuals_per_minute, 1),
                "target_range": (4, 8),
                "recommendation": "Add more visual cues" if visuals_per_minute < 4 else "Visual cadence is good"
            },
            "pause_frequency": {
                "pauses_per_minute": round(pauses_per_minute, 1),
                "target_range": (2, 4),
                "recommendation": "Good pause frequency" if 2 <= pauses_per_minute <= 4 else "Adjust pause frequency"
            }
        }

    def _count_syllables(self, text: str) -> int:
        """Approximate syllable count for readability calculations."""
        # Simple heuristic: count vowel groups
        text = text.lower()
        vowels = 'aeiouy'
        syllable_count = 0
        previous_was_vowel = False

        for char in text:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel

        # Adjust for silent 'e'
        if text.endswith('e'):
            syllable_count -= 1

        # Each word has at least 1 syllable
        word_count = len(text.split())
        return max(syllable_count, word_count)

    def _interpret_fk_grade(self, grade: float) -> str:
        """Interpret Flesch-Kincaid grade level."""
        if grade < 6:
            return "Elementary (very easy)"
        elif grade < 9:
            return "Middle School (easy)"
        elif grade < 12:
            return "High School (standard)"
        elif grade < 16:
            return "College (difficult)"
        else:
            return "Graduate Level (very difficult)"

    def _check_format_compliance(self, analysis: Dict, target_format: str) -> Dict:
        """Check if script complies with format rules."""
        rules = self.format_rules[target_format]
        duration = analysis["metrics"]["estimated_duration_seconds"]
        concepts = analysis["metrics"]["concept_count"]
        steps = analysis["metrics"]["step_count"]

        return {
            "duration_compliant": duration <= rules["max_duration"],
            "concepts_compliant": concepts <= rules["max_concepts"],
            "steps_compliant": steps <= rules["max_steps"],
            "overall_compliant": (
                duration <= rules["max_duration"] and
                concepts <= rules["max_concepts"] and
                steps <= rules["max_steps"]
            )
        }

    def _third_grader_test(self, script_text: str) -> Dict:
        """
        "Can a smart 8-year-old understand this?"

        Checks for:
        - Short sentences (<20 words)
        - Simple vocabulary (avoid words >3 syllables)
        - Concrete examples (not abstract concepts)
        """
        sentences = re.split(r'[.!?]', script_text)
        sentences = [s.strip() for s in sentences if s.strip()]

        long_sentences = [s for s in sentences if len(s.split()) > 20]

        # Count complex words (>3 syllables, excluding technical jargon which we've defined)
        words = script_text.split()
        complex_words = []
        for word in words:
            syllables = self._count_syllables(word)
            if syllables > 3 and word.lower() not in self.jargon_map:
                complex_words.append(word)

        # Check for concrete examples (look for "like", "for example", "imagine")
        has_examples = any(phrase in script_text.lower() for phrase in [
            'like', 'for example', 'imagine', 'think of', 'similar to'
        ])

        passes = (
            len(long_sentences) / len(sentences) < 0.3 and  # <30% long sentences
            len(complex_words) / len(words) < 0.1 and  # <10% complex words
            has_examples  # Has at least one concrete example
        )

        return {
            "passes_test": passes,
            "long_sentences_count": len(long_sentences),
            "complex_words_count": len(complex_words),
            "has_concrete_examples": has_examples,
            "recommendation": "Script is 3rd-grader friendly" if passes else "Simplify language and add more examples"
        }

    def generate_report(self, script_text: str) -> str:
        """
        Generate comprehensive instructional design report.

        Args:
            script_text: Script to analyze

        Returns:
            Formatted markdown report
        """
        analysis = self.analyze_script(script_text)
        format_rec = self.recommend_format(analysis)
        improvements = self.improve_script(script_text, format_rec)
        engagement = self.optimize_engagement(improvements["improved_script"])

        report = f"""# Instructional Design Report
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

## ADDIE Analysis

### Phase 1: Analysis
**Metrics:**
- Word Count: {analysis['metrics']['word_count']}
- Estimated Duration: {analysis['metrics']['estimated_duration_seconds']}s
- Concept Count: {analysis['metrics']['concept_count']}
- Step Count: {analysis['metrics']['step_count']}
- Flesch-Kincaid Grade: {analysis['metrics']['flesch_kincaid_grade']} ({analysis['readability_level']})
- Jargon Density: {analysis['metrics']['jargon_density']}%

**Learning Objectives Found:**
"""
        for verb, level in analysis['learning_objectives'][:5]:
            report += f"- {verb.title()} ({level})\n"

        report += f"""
**Undefined Jargon ({len(analysis['undefined_jargon'])}):**
"""
        for term in analysis['undefined_jargon'][:5]:
            report += f"- {term}\n"

        report += f"""
**Hook Quality:**
- Word Count: {analysis['hook_quality']['hook_word_count']}
- Has Strong Hook: {analysis['hook_quality']['has_strong_hook']}
- Passes 5-Second Test: {analysis['hook_quality']['passes_5_second_test']}

### Phase 2: Design (Format Recommendation)
**Recommended Format:** {format_rec.upper()}

**Format Compliance:**
- Duration: {'[OK]' if improvements['format_compliance']['duration_compliant'] else '[X]'}
- Concepts: {'[OK]' if improvements['format_compliance']['concepts_compliant'] else '[X]'}
- Steps: {'[OK]' if improvements['format_compliance']['steps_compliant'] else '[X]'}
- Overall: {'[OK] COMPLIANT' if improvements['format_compliance']['overall_compliant'] else '[X] NON-COMPLIANT'}

### Phase 3: Development (Improvements Made)
**Changes Applied ({len(improvements['changes_made'])}):**
"""
        for change in improvements['changes_made']:
            report += f"- {change}\n"

        report += f"""
**Readability Improvement:**
- Original Grade Level: {improvements['readability_improvement']['original_grade_level']}
- Improved Grade Level: {improvements['readability_improvement']['improved_grade_level']}
- Improvement: {improvements['readability_improvement']['improvement']} grades easier

**3rd Grader Test:**
- Passes: {'[OK] YES' if improvements['third_grader_test']['passes_test'] else '[X] NO'}
- Long Sentences: {improvements['third_grader_test']['long_sentences_count']}
- Complex Words: {improvements['third_grader_test']['complex_words_count']}
- Has Examples: {improvements['third_grader_test']['has_concrete_examples']}
- Recommendation: {improvements['third_grader_test']['recommendation']}

### Phase 4: Implementation (Engagement Optimization)
**Hook Timing:**
- Duration: {engagement['hook_timing']['hook_duration_seconds']}s
- Passes 5-Second Rule: {engagement['hook_timing']['passes_5_second_rule']}
- Recommendation: {engagement['hook_timing']['recommendation']}

**Pacing:**
- Average WPM: {engagement['pacing']['average_wpm']}
- Target WPM: {engagement['pacing']['target_wpm']}
- Recommendation: {engagement['pacing']['recommendation']}

**Visual Cadence:**
- Visuals per Minute: {engagement['visual_cadence']['visuals_per_minute']}
- Target Range: {engagement['visual_cadence']['target_range']}
- Recommendation: {engagement['visual_cadence']['recommendation']}

**Pause Frequency:**
- Pauses per Minute: {engagement['pause_frequency']['pauses_per_minute']}
- Target Range: {engagement['pause_frequency']['target_range']}
- Recommendation: {engagement['pause_frequency']['recommendation']}

### Phase 5: Evaluation (Overall Score)
"""

        # Calculate overall score
        score = 0
        max_score = 10

        if analysis['hook_quality']['passes_5_second_test']:
            score += 2
        if improvements['third_grader_test']['passes_test']:
            score += 2
        if improvements['format_compliance']['overall_compliant']:
            score += 2
        if engagement['hook_timing']['passes_5_second_rule']:
            score += 1
        if 140 <= engagement['pacing']['average_wpm'] <= 160:
            score += 1
        if 4 <= engagement['visual_cadence']['visuals_per_minute'] <= 8:
            score += 1
        if 2 <= engagement['pause_frequency']['pauses_per_minute'] <= 4:
            score += 1

        report += f"""**Overall Instructional Design Score: {score}/{max_score}**

"""

        if score >= 8:
            report += "[OK] APPROVED - Excellent instructional design\n"
        elif score >= 6:
            report += "[!] NEEDS REVISION - Apply recommended improvements\n"
        else:
            report += "[X] REJECT - Significant instructional design issues\n"

        report += f"""
---

## Improved Script

{improvements['improved_script']}

---
*Generated by InstructionalDesignerAgent v1.0*
*ADDIE Framework | Adult Learning Theory | Bloom's Taxonomy*
"""

        return report


def main():
    """Demo: Analyze existing video scripts"""
    agent = InstructionalDesignerAgent()

    print("=" * 70)
    print("INSTRUCTIONAL DESIGNER AGENT - SCRIPT ANALYSIS")
    print("=" * 70)

    # Find existing video scripts
    videos_dir = agent.project_root / "data" / "videos"
    script_paths = list(videos_dir.glob("*/script.txt"))

    if not script_paths:
        print("\n[ERROR] No video scripts found in data/videos/")
        print("Run auto_generate_video.py first to create test scripts")
        return

    print(f"\nFound {len(script_paths)} video scripts\n")

    # Analyze most recent script
    latest_script = sorted(script_paths)[-1]
    print(f"Analyzing: {latest_script.parent.name}/script.txt\n")

    with open(latest_script, 'r', encoding='utf-8') as f:
        script_text = f.read()

    # Generate full report
    report = agent.generate_report(script_text)

    # Save report
    report_path = latest_script.parent / "instructional_design_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(report)
    print(f"\n[OK] Full report saved: {report_path}")

    print("\n" + "=" * 70)
    print("INSTRUCTIONAL DESIGNER AGENT - READY")
    print("=" * 70)
    print("\nCapabilities:")
    print("  [OK] ADDIE framework analysis")
    print("  [OK] Format recommendations (Short/Series/Deep Dive)")
    print("  [OK] 3rd grader test simplification")
    print("  [OK] Jargon definition engine")
    print("  [OK] Analogy injection")
    print("  [OK] Engagement optimization")
    print("\nNext: Integrate with ScriptwriterAgent for real-time improvements")


if __name__ == "__main__":
    main()
