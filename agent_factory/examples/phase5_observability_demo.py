"""
phase5_observability_demo.py - Phase 5 Enhanced Observability Demonstration

Demonstrates:
1. Structured JSON logging with context
2. Error tracking and categorization
3. Metrics export (StatsD, Prometheus, Console)

Usage:
    poetry run python agent_factory/examples/phase5_observability_demo.py
"""

import sys
from pathlib import Path
import time
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agent_factory.observability import (
    # Phase 5 modules
    StructuredLogger,
    LogLevel,
    ErrorTracker,
    ErrorCategory,
    StatsDExporter,
    PrometheusExporter,
    ConsoleExporter,
    Metric
)


def demo_structured_logging():
    """Demonstrate structured JSON logging."""
    print("\n" + "="*70)
    print("DEMO 1: Structured JSON Logging")
    print("="*70 + "\n")

    # Create logger
    logger = StructuredLogger("agent_factory", level=LogLevel.DEBUG)

    # Basic logging
    logger.info("Application started", version="1.0.0", environment="demo")

    # Logging with trace ID
    logger.info(
        "Processing request",
        trace_id="abc123",
        user_id="user_456",
        agent_name="research"
    )

    # Debug logging
    logger.debug("Debug information", component="llm_router", model="gpt-4")

    # Warning logging
    logger.warning(
        "High latency detected",
        latency_ms=250.5,
        threshold_ms=200,
        agent_name="coding"
    )

    # Error logging
    logger.error(
        "Request failed",
        error="Rate limit exceeded",
        retry_count=3,
        trace_id="abc123"
    )

    # Context-based logging (all logs include trace_id automatically)
    print("\nContext-based logging:")
    with logger.with_context(trace_id="xyz789", request_id="req_001") as ctx_logger:
        ctx_logger.info("Request started")
        ctx_logger.info("Calling LLM", provider="openai", model="gpt-4")
        ctx_logger.info("Request completed", duration_ms=150.5)


def demo_error_tracking():
    """Demonstrate error tracking and categorization."""
    print("\n" + "="*70)
    print("DEMO 2: Error Tracking and Categorization")
    print("="*70 + "\n")

    # Create error tracker
    tracker = ErrorTracker(alert_threshold=5)

    print("Recording various error types...\n")

    # Simulate different error categories
    try:
        raise ValueError("Invalid API key provided")
    except Exception as e:
        tracker.record_error(
            exception=e,
            trace_id="trace_001",
            agent_name="research",
            provider="openai"
        )
        print(f"[OK] Recorded authentication error: {e}")

    try:
        raise Exception("Rate limit exceeded. Too many requests.")
    except Exception as e:
        tracker.record_error(
            exception=e,
            trace_id="trace_002",
            agent_name="coding",
            provider="openai"
        )
        print(f"[OK] Recorded rate limit error: {e}")

    try:
        raise TimeoutError("Request timed out after 30 seconds")
    except Exception as e:
        tracker.record_error(
            exception=e,
            trace_id="trace_003",
            agent_name="research",
            provider="anthropic"
        )
        print(f"[OK] Recorded timeout error: {e}")

    # Record multiple validation errors to trigger alert
    for i in range(6):
        tracker.record_error(
            message=f"Validation error {i+1}",
            category=ErrorCategory.VALIDATION,
            agent_name="analyst"
        )

    print(f"\n[OK] Recorded 6 validation errors")

    # Check alert status
    if tracker.should_alert(ErrorCategory.VALIDATION):
        print("[ALERT] Validation errors exceeded threshold!")

    # Get error summary
    print("\nError Summary:")
    summary = tracker.summary()
    print(f"  Total Errors: {summary['total_errors']}")
    print(f"  Unique Categories: {summary['unique_categories']}")

    print("\n  Top Error Categories:")
    for cat in summary['top_categories']:
        print(f"    - {cat['category']}: {cat['count']} errors")

    print("\n  Top Agents with Errors:")
    for agent in summary['top_agents']:
        print(f"    - {agent['agent']}: {agent['errors']} errors")

    print("\n  Alert Status:")
    alert_status = summary['alert_status']
    print(f"    - Threshold: {alert_status['threshold']}")
    print(f"    - Should Alert: {alert_status['should_alert']}")
    print(f"    - Categories Alerting: {alert_status['categories_alerting']}")


