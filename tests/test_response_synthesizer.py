"""
Tests for Response Synthesizer - Citations, Safety Warnings, and Formatting.

Tests cover:
- Citation formatting (inline [1], [2] + footer)
- Safety warning injection (DANGER, WARNING, CAUTION)
- Troubleshooting step formatting
- Confidence badges
- Feature flag toggling
"""

import pytest
from agent_factory.rivet_pro.response_synthesizer import ResponseSynthesizer, SafetyWarning
from agent_factory.rivet_pro.models import RivetResponse, RivetRequest, KBCoverage, VendorType, AgentID, RouteType


class TestCitationFormatting:
    """Test citation formatting (inline + footer)."""

    def test_inline_citations(self):
        """Test inline citation insertion [1], [2]."""
        synthesizer = ResponseSynthesizer()

        # Create response with sources
        sources = [
            {"title": "Siemens G120C Manual", "page": 45, "url": "https://siemens.com/manual"},
            {"title": "PowerFlex 525 Troubleshooting", "page": 12, "url": "https://rockwell.com/manual"}
        ]

        response = RivetResponse(
            text="The Siemens G120C Manual recommends checking DC bus voltage. Also see PowerFlex 525 Troubleshooting guide.",
            agent_id=AgentID.SIEMENS,
            route_taken=RouteType.ROUTE_A,
            confidence=0.9,
            sources=sources
        )

        request = RivetRequest(text="How to troubleshoot VFD?")

        # Synthesize
        enhanced = synthesizer.synthesize(
            response=response,
            kb_coverage=KBCoverage.STRONG,
            vendor=VendorType.SIEMENS,
            request=request
        )

        # Check inline citations added
        assert "[1]" in enhanced.answer_text
        assert "[2]" in enhanced.answer_text
        assert "Siemens G120C Manual [1]" in enhanced.answer_text

    def test_citation_footer(self):
        """Test citation footer formatting."""
        synthesizer = ResponseSynthesizer()

        sources = [
            {"title": "Siemens G120C Manual", "page": 45, "url": "https://siemens.com/manual"},
            {"title": "PowerFlex 525 Guide", "page": 12}  # No URL
        ]

        response = RivetResponse(
            text="Check voltage levels.",
            agent_id=AgentID.SIEMENS,
            confidence=0.9,
            sources=sources
        )

        request = RivetRequest(text="How to troubleshoot?")

        enhanced = synthesizer.synthesize(
            response=response,
            kb_coverage=KBCoverage.STRONG,
            vendor=VendorType.SIEMENS,
            request=request
        )

        # Check footer format
        assert "📚 **Sources:**" in enhanced.answer_text
        assert "[1] Siemens G120C Manual, Page 45 (https://siemens.com/manual)" in enhanced.answer_text
        assert "[2] PowerFlex 525 Guide, Page 12" in enhanced.answer_text

    def test_no_sources_no_citations(self):
        """Test no citations added when sources empty."""
        synthesizer = ResponseSynthesizer()

        response = RivetResponse(
            text="Check voltage levels.",
            agent_id=AgentID.GENERIC_PLC,
            confidence=0.7,
            sources=[]
        )

        request = RivetRequest(text="How to troubleshoot?")

        enhanced = synthesizer.synthesize(
            response=response,
            kb_coverage=KBCoverage.THIN,
            vendor=VendorType.GENERIC,
            request=request
        )

        # No citations added
        assert "[1]" not in enhanced.answer_text
        assert "📚 **Sources:**" not in enhanced.answer_text


