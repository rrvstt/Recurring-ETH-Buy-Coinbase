# AUD to USDC Weekly Conversion Setup

This guide will help you set up a weekly Lambda function to convert $105 AUD to USDC.

## Step 1: Build the Package

Since this uses the same dependencies as the ETH buy function, you can reuse the same deployment package OR build a new one:

**Option A: Reuse existing package (if you already have lambda-deployment.zip)**
- Skip to Step 2

**Option B: Build new package with the new function**
```powershell
# Copy the new function to replace the old one temporarily
Copy-Item lambda_function_aud_to_usdc.py lambda_function.py -Force

# Build the package
.\build-lambda-package-docker.ps1

# Restore the original ETH function (optional)
# Copy-Item lambda_function.py lambda_function_eth.py
```

## Step 2: Create New Lambda Function

1. Go to [AWS Lambda Console](https://console.aws.amazon.com/lambda/)
2. Click **"Create function"**
3. Select **"Author from scratch"**
4. Fill in:
   - Function name: `weekly-aud-to-usdc`
   - Runtime: `Python 3.11`
   - Architecture: `x86_64`
5. Click **"Create function"**

## Step 3: Upload Code

**Option A: If you built a new package:**
1. In your Lambda function, scroll to **"Code source"**
2. Click **"Upload from"** → **".zip file"**
3. Select `lambda-deployment.zip`
4. Click **"Save"**

**Option B: If reusing package, just update the handler:**
1. Go to **"Code"** tab
2. Click **"Upload from"** → **".zip file"**
3. Upload your existing `lambda-deployment.zip`
4. After upload, rename `lambda_function.py` to `lambda_function_eth.py` (if you want to keep both)
5. Create a new file called `lambda_function.py` and paste the content from `lambda_function_aud_to_usdc.py`
6. Click **"Save"**

## Step 4: Set Handler

1. Go to **"Configuration"** → **"General configuration"**
2. Click **"Edit"**
3. Set **Handler** to: `lambda_function.lambda_handler`
4. Set **Timeout** to: `60 seconds`
5. Set **Memory** to: `256 MB`
6. Click **"Save"**

## Step 5: Set Environment Variables

1. Go to **"Configuration"** → **"Environment variables"**
2. Click **"Edit"**
3. Add/Update these variables:

```
COINBASE_API_KEY = your_api_key_here
COINBASE_API_SECRET = your_api_secret_here
PRODUCT_ID = USDC-AUD
AUD_AMOUNT = 105
```

4. Click **"Save"**

**Note:** Make sure `PRODUCT_ID` is set to `USDC-AUD` (buying USDC with AUD). If Coinbase uses a different product ID format, you may need to adjust this.

## Step 6: Test It

1. Click **"Test"** tab
2. Create a test event (use default empty `{}`)
3. Click **"Test"**
4. Check the result - should see conversion success

## Step 7: Set Up Weekly Schedule

1. Go to **"Configuration"** → **"Triggers"**
2. Click **"Add trigger"**
3. Select **"EventBridge (CloudWatch Events)"**
4. Click **"Create a new rule"**
5. Fill in:
   - Rule name: `weekly-aud-to-usdc-schedule`
   - Rule type: **Schedule**
   - Schedule expression: `cron(0 14 ? * MON *)` 
     - This runs every Monday at 14:00 UTC (2:00 PM UTC)
     - Adjust the day/time as needed
   - Or use: `rate(7 days)` to run every 7 days from creation time
6. Click **"Add"**

### Common Weekly Schedule Expressions:

- **Every Monday at 14:00 UTC**: `cron(0 14 ? * MON *)`
- **Every Sunday at 14:00 UTC**: `cron(0 14 ? * SUN *)`
- **Every 7 days**: `rate(7 days)`
- **Every Monday at 14:30 UTC**: `cron(30 14 ? * MON *)`

## Verify It Works

1. Wait for the scheduled time or trigger manually
2. Check **"Monitor"** tab → **"View CloudWatch logs"**
3. Look for execution logs showing conversion details

## Important Notes

1. **Product ID**: Make sure `USDC-AUD` is the correct trading pair on Coinbase. If not available, you might need to:
   - Check available AUD pairs: `AUD-USDC`, `USDC-AUD`, etc.
   - Or convert AUD → USD → USDC in two steps

2. **Market Order**: This uses a market order, which executes immediately at the current market price. There's no price control, but it ensures the conversion happens.

3. **Balance Check**: The function doesn't check if you have enough AUD balance. Make sure $105 AUD is available in your Coinbase account before the scheduled time.

4. **Fees**: Market orders typically have higher fees than limit orders, but they execute immediately.

## Troubleshooting

- **"Invalid product_id"**: Check what AUD trading pairs are available on Coinbase Advanced Trade
- **"Insufficient funds"**: Make sure you have at least $105 AUD in your account
- **Conversion not happening**: Check CloudWatch logs for detailed error messages
