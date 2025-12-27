"""VPS log monitoring via SSH for real-time troubleshooting."""

import asyncio
import paramiko
from typing import List, Optional, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class VPSLogMonitor:
    """Monitor VPS logs via SSH for real-time troubleshooting."""

    def __init__(self):
        self.host = "72.60.175.144"
        self.username = "root"
        self.key_file = Path.home() / ".ssh" / "vps_deploy_key"
        self.timeout = 5  # seconds

    def tail_recent_errors(self, last_n_lines: int = 20) -> List[str]:
        """Tail last N lines of error log.

        Args:
            last_n_lines: Number of lines to tail from error log

        Returns:
            List of error log lines (empty list if connection fails)
        """
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                self.host,
                username=self.username,
                key_filename=str(self.key_file),
                timeout=5
            )

            stdin, stdout, stderr = ssh.exec_command(
                f"tail -n {last_n_lines} /root/Agent-Factory/logs/bot-error.log"
            )
            errors = stdout.read().decode('utf-8').split('\n')
            ssh.close()
            return [e for e in errors if e.strip()]
        except Exception as e:
            logger.warning(f"VPS log tail failed: {e}")
            return [f"VPS log check failed: {e}"]

    def search_recent_traces(self, trace_id: str) -> Optional[str]:
        """Search for specific trace ID in logs.

        Args:
            trace_id: Trace ID to search for

        Returns:
            Matching trace line (None if not found or connection fails)
        """
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                self.host,
                username=self.username,
                key_filename=str(self.key_file),
                timeout=5
            )

            stdin, stdout, stderr = ssh.exec_command(
                f"grep '{trace_id}' /root/Agent-Factory/logs/traces.jsonl | tail -n 1"
            )
            result = stdout.read().decode('utf-8').strip()
            ssh.close()
            return result if result else None
        except Exception as e:
            logger.warning(f"VPS trace search failed: {e}")
            return None

    async def fetch_vps_logs_for_trace(self, trace_id: str) -> Dict[str, Any]:
        """
        Main entry point - fetch VPS logs for a trace ID asynchronously.

        Args:
            trace_id: Trace ID to fetch logs for

        Returns:
            Dictionary with error_log_tail and trace_search results.
            Returns {"error": str, "available": False} if connection fails.
        """
        try:
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(None, self._fetch_logs_sync, trace_id),
                timeout=self.timeout
            )
            return result
        except asyncio.TimeoutError:
            logger.warning(f"VPS log fetch timeout after {self.timeout}s")
            return {"error": "VPS connection timeout", "available": False}
        except Exception as e:
            logger.error(f"VPS log fetch error: {e}")
            return {"error": str(e), "available": False}

    def _fetch_logs_sync(self, trace_id: str) -> Dict[str, Any]:
        """
        Synchronous SSH operations (run in executor).

        Args:
            trace_id: Trace ID to fetch logs for

        Returns:
            Dictionary with error_log_tail and trace_search results
        """
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh.connect(
                self.host,
                username=self.username,
                key_filename=str(self.key_file),
                timeout=3
            )

            # Fetch error log tail
            stdin, stdout, stderr = ssh.exec_command(
                "tail -n 20 /root/Agent-Factory/logs/bot-error.log 2>/dev/null || echo 'No error log'"
            )
            error_log = stdout.read().decode('utf-8', errors='replace').strip()

            # Search for trace ID
            stdin, stdout, stderr = ssh.exec_command(
                f"grep '{trace_id}' /root/Agent-Factory/logs/traces.jsonl 2>/dev/null | tail -n 1"
            )
            trace_line = stdout.read().decode('utf-8', errors='replace').strip()

            return {
                "available": True,
                "error_log_tail": error_log.split('\n')[-20:],  # Last 20 lines
                "trace_search": trace_line if trace_line else "No trace found"
            }

        finally:
            ssh.close()
