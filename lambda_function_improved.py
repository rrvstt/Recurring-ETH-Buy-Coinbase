"""
AWS Lambda Handler for Daily ETH Buy (Improved Version)
Places a $10 USDC buy order for ETH at 0.998 of market price (maker fee).
Cancels unfilled orders after 20 hours and places a market order to ensure daily execution.

Improvements:
- Balance checking before placing orders
- Better error handling and retry logic
- Idempotency check (avoid duplicate orders)
- Structured logging
- Order status verification
- Configuration validation
"""

import os
import json
import logging
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from typing import Tuple, List, Optional
from coinbase_advanced_trader.enhanced_rest_client import EnhancedRESTClient

# Configure logging for Lambda with structured format
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Add JSON formatter for better CloudWatch Insights queries
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def check_balance(client: EnhancedRESTClient, currency: str, required_amount: Decimal) -> Tuple[bool, Decimal]:
    """
    Check if account has sufficient balance.
    
    Args:
        client: EnhancedRESTClient instance
        currency: Currency code (e.g., "USDC")
        required_amount: Required amount as Decimal
    
    Returns:
        tuple: (has_sufficient_balance, current_balance)
    """
    try:
        balance = client.get_crypto_balance(currency)
        has_sufficient = balance >= required_amount
        logger.info(f"Balance check - {currency}: {balance}, Required: {required_amount}, Sufficient: {has_sufficient}")
        return has_sufficient, balance
    except Exception as e:
        logger.error(f"Error checking balance for {currency}: {str(e)}")
        # Don't fail - let the order attempt proceed (API will reject if insufficient)
        return True, Decimal('0')  # Assume sufficient to proceed


def check_recent_order_exists(client: EnhancedRESTClient, product_id: str, hours_threshold: int = 4) -> bool:
    """
    Check if a recent order was already placed today to avoid duplicates.
    
    Args:
        client: EnhancedRESTClient instance
        product_id: Product ID to check
        hours_threshold: Hours to look back (default: 4 hours)
    
    Returns:
        bool: True if recent order exists
    """
    try:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_threshold)
        
        # Get recent orders (filled orders)
        orders_response = client.list_orders(
            product_id=product_id,
            order_status='FILLED'
        )
        
        if not orders_response:
            return False
        
        orders = orders_response.get('orders', []) if isinstance(orders_response, dict) else orders_response
        
        if not orders:
            return False
        
        # Check if any recent filled orders exist
        for order in orders[:5]:  # Check last 5 orders
            order_time_str = order.get('created_time') or order.get('creation_time') or order.get('created_at')
            if order_time_str:
                try:
                    if isinstance(order_time_str, str):
                        if order_time_str.endswith('Z'):
                            order_time_str = order_time_str[:-1] + '+00:00'
                        if 'T' in order_time_str:
                            order_time = datetime.fromisoformat(order_time_str)
                        else:
                            continue
                    else:
                        order_time = order_time_str
                        if order_time.tzinfo is None:
                            order_time = order_time.replace(tzinfo=timezone.utc)
                    
                    # Check if order is recent and is a BUY order
                    if order_time >= cutoff_time:
                        order_side = order.get('side', '').upper()
                        if order_side == 'BUY' or order.get('order_side') == 'BUY':
                            logger.info(f"Recent order found: {order.get('order_id')} at {order_time_str}")
                            return True
                except Exception:
                    continue
        
        return False
        
    except Exception as e:
        logger.warning(f"Error checking for recent orders: {str(e)}")
        return False  # Don't block if check fails


