"""
RAG Reranker - Cross-Encoder Reranking for RIVET Pro

Improves retrieval quality by reranking initial search results using a
cross-encoder model. Provides more accurate relevance scores than pure
vector or keyword search alone.

Author: Agent Factory
Created: 2025-12-21
Phase: 2/8 (RAG Layer Enhancement)
"""

import logging
from typing import List, Optional, Tuple
from dataclasses import dataclass

from agent_factory.rivet_pro.rag.retriever import RetrievedDoc

# Set up logging
logger = logging.getLogger(__name__)


@dataclass
class RerankConfig:
    """
    Configuration for reranking.

    Attributes:
        model_name: Cross-encoder model to use
        top_k: Number of documents to keep after reranking
        batch_size: Batch size for cross-encoder inference
        max_length: Maximum sequence length for model
    """
    model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    top_k: int = 8
    batch_size: int = 16
    max_length: int = 512


class Reranker:
    """
    Cross-encoder based reranker for RAG retrieval.

    Uses a pre-trained cross-encoder model to score query-document pairs
    and rerank initial retrieval results for better relevance.

    Example:
        >>> from agent_factory.rivet_pro.rag.retriever import search_docs
        >>> from agent_factory.rivet_pro.models import RivetIntent, VendorType
        >>>
        >>> # Get initial retrieval results
        >>> intent = RivetIntent(vendor=VendorType.SIEMENS, symptom="F3002 fault", ...)
        >>> docs = search_docs(intent)
        >>>
        >>> # Rerank for better relevance
        >>> reranker = Reranker()
        >>> reranked_docs = reranker.rerank(query=intent.raw_summary, docs=docs)
        >>> # reranked_docs[0] is now most relevant
    """

    def __init__(self, config: Optional[RerankConfig] = None):
        """
        Initialize reranker.

        Args:
            config: Reranking configuration (uses default if not provided)
        """
        self.config = config if config is not None else RerankConfig()
        self._model = None
        self._model_loaded = False

    def _load_model(self) -> None:
        """
        Lazy-load cross-encoder model on first use.

        Raises:
            ImportError: If sentence-transformers not installed
            RuntimeError: If model fails to load
        """
        if self._model_loaded:
            return

        try:
            from sentence_transformers import CrossEncoder
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Run: poetry add sentence-transformers"
            )

        try:
            logger.info(f"Loading cross-encoder model: {self.config.model_name}")
            self._model = CrossEncoder(
                self.config.model_name,
                max_length=self.config.max_length
            )
            self._model_loaded = True
            logger.info("Cross-encoder model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load cross-encoder model: {e}")
            raise RuntimeError(f"Model loading failed: {e}") from e

    def rerank(
        self,
        query: str,
        docs: List[RetrievedDoc],
        top_k: Optional[int] = None
    ) -> List[RetrievedDoc]:
        """
        Rerank documents using cross-encoder model.

        Args:
            query: User query text
            docs: List of documents from initial retrieval
            top_k: Number of documents to return (uses config default if not provided)

        Returns:
            Reranked documents sorted by cross-encoder score (highest first)

        Example:
            >>> reranker = Reranker()
            >>> query = "Siemens VFD F3002 troubleshooting"
            >>> reranked = reranker.rerank(query, initial_docs, top_k=5)
            >>> len(reranked)
            5
            >>> reranked[0].similarity > reranked[1].similarity
            True
        """
        if not docs:
            logger.warning("No documents to rerank")
            return []

        # Use config default if top_k not specified
        if top_k is None:
            top_k = self.config.top_k

        # Limit to requested top_k (no need to rerank more than needed)
        docs_to_rank = docs[:min(len(docs), top_k * 2)]  # 2x for better reranking

        logger.info(f"Reranking {len(docs_to_rank)} documents for query: {query[:50]}...")

        # Lazy-load model
        self._load_model()

        # Prepare query-document pairs
        pairs = [(query, doc.content) for doc in docs_to_rank]

        # Score all pairs
        try:
            scores = self._model.predict(
                pairs,
                batch_size=self.config.batch_size,
                show_progress_bar=False
            )
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            # Fallback to original order
            return docs[:top_k]

        # Combine scores with documents
        scored_docs: List[Tuple[float, RetrievedDoc]] = []
        for score, doc in zip(scores, docs_to_rank):
            # Update similarity score with cross-encoder score
            doc.similarity = float(score)
            scored_docs.append((float(score), doc))

        # Sort by score (highest first)
        scored_docs.sort(key=lambda x: x[0], reverse=True)

        # Extract top-k documents
        reranked = [doc for score, doc in scored_docs[:top_k]]

        logger.info(
            f"Reranking complete. Top score: {scored_docs[0][0]:.3f}, "
            f"Bottom score: {scored_docs[min(len(scored_docs)-1, top_k-1)][0]:.3f}"
        )

        return reranked

    def score_pair(self, query: str, document: str) -> float:
        """
        Score a single query-document pair.

        Useful for scoring individual documents without full reranking.

        Args:
            query: Query text
            document: Document text

        Returns:
            Relevance score (higher is better, typically -10 to 10)

        Example:
            >>> reranker = Reranker()
            >>> score = reranker.score_pair("motor fault", "ControlLogix motor troubleshooting")
            >>> score > 0
            True
        """
        # Lazy-load model
        self._load_model()

        try:
            score = self._model.predict([(query, document)])[0]
            return float(score)
        except Exception as e:
            logger.error(f"Scoring failed: {e}")
            return 0.0


def rerank_search_results(
    query: str,
    docs: List[RetrievedDoc],
    config: Optional[RerankConfig] = None,
    top_k: Optional[int] = None
) -> List[RetrievedDoc]:
    """
    Convenience function to rerank search results.

    Creates a Reranker instance and performs reranking.

    Args:
        query: User query text
        docs: Documents from initial retrieval
        config: Reranking configuration (uses default if not provided)
        top_k: Number of documents to return (uses config default if not provided)

    Returns:
        Reranked documents sorted by relevance

    Example:
        >>> from agent_factory.rivet_pro.rag.retriever import search_docs
        >>> from agent_factory.rivet_pro.rag.reranker import rerank_search_results
        >>>
        >>> docs = search_docs(intent)
        >>> reranked = rerank_search_results(intent.raw_summary, docs, top_k=5)
    """
    reranker = Reranker(config=config)
    return reranker.rerank(query, docs, top_k=top_k)
