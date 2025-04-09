"""
Alternative API for Yahoo Finance data when web scraping is blocked.
This file provides a fallback method for retrieving stock data.
"""

import yfinance as yf
import pandas as pd
import logging
import datetime
import time

logger = logging.getLogger(__name__)

def get_stock_data_from_api(ticker, start_date, end_date):
    """
    Get stock data from yfinance API as a fallback method
    
    Args:
        ticker (str): Stock ticker symbol (e.g., AAPL)
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        
    Returns:
        DataFrame: Historical stock data or None if error
    """
    try:
        logger.info(f"Fetching data for {ticker} from yfinance API")
        
        # Try to auto-correct common ticker issues
        ticker = ticker.strip().upper()
        
        # Fix date format issues
        try:
            # Check if the date strings appear to be from the future
            current_year = datetime.datetime.now().year
            if int(start_date.split('-')[0]) > current_year or int(end_date.split('-')[0]) > current_year:
                logger.warning(f"API: Future dates detected: start={start_date}, end={end_date}")
                
                # Use the same month/day but change year to current
                parts_start = start_date.split('-')
                parts_end = end_date.split('-')
                
                # Reset to current year
                start_date = f"{current_year}-{parts_start[1]}-{parts_start[2]}"
                end_date = f"{current_year}-{parts_end[1]}-{parts_end[2]}"
                
                logger.info(f"API: Adjusted dates: start={start_date}, end={end_date}")
                
            # Convert to datetime objects to validate
            start_dt = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.datetime.strptime(end_date, '%Y-%m-%d')
            
            # Make sure start is before end
            if start_dt > end_dt:
                logger.warning("API: Start date is after end date, swapping dates")
                start_date, end_date = end_date, start_date
                
            # Make sure date range is not too long (limit to 2 years)
            date_diff = (end_dt - start_dt).days
            if date_diff > 730:  # ~2 years
                logger.warning(f"API: Date range too long ({date_diff} days), limiting to 2 years")
                start_dt = end_dt - datetime.timedelta(days=730)
                start_date = start_dt.strftime('%Y-%m-%d')
                
            logger.info(f"API: Using date range: {start_date} to {end_date}")
            
        except Exception as date_error:
            logger.error(f"API: Date validation error: {str(date_error)}, using default dates")
            end_dt = datetime.datetime.now()
            start_dt = end_dt - datetime.timedelta(days=30)
            start_date = start_dt.strftime('%Y-%m-%d')
            end_date = end_dt.strftime('%Y-%m-%d')
        
        # Add retry mechanism for yfinance
        max_retries = 3
        retry_delay = 2  # seconds
        data = None
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Get data from yfinance with progress False to avoid stdout noise
                logger.info(f"API attempt {attempt+1}: Downloading {ticker} from {start_date} to {end_date}")
                data = yf.download(ticker, start=start_date, end=end_date, progress=False)
                
                if not data.empty:
                    break
                    
                logger.warning(f"API attempt {attempt+1}/{max_retries}: Empty data for {ticker}, retrying...")
                
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
            except Exception as e:
                last_error = e
                logger.warning(f"API error on attempt {attempt+1}/{max_retries}: {str(e)}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2
        
        # Check if all attempts failed
        if data is None or data.empty:
            if last_error:
                logger.error(f"All API requests failed for {ticker}. Last error: {str(last_error)}")
            else:
                logger.error(f"No data returned from yfinance for {ticker}")
            return None
            
        # Reset index to make Date a column
        data = data.reset_index()
        
        # Make column names match our expected format
        data.columns = ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]
        
        # Add debug info about the data we got
        logger.info(f"Successfully retrieved {len(data)} records for {ticker} from {data['Date'].min()} to {data['Date'].max()}")
        
        return data
        
    except Exception as e:
        import traceback
        logger.error(f"Error fetching data from yfinance: {str(e)}")
        logger.error(traceback.format_exc())
        return None