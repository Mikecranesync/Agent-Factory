#!/usr/bin/env python3
"""
ContentEnricherAgent - Organize researched content into teaching structure

Responsibilities:
- Take enriched atom set from ContentResearcherAgent
- Deduplicate atoms (remove overlaps)
- Sequence content (intro → concepts → examples → procedures → recap)
- Create outline with target word counts per section
- NO LLM USAGE - Pure rule-based logic

Purpose: Create optimal teaching structure from KB content
Cost: $0 (pure logic)

Based on: Multi-agent content enhancement chain
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class ContentEnricherAgent:
    """
    Organize researched content into logical teaching outline.

    This agent takes atoms from ContentResearcherAgent and creates
    a structured outline with proper sequencing and word count targets.
    """

    def __init__(self):
        """Initialize agent"""
        self.agent_name = "content_enricher_agent"
        logger.info(f"{self.agent_name} initialized")

    def create_outline(self, research: Dict[str, List[Dict[str, Any]]], topic: str) -> Dict[str, Any]:
        """
        Create structured teaching outline from researched atoms.

        Args:
            research: Dict with categorized atoms from ContentResearcherAgent
            topic: Main topic for the video

        Returns:
            Outline dictionary:
            {
                'topic': str,
                'total_target_words': int,
                'sections': [
                    {
                        'type': str,
                        'title': str,
                        'atoms': List[atom],
                        'target_words': int
                    },
                    ...
                ]
            }

        Example:
            >>> research = researcher.research_topic("Motor Control")
            >>> enricher = ContentEnricherAgent()
            >>> outline = enricher.create_outline(research, "Motor Control Basics")
            >>> print(f"Outline has {len(outline['sections'])} sections")
            >>> print(f"Target word count: {outline['total_target_words']}")
        """
        try:
            logger.info(f"Creating outline for topic: {topic}")

            outline = {
                'topic': topic,
                'sections': [],
                'total_target_words': 0
            }

            # Section 1: Prerequisites (if any)
            if research.get('prerequisites'):
                prereq_section = {
                    'type': 'prerequisite',
                    'title': 'Prerequisites',
                    'atoms': research['prerequisites'][:2],  # Max 2 prereqs
                    'target_words': 80
                }
                outline['sections'].append(prereq_section)
                outline['total_target_words'] += 80
                logger.info(f"Added prerequisite section (2 atoms, 80 words)")

            # Section 2: Main Concept (primary atoms)
            if research.get('primary'):
                concept_section = {
                    'type': 'concept',
                    'title': f'Understanding {topic}',
                    'atoms': research['primary'][:3],  # Top 3 primary atoms
                    'target_words': 180  # Increased for main concept
                }
                outline['sections'].append(concept_section)
                outline['total_target_words'] += 180
                logger.info(f"Added concept section (3 atoms, 180 words)")

            # Section 3: Practical Example (if available)
            if research.get('examples'):
                example_section = {
                    'type': 'example',
                    'title': 'Practical Applications',
                    'atoms': research['examples'][:2],  # Max 2 examples
                    'target_words': 100
                }
                outline['sections'].append(example_section)
                outline['total_target_words'] += 100
                logger.info(f"Added example section (2 atoms, 100 words)")

            # Section 4: Procedure (if applicable)
            if research.get('procedures'):
                procedure_section = {
                    'type': 'procedure',
                    'title': 'Step-by-Step Guide',
                    'atoms': research['procedures'][:1],  # 1 main procedure
                    'target_words': 120
                }
                outline['sections'].append(procedure_section)
                outline['total_target_words'] += 120
                logger.info(f"Added procedure section (1 atom, 120 words)")

            # Section 5: Common Issues / Troubleshooting (if available)
            if research.get('faults'):
                fault_section = {
                    'type': 'troubleshooting',
                    'title': 'Common Issues',
                    'atoms': research['faults'][:1],  # 1 fault example
                    'target_words': 80
                }
                outline['sections'].append(fault_section)
                outline['total_target_words'] += 80
                logger.info(f"Added troubleshooting section (1 atom, 80 words)")

            # If we don't have enough sections or word count, add more primary atoms
            if outline['total_target_words'] < 400 and len(outline['sections']) > 0:
                additional_needed = 400 - outline['total_target_words']
                logger.info(f"Outline below 400 words ({outline['total_target_words']}), need {additional_needed} more")

                # Add more primary atoms if available
                primary_atoms = research.get('primary', [])
                if len(primary_atoms) > 3:
                    additional_section = {
                        'type': 'concept_detail',
                        'title': f'More About {topic}',
                        'atoms': primary_atoms[3:5],  # Use atoms 4-5
                        'target_words': additional_needed
                    }
                    outline['sections'].append(additional_section)
                    outline['total_target_words'] += additional_needed
                    logger.info(f"Added additional concept section ({additional_needed} words)")
                else:
                    # Increase word targets for existing sections proportionally
                    increase_per_section = additional_needed // len(outline['sections'])
                    for section in outline['sections']:
                        section['target_words'] += increase_per_section
                    outline['total_target_words'] += increase_per_section * len(outline['sections'])
                    logger.info(f"Increased word targets by {increase_per_section} per section")

            logger.info(f"Outline complete: {len(outline['sections'])} sections, {outline['total_target_words']} target words")

            return outline

        except Exception as e:
            logger.error(f"Outline creation failed for topic '{topic}': {e}")
            # Return minimal outline on error
            return {
                'topic': topic,
                'sections': [{
                    'type': 'concept',
                    'title': topic,
                    'atoms': research.get('primary', [])[:3],
                    'target_words': 400
                }],
                'total_target_words': 400
            }

    def get_outline_summary(self, outline: Dict[str, Any]) -> str:
        """
        Get human-readable summary of outline.

        Args:
            outline: Outline dict from create_outline()

        Returns:
            Summary string for logging/debugging
        """
        summary_lines = [
            f"Outline for: {outline['topic']}",
            f"Target word count: {outline['total_target_words']} words",
            f"Sections: {len(outline['sections'])}",
            ""
        ]

        for i, section in enumerate(outline['sections'], 1):
            atom_count = len(section.get('atoms', []))
            target_words = section.get('target_words', 0)
            summary_lines.append(
                f"  {i}. {section.get('title', 'Untitled')} "
                f"({section.get('type', 'unknown')}) - "
                f"{atom_count} atoms, {target_words} words"
            )

        return "\n".join(summary_lines)


# Example usage and testing
if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Add project root to path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

    from agents.content.content_researcher_agent import ContentResearcherAgent

    logging.basicConfig(level=logging.INFO)

    # Test with research
    researcher = ContentResearcherAgent()
    research = researcher.research_topic("PLC basics")

    enricher = ContentEnricherAgent()
    outline = enricher.create_outline(research, "Introduction to PLCs")

    print("\n" + "=" * 70)
    print("CONTENT OUTLINE")
    print("=" * 70)
    print(enricher.get_outline_summary(outline))
