#!/usr/bin/env python3
"""
Scrape Victoria's Secret total US store count and append to Google Sheet daily.
Sheet format: Column A = Date, Column B = Total Store Count
"""

import requests
import re
import os
import time
from datetime import datetime, timezone

STATE_CODES = [
    "al", "ak", "az", "ar", "ca", "co", "ct", "de", "dc", "fl",
    "ga", "hi", "id", "il", "in", "ia", "ks", "ky", "la", "me",
    "md", "ma", "mi", "mn", "ms", "mo", "mt", "ne", "nv", "nh",
    "nj", "nm", "ny", "nc", "nd", "oh", "ok", "or", "pa", "pr",
    "ri", "sc", "sd", "tn", "tx", "ut", "vt", "va", "wa", "wv",
    "wi", "wy",
]

BASE_URL = "https://stores.victoriassecret.com/us"


def get_google_credentials():
    """Load Google API credentials from environment or local file."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    if all(os.getenv(k) for k in ['GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET', 'GOOGLE_REFRESH_TOKEN']):
        print("Loading credentials from environment variables")
        token_data = {
            'client_id': os.getenv('GOOGLE_CLIENT_ID'),
            'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
            'refresh_token': os.getenv('GOOGLE_REFRESH_TOKEN'),
            'token_uri': 'https://oauth2.googleapis.com/token',
            'scopes': ['https://www.googleapis.com/auth/spreadsheets']
        }
        creds = Credentials.from_authorized_user_info(token_data)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        return creds
    else:
        import subprocess
        result = subprocess.run(
            ['python3', os.path.expanduser('~/.google_auth_helper.py'), '--get-token'],
            capture_output=True, text=True
        )
        token = result.stdout.strip().split('\n')[-1]

        class TokenHolder:
            def __init__(self, token):
                self.token = token
        return TokenHolder(token)


def scrape_state(state_code):
    """Scrape store count for a single state by summing city counts."""
    url = f"{BASE_URL}/{state_code}/"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            counts = re.findall(r'data-hide-one="(\d+)"', resp.text)
            return sum(int(c) for c in counts)
        else:
            print(f"  HTTP {resp.status_code} for {state_code}")
            return 0
    except Exception as e:
        print(f"  Error scraping {state_code}: {e}")
        return 0


def scrape_total():
    """Scrape all states and return total store count."""
    total = 0
    for code in STATE_CODES:
        count = scrape_state(code)
        total += count
        time.sleep(0.5)
    return total


def append_to_sheet(spreadsheet_id, today, total):
    """Append a row [date, total] to the sheet."""
    creds = get_google_credentials()
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json"
    }

    append_url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}"
        f"/values/Sheet1!A:B:append?valueInputOption=USER_ENTERED"
    )
    body = {"values": [[today, total]]}
    resp = requests.post(append_url, headers=headers, json=body)

    if resp.status_code == 200:
        print(f"Appended: {today} | {total}")
    else:
        print(f"Error: {resp.text}")


def main():
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    print(f"VS Store Count Scraper - {today}")

    total = scrape_total()
    print(f"Total stores: {total}")

    spreadsheet_id = os.getenv('VS_SPREADSHEET_ID')
    if not spreadsheet_id:
        print("VS_SPREADSHEET_ID not set")
        return

    append_to_sheet(spreadsheet_id, today, total)


if __name__ == "__main__":
    main()
