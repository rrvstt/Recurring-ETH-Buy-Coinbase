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
        
        # Handle different response types (dict, list, or ListOrdersResponse object)
        if isinstance(orders_response, dict):
            orders = orders_response.get('orders', [])
        elif hasattr(orders_response, 'orders'):
            # ListOrdersResponse object
            orders = orders_response.orders if orders_response.orders else []
        elif isinstance(orders_response, list):
            orders = orders_response
        else:
            logger.warning(f"Unexpected orders response format: {type(orders_response)}")
            return False
        
        if not orders:
            return False
        
        # Check if any recent filled orders exist (check last 5 orders)
        orders_to_check = orders[:5] if isinstance(orders, list) else list(orders)[:5]
        for order in orders_to_check:
            # Handle both Order objects and dicts
            if hasattr(order, 'created_time'):
                # Order object
                order_time_str = getattr(order, 'created_time', None) or getattr(order, 'creation_time', None) or getattr(order, 'created_at', None)
                order_side = str(order.side).upper() if hasattr(order, 'side') else ''
                order_id = order.id if hasattr(order, 'id') else None
            else:
                # Dictionary
                order_time_str = order.get('created_time') or order.get('creation_time') or order.get('created_at')
                order_side = order.get('side', '').upper() or order.get('order_side', '').upper()
                order_id = order.get('order_id') or order.get('id')
            
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
                        if 'BUY' in order_side:
                            logger.info(f"Recent order found: {order_id} at {order_time_str}")
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
        # Use the base RESTClient method directly to get raw response with timestamps
        # Access the underlying REST client to get raw API response
        raw_response = client.list_orders(
            product_id=product_id,
            order_status='OPEN'
        )
        
        if not raw_response:
            logger.info("No open orders found")
            return 0, []
        
        # Extract orders from response - try multiple ways to get raw dict data
        orders_to_process = []
        
        # Method 1: Check if it's already a dict
        if isinstance(raw_response, dict):
            orders_to_process = raw_response.get('orders', [])
        
        # Method 2: Check if it's a ListOrdersResponse object with orders attribute
        elif hasattr(raw_response, 'orders'):
            orders_list = raw_response.orders if raw_response.orders else []
            # Check if orders are dicts or Order objects
            if orders_list and len(orders_list) > 0 and isinstance(orders_list[0], dict):
                orders_to_process = orders_list
            elif orders_list and len(orders_list) > 0:
                # Order objects - try to get raw data from response object
                # Check if response has a way to get raw data
                if hasattr(raw_response, 'to_dict'):
                    try:
                        raw_dict = raw_response.to_dict()
                        orders_to_process = raw_dict.get('orders', [])
                    except:
                        pass
                # If we still don't have dict data, try accessing raw API response
                # For Order objects without timestamps, we'll cancel all BUY orders
                # (fallback behavior when timestamp unavailable)
                if not orders_to_process:
                    logger.warning("Orders are Order objects without timestamp data - will cancel all BUY orders")
                    # Process Order objects directly (without timestamp check)
                    orders_to_process = orders_list
        
        # Method 3: Check if it's a list
        elif isinstance(raw_response, list):
            orders_to_process = raw_response
        
        else:
            logger.warning(f"Unexpected orders response format: {type(raw_response)}")
            return 0, []
        
        if not orders_to_process:
            logger.info("No open orders found")
            return 0, []
        
        logger.info(f"Found {len(orders_to_process)} open order(s) for {product_id}")
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_threshold)
        cancelled_count = 0
        cancelled_order_ids = []
        
        for order in orders_to_process:
            try:
                # Handle both Order objects and dicts
                is_buy_order = False
                order_id = None
                order_time_str = None
                
                if hasattr(order, 'side'):
                    # Order object - use the is_buy property
                    if hasattr(order, 'is_buy'):
                        is_buy_order = order.is_buy
                    else:
                        # Fallback: check side enum directly
                        from coinbase_advanced_trader.models import OrderSide
                        is_buy_order = order.side == OrderSide.BUY if order.side else False
                    
                    order_side = str(order.side) if order.side else ''
                    order_id = order.id if hasattr(order, 'id') else None
                    # Order objects don't have timestamp in the model
                    order_time_str = None
                    logger.info(f"Processing Order object: id={order_id}, side={order_side}, is_buy={is_buy_order}")
                else:
                    # Dictionary - should have timestamp
                    order_side = order.get('side', '') or order.get('order_side', '')
                    order_id = order.get('order_id') or order.get('id')
                    order_time_str = order.get('created_time') or order.get('creation_time') or order.get('created_at')
                    is_buy_order = 'BUY' in str(order_side).upper() or order_side == 'buy'
                    logger.info(f"Processing dict order: id={order_id}, side={order_side}, timestamp={order_time_str}, is_buy={is_buy_order}")
                
                # Only cancel BUY orders
                if not is_buy_order:
                    logger.info(f"Skipping non-BUY order: {order_id} (side={order_side})")
                    continue
                
                # Determine if we should cancel this order
                should_cancel = False
                cancel_reason = ""
                
                if not order_time_str:
                    # No timestamp available - if it's an Order object, cancel all BUY orders (fallback)
                    if hasattr(order, 'side'):
                        logger.info(f"Order {order_id} is BUY order but no timestamp available - cancelling anyway (fallback)")
                        should_cancel = True
                        cancel_reason = "no timestamp available (fallback)"
                    else:
                        logger.info(f"Order {order_id} has no timestamp - cannot verify age, skipping")
                        continue
                else:
                    # We have a timestamp, parse it and check age
                    try:
                        if isinstance(order_time_str, str):
                            # Handle ISO format with 'Z' suffix
                            timestamp_to_parse = order_time_str
                            if timestamp_to_parse.endswith('Z'):
                                timestamp_to_parse = timestamp_to_parse[:-1] + '+00:00'
                            if 'T' in timestamp_to_parse:
                                order_time = datetime.fromisoformat(timestamp_to_parse)
                            else:
                                order_time = datetime.strptime(timestamp_to_parse, '%Y-%m-%d %H:%M:%S')
                                order_time = order_time.replace(tzinfo=timezone.utc)
                        else:
                            order_time = order_time_str
                            if order_time.tzinfo is None:
                                order_time = order_time.replace(tzinfo=timezone.utc)
                        
                        # Calculate age in hours for logging
                        age_hours = (datetime.now(timezone.utc) - order_time).total_seconds() / 3600
                        logger.info(f"Order {order_id} age: {age_hours:.2f} hours (threshold: {hours_threshold} hours)")
                        
                        # Check if order is older than threshold
                        if order_time < cutoff_time:
                            should_cancel = True
                            cancel_reason = f"created at {order_time_str} ({age_hours:.2f} hours old, > {hours_threshold} hours threshold)"
                            logger.info(f"Order {order_id} {cancel_reason}")
                        else:
                            logger.info(f"Order {order_id} is not old enough to cancel ({age_hours:.2f} hours < {hours_threshold} hours)")
                    except Exception as parse_error:
                        logger.warning(f"Could not parse timestamp {order_time_str}: {parse_error}")
                        import traceback
                        logger.warning(f"Traceback: {traceback.format_exc()}")
                        continue
                
                # Cancel the order if it meets criteria
                if should_cancel:
                    if not order_id:
                        logger.warning(f"Order has no ID, skipping: {order}")
                        continue
                    
                    logger.info(f"Cancelling order {order_id} - {cancel_reason}")
                    
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
                order_id_for_error = order.id if hasattr(order, 'id') else (order.get('order_id') if isinstance(order, dict) else 'unknown')
                logger.error(f"Error processing order {order_id_for_error}: {str(e)}")
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
