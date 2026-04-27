#!/usr/bin/env python3
"""
Scrape Warby Parker total store count and append to Google Sheet daily.
Sheet format: Date | US Stores | Canada Stores | Total
"""

import json
import os
import re
import requests
from datetime import datetime, timezone

DIRECTORY_URL = "https://stores.warbyparker.com/"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
)


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
        if creds.refresh_token:
            creds.refresh(Request())
        return creds

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


def _extract_initial_data(html):
    """Pull the JSON literal assigned to window.__INITIAL__DATA__ from the page."""
    marker = "window.__INITIAL__DATA__ = "
    start = html.find(marker)
    if start == -1:
        raise RuntimeError("INITIAL_DATA marker not found on page")
    start += len(marker)
    depth = 0
    in_str = False
    esc = False
    for i, ch in enumerate(html[start:], start=start):
        if esc:
            esc = False
            continue
        if ch == '\\' and in_str:
            esc = True
            continue
        if ch == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return json.loads(html[start:i + 1])
    raise RuntimeError("Could not parse INITIAL_DATA JSON")


def _collect_leaf_slugs(node, out):
    if not isinstance(node, dict):
        return
    kids = node.get('dm_directoryChildren')
    if kids:
        for c in kids:
            _collect_leaf_slugs(c, out)
        return
    slug = node.get('slug')
    if slug:
        out.append(slug)


def scrape_counts():
    """Return (us_count, canada_count, total)."""
    resp = requests.get(DIRECTORY_URL, headers={"User-Agent": USER_AGENT}, timeout=30)
    resp.raise_for_status()
    data = _extract_initial_data(resp.text)
    countries = data['document'].get('dm_directoryChildren', [])
    counts = {}
    for country in countries:
        name = country.get('c_addressCountryDisplayName') or country.get('name') or 'Unknown'
        slugs = []
        _collect_leaf_slugs(country, slugs)
        counts[name] = len(set(slugs))

    us = counts.get('United States', 0)
    canada = counts.get('Canada', 0)
    total = sum(counts.values())
    return us, canada, total, counts


def append_to_sheet(spreadsheet_id, row):
    creds = get_google_credentials()
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json",
    }
    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}"
        f"/values/Sheet1!A:D:append?valueInputOption=USER_ENTERED"
    )
    body = {"values": [row]}
    resp = requests.post(url, headers=headers, json=body)
    if resp.status_code == 200:
        print(f"Appended: {row}")
    else:
        raise RuntimeError(f"Sheets append failed {resp.status_code}: {resp.text}")


def main():
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    print(f"Warby Parker Store Count Scraper - {today}")

    us, canada, total, all_counts = scrape_counts()
    print(f"Per-country counts: {all_counts}")
    print(f"US: {us} | Canada: {canada} | Total: {total}")

    spreadsheet_id = os.getenv('WP_SPREADSHEET_ID')
    if not spreadsheet_id:
        print("WP_SPREADSHEET_ID not set; skipping sheet append")
        return

    append_to_sheet(spreadsheet_id, [today, us, canada, total])


if __name__ == "__main__":
    main()
