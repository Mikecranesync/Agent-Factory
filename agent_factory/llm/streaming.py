"""
Streaming Support - LLM Response Streaming (Future)

Provides streaming interface for LLM responses, enabling real-time
token-by-token output for better UX.

Currently a stub - full implementation pending.
"""

from typing import Iterator, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class StreamChunk:
    """
    Single chunk from a streaming LLM response.

    Attributes:
        text: Text content of this chunk
        is_final: Whether this is the final chunk
        metadata: Optional metadata (model, usage, etc.)
    """
    text: str
    is_final: bool = False
    metadata: Optional[Dict[str, Any]] = None


def stream_complete(
    messages: list,
    config: Any,
    **kwargs
) -> Iterator[StreamChunk]:
    """
    Stream LLM completion response.

    Args:
        messages: Message list
        config: LLM config
        **kwargs: Additional arguments

    Yields:
        StreamChunk objects

    Currently not implemented - raises NotImplementedError.
    """
    raise NotImplementedError(
        "Streaming not yet implemented. "
        "Use LLMRouter.complete() for non-streaming calls."
    )


def collect_stream(stream: Iterator[StreamChunk]) -> str:
    """
    Collect all chunks from a stream into full text.

    Args:
        stream: Iterator of StreamChunk objects

    Returns:
        Complete text from all chunks

    Currently not implemented - raises NotImplementedError.
    """
    raise NotImplementedError(
        "Streaming not yet implemented. "
        "Use LLMRouter.complete() for non-streaming calls."
    )
