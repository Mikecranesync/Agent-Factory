"""
QuickTroubleshoot Agent - Instant troubleshooting from KB in <3 seconds.

Provides immediate troubleshooting fixes using waterfall strategy:
1. Vector search Neon KB
2. LLM fallback for common equipment
3. Safety warnings from KB
"""

import asyncio
import os
from dataclasses import dataclass, asdict
from typing import Optional
import logging

from groq import Groq
from agent_factory.core.database_manager import DatabaseManager

# Import Phoenix tracer if available
try:
    from phoenix_integration.phoenix_tracer import traced
except ImportError:
    def traced(agent_name=None):
        def decorator(func):
            return func
        return decorator

logger = logging.getLogger(__name__)


@dataclass
class QuickFix:
    """Quick troubleshooting fix."""
    symptom: str
    likely_cause: str
    fix_steps: list[str]
    safety_warnings: list[str]
    source: str  # 'kb', 'llm', 'historical'
    confidence: float

    def to_dict(self) -> dict:
        """Convert to dict for serialization."""
        return asdict(self)


class QuickTroubleshoot:
    """
    Provide instant troubleshooting fixes from knowledge base.

    Waterfall strategy:
    1. Vector search Neon KB for model + fault code
    2. If < 2 results: Search manufacturer + fault code
    3. If still < 2: Use LLM to generate common fixes
    4. Always: Append safety warnings for equipment class
    """

    def __init__(self):
        """Initialize QuickTroubleshoot."""
        self.db = DatabaseManager()

        # Initialize Groq for LLM fallback
        groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_client = Groq(api_key=groq_api_key) if groq_api_key else None

    @traced(agent_name="quick_troubleshoot")
    async def get_quick_fixes(
        self,
        model: str,
        fault_code: Optional[str] = None,
        manufacturer: Optional[str] = None
    ) -> list[QuickFix]:
        """
        Get quick troubleshooting fixes.

        Args:
            model: Equipment model (e.g., "G120", "S7-1200")
            fault_code: Fault code (e.g., "F47", "E001")
            manufacturer: Manufacturer name (e.g., "Siemens")

        Returns:
            List of QuickFix results (up to 5)
        """
        logger.info(f"Getting quick fixes for {model} {fault_code or ''}")

        fixes = []

        try:
            # Step 1: KB vector search (model + fault_code)
            query = f"{model} {fault_code} troubleshooting fix" if fault_code else f"{model} troubleshooting"
            kb_results = await self.query_knowledge_base(query, limit=5)

            if kb_results:
                logger.info(f"Found {len(kb_results)} KB results")
                for result in kb_results:
                    fix = self._parse_kb_result(result)
                    if fix:
                        fixes.append(fix)

            # Step 2: If insufficient results, search by manufacturer
            if len(fixes) < 2 and manufacturer and fault_code:
                query = f"{manufacturer} {fault_code} common causes"
                kb_results = await self.query_knowledge_base(query, limit=3)

                for result in kb_results:
                    fix = self._parse_kb_result(result)
                    if fix and fix not in fixes:  # Avoid duplicates
                        fixes.append(fix)

            # Step 3: LLM fallback if still insufficient
            if len(fixes) < 2:
                logger.info("Using LLM fallback for common fixes")
                llm_fixes = await self.generate_llm_fixes(model, fault_code or "")
                fixes.extend(llm_fixes)

            # Step 4: Add safety warnings for equipment class
            safety_warnings = await self._get_safety_warnings(model, manufacturer)

            # Append safety warnings to all fixes
            for fix in fixes:
                fix.safety_warnings.extend(safety_warnings)

            # Deduplicate and limit
            unique_fixes = []
            seen_symptoms = set()
            for fix in fixes:
                symptom_key = fix.symptom.lower()[:50]
                if symptom_key not in seen_symptoms:
                    seen_symptoms.add(symptom_key)
                    unique_fixes.append(fix)

            return unique_fixes[:5]  # Max 5 fixes

        except Exception as e:
            logger.error(f"Error getting quick fixes: {e}", exc_info=True)
            return []

    async def query_knowledge_base(
        self,
        query: str,
        limit: int = 5
    ) -> list[dict]:
        """
        Vector search Neon KB using pgvector.

        Args:
            query: Search query
            limit: Max results

        Returns:
            List of knowledge atoms
        """
        try:
            # Get active database connection
            conn = self.db.get_connection()
            if not conn:
                logger.warning("No database connection available")
                return []

            cursor = conn.cursor()

            # Simple text search (no embeddings for now - would need embedding generation)
            # In production, you'd:
            # 1. Generate embedding for query using text-embedding-3-small
            # 2. Use pgvector <=> operator for similarity search

            sql = """
                SELECT content, metadata
                FROM knowledge_atoms
                WHERE
                    content ILIKE %s OR
                    title ILIKE %s OR
                    summary ILIKE %s
                ORDER BY created_at DESC
                LIMIT %s
            """

            search_pattern = f"%{query}%"
            cursor.execute(sql, (search_pattern, search_pattern, search_pattern, limit))
            results = cursor.fetchall()

            cursor.close()

            return [{"content": r[0], "metadata": r[1] or {}} for r in results]

        except Exception as e:
            logger.error(f"Error querying KB: {e}", exc_info=True)
            return []

    async def generate_llm_fixes(
        self,
        model: str,
        fault_code: str
    ) -> list[QuickFix]:
        """
        Generate common fixes using Groq LLM.

        Args:
            model: Equipment model
            fault_code: Fault code

        Returns:
            List of LLM-generated QuickFix results
        """
        if not self.groq_client:
            logger.warning("Groq client not available for LLM fallback")
            return []

        try:
            prompt = f"""You are an industrial maintenance expert. Provide 2-3 common troubleshooting fixes for:

Equipment: {model}
Fault Code: {fault_code or "General troubleshooting"}

For each fix, provide:
1. Symptom (what the user sees)
2. Likely cause
3. Fix steps (2-3 actionable steps)
4. Safety warnings (lockout/tagout, voltage, etc.)

Format as JSON array:
[
  {{
    "symptom": "...",
    "likely_cause": "...",
    "fix_steps": ["step1", "step2", "step3"],
    "safety_warnings": ["warning1", "warning2"]
  }}
]"""

            response = self.groq_client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=500
            )

            content = response.choices[0].message.content.strip()

            # Parse JSON response
            import json
            fixes_data = json.loads(content)

            fixes = []
            for fix_data in fixes_data:
                fix = QuickFix(
                    symptom=fix_data.get("symptom", "Unknown symptom"),
                    likely_cause=fix_data.get("likely_cause", "Unknown cause"),
                    fix_steps=fix_data.get("fix_steps", []),
                    safety_warnings=fix_data.get("safety_warnings", []),
                    source="llm",
                    confidence=0.6  # Lower confidence for LLM-generated
                )
                fixes.append(fix)

            logger.info(f"Generated {len(fixes)} LLM fixes")
            return fixes

        except Exception as e:
            logger.error(f"Error generating LLM fixes: {e}", exc_info=True)
            return []

    def _parse_kb_result(self, result: dict) -> Optional[QuickFix]:
        """
        Parse KB result into QuickFix.

        Args:
            result: KB result dict

        Returns:
            QuickFix or None if parsing fails
        """
        try:
            content = result.get("content", "")
            metadata = result.get("metadata", {})

            # Extract symptom (first line or title)
            lines = content.split("\n")
            symptom = lines[0][:200] if lines else "Unknown symptom"

            # Extract likely cause (look for trigger phrases)
            likely_cause = ""
            triggers = ["caused by", "due to", "because", "indicates"]
            for trigger in triggers:
                if trigger in content.lower():
                    idx = content.lower().find(trigger)
                    excerpt = content[idx:idx+300]
                    period_idx = excerpt.find(".")
                    if period_idx > 0:
                        likely_cause = excerpt[:period_idx+1]
                    break

            if not likely_cause:
                likely_cause = content[:200]

            # Extract fix steps (numbered lists or bullet points)
            fix_steps = []
            for line in lines:
                if line.strip().startswith(("1.", "2.", "3.", "-", "•")):
                    fix_steps.append(line.strip())

            # Extract safety warnings
            safety_warnings = []
            safety_keywords = ["lockout", "tagout", "loto", "high voltage", "arc flash"]
            for keyword in safety_keywords:
                if keyword in content.lower():
                    safety_warnings.append(f"⚠️ {keyword.upper()} required")

            return QuickFix(
                symptom=symptom,
                likely_cause=likely_cause,
                fix_steps=fix_steps[:5],  # Max 5 steps
                safety_warnings=safety_warnings,
                source="kb",
                confidence=0.8
            )

        except Exception as e:
            logger.debug(f"Error parsing KB result: {e}")
            return None

    async def _get_safety_warnings(
        self,
        model: str,
        manufacturer: Optional[str]
    ) -> list[str]:
        """
        Get safety warnings for equipment class.

        Args:
            model: Equipment model
            manufacturer: Manufacturer name

        Returns:
            List of safety warnings
        """
        try:
            # Query KB for safety-specific atoms
            query = f"{model} safety" if not manufacturer else f"{manufacturer} {model} safety"
            results = await self.query_knowledge_base(query, limit=3)

            warnings = []
            safety_keywords = [
                "lockout", "tagout", "loto", "high voltage", "arc flash",
                "ppe", "de-energize", "rotating", "hazard"
            ]

            for result in results:
                content = result.get("content", "").lower()
                for keyword in safety_keywords:
                    if keyword in content:
                        warnings.append(f"⚠️ {keyword.upper()}")

            # Deduplicate
            return list(set(warnings))[:3]  # Max 3 warnings

        except Exception as e:
            logger.debug(f"Error getting safety warnings: {e}")
            return []

    def format_telegram_card(self, fixes: list[QuickFix]) -> str:
        """
        Format fixes as Telegram HTML card.

        Args:
            fixes: List of QuickFix results

        Returns:
            Telegram HTML formatted string
        """
        if not fixes:
            return "❌ No quick fixes found"

        lines = ["🔧 <b>Quick Fixes</b>\n"]

        for i, fix in enumerate(fixes, 1):
            lines.append(f"<b>{i}. {fix.symptom}</b>")
            lines.append(f"Likely cause: {fix.likely_cause}\n")

            if fix.fix_steps:
                lines.append("Steps:")
                for step in fix.fix_steps:
                    lines.append(f"  • {step}")
                lines.append("")

            if fix.safety_warnings:
                for warning in fix.safety_warnings:
                    lines.append(warning)
                lines.append("")

        return "\n".join(lines)
