"""
tests/test_phase5_observability.py - Phase 5 Enhanced Observability Tests

Tests for structured logging, error tracking, and metrics export.

Test Coverage:
- StructuredLogger: JSON logging, log levels, context management (12 tests)
- ErrorTracker: Categorization, frequency tracking, alerts (12 tests)
- Exporters: StatsD, Prometheus, Console (10 tests)
Total: 34 tests
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
import json
from datetime import datetime
import tempfile

from agent_factory.observability import (
    # Phase 5 modules
    StructuredLogger,
    LogLevel,
    ErrorTracker,
    ErrorCategory,
    ErrorEvent,
    StatsDExporter,
    PrometheusExporter,
    ConsoleExporter,
    Metric
)


# ============================================================================
# StructuredLogger Tests (12 tests)
# ============================================================================

class TestStructuredLogger:
    """Test structured JSON logging."""

    def test_logger_creation(self):
        """Test logger can be created with defaults."""
        logger = StructuredLogger("test")
        assert logger.name == "test"
        assert logger.level == LogLevel.INFO

    def test_logger_info_log(self, capsys):
        """Test INFO level logging outputs JSON."""
        logger = StructuredLogger("test")
        logger.info("Test message", user_id="user123")

        captured = capsys.readouterr()
        log_data = json.loads(captured.out.strip())

        assert log_data["level"] == "INFO"
        assert log_data["logger"] == "test"
        assert log_data["message"] == "Test message"
        assert log_data["user_id"] == "user123"
        assert "timestamp" in log_data

    def test_logger_debug_filtered(self, capsys):
        """Test DEBUG messages filtered when level is INFO."""
        logger = StructuredLogger("test", level=LogLevel.INFO)
        logger.debug("Debug message")

        captured = capsys.readouterr()
        assert captured.out == ""

    def test_logger_debug_shown_when_enabled(self, capsys):
        """Test DEBUG messages shown when level is DEBUG."""
        logger = StructuredLogger("test", level=LogLevel.DEBUG)
        logger.debug("Debug message")

        captured = capsys.readouterr()
        log_data = json.loads(captured.out.strip())
        assert log_data["level"] == "DEBUG"

    def test_logger_error_log(self, capsys):
        """Test ERROR level logging."""
        logger = StructuredLogger("test")
        logger.error("Error occurred", error_code=500)

        captured = capsys.readouterr()
        log_data = json.loads(captured.out.strip())

        assert log_data["level"] == "ERROR"
        assert log_data["error_code"] == 500

    def test_logger_warning_log(self, capsys):
        """Test WARNING level logging."""
        logger = StructuredLogger("test")
        logger.warning("Warning message")

        captured = capsys.readouterr()
        log_data = json.loads(captured.out.strip())
        assert log_data["level"] == "WARNING"

    def test_logger_critical_log(self, capsys):
        """Test CRITICAL level logging."""
        logger = StructuredLogger("test")
        logger.critical("Critical error")

        captured = capsys.readouterr()
        log_data = json.loads(captured.out.strip())
        assert log_data["level"] == "CRITICAL"

    def test_logger_set_level(self, capsys):
        """Test changing log level."""
        logger = StructuredLogger("test", level=LogLevel.INFO)
        logger.debug("Should not appear")

        logger.set_level(LogLevel.DEBUG)
        logger.debug("Should appear")

        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        assert len(lines) == 1  # Only second debug message

    def test_logger_context_manager(self, capsys):
        """Test logger with context manager for bound fields."""
        logger = StructuredLogger("test")

        with logger.with_context(trace_id="abc123") as ctx_logger:
            ctx_logger.info("Message 1")
            ctx_logger.info("Message 2", user_id="user1")

        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")

        log1 = json.loads(lines[0])
        log2 = json.loads(lines[1])

        assert log1["trace_id"] == "abc123"
        assert log2["trace_id"] == "abc123"
        assert log2["user_id"] == "user1"

    def test_logger_file_output(self):
        """Test logging to file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = Path(f.name)

        try:
            logger = StructuredLogger("test", output_file=log_file)
            logger.info("File message", key="value")

            # Close logger handlers to release file
            for handler in logger._logger.handlers:
                handler.close()

            # Read log file
            content = log_file.read_text()
            log_data = json.loads(content.strip())

            assert log_data["message"] == "File message"
            assert log_data["key"] == "value"
        finally:
            try:
                log_file.unlink()
            except PermissionError:
                pass  # File may still be locked on Windows

    def test_logger_no_timestamp(self, capsys):
        """Test logger without timestamp."""
        logger = StructuredLogger("test", include_timestamp=False)
        logger.info("Test")

        captured = capsys.readouterr()
        log_data = json.loads(captured.out.strip())
        assert "timestamp" not in log_data

    def test_logger_with_hostname(self, capsys):
        """Test logger with hostname."""
        logger = StructuredLogger("test", include_hostname=True)
        logger.info("Test")

        captured = capsys.readouterr()
        log_data = json.loads(captured.out.strip())
        assert "hostname" in log_data


# ============================================================================
# ErrorTracker Tests (12 tests)
# ============================================================================

