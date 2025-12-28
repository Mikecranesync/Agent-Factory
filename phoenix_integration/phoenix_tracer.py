"""
Phoenix Tracer Module for Agent Factory

Production-ready tracing integration for industrial maintenance agents.
Works with Groq, OpenAI, and Anthropic LLM providers.

Usage:
    from phoenix_tracer import traced, init_phoenix, wrap_client
    
    # Initialize once at startup
    session = init_phoenix()
    
    # Wrap your LLM client
    client = wrap_client(Groq())
    
    # Or use decorator for agent functions
    @traced(agent_name="siemens_sme")
    async def diagnose_fault(fault_code: str) -> dict:
        ...
"""

import os
import functools
import time
from typing import Any, Callable, Optional, TypeVar, ParamSpec
from datetime import datetime
import logging

# Type hints for decorators
P = ParamSpec('P')
T = TypeVar('T')

logger = logging.getLogger(__name__)

# Global session reference
_phoenix_session = None
_phoenix_available = False
_tracer = None

try:
    import phoenix as px
    from phoenix.otel import register
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    _phoenix_available = True
except ImportError:
    logger.warning("Phoenix not installed. Run: pip install arize-phoenix[evals]")
    px = None
    trace = None


def init_phoenix(
    project_name: str = "agent_factory",
    port: int = 6006,
    launch_app: bool = True
) -> Optional[Any]:
    """
    Initialize Phoenix session with OpenTelemetry.

    Args:
        project_name: Name for this project's traces
        port: Phoenix UI port (default 6006)
        launch_app: Whether to launch Phoenix app (False if already running)

    Returns:
        TracerProvider or None if unavailable
    """
    global _phoenix_session, _tracer

    if not _phoenix_available:
        logger.warning("Phoenix not available. Tracing disabled.")
        return None

    if _phoenix_session is not None:
        return _phoenix_session

    try:
        if launch_app:
            px.launch_app(port=port)
            logger.info(f"Phoenix UI available at http://localhost:{port}")

        # Register Phoenix OTEL tracer
        tracer_provider = register(
            project_name=project_name,
            endpoint=f"http://localhost:{port}/v1/traces"
        )
        _phoenix_session = tracer_provider
        _tracer = trace.get_tracer(__name__)
        logger.info(f"Phoenix OTEL tracer registered for project: {project_name}")

        return tracer_provider
    except Exception as e:
        logger.error(f"Failed to initialize Phoenix: {e}")
        return None


def wrap_client(client: Any, provider: str = "auto") -> Any:
    """
    Wrap an LLM client for automatic tracing using OpenInference.

    Args:
        client: Groq, OpenAI, or Anthropic client instance
        provider: "groq", "openai", "anthropic", or "auto" to detect

    Returns:
        Original client (instrumentation happens globally)
    """
    if not _phoenix_available:
        return client

    # Auto-detect provider
    if provider == "auto":
        client_type = type(client).__name__.lower()
        if "groq" in client_type:
            provider = "groq"
        elif "openai" in client_type:
            provider = "openai"
        elif "anthropic" in client_type:
            provider = "anthropic"
        else:
            logger.warning(f"Unknown client type: {client_type}. Tracing may be limited.")
            provider = "unknown"

    try:
        # Use OpenInference instrumentors
        if provider == "groq":
            try:
                from openinference.instrumentation.groq import GroqInstrumentor
                GroqInstrumentor().instrument(tracer_provider=_phoenix_session)
                logger.info("Groq client instrumented with OpenInference")
            except ImportError:
                logger.warning("openinference-instrumentation-groq not installed. Run: pip install openinference-instrumentation-groq")

        elif provider == "openai":
            try:
                from openinference.instrumentation.openai import OpenAIInstrumentor
                OpenAIInstrumentor().instrument(tracer_provider=_phoenix_session)
                logger.info("OpenAI client instrumented with OpenInference")
            except ImportError:
                logger.warning("openinference-instrumentation-openai not installed. Run: pip install openinference-instrumentation-openai")

        return client
    except Exception as e:
        logger.error(f"Failed to instrument {provider} client: {e}")
        return client


