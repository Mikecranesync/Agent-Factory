"""
RIVET Orchestrator with Phoenix Tracing Integration

Routes industrial maintenance queries to manufacturer-specific SME agents
with full observability via Phoenix/OpenTelemetry.
"""

import os
import time
import json
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Phoenix tracer functions
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from phoenix_integration.phoenix_tracer import (
    init_phoenix,
    wrap_client,
    traced,
    log_route_decision,
    log_knowledge_retrieval
)

# Initialize Phoenix (connect to existing server, don't launch)
init_phoenix(project_name="rivet_production", launch_app=False)


class RivetOrchestrator:
    """
    Main orchestrator for RIVET industrial maintenance AI.

    Routes queries to manufacturer-specific SME agents:
    - Siemens SME (S7-1200, S7-1500, G120, etc.)
    - Rockwell/Allen-Bradley SME (CompactLogix, PowerFlex, etc.)
    - ABB SME (drives, motors, robots)
    - Schneider SME (Modicon, Altivar)
    - General SME (fallback for unknown manufacturers)
    """

    # Manufacturer detection keywords
    MANUFACTURER_KEYWORDS = {
        "siemens": ["siemens", "s7-1200", "s7-1500", "s7-300", "s7-400", "simatic", "g120", "tia portal"],
        "rockwell": ["rockwell", "allen-bradley", "ab", "compactlogix", "controllogix", "powerflex", "studio 5000"],
        "abb": ["abb", "acs", "ach", "robotics"],
        "schneider": ["schneider", "modicon", "altivar", "somachine"],
    }

    def __init__(self):
        """Initialize orchestrator with Groq client and Phoenix tracing."""
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment")

        try:
            from groq import Groq
            self.client = Groq(api_key=groq_api_key)
            # Wrap client for Phoenix tracing
            self.client = wrap_client(self.client, provider="groq")
        except ImportError:
            raise ImportError("Groq package not installed. Run: pip install groq")

        self.default_model = "llama-3.3-70b-versatile"

    def _detect_manufacturer(self, query: str, equipment_type: str, manufacturer: Optional[str] = None) -> str:
        """
        Detect manufacturer from query text and equipment type.

        Args:
            query: User query text
            equipment_type: Equipment type (e.g., "S7-1200", "CompactLogix")
            manufacturer: Explicitly provided manufacturer (takes precedence)

        Returns:
            Manufacturer route: "siemens", "rockwell", "abb", "schneider", or "general"
        """
        if manufacturer:
            manufacturer_lower = manufacturer.lower()
            for route, keywords in self.MANUFACTURER_KEYWORDS.items():
                if manufacturer_lower in keywords or manufacturer_lower == route:
                    return route

        # Search in equipment type
        equipment_lower = equipment_type.lower() if equipment_type else ""
        for route, keywords in self.MANUFACTURER_KEYWORDS.items():
            if any(keyword in equipment_lower for keyword in keywords):
                return route

        # Search in query
        query_lower = query.lower() if query else ""
        for route, keywords in self.MANUFACTURER_KEYWORDS.items():
            if any(keyword in query_lower for keyword in keywords):
                return route

        return "general"

    def _calculate_route_confidence(self, selected_route: str, query: str, equipment_type: str) -> Dict[str, float]:
        """
        Calculate confidence scores for all routes.

        Returns:
            Dict of route -> confidence score (0-1)
        """
        all_routes = {}
        query_lower = query.lower() if query else ""
        equipment_lower = equipment_type.lower() if equipment_type else ""
        combined = f"{query_lower} {equipment_lower}"

        for route, keywords in self.MANUFACTURER_KEYWORDS.items():
            # Count keyword matches
            matches = sum(1 for keyword in keywords if keyword in combined)
            confidence = min(matches / len(keywords), 1.0)
            all_routes[route] = confidence

        # General fallback has low confidence unless explicitly matched
        all_routes["general"] = 0.3 if selected_route == "general" else 0.1

        # Boost selected route confidence
        if selected_route in all_routes:
            all_routes[selected_route] = max(all_routes[selected_route], 0.7)

        return all_routes

    @traced(agent_name="rivet_orchestrator", route="main")
    def diagnose(
        self,
        fault_code: str,
        equipment_type: str,
        manufacturer: Optional[str] = None,
        sensor_data: Optional[Dict[str, Any]] = None,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Diagnose an industrial maintenance issue.

        Args:
            fault_code: Error/alarm code (e.g., "F47", "E001")
            equipment_type: Equipment model (e.g., "S7-1200", "CompactLogix")
            manufacturer: Manufacturer name (optional, will be detected)
            sensor_data: Sensor readings (optional)
            context: Additional context (optional)

        Returns:
            Dict with keys:
                - root_cause: Identified root cause
                - safety_warnings: List of safety warnings
                - repair_steps: List of repair steps
                - manual_citations: List of manual references
                - selected_route: Which SME was used
                - confidence: Route confidence score
        """
        start_time = time.time()

        # Step 1: Determine route
        query = f"Fault code {fault_code} on {equipment_type}"
        if context:
            query += f". Context: {context}"

        selected_route = self._detect_manufacturer(query, equipment_type, manufacturer)
        all_routes = self._calculate_route_confidence(selected_route, query, equipment_type)
        confidence = all_routes.get(selected_route, 0.5)

        # Step 2: Log route decision to Phoenix
        log_route_decision(
            query=query,
            selected_route=selected_route,
            confidence=confidence,
            all_routes=all_routes
        )

        # Step 3: Build manufacturer-specific prompt
        prompt = self._build_sme_prompt(
            selected_route,
            fault_code,
            equipment_type,
            sensor_data,
            context
        )

        # Step 4: Call LLM for diagnosis
        try:
            response = self.client.chat.completions.create(
                model=self.default_model,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a {selected_route.upper()} industrial maintenance expert. Provide structured fault diagnosis."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=1000
            )

            # Parse response
            result_text = response.choices[0].message.content
            result = json.loads(result_text)

        except Exception as e:
            # Fallback error response
            result = {
                "root_cause": f"Error generating diagnosis: {str(e)}",
                "safety_warnings": [],
                "repair_steps": [],
                "manual_citations": []
            }

        # Step 5: Add metadata
        result["selected_route"] = selected_route
        result["confidence"] = confidence
        result["latency_ms"] = (time.time() - start_time) * 1000

        return result

    def _build_sme_prompt(
        self,
        route: str,
        fault_code: str,
        equipment_type: str,
        sensor_data: Optional[Dict],
        context: Optional[str]
    ) -> str:
        """
        Build manufacturer-specific diagnostic prompt.

        Args:
            route: SME route (siemens, rockwell, etc.)
            fault_code: Error code
            equipment_type: Equipment model
            sensor_data: Optional sensor readings
            context: Optional additional context

        Returns:
            Formatted prompt string
        """
        prompt_parts = [
            f"Equipment: {equipment_type}",
            f"Fault Code: {fault_code}",
        ]

        if sensor_data:
            prompt_parts.append(f"Sensor Data: {json.dumps(sensor_data)}")

        if context:
            prompt_parts.append(f"Context: {context}")

        prompt_parts.append(
            "\nProvide a JSON response with the following structure:\n"
            "{\n"
            '  "root_cause": "Identified root cause of the fault",\n'
            '  "safety_warnings": ["Warning 1", "Warning 2"],\n'
            '  "repair_steps": ["Step 1", "Step 2", "Step 3"],\n'
            '  "manual_citations": ["Manual Section 1", "Manual Section 2"]\n'
            "}"
        )

        return "\n\n".join(prompt_parts)


# Module-level convenience function
def create_orchestrator() -> RivetOrchestrator:
    """Create and return a RIVET orchestrator instance."""
    return RivetOrchestrator()


if __name__ == "__main__":
    # Quick test
    orch = create_orchestrator()
    result = orch.diagnose(
        fault_code="F47",
        equipment_type="S7-1200",
        manufacturer="Siemens",
        context="PLC showing overcurrent alarm on output module"
    )
    print(json.dumps(result, indent=2))
