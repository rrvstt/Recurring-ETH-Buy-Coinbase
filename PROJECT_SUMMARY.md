# Recurring ETH Buy - Coinbase Automation

## Project Overview

This project automates daily Ethereum (ETH) purchases on Coinbase Advanced Trade using AWS Lambda. It implements a Dollar Cost Averaging (DCA) strategy that places a $10 USDC buy order for ETH daily, optimized for maker fees.

## Key Features

### 🤖 Automated Daily Trading
- **Daily Execution**: Runs automatically via AWS Lambda and EventBridge (CloudWatch Events)
- **Dollar Cost Averaging**: Consistent $10 USDC purchases regardless of market conditions
- **Maker Fee Optimization**: Places limit orders at 0.998x market price to qualify for lower maker fees
- **Post-Only Orders**: Ensures orders add liquidity to the market (maker fees)

### 🛡️ Safety & Reliability Features

#### Balance Checking
- Verifies sufficient USDC balance before placing orders
- Prevents "insufficient funds" errors
- Configurable via `CHECK_BALANCE` environment variable

#### Duplicate Order Prevention
- Checks for recent orders (within last 4 hours)
- Prevents multiple orders on the same day
- Configurable via `CHECK_DUPLICATES` environment variable

#### Order Management
- **Automatic Cleanup**: Cancels unfilled orders older than 20 hours
- **Fallback Strategy**: Places market orders if old limit orders are cancelled
- **Smart Filtering**: Only cancels BUY orders (preserves sell orders)
- **Robust Timestamp Handling**: Handles various timestamp formats from Coinbase API

### 📊 Monitoring & Logging
- Structured logging for CloudWatch
- Execution time tracking
- Detailed order placement logs
- Error tracking and reporting

### ⚙️ Configuration
All settings via environment variables:
- `COINBASE_API_KEY`: Your Coinbase API key
- `COINBASE_API_SECRET`: Your Coinbase API secret
- `PRODUCT_ID`: Trading pair (default: `ETH-USDC`)
- `FIAT_AMOUNT`: Purchase amount in USDC (default: `10`)
- `PRICE_MULTIPLIER`: Price multiplier for limit orders (default: `0.998`)
- `POST_ONLY`: Force maker-only orders (default: `true`)
- `CHECK_BALANCE`: Enable balance checking (default: `true`)
- `CHECK_DUPLICATES`: Enable duplicate prevention (default: `true`)

## Architecture

### Components

1. **Lambda Function** (`lambda_function.py`)
   - Main handler for AWS Lambda
   - Implements all trading logic
   - Handles order placement, cancellation, and management

2. **Enhanced REST Client** (`coinbase_advanced_trader/`)
   - Wrapper around Coinbase Advanced Trade API
   - Provides simplified trading methods
   - Handles authentication and API calls

3. **Build Scripts**
   - `build-lambda-package-docker.ps1`: Docker-based build for Linux compatibility
   - `build-lambda-package.ps1`: Windows PowerShell build script
   - `build-lambda-package.sh`: Linux/Mac build script

4. **Documentation**
   - `DEPLOYMENT.md`: Detailed deployment instructions
   - `QUICK_START_LAMBDA.md`: Quick deployment guide
   - `IMPROVEMENTS.md`: Feature documentation
   - `FIX_CRYPTOGRAPHY_ERROR.md`: Troubleshooting guide

## How It Works

### Daily Execution Flow

1. **Trigger**: EventBridge (CloudWatch Events) triggers Lambda daily at scheduled time
2. **Balance Check**: Verifies sufficient USDC balance
3. **Duplicate Check**: Checks for recent orders (last 4 hours)
4. **Order Cleanup**: Cancels unfilled orders older than 20 hours
5. **Order Placement**:
   - If old orders were cancelled → Places market order (ensures execution)
   - Otherwise → Places limit order at 0.998x market price (maker fees)