def traced(
    agent_name: str,
    route: Optional[str] = None,
    capture_output: bool = True,
    log_errors: bool = True
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator to trace agent function calls.
    
    Args:
        agent_name: Name of the agent (e.g., "siemens_sme", "rockwell_sme")
        route: Orchestrator route that called this agent
        capture_output: Whether to capture function output in trace
        log_errors: Whether to log errors to Phoenix
    
    Usage:
        @traced(agent_name="siemens_sme", route="technical")
        def diagnose_plc_fault(fault_code: str) -> dict:
            ...
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            if not _phoenix_available or _tracer is None:
                return func(*args, **kwargs)

            start_time = time.time()

            # Prepare span attributes
            span_attrs = {
                "agent_name": agent_name,
                "route": route or "unknown",
                "function": func.__name__,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Add any user_id or session_id from kwargs
            if "user_id" in kwargs:
                span_attrs["user_id"] = str(kwargs["user_id"])
            if "session_id" in kwargs:
                span_attrs["session_id"] = str(kwargs["session_id"])
            if "chat_id" in kwargs:
                span_attrs["telegram_chat_id"] = str(kwargs["chat_id"])

            try:
                with _tracer.start_as_current_span(
                    name=f"{agent_name}.{func.__name__}",
                    attributes=span_attrs
                ) as span:
                    # Capture input
                    span.set_attribute("input.args", str(args)[:1000])
                    span.set_attribute("input.kwargs", str(kwargs)[:1000])

                    result = func(*args, **kwargs)

                    # Capture output
                    if capture_output:
                        span.set_attribute("output", str(result)[:2000])

                    # Capture latency
                    latency_ms = (time.time() - start_time) * 1000
                    span.set_attribute("latency_ms", latency_ms)

                    span.set_status(Status(StatusCode.OK))
                    return result

            except Exception as e:
                if log_errors:
                    logger.error(f"Error in {agent_name}.{func.__name__}: {e}")
                    if _phoenix_available and _tracer:
                        try:
                            with _tracer.start_as_current_span(name=f"{agent_name}.error") as error_span:
                                error_span.set_attribute("error", str(e))
                                error_span.set_attribute("agent_name", agent_name)
                                error_span.set_attribute("function", func.__name__)
                                error_span.set_status(Status(StatusCode.ERROR, str(e)))
                        except:
                            pass
                raise
        
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            if not _phoenix_available or _tracer is None:
                return await func(*args, **kwargs)

            start_time = time.time()

            # Prepare span attributes
            span_attrs = {
                "agent_name": agent_name,
                "route": route or "unknown",
                "function": func.__name__,
                "timestamp": datetime.utcnow().isoformat(),
                "async": True,
            }

            if "user_id" in kwargs:
                span_attrs["user_id"] = str(kwargs["user_id"])
            if "session_id" in kwargs:
                span_attrs["session_id"] = str(kwargs["session_id"])
            if "chat_id" in kwargs:
                span_attrs["telegram_chat_id"] = str(kwargs["chat_id"])

            try:
                with _tracer.start_as_current_span(
                    name=f"{agent_name}.{func.__name__}",
                    attributes=span_attrs
                ) as span:
                    span.set_attribute("input.args", str(args)[:1000])
                    span.set_attribute("input.kwargs", str(kwargs)[:1000])

                    result = await func(*args, **kwargs)

                    if capture_output:
                        span.set_attribute("output", str(result)[:2000])

                    latency_ms = (time.time() - start_time) * 1000
                    span.set_attribute("latency_ms", latency_ms)

                    span.set_status(Status(StatusCode.OK))
                    return result

            except Exception as e:
                if log_errors:
                    logger.error(f"Error in {agent_name}.{func.__name__}: {e}")
                raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def log_ocr_result(
    image_path: str,
    ocr_text: str,
    confidence: float,
    agent_name: str = "ocr_processor"
) -> None:
    """
    Log OCR processing results as a Phoenix event.

    Args:
        image_path: Path or URL to processed image
        ocr_text: Extracted text
        confidence: OCR confidence score (0-1)
        agent_name: Name of OCR agent
    """
    if not _phoenix_available or _tracer is None:
        return

    try:
        with _tracer.start_as_current_span(name=f"{agent_name}.ocr_result") as span:
            span.set_attribute("image_path", image_path)
            span.set_attribute("ocr_text", ocr_text[:2000])
            span.set_attribute("confidence", confidence)
            span.set_attribute("text_length", len(ocr_text))
            span.set_status(Status(StatusCode.OK))
    except Exception as e:
        logger.error(f"Failed to log OCR result: {e}")


def log_route_decision(
    query: str,
    selected_route: str,
    confidence: float,
    all_routes: dict[str, float]
) -> None:
    """
    Log orchestrator routing decision.

    Args:
        query: User query that was routed
        selected_route: Route that was selected
        confidence: Confidence in selection
        all_routes: Dict of route -> confidence scores
    """
    if not _phoenix_available or _tracer is None:
        return

    try:
        with _tracer.start_as_current_span(name="orchestrator.route_decision") as span:
            span.set_attribute("query", query[:500])
            span.set_attribute("selected_route", selected_route)
            span.set_attribute("confidence", confidence)
            span.set_attribute("route_scores", str(all_routes))
            span.set_status(Status(StatusCode.OK))
    except Exception as e:
        logger.error(f"Failed to log route decision: {e}")


def log_knowledge_retrieval(
    query: str,
    retrieved_atoms: list[dict],
    retrieval_time_ms: float
) -> None:
    """
    Log knowledge base retrieval for Neon/vector search debugging.

    Args:
        query: Search query
        retrieved_atoms: List of retrieved knowledge atoms
        retrieval_time_ms: Time taken for retrieval
    """
    if not _phoenix_available or _tracer is None:
        return

    try:
        with _tracer.start_as_current_span(name="knowledge_base.retrieval") as span:
            span.set_attribute("query", query[:500])
            span.set_attribute("num_results", len(retrieved_atoms))
            span.set_attribute("retrieval_time_ms", retrieval_time_ms)

            # Log top 3 atom IDs for debugging
            top_atoms = [a.get("atom_id", "unknown") for a in retrieved_atoms[:3]]
            span.set_attribute("top_atom_ids", str(top_atoms))
            span.set_status(Status(StatusCode.OK))
    except Exception as e:
        logger.error(f"Failed to log knowledge retrieval: {e}")


# Auto-initialize on import if PHOENIX_AUTO_INIT env var is set
if os.getenv("PHOENIX_AUTO_INIT", "").lower() == "true":
    init_phoenix(launch_app=False)
