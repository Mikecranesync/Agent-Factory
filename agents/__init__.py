"""
Agent Factory - Autonomous Agent System

18 specialized agents organized into 5 teams:
- Executive Team (2 agents): Strategy, project management
- Research & Knowledge Base Team (4 agents): Ingest, validate, organize
- Content Production Team (5 agents): Curriculum, scripts, SEO, visuals
- Media & Publishing Team (4 agents): Voice, video, distribution
- Engagement & Analytics Team (3 agents): Community, feedback, optimization

Based on: docs/AGENT_ORGANIZATION.md
"""

# Executive Team
from agents.executive.ai_ceo_agent import AICEOAgent
from agents.executive.ai_chief_of_staff_agent import AIChiefOfStaffAgent

# Research & Knowledge Base Team
from agents.research.research_agent import ResearchAgent
from agents.research.atom_builder_agent import AtomBuilderAgent
from agents.research.atom_librarian_agent import AtomLibrarianAgent
from agents.research.quality_checker_agent import QualityCheckerAgent

# Content Production Team
from agents.content.master_curriculum_agent import MasterCurriculumAgent
from agents.content.content_strategy_agent import ContentStrategyAgent
from agents.content.scriptwriter_agent import ScriptwriterAgent
from agents.content.seo_agent import SEOAgent
from agents.content.thumbnail_agent import ThumbnailAgent

# Media & Publishing Team
from agents.media.voice_production_agent import VoiceProductionAgent
from agents.media.video_assembly_agent import VideoAssemblyAgent
from agents.media.publishing_strategy_agent import PublishingStrategyAgent
from agents.media.youtube_uploader_agent import YouTubeUploaderAgent

# Engagement & Analytics Team
from agents.engagement.community_agent import CommunityAgent
from agents.engagement.analytics_agent import AnalyticsAgent
from agents.engagement.social_amplifier_agent import SocialAmplifierAgent

__all__ = [
    # Executive
    "AICEOAgent",
    "AIChiefOfStaffAgent",
    # Research
    "ResearchAgent",
    "AtomBuilderAgent",
    "AtomLibrarianAgent",
    "QualityCheckerAgent",
    # Content
    "MasterCurriculumAgent",
    "ContentStrategyAgent",
    "ScriptwriterAgent",
    "SEOAgent",
    "ThumbnailAgent",
    # Media
    "VoiceProductionAgent",
    "VideoAssemblyAgent",
    "PublishingStrategyAgent",
    "YouTubeUploaderAgent",
    # Engagement
    "CommunityAgent",
    "AnalyticsAgent",
    "SocialAmplifierAgent",
]
