#!/usr/bin/env python3
"""
ContentResearcherAgent - Find related content from knowledge base

Responsibilities:
- Query KB for prerequisites, examples, procedures, faults
- Extract keywords from primary atoms
- Return enriched atom sets (10-15 atoms vs 5)
- NO LLM USAGE - Pure KB queries only

Purpose: Enrich content without LLM costs by leveraging existing KB
Cost: $0 (pure Supabase queries)

Based on: Multi-agent content enhancement chain
"""

import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Set
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agent_factory.memory.storage import SupabaseMemoryStorage

logger = logging.getLogger(__name__)


class ContentResearcherAgent:
    """
    Research related content from knowledge base using pure KB queries.

    This agent finds prerequisites, examples, procedures, and troubleshooting
    content to enrich video scripts WITHOUT using LLM calls.
    """

    def __init__(self):
        """Initialize agent with Supabase connection"""
        self.storage = SupabaseMemoryStorage()
        self.agent_name = "content_researcher_agent"
        self._register_status()

    def _register_status(self):
        """Register agent in agent_status table"""
        try:
            self.storage.client.table("agent_status").upsert({
                "agent_name": self.agent_name,
                "status": "idle",
                "last_heartbeat": datetime.now().isoformat(),
                "tasks_completed_today": 0,
                "tasks_failed_today": 0
            }).execute()
            logger.info(f"{self.agent_name} registered")
        except Exception as e:
            logger.error(f"Failed to register {self.agent_name}: {e}")

    def research_topic(self, topic: str, primary_atoms: List[Dict[str, Any]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Research topic by querying KB for related content.

        Args:
            topic: Main topic (e.g., "PLC basics")
            primary_atoms: Optional primary atoms (if already queried)

        Returns:
            Dictionary with categorized atoms:
            {
                'primary': List[atom],
                'prerequisites': List[atom],
                'examples': List[atom],
                'procedures': List[atom],
                'faults': List[atom]
            }

        Example:
            >>> agent = ContentResearcherAgent()
            >>> research = agent.research_topic("Motor Control")
            >>> print(f"Found {len(research['primary'])} primary atoms")
            >>> print(f"Found {len(research['examples'])} examples")
        """
        try:
            logger.info(f"Researching topic: {topic}")

            # 1. Get primary atoms (if not provided)
            if primary_atoms is None:
                primary_atoms = self._query_atoms(topic, limit=5)

            logger.info(f"Starting with {len(primary_atoms)} primary atoms")

            # 2. Extract keywords from primary atoms
            keywords = self._extract_keywords(primary_atoms, topic)
            logger.info(f"Extracted keywords: {keywords}")

            # 3. Query for prerequisites (fundamentals, basics)
            prereqs = self._query_prerequisites(keywords)

            # 4. Query for examples (applications, use cases)
            examples = self._query_examples(keywords)

            # 5. Query for procedures (how-to, steps)
            procedures = self._query_procedures(keywords)

            # 6. Query for troubleshooting (faults, problems)
            faults = self._query_faults(keywords)

            # 7. Deduplicate (remove atoms that appear in primary)
            primary_ids = {a.get('id') for a in primary_atoms if a.get('id')}
            prereqs = [a for a in prereqs if a.get('id') not in primary_ids]
            examples = [a for a in examples if a.get('id') not in primary_ids]
            procedures = [a for a in procedures if a.get('id') not in primary_ids]
            faults = [a for a in faults if a.get('id') not in primary_ids]

            research = {
                'primary': primary_atoms,
                'prerequisites': prereqs,
                'examples': examples,
                'procedures': procedures,
                'faults': faults
            }

            total_atoms = sum(len(v) for v in research.values())
            logger.info(f"Research complete: {total_atoms} total atoms ({len(primary_atoms)} primary, {len(prereqs)} prereqs, {len(examples)} examples, {len(procedures)} procedures, {len(faults)} faults)")

            return research

        except Exception as e:
            logger.error(f"Research failed for topic '{topic}': {e}")
            # Return minimal research on error
            return {
                'primary': primary_atoms or [],
                'prerequisites': [],
                'examples': [],
                'procedures': [],
                'faults': []
            }

    def _extract_keywords(self, atoms: List[Dict[str, Any]], topic: str) -> List[str]:
        """
        Extract key search terms from atoms and topic.

        Returns list of 3-5 keywords for searching.
        """
        keywords = set()

        # Add words from topic
        topic_words = topic.lower().replace('-', ' ').split()
        keywords.update(word for word in topic_words if len(word) > 3)

        # Extract from atom titles
        for atom in atoms[:3]:  # Use first 3 atoms
            title = atom.get('title', '')
            title_words = title.lower().replace('-', ' ').split()
            keywords.update(word for word in title_words if len(word) > 4)

        # Filter stopwords
        stopwords = {'this', 'that', 'with', 'from', 'have', 'what', 'when', 'where', 'about'}
        keywords = {k for k in keywords if k not in stopwords}

        # Return top 5 keywords
        return list(keywords)[:5]

    def _query_atoms(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Basic atom query (keyword search)"""
        try:
            result = self.storage.client.table('knowledge_atoms') \
                .select('*') \
                .or_(f'title.ilike.%{query}%,summary.ilike.%{query}%,content.ilike.%{query}%') \
                .limit(limit) \
                .execute()

            return result.data
        except Exception as e:
            logger.error(f"Query failed for '{query}': {e}")
            return []

    def _query_prerequisites(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """Query for prerequisite knowledge (fundamentals, basics)"""
        prereq_terms = ['fundamentals', 'basics', 'introduction', 'basic']
        atoms = []

        for keyword in keywords[:2]:  # Use top 2 keywords
            for term in prereq_terms:
                query = f"{keyword} {term}"
                results = self._query_atoms(query, limit=2)
                atoms.extend(results)
                if len(atoms) >= 3:
                    break
            if len(atoms) >= 3:
                break

        # Deduplicate by ID
        seen = set()
        unique_atoms = []
        for atom in atoms:
            atom_id = atom.get('id')
            if atom_id and atom_id not in seen:
                seen.add(atom_id)
                unique_atoms.append(atom)

        return unique_atoms[:3]

    def _query_examples(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """Query for practical examples and applications"""
        example_terms = ['example', 'application', 'use case', 'demo']
        atoms = []

        for keyword in keywords[:2]:
            for term in example_terms:
                query = f"{keyword} {term}"
                results = self._query_atoms(query, limit=2)
                atoms.extend(results)
                if len(atoms) >= 3:
                    break
            if len(atoms) >= 3:
                break

        # Deduplicate
        seen = set()
        unique_atoms = []
        for atom in atoms:
            atom_id = atom.get('id')
            if atom_id and atom_id not in seen:
                seen.add(atom_id)
                unique_atoms.append(atom)

        return unique_atoms[:3]

    def _query_procedures(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """Query for step-by-step procedures"""
        procedure_terms = ['how to', 'step', 'procedure', 'create', 'setup']
        atoms = []

        for keyword in keywords[:2]:
            for term in procedure_terms:
                query = f"{keyword} {term}"
                results = self._query_atoms(query, limit=2)
                atoms.extend(results)
                if len(atoms) >= 3:
                    break
            if len(atoms) >= 3:
                break

        # Deduplicate
        seen = set()
        unique_atoms = []
        for atom in atoms:
            atom_id = atom.get('id')
            if atom_id and atom_id not in seen:
                seen.add(atom_id)
                unique_atoms.append(atom)

        return unique_atoms[:3]

    def _query_faults(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """Query for troubleshooting and common faults"""
        fault_terms = ['troubleshoot', 'problem', 'fault', 'error', 'issue']
        atoms = []

        for keyword in keywords[:2]:
            for term in fault_terms:
                query = f"{keyword} {term}"
                results = self._query_atoms(query, limit=1)
                atoms.extend(results)
                if len(atoms) >= 2:
                    break
            if len(atoms) >= 2:
                break

        # Deduplicate
        seen = set()
        unique_atoms = []
        for atom in atoms:
            atom_id = atom.get('id')
            if atom_id and atom_id not in seen:
                seen.add(atom_id)
                unique_atoms.append(atom)

        return unique_atoms[:2]


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    agent = ContentResearcherAgent()

    # Test research
    research = agent.research_topic("PLC basics")

    print("\n" + "=" * 70)
    print("CONTENT RESEARCH RESULTS")
    print("=" * 70)
    print(f"\nTopic: PLC basics")
    print(f"\nPrimary atoms: {len(research['primary'])}")
    print(f"Prerequisites: {len(research['prerequisites'])}")
    print(f"Examples: {len(research['examples'])}")
    print(f"Procedures: {len(research['procedures'])}")
    print(f"Faults: {len(research['faults'])}")
    print(f"\nTotal atoms found: {sum(len(v) for v in research.values())}")

    # Show some titles
    print("\n" + "-" * 70)
    print("Sample Atoms:")
    print("-" * 70)

    if research['primary']:
        print(f"\nPrimary: {research['primary'][0].get('title', 'Untitled')}")

    if research['prerequisites']:
        print(f"Prerequisite: {research['prerequisites'][0].get('title', 'Untitled')}")

    if research['examples']:
        print(f"Example: {research['examples'][0].get('title', 'Untitled')}")

    if research['procedures']:
        print(f"Procedure: {research['procedures'][0].get('title', 'Untitled')}")

    if research['faults']:
        print(f"Fault: {research['faults'][0].get('title', 'Untitled')}")
