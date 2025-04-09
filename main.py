import os
import logging
import platform
import time

# Configure logging based on environment
log_level = os.environ.get('LOG_LEVEL', 'DEBUG')
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# First log entry - helps with debugging startup issues
logger = logging.getLogger(__name__)
logger.info(f"Starting Yahoo Finance Scraper application (Python {platform.python_version()})")

# Set environment variables to control behavior on Render.com
if os.environ.get('RENDER') == 'true' or os.environ.get('RENDER_SERVICE_ID'):
    logger.info("Detected Render.com environment, optimizing settings")
    # Force use of the yfinance API on Render.com instead of web scraping
    os.environ['PREFER_API_OVER_SCRAPING'] = 'true'
    os.environ['FLASK_ENV'] = 'production'  # Ensure production settings on Render

# Log timestamp info for detecting timezone/date-time issues
timestamp_now = int(time.time())
logger.info(f"Current timestamp: {timestamp_now}")
logger.info(f"Current date: {time.strftime('%Y-%m-%d', time.localtime())}")

# Import app after setting environment variables
from app import app

# Set debug mode based on environment
debug_mode = os.environ.get('FLASK_ENV', 'development') != 'production'

if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))
    
    # Start the app with enhanced error handling
    try:
        logger.info(f"Starting server on port {port}")
        app.run(host="0.0.0.0", port=port, debug=debug_mode)
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
