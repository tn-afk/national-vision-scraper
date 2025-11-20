# Store Count Scraper

Automated daily scraper that collects store counts from Eyeglass World and America's Best and logs them to a Google Sheet.

## Features

- Scrapes store counts from:
  - Eyeglass World (eyeglassworld.com)
  - America's Best (americasbest.com)
- Appends daily data to Google Sheets
- Runs automatically via Render cron job (daily at 9 AM UTC / 10 AM UK)

## Deployment on Render

This project is configured for automatic deployment on Render as a cron job.

### Prerequisites

1. **Google Service Account** with Google Sheets API access
   - Create a service account in Google Cloud Console
   - Enable Google Sheets API
   - Download the service account JSON key
   - Share your Google Sheet with the service account email

2. **Google Sheet**
   - Create a new Google Sheet or use existing
   - Add header row: `Date | Eyeglass World | America's Best`
   - Share with service account email (viewer/editor permissions)
   - Note the Spreadsheet ID from the URL

### Environment Variables

Set these in Render dashboard:

- `GOOGLE_SPREADSHEET_ID`: Your Google Sheet ID (from the URL)
- `GOOGLE_SERVICE_ACCOUNT_JSON`: Full JSON content of your service account key

### Deployment Steps

1. Push to GitHub:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/store-count-scraper.git
   git push -u origin main
   ```

2. Create Render service:
   - Connect your GitHub repository
   - Render will auto-detect `render.yaml`
   - Set environment variables in dashboard
   - Deploy

3. Monitor:
   - Check Render dashboard for cron job execution
   - View logs for each run
   - Check Google Sheet for new data entries

## Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GOOGLE_SPREADSHEET_ID="your-sheet-id"
export GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'

# Run scraper
python scraper.py
```

## Schedule

Runs daily at 9:00 AM UTC (10:00 AM UK time, 9:00 AM GMT)

## Data Format

| Date       | Eyeglass World | America's Best |
|------------|----------------|----------------|
| 2025-11-20 | 147            | 1058           |
| 2025-11-21 | ...            | ...            |