class TestErrorTracker:
    """Test error tracking and categorization."""

    def test_error_tracker_creation(self):
        """Test error tracker can be created."""
        tracker = ErrorTracker(alert_threshold=5)
        assert tracker.alert_threshold == 5
        assert len(tracker.events) == 0

    def test_error_tracker_record_error(self):
        """Test recording an error."""
        tracker = ErrorTracker()
        event = tracker.record_error(
            message="Test error",
            category=ErrorCategory.VALIDATION,
            trace_id="abc123"
        )

        assert event.category == ErrorCategory.VALIDATION
        assert event.message == "Test error"
        assert event.trace_id == "abc123"
        assert len(tracker.events) == 1

    def test_error_tracker_categorize_auth_error(self):
        """Test automatic categorization of authentication errors."""
        tracker = ErrorTracker()

        error = ValueError("Invalid API key provided")
        event = tracker.record_error(exception=error)

        assert event.category == ErrorCategory.AUTHENTICATION

    def test_error_tracker_categorize_rate_limit(self):
        """Test automatic categorization of rate limit errors."""
        tracker = ErrorTracker()

        error = Exception("Rate limit exceeded. Too many requests.")
        event = tracker.record_error(exception=error)

        assert event.category == ErrorCategory.RATE_LIMIT

    def test_error_tracker_categorize_timeout(self):
        """Test automatic categorization of timeout errors."""
        tracker = ErrorTracker()

        error = TimeoutError("Request timed out")
        event = tracker.record_error(exception=error)

        assert event.category == ErrorCategory.TIMEOUT

    def test_error_tracker_category_counts(self):
        """Test error category counting."""
        tracker = ErrorTracker()

        tracker.record_error(message="Error 1", category=ErrorCategory.VALIDATION)
        tracker.record_error(message="Error 2", category=ErrorCategory.VALIDATION)
        tracker.record_error(message="Error 3", category=ErrorCategory.NETWORK)

        assert tracker.category_counts[ErrorCategory.VALIDATION] == 2
        assert tracker.category_counts[ErrorCategory.NETWORK] == 1

    def test_error_tracker_alert_threshold(self):
        """Test alert threshold detection."""
        tracker = ErrorTracker(alert_threshold=3)

        tracker.record_error(message="Error 1", category=ErrorCategory.VALIDATION)
        assert not tracker.should_alert(ErrorCategory.VALIDATION)

        tracker.record_error(message="Error 2", category=ErrorCategory.VALIDATION)
        assert not tracker.should_alert(ErrorCategory.VALIDATION)

        tracker.record_error(message="Error 3", category=ErrorCategory.VALIDATION)
        assert tracker.should_alert(ErrorCategory.VALIDATION)

    def test_error_tracker_agent_errors(self):
        """Test tracking errors by agent."""
        tracker = ErrorTracker()

        tracker.record_error(message="Error 1", agent_name="research", category=ErrorCategory.NETWORK)
        tracker.record_error(message="Error 2", agent_name="research", category=ErrorCategory.TIMEOUT)
        tracker.record_error(message="Error 3", agent_name="coding", category=ErrorCategory.TOOL_ERROR)

        assert sum(tracker.agent_errors["research"].values()) == 2
        assert sum(tracker.agent_errors["coding"].values()) == 1

    def test_error_tracker_provider_errors(self):
        """Test tracking errors by provider."""
        tracker = ErrorTracker()

        tracker.record_error(message="Error 1", provider="openai", category=ErrorCategory.RATE_LIMIT)
        tracker.record_error(message="Error 2", provider="openai", category=ErrorCategory.TIMEOUT)
        tracker.record_error(message="Error 3", provider="anthropic", category=ErrorCategory.NETWORK)

        assert sum(tracker.provider_errors["openai"].values()) == 2
        assert sum(tracker.provider_errors["anthropic"].values()) == 1

    def test_error_tracker_get_errors_by_category(self):
        """Test retrieving errors by category."""
        tracker = ErrorTracker()

        tracker.record_error(message="Error 1", category=ErrorCategory.VALIDATION)
        tracker.record_error(message="Error 2", category=ErrorCategory.NETWORK)
        tracker.record_error(message="Error 3", category=ErrorCategory.VALIDATION)

        validation_errors = tracker.get_errors_by_category(ErrorCategory.VALIDATION)
        assert len(validation_errors) == 2

    def test_error_tracker_summary(self):
        """Test error summary generation."""
        tracker = ErrorTracker(alert_threshold=2)

        tracker.record_error(message="Error 1", category=ErrorCategory.VALIDATION, agent_name="research")
        tracker.record_error(message="Error 2", category=ErrorCategory.VALIDATION, agent_name="research")
        tracker.record_error(message="Error 3", category=ErrorCategory.NETWORK, provider="openai")

        summary = tracker.summary()

        assert summary["total_errors"] == 3
        assert summary["unique_categories"] == 2
        assert len(summary["top_categories"]) > 0
        assert summary["alert_status"]["should_alert"]

    def test_error_tracker_clear(self):
        """Test clearing error tracker."""
        tracker = ErrorTracker()

        tracker.record_error(message="Error 1", category=ErrorCategory.VALIDATION)
        tracker.record_error(message="Error 2", category=ErrorCategory.NETWORK)

        assert len(tracker.events) == 2

        tracker.clear()

        assert len(tracker.events) == 0
        assert sum(tracker.category_counts.values()) == 0


