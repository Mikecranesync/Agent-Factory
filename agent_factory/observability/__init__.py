"""
Agent Factory Observability Package

Production monitoring and observability for agent systems.

Phase 3 Features:
- Request tracing (end-to-end visibility)
- Performance metrics (latency, success rates)
- Cost tracking (API usage costs)

Phase 5 Enhancements:
- Structured JSON logging
- Error categorization and tracking
- Metrics export (StatsD, Prometheus)

Usage:
    from agent_factory.observability import (
        Tracer, Metrics, CostTracker,
        StructuredLogger, ErrorTracker, StatsDExporter
    )

    # Create observability components
    tracer = Tracer()
    metrics = Metrics()
    cost_tracker = CostTracker()

    # Phase 5: Structured logging
    logger = StructuredLogger("agent_factory")
    logger.info("Request started", trace_id="abc123", user_id="user1")

    # Phase 5: Error tracking
    error_tracker = ErrorTracker(alert_threshold=10)
    try:
        result = api_call()
    except Exception as e:
        error_tracker.record_error(e, trace_id="abc123")

    # Phase 5: Metrics export
    exporter = StatsDExporter(host="localhost", port=8125)
    exporter.export(metrics_list)

Available Classes:
    # Phase 3
    Tracer: Request tracing with spans
    Trace: Complete request trace
    Span: Single operation in a trace
    Metrics: Performance metrics aggregator
    CostTracker: API cost calculator and tracker

    # Phase 5
    StructuredLogger: JSON-formatted logging
    LogLevel: Log severity levels
    ErrorTracker: Error categorization and tracking
    ErrorCategory: Error classification enum
    ErrorEvent: Individual error occurrence
    StatsDExporter: Export to StatsD/Datadog
    PrometheusExporter: Export to Prometheus
    ConsoleExporter: Debug export to console
    Metric: Individual metric data point
"""

# Phase 3 - Base observability
from .tracer import Tracer, Trace, Span
from .metrics import Metrics
from .cost_tracker import CostTracker

# Phase 5 - Enhanced observability
from .logger import StructuredLogger, LogLevel, LoggerContext
from .errors import ErrorTracker, ErrorCategory, ErrorEvent
from .exporters import (
    StatsDExporter,
    PrometheusExporter,
    ConsoleExporter,
    MetricsExporter,
    Metric
)

# LangFuse integration for LangGraph workflows
from .langfuse_tracker import LangFuseTracker, create_tracked_callback

__all__ = [
    # Phase 3: Tracing
    "Tracer",
    "Trace",
    "Span",
    # Phase 3: Metrics
    "Metrics",
    # Phase 3: Cost tracking
    "CostTracker",
    # Phase 5: Structured logging
    "StructuredLogger",
    "LogLevel",
    "LoggerContext",
    # Phase 5: Error tracking
    "ErrorTracker",
    "ErrorCategory",
    "ErrorEvent",
    # Phase 5: Metrics export
    "StatsDExporter",
    "PrometheusExporter",
    "ConsoleExporter",
    "MetricsExporter",
    "Metric",
    # LangFuse observability
    "LangFuseTracker",
    "create_tracked_callback",
]
