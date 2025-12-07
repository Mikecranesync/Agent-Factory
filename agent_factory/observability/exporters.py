"""
exporters.py - Metrics export to external monitoring systems

Phase 5 Enhancement: Export metrics to production monitoring tools
(StatsD, Prometheus, CloudWatch, Datadog).

Features:
- StatsD format export (for Datadog, Grafana)
- Prometheus metrics endpoint
- CloudWatch compatible metrics
- Custom metric collectors
- Batch export for efficiency
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import socket
import time


@dataclass
class Metric:
    """
    Represents a single metric data point.

    Compatible with multiple export formats.
    """
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str]
    metric_type: str = "gauge"  # gauge, counter, histogram, timer

    def to_statsd(self) -> str:
        """
        Format metric as StatsD string.

        Format: metric_name:value|type|#tag1:val1,tag2:val2

        Returns:
            StatsD-formatted string
        """
        # Map metric types to StatsD types
        type_map = {
            "gauge": "g",
            "counter": "c",
            "timer": "ms",
            "histogram": "h"
        }
        statsd_type = type_map.get(self.metric_type, "g")

        # Format tags
        if self.tags:
            tags_str = ",".join(f"{k}:{v}" for k, v in self.tags.items())
            return f"{self.name}:{self.value}|{statsd_type}|#{tags_str}"
        else:
            return f"{self.name}:{self.value}|{statsd_type}"

    def to_prometheus(self) -> str:
        """
        Format metric as Prometheus exposition format.

        Format:
            # HELP metric_name Description
            # TYPE metric_name type
            metric_name{label1="value1"} value timestamp

        Returns:
            Prometheus-formatted string
        """
        # Map metric types to Prometheus types
        type_map = {
            "gauge": "gauge",
            "counter": "counter",
            "timer": "summary",
            "histogram": "histogram"
        }
        prom_type = type_map.get(self.metric_type, "gauge")

        # Format labels
        if self.tags:
            labels_str = ",".join(f'{k}="{v}"' for k, v in self.tags.items())
            metric_line = f"{self.name}{{{labels_str}}} {self.value}"
        else:
            metric_line = f"{self.name} {self.value}"

        # Add timestamp (Unix milliseconds)
        timestamp_ms = int(self.timestamp.timestamp() * 1000)
        metric_line += f" {timestamp_ms}"

        return f"# TYPE {self.name} {prom_type}\n{metric_line}"


class MetricsExporter(ABC):
    """
    Abstract base class for metrics exporters.

    Subclasses implement export to specific monitoring systems.
    """

    @abstractmethod
    def export(self, metrics: List[Metric]) -> bool:
        """
        Export metrics to monitoring system.

        Args:
            metrics: List of metrics to export

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close exporter and clean up resources."""
        pass


class StatsDExporter(MetricsExporter):
    """
    Export metrics to StatsD-compatible systems.

    Compatible with:
    - Datadog (via DogStatsD)
    - Grafana Cloud
    - Graphite
    - InfluxDB

    Usage:
        exporter = StatsDExporter(host="localhost", port=8125)
        metrics = [
            Metric("request.duration", 150.5, datetime.now(), {"agent": "research"}, "timer"),
            Metric("request.count", 1, datetime.now(), {"agent": "research"}, "counter")
        ]
        exporter.export(metrics)
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8125,
        prefix: str = "agent_factory",
        max_packet_size: int = 1432  # Max UDP packet size
    ):
        """
        Initialize StatsD exporter.

        Args:
            host: StatsD server hostname
            port: StatsD server port
            prefix: Metric name prefix
            max_packet_size: Maximum UDP packet size
        """
        self.host = host
        self.port = port
        self.prefix = prefix
        self.max_packet_size = max_packet_size

        # Create UDP socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setblocking(False)

    def export(self, metrics: List[Metric]) -> bool:
        """
        Export metrics to StatsD server.

        Args:
            metrics: List of metrics to export

        Returns:
            True if successful
        """
        try:
            # Convert metrics to StatsD format
            statsd_lines = []
            for metric in metrics:
                # Add prefix
                metric_name = f"{self.prefix}.{metric.name}" if self.prefix else metric.name
                metric_copy = Metric(
                    name=metric_name,
                    value=metric.value,
                    timestamp=metric.timestamp,
                    tags=metric.tags,
                    metric_type=metric.metric_type
                )
                statsd_lines.append(metric_copy.to_statsd())

            # Batch metrics into UDP packets
            packets = self._batch_metrics(statsd_lines)

            # Send packets
            for packet in packets:
                self.socket.sendto(packet.encode('utf-8'), (self.host, self.port))

            return True

        except Exception as e:
            # Log error but don't fail
            print(f"StatsD export failed: {e}")
            return False

    def _batch_metrics(self, metrics: List[str]) -> List[str]:
        """
        Batch metrics into packets that fit within max_packet_size.

        Args:
            metrics: List of StatsD metric strings

        Returns:
            List of packet strings
        """
        packets = []
        current_packet = []
        current_size = 0

        for metric in metrics:
            metric_size = len(metric) + 1  # +1 for newline

            if current_size + metric_size > self.max_packet_size:
                # Packet full, start new one
                if current_packet:
                    packets.append("\n".join(current_packet))
                current_packet = [metric]
                current_size = metric_size
            else:
                current_packet.append(metric)
                current_size += metric_size

        # Add final packet
        if current_packet:
            packets.append("\n".join(current_packet))

        return packets

    def close(self) -> None:
        """Close UDP socket."""
        self.socket.close()