6. **Logging**: Records all actions and results to CloudWatch

### Order Cancellation Logic

The function intelligently manages stale orders:
- Only cancels BUY orders (preserves sell orders)
- Cancels orders older than 20 hours
- Falls back to market orders if cancellation occurs
- Handles Order objects without timestamps gracefully

## Deployment

### Prerequisites
- AWS Account
- Coinbase Advanced Trade API credentials
- Docker (for Windows builds)
- Python 3.11+

### Quick Deploy

1. **Build Package**:
   ```powershell
   .\build-lambda-package-docker.ps1
   ```

2. **Create Lambda Function**:
   - Runtime: Python 3.11
   - Memory: 256 MB
   - Timeout: 60 seconds

3. **Upload Code**: Upload `lambda-deployment.zip`

4. **Set Environment Variables**: Add Coinbase credentials and configuration

5. **Configure Trigger**: Set up EventBridge schedule (e.g., `cron(0 9 * * ? *)` for 9 AM UTC daily)

See `QUICK_START_LAMBDA.md` for detailed steps.

## Security

### Credentials Management
- ✅ API credentials stored in Lambda environment variables (encrypted at rest)
- ✅ `.env` file excluded from Git (never committed)
- ✅ `.gitignore` configured to exclude sensitive files

### Best Practices
- Use least-privilege IAM roles for Lambda
- Enable CloudWatch logging for audit trail
- Monitor execution logs regularly
- Set up CloudWatch alarms for failures

## Cost Analysis

### AWS Lambda
- **Free Tier**: 1M requests/month free
- **Your Usage**: ~30 requests/month (daily)
- **Cost**: $0/month ✅

### Coinbase Fees
- **Maker Fees**: ~0.4% (with post-only orders)
- **Taker Fees**: ~0.6% (if market order fallback used)
- **Daily Cost**: ~$0.04 (on $10 purchase)
- **Monthly Cost**: ~$1.20

## Monitoring

### CloudWatch Metrics
- Execution duration
- Error rate
- Order placement success rate
- Balance check failures

### Recommended Alarms
- Function errors
- Execution duration > 10 seconds
- Multiple consecutive failures

## File Structure

```
.
├── lambda_function.py              # Main Lambda handler
├── daily_eth_buy.py                # Local version (for testing)
├── coinbase_advanced_trader/       # Coinbase API wrapper
├── build-lambda-package-docker.ps1 # Docker build script
├── lambda-requirements.txt         # Lambda dependencies
├── DEPLOYMENT.md                   # Detailed deployment guide
├── QUICK_START_LAMBDA.md           # Quick start guide
├── IMPROVEMENTS.md                 # Feature documentation
└── .env.example                     # Environment variable template
```

## Troubleshooting

### Common Issues

1. **Cryptography Import Error**
   - Solution: Use Docker build script (`build-lambda-package-docker.ps1`)
   - See `FIX_CRYPTOGRAPHY_ERROR.md` for details

2. **Orders Not Cancelling**
   - Check CloudWatch logs for order processing details
   - Verify orders are BUY orders (not SELL)
   - Check timestamp parsing in logs

3. **Insufficient Balance**
   - Function will log balance check failures
   - Ensure sufficient USDC in Coinbase account
   - Check `CHECK_BALANCE` environment variable

## Future Enhancements

Potential improvements (not yet implemented):
- Retry logic for transient failures
- Circuit breaker pattern
- SNS/SES notifications on failures
- Cost tracking and reporting
- Dry run mode for testing
- Rate limiting handling
- Order status verification

## License

MIT License - See LICENSE file for details

## Disclaimer

This project is not affiliated with Coinbase. Use at your own risk. Trading cryptocurrencies carries financial risk. The developers are not responsible for any financial losses.

## Support

For issues or questions:
1. Check CloudWatch logs
2. Review documentation files
3. Verify environment variables
4. Check Coinbase API status
