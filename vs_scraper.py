#!/usr/bin/env python3
"""
Scrape Victoria's Secret store counts by state and append to Google Sheet daily.
"""

import requests
import re
import os
import time
from datetime import datetime, timezone

STATES = {
    "Alabama": "al", "Alaska": "ak", "Arizona": "az", "Arkansas": "ar",
    "California": "ca", "Colorado": "co", "Connecticut": "ct", "Delaware": "de",
    "District of Columbia": "dc", "Florida": "fl", "Georgia": "ga", "Hawaii": "hi",
    "Idaho": "id", "Illinois": "il", "Indiana": "in", "Iowa": "ia",
    "Kansas": "ks", "Kentucky": "ky", "Louisiana": "la", "Maine": "me",
    "Maryland": "md", "Massachusetts": "ma", "Michigan": "mi", "Minnesota": "mn",
    "Mississippi": "ms", "Missouri": "mo", "Montana": "mt", "Nebraska": "ne",
    "Nevada": "nv", "New Hampshire": "nh", "New Jersey": "nj", "New Mexico": "nm",
    "New York": "ny", "North Carolina": "nc", "North Dakota": "nd", "Ohio": "oh",
    "Oklahoma": "ok", "Oregon": "or", "Pennsylvania": "pa", "Puerto Rico": "pr",
    "Rhode Island": "ri", "South Carolina": "sc", "South Dakota": "sd",
    "Tennessee": "tn", "Texas": "tx", "Utah": "ut", "Vermont": "vt",
    "Virginia": "va", "Washington": "wa", "West Virginia": "wv",
    "Wisconsin": "wi", "Wyoming": "wy",
}

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
            'token_uri': os.getenv('GOOGLE_TOKEN_URI', 'https://oauth2.googleapis.com/token'),
            'scopes': ['https://www.googleapis.com/auth/spreadsheets']
        }
        creds = Credentials.from_authorized_user_info(token_data)
        if creds.expired and creds.refresh_token:
            print("Refreshing credentials...")
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
            return None
    except Exception as e:
        print(f"  Error scraping {state_code}: {e}")
        return None


def scrape_all_states():
    """Scrape all states and return dict of {state_name: count}."""
    results = {}
    for state_name, state_code in sorted(STATES.items()):
        count = scrape_state(state_code)
        results[state_name] = count
        status = count if count is not None else "FAILED"
        print(f"  {state_name}: {status}")
        time.sleep(0.5)  # be polite
    return results


def append_to_sheet(spreadsheet_id, results, today):
    """Append today's data to the Google Sheet."""
    creds = get_google_credentials()
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json"
    }

    # Build rows: one per state + total row
    rows = []
    total = 0
    for state_name in sorted(results.keys()):
        count = results[state_name]
        if count is not None:
            total += count
        rows.append([state_name, count if count is not None else "ERROR", today])

    rows.append(["", "", ""])
    rows.append(["TOTAL", total, today])

    # Clear existing data and write fresh (since we want a snapshot, not append)
    range_name = "Store Counts!A1:C55"
    header = [["State", "Store Count", "Date"]]
    all_rows = header + rows

    update_url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}"
        f"/values/{range_name}?valueInputOption=USER_ENTERED"
    )
    body = {"range": range_name, "majorDimension": "ROWS", "values": all_rows}
    resp = requests.put(update_url, headers=headers, json=body)

    if resp.status_code == 200:
        print(f"✓ Sheet updated: {resp.json().get('updatedCells')} cells")
    else:
        print(f"✗ Error updating sheet: {resp.text}")
        return False

    # Also append a daily summary row to "Daily Summary" sheet
    _ensure_daily_summary_sheet(spreadsheet_id, headers)
    summary_range = "Daily Summary!A:C"
    append_url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}"
        f"/values/{summary_range}:append?valueInputOption=USER_ENTERED"
    )
    summary_body = {"values": [[today, total, len([v for v in results.values() if v is not None])]]}
    resp = requests.post(append_url, headers=headers, json=summary_body)
    if resp.status_code == 200:
        print(f"✓ Daily summary appended")
    else:
        print(f"  Warning: Could not append daily summary: {resp.text}")

    return True


def _ensure_daily_summary_sheet(spreadsheet_id, headers):
    """Create 'Daily Summary' sheet if it doesn't exist, with headers."""
    # Check if sheet exists
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}"
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        return

    sheets = [s['properties']['title'] for s in resp.json().get('sheets', [])]
    if 'Daily Summary' in sheets:
        return

    # Add sheet
    add_url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}:batchUpdate"
    body = {
        "requests": [{
            "addSheet": {
                "properties": {"title": "Daily Summary"}
            }
        }]
    }
    resp = requests.post(add_url, headers=headers, json=body)
    if resp.status_code == 200:
        # Add headers
        header_url = (
            f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}"
            f"/values/Daily Summary!A1:C1?valueInputOption=USER_ENTERED"
        )
        requests.put(header_url, headers=headers, json={
            "values": [["Date", "Total Stores", "States Counted"]]
        })
        print("  Created 'Daily Summary' sheet")


def main():
    print(f"=== Victoria's Secret Store Count Scraper - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")

    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

    print("Scraping store counts by state...")
    results = scrape_all_states()

    total = sum(v for v in results.values() if v is not None)
    failed = sum(1 for v in results.values() if v is None)
    print(f"\nTotal stores: {total}")
    if failed:
        print(f"Failed states: {failed}")

    spreadsheet_id = os.getenv('VS_SPREADSHEET_ID')
    if not spreadsheet_id:
        print("\n✗ VS_SPREADSHEET_ID not set")
        return

    print(f"\nUpdating Google Sheet...")
    append_to_sheet(spreadsheet_id, results, today)
    print(f"\n✓ Done! View at: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")


if __name__ == "__main__":
    main()