# ============================================================================
# Metrics Exporters Tests (10 tests)
# ============================================================================

class TestMetricsExporters:
    """Test metrics export to different formats."""

    def test_metric_creation(self):
        """Test creating a metric."""
        metric = Metric(
            name="request.duration",
            value=150.5,
            timestamp=datetime.utcnow(),
            tags={"agent": "research"},
            metric_type="timer"
        )

        assert metric.name == "request.duration"
        assert metric.value == 150.5
        assert metric.tags["agent"] == "research"

    def test_metric_to_statsd(self):
        """Test metric StatsD formatting."""
        metric = Metric(
            name="request.count",
            value=1,
            timestamp=datetime.utcnow(),
            tags={"agent": "research", "status": "success"},
            metric_type="counter"
        )

        statsd_str = metric.to_statsd()

        assert "request.count:1|c|#" in statsd_str
        assert "agent:research" in statsd_str
        assert "status:success" in statsd_str

    def test_metric_to_prometheus(self):
        """Test metric Prometheus formatting."""
        metric = Metric(
            name="request_duration_seconds",
            value=0.150,
            timestamp=datetime.utcnow(),
            tags={"agent": "research"},
            metric_type="histogram"
        )

        prom_str = metric.to_prometheus()

        assert "# TYPE request_duration_seconds histogram" in prom_str
        assert 'agent="research"' in prom_str
        assert "0.15" in prom_str

    def test_statsd_exporter_creation(self):
        """Test StatsD exporter creation."""
        exporter = StatsDExporter(host="localhost", port=8125, prefix="test")

        assert exporter.host == "localhost"
        assert exporter.port == 8125
        assert exporter.prefix == "test"

    def test_statsd_exporter_export(self):
        """Test StatsD export (doesn't actually send, just validates)."""
        exporter = StatsDExporter(host="localhost", port=8125)

        metrics = [
            Metric("request.count", 1, datetime.utcnow(), {"agent": "research"}, "counter"),
            Metric("request.duration", 150.5, datetime.utcnow(), {"agent": "research"}, "timer")
        ]

        # Should not raise exception
        result = exporter.export(metrics)
        assert result is True

        exporter.close()

    def test_prometheus_exporter_creation(self):
        """Test Prometheus exporter creation."""
        exporter = PrometheusExporter(namespace="test")

        assert exporter.namespace == "test"
        assert len(exporter.metrics_buffer) == 0

    def test_prometheus_exporter_export_text(self):
        """Test Prometheus text export."""
        exporter = PrometheusExporter(namespace="test")

        metrics = [
            Metric("request_count", 10, datetime.utcnow(), {"agent": "research"}, "counter"),
            Metric("request_duration", 150.5, datetime.utcnow(), {"agent": "research"}, "gauge")
        ]

        text = exporter.export_text(metrics)

        assert "# TYPE test_request_count counter" in text
        assert "# TYPE test_request_duration gauge" in text
        assert 'agent="research"' in text

    def test_console_exporter_statsd_format(self, capsys):
        """Test console export in StatsD format."""
        exporter = ConsoleExporter(format="statsd")

        metrics = [
            Metric("request.count", 1, datetime.utcnow(), {}, "counter")
        ]

        exporter.export(metrics)

        captured = capsys.readouterr()
        assert "request.count:1|c" in captured.out
        assert "=== Metrics Export (statsd) ===" in captured.out

    def test_console_exporter_prometheus_format(self, capsys):
        """Test console export in Prometheus format."""
        exporter = ConsoleExporter(format="prometheus")

        metrics = [
            Metric("request_count", 1, datetime.utcnow(), {}, "counter")
        ]

        exporter.export(metrics)

        captured = capsys.readouterr()
        assert "# TYPE request_count counter" in captured.out

    def test_prometheus_exporter_buffer(self):
        """Test Prometheus exporter buffering."""
        exporter = PrometheusExporter()

        metrics = [
            Metric("request_count", 1, datetime.utcnow(), {}, "counter")
        ]

        exporter.export(metrics)
        assert len(exporter.metrics_buffer) == 1

        exporter.clear_buffer()
        assert len(exporter.metrics_buffer) == 0


# ============================================================================
# Summary
# ============================================================================

def test_phase5_module_imports():
    """Test that all Phase 5 modules can be imported."""
    from agent_factory.observability import (
        StructuredLogger,
        LogLevel,
        LoggerContext,
        ErrorTracker,
        ErrorCategory,
        ErrorEvent,
        StatsDExporter,
        PrometheusExporter,
        ConsoleExporter,
        Metric
    )

    assert StructuredLogger is not None
    assert LogLevel is not None
    assert ErrorTracker is not None
    assert StatsDExporter is not None
