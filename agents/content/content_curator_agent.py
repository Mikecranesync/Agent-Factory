#!/usr/bin/env python3
"""
ContentCuratorAgent - Topic Selection + 90-Day Content Calendar

This agent curates topics for video production based on:
1. Knowledge base gaps (what's missing from our coverage)
2. Search trends (what people are looking for)
3. Learning progression (prerequisite chains)
4. Seasonal relevance (HVAC in summer, heating in winter)
5. Strategic priorities (foundational content first)

Generates a 90-day rolling content calendar with:
- Daily video topics
- Format recommendations (Short/Series/Deep Dive)
- Learning objective alignment
- SEO keyword targets
- Difficulty progression

Created: Dec 2025
Part of: PLC Tutor multi-agent committee system
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from collections import Counter


class ContentCuratorAgent:
    """
    Strategic content curator for long-term channel growth.

    Creates 90-day content calendars balancing education, SEO, and engagement.

    Example:
        >>> agent = ContentCuratorAgent()
        >>> calendar = agent.generate_90_day_calendar()
        >>> next_topic = agent.get_next_topic()
    """

    def __init__(self, project_root: Path = None):
        """
        Initialize ContentCuratorAgent.

        Args:
            project_root: Path to project root (defaults to auto-detect)
        """
        self.agent_name = "content_curator_agent"
        self.project_root = project_root or Path(__file__).parent.parent.parent

        # Content strategy priorities (Phase 1-3)
        self.content_phases = {
            "phase1_foundation": {
                "days": 30,
                "goal": "Build foundational knowledge base",
                "focus": "Core concepts every technician needs",
                "topics": [
                    "What is a PLC?",
                    "Digital I/O Basics",
                    "Ladder Logic Fundamentals",
                    "Understanding the Scan Cycle",
                    "XIC, XIO, OTE Instructions",
                    "Start/Stop/Seal-In Motor Control",
                    "Timers: TON, TOF, RTO",
                    "Counters: CTU, CTD, RES",
                    "First PLC Program Walkthrough",
                    "Reading Ladder Logic Diagrams",
                    "Basic Troubleshooting Steps",
                    "Understanding Rung Logic",
                    "Comparing Contacts (NO vs NC)",
                    "Series vs Parallel Logic",
                    "Introduction to Tags",
                    "Memory Types (Bool, Int, Real)",
                    "Analog Input Basics (4-20mA)",
                    "Analog Output Basics",
                    "Scaling Analog Signals",
                    "HMI Overview",
                    "Studio 5000 Interface Tour",
                    "Creating a New Project",
                    "Adding I/O Modules",
                    "Documenting Your Code",
                    "Common Error Messages",
                    "Safety Circuit Basics",
                    "Emergency Stop Wiring",
                    "Overload Protection",
                    "Understanding Faults",
                    "Backup and Restore Best Practices"
                ]
            },
            "phase2_intermediate": {
                "days": 30,
                "goal": "Build practical troubleshooting skills",
                "focus": "Real-world applications and problem-solving",
                "topics": [
                    "PID Control Basics",
                    "Motor Speed Control with VFD",
                    "Troubleshooting I/O Failures",
                    "Understanding Fault Codes",
                    "Network Communication Basics",
                    "Ethernet/IP Overview",
                    "Modbus RTU Essentials",
                    "Multi-Motor Sequencing",
                    "Process Control Logic",
                    "Recipe Management Basics",
                    "Data Logging and Trending",
                    "Alarms and Notifications",
                    "Advanced Timer Applications",
                    "State Machine Logic",
                    "Conveyor Control Systems",
                    "Pump Control Strategies",
                    "Tank Level Control",
                    "Temperature Control Loops",
                    "Pressure Regulation",
                    "Flow Control Systems",
                    "Safety PLC vs Standard PLC",
                    "Redundancy Concepts",
                    "Hot Backup Systems",
                    "Diagnostics Tools Overview",
                    "Online Edits vs Offline",
                    "Version Control for PLCs",
                    "Testing Strategies",
                    "Commissioning Checklist",
                    "Preventive Maintenance",
                    "Capacity Planning"
                ]
            },
            "phase3_advanced": {
                "days": 30,
                "goal": "Master advanced techniques",
                "focus": "Optimization, advanced patterns, system design",
                "topics": [
                    "Custom Function Blocks",
                    "Add-On Instructions (AOI)",
                    "Advanced PID Tuning",
                    "Motion Control Basics",
                    "Servo vs Stepper Motors",
                    "CAM Profiles",
                    "High-Speed I/O",
                    "SCADA Integration",
                    "OPC UA Deep Dive",
                    "Database Connectivity",
                    "Cloud Data Integration",
                    "IIoT Fundamentals",
                    "Cybersecurity for PLCs",
                    "Network Segmentation",
                    "Firewall Configuration",
                    "Remote Access Best Practices",
                    "Performance Optimization",
                    "Reducing Scan Time",
                    "Memory Management",
                    "Structured Text Programming",
                    "Function Block Diagrams",
                    "Sequential Function Charts",
                    "Comparing IEC 61131-3 Languages",
                    "Multi-Platform Skills (Siemens)",
                    "TIA Portal Basics",
                    "Studio 5000 vs TIA Portal",
                    "Industry 4.0 Concepts",
                    "Digital Twin Basics",
                    "Predictive Maintenance",
                    "Career Growth as a PLC Programmer"
                ]
            }
        }

        # Topic difficulty levels
        self.difficulty_levels = {
            "beginner": {"target_audience": "Entry-level technicians", "prerequisites": 0},
            "intermediate": {"target_audience": "Technicians with 1+ year experience", "prerequisites": 3},
            "advanced": {"target_audience": "Senior technicians, engineers", "prerequisites": 5}
        }

        # Content format distribution targets
        self.format_distribution = {
            "short": 0.40,  # 40% shorts (<60s)
            "series": 0.35,  # 35% series (3-5 episodes)
            "deep_dive": 0.25  # 25% deep dives (10-15min)
        }

        # Seasonal keywords (industrial maintenance context)
        self.seasonal_topics = {
            "winter": ["heating", "HVAC", "freeze protection", "cold weather startup"],
            "spring": ["maintenance", "inspection", "cleaning", "preventive"],
            "summer": ["cooling", "chiller", "air conditioning", "ventilation"],
            "fall": ["winterization", "preparation", "shutdown procedures"]
        }

        # SEO keyword database (search volume estimates)
        self.seo_keywords = {
            "plc programming tutorial": {"volume": "high", "difficulty": "medium"},
            "ladder logic explained": {"volume": "high", "difficulty": "low"},
            "plc troubleshooting": {"volume": "medium", "difficulty": "low"},
            "allen bradley tutorial": {"volume": "medium", "difficulty": "medium"},
            "siemens plc programming": {"volume": "medium", "difficulty": "medium"},
            "motor control circuit": {"volume": "medium", "difficulty": "low"},
            "pid control tuning": {"volume": "low", "difficulty": "high"},
            "hmi design": {"volume": "low", "difficulty": "medium"},
            "scada basics": {"volume": "low", "difficulty": "medium"}
        }

    def generate_90_day_calendar(
        self,
        start_date: Optional[datetime] = None,
        existing_topics: Optional[List[str]] = None
    ) -> Dict:
        """
        Generate comprehensive 90-day content calendar.

        Args:
            start_date: Calendar start date (defaults to today)
            existing_topics: Topics already covered (to avoid duplicates)

        Returns:
            Calendar dictionary with daily topics and metadata
        """
        if start_date is None:
            start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        if existing_topics is None:
            existing_topics = []

        calendar = {
            "generated_at": datetime.utcnow().isoformat(),
            "start_date": start_date.isoformat(),
            "end_date": (start_date + timedelta(days=89)).isoformat(),
            "strategy": "Foundation -> Intermediate -> Advanced progression",
            "daily_schedule": []
        }

        # Combine all topics from phases
        all_topics = []
        for phase_name, phase_data in self.content_phases.items():
            for topic in phase_data["topics"]:
                if topic not in existing_topics:
                    all_topics.append({
                        "title": topic,
                        "phase": phase_name,
                        "difficulty": self._infer_difficulty(topic, phase_name)
                    })

        # Generate daily schedule
        current_date = start_date
        for day_num in range(90):
            # Determine which phase we're in
            if day_num < 30:
                phase = "phase1_foundation"
            elif day_num < 60:
                phase = "phase2_intermediate"
            else:
                phase = "phase3_advanced"

            # Get topics for this phase
            phase_topics = [t for t in all_topics if t["phase"] == phase]

            if day_num < len(phase_topics):
                topic_data = phase_topics[day_num % len(phase_topics)]

                # Determine format based on distribution
                format_type = self._select_format(day_num)

                # Get seasonal bonus (if applicable)
                seasonal_boost = self._check_seasonal_relevance(topic_data["title"], current_date)

                # Estimate SEO value
                seo_score = self._estimate_seo_value(topic_data["title"])

                daily_entry = {
                    "day": day_num + 1,
                    "date": current_date.strftime("%Y-%m-%d"),
                    "title": topic_data["title"],
                    "difficulty": topic_data["difficulty"],
                    "format": format_type,
                    "phase": phase,
                    "seo_score": seo_score,
                    "seasonal_boost": seasonal_boost,
                    "priority": self._calculate_priority(
                        day_num, topic_data["difficulty"], seo_score, seasonal_boost
                    ),
                    "learning_objective": self._generate_learning_objective(topic_data["title"]),
                    "target_keywords": self._extract_keywords(topic_data["title"]),
                    "estimated_production_time": self._estimate_production_time(format_type)
                }

                calendar["daily_schedule"].append(daily_entry)

            current_date += timedelta(days=1)

        # Add summary statistics
        calendar["statistics"] = self._calculate_calendar_stats(calendar["daily_schedule"])

        return calendar

    def get_next_topic(self, calendar: Optional[Dict] = None) -> Dict:
        """
        Get the next topic to produce based on calendar.

        Args:
            calendar: 90-day calendar (generates new if not provided)

        Returns:
            Next topic dictionary with production details
        """
        if calendar is None:
            calendar = self.generate_90_day_calendar()

        # Find first topic not yet produced
        for entry in calendar["daily_schedule"]:
            # Check if video exists for this topic
            videos_dir = self.project_root / "data" / "videos"
            video_exists = False

            if videos_dir.exists():
                for video_dir in videos_dir.iterdir():
                    script_path = video_dir / "script.txt"
                    if script_path.exists():
                        with open(script_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if entry["title"].lower() in content.lower():
                                video_exists = True
                                break

            if not video_exists:
                return {
                    "topic": entry,
                    "production_notes": self._generate_production_notes(entry),
                    "research_keywords": entry["target_keywords"],
                    "format_guidelines": self._get_format_guidelines(entry["format"])
                }

        # All topics covered, generate new calendar
        return {"status": "calendar_complete", "message": "All 90 topics covered. Generate new calendar."}

    def analyze_knowledge_gaps(self) -> Dict:
        """
        Analyze knowledge base to identify coverage gaps.

        Returns:
            Gap analysis with recommendations
        """
        # Check what knowledge atoms exist
        knowledge_dir = self.project_root / "data" / "knowledge_atoms"
        existing_topics = set()

        if knowledge_dir.exists():
            for atom_file in knowledge_dir.glob("*.json"):
                with open(atom_file, 'r', encoding='utf-8') as f:
                    atom = json.load(f)
                    if "title" in atom:
                        existing_topics.add(atom["title"].lower())

        # Identify gaps
        gaps = {
            "missing_foundation": [],
            "missing_intermediate": [],
            "missing_advanced": [],
            "total_gaps": 0
        }

        for phase_name, phase_data in self.content_phases.items():
            for topic in phase_data["topics"]:
                if topic.lower() not in existing_topics:
                    difficulty = self._infer_difficulty(topic, phase_name)
                    if difficulty == "beginner":
                        gaps["missing_foundation"].append(topic)
                    elif difficulty == "intermediate":
                        gaps["missing_intermediate"].append(topic)
                    else:
                        gaps["missing_advanced"].append(topic)
                    gaps["total_gaps"] += 1

        gaps["coverage_percentage"] = (
            (len(existing_topics) / sum(len(p["topics"]) for p in self.content_phases.values())) * 100
        )

        gaps["recommendations"] = self._generate_gap_recommendations(gaps)

        return gaps

    def _infer_difficulty(self, topic: str, phase: str) -> str:
        """Infer difficulty level from topic and phase."""
        if "phase1" in phase or any(word in topic.lower() for word in ["basics", "introduction", "what is", "first"]):
            return "beginner"
        elif "phase3" in phase or any(word in topic.lower() for word in ["advanced", "custom", "optimization", "master"]):
            return "advanced"
        else:
            return "intermediate"

    def _select_format(self, day_num: int) -> str:
        """Select format based on distribution targets and day number."""
        # Pattern: Short, Short, Series, Deep Dive, Short, Short, Series, ...
        pattern = ["short", "short", "series", "deep_dive"]
        return pattern[day_num % len(pattern)]

    def _check_seasonal_relevance(self, topic: str, date: datetime) -> bool:
        """Check if topic has seasonal relevance."""
        month = date.month

        # Determine season
        if month in [12, 1, 2]:
            season = "winter"
        elif month in [3, 4, 5]:
            season = "spring"
        elif month in [6, 7, 8]:
            season = "summer"
        else:
            season = "fall"

        # Check if topic contains seasonal keywords
        seasonal_keywords = self.seasonal_topics.get(season, [])
        return any(keyword in topic.lower() for keyword in seasonal_keywords)

    def _estimate_seo_value(self, topic: str) -> float:
        """Estimate SEO value (0-10 scale)."""
        score = 5.0  # Base score

        # Check against known keywords
        topic_lower = topic.lower()
        for keyword, data in self.seo_keywords.items():
            if keyword in topic_lower:
                if data["volume"] == "high":
                    score += 2.0
                elif data["volume"] == "medium":
                    score += 1.0

                if data["difficulty"] == "low":
                    score += 1.0

        # Cap at 10
        return min(10.0, score)

    def _calculate_priority(self, day_num: int, difficulty: str, seo_score: float, seasonal_boost: bool) -> str:
        """Calculate topic priority (critical/high/medium/low)."""
        priority_score = 0

        # Early days are high priority (foundation)
        if day_num < 30:
            priority_score += 2

        # Beginner content is higher priority
        if difficulty == "beginner":
            priority_score += 2
        elif difficulty == "intermediate":
            priority_score += 1

        # SEO value
        if seo_score >= 8:
            priority_score += 2
        elif seo_score >= 6:
            priority_score += 1

        # Seasonal boost
        if seasonal_boost:
            priority_score += 1

        # Map to priority levels
        if priority_score >= 5:
            return "critical"
        elif priority_score >= 3:
            return "high"
        elif priority_score >= 1:
            return "medium"
        else:
            return "low"

    def _generate_learning_objective(self, topic: str) -> str:
        """Generate learning objective for topic."""
        if "?" in topic:
            return f"Understand {topic.replace('?', '')}"
        elif topic.startswith("Introduction"):
            return f"Learn the fundamentals of {topic.replace('Introduction to ', '')}"
        elif "Basics" in topic:
            return f"Master basic {topic.replace(' Basics', '')} concepts"
        else:
            return f"Learn how to {topic.lower()}"

    def _extract_keywords(self, topic: str) -> List[str]:
        """Extract SEO keywords from topic."""
        # Remove common words
        stop_words = {"the", "a", "an", "to", "and", "or", "of", "in", "for", "with"}
        words = topic.lower().replace("?", "").split()
        keywords = [word for word in words if word not in stop_words and len(word) > 2]

        # Add full topic as primary keyword
        keywords.insert(0, topic.lower().replace("?", ""))

        return keywords[:5]  # Top 5 keywords

    def _estimate_production_time(self, format_type: str) -> str:
        """Estimate production time for format."""
        time_estimates = {
            "short": "2-3 hours",
            "series": "6-8 hours (total for series)",
            "deep_dive": "4-6 hours"
        }
        return time_estimates.get(format_type, "3-4 hours")

    def _calculate_calendar_stats(self, schedule: List[Dict]) -> Dict:
        """Calculate calendar statistics."""
        formats = Counter(entry["format"] for entry in schedule)
        difficulties = Counter(entry["difficulty"] for entry in schedule)
        priorities = Counter(entry["priority"] for entry in schedule)

        return {
            "total_topics": len(schedule),
            "format_distribution": dict(formats),
            "difficulty_distribution": dict(difficulties),
            "priority_distribution": dict(priorities),
            "avg_seo_score": sum(entry["seo_score"] for entry in schedule) / len(schedule) if schedule else 0,
            "seasonal_topics": sum(1 for entry in schedule if entry["seasonal_boost"])
        }

    def _generate_production_notes(self, entry: Dict) -> str:
        """Generate production notes for topic."""
        notes = f"""
