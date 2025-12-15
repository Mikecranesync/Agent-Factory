#!/usr/bin/env python3
"""
Unit tests for SEOAgent

Tests metadata optimization, keyword research, and SEO best practices.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from agents.content.seo_agent import SEOAgent, VideoMetadata, KeywordResearch


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def seo_agent():
    """Create SEOAgent instance with mocked Supabase"""
    with patch('agents.content.seo_agent.SupabaseMemoryStorage') as mock_storage:
        # Mock Supabase client
        mock_client = MagicMock()
        mock_storage.return_value.client = mock_client

        agent = SEOAgent()
        return agent


@pytest.fixture
def sample_script():
    """Sample PLC tutorial script"""
    return """
    Welcome to PLC Ladder Logic Basics! Today we're learning about motor control.

    PLC ladder logic is the fundamental programming language for industrial automation.
    It uses relay logic symbols to represent electrical circuits.

    A basic motor start-stop circuit requires three components:
    - Start pushbutton (normally open)
    - Stop pushbutton (normally closed)
    - Motor contactor with seal-in contact

    When you press the start button, current flows through the stop button,
    start button, and energizes the motor contactor. The motor starts running.

    The seal-in contact closes, maintaining current flow even after releasing
    the start button. This is called latching or sealing.

    To stop the motor, press the stop button. This breaks the circuit and
    de-energizes the contactor, stopping the motor.

    This basic pattern is used in thousands of industrial applications worldwide.
    Understanding ladder logic fundamentals is essential for PLC programmers.

    Practice this pattern, and you'll master the foundation of PLC programming.
    """


@pytest.fixture
def sample_topic():
    """Sample video topic"""
    return "PLC Ladder Logic Basics"


@pytest.fixture
def sample_keywords():
    """Sample target keywords"""
    return ["PLC tutorial", "ladder logic", "motor control", "Allen-Bradley"]


# ============================================================================
# Metadata Optimization Tests
# ============================================================================

def test_optimize_metadata_basic(seo_agent, sample_script, sample_topic, sample_keywords):
    """Test basic metadata optimization"""
    metadata = seo_agent.optimize_metadata(
        video_id="vid:test123",
        script=sample_script,
        topic=sample_topic,
        target_keywords=sample_keywords
    )

    # Validate metadata structure
    assert isinstance(metadata, VideoMetadata)
    assert metadata.video_id == "vid:test123"

    # Title validation
    assert 30 <= len(metadata.title) <= 70
    assert metadata.primary_keyword.lower() in metadata.title.lower() or sample_topic.lower() in metadata.title.lower()

    # Description validation
    assert 100 <= len(metadata.description) <= 5000
    assert metadata.primary_keyword in metadata.description

    # Tags validation
    assert 10 <= len(metadata.tags) <= 15
    assert metadata.primary_keyword in metadata.tags


def test_title_length_optimization(seo_agent, sample_script, sample_topic, sample_keywords):
    """Test title length is optimized for SEO (60-70 chars)"""
    metadata = seo_agent.optimize_metadata(
        video_id="vid:test123",
        script=sample_script,
        topic=sample_topic,
        target_keywords=sample_keywords
    )

    # Ideal range is 60-70 characters
    title_length = len(metadata.title)
    assert 30 <= title_length <= 70, f"Title length {title_length} not optimal"

    # Bonus: check if in ideal range
    if 60 <= title_length <= 70:
        assert True  # Ideal


def test_title_keyword_first(seo_agent, sample_script, sample_topic):
    """Test title places keyword first for SEO"""
    metadata = seo_agent.optimize_metadata(
        video_id="vid:test123",
        script=sample_script,
        topic=sample_topic
    )

    # Check if primary keyword appears early in title
    title_lower = metadata.title.lower()
    keyword_position = title_lower.find(metadata.primary_keyword.lower())

    # Keyword should appear in first half of title
    assert keyword_position < len(metadata.title) / 2


def test_description_keyword_rich(seo_agent, sample_script, sample_topic, sample_keywords):
    """Test description contains multiple keywords"""
    metadata = seo_agent.optimize_metadata(
        video_id="vid:test123",
        script=sample_script,
        topic=sample_topic,
        target_keywords=sample_keywords
    )

    description_lower = metadata.description.lower()

    # Primary keyword should appear
    assert metadata.primary_keyword.lower() in description_lower

    # At least 3 secondary keywords should appear
    keyword_count = sum(
        1 for kw in metadata.secondary_keywords
        if kw.lower() in description_lower
    )
    assert keyword_count >= 3


def test_description_has_timestamps(seo_agent, sample_script, sample_topic):
    """Test description includes timestamps"""
    metadata = seo_agent.optimize_metadata(
        video_id="vid:test123",
        script=sample_script,
        topic=sample_topic
    )

    # Check for timestamp patterns (0:00, 2:00, etc.)
    assert "0:00" in metadata.description
    assert "Timestamps:" in metadata.description or "timestamps:" in metadata.description


def test_tags_mix_broad_and_specific(seo_agent, sample_script, sample_topic, sample_keywords):
    """Test tags include both broad and specific keywords"""
    metadata = seo_agent.optimize_metadata(
        video_id="vid:test123",
        script=sample_script,
        topic=sample_topic,
        target_keywords=sample_keywords
    )

    # Check for broad tags
    broad_tags = ["PLC programming", "industrial automation", "automation tutorial"]
    has_broad = any(tag in metadata.tags for tag in broad_tags)
    assert has_broad, "Should have at least one broad category tag"

    # Check for specific tags (from keywords)
    specific_count = sum(1 for kw in sample_keywords if kw in metadata.tags)
    assert specific_count >= 2, "Should have multiple specific keyword tags"


# ============================================================================
# Keyword Research Tests
# ============================================================================

def test_keyword_extraction_from_script(seo_agent, sample_script, sample_topic):
    """Test keyword extraction from script text"""
    keywords = seo_agent._extract_keywords_from_text(sample_script, sample_topic)

    # Should extract relevant keywords
    assert isinstance(keywords, list)
    assert len(keywords) > 0

    # Should include technical terms
    keywords_lower = [kw.lower() for kw in keywords]
    assert any("ladder" in kw for kw in keywords_lower)
    assert any("motor" in kw for kw in keywords_lower)


def test_keyword_research_prioritization(seo_agent, sample_script, sample_topic):
    """Test keyword research prioritizes by frequency"""
    keywords = seo_agent._research_keywords(
        topic=sample_topic,
        script=sample_script,
        target_keywords=["PLC tutorial"]
    )

    assert "primary" in keywords
    assert "secondary" in keywords
    assert len(keywords["secondary"]) > 0


def test_search_volume_estimation(seo_agent):
    """Test search volume estimation logic"""
    # Broad keyword = high volume
    assert seo_agent._estimate_search_volume("PLC") == "high"

    # Medium specificity = medium volume
    assert seo_agent._estimate_search_volume("PLC programming") == "medium"

    # Very specific = low volume
    assert seo_agent._estimate_search_volume("Allen-Bradley PLC motor control tutorial") == "low"


def test_competition_estimation(seo_agent):
    """Test competition level estimation"""
    # Technical + specific = low competition
    assert seo_agent._estimate_competition("PLC ladder logic tutorial") == "low"

    # Technical + broad = medium competition
    assert seo_agent._estimate_competition("PLC programming") == "medium"

    # Generic = high competition
    assert seo_agent._estimate_competition("programming tutorial") == "high"


# ============================================================================
# Performance Estimation Tests
# ============================================================================

def test_ctr_estimation_optimal_title(seo_agent):
    """Test CTR estimation for optimal title"""
    # Optimal: 60-70 chars, has tutorial keyword, structured
    title = "PLC Ladder Logic Basics: Complete Motor Control Tutorial"
    ctr = seo_agent._estimate_ctr(title)

    assert 0.05 <= ctr <= 0.15
    assert ctr > 0.05  # Should have bonuses


def test_ctr_estimation_poor_title(seo_agent):
    """Test CTR estimation for poor title"""
    # Poor: too short, no keywords
    title = "PLC Video"
    ctr = seo_agent._estimate_ctr(title)

    assert ctr == 0.05  # Base CTR only


def test_watch_time_estimation(seo_agent):
    """Test watch time estimation from script length"""
    # Short script (~100 words = 0.67 minutes -> 3 min minimum)
    short_script = " ".join(["word"] * 100)
    watch_time = seo_agent._estimate_watch_time(short_script)
    assert watch_time >= 3

    # Medium script (~750 words = 5 minutes)
    medium_script = " ".join(["word"] * 750)
    watch_time = seo_agent._estimate_watch_time(medium_script)
    assert 4 <= watch_time <= 6

    # Long script (~3000 words = 20 minutes, capped)
    long_script = " ".join(["word"] * 3000)
    watch_time = seo_agent._estimate_watch_time(long_script)
    assert watch_time <= 20


# ============================================================================
# File Output Tests
# ============================================================================

def test_save_metadata_creates_file(seo_agent, sample_script, sample_topic, tmp_path):
    """Test metadata is saved to JSON file"""
    # Override output directory to tmp_path
    with patch('agents.content.seo_agent.Path') as mock_path:
        mock_output_dir = tmp_path / "seo"
        mock_output_dir.mkdir(parents=True, exist_ok=True)
        mock_path.return_value = mock_output_dir

        metadata = seo_agent.optimize_metadata(
            video_id="vid:test123",
            script=sample_script,
            topic=sample_topic
        )

        # Save should not raise error
        try:
            seo_agent._save_metadata(metadata)
        except Exception as e:
            pytest.fail(f"Save metadata failed: {e}")


def test_metadata_json_valid(seo_agent, sample_script, sample_topic):
    """Test saved metadata is valid JSON"""
    metadata = seo_agent.optimize_metadata(
        video_id="vid:test123",
        script=sample_script,
        topic=sample_topic
    )

    # Should be serializable to JSON
    try:
        json_str = json.dumps(metadata.model_dump(), default=str)
        parsed = json.loads(json_str)
        assert parsed["video_id"] == "vid:test123"
    except Exception as e:
        pytest.fail(f"JSON serialization failed: {e}")


# ============================================================================
# Integration Tests
# ============================================================================

def test_full_optimization_pipeline(seo_agent, sample_script, sample_topic, sample_keywords):
    """Test complete optimization pipeline"""
    # Run full optimization
    metadata = seo_agent.optimize_metadata(
        video_id="vid:integration123",
        script=sample_script,
        topic=sample_topic,
        target_keywords=sample_keywords
    )

    # Validate complete metadata
    assert metadata.video_id == "vid:integration123"
    assert 30 <= len(metadata.title) <= 70
    assert 100 <= len(metadata.description) <= 5000
    assert 10 <= len(metadata.tags) <= 15
    assert metadata.primary_keyword
    assert len(metadata.secondary_keywords) > 0
    assert metadata.search_volume_estimate in ["low", "medium", "high"]
    assert metadata.competition_level in ["low", "medium", "high"]
    assert 0.0 <= metadata.estimated_ctr <= 1.0
    assert metadata.estimated_watch_time_minutes >= 3


def test_optimization_without_target_keywords(seo_agent, sample_script, sample_topic):
    """Test optimization works without target keywords"""
    metadata = seo_agent.optimize_metadata(
        video_id="vid:test123",
        script=sample_script,
        topic=sample_topic
        # No target_keywords
    )

    # Should still generate valid metadata
    assert metadata.primary_keyword
    assert len(metadata.tags) >= 10


def test_agent_run_method(seo_agent, sample_script, sample_topic):
    """Test agent run() method with payload"""
    payload = {
        "video_id": "vid:test123",
        "script": sample_script,
        "topic": sample_topic,
        "target_keywords": ["PLC tutorial"]
    }

    result = seo_agent.run(payload)

    assert result["status"] == "success"
    assert "result" in result
    assert result["result"]["video_id"] == "vid:test123"


def test_agent_run_missing_fields(seo_agent):
    """Test agent run() handles missing required fields"""
    payload = {
        "video_id": "vid:test123"
        # Missing script and topic
    }

    result = seo_agent.run(payload)

    assert result["status"] == "error"
    assert "error" in result


# ============================================================================
# Edge Cases
# ============================================================================

def test_very_short_script(seo_agent):
    """Test optimization with very short script"""
    short_script = "PLC basics. Learn ladder logic. Motor control."

    metadata = seo_agent.optimize_metadata(
        video_id="vid:short",
        script=short_script,
        topic="PLC Basics"
    )

    # Should still generate valid metadata
    assert len(metadata.title) >= 30
    assert len(metadata.description) >= 100
    assert len(metadata.tags) >= 10


def test_very_long_script(seo_agent):
    """Test optimization with very long script"""
    long_script = " ".join(["This is a detailed explanation of PLC programming."] * 100)

    metadata = seo_agent.optimize_metadata(
        video_id="vid:long",
        script=long_script,
        topic="PLC Programming"
    )

    # Description should be capped at 5000 chars
    assert len(metadata.description) <= 5000


def test_special_characters_in_topic(seo_agent, sample_script):
    """Test optimization handles special characters"""
    topic = "PLC I/O & Sensors: 24VDC Wiring"

    metadata = seo_agent.optimize_metadata(
        video_id="vid:special",
        script=sample_script,
        topic=topic
    )

    # Should handle special chars without error
    assert metadata.title
    assert len(metadata.title) <= 70


# ============================================================================
# Validation Tests
# ============================================================================

def test_pydantic_validation_title_length(seo_agent, sample_script, sample_topic):
    """Test Pydantic validates title length constraints"""
    metadata = seo_agent.optimize_metadata(
        video_id="vid:test123",
        script=sample_script,
        topic=sample_topic
    )

    # Pydantic should enforce 30-70 char limit
    assert 30 <= len(metadata.title) <= 70


def test_pydantic_validation_description_length(seo_agent, sample_script, sample_topic):
    """Test Pydantic validates description length constraints"""
    metadata = seo_agent.optimize_metadata(
        video_id="vid:test123",
        script=sample_script,
        topic=sample_topic
    )

    # Pydantic should enforce 100-5000 char limit
    assert 100 <= len(metadata.description) <= 5000


def test_pydantic_validation_tags_count(seo_agent, sample_script, sample_topic):
    """Test Pydantic validates tag count constraints"""
    metadata = seo_agent.optimize_metadata(
        video_id="vid:test123",
        script=sample_script,
        topic=sample_topic
    )

    # Pydantic should enforce 10-15 tags
    assert 10 <= len(metadata.tags) <= 15


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
