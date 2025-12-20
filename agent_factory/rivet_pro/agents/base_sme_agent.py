"""
Base SME (Subject Matter Expert) Agent for RIVET Pro Phase 3.

All vendor-specific agents inherit from this base class which provides:
- RAG integration (knowledge base search)
- LLM-based response generation
- Citation extraction
- Common response formatting
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any
import os

from agent_factory.rivet_pro.models import (
    RivetRequest,
    RivetIntent,
    RivetResponse,
    AgentID,
    RouteType,
    KBCoverage
)
from agent_factory.rivet_pro.rag.retriever import (
    search_docs,
    estimate_coverage,
    RetrievedDoc
)
from agent_factory.rivet_pro.rag.config import RAGConfig


class BaseSMEAgent(ABC):
    """
    Abstract base class for all Subject Matter Expert agents.

    Concrete agents must implement:
    - get_system_prompt() - Returns vendor/domain-specific expertise prompt
    - agent_id property - Returns AgentID enum value
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        temperature: float = 0.2,
        rag_config: Optional[RAGConfig] = None
    ):
        """
        Initialize base SME agent.

        Args:
            model: OpenAI model name (default: gpt-4o-mini for cost optimization)
            temperature: LLM temperature (default: 0.2 for factual responses)
            rag_config: Optional RAG configuration overrides
        """
        self.model = model
        self.temperature = temperature
        self.rag_config = rag_config or RAGConfig()

    @property
    @abstractmethod
    def agent_id(self) -> AgentID:
        """Return the agent's unique identifier."""
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Return the system prompt defining this agent's expertise.

        This prompt should include:
        - Domain-specific terminology and concepts
        - Common fault codes or error patterns
        - Vendor-specific tools and software
        - Safety disclaimers if applicable

        Returns:
            System prompt string for LLM
        """
        pass

    def _search_knowledge(self, intent: RivetIntent) -> List[RetrievedDoc]:
        """
        Search knowledge base for relevant documents.

        Args:
            intent: Classified user intent with vendor/equipment context

        Returns:
            List of retrieved documents sorted by relevance
        """
        try:
            docs = search_docs(
                intent=intent,
                config=self.rag_config,
                db=None  # Uses default database connection
            )
            return docs
        except Exception as e:
            # Graceful fallback: log error but continue with empty docs
            print(f"[WARN] RAG search failed: {e}. Continuing with zero docs.")
            return []

    def _extract_citations(self, docs: List[RetrievedDoc]) -> List[Dict[str, Any]]:
        """
        Extract citation metadata from retrieved documents.

        Args:
            docs: List of retrieved documents

        Returns:
            List of citation dictionaries with source, page, similarity
        """
        citations = []
        for i, doc in enumerate(docs, start=1):
            citation = {
                "id": f"ref_{i}",
                "atom_id": doc.atom_id,
                "title": doc.title,
                "source": doc.source or "Knowledge Base",
                "page_number": doc.page_number,
                "similarity": round(doc.similarity, 2),
                "vendor": doc.vendor,
                "equipment_type": doc.equipment_type,
            }
            citations.append(citation)
        return citations

    def _build_rag_context(self, docs: List[RetrievedDoc]) -> str:
        """
        Build formatted RAG context for LLM prompt.

        Args:
            docs: List of retrieved documents

        Returns:
            Formatted string with document summaries and content
        """
        if not docs:
            return "No relevant knowledge base articles found."

        context_parts = ["**Relevant Knowledge Base Articles:**\n"]

        for i, doc in enumerate(docs, start=1):
            context_parts.append(f"\n[{i}] **{doc.title}**")
            context_parts.append(f"Source: {doc.source or 'KB'}")
            if doc.page_number:
                context_parts.append(f"Page: {doc.page_number}")
            context_parts.append(f"Summary: {doc.summary}")
            context_parts.append(f"Content: {doc.content[:800]}...")  # Truncate long content
            context_parts.append("")  # Blank line

        return "\n".join(context_parts)

    def _generate_response_text(
        self,
        intent: RivetIntent,
        rag_context: str,
        request: RivetRequest
    ) -> str:
        """
        Generate response text using LLM.

        Args:
            intent: Classified user intent
            rag_context: Formatted KB articles
            request: Original user request

        Returns:
            Generated response text
        """
        try:
            # Import OpenAI here to avoid initialization overhead if not used
            from openai import OpenAI

            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            # Build user prompt
            user_prompt = f"""
User Question: {request.text}

Vendor: {intent.vendor.value if intent.vendor else "Unknown"}
Equipment: {intent.equipment_type.value if intent.equipment_type else "Unknown"}
Symptom: {intent.symptom_description or "Not specified"}

{rag_context}

Please provide a clear, actionable troubleshooting response. If the knowledge base
articles are relevant, cite them using [1], [2] notation. If no relevant info was
found, provide general guidance based on best practices.
"""

            # Call LLM
            response = client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": self.get_system_prompt()},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=1000
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            # Graceful fallback
            return f"I encountered an error generating the response: {str(e)}. " \
                   f"Please try again or contact support."

    def handle(
        self,
        request: RivetRequest,
        intent: RivetIntent,
        route: RouteType
    ) -> RivetResponse:
        """
        Main handler for processing requests.

        This orchestrates the full agent workflow:
        1. Search knowledge base
        2. Build RAG context
        3. Generate LLM response
        4. Extract citations
        5. Return structured response

        Args:
            request: Original user request
            intent: Classified intent
            route: Routing decision (A/B/C/D)

        Returns:
            Structured RivetResponse with text, citations, and metadata
        """
        # Step 1: Search KB
        docs = self._search_knowledge(intent)

        # Step 2: Build RAG context
        rag_context = self._build_rag_context(docs)

        # Step 3: Generate response
        response_text = self._generate_response_text(intent, rag_context, request)

        # Step 4: Extract citations
        citations = self._extract_citations(docs)

        # Step 5: Determine confidence and flags
        confidence = 0.8 if len(docs) >= 2 else 0.5 if len(docs) == 1 else 0.5
        kb_enrichment_triggered = len(docs) == 0  # Trigger research if no docs

        # Step 6: Build trace metadata
        trace = {
            "agent_id": self.agent_id.value,
            "route": route.value,
            "docs_retrieved": len(docs),
            "kb_coverage": intent.kb_coverage.value if intent.kb_coverage else "unknown",
            "llm_model": self.model,
            "temperature": self.temperature,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Step 7: Return structured response
        return RivetResponse(
            text=response_text,
            agent_id=self.agent_id,
            route_taken=route,
            confidence=confidence,
            cited_documents=citations,
            kb_enrichment_triggered=kb_enrichment_triggered,
            trace=trace,
            channel=request.channel,
            user_id=request.user_id
        )
