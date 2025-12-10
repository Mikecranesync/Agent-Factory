"""
PLC Agents Package

15 autonomous agents organized into 3 teams:
- Product & Engineering (5 agents): Data collection, validation, code generation
- Content & Media (4 agents): Education, video, social
- Business & GTM (6 agents): Pricing, sales, analytics, partnerships
"""

from .product_engineering import *
from .content_media import *
from .business_gtm import *

__all__ = [
    # Product & Engineering
    "PLCTextbookScraperAgent",
    "VendorManualScraperAgent",
    "AtomValidatorAgent",
    "AtomPublisherAgent",
    "DuplicateDetectorAgent",

    # Content & Media
    "TutorialWriterAgent",
    "CodeGeneratorAgent",
    "VideoProducerAgent",
    "SocialMediaAgent",

    # Business & GTM
    "PricingAnalystAgent",
    "SalesAgentBDR",
    "CommunityManagerAgent",
    "AnalyticsAgent",
    "PartnershipAgent",
    "CustomerSuccessAgent",
]
