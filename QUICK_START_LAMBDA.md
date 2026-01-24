# Quick Start: Deploy to AWS Lambda

## Prerequisites Checklist

- [ ] AWS Account created
- [ ] AWS CLI installed (`aws --version`)
- [ ] AWS CLI configured (`aws configure`)
- [ ] Python 3.9+ installed
- [ ] Coinbase API credentials ready

## Quick Deployment Steps

### 1. Build the Package

**Windows:**
```powershell
.\build-lambda-package.ps1
```

**Linux/Mac:**
```bash
chmod +x build-lambda-package.sh
./build-lambda-package.sh
```

### 2. Create Lambda Function (AWS Console)

1. Go to [AWS Lambda Console](https://console.aws.amazon.com/lambda/)
2. Click **"Create function"**
3. Select **"Author from scratch"**
4. Fill in:
   - Function name: `daily-eth-buy`
   - Runtime: `Python 3.11`
   - Architecture: `x86_64`
5. Click **"Create function"**

### 3. Upload Code

1. In your Lambda function, scroll to **"Code source"**
2. Click **"Upload from"** → **".zip file"**
3. Select `lambda-deployment.zip`
4. Click **"Save"**

### 4. Set Environment Variables

1. Go to **"Configuration"** → **"Environment variables"**
2. Click **"Edit"**
3. Add these variables:

```
COINBASE_API_KEY = your_api_key_here
COINBASE_API_SECRET = your_api_secret_here
PRODUCT_ID = ETH-USDC
FIAT_AMOUNT = 10
PRICE_MULTIPLIER = 0.998
POST_ONLY = true
```

4. Click **"Save"**

### 5. Configure Timeout

1. Go to **"Configuration"** → **"General configuration"**
2. Click **"Edit"**
3. Set Timeout to **60 seconds**
4. Set Memory to **256 MB**
5. Click **"Save"**

### 6. Test It

1. Click **"Test"** tab
2. Create a test event (use default empty `{}`)
3. Click **"Test"**
4. Check the result - should see order details if successful

### 7. Set Up Daily Schedule

1. Go to **"Configuration"** → **"Triggers"**
2. Click **"Add trigger"**
3. Select **"EventBridge (CloudWatch Events)"**
4. Click **"Create a new rule"**
5. Fill in:
   - Rule name: `daily-eth-buy-schedule`
   - Rule type: **Schedule**
   - Schedule expression: `cron(0 9 * * ? *)` (9 AM UTC daily)
6. Click **"Add"**

### 8. Verify It Works

1. Wait for the scheduled time or trigger manually
2. Check **"Monitor"** tab → **"View CloudWatch logs"**
3. Look for execution logs showing order placement

## That's It! 🎉

Your Lambda function will now:
- Run daily at 9:00 AM UTC
- Place a $10 USDC buy order for ETH
- Use maker fees (0.998 of market price)
- Log all activity to CloudWatch

## Need Help?

- See `DEPLOYMENT.md` for detailed instructions
- Check CloudWatch logs for errors
- Verify environment variables are set correctly

## Cost

- **Free tier**: First 1M Lambda requests/month
- **Your usage**: ~30 requests/month (daily)
- **Cost**: $0/month ✅
