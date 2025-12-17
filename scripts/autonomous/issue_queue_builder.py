#!/usr/bin/env python3
"""
Issue Queue Builder - Smart Scoring and Ranking

Analyzes ALL open GitHub issues, scores by complexity + priority, selects best 5-10 candidates.

Scoring Algorithm:
- Hybrid approach: Heuristic (fast, $0) + LLM semantic analysis (accurate, ~$0.002/issue)
- Final complexity = (heuristic * 0.4) + (llm_score * 0.6)
- Priority = business_value * (1 / complexity) * feasibility

Usage:
    from scripts.autonomous.issue_queue_builder import IssueQueueBuilder

    builder = IssueQueueBuilder()
    queue = builder.build_queue(max_issues=10)

    for issue_data in queue:
        print(f"#{issue_data['number']}: {issue_data['title']}")
        print(f"  Complexity: {issue_data['final_complexity']:.1f}/10")
        print(f"  Priority: {issue_data['priority_score']:.1f}")
"""

import os
import sys
import re
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from github import Github, GithubException
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage

logger = logging.getLogger("issue_queue_builder")


class IssueQueueBuilder:
    """
    Smart issue queue builder with hybrid scoring.

    Features:
    - Heuristic scoring: Fast label/length/code analysis
    - LLM semantic scoring: Intelligent complexity assessment
    - Priority ranking: Business value * feasibility / complexity
    - Queue selection: Top 5-10 issues under 4-hour total estimate
    """

    def __init__(self):
        """Initialize queue builder with GitHub API and LLM."""
        self.github_token = os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable required")

        self.github = Github(self.github_token)
        self.repo_owner = os.getenv("GITHUB_OWNER", "Mikecranesync")
        self.repo_name = os.getenv("GITHUB_REPO", "Agent-Factory")

        try:
            self.repo = self.github.get_repo(f"{self.repo_owner}/{self.repo_name}")
            logger.info(f"Connected to repository: {self.repo_owner}/{self.repo_name}")
        except GithubException as e:
            logger.error(f"Failed to connect to repository: {e}")
            raise

        # Initialize LLM for semantic scoring
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            self.llm = ChatAnthropic(
                model="claude-3-5-haiku-20241022",  # Fast, cheap model for scoring
                temperature=0.0,
                anthropic_api_key=anthropic_key
            )
            logger.info("LLM initialized for semantic scoring")
        else:
            logger.warning("ANTHROPIC_API_KEY not set, will use heuristic scoring only")
            self.llm = None

    def build_queue(self, max_issues: int = 10) -> List[Dict[str, Any]]:
        """
        Build prioritized issue queue.

        Args:
            max_issues: Maximum number of issues to select (default: 10)

        Returns:
            List of issue data dicts sorted by priority (highest first)
        """
        logger.info("Starting issue queue building...")

        # STEP 1: Fetch all open issues
        open_issues = self._fetch_open_issues()
        logger.info(f"Found {len(open_issues)} open issues")

        if not open_issues:
            logger.warning("No open issues found")
            return []

        # STEP 2: Score each issue
        scored_issues = []

        for issue in open_issues:
            try:
                # Skip if issue already has PR or is in excluded state
                if self._should_skip_issue(issue):
                    logger.debug(f"Skipping issue #{issue.number}: {self._get_skip_reason(issue)}")
                    continue

                # Calculate scores
                analysis = self._calculate_final_score(issue)
                priority = self._calculate_priority_score(issue, analysis)

                scored_issues.append({
                    "number": issue.number,
                    "title": issue.title,
                    "url": issue.html_url,
                    "labels": [l.name for l in issue.labels],
                    "created_at": issue.created_at.isoformat(),
                    "updated_at": issue.updated_at.isoformat(),
                    "body": issue.body or "",
                    **analysis,
                    "priority_score": priority
                })

                logger.info(
                    f"Scored #{issue.number}: "
                    f"complexity={analysis['final_complexity']:.1f}, "
                    f"priority={priority:.1f}"
                )

            except Exception as e:
                logger.error(f"Failed to score issue #{issue.number}: {e}")
                continue

        # STEP 3: Sort by priority (highest first)
        scored_issues.sort(key=lambda x: x["priority_score"], reverse=True)

        # STEP 4: Select top N issues with constraints
        selected_queue = self._select_queue(scored_issues, max_issues)

        logger.info(
            f"Queue built: {len(selected_queue)} issues selected "
            f"(total estimated: {sum(i['estimated_time_hours'] for i in selected_queue):.1f}h)"
        )

        return selected_queue

    def _fetch_open_issues(self) -> List[Any]:
        """Fetch all open issues from repository."""
        try:
            return list(self.repo.get_issues(state="open"))
        except GithubException as e:
            logger.error(f"Failed to fetch issues: {e}")
            return []

    def _should_skip_issue(self, issue) -> bool:
        """Check if issue should be skipped."""
        # Skip if has pull request linked
        if issue.pull_request is not None:
            return True

        # Skip if labeled with exclusion labels
        exclusion_labels = {"wontfix", "duplicate", "invalid", "on-hold"}
        issue_labels = {l.name.lower() for l in issue.labels}
        if issue_labels & exclusion_labels:
            return True

        return False

    def _get_skip_reason(self, issue) -> str:
        """Get reason for skipping issue."""
        if issue.pull_request:
            return "has linked PR"

        exclusion_labels = {"wontfix", "duplicate", "invalid", "on-hold"}
        issue_labels = {l.name.lower() for l in issue.labels}
        matched = issue_labels & exclusion_labels
        if matched:
            return f"labeled: {', '.join(matched)}"

        return "unknown"

    def _calculate_heuristic_score(self, issue) -> Dict[str, Any]:
        """
        Calculate heuristic complexity score (fast, no API cost).

        Factors:
        - Description length
        - Labels (bug, feature, docs, etc.)
        - Code snippets
        - File mentions
        - Issue age

        Returns:
            {"score": 0-10, "factors": {...}}
        """
        score = 5.0  # Baseline
        factors = {}

        # FACTOR 1: Description length
        body = issue.body or ""
        desc_len = len(body)

        if desc_len < 100:
            factors["sparse_description"] = +2.0  # Vague → harder
        elif desc_len > 1000:
            factors["detailed_description"] = -1.0  # Clear → easier

        # FACTOR 2: Labels
        labels = {l.name.lower() for l in issue.labels}

        if "good first issue" in labels or "good-first-issue" in labels:
            factors["good_first_issue"] = -3.0
        if "bug" in labels:
            factors["bug"] = +1.0
        if "enhancement" in labels or "feature" in labels:
            factors["feature"] = +2.0
        if "documentation" in labels or "docs" in labels:
            factors["docs"] = -2.0
        if "breaking change" in labels or "breaking-change" in labels:
            factors["breaking_change"] = +4.0
        if "help wanted" in labels or "help-wanted" in labels:
            factors["help_wanted"] = +0.5

        # FACTOR 3: Code snippets (indicates technical depth)
        code_blocks = body.count("```")
        if code_blocks > 0:
            factors["code_snippets"] = min(code_blocks * 0.5, 2.0)

        # FACTOR 4: File mentions
        file_pattern = r'\.(py|js|ts|tsx|jsx|go|java|rb|php|cpp|c|rs)'
        file_mentions = len(re.findall(file_pattern, body))
        if file_mentions > 0:
            factors["file_mentions"] = min(file_mentions * 0.3, 2.0)

        # FACTOR 5: Issue age (old → probably harder)
        age_days = (datetime.now(timezone.utc) - issue.created_at).days
        if age_days > 90:
            factors["aged_issue"] = +1.5

        # Calculate total
        total = score + sum(factors.values())
        final_score = max(0, min(10, total))

        return {"score": final_score, "factors": factors}

    def _calculate_llm_score(self, issue) -> Dict[str, Any]:
        """
        Calculate LLM-based semantic complexity score.

        Uses Claude Haiku for fast, cheap analysis (~$0.002/issue).

        Returns:
            {
                "complexity_score": 0-10,
                "reasoning": str,
                "estimated_time_hours": float,
                "risk_level": "low"|"medium"|"high",
                "keywords": [str, ...]
            }
        """
        if not self.llm:
            # Fallback if LLM not available
            return {
                "complexity_score": 5.0,
                "reasoning": "LLM not available, using default score",
                "estimated_time_hours": 1.0,
                "risk_level": "medium",
                "keywords": []
            }

        prompt = f"""Analyze this GitHub issue complexity on a 0-10 scale.

Issue Title: {issue.title}

Description:
{issue.body or "No description provided"}

Labels: {", ".join([l.name for l in issue.labels])}

Scoring guide:
- 0-3: Simple (docs, typos, config changes, obvious bug fixes)
- 4-6: Moderate (single feature, isolated bug fix, refactoring one file)
- 7-10: Complex (architectural changes, breaking changes, multi-file refactor, new systems)

Consider:
- Scope: How many files/components affected?
- Clarity: Is the requirement clear or vague?
- Technical difficulty: Does it require deep system knowledge?
- Risk: Could changes introduce bugs elsewhere?

Respond with JSON only (no markdown code blocks):
{{
  "complexity_score": <0-10 as number>,
  "reasoning": "<2-3 sentence explanation>",
  "estimated_time_hours": <0.5-4.0 as number>,
  "risk_level": "<low|medium|high>",
  "keywords": ["keyword1", "keyword2"]
}}"""

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            content = response.content.strip()

            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = re.sub(r'^```json\n|```\n?$', '', content, flags=re.MULTILINE)

            result = json.loads(content)

            # Validate response
            if not all(k in result for k in ["complexity_score", "reasoning", "estimated_time_hours", "risk_level"]):
                raise ValueError("Missing required fields in LLM response")

            # Clamp values
            result["complexity_score"] = max(0, min(10, float(result["complexity_score"])))
            result["estimated_time_hours"] = max(0.5, min(4.0, float(result["estimated_time_hours"])))

            return result

        except Exception as e:
            logger.error(f"LLM scoring failed for issue #{issue.number}: {e}")
            # Fallback to default
            return {
                "complexity_score": 5.0,
                "reasoning": f"LLM error: {str(e)[:100]}",
                "estimated_time_hours": 1.0,
                "risk_level": "medium",
                "keywords": []
            }

    def _calculate_final_score(self, issue) -> Dict[str, Any]:
        """
        Calculate final combined score (heuristic + LLM).

        Final complexity = (heuristic * 0.4) + (llm_score * 0.6)

        Returns:
            {
                "final_complexity": 0-10,
                "heuristic_score": 0-10,
                "llm_score": 0-10,
                "estimated_time_hours": float,
                "risk_level": str,
                "llm_reasoning": str,
                "heuristic_factors": {...}
            }
        """
        heuristic = self._calculate_heuristic_score(issue)
        llm_analysis = self._calculate_llm_score(issue)

        # Weighted average: 40% heuristic, 60% LLM
        final_complexity = (heuristic["score"] * 0.4) + (llm_analysis["complexity_score"] * 0.6)

        return {
            "final_complexity": round(final_complexity, 2),
            "heuristic_score": heuristic["score"],
            "llm_score": llm_analysis["complexity_score"],
            "estimated_time_hours": llm_analysis["estimated_time_hours"],
            "risk_level": llm_analysis["risk_level"],
            "llm_reasoning": llm_analysis["reasoning"],
            "heuristic_factors": heuristic["factors"],
            "keywords": llm_analysis.get("keywords", [])
        }

    def _calculate_priority_score(self, issue, analysis: Dict[str, Any]) -> float:
        """
        Calculate priority score.

        Formula: priority = business_value * (1 / complexity) * feasibility

        Higher priority = more valuable, less complex, more feasible
        """
        complexity = analysis["final_complexity"]

        # Business value (from labels/mentions)
        business_value = 5.0  # Baseline

        labels = {l.name.lower() for l in issue.labels}
        if "critical" in labels or "urgent" in labels:
            business_value += 3.0
        if "high priority" in labels or "high-priority" in labels:
            business_value += 2.0
        if "good first issue" in labels or "good-first-issue" in labels:
            business_value += 1.0  # Easy wins are valuable
        if "technical debt" in labels or "technical-debt" in labels:
            business_value += 1.5

        # Feasibility (can Claude actually solve this?)
        feasibility = 1.0

        risk = analysis["risk_level"]
        if risk == "low":
            feasibility = 1.0
        elif risk == "medium":
            feasibility = 0.7
        elif risk == "high":
            feasibility = 0.3  # Risky, deprioritize

        # Complexity penalty (simpler = higher priority)
        # Avoid division by zero
        complexity_factor = max(0.1, (10 - complexity) / 10)

        # Final priority formula
        priority = business_value * complexity_factor * feasibility

        return round(priority, 2)

    def _select_queue(self, scored_issues: List[Dict], max_issues: int) -> List[Dict]:
        """
        Select top N issues with constraints.

        Constraints:
        - Max queue size (max_issues)
        - Complexity filter: Skip issues > 8/10 complexity
        - Time estimate cap: Skip issues > 2 hours estimated
        - Total time budget: Ensure total estimated time < 4 hours
        """
        selected = []
        total_estimated_time = 0.0

        for issue_data in scored_issues:
            # Constraint 1: Max queue size
            if len(selected) >= max_issues:
                logger.info(f"Reached max queue size ({max_issues}), stopping selection")
                break

            # Constraint 2: Complexity filter
            if issue_data["final_complexity"] > 8.0:
                logger.debug(
                    f"Skipping #{issue_data['number']} (complexity {issue_data['final_complexity']:.1f} > 8.0)"
                )
                continue

            # Constraint 3: Time estimate cap
            if issue_data["estimated_time_hours"] > 2.0:
                logger.debug(
                    f"Skipping #{issue_data['number']} "
                    f"(estimated {issue_data['estimated_time_hours']:.1f}h > 2.0h)"
                )
                continue

            # Constraint 4: Total time budget
            if total_estimated_time + issue_data["estimated_time_hours"] > 4.0:
                logger.info(
                    f"Total time budget would exceed 4.0h, stopping selection "
                    f"(current: {total_estimated_time:.1f}h)"
                )
                break

            # Add to queue
            selected.append(issue_data)
            total_estimated_time += issue_data["estimated_time_hours"]

            logger.info(
                f"Selected #{issue_data['number']}: "
                f"{issue_data['title'][:50]}... "
                f"(priority={issue_data['priority_score']:.1f}, "
                f"complexity={issue_data['final_complexity']:.1f}, "
                f"est={issue_data['estimated_time_hours']:.1f}h)"
            )

        return selected


if __name__ == "__main__":
    # Test queue builder locally
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

    try:
        builder = IssueQueueBuilder()
        queue = builder.build_queue(max_issues=10)

        print("\n" + "="*70)
        print("ISSUE QUEUE")
        print("="*70)

        for i, issue_data in enumerate(queue, 1):
            print(f"\n{i}. Issue #{issue_data['number']}: {issue_data['title']}")
            print(f"   Complexity: {issue_data['final_complexity']:.1f}/10 (heuristic={issue_data['heuristic_score']:.1f}, llm={issue_data['llm_score']:.1f})")
            print(f"   Priority: {issue_data['priority_score']:.1f}")
            print(f"   Estimated Time: {issue_data['estimated_time_hours']:.1f}h")
            print(f"   Risk: {issue_data['risk_level']}")
            print(f"   Reasoning: {issue_data['llm_reasoning']}")
            print(f"   URL: {issue_data['url']}")

        total_time = sum(i["estimated_time_hours"] for i in queue)
        print(f"\nTotal Estimated Time: {total_time:.1f}h")
        print(f"Queue Size: {len(queue)} issues")

    except Exception as e:
        logger.error(f"Queue builder test failed: {e}")
        sys.exit(1)
