#!/usr/bin/env python3
"""
Deploy store-count-scraper to Render as a cron job
"""

import requests
import json
import sys
import os

# Add render-tools to path to import creds
sys.path.insert(0, os.path.expanduser('~/repos/deployment-tools/render-tools'))
from creds import get_secret

API = "https://api.render.com/v1"
RENDER_API_KEY = get_secret("RENDER_API_KEY")

if not RENDER_API_KEY:
    print("Error: RENDER_API_KEY not found")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json",
}

# Create the cron job service
payload = {
    "type": "cron_job",
    "name": "store-count-scraper",
    "ownerId": "tea-d3vjeseuk2gs73el0lvg",
    "environmentId": "evm-d4eugcemcj7s73cu99eg",
    "serviceDetails": {
        "plan": "starter",
        "region": "frankfurt",
        "schedule": "0 9 * * *",  # 9 AM UTC daily
        "env": "python",
        "envSpecificDetails": {
            "pythonVersion": "3.11",
            "buildCommand": "pip install -r requirements.txt",
            "startCommand": "python scraper.py"
        }
    },
    "branch": "main",
    "repo": "https://github.com/tn-afk/store-count-scraper"
}

print("Creating Render cron job service...")
print(json.dumps(payload, indent=2))

response = requests.post(f"{API}/services", headers=HEADERS, json=payload)

if response.status_code in [200, 201]:
    service = response.json()
    print("\n✓ Service created successfully!")
    print(f"Service ID: {service.get('id')}")
    print(f"Name: {service.get('name')}")
    print(f"Dashboard: https://dashboard.render.com/cron/{service.get('id')}")
    print("\n⚠ Important: Set these environment variables in the Render dashboard:")
    print("  - GOOGLE_SPREADSHEET_ID")
    print("  - GOOGLE_SERVICE_ACCOUNT_JSON")
else:
    print(f"\n✗ Error creating service: {response.status_code}")
    print(response.text)
    sys.exit(1)
