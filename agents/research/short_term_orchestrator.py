"""
ShortTermOrchestrator - Coordinate all short-term research agents in parallel (<10s).

Runs ManualFinder, QuickTroubleshoot, and FieldFixRetriever concurrently
with hard timeout and graceful degradation.
"""

import asyncio
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional
import logging

from agents.research.manual_finder import ManualFinder, ManualResult
from agents.research.quick_troubleshoot import QuickTroubleshoot, QuickFix
from agents.research.field_fix_retriever import FieldFixRetriever, FieldFix

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
class ShortTermResult:
    """Result from short-term research orchestration."""
    manual: Optional[ManualResult]
    quick_fixes: list[QuickFix]
    field_fixes: list[FieldFix]
    research_time_ms: int
    sources_checked: list[str]
    completed_at: datetime

    def to_dict(self) -> dict:
        """Convert to dict for serialization."""
        data = {
            "manual": self.manual.to_dict() if self.manual else None,
            "quick_fixes": [f.to_dict() for f in self.quick_fixes],
            "field_fixes": [f.to_dict() for f in self.field_fixes],
            "research_time_ms": self.research_time_ms,
            "sources_checked": self.sources_checked,
            "completed_at": self.completed_at.isoformat()
        }
        return data


class ShortTermResearch:
    """
    Coordinate short-term research agents in parallel.

    Strategy:
    1. Launch ManualFinder, QuickTroubleshoot, FieldFixRetriever in parallel
    2. Hard timeout: 10 seconds max
    3. Graceful degradation: Return partial results if any agent fails/times out
    4. Phoenix tracing: Full span tree for monitoring

    Phoenix Span Structure:
        research_short_term (10s max)
        ├─ fetch_manual (parallel, <5s)
        ├─ fetch_quick_fixes (parallel, <3s)
        └─ fetch_field_fixes (parallel, <5s)
    """

    def __init__(self):
        """Initialize ShortTermResearch orchestrator."""
        self.manual_finder = ManualFinder()
        self.quick_troubleshoot = QuickTroubleshoot()
        self.field_fix_retriever = FieldFixRetriever()

    @traced(agent_name="short_term_orchestrator")
    async def run(
        self,
        model: str,
        manufacturer: str,
        fault_code: Optional[str] = None,
        context: Optional[str] = None
    ) -> ShortTermResult:
        """
        Execute short-term research in parallel.

        Args:
            model: Equipment model (e.g., "G120", "S7-1200")
            manufacturer: Manufacturer name (e.g., "Siemens", "Rockwell")
            fault_code: Optional fault code (e.g., "F47", "E001")
            context: Optional problem context for field fix ranking

        Returns:
            ShortTermResult with all agent results
        """
        start_time = time.time()
        logger.info(f"Starting short-term research for {manufacturer} {model}")

        sources_checked = []
        manual = None
        quick_fixes = []
        field_fixes = []

        try:
            # Run all three agents in parallel with timeout
            results = await asyncio.wait_for(
                asyncio.gather(
                    self.manual_finder.find_manual(model, manufacturer),
                    self.quick_troubleshoot.get_quick_fixes(model, fault_code, manufacturer),
                    self.field_fix_retriever.get_field_fixes(model, context),
                    return_exceptions=True  # Don't fail entire call if one agent errors
                ),
                timeout=10.0  # Hard 10-second timeout
            )

            # Unpack results
            manual_result, fixes_result, field_result = results

            # Handle individual failures gracefully
            if isinstance(manual_result, Exception):
                logger.error(f"ManualFinder failed: {manual_result}")
                sources_checked.append("manual_finder:failed")
            elif manual_result:
                manual = manual_result
                sources_checked.append(f"manual_finder:{manual.source}")
            else:
                sources_checked.append("manual_finder:not_found")

            if isinstance(fixes_result, Exception):
                logger.error(f"QuickTroubleshoot failed: {fixes_result}")
                sources_checked.append("quick_troubleshoot:failed")
            else:
                quick_fixes = fixes_result if fixes_result else []
                sources_checked.append(f"quick_troubleshoot:{len(quick_fixes)}_fixes")

            if isinstance(field_result, Exception):
                logger.error(f"FieldFixRetriever failed: {field_result}")
                sources_checked.append("field_fix_retriever:failed")
            else:
                field_fixes = field_result if field_result else []
                sources_checked.append(f"field_fix_retriever:{len(field_fixes)}_fixes")

        except asyncio.TimeoutError:
            logger.warning("⚠️  Short-term research timed out after 10s - returning partial results")
            sources_checked.append("timeout:10s")
        except Exception as e:
            logger.error(f"❌ Error in short-term research: {e}", exc_info=True)
            sources_checked.append(f"error:{type(e).__name__}")

        elapsed_ms = int((time.time() - start_time) * 1000)

        result = ShortTermResult(
            manual=manual,
            quick_fixes=quick_fixes,
            field_fixes=field_fixes,
            research_time_ms=elapsed_ms,
            sources_checked=sources_checked,
            completed_at=datetime.now()
        )

        logger.info(f"✅ Short-term research complete in {elapsed_ms}ms")
        logger.info(f"   Manual: {'✅' if manual else '❌'}")
        logger.info(f"   Quick fixes: {len(quick_fixes)}")
        logger.info(f"   Field fixes: {len(field_fixes)}")

        return result

    async def parallel_fetch_all(
        self,
        model: str,
        manufacturer: str,
        fault_code: Optional[str]
    ) -> dict:
        """
        Internal method: Run all 3 agents in parallel.

        Args:
            model: Equipment model
            manufacturer: Manufacturer name
            fault_code: Optional fault code

        Returns:
            Dict with manual, quick_fixes, field_fixes
        """
        # This method is called internally by run()
        # Kept for potential direct usage
        results = await asyncio.gather(
            self.manual_finder.find_manual(model, manufacturer),
            self.quick_troubleshoot.get_quick_fixes(model, fault_code, manufacturer),
            self.field_fix_retriever.get_field_fixes(model),
            return_exceptions=True
        )

        return {
            "manual": results[0] if not isinstance(results[0], Exception) else None,
            "quick_fixes": results[1] if not isinstance(results[1], Exception) else [],
            "field_fixes": results[2] if not isinstance(results[2], Exception) else []
        }

    def to_telegram_message(self, result: ShortTermResult) -> str:
        """
        Format results as Telegram HTML message.

        Args:
            result: ShortTermResult

        Returns:
            Telegram HTML formatted string
        """
        lines = ["🔧 <b>Short-Term Research Results</b>\n"]

        # Manual
        if result.manual:
            lines.append(f"📘 <b>Manual Found</b>")
            lines.append(f"  Source: {result.manual.source}")
            lines.append(f"  Title: {result.manual.title}")
            if result.manual.pdf_local_path:
                lines.append(f"  Local: {result.manual.pdf_local_path}")
            lines.append(f"  URL: {result.manual.pdf_url}\n")
        else:
            lines.append("📘 <b>Manual:</b> Not found\n")

        # Quick Fixes
        if result.quick_fixes:
            lines.append(f"🔍 <b>Quick Fixes ({len(result.quick_fixes)})</b>")
            for i, fix in enumerate(result.quick_fixes[:3], 1):  # Top 3
                lines.append(f"{i}. {fix.symptom}")
                lines.append(f"   Cause: {fix.likely_cause[:100]}...")
                if fix.safety_warnings:
                    for warning in fix.safety_warnings[:2]:
                        lines.append(f"   {warning}")
                lines.append("")
        else:
            lines.append("🔍 <b>Quick Fixes:</b> None found\n")

        # Field Fixes
        if result.field_fixes:
            lines.append(f"🛠 <b>Field Fixes ({len(result.field_fixes)})</b>")
            for i, fix in enumerate(result.field_fixes[:2], 1):  # Top 2
                lines.append(f"{i}. {fix.problem_description[:100]}...")
                lines.append(f"   Solution: {fix.solution_applied[:100]}...")
                lines.append(f"   Source: {fix.source}")
                lines.append("")
        else:
            lines.append("🛠 <b>Field Fixes:</b> None found\n")

        # Metadata
        lines.append(f"⏱ Research time: {result.research_time_ms}ms")
        lines.append(f"📊 Sources: {', '.join(result.sources_checked)}")

        return "\n".join(lines)

    async def close(self):
        """Close all agent resources."""
        try:
            await self.manual_finder.close()
        except Exception as e:
            logger.debug(f"Error closing ManualFinder: {e}")


# Example usage
if __name__ == "__main__":
    async def test():
        research = ShortTermResearch()
        result = await research.run("G120", "Siemens", "F47")

        print(f"\nManual: {result.manual}")
        print(f"Quick fixes: {len(result.quick_fixes)}")
        print(f"Field fixes: {len(result.field_fixes)}")
        print(f"Time: {result.research_time_ms}ms")

        print("\nTelegram message:")
        print(research.to_telegram_message(result))

        await research.close()

    asyncio.run(test())
