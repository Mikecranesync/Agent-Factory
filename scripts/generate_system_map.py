#!/usr/bin/env python3
"""
Generate system map for README.md.

This script analyzes the codebase structure and generates a visual map
showing all major components that have been built.

Usage:
    poetry run python scripts/generate_system_map.py

Output:
    Prints markdown system map to stdout
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple, Set
import json


def check_component(base_path: Path, paths: List[str]) -> bool:
    """Check if any of the given paths exist."""
    for path in paths:
        if (base_path / path).exists():
            return True
    return False


def count_files_in_dir(base_path: Path, pattern: str = "*.py") -> int:
    """Count files matching pattern in directory."""
    try:
        return len(list(base_path.glob(pattern)))
    except:
        return 0


def analyze_codebase(repo_root: Path) -> Dict[str, any]:
    """
    Analyze codebase structure and return component status.

    Returns:
        Dictionary with component information
    """
    components = {
        # Core Platform
        "core": {
            "name": "Agent Factory Core",
            "status": check_component(repo_root, [
                "agent_factory/core/agent_factory.py",
                "agent_factory/core/orchestrator.py",
                "agent_factory/core/settings_service.py"
            ]),
            "subcomponents": {
                "AgentFactory": check_component(repo_root, ["agent_factory/core/agent_factory.py"]),
                "Orchestrator": check_component(repo_root, ["agent_factory/core/orchestrator.py"]),
                "Settings Service": check_component(repo_root, ["agent_factory/core/settings_service.py"]),
                "Database Manager": check_component(repo_root, ["agent_factory/core/database_manager.py"]),
            }
        },

        # Memory & Knowledge
        "memory": {
            "name": "Memory & Knowledge Systems",
            "status": check_component(repo_root, [
                "agent_factory/memory/storage.py",
                "agent_factory/memory/history.py"
            ]),
            "subcomponents": {
                "PostgreSQL Storage": check_component(repo_root, ["agent_factory/memory/storage.py"]),
                "Message History": check_component(repo_root, ["agent_factory/memory/history.py"]),
                "Hybrid Search": check_component(repo_root, ["agent_factory/memory/hybrid_search.py"]),
            }
        },

        # LLM Integration
        "llm": {
            "name": "LLM Router & Cost Optimization",
            "status": check_component(repo_root, [
                "agent_factory/llm/router.py",
                "agent_factory/llm/langchain_adapter.py"
            ]),
            "subcomponents": {
                "LLM Router": check_component(repo_root, ["agent_factory/llm/router.py"]),
                "LangChain Adapter": check_component(repo_root, ["agent_factory/llm/langchain_adapter.py"]),
                "Cost Tracker": check_component(repo_root, ["agent_factory/llm/tracker.py"]),
                "Model Registry": check_component(repo_root, ["agent_factory/llm/config.py"]),
            }
        },

        # RIVET Platform
        "rivet": {
            "name": "RIVET Industrial Maintenance",
            "status": check_component(repo_root, [
                "agent_factory/integrations/telegram/orchestrator_bot.py",
                "agent_factory/rivet_pro/orchestrator.py",
                "agent_factory/core/orchestrator.py"
            ]),
            "subcomponents": {
                "Telegram Bot": check_component(repo_root, ["agent_factory/integrations/telegram/orchestrator_bot.py"]),
                "Knowledge Base": check_component(repo_root, ["agent_factory/rivet_pro/kb/", "agent_factory/rivet_pro/models.py"]),
                "Orchestrator (A/B/C/D)": check_component(repo_root, ["agent_factory/rivet_pro/orchestrator.py", "agent_factory/core/orchestrator.py"]),
                "Voice to Whisper": check_component(repo_root, ["agent_factory/integrations/telegram/voice/", "agent_factory/integrations/telegram/orchestrator_bot.py"]),
                "Photo OCR (Claude Vision)": check_component(repo_root, ["agent_factory/integrations/telegram/ocr/", "agent_factory/rivet_pro/print_analyzer.py"]),
                "Research Pipeline": check_component(repo_root, ["agent_factory/rivet_pro/research/", "agent_factory/rivet_pro/research/research_pipeline.py"]),
                "SME Agents": count_files_in_dir(repo_root / "agent_factory/rivet_pro/agents") > 0,
            }
        },

        # PLC Tutor
        "plc": {
            "name": "PLC Tutor / ISH Platform",
            "status": check_component(repo_root, [
                "plc/",
                "agents/content/",
                "agents/media/"
            ]),
            "subcomponents": {
                "Content Agents": count_files_in_dir(repo_root / "agents/content") > 0,
                "Media Agents": count_files_in_dir(repo_root / "agents/media") > 0,
                "Research Agents": count_files_in_dir(repo_root / "agents/research") > 0,
                "PLC Atoms": check_component(repo_root, ["plc/atoms/"]),
                "Curriculum": check_component(repo_root, ["plc/content/CONTENT_ROADMAP_AtoZ.md"]),
            }
        },

        # Infrastructure
        "infra": {
            "name": "Infrastructure & Deployment",
            "status": check_component(repo_root, [
                "deploy/",
                "scripts/",
                ".githooks/"
            ]),
            "subcomponents": {
                "VPS Deployment": check_component(repo_root, ["deploy/vps/"]),
                "Database Schemas": check_component(repo_root, ["docs/database/supabase_complete_schema.sql"]),
                "Pre-push Hooks": check_component(repo_root, [".githooks/pre-push"]),
                "Task Management (Backlog.md)": check_component(repo_root, ["backlog/tasks/"]),
                "Automation Scripts": count_files_in_dir(repo_root / "scripts") > 10,
            }
        },

        # Observability
        "observability": {
            "name": "Observability & Analytics",
            "status": check_component(repo_root, [
                "agent_factory/observability/",
                "agent_factory/rivet_pro/observability/"
            ]),
            "subcomponents": {
                "LangSmith Integration": check_component(repo_root, ["agent_factory/observability/langsmith_config.py", "agent_factory/observability/"]),
                "KB Ingestion Metrics": check_component(repo_root, ["agent_factory/rivet_pro/observability/", "agent_factory/rivet_pro/observability/metrics.py"]),
                "Telegram Notifications": check_component(repo_root, ["agent_factory/rivet_pro/observability/telegram_notifier.py"]),
            }
        },
    }

    return components


def generate_system_map(components: Dict[str, any]) -> str:
    """
    Generate markdown system map from component analysis.

    Args:
        components: Dictionary of component information

    Returns:
        Markdown string representing the system map
    """
    output = []

    # Header
    output.append("```")
    output.append("AGENT FACTORY - SYSTEM MAP")
    output.append("=" * 60)
    output.append("")

    # Iterate through components
    for key, comp in components.items():
        status_icon = "[x]" if comp["status"] else "[ ]"
        output.append(f"{status_icon} {comp['name']}")

        # Show subcomponents
        for sub_name, sub_status in comp["subcomponents"].items():
            if isinstance(sub_status, bool):
                sub_icon = "  +- [x]" if sub_status else "  +- [ ]"
            elif isinstance(sub_status, int):
                sub_icon = f"  +- [x] ({sub_status} files)" if sub_status > 0 else "  +- [ ]"
            else:
                sub_icon = "  +- [?]"

            output.append(f"{sub_icon} {sub_name}")

        output.append("")

    # Footer with stats
    total_components = len(components)
    built_components = sum(1 for c in components.values() if c["status"])
    percentage = (built_components / total_components * 100) if total_components > 0 else 0

    output.append("-" * 60)
    output.append(f"BUILT: {built_components}/{total_components} major components ({percentage:.0f}%)")
    output.append("```")

    return "\n".join(output)


def main():
    """Generate and print system map."""
    # Get repo root (script is in scripts/)
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent

    # Analyze codebase
    components = analyze_codebase(repo_root)

    # Generate map
    system_map = generate_system_map(components)

    # Save to JSON for potential future use
    map_data = {
        "components": components,
        "markdown": system_map
    }

    output_path = repo_root / "data" / "system_map.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(map_data, f, indent=2)

    # Write to markdown file (avoid console encoding issues)
    map_md_path = repo_root / "data" / "system_map.md"
    with open(map_md_path, "w", encoding="utf-8") as f:
        f.write(system_map)

    # Print to stdout (ASCII only for Windows console)
    safe_map = system_map.encode('ascii', errors='replace').decode('ascii')
    print(safe_map)

    print(f"\nSystem map saved to: {map_md_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
