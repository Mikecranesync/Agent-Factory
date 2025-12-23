"""Rockwell Automation SME Agent - Phase 3 Implementation.

Specialized agent for Rockwell Automation / Allen-Bradley industrial equipment.
Handles queries about Allen-Bradley PLCs, drives, HMIs, and safety systems.

Author: Agent Factory
Created: 2025-12-23
Phase: 3/8 (SME Agents)
"""

from typing import List
from agent_factory.rivet_pro.models import AgentID
from .generic_agent import GenericAgent


class RockwellAgent(GenericAgent):
    """Rockwell Automation SME agent specialized in Allen-Bradley equipment.

    Expertise areas:
    - ControlLogix, CompactLogix PLCs (L8x, L7x, L6x, L4x, L3x)
    - MicroLogix, SLC 500 legacy PLCs
    - PowerFlex drives (525, 753, 755, AC drives)
    - PanelView HMI terminals
    - GuardLogix safety PLCs
    - Studio 5000 / RSLogix programming
    - EtherNet/IP, ControlNet, DeviceNet networks
    """

    def __init__(self, llm_router=None):
        """Initialize Rockwell agent."""
        super().__init__(llm_router)
        self.agent_id = AgentID.ROCKWELL
        self.agent_name = "Rockwell Agent"

    async def _generate_response_with_kb(self, query: str, kb_atoms: List) -> str:
        """Generate LLM response using KB atoms with Rockwell-specific context.

        Args:
            query: User's question
            kb_atoms: List of RetrievedDoc objects from KB search

        Returns:
            Generated response text
        """
        # Format KB atoms into context string
        kb_context = self._format_kb_atoms(kb_atoms)

        # Rockwell-specific system prompt
        system_prompt = """You are a Rockwell Automation-certified industrial automation specialist with 20+ years of hands-on experience with Allen-Bradley equipment.

Your expertise includes:
- PLCs: ControlLogix (L8x, L7x), CompactLogix (L3x, L4x), MicroLogix (1100, 1400, 1500), SLC 500
- Drives: PowerFlex 525, 753, 755, 40P, AC drives
- HMI: PanelView Plus 7, PanelView 5000, FactoryTalk View
- Safety: GuardLogix controllers, safety I/O modules
- Programming: Studio 5000 (Logix Designer), RSLogix 5000, RSLinx
- Networks: EtherNet/IP, ControlNet, DeviceNet, SERCOS

Common Allen-Bradley terminology you use:
- AOI (Add-On Instruction), UDT (User-Defined Type), MSG (Message) instruction
- Ladder Logic (LAD), Function Block Diagram (FBD), Structured Text (ST)
- Drive faults: Fault codes (e.g., Fault 22 = Drive Overload)
- Tag addressing: Program-scoped vs Controller-scoped tags
- I/O modules: 1756-IB16, 1769-OW8, POINT I/O, Flex I/O

Guidelines:
1. Answer based ONLY on the provided Allen-Bradley knowledge base articles
2. Use correct Rockwell terminology (e.g., "AOI" not "custom instruction", "tag" not "variable")
3. Reference specific Studio 5000 versions when relevant (V20, V21, V24, V30, V32)
4. Include drive parameter numbers for PowerFlex when applicable (e.g., Parameter 58, 31)
5. Cite sources using [Source X] notation
6. Provide step-by-step Studio 5000 navigation when applicable
7. Include module catalog numbers when referencing I/O (e.g., 1756-IB16)
8. Include safety warnings for electrical work
9. Be concise but thorough (aim for 150-300 words)

Format your response as:
- Direct answer to the question
- Relevant Allen-Bradley-specific technical details
- Step-by-step procedure in Studio 5000 (if applicable)
- Parameter settings or fault codes (if applicable)
- Module catalog numbers (if applicable)
- Safety warnings (if applicable)
- Source citations"""

        # Create user prompt with KB context
        user_prompt = f"""Allen-Bradley Knowledge Base Articles:
{kb_context}

User Question: {query}

Answer the user's question using the Allen-Bradley knowledge base articles above. Use proper Rockwell terminology and cite sources using [Source 1], [Source 2], etc."""

        # Call LLM
        from agent_factory.llm.types import LLMConfig, LLMProvider

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4o-mini",
            temperature=0.2,  # Very low temp for Allen-Bradley-specific factual responses
            max_tokens=600  # Allow slightly more for technical details
        )

        response = self.llm_router.complete(messages, config)
        return response.content

    def _generate_fallback_response(self, query: str) -> str:
        """Generate Rockwell-specific fallback response.

        Args:
            query: User's question

        Returns:
            Fallback response text
        """
        return f"""I don't have specific Allen-Bradley documentation in my knowledge base about "{query}".

To help you with your Rockwell Automation equipment, I would need:
1. Specific model/catalog number (e.g., 1756-L83E ControlLogix, PowerFlex 525)
2. Studio 5000 version you're using (if programming question)
3. Exact fault code or error message (e.g., Fault 22, Error Code 16#0042)
4. What troubleshooting steps you've already tried

Recommended next steps:
- Check Rockwell Automation Knowledgebase: https://rockwellautomation.custhelp.com
- Review the product manual for your specific catalog number
- Check Studio 5000 Help (F1 key) for programming questions
- Review drive display for detailed fault information and parameters

Would you like to provide more details so I can search my Allen-Bradley knowledge base more effectively?"""
