"""
AWS Lambda Handler for Weekly AUD to USDC Conversion
Converts $105 AUD to USDC using a market buy order (executes immediately at market price).
"""

import os
import json
import logging
from coinbase_advanced_trader.enhanced_rest_client import EnhancedRESTClient

# Configure logging for Lambda
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    AWS Lambda handler function for AUD to USDC conversion.
    
    Args:
        event: Lambda event (not used, but required by Lambda)
        context: Lambda context (not used, but required by Lambda)
    
    Returns:
        dict: Response with status code and message
    """
    try:
        # Get configuration from environment variables
        api_key = os.environ.get("COINBASE_API_KEY")
        api_secret = os.environ.get("COINBASE_API_SECRET")
        product_id = os.environ.get("PRODUCT_ID", "USDC-AUD")  # Buy USDC with AUD
        aud_amount = os.environ.get("AUD_AMOUNT", "105")  # $105 AUD
        
        # Validate credentials
        if not api_key or not api_secret:
            error_msg = "Missing COINBASE_API_KEY or COINBASE_API_SECRET environment variables"
            logger.error(error_msg)
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'success': False,
                    'error': error_msg
                })
            }
        
        logger.info(f"Converting {aud_amount} AUD to USDC")
        logger.info(f"Product: {product_id}")
        
        # Initialize client
        client = EnhancedRESTClient(api_key=api_key, api_secret=api_secret)
        
        # Place a market buy order to convert AUD to USDC
        # This executes immediately at the current market price
        order = client.fiat_market_buy(
            product_id=product_id,
            fiat_amount=aud_amount
        )
        
        # Format response
        if hasattr(order, 'id'):
            response_data = {
                'success': True,
                'order_id': order.id,
                'product_id': order.product_id,
                'size': str(order.size),
                'status': order.status,
                'message': f'Successfully converted {aud_amount} AUD to USDC'
            }
            logger.info(f"✅ Conversion successful! Order ID: {order.id}")
            logger.info(f"   Converted {aud_amount} AUD to USDC")
        else:
            # Handle case where order might be a dict
            response_data = {
                'success': True,
                'order': str(order),
                'message': f'Successfully converted {aud_amount} AUD to USDC'
            }
            logger.info(f"✅ Conversion successful! Response: {order}")
        
        return {
            'statusCode': 200,
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        error_msg = f"Failed to convert AUD to USDC: {str(e)}"
        logger.error(error_msg)
        logger.exception("Full error details:")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': error_msg
            })
        }
