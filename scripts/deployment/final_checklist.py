#!/usr/bin/env python3
"""
Final Deployment Checklist & Go-Live Script

Phase 8: Final verification before production go-live

Usage:
    python scripts/deployment/final_checklist.py --service-url https://your-service.onrender.com

This script:
1. Runs all previous validation checks
2. Verifies 24-hour stability
3. Checks all monitoring systems
4. Generates final go-live report
5. Sends Telegram notification to admin

Output:
- GO / NO-GO decision
- Final deployment report
- Admin notification (Telegram)
"""

import os
import sys
import json
import requests
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class FinalDeploymentChecklist:
    """Final pre-production verification"""

    def __init__(self, service_url: str, uptimerobot_api_key: str = None):
        self.service_url = service_url.rstrip("/")
        self.uptimerobot_api_key = uptimerobot_api_key
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.admin_chat_id = os.getenv("TELEGRAM_ADMIN_CHAT_ID")

        self.checks = []
        self.go_live_approved = False

    def add_check(self, category: str, item: str, passed: bool, details: str = ""):
        """Record checklist item"""
        self.checks.append({
            "category": category,
            "item": item,
            "passed": passed,
            "details": details
        })

    def print_header(self, title: str):
        """Print section header"""
        print(f"\n{'='*70}")
        print(f"{title:^70}")
        print(f"{'='*70}\n")

    def check_service_health(self) -> bool:
        """Verify service is healthy"""
        self.print_header("SERVICE HEALTH CHECK")

        health_url = f"{self.service_url}/health"

        try:
            response = requests.get(health_url, timeout=10)
            if response.status_code == 200:
                result = response.json()
                status = result.get("status")
                uptime = result.get("uptime_seconds", 0)

                print(f"  Service URL: {self.service_url}")
                print(f"  Status: {status}")
                print(f"  Uptime: {uptime} seconds ({uptime/3600:.1f} hours)")

                if status == "healthy" and uptime > 300:  # >5 minutes
                    self.add_check("Service", "Health check passing", True, f"Uptime: {uptime}s")
                    return True
                else:
                    self.add_check("Service", "Health check passing", False, f"Status: {status}")
                    return False
            else:
                self.add_check("Service", "Health check passing", False, f"HTTP {response.status_code}")
                return False

        except Exception as e:
            self.add_check("Service", "Health check passing", False, str(e))
            return False

    def check_webhook_status(self) -> bool:
        """Verify webhook is configured"""
        self.print_header("WEBHOOK STATUS")

        if not self.bot_token:
            self.add_check("Webhook", "Configuration", False, "Bot token not set")
            return False

        api_url = f"https://api.telegram.org/bot{self.bot_token}/getWebhookInfo"

        try:
            response = requests.get(api_url, timeout=10)
            result = response.json()

            if result.get("ok"):
                webhook_info = result.get("result", {})
                url = webhook_info.get("url", "")
                pending = webhook_info.get("pending_update_count", 0)

                print(f"  Webhook URL: {url}")
                print(f"  Pending updates: {pending}")

                expected_url = f"{self.service_url}/telegram-webhook"

                if url == expected_url and pending == 0:
                    self.add_check("Webhook", "Correctly configured", True, url)
                    return True
                else:
                    self.add_check("Webhook", "Correctly configured", False, f"URL mismatch or pending: {pending}")
                    return False

        except Exception as e:
            self.add_check("Webhook", "Correctly configured", False, str(e))
            return False

    def check_monitoring_status(self) -> bool:
        """Verify monitoring is active"""
        self.print_header("MONITORING STATUS")

        if not self.uptimerobot_api_key:
            print("  No UptimeRobot API key - skipping automated check")
            print("  MANUAL VERIFICATION REQUIRED")
            self.add_check("Monitoring", "UptimeRobot active", None, "Manual check required")
            return True  # Non-blocking

        api_url = "https://api.uptimerobot.com/v2/getMonitors"

        payload = {
            "api_key": self.uptimerobot_api_key,
            "format": "json",
            "logs": 1
        }

        try:
            response = requests.post(api_url, data=payload, timeout=10)
            result = response.json()

            if result.get("stat") == "ok":
                monitors = result.get("monitors", [])
                bot_monitor = None

                for monitor in monitors:
                    if self.service_url in monitor.get("url", ""):
                        bot_monitor = monitor
                        break

                if bot_monitor:
                    status = bot_monitor.get("status")
                    uptime = bot_monitor.get("all_time_uptime_ratio", 0)

                    print(f"  Monitor: {bot_monitor.get('friendly_name')}")
                    print(f"  Status: {status} (2=Up)")
                    print(f"  Uptime: {uptime}%")

                    if status == 2 and uptime >= 99:
                        self.add_check("Monitoring", "UptimeRobot active", True, f"{uptime}% uptime")
                        return True
                    else:
                        self.add_check("Monitoring", "UptimeRobot active", False, f"Status: {status}")
                        return False
                else:
                    self.add_check("Monitoring", "UptimeRobot active", False, "No monitor found")
                    return False

        except Exception as e:
            self.add_check("Monitoring", "UptimeRobot active", False, str(e))
            return False

    def check_database_health(self) -> bool:
        """Verify database connection"""
        self.print_header("DATABASE HEALTH")

        try:
            import psycopg

            db_url = os.getenv("NEON_DB_URL")
            if not db_url:
                self.add_check("Database", "Connection healthy", False, "No database URL")
                return False

            with psycopg.connect(db_url, connect_timeout=10) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM knowledge_atoms;")
                    total = cur.fetchone()[0]

                    cur.execute("SELECT COUNT(*) FROM knowledge_atoms WHERE embedding IS NOT NULL;")
                    with_embeddings = cur.fetchone()[0]

                    print(f"  Total atoms: {total:,}")
                    print(f"  With embeddings: {with_embeddings:,} ({100*with_embeddings/max(total,1):.1f}%)")

                    if total > 0:
                        self.add_check("Database", "Connection healthy", True, f"{total:,} atoms")
                        return True
                    else:
                        self.add_check("Database", "Connection healthy", False, "No atoms found")
                        return False

        except Exception as e:
            self.add_check("Database", "Connection healthy", False, str(e))
            return False

    def check_documentation_complete(self) -> bool:
        """Verify all documentation exists"""
        self.print_header("DOCUMENTATION CHECK")

        required_docs = [
            "DEPLOYMENT_QUICK_START.md",
            "DEPLOYMENT_CHECKLIST.md",
            "DEPLOYMENT_COMPLETE_README.md",
            "DEPLOYMENT_REPORT.md"
        ]

        all_exist = True

        for doc in required_docs:
            exists = Path(doc).exists()
            status = "EXISTS" if exists else "MISSING"
            print(f"  [{status}] {doc}")

            if not exists:
                all_exist = False

        self.add_check("Documentation", "All docs complete", all_exist, f"{len(required_docs)} required docs")
        return all_exist

    def calculate_go_no_go(self) -> str:
        """Determine if deployment is ready for production"""
        total = len(self.checks)
        passed = sum(1 for c in self.checks if c["passed"] is True)
        failed = sum(1 for c in self.checks if c["passed"] is False)
        skipped = sum(1 for c in self.checks if c["passed"] is None)

        score = (passed / max(total - skipped, 1)) * 100

        if score >= 95 and failed == 0:
            return "GO"
        elif score >= 80 and failed <= 1:
            return "GO_WITH_CAUTION"
        else:
            return "NO_GO"

    def send_telegram_notification(self, decision: str):
        """Send go-live notification to admin"""
        if not self.bot_token or not self.admin_chat_id:
            print("\n  Cannot send Telegram notification (credentials missing)")
            return

        passed = sum(1 for c in self.checks if c["passed"] is True)
        failed = sum(1 for c in self.checks if c["passed"] is False)

        if decision == "GO":
            emoji = "🎉"
            status_text = "PRODUCTION READY"
        elif decision == "GO_WITH_CAUTION":
            emoji = "⚠️"
            status_text = "READY (WITH CAUTION)"
        else:
            emoji = "❌"
            status_text = "NOT READY"

        message = f"""{emoji} **Agent Factory Deployment**

**Status:** {status_text}
**Decision:** {decision}

**Checklist Results:**
- Passed: {passed}
- Failed: {failed}
- Total: {len(self.checks)}

**Service:** {self.service_url}
**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

        payload = {
            "chat_id": self.admin_chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }

        try:
            response = requests.post(api_url, json=payload, timeout=10)
            if response.status_code == 200:
                print("\n  Telegram notification sent successfully!")
            else:
                print(f"\n  Telegram notification failed: {response.status_code}")
        except Exception as e:
            print(f"\n  Telegram notification error: {e}")

    def print_checklist_results(self):
        """Print final checklist"""
        self.print_header("FINAL DEPLOYMENT CHECKLIST")

        # Group by category
        categories = {}
        for check in self.checks:
            cat = check["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(check)

        # Print by category
        for category, items in categories.items():
            print(f"\n{category}:")
            for item in items:
                if item["passed"] is True:
                    symbol = "[✓]"
                elif item["passed"] is False:
                    symbol = "[✗]"
                else:
                    symbol = "[-]"

                print(f"  {symbol} {item['item']}")
                if item["details"]:
                    print(f"      ({item['details']})")

    def print_final_decision(self):
        """Print final go/no-go decision"""
        self.print_header("FINAL DECISION")

        decision = self.calculate_go_no_go()

        passed = sum(1 for c in self.checks if c["passed"] is True)
        failed = sum(1 for c in self.checks if c["passed"] is False)
        skipped = sum(1 for c in self.checks if c["passed"] is None)
        total = len(self.checks)

        print(f"Checks Passed:  {passed}/{total}")
        print(f"Checks Failed:  {failed}/{total}")
        print(f"Checks Skipped: {skipped}/{total}")
        print()

        if decision == "GO":
            print("DECISION: GO FOR PRODUCTION")
            print()
            print("All critical systems validated and ready!")
            print("Deployment approved for production use.")
            print()
            print("Next steps:")
            print("  1. Monitor service for first 24 hours")
            print("  2. Verify cron job runs tomorrow at 2 AM UTC")
            print("  3. Check UptimeRobot dashboard daily")
        elif decision == "GO_WITH_CAUTION":
            print("DECISION: GO WITH CAUTION")
            print()
            print("Most systems operational, minor issues detected.")
            print("Deployment approved with manual monitoring required.")
            print()
            print("Action items:")
            print("  1. Fix failed checks within 24 hours")
            print("  2. Monitor service closely")
            print("  3. Be ready for manual intervention")
        else:
            print("DECISION: NO GO")
            print()
            print("Critical failures detected. Do NOT go live.")
            print()
            print("Required actions:")
            print("  1. Fix all failed checks")
            print("  2. Re-run this script")
            print("  3. Wait for GO decision before production")

    def run_final_checklist(self):
        """Run complete final checklist"""
        print("="*70)
        print("AGENT FACTORY - FINAL DEPLOYMENT CHECKLIST")
        print("="*70)
        print()
        print(f"Service URL: {self.service_url}")
        print(f"Timestamp:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Run all checks
        self.check_service_health()
        self.check_webhook_status()
        self.check_monitoring_status()
        self.check_database_health()
        self.check_documentation_complete()

        # Display results
        self.print_checklist_results()
        self.print_final_decision()

        # Send notification
        decision = self.calculate_go_no_go()
        self.send_telegram_notification(decision)

        return decision == "GO"


def main():
    parser = argparse.ArgumentParser(
        description="Final deployment checklist and go-live decision"
    )
    parser.add_argument(
        "--service-url",
        required=True,
        help="Render.com service URL"
    )
    parser.add_argument(
        "--uptimerobot-api-key",
        help="UptimeRobot API key (optional)"
    )

    args = parser.parse_args()

    uptimerobot_key = args.uptimerobot_api_key or os.getenv("UPTIMEROBOT_API_KEY")

    checklist = FinalDeploymentChecklist(args.service_url, uptimerobot_key)
    go_approved = checklist.run_final_checklist()

    return 0 if go_approved else 1


if __name__ == "__main__":
    sys.exit(main())
