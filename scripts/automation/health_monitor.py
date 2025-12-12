#!/usr/bin/env python3
"""
HEALTH MONITOR - 24/7 System Monitoring

Runs every 15 minutes to check system health:
1. Are scheduled tasks running?
2. Is Supabase responding?
3. When was last successful atom upload?
4. Are there critical errors in logs?
5. Send alerts if issues detected

Usage:
    poetry run python scripts/health_monitor.py

Logs: data/logs/health_monitor.log
Alerts: Telegram (critical issues only)
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client

# ============================================================================
# CONFIGURATION
# ============================================================================

# Logging setup
log_dir = Path("data/logs")
log_dir.mkdir(parents=True, exist_ok=True)

log_file = log_dir / "health_monitor.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Credentials
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

# Health check thresholds
MAX_HOURS_NO_ACTIVITY = 24  # Alert if no atom uploads in 24 hours
MAX_ERRORS_IN_LOG = 10      # Alert if >10 errors in recent logs

# ============================================================================
# UTILITIES
# ============================================================================

def send_telegram_alert(message: str):
    """Send critical alert to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram not configured")
        return

    try:
        import requests
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": f"🚨 **HEALTH ALERT**\n\n{message}",
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            logger.info("Telegram alert sent")
        else:
            logger.error(f"Telegram alert failed: {response.text}")
    except Exception as e:
        logger.error(f"Failed to send Telegram alert: {e}")


# ============================================================================
# HEALTH CHECKS
# ============================================================================

def check_supabase_connection() -> Dict[str, Any]:
    """
    Check if Supabase is responding.
    Returns: Health status dict
    """
    logger.info("Checking Supabase connection...")

    if not SUPABASE_URL or not SUPABASE_KEY:
        return {
            "status": "error",
            "message": "Supabase credentials not configured"
        }

    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        # Simple query to test connection
        result = supabase.table("knowledge_atoms").select("id", count="exact").limit(1).execute()

        return {
            "status": "healthy",
            "message": "Supabase responding",
            "total_atoms": result.count
        }

    except Exception as e:
        logger.error(f"Supabase connection failed: {e}")
        return {
            "status": "critical",
            "message": f"Supabase unreachable: {str(e)}"
        }


