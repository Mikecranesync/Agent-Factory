#!/usr/bin/env python3
"""
Import n8n workflows via REST API
Imports all 5 RIVET Pro workflows as INACTIVE for review
"""

import json
import os
import requests
from pathlib import Path

# Configuration
N8N_URL = "http://72.60.175.144:5678"
# VPS API key
N8N_API_KEYS = [
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxNzBlNDViYy1iNjFjLTQwOGItYTFmYS00OGQyMTA5Y2FjZWMiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzY3ODk1NjAxLCJleHAiOjE3NzA0NDA0MDB9.h6SfSY_ngmXKpsZjJ8DY6qRJU7Nir_0ovrig383H3a4"  # VPS API key
]

# Workflow files to import (in order)
WORKFLOWS = [
    "rivet_commands.json",
    "rivet_usage_tracker.json",
    "rivet_stripe_checkout.json",
    "rivet_stripe_webhook.json",
    "rivet_chat_with_print.json"
]

def import_workflow(workflow_path):
    """Import a single workflow to n8n as INACTIVE"""

    # Read workflow JSON
    with open(workflow_path, 'r', encoding='utf-8') as f:
        workflow_data = json.load(f)

    # Clean settings object - only include allowed fields
    allowed_settings = ['executionOrder']
    if 'settings' in workflow_data:
        workflow_data['settings'] = {
            k: v for k, v in workflow_data['settings'].items()
            if k in allowed_settings
        }

    # Remove fields that shouldn't be in POST request (n8n API validation)
    workflow_data.pop('id', None)
    workflow_data.pop('active', None)  # Read-only, workflows are inactive by default
    workflow_data.pop('createdAt', None)
    workflow_data.pop('updatedAt', None)
    workflow_data.pop('versionId', None)
    workflow_data.pop('triggerCount', None)
    workflow_data.pop('tags', None)

    # Remove pinData if it exists and is empty
    if 'pinData' in workflow_data and not workflow_data['pinData']:
        workflow_data.pop('pinData')

    # Remove staticData if null
    if workflow_data.get('staticData') is None:
        workflow_data.pop('staticData', None)

    # Try each API key
    last_error = None
    for api_key in N8N_API_KEYS:
        headers = {
            'X-N8N-API-KEY': api_key,
            'Content-Type': 'application/json'
        }

        try:
            response = requests.post(
                f"{N8N_URL}/api/v1/workflows",
                headers=headers,
                json=workflow_data,
                timeout=30
            )

            if response.status_code in [200, 201]:
                result = response.json()
                return {
                    'success': True,
                    'id': result.get('id'),
                    'name': result.get('name'),
                    'active': result.get('active', False),
                    'api_key_used': api_key[:20] + '...'
                }
            else:
                last_error = {
                    'error': response.text,
                    'status_code': response.status_code
                }
        except Exception as e:
            last_error = {
                'error': str(e),
                'status_code': 'exception'
            }

    # If all keys failed, return last error
    return {
        'success': False,
        **last_error
    }

def main():
    """Import all workflows"""

    # Get workflows directory
    script_dir = Path(__file__).parent
    workflows_dir = script_dir.parent / 'n8n' / 'workflows' / 'test'

    print(f">> Importing RIVET Pro workflows to {N8N_URL}")
    print(f">> Source: {workflows_dir}")
    print(f">> All workflows will be imported as INACTIVE\n")

    results = []

    for workflow_file in WORKFLOWS:
        workflow_path = workflows_dir / workflow_file

        if not workflow_path.exists():
            print(f"[ERROR] {workflow_file}: FILE NOT FOUND")
            continue

        print(f">> Importing {workflow_file}...")

        result = import_workflow(workflow_path)
        results.append(result)

        if result['success']:
            print(f"   [OK] Imported as ID: {result['id']}")
            print(f"        Name: {result['name']}")
            print(f"        Active: {result['active']}\n")
        else:
            print(f"   [FAILED] {result.get('error', 'Unknown error')}")
            print(f"            Status Code: {result.get('status_code', 'N/A')}\n")

    # Summary
    print("=" * 60)
    print("IMPORT SUMMARY")
    print("=" * 60)

    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    print(f"\n[OK] Successful: {len(successful)}/{len(results)}")
    if successful:
        for r in successful:
            print(f"     - {r['name']} (ID: {r['id']})")

    if failed:
        print(f"\n[ERROR] Failed: {len(failed)}/{len(results)}")
        for r in failed:
            print(f"        - Error: {r.get('error', 'Unknown')}")

    print("\nNext Steps:")
    print("   1. Open n8n: http://72.60.175.144:5678")
    print("   2. Configure credentials for each workflow")
    print("   3. Test each workflow individually")
    print("   4. Activate workflows in order (see DEPLOYMENT_CHECKLIST.md)")

    return 0 if not failed else 1

if __name__ == '__main__':
    exit(main())
