"""
SME Agent Example - Motor Control SME

Demonstrates how to build a specialized SME agent using the SMEAgentTemplate.
This example shows a simplified Motor Control SME that answers motor-related questions.

Usage:
    poetry run python examples/sme_agent_example.py

Author: Agent Factory
Created: 2025-12-21
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_factory.templates import SMEAgentTemplate
from agent_factory.templates.sme_agent_template import QueryAnalysis, SMEAnswer


class MotorControlSMEExample(SMEAgentTemplate):
    """
    Example Motor Control SME agent.

    Simplified implementation for demonstration purposes.
    Production version in agent_factory/rivet_pro/agents/motor_control_sme.py
    """

    def __init__(self):
        super().__init__(
            name="Motor Control SME (Example)",
            domain="motor_control",
            min_confidence=0.7,
            max_docs=8
        )

    def analyze_query(self, query: str) -> QueryAnalysis:
        """
        Analyze motor-related query.

        Simplified implementation using keyword matching.
        Production would use LLM for better analysis.
        """
        query_lower = query.lower()

        # Determine question type
        if any(word in query_lower for word in ["why", "fault", "error", "problem"]):
            question_type = "troubleshooting"
        elif any(word in query_lower for word in ["how", "setup", "configure"]):
            question_type = "how_to"
        else:
            question_type = "concept"

        # Extract keywords (simple regex)
        # Remove stop words and keep meaningful terms
        stop_words = {"is", "my", "the", "a", "an", "does", "why", "how", "what"}
        words = re.findall(r'\w+', query_lower)
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        # Extract entities (simplified - just look for motor-related terms)
        entities = []
        motor_terms = ["motor", "vfd", "drive", "contactor", "relay"]
        for term in motor_terms:
            if term in query_lower:
                entities.append(term)

        # Estimate complexity
        if len(keywords) <= 3:
            complexity = "simple"
        elif len(keywords) <= 6:
            complexity = "moderate"
        else:
            complexity = "complex"

        return QueryAnalysis(
            domain="motor_control",
            question_type=question_type,
            key_entities=entities,
            search_keywords=keywords[:5],  # Top 5 keywords
            complexity=complexity,
            metadata={
                "word_count": len(words),
                "original_query": query
            }
        )

    def search_kb(self, analysis: QueryAnalysis) -> List[Dict[str, Any]]:
        """
        Search knowledge base for motor documents.

        Simplified implementation using mock data.
        Production would use PostgreSQL + pgvector + reranking.
        """
        # Mock knowledge base (in production, query real DB)
        kb = [
            {
                "atom_id": "motor-001",
                "title": "Motor Overheating Causes",
                "content": "Motors overheat due to: 1) Overload conditions, 2) Poor ventilation, 3) Bearing failures, 4) High ambient temperature. Check load current first.",
                "similarity": 0.9 if "overheat" in analysis.search_keywords else 0.3
            },
            {
                "atom_id": "motor-002",
                "title": "VFD Fault Codes",
                "content": "Common VFD faults: F001 Overcurrent, F002 Overvoltage, F003 Undervoltage. Check input power and motor connections.",
                "similarity": 0.85 if "vfd" in analysis.key_entities or "fault" in analysis.search_keywords else 0.2
            },
            {
                "atom_id": "motor-003",
                "title": "Motor Vibration Troubleshooting",
                "content": "Excessive vibration causes: 1) Misalignment, 2) Unbalanced rotor, 3) Worn bearings, 4) Loose mounting. Use vibration analyzer for diagnosis.",
                "similarity": 0.88 if "vibration" in analysis.search_keywords or "vibrate" in analysis.search_keywords else 0.1
            },
            {
                "atom_id": "motor-004",
                "title": "Motor Wiring Basics",
                "content": "Three-phase motor wiring: Connect L1, L2, L3 to motor terminals T1, T2, T3. Verify rotation direction. Ground motor frame.",
                "similarity": 0.75 if "wiring" in analysis.search_keywords or "wire" in analysis.search_keywords else 0.15
            },
            {
                "atom_id": "motor-005",
                "title": "Motor Starting Methods",
                "content": "Motor starting methods: 1) Direct-on-line (DOL), 2) Star-delta, 3) Soft starter, 4) VFD. VFD provides best control and efficiency.",
                "similarity": 0.7 if "start" in analysis.search_keywords else 0.2
            }
        ]

        # Filter and sort by similarity
        relevant_docs = [doc for doc in kb if doc["similarity"] > 0.5]
        relevant_docs.sort(key=lambda x: x["similarity"], reverse=True)

        # Return top-k
        return relevant_docs[:self.max_docs]

    def generate_answer(self, query: str, docs: List[Dict[str, Any]]) -> str:
        """
        Generate answer from documents.

        Simplified implementation using template.
        Production would use LLM (GPT-4o-mini) for better answers.
        """
        if not docs:
            return "I don't have enough information to answer this question."

        # Build answer from top 2 documents
        answer_parts = []

        # Add primary answer from top document
        top_doc = docs[0]
        answer_parts.append(f"Based on motor control documentation:\n\n{top_doc['content']}")

        # Add supporting info from second document if available
        if len(docs) > 1:
            second_doc = docs[1]
            answer_parts.append(f"\n\nAdditional context from {second_doc['title']}:\n{second_doc['content'][:200]}...")

        # Add citations
        citations = ", ".join([doc["atom_id"] for doc in docs[:3]])
        answer_parts.append(f"\n\n[Sources: {citations}]")

        return "\n".join(answer_parts)

    def score_confidence(
        self,
        query: str,
        answer: str,
        docs: List[Dict[str, Any]]
    ) -> float:
        """
        Score answer confidence.

        Combines document relevance, coverage, and answer quality.
        """
        if not docs:
            return 0.0

        # Factor 1: Average document similarity
        avg_similarity = sum(doc["similarity"] for doc in docs) / len(docs)

        # Factor 2: Document coverage (did we find enough?)
        coverage_score = min(len(docs) / 3, 1.0)  # 3+ docs = 1.0

        # Factor 3: Answer length (too short = low confidence)
        length_score = min(len(answer) / 200, 1.0)  # 200+ chars = 1.0

        # Factor 4: Keyword overlap (does answer mention query keywords?)
        query_words = set(query.lower().split())
        answer_words = set(answer.lower().split())
        overlap = len(query_words & answer_words) / len(query_words) if query_words else 0
        overlap_score = overlap

        # Weighted combination
        confidence = (
            avg_similarity * 0.4 +
            coverage_score * 0.2 +
            length_score * 0.2 +
            overlap_score * 0.2
        )

        return min(confidence, 1.0)


def main():
    """Run example SME agent"""
    print("=" * 60)
    print("Motor Control SME Agent - Example")
    print("=" * 60)

    # Create agent
    sme = MotorControlSMEExample()

    # Test queries
    queries = [
        "Why is my motor overheating?",
        "How do I wire a three-phase motor?",
        "What causes excessive motor vibration?",
        "VFD fault troubleshooting",
        "How do I configure a firewall?"  # Out of domain (should escalate)
    ]

    for query in queries:
        print(f"\n{'-' * 60}")
        print(f"Question: {query}")
        print(f"{'-' * 60}")

        # Get answer
        result = sme.answer(query)

        # Display result
        print(f"\nAnswer:\n{result.answer_text[:300]}...")
        print(f"\nConfidence: {result.confidence:.2f}")
        print(f"Sources: {result.sources}")
        print(f"Escalate: {result.escalate}")

        if result.escalate:
            print("WARNING: LOW CONFIDENCE - Escalating to human expert")

        if result.follow_up_questions:
            print(f"\nSuggested follow-ups:")
            for i, q in enumerate(result.follow_up_questions, 1):
                print(f"  {i}. {q}")

        # Display metadata
        print(f"\nMetadata:")
        print(f"  - Latency: {result.metadata.get('latency_ms', 0):.0f}ms")
        print(f"  - Documents: {result.metadata.get('doc_count', 0)}")
        print(f"  - Domain: {result.metadata.get('domain')}")

    print(f"\n{'=' * 60}")
    print("Example complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
