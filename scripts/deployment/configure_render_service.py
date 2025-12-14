#!/usr/bin/env python3
"""
Render.com Service Configuration via API

Automatically configures environment variables for a Render service using the Render API.

Usage:
    python scripts/deployment/configure_render_service.py --api-key YOUR_API_KEY --service-id YOUR_SERVICE_ID

Required:
    --api-key: Render API key (from Account Settings → API Keys)
    --service-id: Service ID (from dashboard URL: srv-xxxxx)

Optional:
    --env-file: Path to .env file (default: .env)
    --dry-run: Show what would be configured without making changes

This script:
1. Reads all environment variables from .env file
2. Uses Render API to configure the service
3. Triggers a new deployment
4. Validates the configuration

Get your API key:
    1. Go to: https://dashboard.render.com/account/settings
    2. Scroll to "API Keys"
    3. Click "Create API Key"
    4. Copy the key (shown only once!)

Get your service ID:
    1. Go to your Render dashboard
    2. Click on your service
    3. Look at the URL: https://dashboard.render.com/web/srv-XXXXX
    4. The part after "srv-" is your service ID
"""

import os
import sys
import json
import argparse
import requests
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, List, Optional


class RenderServiceConfigurator:
    """Configure Render.com service via API"""

    def __init__(self, api_key: str, service_id: str):
        self.api_key = api_key
        self.service_id = service_id
        self.base_url = "https://api.render.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def get_service_info(self) -> Optional[Dict]:
        """Get current service information"""
        url = f"{self.base_url}/services/{self.service_id}"

        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                print("ERROR: Invalid API key or unauthorized")
            elif e.response.status_code == 404:
                print(f"ERROR: Service {self.service_id} not found")
            else:
                print(f"ERROR: HTTP {e.response.status_code}: {e}")
            return None
        except Exception as e:
            print(f"ERROR: Failed to get service info: {e}")
            return None

    def get_current_env_vars(self) -> Optional[List[Dict]]:
        """Get current environment variables"""
        url = f"{self.base_url}/services/{self.service_id}/env-vars"

        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"ERROR: Failed to get environment variables: {e}")
            return None

    def update_env_vars(self, env_vars: List[Dict]) -> bool:
        """
        Update environment variables for service

        Args:
            env_vars: List of env var dicts with 'key' and 'value'

        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/services/{self.service_id}/env-vars"

        payload = env_vars

        try:
            response = requests.put(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            print(f"✅ Successfully updated {len(env_vars)} environment variables")
            return True
        except requests.exceptions.HTTPError as e:
            print(f"ERROR: Failed to update env vars: HTTP {e.response.status_code}")
            try:
                error_data = e.response.json()
                print(f"  Details: {error_data}")
            except:
                print(f"  Response: {e.response.text}")
            return False
        except Exception as e:
            print(f"ERROR: Failed to update env vars: {e}")
            return False

    def trigger_deploy(self) -> bool:
        """Trigger a new deployment"""
        url = f"{self.base_url}/services/{self.service_id}/deploys"

        payload = {
            "clearCache": "do_not_clear"
        }

        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            deploy_info = response.json()
            deploy_id = deploy_info.get("id", "unknown")
            print(f"✅ Deployment triggered: {deploy_id}")
            return True
        except Exception as e:
            print(f"ERROR: Failed to trigger deployment: {e}")
            return False


def load_env_vars_from_file(env_file: str = ".env") -> Dict[str, str]:
    """
    Load environment variables from .env file

    Returns:
        Dictionary of env var name -> value
    """
    # Load .env file
    load_dotenv(env_file)

    # Required environment variables for Render deployment
    required_vars = [
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_ADMIN_CHAT_ID",
        "AUTHORIZED_TELEGRAM_USERS",
        "NEON_DB_URL",
        "DATABASE_PROVIDER",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "VOICE_MODE",
        "EDGE_VOICE",
        "DEFAULT_LLM_PROVIDER",
        "DEFAULT_MODEL",
        "PYTHONUNBUFFERED",
        "LOG_LEVEL"
    ]

    # Optional but recommended
    optional_vars = [
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
        "GOOGLE_API_KEY",
        "FIRECRAWL_API_KEY",
        "TAVILY_API_KEY",
        "DATABASE_FAILOVER_ENABLED",
        "DATABASE_FAILOVER_ORDER"
    ]

    env_vars = {}

    # Load required variables
    for var in required_vars:
        value = os.getenv(var)
        if value:
            env_vars[var] = value
        else:
            print(f"WARNING: Required variable {var} not found in {env_file}")

    # Load optional variables
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            env_vars[var] = value

    return env_vars


def format_env_vars_for_render(env_vars: Dict[str, str]) -> List[Dict]:
    """
    Format environment variables for Render API

    Args:
        env_vars: Dictionary of env var name -> value

    Returns:
        List of dicts with 'key' and 'value'
    """
    return [{"key": k, "value": v} for k, v in env_vars.items()]


def main():
    parser = argparse.ArgumentParser(
        description="Configure Render.com service environment variables via API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Configure service with env vars from .env file
  python configure_render_service.py --api-key rnd_xxx --service-id srv-xxx

  # Dry run (show what would be configured)
  python configure_render_service.py --api-key rnd_xxx --service-id srv-xxx --dry-run

  # Use custom .env file
  python configure_render_service.py --api-key rnd_xxx --service-id srv-xxx --env-file .env.production

How to get your credentials:
  API Key: https://dashboard.render.com/account/settings → API Keys → Create API Key
  Service ID: Your service dashboard URL contains it (srv-xxxxx)
        """
    )

    parser.add_argument(
        "--api-key",
        required=True,
        help="Render API key (from Account Settings)"
    )
    parser.add_argument(
        "--service-id",
        required=True,
        help="Render service ID (srv-xxxxx from dashboard URL)"
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Path to .env file (default: .env)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be configured without making changes"
    )
    parser.add_argument(
        "--no-deploy",
        action="store_true",
        help="Update env vars but don't trigger deployment"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("RENDER.COM SERVICE CONFIGURATION")
    print("=" * 70)
    print()

    # Validate inputs
    if not args.api_key.startswith("rnd_"):
        print("WARNING: API key should start with 'rnd_'")
        print("  Make sure you copied the full API key from Render dashboard")
        print()

    if not args.service_id.startswith("srv-"):
        print("WARNING: Service ID should start with 'srv-'")
        print("  Check your service URL: https://dashboard.render.com/web/srv-xxxxx")
        print()

    # Initialize configurator
    configurator = RenderServiceConfigurator(args.api_key, args.service_id)

    # Get service info
    print("[1/5] Fetching service information...")
    service_info = configurator.get_service_info()

    if not service_info:
        print("\nFailed to fetch service info. Please check:")
        print("  1. API key is correct")
        print("  2. Service ID is correct")
        print("  3. You have access to this service")
        return 1

    service_name = service_info.get("name", "Unknown")
    service_type = service_info.get("type", "Unknown")
    print(f"  Service: {service_name}")
    print(f"  Type: {service_type}")
    print(f"  ID: {args.service_id}")
    print()

    # Get current env vars
    print("[2/5] Fetching current environment variables...")
    current_env_vars = configurator.get_current_env_vars()

    if current_env_vars is not None:
        print(f"  Currently configured: {len(current_env_vars)} variables")
        current_keys = [var.get("key") for var in current_env_vars]
        print(f"  Existing keys: {', '.join(current_keys[:5])}{'...' if len(current_keys) > 5 else ''}")
    else:
        print("  Could not fetch current env vars (will proceed anyway)")
        current_keys = []

    print()

    # Load env vars from file
    print(f"[3/5] Loading environment variables from {args.env_file}...")
    env_vars = load_env_vars_from_file(args.env_file)

    if not env_vars:
        print(f"\nERROR: No environment variables loaded from {args.env_file}")
        print("  Check that the file exists and contains valid variables")
        return 1

    print(f"  Loaded: {len(env_vars)} variables")
    print(f"  Keys: {', '.join(list(env_vars.keys())[:5])}{'...' if len(env_vars) > 5 else ''}")
    print()

    # Format for Render API
    render_env_vars = format_env_vars_for_render(env_vars)

    # Check what's new
    new_keys = [var["key"] for var in render_env_vars if var["key"] not in current_keys]
    updated_keys = [var["key"] for var in render_env_vars if var["key"] in current_keys]

    if new_keys:
        print(f"  New variables to add: {len(new_keys)}")
        print(f"    {', '.join(new_keys)}")
    if updated_keys:
        print(f"  Existing variables to update: {len(updated_keys)}")
        print(f"    {', '.join(updated_keys[:5])}{'...' if len(updated_keys) > 5 else ''}")
    print()

    # Dry run check
    if args.dry_run:
        print("[DRY RUN] Would configure the following environment variables:")
        print()
        for var in render_env_vars:
            value_preview = var["value"][:20] + "..." if len(var["value"]) > 20 else var["value"]
            print(f"  {var['key']} = {value_preview}")
        print()
        print("[DRY RUN] No changes made. Remove --dry-run to apply configuration.")
        return 0

    # Update env vars
    print("[4/5] Updating environment variables...")
    success = configurator.update_env_vars(render_env_vars)

    if not success:
        print("\nConfiguration failed. Please check the error message above.")
        return 1

    print()

    # Trigger deployment
    if not args.no_deploy:
        print("[5/5] Triggering deployment...")
        deploy_success = configurator.trigger_deploy()

        if not deploy_success:
            print("\nWARNING: Env vars updated but deployment trigger failed")
            print("  You can manually deploy from the Render dashboard")
            return 1
    else:
        print("[5/5] Skipping deployment (--no-deploy flag set)")
        print("  Don't forget to manually deploy from Render dashboard!")

    print()
    print("=" * 70)
    print("✅ CONFIGURATION COMPLETE")
    print("=" * 70)
    print()
    print("Next steps:")
    print(f"  1. Monitor deployment: https://dashboard.render.com/web/{args.service_id}")
    print(f"  2. Check logs for any errors")
    print(f"  3. Test health endpoint once deployed")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
