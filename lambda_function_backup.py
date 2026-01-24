"""
AWS Lambda Handler for Daily ETH Buy
Places a $10 USDC buy order for ETH at 0.998 of market price (maker fee).
Cancels unfilled orders after 20 hours and places a market order to ensure daily execution.
"""

import os
import json
import logging
from datetime import datetime, timedelta, timezone
from coinbase_advanced_trader.enhanced_rest_client import EnhancedRESTClient

# Configure logging for Lambda
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def cancel_old_orders(client, product_id, hours_threshold=20):
    """
    Cancel unfilled ETH-USDC orders older than the specified hours.
    
    Args:
        client: EnhancedRESTClient instance (inherits from RESTClient)
        product_id: Product ID to filter orders (e.g., "ETH-USDC")
        hours_threshold: Hours threshold for cancelling orders (default: 20)
    
    Returns:
        tuple: (number_of_cancelled_orders, list_of_cancelled_order_ids)
    """
    try:
        # Get list of orders using RESTClient.list_orders()
        # Filter by product_id and order_status='OPEN' for unfilled orders
        orders_response = client.list_orders(
            product_id=product_id,
            order_status='OPEN'  # Only get open/unfilled orders
        )
        
        if not orders_response:
            logger.info("No open orders found")
            return 0, []
        
        # Handle different response formats
        if isinstance(orders_response, dict):
            orders = orders_response.get('orders', [])
        elif isinstance(orders_response, list):
            orders = orders_response
        else:
            logger.warning(f"Unexpected orders response format: {type(orders_response)}")
            return 0, []
        
        if not orders:
            logger.info("No open orders found")
            return 0, []
        
        logger.info(f"Found {len(orders)} open order(s) for {product_id}")
        
        # Calculate cutoff time (20 hours ago)
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_threshold)
        cancelled_count = 0
        cancelled_order_ids = []
        
        for order in orders:
            try:
                # Parse order creation time
                # Coinbase API typically returns ISO format timestamps
                order_time_str = order.get('created_time') or order.get('creation_time') or order.get('created_at')
                if not order_time_str:
                    logger.warning(f"Order {order.get('order_id')} has no timestamp, skipping")
                    continue
                
                # Parse the timestamp (handle different formats)
                try:
                    if isinstance(order_time_str, str):
                        if order_time_str.endswith('Z'):
                            order_time_str = order_time_str[:-1] + '+00:00'
                        if 'T' in order_time_str:
                            order_time = datetime.fromisoformat(order_time_str)
                        else:
                            order_time = datetime.strptime(order_time_str, '%Y-%m-%d %H:%M:%S')
                            order_time = order_time.replace(tzinfo=timezone.utc)
                    else:
                        # If it's already a datetime object
                        order_time = order_time_str
                        if order_time.tzinfo is None:
                            order_time = order_time.replace(tzinfo=timezone.utc)
                except Exception as parse_error:
                    logger.warning(f"Could not parse timestamp {order_time_str}: {parse_error}")
                    continue
                
                # Check if order is older than threshold
                if order_time < cutoff_time:
                    order_id = order.get('order_id') or order.get('id')
                    if not order_id:
                        logger.warning(f"Order has no ID, skipping: {order}")
                        continue
                    
                    logger.info(f"Cancelling order {order_id} created at {order_time_str} (> {hours_threshold} hours old)")
                    
                    # Cancel the order using RESTClient.cancel_orders()
                    cancel_response = client.cancel_orders(order_ids=[order_id])
                    
                    # Check cancellation success
                    if cancel_response:
                        if isinstance(cancel_response, dict):
                            if cancel_response.get('success') or 'results' in cancel_response:
                                cancelled_count += 1
                                cancelled_order_ids.append(order_id)
                                logger.info(f"✅ Successfully cancelled order {order_id}")
                            else:
                                logger.warning(f"Failed to cancel order {order_id}: {cancel_response}")
                        else:
                            # Assume success if we get a response
                            cancelled_count += 1
                            cancelled_order_ids.append(order_id)
                            logger.info(f"✅ Successfully cancelled order {order_id}")
                    else:
                        logger.warning(f"No response when cancelling order {order_id}")
                        
            except Exception as e:
                logger.error(f"Error processing order {order.get('order_id', 'unknown')}: {str(e)}")
                continue
        
        logger.info(f"Cancelled {cancelled_count} order(s) older than {hours_threshold} hours")
        return cancelled_count, cancelled_order_ids
        
    except Exception as e:
        logger.error(f"Error checking/cancelling old orders: {str(e)}")
        logger.exception("Full error details:")
        # Don't fail the entire function if order cancellation fails
        return 0, []


def lambda_handler(event, context):
    """
    AWS Lambda handler function.
    
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
        product_id = os.environ.get("PRODUCT_ID", "ETH-USDC")
        fiat_amount = os.environ.get("FIAT_AMOUNT", "10")
        price_multiplier = float(os.environ.get("PRICE_MULTIPLIER", "0.998"))
        post_only = os.environ.get("POST_ONLY", "true").lower() == "true"
        hours_threshold = int(os.environ.get("ORDER_CANCEL_HOURS", "20"))
        
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
        
        # Initialize client
        client = EnhancedRESTClient(api_key=api_key, api_secret=api_secret)
        
        # Step 1: Check and cancel old unfilled orders
        logger.info(f"Checking for unfilled {product_id} orders older than {hours_threshold} hours...")
        cancelled_count, cancelled_order_ids = cancel_old_orders(client, product_id, hours_threshold)
        
        # Step 2: Place order (market if old orders were cancelled, limit otherwise)
        if cancelled_count > 0:
            logger.info(f"Placing MARKET buy order (old orders cancelled): ${fiat_amount} USDC")
            # Place market order to ensure execution
            order = client.fiat_market_buy(
                product_id=product_id,
                fiat_amount=fiat_amount
            )
            order_type = "market"
        else:
            logger.info(f"Placing LIMIT buy order: ${fiat_amount} USDC at {price_multiplier}x market price")
            logger.info(f"Product: {product_id}, Post-only: {post_only}")
            # Place limit order for maker fee
            order = client.fiat_limit_buy(
                product_id=product_id,
                fiat_amount=fiat_amount,
                price_multiplier=price_multiplier,
                post_only=post_only
            )
            order_type = "limit"
        
        # Format response
        if hasattr(order, 'id'):
            response_data = {
                'success': True,
                'order_type': order_type,
                'order_id': order.id,
                'product_id': order.product_id,
                'size': str(order.size),
                'price': str(order.price) if order.price else None,
                'status': order.status,
                'cancelled_old_orders': cancelled_count,
                'cancelled_order_ids': cancelled_order_ids
            }
            logger.info(f"✅ {order_type.upper()} order placed successfully! Order ID: {order.id}")
            if cancelled_count > 0:
                logger.info(f"   Cancelled {cancelled_count} old order(s): {cancelled_order_ids}")
        else:
            # Handle case where order might be a dict
            response_data = {
                'success': True,
                'order_type': order_type,
                'order': str(order),
                'cancelled_old_orders': cancelled_count,
                'cancelled_order_ids': cancelled_order_ids
            }
            logger.info(f"✅ {order_type.upper()} order placed successfully! Response: {order}")
        
        return {
            'statusCode': 200,
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        error_msg = f"Failed to place ETH buy order: {str(e)}"
        logger.error(error_msg)
        logger.exception("Full error details:")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': error_msg
            })
        }
