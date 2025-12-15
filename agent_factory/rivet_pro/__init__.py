"""
RIVET Pro - Monetizable Industrial Troubleshooting Platform

This module provides the core functionality for RIVET Pro, a tiered troubleshooting
service that transforms the Agent Factory knowledge base into a revenue-generating
platform.

Features:
- Intent detection for troubleshooting questions
- Confidence scoring and quality gates
- Tiered access control (Free, Pro, Premium, Enterprise)
- Expert marketplace integration
- Conversion funnel tracking

Components:
- intent_detector: Classifies questions and extracts equipment details
- confidence_scorer: Scores answer quality and triggers upsells
- subscription_manager: Manages user tiers and limits
- expert_matcher: Finds and books expert technicians
"""

from agent_factory.rivet_pro.intent_detector import (
    IntentDetector,
    TroubleshootingIntent,
    EquipmentInfo,
)
from agent_factory.rivet_pro.confidence_scorer import (
    ConfidenceScorer,
    AnswerQuality,
)
from agent_factory.rivet_pro.database import (
    RIVETProDatabase,
)

__all__ = [
    "IntentDetector",
    "TroubleshootingIntent",
    "EquipmentInfo",
    "ConfidenceScorer",
    "AnswerQuality",
    "RIVETProDatabase",
]

__version__ = "1.0.0"