class TestSafetyWarnings:
    """Test safety warning injection."""

    def test_danger_warnings_high_voltage(self):
        """Test DANGER warning for high voltage mentions."""
        synthesizer = ResponseSynthesizer()

        response = RivetResponse(
            text="Check the 480V panel. Verify arc flash boundaries.",
            agent_id=AgentID.GENERIC_PLC,
            confidence=0.8
        )

        request = RivetRequest(text="How to troubleshoot 480V panel?")

        enhanced = synthesizer.synthesize(
            response=response,
            kb_coverage=KBCoverage.STRONG,
            vendor=VendorType.GENERIC,
            request=request
        )

        # Check DANGER warning added
        assert "🛡️ **SAFETY FIRST**" in enhanced.answer_text
        assert "🔴" in enhanced.answer_text
        assert "DANGER" in enhanced.answer_text
        assert "De-energize" in enhanced.answer_text
        assert "NFPA 70E" in enhanced.answer_text

    def test_warning_vfd_capacitors(self):
        """Test WARNING for VFD/capacitor mentions."""
        synthesizer = ResponseSynthesizer()

        response = RivetResponse(
            text="Check VFD DC bus voltage.",
            agent_id=AgentID.SIEMENS,
            confidence=0.9
        )

        request = RivetRequest(text="How to troubleshoot VFD fault?")

        enhanced = synthesizer.synthesize(
            response=response,
            kb_coverage=KBCoverage.STRONG,
            vendor=VendorType.SIEMENS,
            request=request
        )

        # Check VFD-specific warning
        assert "⚠️" in enhanced.answer_text
        assert "VFD Safety" in enhanced.answer_text
        assert "5+ minutes" in enhanced.answer_text
        assert "multimeter" in enhanced.answer_text

    def test_vendor_specific_vfd_warnings(self):
        """Test vendor-specific VFD safety warnings."""
        synthesizer = ResponseSynthesizer()

        # Siemens
        response_siemens = RivetResponse(
            text="Check drive DC bus.",
            agent_id=AgentID.SIEMENS,
            confidence=0.9
        )

        enhanced_siemens = synthesizer.synthesize(
            response=response_siemens,
            kb_coverage=KBCoverage.STRONG,
            vendor=VendorType.SIEMENS,
            request=RivetRequest(text="VFD troubleshooting")
        )

        assert "Siemens drives" in enhanced_siemens.answer_text

        # Rockwell
        response_rockwell = RivetResponse(
            text="Check drive DC bus.",
            agent_id=AgentID.ROCKWELL,
            confidence=0.9
        )

        enhanced_rockwell = synthesizer.synthesize(
            response=response_rockwell,
            kb_coverage=KBCoverage.STRONG,
            vendor=VendorType.ROCKWELL,
            request=RivetRequest(text="VFD troubleshooting")
        )

        assert "PowerFlex drives" in enhanced_rockwell.answer_text

    def test_default_loto_reminder(self):
        """Test default LOTO reminder when no specific hazard."""
        synthesizer = ResponseSynthesizer()

        response = RivetResponse(
            text="Check motor bearings for wear.",
            agent_id=AgentID.GENERIC_PLC,
            confidence=0.8
        )

        request = RivetRequest(text="How to inspect motor?")

        enhanced = synthesizer.synthesize(
            response=response,
            kb_coverage=KBCoverage.STRONG,
            vendor=VendorType.GENERIC,
            request=request
        )

        # Check default LOTO reminder
        assert "🛡️ **SAFETY FIRST**" in enhanced.answer_text
        assert "lockout/tagout" in enhanced.answer_text.lower() or "loto" in enhanced.answer_text.lower()


class TestStepFormatting:
    """Test troubleshooting step formatting."""

    def test_numbered_list_formatting(self):
        """Test numbered list gets checkboxes."""
        synthesizer = ResponseSynthesizer()

        response = RivetResponse(
            text="Follow these steps:\n1. Check voltage\n2. Inspect wiring\n3. Reset fault",
            agent_id=AgentID.GENERIC_PLC,
            confidence=0.9
        )

        request = RivetRequest(text="How to troubleshoot?")

        enhanced = synthesizer.synthesize(
            response=response,
            kb_coverage=KBCoverage.STRONG,
            vendor=VendorType.GENERIC,
            request=request
        )

        # Check checkboxes added
        assert "☐ 1. Check voltage" in enhanced.answer_text
        assert "☐ 2. Inspect wiring" in enhanced.answer_text
        assert "☐ 3. Reset fault" in enhanced.answer_text

    def test_step_keyword_detection(self):
        """Test step detection from keywords."""
        synthesizer = ResponseSynthesizer()

        response = RivetResponse(
            text="Step 1: Check voltage.\nStep 2: Inspect wiring.",
            agent_id=AgentID.GENERIC_PLC,
            confidence=0.9
        )

        # Should detect "step" keyword
        assert synthesizer._has_steps(response.text)

    def test_no_step_formatting_when_no_steps(self):
        """Test no formatting applied when no steps detected."""
        synthesizer = ResponseSynthesizer()

        response = RivetResponse(
            text="This is a general response without steps.",
            agent_id=AgentID.GENERIC_PLC,
            confidence=0.8
        )

        request = RivetRequest(text="What is a PLC?")

        enhanced = synthesizer.synthesize(
            response=response,
            kb_coverage=KBCoverage.STRONG,
            vendor=VendorType.GENERIC,
            request=request
        )

        # No checkboxes added
        assert "☐" not in enhanced.answer_text


class TestConfidenceBadges:
    """Test confidence indicator badges."""

    def test_strong_coverage_badge(self):
        """Test HIGH CONFIDENCE badge for strong KB coverage."""
        synthesizer = ResponseSynthesizer()

        response = RivetResponse(
            text="Answer based on strong KB coverage.",
            agent_id=AgentID.SIEMENS,
            confidence=0.95
        )

        request = RivetRequest(text="How to troubleshoot?")

        enhanced = synthesizer.synthesize(
            response=response,
            kb_coverage=KBCoverage.STRONG,
            vendor=VendorType.SIEMENS,
            request=request
        )

        # Check HIGH CONFIDENCE badge
        assert "✅ **High Confidence**" in enhanced.answer_text
        assert "Strong knowledge base coverage" in enhanced.answer_text

    def test_thin_coverage_badge(self):
        """Test LIMITED COVERAGE badge for thin KB coverage."""
        synthesizer = ResponseSynthesizer()

        response = RivetResponse(
            text="Answer based on limited documentation.",
            agent_id=AgentID.GENERIC_PLC,
            confidence=0.7
        )

        request = RivetRequest(text="How to troubleshoot?")

        enhanced = synthesizer.synthesize(
            response=response,
            kb_coverage=KBCoverage.THIN,
            vendor=VendorType.GENERIC,
            request=request
        )

        # Check LIMITED COVERAGE badge
        assert "⚠️ **Limited Coverage**" in enhanced.answer_text
        assert "available documentation" in enhanced.answer_text

    def test_no_coverage_badge(self):
        """Test LOW CONFIDENCE badge for no KB coverage."""
        synthesizer = ResponseSynthesizer()

        response = RivetResponse(
            text="Answer based on general knowledge.",
            agent_id=AgentID.GENERIC_PLC,
            confidence=0.5
        )

        request = RivetRequest(text="How to troubleshoot?")

        enhanced = synthesizer.synthesize(
            response=response,
            kb_coverage=KBCoverage.NONE,
            vendor=VendorType.GENERIC,
            request=request
        )

        # Check LOW CONFIDENCE badge
        assert "❓ **Low Confidence**" in enhanced.answer_text
        assert "expert call" in enhanced.answer_text


