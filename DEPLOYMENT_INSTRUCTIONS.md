# Deployment Instructions for Render

## Quick Deploy

Since this is a private GitHub repository, deploy via the Render Dashboard:

### Step 1: Connect to Render

1. Go to https://dashboard.render.com/
2. Click "New +" → "Cron Job"
3. Connect your GitHub account if not already connected
4. Select repository: `tn-afk/store-count-scraper`
5. Render will auto-detect the `render.yaml` configuration

### Step 2: Configure Environment Variables

In the Render dashboard, add these environment variables:

**Required:**
- `GOOGLE_SPREADSHEET_ID` = `13UQ83anQ28YufQvv6BhBPYpmShlf78IF3LgIIb0OYbs` (or your preferred sheet ID)
- `GOOGLE_SERVICE_ACCOUNT_JSON` = Your Google service account JSON (full content)

### Step 3: Google Service Account Setup

If you don't have a service account yet:

1. Go to https://console.cloud.google.com/
2. Create a new project or select existing
3. Enable Google Sheets API
4. Go to "IAM & Admin" → "Service Accounts"
5. Create service account
6. Create a JSON key
7. Copy the entire JSON content to `GOOGLE_SERVICE_ACCOUNT_JSON` env var
8. Share your Google Sheet with the service account email (e.g., `scraper@project.iam.gserviceaccount.com`)

### Step 4: Deploy

Click "Create Cron Job" and Render will:
- Install dependencies from `requirements.txt`
- Run `python scraper.py` daily at 9 AM UTC (10 AM UK time)
- Append new data to your Google Sheet

## Existing Google Sheet

Your existing sheet with the correct data:
https://docs.google.com/spreadsheets/d/13UQ83anQ28YufQvv6BhBPYpmShlf78IF3LgIIb0OYbs

Sheet ID: `13UQ83anQ28YufQvv6BhBPYpmShlf78IF3LgIIb0OYbs`

## Monitoring

- View cron job status: https://dashboard.render.com/
- Check logs for each execution
- Verify data in Google Sheet

## Manual Trigger

To manually trigger the cron job:
1. Go to Render dashboard
2. Find "store-count-scraper" service
3. Click "Trigger Deploy"

## Schedule

Current schedule: `0 9 * * *` (9 AM UTC daily)

To change schedule:
1. Edit `render.yaml`
2. Commit and push to GitHub
3. Render will auto-redeploy
