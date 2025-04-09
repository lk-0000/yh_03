"""
Alternative API for Yahoo Finance data when web scraping is blocked.
This file provides a fallback method for retrieving stock data.
"""

import yfinance as yf
import pandas as pd
import logging

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
        
        # Add retry mechanism for yfinance
        max_retries = 3
        retry_delay = 2  # seconds
        data = None
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Get data from yfinance with progress False to avoid stdout noise
                data = yf.download(ticker, start=start_date, end=end_date, progress=False)
                
                if not data.empty:
                    break
                    
                logger.warning(f"Attempt {attempt+1}/{max_retries}: Empty data for {ticker}, retrying...")
                
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