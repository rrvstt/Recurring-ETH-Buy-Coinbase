"""
Daily ETH Buy Script
Places a $10 USDC buy order for ETH at 0.998 of market price (maker fee) daily.
"""

import os
import schedule
import time
from datetime import datetime
from dotenv import load_dotenv
from coinbase_advanced_trader.enhanced_rest_client import EnhancedRESTClient
from coinbase_advanced_trader.logger import logger

# Load environment variables from .env file
load_dotenv()

# API Credentials from environment variables
API_KEY = os.getenv("COINBASE_API_KEY")
API_SECRET = os.getenv("COINBASE_API_SECRET")

# Validate that credentials are set
if not API_KEY or not API_SECRET:
    raise ValueError(
        "Missing required environment variables. Please set COINBASE_API_KEY and COINBASE_API_SECRET.\n"
        "Create a .env file based on .env.example or set them as environment variables."
    )

# Trading parameters (can be overridden via environment variables)
PRODUCT_ID = os.getenv("PRODUCT_ID", "ETH-USDC")
FIAT_AMOUNT = os.getenv("FIAT_AMOUNT", "10")  # $10 USDC
PRICE_MULTIPLIER = float(os.getenv("PRICE_MULTIPLIER", "0.998"))  # 0.998 of market price to get maker fee
POST_ONLY = os.getenv("POST_ONLY", "true").lower() == "true"  # Ensure maker-only execution
SCHEDULE_TIME = os.getenv("SCHEDULE_TIME", "09:00")  # Daily execution time

# Initialize client
client = EnhancedRESTClient(api_key=API_KEY, api_secret=API_SECRET)


def place_daily_eth_buy():
    """
    Place a $10 USDC limit buy order for ETH at 0.998 of market price.
    This ensures maker fees are charged.
    """
    try:
        logger.info(f"Placing daily ETH buy order: ${FIAT_AMOUNT} USDC at {PRICE_MULTIPLIER}x market price")
        
        # Place the limit buy order
        order = client.fiat_limit_buy(
            product_id=PRODUCT_ID,
            fiat_amount=FIAT_AMOUNT,
            price_multiplier=PRICE_MULTIPLIER,
            post_only=POST_ONLY
        )
        
        # Log order details
        if hasattr(order, 'id'):
            logger.info(f"✅ Order placed successfully!")
            logger.info(f"   Order ID: {order.id}")
            logger.info(f"   Product: {order.product_id}")
            logger.info(f"   Size: {order.size}")
            logger.info(f"   Price: {order.price}")
            logger.info(f"   Status: {order.status}")
        else:
            logger.info(f"✅ Order placed successfully! Response: {order}")
            
        return order
        
    except Exception as e:
        logger.error(f"❌ Failed to place ETH buy order: {str(e)}")
        logger.exception("Full error details:")
        return None


def run_daily_schedule():
    """
    Run the scheduler to execute daily buy orders.
    """
    # Schedule the buy order to run daily at a specific time
    # Time can be configured via SCHEDULE_TIME environment variable (24-hour format)
    schedule.every().day.at(SCHEDULE_TIME).do(place_daily_eth_buy)
    
    logger.info("Daily ETH buy scheduler started")
    logger.info(f"Scheduled to run daily at {SCHEDULE_TIME}")
    logger.info(f"Product: {PRODUCT_ID}")
    logger.info(f"Amount: ${FIAT_AMOUNT} USDC")
    logger.info(f"Price: {PRICE_MULTIPLIER}x market price (maker fee)")
    logger.info("Press Ctrl+C to stop")
    
    # Optionally place an order immediately on startup
    # Uncomment the next line if you want to place an order right away
    # place_daily_eth_buy()
    
    # Run the scheduler
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == "__main__":
    try:
        run_daily_schedule()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler error: {str(e)}")
        logger.exception("Full error details:")
