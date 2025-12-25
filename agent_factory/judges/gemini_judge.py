"""Gemini Judge for Knowledge Atoms

Dual-purpose evaluation:
1. Quality scoring (1-5 scale): clarity, completeness, reusability, grounding
2. Product discovery: monetization potential, confidence, effort estimation
"""

import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Optional

from agent_factory.llm.router import LLMRouter
from agent_factory.llm.types import ModelCapability

logger = logging.getLogger(__name__)


@dataclass
class JudgmentResult:
    """Result from Gemini judge evaluation.

    Attributes:
        task_id: ID of the task these atoms were evaluated for
        atoms_evaluated: Number of atoms evaluated
        median_quality_score: Median overall_score across all atoms
        quality_distribution: Count of atoms by score tier
        fastest_monetization_pick: Top product candidate (confidence ≥ 4, lowest effort)
        all_product_candidates: All atoms with product_potential: "yes"
        atoms_with_scores: Individual atom scores
    """
    task_id: str
    atoms_evaluated: int
    median_quality_score: float
    quality_distribution: Dict[str, int]
    fastest_monetization_pick: Optional[Dict]
    all_product_candidates: List[Dict]
    atoms_with_scores: List[Dict]

    def to_dict(self) -> Dict:
        """Convert to dict for JSON serialization."""
        return asdict(self)


class GeminiJudge:
    """Gemini-powered judge for knowledge atom evaluation and product discovery."""

    def __init__(self, model: str = "gemini-2.0-flash"):
        """Initialize Gemini judge.

        Args:
            model: Gemini model to use (default: gemini-2.0-flash for speed + cost)
        """
        self.model = model
        self.router = LLMRouter()
        self.judge_prompt_template = self._load_judge_prompt_template()
        logger.info(f"GeminiJudge initialized with model: {model}")

    def _load_judge_prompt_template(self) -> str:
        """Load judge prompt template from docs.

        Returns:
            Judge prompt markdown content
        """
        template_path = Path(__file__).parent.parent.parent / "docs" / "JUDGE_TASK_AND_ATOMS_PROMPT.md"

        if not template_path.exists():
            logger.warning(f"Judge prompt template not found: {template_path}")
            return ""

        return template_path.read_text(encoding='utf-8')

    def judge_atoms(
        self,
        atoms: List[Dict],
        task_context: str,
        task_id: str = "unknown"
    ) -> JudgmentResult:
        """Evaluate atoms for quality and product potential.

        Args:
            atoms: List of knowledge atom dicts
            task_context: Description of the task these atoms relate to
            task_id: Task identifier

        Returns:
            JudgmentResult with quality scores and product discoveries

        Raises:
            ValueError: If atoms list is empty
            json.JSONDecodeError: If Gemini returns invalid JSON
        """
        if not atoms:
            raise ValueError("Cannot judge empty atom list")

        logger.info(f"Judging {len(atoms)} atoms for task: {task_id}")

        # Build prompt
        prompt = self._build_judge_prompt(atoms, task_context, task_id)

        # Call Gemini via LLMRouter
        response = self.router.complete(
            prompt=prompt,
            model=self.model,
            temperature=0.3,  # Lower temp for more consistent JSON
            max_tokens=4096
        )

        # Parse response
        judgment = self._parse_judge_response(response, task_id, len(atoms))

        logger.info(
            f"Judgment complete: {judgment.atoms_evaluated} atoms, "
            f"median score: {judgment.median_quality_score:.2f}, "
            f"product candidates: {len(judgment.all_product_candidates)}"
        )

        return judgment

    def _build_judge_prompt(
        self,
        atoms: List[Dict],
        task_context: str,
        task_id: str
    ) -> str:
        """Build judge prompt from template.

        Args:
            atoms: List of knowledge atom dicts
            task_context: Task description
            task_id: Task identifier

        Returns:
            Complete prompt for Gemini
        """
        # Format atoms as JSON
        atoms_json = json.dumps(atoms, indent=2, ensure_ascii=False)

        prompt = f"""You are a dual-purpose judge evaluating knowledge atoms extracted from GitHub repositories.

TASK ID: {task_id}

TASK CONTEXT:
{task_context}

ATOMS TO EVALUATE ({len(atoms)} total):
{atoms_json}

Please evaluate these atoms using the criteria in docs/JUDGE_TASK_AND_ATOMS_PROMPT.md.

Return a JSON object with:
1. Quality scores for each atom (clarity, completeness, reusability, grounding, overall)
2. Product potential assessment (yes/maybe/no)
3. The single fastest monetization pick (highest confidence + lowest effort)
4. All product candidates (confidence >= 4)

Focus on finding products that can ship in 1-2 months and generate $1K-$5K MRR.

**CRITICAL**: Output ONLY valid JSON matching the schema in the prompt document. No markdown code blocks, no explanatory text, just raw JSON starting with {{ and ending with }}.

Expected JSON structure:
{{
  "task_id": "{task_id}",
  "atoms_evaluated": {len(atoms)},
  "median_quality_score": <float>,
  "quality_distribution": {{"excellent": <int>, "good": <int>, "fair": <int>, "poor": <int>, "unusable": <int>}},
  "fastest_monetization_pick": {{...}} or null,
  "all_product_candidates": [...],
  "atoms_with_scores": [...]
}}
"""

        return prompt

    def _parse_judge_response(
        self,
        response: str,
        task_id: str,
        expected_count: int
    ) -> JudgmentResult:
        """Parse Gemini response into structured JudgmentResult.

        Args:
            response: Raw response from Gemini
            task_id: Task identifier
            expected_count: Expected number of atoms

        Returns:
            Parsed JudgmentResult

        Raises:
            json.JSONDecodeError: If response is not valid JSON
            ValueError: If response doesn't match expected schema
        """
        # Clean response (remove markdown code blocks if present)
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]  # Remove ```json
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]  # Remove ```
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]  # Remove ```
        cleaned = cleaned.strip()

        # Parse JSON
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response preview: {response[:500]}")
            raise

        # Validate schema
        required_fields = [
            "task_id", "atoms_evaluated", "median_quality_score",
            "quality_distribution", "fastest_monetization_pick",
            "all_product_candidates", "atoms_with_scores"
        ]

        missing = [f for f in required_fields if f not in data]
        if missing:
            raise ValueError(f"Missing required fields in judgment: {missing}")

        # Validate counts
        if data["atoms_evaluated"] != expected_count:
            logger.warning(
                f"Expected {expected_count} atoms, "
                f"but judgment shows {data['atoms_evaluated']}"
            )

        # Create JudgmentResult
        return JudgmentResult(
            task_id=data["task_id"],
            atoms_evaluated=data["atoms_evaluated"],
            median_quality_score=float(data["median_quality_score"]),
            quality_distribution=data["quality_distribution"],
            fastest_monetization_pick=data.get("fastest_monetization_pick"),
            all_product_candidates=data.get("all_product_candidates", []),
            atoms_with_scores=data.get("atoms_with_scores", [])
        )


class JudgeError(Exception):
    """Base exception for judge-related errors."""
    pass


class InvalidJudgmentError(JudgeError):
    """Raised when Gemini returns invalid or incomplete judgment."""
    pass
