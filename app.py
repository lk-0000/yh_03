import os
import logging
import uuid
from datetime import datetime, timedelta
from functools import wraps
from urllib.parse import quote

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response, flash
from flask_caching import Cache
import pandas as pd
import io

from yahoo_scraper import scrape_yahoo_finance_history, get_period_timestamps
import traceback

# Import the alternative API module
try:
    # First try to import yfinance to check if it's installed
    import yfinance
    
    # Then try to import our API function
    from alternative_api import get_stock_data_from_api
    ALTERNATIVE_API_AVAILABLE = True
    logging.info("yfinance API support is available and will be used as a fallback")
except ImportError as e:
    ALTERNATIVE_API_AVAILABLE = False
    logging.warning(f"yfinance API is not available: {str(e)}")
    logging.warning("Install yfinance with: pip install yfinance")
    
    # Define an empty function as a placeholder to avoid errors
    def get_stock_data_from_api(ticker, start_date, end_date):
        logging.error("yfinance not installed - cannot use API fallback")
        return None

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Configure for Render.com
if os.environ.get("RENDER") or os.environ.get("PORT"):
    # Trust the Render proxy
    app.config['PREFERRED_URL_SCHEME'] = 'https'
    # Keep the session cookie secure on Render.com
    app.config['SESSION_COOKIE_SECURE'] = True
    # Ensure session cookies survive free tier spin-ups
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    # Increased timeout for Render's free tier spin-ups
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    # Set a flag to prioritize API over scraping when on Render.com
    PREFER_API_OVER_SCRAPING = True
else:
    PREFER_API_OVER_SCRAPING = False

# Configure cache
cache_config = {
    "DEBUG": True,
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 1800  # 30 minutes
}
app.config.from_mapping(cache_config)
cache = Cache(app)

@app.route('/')
def index():
    """Render the main page with the form"""
    # Default date range (30 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Format dates for the template, ensuring we use current year
    current_year = datetime.now().year
    formatted_start = start_date.strftime(f'{current_year}-%m-%d')
    formatted_end = end_date.strftime(f'{current_year}-%m-%d')
    
    logger.debug(f"Index page loaded with default dates: {formatted_start} to {formatted_end}")
    
    return render_template('index.html', 
                           start_date=formatted_start,
                           end_date=formatted_end)

@app.route('/scrape', methods=['POST'])
def scrape():
    """Handle form submission and scrape data"""
    try:
        # Get form data
        ticker = request.form.get('ticker', '').strip().upper()
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
        # Validate inputs
        if not ticker:
            flash("Please enter a ticker symbol", "danger")
            return redirect(url_for('index'))
        
        # Convert dates to timestamps for Yahoo Finance URL
        period1, period2 = get_period_timestamps(start_date, end_date)
        
        # Create Yahoo Finance URL
        url = f"https://finance.yahoo.com/quote/{ticker}/history/?period1={period1}&period2={period2}"
        
        # Check cache first
        cache_key = f"{ticker}_{period1}_{period2}"
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            logger.debug(f"Using cached data for {ticker}")
            df = cached_data
            source = "cache"
        else:
            # On Render.com, use the API first since scraping is often blocked
            if PREFER_API_OVER_SCRAPING and ALTERNATIVE_API_AVAILABLE:
                logger.info(f"On Render.com platform, trying API first for {ticker}")
                df = get_stock_data_from_api(ticker, start_date, end_date)
                source = "api"
                
                # If API fails, then try scraping as a fallback
                if df is None or df.empty:
                    logger.debug(f"API failed, trying to scrape data for {ticker}")
                    df = scrape_yahoo_finance_history(url)
                    source = "scrape"
            else:
                # When not on Render.com, try scraping first
                logger.debug(f"Scraping data for {ticker}")
                df = scrape_yahoo_finance_history(url)
                source = "scrape"
                
                # If scraping fails, try alternative API if available
                if (df is None or df.empty) and ALTERNATIVE_API_AVAILABLE:
                    logger.info(f"Scraping failed, trying alternative API for {ticker}")
                    df = get_stock_data_from_api(ticker, start_date, end_date)
                    source = "api"
            
            # If all methods fail, show error with more helpful message
            if df is None or df.empty:
                logger.error(f"Could not retrieve data for {ticker} using any method")
                flash(f"No data found for {ticker} in the selected date range. Please verify the ticker symbol is correct (e.g., MSFT for Microsoft).", "warning")
                return redirect(url_for('index'))
            
            # Cache the result
            cache.set(cache_key, df)
        
        # Generate a unique ID for this dataset and store in cache
        download_id = str(uuid.uuid4())
        download_cache_key = f"download_{download_id}"
        cache.set(download_cache_key, df, timeout=1800)  # 30 minutes timeout
        
        # Store minimal info in session
        session['download_id'] = download_id
        session['ticker'] = ticker
        
        # Format data for display
        data_for_template = {
            'ticker': ticker,
            'data': df.to_dict('records'),
            'start_date': start_date,
            'end_date': end_date,
            'source': source,
            'download_id': download_id
        }
        
        return render_template('results.html', **data_for_template)
    
    except Exception as e:
        error_msg = f"Error scraping data: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        flash(error_msg, "danger")
        return redirect(url_for('index'))

@app.route('/download')
def download():
    """Download the last scraped data as Excel"""
    if 'download_id' not in session or 'ticker' not in session:
        flash("No data available for download", "warning")
        return redirect(url_for('index'))
    
    try:
        # Retrieve the data from the cache
        download_id = session['download_id']
        download_cache_key = f"download_{download_id}"
        df = cache.get(download_cache_key)
        
        if df is None:
            flash("Data has expired. Please search again.", "warning")
            return redirect(url_for('index'))
            
        ticker = session['ticker']
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name=f"{ticker} History", index=False)
            
            # Configure workbook
            workbook = writer.book
            worksheet = writer.sheets[f"{ticker} History"]
            
            # Format for dates
            date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
            worksheet.set_column('A:A', 12, date_format)
            
            # Format for numbers
            number_format = workbook.add_format({'num_format': '0.00'})
            worksheet.set_column('B:F', 12, number_format)
            
            # Format for volume
            volume_format = workbook.add_format({'num_format': '#,##0'})
            worksheet.set_column('G:G', 15, volume_format)
        
        # Set file for download
        output.seek(0)
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"{ticker}_historical_data_{today}.xlsx"
        
        return Response(
            output.read(),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment;filename={filename}"}
        )
    except Exception as e:
        error_msg = f"Error generating Excel file: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        flash(error_msg, "danger")
        return redirect(url_for('index'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html', error="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"500 error occurred: {str(e)}")
    logger.error(traceback.format_exc())
    return render_template('index.html', error="Internal server error"), 500

# Catch-all route for any undefined URL
@app.route('/<path:undefined_path>')
def catch_all(undefined_path):
    logger.warning(f"Undefined route accessed: /{undefined_path}")
    flash("The page you're looking for doesn't exist. You've been redirected to the home page.", "warning")
    return redirect(url_for('index'))
