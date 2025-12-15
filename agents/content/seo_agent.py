#!/usr/bin/env python3
"""
SEOAgent - Optimize metadata for discoverability

Responsibilities:
- Generate SEO-optimized titles (60-70 characters, keyword-first)
- Write compelling descriptions (5000 char limit, keyword-rich)
- Select relevant tags (mix of broad + specific, 500 char limit)
- Identify target keywords (search volume + competition analysis)
- Optimize for YouTube algorithm (watch time, CTR predictions)
- Track ranking performance (keyword positions over time)

Schedule: On-demand (triggered by orchestrator)
Dependencies: Supabase, agent_factory.memory
Output: Updates Supabase tables, logs to agent_status

Based on: docs/AGENT_ORGANIZATION.md Section 4
"""

import os
import re
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
from pydantic import BaseModel, Field

from agent_factory.memory.storage import SupabaseMemoryStorage

logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Models
# ============================================================================

class VideoMetadata(BaseModel):
    """SEO-optimized metadata for YouTube videos"""

    video_id: str = Field(..., description="Unique video identifier")

    # Core Metadata
    title: str = Field(..., min_length=30, max_length=70, description="SEO-optimized title")
    description: str = Field(..., min_length=100, max_length=5000, description="Keyword-rich description")
    tags: List[str] = Field(..., min_length=10, max_length=15, description="YouTube tags")

    # SEO Data
    primary_keyword: str = Field(..., description="Main target keyword")
    secondary_keywords: List[str] = Field(default_factory=list, description="Additional target keywords")
    search_volume_estimate: Optional[str] = Field(None, description="Estimated monthly searches (low/medium/high)")
    competition_level: Optional[str] = Field(None, description="Keyword competition (low/medium/high)")

    # Performance Predictions
    estimated_ctr: Optional[float] = Field(None, ge=0.0, le=1.0, description="Predicted click-through rate")
    estimated_watch_time_minutes: Optional[int] = Field(None, ge=1, description="Expected watch time")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "video_id": "vid:abc123",
                "title": "PLC Ladder Logic Basics: Simple Motor Control Tutorial",
                "description": "Learn PLC ladder logic fundamentals with this beginner-friendly tutorial...",
                "tags": ["PLC tutorial", "ladder logic", "Allen-Bradley", "motor control"],
                "primary_keyword": "PLC ladder logic tutorial",
                "secondary_keywords": ["motor control", "Allen-Bradley PLC"],
                "search_volume_estimate": "medium",
                "competition_level": "low",
                "estimated_ctr": 0.08
            }
        }


class KeywordResearch(BaseModel):
    """Keyword research results for topic"""

    topic: str = Field(..., description="Main topic being researched")

    # Keywords
    primary_keywords: List[str] = Field(..., description="High-value target keywords")
    long_tail_keywords: List[str] = Field(default_factory=list, description="Long-tail variations")
    related_keywords: List[str] = Field(default_factory=list, description="Related search terms")

    # Analysis
    competition_analysis: Dict[str, str] = Field(
        default_factory=dict,
        description="Competition level per keyword (low/medium/high)"
    )
    search_volume_analysis: Dict[str, str] = Field(
        default_factory=dict,
        description="Search volume per keyword (low/medium/high)"
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)