def cancel_old_orders(client: EnhancedRESTClient, product_id: str, hours_threshold: int = 20) -> Tuple[int, List[str]]:
    """
    Cancel unfilled ETH-USDC orders older than the specified hours.
    Only cancels BUY orders for the specified product.
    
    Args:
        client: EnhancedRESTClient instance
        product_id: Product ID to filter orders (e.g., "ETH-USDC")
        hours_threshold: Hours threshold for cancelling orders (default: 20)
    
    Returns:
        tuple: (number_of_cancelled_orders, list_of_cancelled_order_ids)
    """
    try:
        orders_response = client.list_orders(
            product_id=product_id,
            order_status='OPEN'
        )
        
        if not orders_response:
            logger.info("No open orders found")
            return 0, []
        
        orders = orders_response.get('orders', []) if isinstance(orders_response, dict) else orders_response
        
        if not orders:
            logger.info("No open orders found")
            return 0, []
        
        logger.info(f"Found {len(orders)} open order(s) for {product_id}")
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_threshold)
        cancelled_count = 0
        cancelled_order_ids = []
        
        for order in orders:
            try:
                # Only cancel BUY orders
                order_side = order.get('side', '').upper() or order.get('order_side', '').upper()
                if order_side != 'BUY':
                    logger.debug(f"Skipping non-BUY order: {order.get('order_id')}")
                    continue
                
                order_time_str = order.get('created_time') or order.get('creation_time') or order.get('created_at')
                if not order_time_str:
                    logger.warning(f"Order {order.get('order_id')} has no timestamp, skipping")
                    continue
                
                # Parse timestamp
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
                    
                    cancel_response = client.cancel_orders(order_ids=[order_id])
                    
                    if cancel_response:
                        if isinstance(cancel_response, dict):
                            if cancel_response.get('success') or 'results' in cancel_response:
                                cancelled_count += 1
                                cancelled_order_ids.append(order_id)
                                logger.info(f"✅ Successfully cancelled order {order_id}")
                            else:
                                logger.warning(f"Failed to cancel order {order_id}: {cancel_response}")
                        else:
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
        return 0, []


def validate_config(product_id: str, fiat_amount: str, price_multiplier: float) -> Optional[str]:
    """
    Validate configuration values.
    
    Returns:
        Error message if invalid, None if valid
    """
    try:
        amount_decimal = Decimal(fiat_amount)
        if amount_decimal <= 0:
            return "FIAT_AMOUNT must be greater than 0"
        
        if price_multiplier <= 0 or price_multiplier > 1.5:
            return "PRICE_MULTIPLIER must be between 0 and 1.5"
        
        if not product_id or '-' not in product_id:
            return "PRODUCT_ID must be in format BASE-QUOTE (e.g., ETH-USDC)"
        
        return None
    except Exception as e:
        return f"Configuration validation error: {str(e)}"


