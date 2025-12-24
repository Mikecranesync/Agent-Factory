"""Performance instrumentation utilities for RIVET orchestrator.

Provides decorators and context managers for measuring operation latency.
"""

import time
import logging
from functools import wraps
from typing import Optional, Callable
from contextlib import contextmanager

logger = logging.getLogger(__name__)


def timed_operation(operation_name: str, log_level: int = logging.INFO):
    """Decorator to measure and log operation execution time.

    Usage:
        @timed_operation("route_c_handler")
        async def _route_c_no_kb(self, request, decision):
            ...

    Args:
        operation_name: Name to display in logs
        log_level: Logging level (default: INFO)

    Returns:
        Decorated function that logs execution time
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start) * 1000
                logger.log(
                    log_level,
                    f"⏱️  PERF [{operation_name}]: {duration_ms:.1f}ms"
                )
                return result
            except Exception as e:
                duration_ms = (time.perf_counter() - start) * 1000
                logger.error(
                    f"⏱️  PERF [{operation_name}]: {duration_ms:.1f}ms (FAILED: {e})"
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start) * 1000
                logger.log(
                    log_level,
                    f"⏱️  PERF [{operation_name}]: {duration_ms:.1f}ms"
                )
                return result
            except Exception as e:
                duration_ms = (time.perf_counter() - start) * 1000
                logger.error(
                    f"⏱️  PERF [{operation_name}]: {duration_ms:.1f}ms (FAILED: {e})"
                )
                raise

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


@contextmanager
def timer(operation_name: str, log_level: int = logging.INFO):
    """Context manager to measure code block execution time.

    Usage:
        with timer("database_query"):
            result = db.execute(query)

    Args:
        operation_name: Name to display in logs
        log_level: Logging level (default: INFO)

    Yields:
        None
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.log(
            log_level,
            f"⏱️  PERF [{operation_name}]: {duration_ms:.1f}ms"
        )


class PerformanceTracker:
    """Track cumulative performance metrics across operations.

    Usage:
        tracker = PerformanceTracker()

        with tracker.measure("llm_call"):
            response = llm.complete(messages)

        with tracker.measure("db_query"):
            results = db.query(sql)

        print(tracker.summary())
    """

    def __init__(self):
        self.operations = {}
        self.total_time_ms = 0.0

    @contextmanager
    def measure(self, operation_name: str):
        """Measure and record operation time.

        Args:
            operation_name: Name of operation to measure

        Yields:
            None
        """
        start = time.perf_counter()
        try:
            yield
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            self.total_time_ms += duration_ms

            if operation_name not in self.operations:
                self.operations[operation_name] = {
                    "count": 0,
                    "total_ms": 0.0,
                    "min_ms": float('inf'),
                    "max_ms": 0.0
                }

            op = self.operations[operation_name]
            op["count"] += 1
            op["total_ms"] += duration_ms
            op["min_ms"] = min(op["min_ms"], duration_ms)
            op["max_ms"] = max(op["max_ms"], duration_ms)

    def summary(self) -> str:
        """Generate performance summary report.

        Returns:
            Formatted string with operation statistics
        """
        if not self.operations:
            return "No operations measured"

        lines = ["=" * 70]
        lines.append("PERFORMANCE SUMMARY")
        lines.append("=" * 70)

        for op_name, stats in sorted(
            self.operations.items(),
            key=lambda x: x[1]["total_ms"],
            reverse=True
        ):
            avg_ms = stats["total_ms"] / stats["count"]
            pct = (stats["total_ms"] / self.total_time_ms * 100) if self.total_time_ms > 0 else 0

            lines.append(
                f"{op_name:30s} | "
                f"Calls: {stats['count']:3d} | "
                f"Total: {stats['total_ms']:7.1f}ms ({pct:5.1f}%) | "
                f"Avg: {avg_ms:6.1f}ms | "
                f"Min: {stats['min_ms']:6.1f}ms | "
                f"Max: {stats['max_ms']:6.1f}ms"
            )

        lines.append("=" * 70)
        lines.append(f"TOTAL TIME: {self.total_time_ms:.1f}ms")
        lines.append("=" * 70)

        return "\n".join(lines)

    def reset(self):
        """Reset all tracked metrics."""
        self.operations.clear()
        self.total_time_ms = 0.0