class TestFeatureFlags:
    """Test feature flag toggling."""

    def test_disable_citations(self):
        """Test citations disabled via feature flag."""
        synthesizer = ResponseSynthesizer(enable_citations=False)

        sources = [{"title": "Manual", "page": 45, "url": "https://example.com"}]

        response = RivetResponse(
            text="Check voltage levels.",
            agent_id=AgentID.GENERIC_PLC,
            confidence=0.9,
            sources=sources
        )

        request = RivetRequest(text="How to troubleshoot?")

        enhanced = synthesizer.synthesize(
            response=response,
            kb_coverage=KBCoverage.STRONG,
            vendor=VendorType.GENERIC,
            request=request
        )

        # No citations added
        assert "[1]" not in enhanced.answer_text
        assert "📚 **Sources:**" not in enhanced.answer_text

    def test_disable_safety(self):
        """Test safety warnings disabled via feature flag."""
        synthesizer = ResponseSynthesizer(enable_safety=False)

        response = RivetResponse(
            text="Check 480V panel.",
            agent_id=AgentID.GENERIC_PLC,
            confidence=0.9
        )

        request = RivetRequest(text="How to troubleshoot 480V panel?")

        enhanced = synthesizer.synthesize(
            response=response,
            kb_coverage=KBCoverage.STRONG,
            vendor=VendorType.GENERIC,
            request=request
        )

        # No safety warnings added
        assert "🛡️ **SAFETY FIRST**" not in enhanced.answer_text
        assert "DANGER" not in enhanced.answer_text


class TestIntegrationScenarios:
    """Test complete synthesis with all features."""

    def test_full_synthesis_route_a(self):
        """Test complete synthesis for Route A (strong KB)."""
        synthesizer = ResponseSynthesizer()

        sources = [
            {"title": "Siemens G120C Manual", "page": 45, "url": "https://siemens.com/manual"}
        ]

        response = RivetResponse(
            text="The Siemens G120C Manual recommends these steps:\n1. Check DC bus voltage\n2. Inspect capacitors\n3. Reset drive",
            agent_id=AgentID.SIEMENS,
            confidence=0.95,
            sources=sources
        )

        request = RivetRequest(text="How to troubleshoot VFD fault F3002?")

        enhanced = synthesizer.synthesize(
            response=response,
            kb_coverage=KBCoverage.STRONG,
            vendor=VendorType.SIEMENS,
            request=request
        )

        # Check all features applied
        # 1. Confidence badge
        assert "✅ **High Confidence**" in enhanced.answer_text

        # 2. Safety warnings
        assert "🛡️ **SAFETY FIRST**" in enhanced.answer_text
        assert "VFD Safety" in enhanced.answer_text

        # 3. Inline citations
        assert "[1]" in enhanced.answer_text

        # 4. Citation footer
        assert "📚 **Sources:**" in enhanced.answer_text
        assert "[1] Siemens G120C Manual, Page 45" in enhanced.answer_text

        # 5. Step checkboxes
        assert "☐ 1. Check DC bus voltage" in enhanced.answer_text

    def test_full_synthesis_route_c(self):
        """Test complete synthesis for Route C (no KB, LLM fallback)."""
        synthesizer = ResponseSynthesizer()

        response = RivetResponse(
            text="Based on general knowledge, check voltage levels and inspect wiring.",
            agent_id=AgentID.GENERIC_PLC,
            confidence=0.5
        )

        request = RivetRequest(text="How to troubleshoot unknown device?")

        enhanced = synthesizer.synthesize(
            response=response,
            kb_coverage=KBCoverage.NONE,
            vendor=VendorType.GENERIC,
            request=request
        )

        # Check features applied
        # 1. Low confidence badge
        assert "❓ **Low Confidence**" in enhanced.answer_text

        # 2. Default LOTO reminder
        assert "🛡️ **SAFETY FIRST**" in enhanced.answer_text

        # 3. No citations (no sources)
        assert "📚 **Sources:**" not in enhanced.answer_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