class PrometheusExporter(MetricsExporter):
    """
    Export metrics in Prometheus exposition format.

    Provides /metrics endpoint format for Prometheus scraping.

    Usage:
        exporter = PrometheusExporter()
        metrics = [
            Metric("request_duration_seconds", 0.150, datetime.now(), {"agent": "research"}, "histogram")
        ]
        prometheus_text = exporter.export_text(metrics)
        # Serve via HTTP endpoint
    """

    def __init__(self, namespace: str = "agent_factory"):
        """
        Initialize Prometheus exporter.

        Args:
            namespace: Metric namespace prefix
        """
        self.namespace = namespace
        self.metrics_buffer: List[Metric] = []

    def export(self, metrics: List[Metric]) -> bool:
        """
        Store metrics in buffer for export.

        Args:
            metrics: List of metrics to export

        Returns:
            True always
        """
        self.metrics_buffer.extend(metrics)
        return True

    def export_text(self, metrics: Optional[List[Metric]] = None) -> str:
        """
        Export metrics as Prometheus text format.

        Args:
            metrics: Optional metrics list (uses buffer if not provided)

        Returns:
            Prometheus exposition format text
        """
        if metrics is None:
            metrics = self.metrics_buffer

        # Group metrics by name
        grouped: Dict[str, List[Metric]] = {}
        for metric in metrics:
            metric_name = f"{self.namespace}_{metric.name}" if self.namespace else metric.name
            if metric_name not in grouped:
                grouped[metric_name] = []
            grouped[metric_name].append(metric)

        # Format each metric group
        output_lines = []
        for name, metric_list in grouped.items():
            # Get metric type from first metric
            metric_type = metric_list[0].metric_type
            prom_type = {
                "gauge": "gauge",
                "counter": "counter",
                "timer": "summary",
                "histogram": "histogram"
            }.get(metric_type, "gauge")

            # Add TYPE header
            output_lines.append(f"# TYPE {name} {prom_type}")

            # Add metric values
            for metric in metric_list:
                if metric.tags:
                    labels = ",".join(f'{k}="{v}"' for k, v in metric.tags.items())
                    line = f"{name}{{{labels}}} {metric.value}"
                else:
                    line = f"{name} {metric.value}"
                output_lines.append(line)

            output_lines.append("")  # Blank line between metric families

        return "\n".join(output_lines)

    def clear_buffer(self) -> None:
        """Clear metrics buffer."""
        self.metrics_buffer.clear()

    def close(self) -> None:
        """Clear buffer on close."""
        self.clear_buffer()


class ConsoleExporter(MetricsExporter):
    """
    Export metrics to console (for debugging).

    Usage:
        exporter = ConsoleExporter()
        exporter.export(metrics)
    """

    def __init__(self, format: str = "statsd"):
        """
        Initialize console exporter.

        Args:
            format: Output format ("statsd" or "prometheus")
        """
        self.format = format

    def export(self, metrics: List[Metric]) -> bool:
        """
        Print metrics to console.

        Args:
            metrics: List of metrics to export

        Returns:
            True always
        """
        print(f"\n=== Metrics Export ({self.format}) ===")

        for metric in metrics:
            if self.format == "statsd":
                print(metric.to_statsd())
            elif self.format == "prometheus":
                print(metric.to_prometheus())
            else:
                print(f"{metric.name}: {metric.value} ({metric.tags})")

        print("=" * 40)
        return True

    def close(self) -> None:
        """No cleanup needed."""
        pass


# Convenience function for creating exporters
def create_exporter(exporter_type: str, **kwargs) -> MetricsExporter:
    """
    Create metrics exporter by type.

    Args:
        exporter_type: Type of exporter ("statsd", "prometheus", "console")
        **kwargs: Exporter-specific configuration

    Returns:
        MetricsExporter instance

    Raises:
        ValueError: Unknown exporter type
    """
    if exporter_type == "statsd":
        return StatsDExporter(**kwargs)
    elif exporter_type == "prometheus":
        return PrometheusExporter(**kwargs)
    elif exporter_type == "console":
        return ConsoleExporter(**kwargs)
    else:
        raise ValueError(f"Unknown exporter type: {exporter_type}")