def check_last_atom_upload() -> Dict[str, Any]:
    """
    Check when last atom was uploaded.
    Returns: Health status dict
    """
    logger.info("Checking last atom upload time...")

    if not SUPABASE_URL or not SUPABASE_KEY:
        return {"status": "error", "message": "Supabase not configured"}

    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        # Get most recent atom by created_at
        result = supabase.table("knowledge_atoms").select("created_at").order("created_at", desc=True).limit(1).execute()

        if not result.data:
            return {
                "status": "warning",
                "message": "No atoms in database"
            }

        last_upload = datetime.fromisoformat(result.data[0]['created_at'].replace('Z', '+00:00'))
        now = datetime.now(last_upload.tzinfo)
        hours_since = (now - last_upload).total_seconds() / 3600

        if hours_since > MAX_HOURS_NO_ACTIVITY:
            return {
                "status": "critical",
                "message": f"No atom uploads in {hours_since:.1f} hours (threshold: {MAX_HOURS_NO_ACTIVITY}h)",
                "last_upload": last_upload.isoformat()
            }

        return {
            "status": "healthy",
            "message": f"Last upload {hours_since:.1f} hours ago",
            "last_upload": last_upload.isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to check last upload: {e}")
        return {
            "status": "error",
            "message": f"Check failed: {str(e)}"
        }


def check_recent_logs() -> Dict[str, Any]:
    """
    Check recent logs for errors.
    Returns: Health status dict
    """
    logger.info("Checking recent logs for errors...")

    # Check today's KB daily log
    today = datetime.now().strftime('%Y%m%d')
    kb_daily_log = log_dir / f"kb_daily_{today}.log"

    error_count = 0
    critical_count = 0

    if kb_daily_log.exists():
        try:
            with open(kb_daily_log, 'r') as f:
                for line in f:
                    if '[ERROR]' in line:
                        error_count += 1
                    if '[CRITICAL]' in line:
                        critical_count += 1
        except Exception as e:
            logger.error(f"Failed to read log file: {e}")

    if critical_count > 0:
        return {
            "status": "critical",
            "message": f"{critical_count} critical errors in today's logs",
            "error_count": error_count,
            "critical_count": critical_count
        }

    if error_count > MAX_ERRORS_IN_LOG:
        return {
            "status": "warning",
            "message": f"{error_count} errors in today's logs (threshold: {MAX_ERRORS_IN_LOG})",
            "error_count": error_count
        }

    return {
        "status": "healthy",
        "message": f"{error_count} errors (acceptable)",
        "error_count": error_count
    }


def check_scheduled_tasks() -> Dict[str, Any]:
    """
    Check if scheduled tasks are registered (Windows Task Scheduler).
    Returns: Health status dict
    """
    logger.info("Checking scheduled tasks...")

    try:
        import subprocess

        # Check if AgentFactory_KB_Daily task exists
        result = subprocess.run(
            ['schtasks', '/query', '/tn', 'AgentFactory_KB_Daily'],
            capture_output=True,
            text=True,
            timeout=10
        )

        task_exists = result.returncode == 0

        if not task_exists:
            return {
                "status": "warning",
                "message": "Scheduled task 'AgentFactory_KB_Daily' not found"
            }

        return {
            "status": "healthy",
            "message": "Scheduled tasks registered"
        }

    except Exception as e:
        logger.error(f"Failed to check scheduled tasks: {e}")
        return {
            "status": "error",
            "message": f"Check failed: {str(e)}"
        }


def check_disk_space() -> Dict[str, Any]:
    """
    Check available disk space for data storage.
    Returns: Health status dict
    """
    logger.info("Checking disk space...")

    try:
        import shutil

        total, used, free = shutil.disk_usage(Path.cwd())

        free_gb = free // (2**30)  # Convert to GB

        if free_gb < 1:
            return {
                "status": "critical",
                "message": f"Low disk space: {free_gb}GB free",
                "free_gb": free_gb
            }

        if free_gb < 5:
            return {
                "status": "warning",
                "message": f"Disk space getting low: {free_gb}GB free",
                "free_gb": free_gb
            }

        return {
            "status": "healthy",
            "message": f"{free_gb}GB free",
            "free_gb": free_gb
        }

    except Exception as e:
        logger.error(f"Failed to check disk space: {e}")
        return {
            "status": "error",
            "message": f"Check failed: {str(e)}"
        }


# ============================================================================
# MAIN HEALTH CHECK
# ============================================================================

def run_health_checks() -> Dict[str, Any]:
    """
    Run all health checks.
    Returns: Overall health status
    """
    logger.info("")
    logger.info("=" * 80)
    logger.info("HEALTH MONITOR - RUNNING CHECKS")
    logger.info("=" * 80)
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")

    health_checks = {
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }

    # Run all checks
    health_checks["checks"]["supabase"] = check_supabase_connection()
    health_checks["checks"]["last_upload"] = check_last_atom_upload()
    health_checks["checks"]["logs"] = check_recent_logs()
    health_checks["checks"]["tasks"] = check_scheduled_tasks()
    health_checks["checks"]["disk"] = check_disk_space()

    # Determine overall status
    critical_count = sum(1 for check in health_checks["checks"].values() if check["status"] == "critical")
    warning_count = sum(1 for check in health_checks["checks"].values() if check["status"] == "warning")
    error_count = sum(1 for check in health_checks["checks"].values() if check["status"] == "error")

    if critical_count > 0:
        health_checks["overall_status"] = "critical"
        health_checks["summary"] = f"{critical_count} critical issues detected"
    elif error_count > 0:
        health_checks["overall_status"] = "error"
        health_checks["summary"] = f"{error_count} errors detected"
    elif warning_count > 0:
        health_checks["overall_status"] = "warning"
        health_checks["summary"] = f"{warning_count} warnings detected"
    else:
        health_checks["overall_status"] = "healthy"
        health_checks["summary"] = "All systems operational"

    # Log results
    for check_name, check_result in health_checks["checks"].items():
        status_icon = {
            "healthy": "✅",
            "warning": "⚠️",
            "error": "❌",
            "critical": "🔴"
        }.get(check_result["status"], "❓")

        logger.info(f"{status_icon} {check_name}: {check_result['message']}")

    logger.info("")
    logger.info(f"Overall Status: {health_checks['overall_status'].upper()} - {health_checks['summary']}")
    logger.info("")

    # Save health check results
    health_dir = Path("data/health")
    health_dir.mkdir(parents=True, exist_ok=True)

    health_file = health_dir / "latest.json"
    health_file.write_text(json.dumps(health_checks, indent=2))

    # Send alerts for critical issues
    if health_checks["overall_status"] == "critical":
        alert_message = f"**Critical Issues Detected:**\n\n"
        for check_name, check_result in health_checks["checks"].items():
            if check_result["status"] == "critical":
                alert_message += f"• {check_name}: {check_result['message']}\n"

        send_telegram_alert(alert_message)

    return health_checks


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main health monitor"""
    try:
        health_checks = run_health_checks()

        # Exit with error code if critical issues
        if health_checks["overall_status"] == "critical":
            return 1

        return 0

    except Exception as e:
        logger.error(f"Health monitor failed: {e}", exc_info=True)
        send_telegram_alert(f"Health monitor crashed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