def demo_metrics_export():
    """Demonstrate metrics export to different formats."""
    print("\n" + "="*70)
    print("DEMO 3: Metrics Export (StatsD, Prometheus, Console)")
    print("="*70 + "\n")

    # Create sample metrics
    metrics = [
        Metric(
            name="request.count",
            value=150,
            timestamp=datetime.utcnow(),
            tags={"agent": "research", "status": "success"},
            metric_type="counter"
        ),
        Metric(
            name="request.duration",
            value=125.5,
            timestamp=datetime.utcnow(),
            tags={"agent": "research"},
            metric_type="timer"
        ),
        Metric(
            name="cache.hit_rate",
            value=0.85,
            timestamp=datetime.utcnow(),
            tags={"cache_type": "llm_response"},
            metric_type="gauge"
        ),
        Metric(
            name="tokens.total",
            value=1250,
            timestamp=datetime.utcnow(),
            tags={"provider": "openai", "model": "gpt-4"},
            metric_type="counter"
        ),
        Metric(
            name="cost.total_usd",
            value=0.0375,
            timestamp=datetime.utcnow(),
            tags={"provider": "openai"},
            metric_type="gauge"
        )
    ]

    # Export to console (StatsD format)
    print("1. Console Export (StatsD format):")
    console_exporter = ConsoleExporter(format="statsd")
    console_exporter.export(metrics)

    # Export to console (Prometheus format)
    print("\n2. Console Export (Prometheus format):")
    console_exporter_prom = ConsoleExporter(format="prometheus")
    console_exporter_prom.export(metrics[:2])  # Show fewer for brevity

    # StatsD exporter (would send to actual StatsD server in production)
    print("\n3. StatsD Exporter:")
    print("   (Would send to localhost:8125 in production)")
    statsd_exporter = StatsDExporter(host="localhost", port=8125, prefix="agent_factory")
    result = statsd_exporter.export(metrics)
    print(f"   Export successful: {result}")
    statsd_exporter.close()

    # Prometheus exporter
    print("\n4. Prometheus Exporter:")
    prom_exporter = PrometheusExporter(namespace="agent_factory")
    prom_exporter.export(metrics)

    print("   Prometheus exposition format (for /metrics endpoint):")
    prom_text = prom_exporter.export_text()
    print("   " + "\n   ".join(prom_text.split("\n")[:15]))  # Show first 15 lines
    print("   ...")
    prom_exporter.close()


def demo_integrated_observability():
    """Demonstrate integrated observability in a simulated workflow."""
    print("\n" + "="*70)
    print("DEMO 4: Integrated Observability (Logging + Errors + Metrics)")
    print("="*70 + "\n")

    # Initialize observability components
    logger = StructuredLogger("agent_workflow")
    error_tracker = ErrorTracker(alert_threshold=3)
    metrics_exporter = ConsoleExporter(format="statsd")

    # Simulate a workflow
    trace_id = "trace_integrated_001"

    logger.info("Workflow started", trace_id=trace_id, workflow="research_task")

    # Simulate successful request
    start_time = time.time()
    logger.debug("Calling LLM", trace_id=trace_id, provider="openai", model="gpt-4")

    # Simulate some processing
    time.sleep(0.1)

    duration_ms = (time.time() - start_time) * 1000
    logger.info(
        "Request completed",
        trace_id=trace_id,
        duration_ms=round(duration_ms, 2),
        tokens=150
    )

    # Record metrics
    workflow_metrics = [
        Metric("workflow.duration", duration_ms, datetime.utcnow(), {"workflow": "research"}, "timer"),
        Metric("workflow.success", 1, datetime.utcnow(), {"workflow": "research"}, "counter")
    ]
    metrics_exporter.export(workflow_metrics)

    # Simulate an error scenario
    logger.warning("Simulating error scenario", trace_id=trace_id)

    try:
        raise Exception("Rate limit exceeded")
    except Exception as e:
        error_tracker.record_error(
            exception=e,
            trace_id=trace_id,
            agent_name="research",
            provider="openai"
        )
        logger.error(
            "Request failed",
            trace_id=trace_id,
            error=str(e),
            will_retry=True
        )

    # Check if we should alert
    if error_tracker.should_alert():
        logger.critical(
            "Alert threshold exceeded",
            trace_id=trace_id,
            total_errors=len(error_tracker.events)
        )

    logger.info("Workflow completed", trace_id=trace_id)


def main():
    """Run all Phase 5 demos."""
    print("\n")
    print("=" * 70)
    print("  PHASE 5: ENHANCED OBSERVABILITY DEMONSTRATION")
    print("=" * 70)
    print("\n  Features:")
    print("    - Structured JSON Logging")
    print("    - Error Tracking & Categorization")
    print("    - Metrics Export (StatsD, Prometheus)")
    print("=" * 70)

    demo_structured_logging()
    demo_error_tracking()
    demo_metrics_export()
    demo_integrated_observability()

    print("\n" + "="*70)
    print("PHASE 5 DEMONSTRATION COMPLETE")
    print("="*70)
    print("\nNext Steps:")
    print("  1. Integrate with LLMRouter for automatic tracing")
    print("  2. Set up StatsD/Prometheus in production")
    print("  3. Configure alerting thresholds")
    print("  4. Enable structured logging in production\n")


if __name__ == "__main__":
    main()
