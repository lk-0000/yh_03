# Yahoo Finance Stock Data Scraper

A web application that allows you to retrieve and visualize historical stock data from Yahoo Finance.

## Features

- Search for any stock ticker symbol
- Select custom date ranges
- View data in interactive chart or table format
- Download data as Excel files
- Automatic fallback to API when scraping is blocked

## Deployment Instructions

### Option 1: Deploy on Render.com (Recommended)

1. Fork or upload this repo to your GitHub account
2. Create a new Web Service on Render.com
3. Connect your GitHub repo
4. Use the following settings:
   - **Build Command**: `pip install -r render-requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT --reuse-port main:app`
5. Add the following environment variables:
   - `SESSION_SECRET` (generate a random string)
   - `FLASK_ENV`: production
   - `CACHE_TYPE`: SimpleCache
   - `CACHE_DEFAULT_TIMEOUT`: 1800
   - `LOG_LEVEL`: INFO

## Running Locally

1. Install dependencies:
   ```
   pip install -r render-requirements.txt
   ```

2. Run the application:
   ```
   python main.py
   ```

3. Open http://localhost:5000 in your browser

## Troubleshooting

If you're having issues retrieving data on Render.com:

1. The free tier "spins down" after 15 minutes of inactivity, causing initial slowness
2. Verify you're using the correct ticker symbol (e.g., "MSFT" for Microsoft)
3. Try limiting your date range to less than 2 years
4. Check the Render.com logs for specific error messages