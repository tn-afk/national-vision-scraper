#!/usr/bin/env python3
"""
Scrape store counts from Eyeglass World and America's Best
and append to Google Sheet daily
"""

import requests
import json
import os
from datetime import datetime

def get_google_token():
    """Get Google OAuth token from environment"""
    # For Render deployment, we'll use a service account
    # For local testing, fallback to the auth helper
    service_account_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')

    if service_account_json:
        # Use service account for Render
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request

        credentials_dict = json.loads(service_account_json)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        credentials.refresh(Request())
        return credentials.token
    else:
        # Fallback to local auth helper for testing
        import subprocess
        result = subprocess.run(
            ['python3', os.path.expanduser('~/.google_auth_helper.py'), '--get-token'],
            capture_output=True,
            text=True
        )
        return result.stdout.strip().split('\n')[-1]

def get_eyeglass_world_count():
    """Get Eyeglass World store count from their API"""
    try:
        url = "https://eyeglassworld.cname.meetsoci.com/rest/getlist"
        payload = {
            "request": {
                "appkey": "18A65B78-4141-11EE-AE6A-81887089056E",
                "formdata": {
                    "objectname": "Locator",
                    "where": {
                        "eyeglass_world": {
                            "eq": 1
                        }
                    }
                }
            }
        }

        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 1:
                count = data.get('response', {}).get('collectioncount', None)
                if count is not None:
                    return count
                collection = data.get('response', {}).get('collection', [])
                if collection:
                    return len(collection)

        return None
    except Exception as e:
        print(f"Error fetching Eyeglass World data: {e}")
        return None

def get_americas_best_count():
    """Get America's Best store count from their API"""
    try:
        url = "https://americasbest.cname.meetsoci.com/rest/getlist"
        payload = {
            "request": {
                "appkey": "0068BFCA-3EA9-4DC1-A2F0-24378908A3CC",
                "formdata": {
                    "objectname": "Locator",
                    "limit": "2000",
                    "where": {
                        "americas_best": {
                            "eq": 1
                        }
                    }
                }
            }
        }

        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 1:
                count = data.get('response', {}).get('collectioncount', None)
                if count is not None:
                    return count
                collection = data.get('response', {}).get('collection', [])
                if collection:
                    return len(collection)

        return None
    except Exception as e:
        print(f"Error fetching America's Best data: {e}")
        return None

def append_to_google_sheet(spreadsheet_id, data):
    """Append data to existing Google Sheet"""
    token = get_google_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Append the data to the sheet
    range_name = "Store Data!A:C"
    append_url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{range_name}:append?valueInputOption=RAW"

    body = {
        "values": [data]
    }

    response = requests.post(append_url, headers=headers, json=body)

    if response.status_code == 200:
        print(f"✓ Data appended successfully!")
        return True
    else:
        print(f"Error appending to sheet: {response.text}")
        return False

def create_google_sheet_if_needed():
    """Create initial Google Sheet if SPREADSHEET_ID is not set"""
    token = get_google_token()

    create_url = "https://sheets.googleapis.com/v4/spreadsheets"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    spreadsheet_body = {
        "properties": {
            "title": f"Store Counts - {datetime.now().strftime('%Y-%m-%d')}"
        },
        "sheets": [{
            "properties": {
                "title": "Store Data"
            }
        }]
    }

    response = requests.post(create_url, headers=headers, json=spreadsheet_body)

    if response.status_code != 200:
        print(f"Error creating spreadsheet: {response.text}")
        return None

    spreadsheet = response.json()
    spreadsheet_id = spreadsheet['spreadsheetId']
    spreadsheet_url = spreadsheet['spreadsheetUrl']

    # Add header row
    values = [["Date", "Eyeglass World", "America's Best"]]
    range_name = "Store Data!A1:C1"
    update_url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{range_name}?valueInputOption=RAW"

    body = {"values": values}
    requests.put(update_url, headers=headers, json=body)

    print(f"\n✓ New Google Sheet created!")
    print(f"URL: {spreadsheet_url}")
    print(f"Spreadsheet ID: {spreadsheet_id}")
    print(f"\nSet this as environment variable:")
    print(f"GOOGLE_SPREADSHEET_ID={spreadsheet_id}")

    return spreadsheet_id

def main():
    print(f"=== Store Count Scraper - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")

    # Get today's date
    today = datetime.now().strftime('%Y-%m-%d')

    # Get Eyeglass World count
    print("Fetching Eyeglass World store count...")
    eyeglass_count = get_eyeglass_world_count()
    print(f"Eyeglass World stores: {eyeglass_count if eyeglass_count else 'Not found'}")

    # Get America's Best count
    print("\nFetching America's Best store count...")
    americas_best_count = get_americas_best_count()
    print(f"America's Best stores: {americas_best_count if americas_best_count else 'Not found'}")

    # Prepare data row
    data = [today, eyeglass_count or "N/A", americas_best_count or "N/A"]

    # Get spreadsheet ID from environment
    spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')

    if not spreadsheet_id:
        print("\n⚠ GOOGLE_SPREADSHEET_ID not set. Creating new sheet...")
        spreadsheet_id = create_google_sheet_if_needed()
        if not spreadsheet_id:
            print("✗ Failed to create Google Sheet")
            return

    print(f"\nAppending to Google Sheet...")
    success = append_to_google_sheet(spreadsheet_id, data)

    if success:
        print(f"\n✓ Complete!")
        print(f"Date: {today}")
        print(f"Eyeglass World: {eyeglass_count if eyeglass_count else 'N/A'}")
        print(f"America's Best: {americas_best_count if americas_best_count else 'N/A'}")
        sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
        print(f"View at: {sheet_url}")
    else:
        print(f"\n✗ Failed to append data")

if __name__ == "__main__":
    main()
