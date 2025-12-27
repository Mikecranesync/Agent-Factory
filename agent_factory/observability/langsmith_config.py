"""LangSmith tracing configuration.

Provides decorators and utilities for tracing API endpoints.
"""
import os
import functools
from typing import Callable
import logging

logger = logging.getLogger(__name__)

# Initialize LangSmith client
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "rivet-api")
LANGSMITH_ENABLED = bool(LANGSMITH_API_KEY)

# Import LangSmith only if enabled
if LANGSMITH_ENABLED:
    try:
        from langsmith import Client
        client = Client(api_key=LANGSMITH_API_KEY)
        logger.info(f"LangSmith tracing enabled for project: {LANGSMITH_PROJECT}")
    except ImportError:
        logger.warning("langsmith package not installed. Install with: pip install langsmith")
        client = None
        LANGSMITH_ENABLED = False
else:
    client = None
    logger.warning("LangSmith tracing disabled (no API key)")


def trace_endpoint(name: str = None, metadata: dict = None):
    """
    Decorator to trace FastAPI endpoint execution with LangSmith.

    Usage:
        @router.post("/users/provision")
        @trace_endpoint(name="provision_user", metadata={"category": "users"})
        async def provision_user(request: UserProvisionRequest):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if not LANGSMITH_ENABLED or not client:
                # Skip tracing if not enabled
                return await func(*args, **kwargs)

            trace_name = name or func.__name__
            trace_metadata = metadata or {}
            trace_metadata["endpoint"] = func.__name__
            trace_metadata["project"] = LANGSMITH_PROJECT

            # Create run tree for this endpoint call
            try:
                with client.start_run(
                    name=trace_name,
                    run_type="chain",
                    inputs={"args": str(args), "kwargs": str(kwargs)},
                    metadata=trace_metadata
                ) as run:
                    try:
                        result = await func(*args, **kwargs)
                        run.end(outputs={"result": str(result)})
                        return result
                    except Exception as e:
                        run.end(error=str(e))
                        raise
            except Exception as e:
                logger.error(f"LangSmith tracing error: {e}")
                # Continue without tracing if LangSmith fails
                return await func(*args, **kwargs)

        return wrapper
    return decorator


def get_trace_url(run_id: str) -> str:
    """Get LangSmith trace URL for a run ID."""
    if not LANGSMITH_ENABLED:
        return None
    return f"https://smith.langchain.com/o/{LANGSMITH_PROJECT}/runs/{run_id}"


def track_llm_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    metadata: dict = None
):
    """
    Track LLM usage costs in LangSmith.

    Usage:
        response = llm.invoke(prompt)
        track_llm_cost(
            model="claude-sonnet-4",
            input_tokens=response.usage_metadata["input_tokens"],
            output_tokens=response.usage_metadata["output_tokens"],
            metadata={"endpoint": "provision_user"}
        )
    """
    if not LANGSMITH_ENABLED or not client:
        return

    trace_metadata = metadata or {}
    trace_metadata.update({
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "project": LANGSMITH_PROJECT
    })

    try:
        with client.start_run(
            name="llm_cost_tracking",
            run_type="llm",
            inputs={"model": model},
            metadata=trace_metadata
        ) as run:
            # Calculate approximate cost (update pricing as needed)
            pricing = {
                "claude-sonnet-4": {"input": 0.003, "output": 0.015},  # per 1k tokens
                "gpt-4o": {"input": 0.005, "output": 0.015},
            }

            if model in pricing:
                input_cost = (input_tokens / 1000) * pricing[model]["input"]
                output_cost = (output_tokens / 1000) * pricing[model]["output"]
                total_cost = input_cost + output_cost

                run.end(outputs={
                    "input_cost_usd": input_cost,
                    "output_cost_usd": output_cost,
                    "total_cost_usd": total_cost
                })
            else:
                run.end(outputs={"error": f"Unknown model: {model}"})
    except Exception as e:
        logger.error(f"LangSmith cost tracking error: {e}")
