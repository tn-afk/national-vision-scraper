# Google Service Account Setup

## Quick Setup Steps

### 1. Create Service Account in Google Cloud Console

1. Go to https://console.cloud.google.com/
2. Select or create a project
3. Enable Google Sheets API:
   - Go to "APIs & Services" → "Library"
   - Search for "Google Sheets API"
   - Click "Enable"

4. Create Service Account:
   - Go to "IAM & Admin" → "Service Accounts"
   - Click "Create Service Account"
   - Name: `store-count-scraper`
   - Click "Create and Continue"
   - Skip granting roles (not needed for Sheets)
   - Click "Done"

5. Create JSON Key:
   - Click on the service account you just created
   - Go to "Keys" tab
   - Click "Add Key" → "Create new key"
   - Select "JSON"
   - Click "Create" - this downloads the JSON file

### 2. Share Google Sheet with Service Account

1. Open the JSON file you downloaded
2. Find the `client_email` field (looks like `store-count-scraper@project.iam.gserviceaccount.com`)
3. Open your Google Sheet: https://docs.google.com/spreadsheets/d/13UQ83anQ28YufQvv6BhBPYpmShlf78IF3LgIIb0OYbs
4. Click "Share"
5. Add the service account email
6. Give it "Editor" permissions
7. Click "Send"

### 3. Set Environment Variable in Render

**Option A: Via Dashboard (Recommended)**
1. Go to https://dashboard.render.com/cron/crn-d4flp2mmcj7s73aqoa9g
2. Click "Environment"
3. Add new environment variable:
   - Key: `GOOGLE_SERVICE_ACCOUNT_JSON`
   - Value: Paste the entire contents of the JSON file
4. Click "Save"
5. The service will automatically redeploy

**Option B: Via CLI**
```bash
# Save your service account JSON to a file
cat > /tmp/service-account.json << 'EOF'
{
  "type": "service_account",
  "project_id": "your-project",
  ...paste full JSON here...
}
EOF

# Set the environment variable
cd ~/repos/deployment-tools/render-tools
export RENDER_SERVICE_ID="crn-d4flp2mmcj7s73aqoa9g"
python3 render_api.py set GOOGLE_SERVICE_ACCOUNT_JSON "$(cat /tmp/service-account.json)"

# Clean up
rm /tmp/service-account.json
```

## Verify Setup

Once configured, the cron job will run daily at 9 AM UTC (10 AM UK time) and append data to your Google Sheet.

### Manual Test Run

To manually trigger the cron job before the scheduled time:
1. Go to https://dashboard.render.com/cron/crn-d4flp2mmcj7s73aqoa9g
2. Click "Manual Deploy" or "Trigger Deploy"
3. Check logs to verify it ran successfully
4. Check your Google Sheet for the new row

## Service Details

- **Service ID**: crn-d4flp2mmcj7s73aqoa9g
- **Dashboard**: https://dashboard.render.com/cron/crn-d4flp2mmcj7s73aqoa9g
- **Schedule**: Daily at 9 AM UTC (10 AM UK time)
- **Google Sheet**: https://docs.google.com/spreadsheets/d/13UQ83anQ28YufQvv6BhBPYpmShlf78IF3LgIIb0OYbs
- **GitHub Repo**: https://github.com/tn-afk/store-count-scraper (private)
