"""
SME (Subject Matter Expert) Agent Template

Standard template for building specialized SME agents for RIVET Pro.
All SME agents should inherit from this base class to ensure consistent
structure, error handling, and observability.

Author: Agent Factory
Created: 2025-12-21
Phase: 3/8 (Agent Templates)
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)


@dataclass
class QueryAnalysis:
    """
    Results of query analysis.

    Attributes:
        domain: Subject domain (e.g., "motor_control", "plc_programming")
        question_type: Type of question (e.g., "troubleshooting", "how_to", "concept")
        key_entities: Important entities extracted from query
        search_keywords: Keywords for KB search
        complexity: Estimated complexity (simple, moderate, complex)
        metadata: Additional analysis metadata
    """
    domain: str
    question_type: str
    key_entities: List[str]
    search_keywords: List[str]
    complexity: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SMEAnswer:
    """
    Structured answer from SME agent.

    Attributes:
        answer_text: The generated answer
        confidence: Confidence score (0.0-1.0)
        sources: List of source document IDs used
        reasoning: Brief explanation of how answer was derived
        follow_up_questions: Suggested follow-up questions
        escalate: Whether to escalate to human expert
        metadata: Additional answer metadata
    """
    answer_text: str
    confidence: float
    sources: List[str]
    reasoning: str
    follow_up_questions: List[str]
    escalate: bool
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "answer_text": self.answer_text,
            "confidence": self.confidence,
            "sources": self.sources,
            "reasoning": self.reasoning,
            "follow_up_questions": self.follow_up_questions,
            "escalate": self.escalate,
            "metadata": self.metadata
        }


class SMEAgentTemplate(ABC):
    """
    Abstract base class for SME agents.

    All SME agents must implement:
    - analyze_query(): Parse and understand user's question
    - search_kb(): Search knowledge base for relevant documents
    - generate_answer(): Generate response from retrieved documents
    - score_confidence(): Assess confidence in the answer

    Example:
        >>> class MotorControlSME(SMEAgentTemplate):
        ...     def __init__(self):
        ...         super().__init__(
        ...             name="Motor Control SME",
        ...             domain="motor_control",
        ...             min_confidence=0.7
        ...         )
        ...
        ...     def analyze_query(self, query: str) -> QueryAnalysis:
        ...         # Implement motor-specific analysis
        ...         return QueryAnalysis(...)
        ...
        ...     def search_kb(self, analysis: QueryAnalysis) -> List[Dict]:
        ...         # Search for motor-related documents
        ...         return docs
        ...
        ...     def generate_answer(self, query: str, docs: List[Dict]) -> str:
        ...         # Generate motor-specific answer
        ...         return answer
        ...
        ...     def score_confidence(self, query: str, answer: str, docs: List[Dict]) -> float:
        ...         # Score answer confidence
        ...         return 0.85
        >>>
        >>> sme = MotorControlSME()
        >>> result = sme.answer("Why is my motor overheating?")
        >>> print(result.answer_text)
    """

    def __init__(
        self,
        name: str,
        domain: str,
        min_confidence: float = 0.7,
        max_docs: int = 10
    ):
        """
        Initialize SME agent template.

        Args:
            name: Agent name (e.g., "Motor Control SME")
            domain: Subject domain (e.g., "motor_control")
            min_confidence: Minimum confidence threshold for answers
            max_docs: Maximum documents to retrieve from KB
        """
        self.name = name
        self.domain = domain
        self.min_confidence = min_confidence
        self.max_docs = max_docs
        self.logger = logging.getLogger(f"sme.{domain}")

    @abstractmethod
    def analyze_query(self, query: str) -> QueryAnalysis:
        """
        Analyze user query to extract intent and search parameters.

        Args:
            query: Raw user question

        Returns:
            QueryAnalysis with domain, question type, entities, keywords

        Example:
            >>> analysis = sme.analyze_query("Why does my motor overheat?")
            >>> analysis.domain
            'motor_control'
            >>> analysis.question_type
            'troubleshooting'
            >>> analysis.key_entities
            ['motor', 'overheat']
        """
        pass

    @abstractmethod
    def search_kb(self, analysis: QueryAnalysis) -> List[Dict[str, Any]]:
        """
        Search knowledge base for relevant documents.

        Args:
            analysis: Query analysis from analyze_query()

        Returns:
            List of relevant documents (dicts with keys: atom_id, title, content, similarity)

        Example:
            >>> docs = sme.search_kb(analysis)
            >>> len(docs) <= self.max_docs
            True
            >>> docs[0]['similarity'] > 0.7
            True
        """
        pass

    @abstractmethod
    def generate_answer(
        self,
        query: str,
        docs: List[Dict[str, Any]]
    ) -> str:
        """
        Generate answer from retrieved documents.

        Args:
            query: Original user question
            docs: Retrieved documents from search_kb()

        Returns:
            Generated answer text

        Example:
            >>> answer = sme.generate_answer(query, docs)
            >>> len(answer) > 50
            True
        """
        pass

    @abstractmethod
    def score_confidence(
        self,
        query: str,
        answer: str,
        docs: List[Dict[str, Any]]
    ) -> float:
        """
        Score confidence in the generated answer.

        Args:
            query: Original question
            answer: Generated answer
            docs: Documents used for answer

        Returns:
            Confidence score (0.0-1.0)

        Example:
            >>> confidence = sme.score_confidence(query, answer, docs)
            >>> 0.0 <= confidence <= 1.0
            True
        """
        pass

    def answer(self, query: str) -> SMEAnswer:
        """
        Main entry point - answer user question.

        Orchestrates the full pipeline:
        1. Analyze query
        2. Search knowledge base
        3. Generate answer
        4. Score confidence
        5. Decide whether to escalate

        Args:
            query: User's question

        Returns:
            SMEAnswer with answer text, confidence, sources, etc.

        Example:
            >>> result = sme.answer("Why is my motor overheating?")
            >>> result.confidence > 0.7
            True
            >>> len(result.sources) > 0
            True
        """
        self.logger.info(f"Processing query: {query[:50]}...")
        start_time = datetime.now()

        try:
            # Step 1: Analyze query
            self.logger.debug("Step 1: Analyzing query...")
            analysis = self.analyze_query(query)
            self.logger.debug(f"Analysis complete: domain={analysis.domain}, type={analysis.question_type}")

            # Step 2: Search KB
            self.logger.debug(f"Step 2: Searching KB with keywords: {analysis.search_keywords[:5]}")
            docs = self.search_kb(analysis)
            self.logger.debug(f"Retrieved {len(docs)} documents")

            if not docs:
                # No documents found - escalate immediately
                return SMEAnswer(
                    answer_text="I don't have enough information to answer this question accurately.",
                    confidence=0.0,
                    sources=[],
                    reasoning="No relevant documents found in knowledge base",
                    follow_up_questions=[],
                    escalate=True,
                    metadata={
                        "analysis": analysis.__dict__,
                        "latency_ms": (datetime.now() - start_time).total_seconds() * 1000
                    }
                )

            # Step 3: Generate answer
            self.logger.debug("Step 3: Generating answer...")
            answer_text = self.generate_answer(query, docs)

            # Step 4: Score confidence
            self.logger.debug("Step 4: Scoring confidence...")
            confidence = self.score_confidence(query, answer_text, docs)

            # Step 5: Decide escalation
            escalate = confidence < self.min_confidence
            if escalate:
                self.logger.warning(
                    f"Low confidence ({confidence:.2f}), escalating to human expert"
                )

            # Build result
            result = SMEAnswer(
                answer_text=answer_text,
                confidence=confidence,
                sources=[doc.get("atom_id", "") for doc in docs],
                reasoning=f"Generated from {len(docs)} relevant documents with avg similarity {sum(doc.get('similarity', 0) for doc in docs) / len(docs):.2f}",
                follow_up_questions=self._generate_follow_ups(query, analysis),
                escalate=escalate,
                metadata={
                    "analysis": analysis.__dict__,
                    "doc_count": len(docs),
                    "latency_ms": (datetime.now() - start_time).total_seconds() * 1000,
                    "domain": self.domain,
                    "agent_name": self.name
                }
            )

            self.logger.info(
                f"Answer generated: confidence={confidence:.2f}, "
                f"sources={len(result.sources)}, "
                f"escalate={escalate}"
            )

            return result

        except Exception as e:
            self.logger.error(f"Error answering query: {e}", exc_info=True)
            # Return error answer with escalation
            return SMEAnswer(
                answer_text="I encountered an error while processing your question.",
                confidence=0.0,
                sources=[],
                reasoning=f"Error: {str(e)}",
                follow_up_questions=[],
                escalate=True,
                metadata={
                    "error": str(e),
                    "latency_ms": (datetime.now() - start_time).total_seconds() * 1000
                }
            )

    def _generate_follow_ups(
        self,
        query: str,
        analysis: QueryAnalysis
    ) -> List[str]:
        """
        Generate follow-up questions (default implementation).

        Subclasses can override for domain-specific follow-ups.

        Args:
            query: Original question
            analysis: Query analysis

        Returns:
            List of follow-up questions
        """
        # Default: generic follow-ups based on question type
        if analysis.question_type == "troubleshooting":
            return [
                "What error codes are you seeing?",
                "When did this issue start?",
                "Have you made any recent changes?"
            ]
        elif analysis.question_type == "how_to":
            return [
                "What equipment are you using?",
                "What's your current setup?",
                "Are there any specific constraints?"
            ]
        else:
            return [
                "Can you provide more details?",
                "What have you tried so far?"
            ]
