"""Siemens SME Agent - Phase 3 Implementation.

Specialized agent for Siemens industrial automation equipment.
Handles queries about Siemens PLCs, drives, HMIs, and safety systems.

Author: Agent Factory
Created: 2025-12-23
Phase: 3/8 (SME Agents)
"""

from typing import List
from agent_factory.rivet_pro.models import AgentID
from .generic_agent import GenericAgent


class SiemensAgent(GenericAgent):
    """Siemens SME agent specialized in Siemens industrial automation.

    Expertise areas:
    - SIMATIC S7 PLCs (S7-300, S7-400, S7-1200, S7-1500)
    - SINAMICS drives (G120, G130, S120, V20, V90)
    - TIA Portal programming environment
    - WinCC HMI systems
    - Safety Integrated (F-Systems)
    - PROFINET and PROFIBUS networks
    """

    def __init__(self, llm_router=None):
        """Initialize Siemens agent."""
        super().__init__(llm_router)
        self.agent_id = AgentID.SIEMENS
        self.agent_name = "Siemens Agent"

    async def _generate_response_with_kb(self, query: str, kb_atoms: List) -> str:
        """Generate LLM response using KB atoms with Siemens-specific context.

        Args:
            query: User's question
            kb_atoms: List of RetrievedDoc objects from KB search

        Returns:
            Generated response text
        """
        # Format KB atoms into context string
        kb_context = self._format_kb_atoms(kb_atoms)

        # Siemens-specific system prompt
        system_prompt = """You are a Siemens-certified industrial automation specialist with 20+ years of hands-on experience with Siemens equipment.

Your expertise includes:
- SIMATIC S7 PLCs: S7-300, S7-400, S7-1200, S7-1500, ET200 distributed I/O
- SINAMICS drives: G120, G130, S120, V20, V90 (servo drives)
- TIA Portal: Programming, configuration, diagnostics
- WinCC HMI: Panels, SCADA, runtime systems
- Safety Integrated: F-CPUs, F-I/O, safety programming
- Industrial communication: PROFINET, PROFIBUS, Ethernet/IP
- Motion control: SIMOTION, Technology Objects

Common Siemens terminology you use:
- FB (Function Block), FC (Function), DB (Data Block), OB (Organization Block)
- STL (Statement List), LAD (Ladder Logic), FBD (Function Block Diagram)
- Drive faults: F codes (e.g., F0001 = overcurrent)
- Tag addressing: %I (inputs), %Q (outputs), %M (memory), %DB (data blocks)

Guidelines:
1. Answer based ONLY on the provided Siemens knowledge base articles
2. Use correct Siemens terminology (e.g., "FB" not "function block", "PROFINET" not "ethernet")
3. Reference specific TIA Portal versions when relevant (V13, V14, V15, V16, V17)
4. Include drive parameter numbers for SINAMICS when applicable (e.g., P0010, r0052)
5. Cite sources using [Source X] notation
6. Provide step-by-step TIA Portal navigation when applicable
7. Include safety warnings for electrical work
8. Be concise but thorough (aim for 150-300 words)

Format your response as:
- Direct answer to the question
- Relevant Siemens-specific technical details
- Step-by-step procedure in TIA Portal (if applicable)
- Parameter settings or drive codes (if applicable)
- Safety warnings (if applicable)
- Source citations"""

        # Create user prompt with KB context
        user_prompt = f"""Siemens Knowledge Base Articles:
{kb_context}

User Question: {query}

Answer the user's question using the Siemens knowledge base articles above. Use proper Siemens terminology and cite sources using [Source 1], [Source 2], etc."""

        # Call LLM
        from agent_factory.llm.types import LLMConfig, LLMProvider

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4o-mini",
            temperature=0.2,  # Very low temp for Siemens-specific factual responses
            max_tokens=600  # Allow slightly more for technical details
        )

        response = self.llm_router.complete(messages, config)
        return response.content

    def _generate_fallback_response(self, query: str) -> str:
        """Generate Siemens-specific fallback response.

        Args:
            query: User's question

        Returns:
            Fallback response text
        """
        return f"""I don't have specific Siemens documentation in my knowledge base about "{query}".

To help you with your Siemens equipment, I would need:
1. Specific model number (e.g., S7-1200 CPU 1214C, G120 PM240-2)
2. TIA Portal version you're using (if programming question)
3. Exact fault code (e.g., F0001, A0502) or error message
4. What you've already tried

Recommended next steps:
- Check Siemens Industry Online Support: https://support.industry.siemens.com
- Review the equipment manual for your specific model
- Search TIA Portal Help (F1 key) for programming questions
- Check SINAMICS drive display for detailed fault information

Would you like to provide more details so I can search my Siemens knowledge base more effectively?"""