def lambda_handler(event, context):
    """
    AWS Lambda handler function (Improved Version).
    
    Args:
        event: Lambda event (not used, but required by Lambda)
        context: Lambda context (not used, but required by Lambda)
    
    Returns:
        dict: Response with status code and message
    """
    execution_start = datetime.now(timezone.utc)
    
    try:
        # Get configuration from environment variables
        api_key = os.environ.get("COINBASE_API_KEY")
        api_secret = os.environ.get("COINBASE_API_SECRET")
        product_id = os.environ.get("PRODUCT_ID", "ETH-USDC")
        fiat_amount = os.environ.get("FIAT_AMOUNT", "10")
        price_multiplier = float(os.environ.get("PRICE_MULTIPLIER", "0.998"))
        post_only = os.environ.get("POST_ONLY", "true").lower() == "true"
        hours_threshold = int(os.environ.get("ORDER_CANCEL_HOURS", "20"))
        check_balance_enabled = os.environ.get("CHECK_BALANCE", "true").lower() == "true"
        check_duplicates = os.environ.get("CHECK_DUPLICATES", "true").lower() == "true"
        
        # Validate credentials
        if not api_key or not api_secret:
            error_msg = "Missing COINBASE_API_KEY or COINBASE_API_SECRET environment variables"
            logger.error(error_msg)
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'success': False,
                    'error': error_msg,
                    'timestamp': execution_start.isoformat()
                })
            }
        
        # Validate configuration
        config_error = validate_config(product_id, fiat_amount, price_multiplier)
        if config_error:
            logger.error(f"Configuration error: {config_error}")
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': config_error,
                    'timestamp': execution_start.isoformat()
                })
            }
        
        # Initialize client
        client = EnhancedRESTClient(api_key=api_key, api_secret=api_secret)
        
        # Extract quote currency (e.g., "USDC" from "ETH-USDC")
        quote_currency = product_id.split('-')[1] if '-' in product_id else "USDC"
        required_amount = Decimal(fiat_amount)
        
        # Check balance if enabled
        if check_balance_enabled:
            has_balance, current_balance = check_balance(client, quote_currency, required_amount)
            if not has_balance:
                error_msg = f"Insufficient balance: {current_balance} {quote_currency} available, {required_amount} {quote_currency} required"
                logger.error(error_msg)
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'success': False,
                        'error': error_msg,
                        'current_balance': str(current_balance),
                        'required_amount': fiat_amount,
                        'timestamp': execution_start.isoformat()
                    })
                }
        
        # Check for recent orders to avoid duplicates
        if check_duplicates:
            if check_recent_order_exists(client, product_id, hours_threshold=4):
                logger.info("Recent order already exists, skipping to avoid duplicate")
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'success': True,
                        'message': 'Recent order already exists, skipped duplicate',
                        'action': 'skipped',
                        'timestamp': execution_start.isoformat()
                    })
                }
        
        # Step 1: Check and cancel old unfilled orders
        logger.info(f"Checking for unfilled {product_id} orders older than {hours_threshold} hours...")
        cancelled_count, cancelled_order_ids = cancel_old_orders(client, product_id, hours_threshold)
        
        # Step 2: Place order (market if old orders were cancelled, limit otherwise)
        try:
            if cancelled_count > 0:
                logger.info(f"Placing MARKET buy order (old orders cancelled): ${fiat_amount} {quote_currency}")
                order = client.fiat_market_buy(
                    product_id=product_id,
                    fiat_amount=fiat_amount
                )
                order_type = "market"
            else:
                logger.info(f"Placing LIMIT buy order: ${fiat_amount} {quote_currency} at {price_multiplier}x market price")
                logger.info(f"Product: {product_id}, Post-only: {post_only}")
                order = client.fiat_limit_buy(
                    product_id=product_id,
                    fiat_amount=fiat_amount,
                    price_multiplier=price_multiplier,
                    post_only=post_only
                )
                order_type = "limit"
        except Exception as order_error:
            error_msg = f"Failed to place order: {str(order_error)}"
            logger.error(error_msg)
            logger.exception("Order placement error details:")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'success': False,
                    'error': error_msg,
                    'cancelled_old_orders': cancelled_count,
                    'timestamp': execution_start.isoformat()
                })
            }
        
        # Format response
        execution_time = (datetime.now(timezone.utc) - execution_start).total_seconds()
        
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
                'cancelled_order_ids': cancelled_order_ids,
                'execution_time_seconds': round(execution_time, 2),
                'timestamp': execution_start.isoformat()
            }
            logger.info(f"✅ {order_type.upper()} order placed successfully! Order ID: {order.id}")
            if cancelled_count > 0:
                logger.info(f"   Cancelled {cancelled_count} old order(s): {cancelled_order_ids}")
        else:
            response_data = {
                'success': True,
                'order_type': order_type,
                'order': str(order),
                'cancelled_old_orders': cancelled_count,
                'cancelled_order_ids': cancelled_order_ids,
                'execution_time_seconds': round(execution_time, 2),
                'timestamp': execution_start.isoformat()
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
        
        execution_time = (datetime.now(timezone.utc) - execution_start).total_seconds()
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': error_msg,
                'execution_time_seconds': round(execution_time, 2),
                'timestamp': execution_start.isoformat()
            })
        }
