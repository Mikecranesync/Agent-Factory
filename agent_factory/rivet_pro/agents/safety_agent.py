"""Safety SME Agent - Phase 3 Implementation.

Specialized agent for industrial safety systems and safety-rated equipment.
Handles queries about safety PLCs, safety relays, light curtains, e-stops, and safety standards.

Author: Agent Factory
Created: 2025-12-23
Phase: 3/8 (SME Agents)
"""

from typing import List
from agent_factory.rivet_pro.models import AgentID
from .generic_agent import GenericAgent


class SafetyAgent(GenericAgent):
    """Safety SME agent specialized in industrial safety systems.

    Expertise areas:
    - Safety PLCs (Siemens F-Systems, GuardLogix, Pilz PSS 4000)
    - Safety relays and modules
    - Safety light curtains, laser scanners
    - Emergency stop systems
    - Safety mats and edges
    - Safety standards (ISO 13849, IEC 62061, IEC 61508)
    - Risk assessment and SIL/PLr calculations
    """

    def __init__(self, llm_router=None):
        """Initialize Safety agent."""
        super().__init__(llm_router)
        self.agent_id = AgentID.SAFETY
        self.agent_name = "Safety Agent"

    async def _generate_response_with_kb(self, query: str, kb_atoms: List) -> str:
        """Generate LLM response using KB atoms with safety-specific context.

        Args:
            query: User's question
            kb_atoms: List of RetrievedDoc objects from KB search

        Returns:
            Generated response text
        """
        # Format KB atoms into context string
        kb_context = self._format_kb_atoms(kb_atoms)

        # Safety-specific system prompt
        system_prompt = """You are a certified industrial safety specialist with 20+ years of experience in machine safety and functional safety.

Your expertise includes:
- Safety PLCs: Siemens Safety Integrated (F-CPUs), Rockwell GuardLogix, Pilz PSS 4000
- Safety I/O: Safety input/output modules, safety relays
- Safety devices: Light curtains, laser scanners, safety mats, e-stops, safety interlocks
- Safety standards: ISO 13849-1 (PLr), IEC 62061 (SIL), IEC 61508, ISO 12100
- Risk assessment: Safety category determination, PL/SIL calculation
- Safety programming: F-FBD, CIP Safety, SafetyBridge

Critical safety guidelines you ALWAYS follow:
1. NEVER suggest bypassing safety devices
2. ALWAYS emphasize lockout/tagout procedures
3. ALWAYS reference applicable safety standards
4. ALWAYS recommend qualified personnel for safety system work
5. ALWAYS include warnings about legal/liability issues

Common safety terminology you use:
- PLr (Performance Level required), SIL (Safety Integrity Level)
- Category B, 1, 2, 3, 4 (ISO 13849)
- MTTF (Mean Time To Failure), DC (Diagnostic Coverage)
- Safe state, safety function, safety-related control system

Guidelines:
1. Answer based ONLY on the provided safety knowledge base articles
2. Use correct safety terminology and standard references
3. Include applicable safety standard citations (ISO 13849, IEC 62061)
4. Provide clear warnings about safety-critical modifications
5. Emphasize need for qualified safety personnel
6. Cite sources using [Source X] notation
7. Be concise but thorough (aim for 150-300 words)

Format your response as:
- Direct answer to the question
- Relevant safety standard references
- Step-by-step safe procedure (if applicable)
- **CRITICAL SAFETY WARNINGS in bold**
- Recommendation to involve qualified safety personnel
- Source citations"""

        # Create user prompt with KB context
        user_prompt = f"""Safety Knowledge Base Articles:
{kb_context}

User Question: {query}

Answer the user's question using the safety knowledge base articles above. Include all necessary safety warnings and cite sources using [Source 1], [Source 2], etc."""

        # Call LLM
        from agent_factory.llm.types import LLMConfig, LLMProvider

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4o",  # Use premium model for safety-critical responses
            temperature=0.1,  # Extremely low temp for safety responses
            max_tokens=700  # Allow more for safety warnings
        )

        response = self.llm_router.complete(messages, config)
        return response.content

    def _generate_fallback_response(self, query: str) -> str:
        """Generate safety-specific fallback response.

        Args:
            query: User's question

        Returns:
            Fallback response text
        """
        return f"""I don't have specific safety documentation in my knowledge base about "{query}".

**CRITICAL SAFETY WARNING:**
Safety systems are designed to protect human life. Any modifications to safety systems should ONLY be performed by:
- Qualified safety personnel
- Personnel trained in applicable safety standards (ISO 13849, IEC 62061)
- Personnel authorized by your facility's safety management system

Before proceeding, you should:
1. Consult your facility's safety officer or manager
2. Review applicable safety standards for your jurisdiction
3. Ensure work complies with OSHA regulations (US) or equivalent
4. Document all safety system changes for audit trail
5. Perform risk assessment before and after changes

Recommended resources:
- Equipment manufacturer's safety manual
- ISO 13849-1: Safety of machinery - Safety-related parts of control systems
- IEC 62061: Safety of machinery - Functional safety
- OSHA 1910.147: Lockout/Tagout procedures
- Hire a certified safety consultant if in doubt

**DO NOT bypass, disable, or modify safety devices without proper authorization and risk assessment.**

Would you like to provide more specific details about your safety question?"""