class SEOAgent:
    """
    Optimize metadata for discoverability

    Optimize metadata for discoverability\n\nThis agent is part of the Content Team.
    """

    def __init__(self):
        """Initialize agent with Supabase connection"""
        self.storage = SupabaseMemoryStorage()
        self.agent_name = "seo_agent"
        self._register_status()

    def _register_status(self):
        """Register agent in agent_status table"""
        try:
            self.storage.client.table("agent_status").upsert({
                "agent_name": self.agent_name,
                "status": "idle",
                "last_heartbeat": datetime.now().isoformat(),
                "tasks_completed_today": 0,
                "tasks_failed_today": 0
            }).execute()
            logger.info(f"{self.agent_name} registered")
        except Exception as e:
            logger.error(f"Failed to register {self.agent_name}: {e}")

    def _send_heartbeat(self):
        """Update heartbeat in agent_status table"""
        try:
            self.storage.client.table("agent_status") \
                .update({"last_heartbeat": datetime.now().isoformat()}) \
                .eq("agent_name", self.agent_name) \
                .execute()
        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method called by orchestrator.

        Args:
            payload: Job payload from agent_jobs table

        Returns:
            Dict with status, result/error

        Example:
            >>> agent = SEOAgent()
            >>> result = agent.run({"task": "process"})
            >>> assert result["status"] == "success"
        """
        try:
            self._send_heartbeat()
            self._update_status("running")

            # TODO: Implement agent logic
            result = self._process(payload)

            self._update_status("completed")
            return {"status": "success", "result": result}

        except Exception as e:
            logger.error(f"{self.agent_name} failed: {e}")
            self._update_status("error", str(e))
            return {"status": "error", "error": str(e)}

    def _process(self, payload: Dict[str, Any]) -> Any:
        """
        Agent-specific processing logic.

        Args:
            payload: Must contain:
                - video_id: Unique video identifier
                - script: Full video script text
                - topic: Main topic/concept
                - target_keywords: Optional list of keywords to target

        Returns:
            VideoMetadata with optimized title, description, tags
        """
        video_id = payload.get("video_id")
        script = payload.get("script")
        topic = payload.get("topic")
        target_keywords = payload.get("target_keywords", [])

        if not all([video_id, script, topic]):
            raise ValueError("Payload must contain video_id, script, and topic")

        # Generate optimized metadata
        metadata = self.optimize_metadata(
            video_id=video_id,
            script=script,
            topic=topic,
            target_keywords=target_keywords
        )

        # Save to file
        self._save_metadata(metadata)

        return metadata.model_dump()

    def _update_status(self, status: str, error_message: Optional[str] = None):
        """Update agent status in database"""
        try:
            update_data = {"status": status}
            if error_message:
                update_data["error_message"] = error_message

            self.storage.client.table("agent_status") \
                .update(update_data) \
                .eq("agent_name", self.agent_name) \
                .execute()
        except Exception as e:
            logger.error(f"Failed to update status: {e}")


    # ========================================================================
    # Core SEO Optimization Methods
    # ========================================================================

    def optimize_metadata(
        self,
        video_id: str,
        script: str,
        topic: str,
        target_keywords: Optional[List[str]] = None
    ) -> VideoMetadata:
        """
        Generate SEO-optimized title, description, and tags.

        Args:
            video_id: Unique video identifier
            script: Full video script
            topic: Main topic/concept
            target_keywords: Optional list of keywords to target

        Returns:
            VideoMetadata with optimized title, description, tags
        """
        # Research keywords
        keywords = self._research_keywords(topic, script, target_keywords or [])

        # Generate title (60-70 chars, keyword-first)
        title = self._generate_title(topic, keywords["primary"])

        # Generate description (keyword-rich, under 5000 chars)
        description = self._generate_description(script, topic, keywords)

        # Generate tags (10-15 tags, mix of broad + specific)
        tags = self._generate_tags(keywords)

        # Estimate performance
        estimated_ctr = self._estimate_ctr(title)
        estimated_watch_time = self._estimate_watch_time(script)

        return VideoMetadata(
            video_id=video_id,
            title=title,
            description=description,
            tags=tags,
            primary_keyword=keywords["primary"],
            secondary_keywords=keywords["secondary"],
            search_volume_estimate=keywords.get("volume", "medium"),
            competition_level=keywords.get("competition", "medium"),
            estimated_ctr=estimated_ctr,
            estimated_watch_time_minutes=estimated_watch_time
        )

    def _research_keywords(
        self,
        topic: str,
        script: str,
        target_keywords: List[str]
    ) -> Dict[str, Any]:
        """
        Research keywords for topic.

        Args:
            topic: Main topic
            script: Full script text
            target_keywords: User-provided target keywords

        Returns:
            Dict with primary, secondary keywords and analysis
        """
        # Extract keywords from script and topic
        extracted = self._extract_keywords_from_text(script, topic)

        # Combine with target keywords
        all_keywords = list(set(target_keywords + extracted))

        # Sort by relevance (simple heuristic: frequency in script)
        keyword_scores = {}
        script_lower = script.lower()
        for kw in all_keywords:
            keyword_scores[kw] = script_lower.count(kw.lower())

        sorted_keywords = sorted(
            keyword_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Select primary and secondary
        primary = sorted_keywords[0][0] if sorted_keywords else topic
        secondary = [kw for kw, _ in sorted_keywords[1:6]]  # Top 5 secondary

        return {
            "primary": primary,
            "secondary": secondary,
            "volume": self._estimate_search_volume(primary),
            "competition": self._estimate_competition(primary)
        }

    def _extract_keywords_from_text(self, script: str, topic: str) -> List[str]:
        """
        Extract potential keywords from script text.

        Args:
            script: Full script text
            topic: Main topic

        Returns:
            List of extracted keywords
        """
        # Remove common words
        stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
            "for", "of", "with", "by", "from", "is", "are", "was", "were",
            "be", "been", "being", "have", "has", "had", "do", "does", "did",
            "will", "would", "could", "should", "may", "might", "this", "that",
            "these", "those", "i", "you", "we", "they", "it", "he", "she"
        }

        # Tokenize and filter
        words = re.findall(r'\b\w+\b', script.lower())
        keywords = [w for w in words if w not in stopwords and len(w) > 3]

        # Count frequency
        word_freq = {}
        for word in keywords:
            word_freq[word] = word_freq.get(word, 0) + 1

        # Get top 20 most frequent
        top_keywords = sorted(
            word_freq.items(),
            key=lambda x: x[1],
            reverse=True
        )[:20]

        # Add topic variations
        result = [kw for kw, _ in top_keywords]
        result.append(topic.lower())
        result.append(f"{topic.lower()} tutorial")
        result.append(f"{topic.lower()} guide")

        return list(set(result))

    def _generate_title(self, topic: str, primary_keyword: str) -> str:
        """
        Generate SEO-optimized title (60-70 chars, keyword-first).

        Args:
            topic: Main topic
            primary_keyword: Primary target keyword

        Returns:
            Optimized title string
        """
        # Start with keyword
        if primary_keyword.lower() in topic.lower():
            base = topic
        else:
            base = f"{primary_keyword}: {topic}"

        # Add hook/curiosity element
        hooks = [
            "Complete Tutorial",
            "Beginner's Guide",
            "Step-by-Step Guide",
            "Essential Tutorial",
            "Quick Start Guide"
        ]

        # Try different combinations to hit 60-70 char target
        for hook in hooks:
            title = f"{base} - {hook}"
            if 60 <= len(title) <= 70:
                return title

        # Fallback: trim to fit
        if len(base) > 70:
            return base[:67] + "..."
        elif len(base) < 60:
            return f"{base} - Complete Tutorial"

        return base

    def _generate_description(
        self,
        script: str,
        topic: str,
        keywords: Dict[str, Any]
    ) -> str:
        """
        Generate keyword-rich YouTube description.

        Args:
            script: Full script text
            topic: Main topic
            keywords: Keyword research results

        Returns:
            Optimized description (under 5000 chars)
        """
        # Extract first few sentences from script for summary
        sentences = script.split(". ")
        summary = ". ".join(sentences[:3]) + "."

        # Build description
        description_parts = [
            # Opening with primary keyword
            f"Learn {keywords['primary']} in this comprehensive tutorial.",
            "",
            summary,
            "",
            "In this video, you'll learn:",
            f"- What is {topic}",
            f"- How to use {keywords['primary']}",
            f"- Practical examples and applications",
            f"- Common mistakes to avoid",
            "",
            "Topics covered:",
            f"- {keywords['primary']}",
        ]

        # Add secondary keywords
        for kw in keywords["secondary"][:5]:
            description_parts.append(f"- {kw}")

        description_parts.extend([
            "",
            "Perfect for beginners and professionals looking to master industrial automation.",
            "",
            "Subscribe for more tutorials on PLCs, automation, and industrial maintenance!",
            "",
            "Timestamps:",
            "0:00 - Introduction",
            f"0:30 - What is {topic}?",
            "2:00 - Step-by-step tutorial",
            "5:00 - Examples and applications",
            "7:00 - Recap and next steps",
            "",
            "Related videos:",
            "- PLC Programming Basics",
            "- Industrial Automation Fundamentals",
            "",
            f"#PLC #Automation #IndustrialSkills #{keywords['primary'].replace(' ', '')}"
        ])

        description = "\n".join(description_parts)

        # Ensure under 5000 chars
        if len(description) > 5000:
            description = description[:4997] + "..."

        return description

    def _generate_tags(self, keywords: Dict[str, Any]) -> List[str]:
        """
        Generate 10-15 relevant tags.

        Args:
            keywords: Keyword research results

        Returns:
            List of tags (10-15 items)
        """
        tags = []

        # Primary keyword
        tags.append(keywords["primary"])

        # Secondary keywords
        tags.extend(keywords["secondary"][:5])

        # Broad category tags
        broad_tags = [
            "PLC programming",
            "industrial automation",
            "PLC tutorial",
            "automation tutorial",
            "industrial skills"
        ]
        tags.extend(broad_tags)

        # Remove duplicates and limit to 15
        tags = list(dict.fromkeys(tags))[:15]

        # Ensure at least 10 tags
        if len(tags) < 10:
            filler_tags = [
                "programming tutorial",
                "engineering tutorial",
                "technical training",
                "automation basics"
            ]
            tags.extend(filler_tags[:(10 - len(tags))])

        return tags

    def _estimate_search_volume(self, keyword: str) -> str:
        """
        Estimate search volume for keyword.

        Args:
            keyword: Keyword to analyze

        Returns:
            Volume estimate (low/medium/high)
        """
        # Simple heuristic: longer = more specific = lower volume
        if len(keyword.split()) > 4:
            return "low"
        elif len(keyword.split()) > 2:
            return "medium"
        else:
            return "high"

    def _estimate_competition(self, keyword: str) -> str:
        """
        Estimate competition level for keyword.

        Args:
            keyword: Keyword to analyze

        Returns:
            Competition level (low/medium/high)
        """
        # Simple heuristic: specific technical terms = lower competition
        technical_indicators = [
            "plc", "ladder", "hmi", "scada", "vfd",
            "siemens", "allen-bradley", "automation"
        ]

        keyword_lower = keyword.lower()
        has_technical = any(term in keyword_lower for term in technical_indicators)

        if has_technical and len(keyword.split()) > 2:
            return "low"
        elif has_technical:
            return "medium"
        else:
            return "high"

    def _estimate_ctr(self, title: str) -> float:
        """
        Estimate click-through rate based on title quality.

        Args:
            title: Video title

        Returns:
            Estimated CTR (0.0-1.0)
        """
        base_ctr = 0.05  # 5% baseline

        # Bonuses
        if 60 <= len(title) <= 70:
            base_ctr += 0.02  # Optimal length

        if any(word in title.lower() for word in ["tutorial", "guide", "how to"]):
            base_ctr += 0.01  # Clear value proposition

        if any(char in title for char in [":", "-", "|"]):
            base_ctr += 0.005  # Structured title

        return min(base_ctr, 0.15)  # Cap at 15%

    def _estimate_watch_time(self, script: str) -> int:
        """
        Estimate watch time based on script length.

        Args:
            script: Full script text

        Returns:
            Estimated watch time in minutes
        """
        # Assume 150 words per minute (average narration speed)
        word_count = len(script.split())
        minutes = word_count / 150

        return max(3, min(int(minutes), 20))  # 3-20 minute range

    def _save_metadata(self, metadata: VideoMetadata) -> None:
        """
        Save metadata to JSON file.

        Args:
            metadata: VideoMetadata to save
        """
        try:
            # Create output directory
            output_dir = Path("data/seo")
            output_dir.mkdir(parents=True, exist_ok=True)

            # Save to file
            output_path = output_dir / f"{metadata.video_id}_metadata.json"
            with open(output_path, "w") as f:
                json.dump(metadata.model_dump(), f, indent=2, default=str)

            logger.info(f"Saved metadata to {output_path}")

        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")

    # ========================================================================
    # Legacy Method Stubs (for backward compatibility)
    # ========================================================================

    def refine_title(self, topic: str, keywords: List[str]) -> str:
        """Refine title with SEO keywords + human appeal"""
        return self._generate_title(topic, keywords[0] if keywords else topic)

    def write_description(self, script: str, topic: str, keywords: Dict[str, Any]) -> str:
        """Write YouTube description with timestamps, links"""
        return self._generate_description(script, topic, keywords)

    def generate_tags(self, keywords: Dict[str, Any]) -> List[str]:
        """Generate 10-15 relevant tags"""
        return self._generate_tags(keywords)

    def assign_playlists(self, video_id: str, topic: str) -> List[str]:
        """
        Assign video to playlists (learning paths).

        Args:
            video_id: Video identifier
            topic: Main topic

        Returns:
            List of playlist IDs
        """
        # TODO: Implement playlist assignment logic
        playlists = []

        if "plc" in topic.lower():
            playlists.append("playlist:plc-basics")
        if "motor" in topic.lower():
            playlists.append("playlist:motor-control")
        if "tutorial" in topic.lower():
            playlists.append("playlist:tutorials")

        return playlists

    def ab_test_titles(self, video_id: str, current_title: str) -> Optional[str]:
        """
        A/B test titles (swap after 100 impressions).

        Args:
            video_id: Video identifier
            current_title: Current title

        Returns:
            Alternative title or None
        """
        # TODO: Implement A/B testing logic with analytics
        return None