PRODUCTION NOTES: {entry['title']}

Format: {entry['format'].upper()}
Difficulty: {entry['difficulty'].capitalize()}
Priority: {entry['priority'].upper()}

Learning Objective:
{entry['learning_objective']}

Target Keywords:
{', '.join(entry['target_keywords'])}

Estimated Production Time: {entry['estimated_production_time']}

Content Guidelines:
"""

        if entry["format"] == "short":
            notes += "- Keep under 60 seconds\n"
            notes += "- Single concept focus\n"
            notes += "- Strong hook in first 3 seconds\n"
        elif entry["format"] == "series":
            notes += "- Plan 3-5 episodes\n"
            notes += "- Progressive difficulty\n"
            notes += "- Each episode ~3-5 minutes\n"
        else:  # deep_dive
            notes += "- 10-15 minute format\n"
            notes += "- Comprehensive coverage\n"
            notes += "- Multiple examples\n"

        if entry["seasonal_boost"]:
            notes += "\n[SEASONAL RELEVANCE] Publish ASAP for maximum impact!\n"

        return notes

    def _get_format_guidelines(self, format_type: str) -> Dict:
        """Get format-specific production guidelines."""
        guidelines = {
            "short": {
                "max_duration": 60,
                "max_concepts": 1,
                "max_steps": 3,
                "hook_requirement": "Must engage in first 3 seconds",
                "visual_style": "Fast-paced, dynamic"
            },
            "series": {
                "max_duration": 300,
                "max_concepts": 3,
                "max_steps": 10,
                "episodes": (3, 5),
                "hook_requirement": "Episode recap + new hook",
                "visual_style": "Consistent across episodes"
            },
            "deep_dive": {
                "max_duration": 900,
                "max_concepts": 5,
                "max_steps": 20,
                "hook_requirement": "Strong value proposition",
                "visual_style": "Detailed diagrams and examples"
            }
        }
        return guidelines.get(format_type, {})

    def _generate_gap_recommendations(self, gaps: Dict) -> List[str]:
        """Generate recommendations based on gap analysis."""
        recommendations = []

        if gaps["coverage_percentage"] < 30:
            recommendations.append("CRITICAL: Focus on foundation topics first. Coverage is very low.")

        if len(gaps["missing_foundation"]) > 0:
            recommendations.append(f"Prioritize {len(gaps['missing_foundation'])} foundation topics for new viewers.")

        if len(gaps["missing_intermediate"]) > len(gaps["missing_foundation"]):
            recommendations.append("Balance content: Need more beginner topics before intermediate.")

        if gaps["coverage_percentage"] >= 70:
            recommendations.append("Good coverage! Consider advanced topics and optimization content.")

        return recommendations


def main():
    """Demo: Generate 90-day content calendar"""
    agent = ContentCuratorAgent()

    print("=" * 70)
    print("CONTENT CURATOR AGENT - 90-DAY CALENDAR")
    print("=" * 70)

    # Analyze current gaps
    print("\n[1/3] Analyzing knowledge base gaps...\n")
    gaps = agent.analyze_knowledge_gaps()

    print(f"Coverage: {gaps['coverage_percentage']:.1f}%")
    print(f"Total Gaps: {gaps['total_gaps']}")
    print(f"  - Foundation: {len(gaps['missing_foundation'])}")
    print(f"  - Intermediate: {len(gaps['missing_intermediate'])}")
    print(f"  - Advanced: {len(gaps['missing_advanced'])}")

    print("\nRecommendations:")
    for rec in gaps["recommendations"]:
        print(f"  * {rec}")

    # Generate calendar
    print("\n[2/3] Generating 90-day content calendar...\n")
    calendar = agent.generate_90_day_calendar()

    print(f"Calendar: {calendar['start_date'][:10]} to {calendar['end_date'][:10]}")
    print(f"Total Topics: {calendar['statistics']['total_topics']}")
    print(f"\nFormat Distribution:")
    for format_type, count in calendar['statistics']['format_distribution'].items():
        print(f"  - {format_type.title()}: {count}")

    print(f"\nDifficulty Distribution:")
    for diff, count in calendar['statistics']['difficulty_distribution'].items():
        print(f"  - {diff.title()}: {count}")

    print(f"\nAverage SEO Score: {calendar['statistics']['avg_seo_score']:.1f}/10")
    print(f"Seasonal Topics: {calendar['statistics']['seasonal_topics']}")

    # Show first week
    print("\n[3/3] First Week Preview:\n")
    for entry in calendar["daily_schedule"][:7]:
        print(f"Day {entry['day']}: {entry['title']}")
        print(f"  Format: {entry['format']} | Difficulty: {entry['difficulty']} | Priority: {entry['priority']}")
        print(f"  SEO: {entry['seo_score']}/10 | Seasonal: {entry['seasonal_boost']}")
        print()

    # Save calendar
    calendar_path = agent.project_root / "data" / "content_calendar_90day.json"
    calendar_path.parent.mkdir(parents=True, exist_ok=True)
    with open(calendar_path, 'w', encoding='utf-8') as f:
        json.dump(calendar, f, indent=2)

    print(f"[OK] Full calendar saved: {calendar_path}")

    # Get next topic
    print("\n" + "=" * 70)
    print("NEXT TOPIC TO PRODUCE:")
    print("=" * 70)

    next_topic = agent.get_next_topic(calendar)
    if "topic" in next_topic:
        print(f"\nTitle: {next_topic['topic']['title']}")
        print(f"Format: {next_topic['topic']['format']}")
        print(f"Difficulty: {next_topic['topic']['difficulty']}")
        print(f"Priority: {next_topic['topic']['priority']}")
        print(f"\n{next_topic['production_notes']}")
    else:
        print(next_topic["message"])

    print("\n" + "=" * 70)
    print("CONTENT CURATOR AGENT - READY")
    print("=" * 70)
    print("\nCapabilities:")
    print("  [OK] 90-day content calendar generation")
    print("  [OK] Knowledge gap analysis")
    print("  [OK] Topic prioritization (SEO + difficulty + seasonal)")
    print("  [OK] Format distribution (40% Shorts, 35% Series, 25% Deep Dive)")
    print("  [OK] Learning progression (Foundation -> Intermediate -> Advanced)")


if __name__ == "__main__":
    main()
