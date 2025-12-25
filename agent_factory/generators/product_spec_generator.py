"""Product Spec Generator

Generates markdown product specifications and BUILD tasks from CEO Agent
judgment results.
"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ProductSpecGenerator:
    """Generate product specs and BUILD tasks from judgment results."""

    def __init__(
        self,
        spec_template_path: Optional[Path] = None,
        task_template_path: Optional[Path] = None,
        products_dir: Optional[Path] = None
    ):
        """Initialize product spec generator.

        Args:
            spec_template_path: Path to product spec template (default: agent_factory/templates/product_spec_template.md)
            task_template_path: Path to BUILD task template (default: agent_factory/templates/build_task_template.md)
            products_dir: Directory for product specs (default: docs/products/)
        """
        base_dir = Path(__file__).parent.parent

        self.spec_template_path = spec_template_path or (base_dir / "templates" / "product_spec_template.md")
        self.task_template_path = task_template_path or (base_dir / "templates" / "build_task_template.md")
        self.products_dir = products_dir or (base_dir.parent / "docs" / "products")

        # Load templates
        self.spec_template = self._load_template(self.spec_template_path)
        self.task_template = self._load_template(self.task_template_path)

        # Ensure products directory exists
        self.products_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"ProductSpecGenerator initialized. Products dir: {self.products_dir}")

    def _load_template(self, path: Path) -> str:
        """Load template from file.

        Args:
            path: Template file path

        Returns:
            Template content

        Raises:
            FileNotFoundError: If template file doesn't exist
        """
        if not path.exists():
            raise FileNotFoundError(f"Template not found: {path}")

        return path.read_text(encoding='utf-8')

    def generate_product_spec(
        self,
        product: Dict,
        task_id: str,
        source_repo: str = "agent-factory"
    ) -> Path:
        """Generate product spec markdown file.

        Args:
            product: Product dict from fastest_monetization_pick
            task_id: Task ID this product was discovered from
            source_repo: Source repository name

        Returns:
            Path to generated product spec file

        Raises:
            ValueError: If required product fields are missing
        """
        # Validate required fields
        required = ["chosen_product_name", "product_idea", "product_confidence", "effort_to_productize"]
        missing = [f for f in required if f not in product]
        if missing:
            raise ValueError(f"Missing required product fields: {missing}")

        # Generate slug
        slug = self._generate_slug(product["chosen_product_name"])

        # Calculate revenue projections
        price_tier = product.get("price_tier", "$99/mo")
        base_price = self._extract_price(price_tier)

        # Format next steps as markdown list
        next_steps = product.get("next_steps", [])
        next_steps_formatted = "\n".join([f"{i+1}. {step}" for i, step in enumerate(next_steps)])

        # Build context for template
        context = {
            "product_name": product["chosen_product_name"],
            "product_idea": product["product_idea"],
            "problem": product.get("problem", "See source atom for problem statement"),
            "solution": product.get("solution", "See source atom for solution details"),
            "target_market": product.get("target_market", "To be determined"),
            "price_tier": price_tier,
            "monthly_revenue_10": base_price * 10,
            "monthly_revenue_50": base_price * 50,
            "monthly_revenue_100": base_price * 100,
            "effort_to_productize": product["effort_to_productize"],
            "effort_description": self._get_effort_description(product["effort_to_productize"]),
            "next_steps_formatted": next_steps_formatted or "No specific steps provided",
            "atom_id": product.get("chosen_product_atom_id", "unknown"),
            "source_repo": source_repo,
            "discovery_date": datetime.now().strftime("%Y-%m-%d"),
            "task_id": task_id,
            "product_notes": product.get("product_notes", "No additional notes"),
            "product_confidence": product["product_confidence"]
        }

        # Fill template
        spec_content = self.spec_template.format(**context)

        # Write to file
        spec_path = self.products_dir / f"{slug}.md"
        spec_path.write_text(spec_content, encoding='utf-8')

        logger.info(f"Generated product spec: {spec_path}")
        return spec_path

    def generate_build_task(
        self,
        product: Dict,
        task_id: str,
        source_repo: str = "agent-factory",
        milestone: str = "Product Discovery",
        backlog_dir: Optional[Path] = None
    ) -> tuple[str, Path]:
        """Generate BUILD task markdown file.

        Args:
            product: Product dict from fastest_monetization_pick
            task_id: Task ID this product was discovered from
            source_repo: Source repository name
            milestone: Milestone for this BUILD task
            backlog_dir: Directory for backlog tasks (default: backlog/tasks/)

        Returns:
            Tuple of (task_id, task_path)

        Raises:
            ValueError: If required product fields are missing
        """
        if backlog_dir is None:
            backlog_dir = Path(__file__).parent.parent.parent / "backlog" / "tasks"

        backlog_dir.mkdir(parents=True, exist_ok=True)

        # Generate slug and task ID
        slug = self._generate_slug(product["chosen_product_name"])
        build_task_id = f"task-build-{slug}"

        # Calculate revenue targets
        price_tier = product.get("price_tier", "$99/mo")
        base_price = self._extract_price(price_tier)

        # Format next steps
        next_steps = product.get("next_steps", [])
        next_steps_formatted = "\n".join([f"{i+1}. {step}" for i, step in enumerate(next_steps)])

        # Determine product category
        product_category = self._categorize_product(product["product_idea"])

        # Build context
        context = {
            "product_name": product["chosen_product_name"],
            "product_slug": slug,
            "product_confidence": product["product_confidence"],
            "effort_to_productize": product["effort_to_productize"],
            "next_steps_formatted": next_steps_formatted or "See product spec for details",
            "price_tier": price_tier,
            "target_mrr_month1": base_price * 5,  # 5 customers Month 1
            "target_mrr_month3": base_price * 20,  # 20 customers Month 3
            "atom_id": product.get("chosen_product_atom_id", "unknown"),
            "source_repo": source_repo,
            "discovery_date": datetime.now().strftime("%Y-%m-%d"),
            "task_id": task_id,
            "product_notes": product.get("product_notes", ""),
            "product_category": product_category,
            "milestone": milestone
        }

        # Fill template
        task_content = self.task_template.format(**context)

        # Write to file
        task_path = backlog_dir / f"{build_task_id}.md"
        task_path.write_text(task_content, encoding='utf-8')

        logger.info(f"Generated BUILD task: {task_path}")
        return (build_task_id, task_path)

    def _generate_slug(self, product_name: str) -> str:
        """Generate URL-safe slug from product name.

        Args:
            product_name: Product name

        Returns:
            Lowercase hyphenated slug
        """
        # Convert to lowercase, replace spaces/special chars with hyphens
        slug = re.sub(r'[^\w\s-]', '', product_name.lower())
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)  # Remove duplicate hyphens
        return slug.strip('-')

    def _extract_price(self, price_tier: str) -> int:
        """Extract numeric price from price tier string.

        Args:
            price_tier: Price tier (e.g., "$99/mo", "$499/month")

        Returns:
            Numeric price
        """
        match = re.search(r'\$?(\d+)', price_tier)
        if match:
            return int(match.group(1))
        return 99  # Default fallback

    def _get_effort_description(self, effort: str) -> str:
        """Get description for effort level.

        Args:
            effort: Effort level (Low, Medium, High)

        Returns:
            Effort description
        """
        descriptions = {
            "Low": "**1-2 weeks:** Pattern is 80% complete. Minor UI/packaging needed.",
            "Medium": "**3-6 weeks:** Core logic exists. Needs significant integration work.",
            "High": "**2-3 months:** Complex feature. Multiple components + infrastructure work."
        }
        return descriptions.get(effort, "Effort estimate not available")

    def _categorize_product(self, product_idea: str) -> str:
        """Categorize product based on idea text.

        Args:
            product_idea: Product idea description

        Returns:
            Product category
        """
        idea_lower = product_idea.lower()

        if any(word in idea_lower for word in ["search", "query", "index"]):
            return "search"
        elif any(word in idea_lower for word in ["api", "service", "sdk"]):
            return "api-service"
        elif any(word in idea_lower for word in ["automation", "workflow", "pipeline"]):
            return "automation"
        elif any(word in idea_lower for word in ["monitor", "alert", "tracking"]):
            return "monitoring"
        elif any(word in idea_lower for word in ["ai", "llm", "ml", "agent"]):
            return "ai-ml"
        else:
            return "general"


class ProductSpecGeneratorError(Exception):
    """Base exception for product spec generator errors."""
    pass
