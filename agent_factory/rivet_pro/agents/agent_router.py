"""
Agent Router for RIVET Pro Phase 3.

Routes classified intents to the appropriate SME agent based on:
1. Equipment type (safety has highest priority)
2. Vendor identification
3. Fallback to generic agent
"""

from typing import Optional

from agent_factory.rivet_pro.models import RivetIntent, VendorType, EquipmentType
from agent_factory.rivet_pro.agents.base_sme_agent import BaseSMEAgent
from agent_factory.rivet_pro.agents.generic_plc_agent import GenericPLCAgent
from agent_factory.rivet_pro.agents.siemens_agent import SiemensAgent
from agent_factory.rivet_pro.agents.rockwell_agent import RockwellAgent
from agent_factory.rivet_pro.agents.safety_agent import SafetyAgent


class AgentRouter:
    """
    Routes intents to appropriate SME agents.

    Routing priority:
    1. **Safety equipment** → SafetyAgent (highest priority)
    2. **Known vendor** → Vendor-specific agent
    3. **Unknown vendor** → GenericPLCAgent (fallback)

    This ensures safety-critical systems always get specialist review
    and vendor-specific questions get expert knowledge.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        temperature: float = 0.2
    ):
        """
        Initialize agent router with shared LLM configuration.

        Args:
            model: OpenAI model name for all agents
            temperature: LLM temperature for all agents
        """
        self.model = model
        self.temperature = temperature

        # Initialize agents (lazy initialization pattern - create on demand)
        self._siemens_agent: Optional[SiemensAgent] = None
        self._rockwell_agent: Optional[RockwellAgent] = None
        self._safety_agent: Optional[SafetyAgent] = None
        self._generic_agent: Optional[GenericPLCAgent] = None

    def route(self, intent: RivetIntent) -> BaseSMEAgent:
        """
        Route intent to appropriate SME agent.

        Args:
            intent: Classified user intent with vendor/equipment context

        Returns:
            Appropriate SME agent instance

        Routing Logic:
        1. If equipment is safety-related → SafetyAgent
        2. If vendor is Siemens → SiemensAgent
        3. If vendor is Rockwell/Allen-Bradley → RockwellAgent
        4. Otherwise → GenericPLCAgent (fallback)
        """
        # Priority 1: Safety equipment always goes to safety specialist
        if self._is_safety_equipment(intent):
            return self._get_safety_agent()

        # Priority 2: Vendor-specific routing
        if intent.vendor == VendorType.SIEMENS:
            return self._get_siemens_agent()

        if intent.vendor in [VendorType.ROCKWELL, VendorType.ALLEN_BRADLEY]:
            return self._get_rockwell_agent()

        # Priority 3: Fallback to generic PLC agent
        return self._get_generic_agent()

    def _is_safety_equipment(self, intent: RivetIntent) -> bool:
        """
        Check if equipment is safety-related.

        Args:
            intent: User intent

        Returns:
            True if safety equipment detected
        """
        # Safety equipment types
        safety_equipment = {
            EquipmentType.SAFETY_RELAY,
            # Could add more safety types here:
            # EquipmentType.SAFETY_PLC,
            # EquipmentType.LIGHT_CURTAIN,
            # EquipmentType.SAFETY_SCANNER,
        }

        if intent.equipment_type in safety_equipment:
            return True

        # Check for safety keywords in symptom description
        if intent.symptom_description:
            safety_keywords = [
                'e-stop', 'emergency stop', 'e stop',
                'safety relay', 'safety circuit',
                'guard', 'interlock',
                'sil', 'sil1', 'sil2', 'sil3',
                'category 3', 'category 4',
                'performance level', 'pl d', 'pl e',
                'iec 61508', 'iec 61511', 'iso 13849'
            ]
            symptom_lower = intent.symptom_description.lower()
            if any(keyword in symptom_lower for keyword in safety_keywords):
                return True

        return False

    def _get_siemens_agent(self) -> SiemensAgent:
        """Get or create Siemens agent instance."""
        if self._siemens_agent is None:
            self._siemens_agent = SiemensAgent(
                model=self.model,
                temperature=self.temperature
            )
        return self._siemens_agent

    def _get_rockwell_agent(self) -> RockwellAgent:
        """Get or create Rockwell agent instance."""
        if self._rockwell_agent is None:
            self._rockwell_agent = RockwellAgent(
                model=self.model,
                temperature=self.temperature
            )
        return self._rockwell_agent

    def _get_safety_agent(self) -> SafetyAgent:
        """Get or create Safety agent instance."""
        if self._safety_agent is None:
            self._safety_agent = SafetyAgent(
                model=self.model,
                temperature=self.temperature
            )
        return self._safety_agent

    def _get_generic_agent(self) -> GenericPLCAgent:
        """Get or create Generic PLC agent instance."""
        if self._generic_agent is None:
            self._generic_agent = GenericPLCAgent(
                model=self.model,
                temperature=self.temperature
            )
        return self._generic_agent
