# AWS Lambda Deployment Guide

This guide will help you deploy the daily ETH buy script to AWS Lambda.

## Prerequisites

1. AWS Account with appropriate permissions
2. AWS CLI installed and configured (`aws configure`)
3. Python 3.9+ installed locally
4. Your Coinbase API credentials

## Step 1: Create Deployment Package

### Option A: Using the provided build script (Windows)

```powershell
.\build-lambda-package.ps1
```

### Option B: Manual build

1. Create a temporary directory:
```bash
mkdir lambda-package
cd lambda-package
```

2. Copy the Lambda function and dependencies:
```bash
# Copy the Lambda handler
cp ../lambda_function.py .

# Copy the coinbase_advanced_trader package
cp -r ../coinbase_advanced_trader .
```

3. Install dependencies:
```bash
pip install -r ../lambda-requirements.txt -t .
```

4. Create a zip file:
```bash
# Windows PowerShell
Compress-Archive -Path * -DestinationPath ../lambda-deployment.zip

# Linux/Mac
zip -r ../lambda-deployment.zip .
```

5. Clean up:
```bash
cd ..
rm -rf lambda-package
```

## Step 2: Create Lambda Function

### Using AWS Console:

1. Go to AWS Lambda Console
2. Click "Create function"
3. Choose "Author from scratch"
4. Configure:
   - Function name: `daily-eth-buy`
   - Runtime: `Python 3.9` or `Python 3.11`
   - Architecture: `x86_64`
   - Execution role: Create a new role with basic Lambda permissions
5. Click "Create function"
6. Upload the deployment package:
   - Scroll to "Code source"
   - Click "Upload from" → ".zip file"
   - Select `lambda-deployment.zip`
   - Click "Save"

### Using AWS CLI:

```bash
aws lambda create-function \
  --function-name daily-eth-buy \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://lambda-deployment.zip \
  --timeout 60 \
  --memory-size 256
```

## Step 3: Configure Environment Variables

### Using AWS Console:

1. Go to your Lambda function
2. Click "Configuration" → "Environment variables"
3. Click "Edit"
4. Add the following variables:
   - `COINBASE_API_KEY`: Your Coinbase API key
   - `COINBASE_API_SECRET`: Your Coinbase API secret (private key)
   - `PRODUCT_ID`: `ETH-USDC` (optional, defaults to this)
   - `FIAT_AMOUNT`: `10` (optional, defaults to this)
   - `PRICE_MULTIPLIER`: `0.998` (optional, defaults to this)
   - `POST_ONLY`: `true` (optional, defaults to this)
5. Click "Save"

### Using AWS CLI:

```bash
aws lambda update-function-configuration \
  --function-name daily-eth-buy \
  --environment Variables="{
    COINBASE_API_KEY=your_api_key_here,
    COINBASE_API_SECRET=your_api_secret_here,
    PRODUCT_ID=ETH-USDC,
    FIAT_AMOUNT=10,
    PRICE_MULTIPLIER=0.998,
    POST_ONLY=true
  }"
```

**⚠️ Security Note**: For production, consider using AWS Secrets Manager instead of environment variables for sensitive credentials.

## Step 4: Set Up EventBridge (CloudWatch Events) for Daily Schedule

### Using AWS Console:

1. Go to EventBridge → Rules
2. Click "Create rule"
3. Configure:
   - Name: `daily-eth-buy-schedule`
   - Rule type: `Schedule`
   - Schedule pattern: `Rate expression` or `Cron expression`
     - Rate: `rate(1 day)` (runs every day at the time you created it)
     - Cron: `cron(0 9 * * ? *)` (runs daily at 9:00 AM UTC)
4. Select target:
   - Target type: `AWS Lambda function`
   - Function: `daily-eth-buy`
5. Click "Create"

### Using AWS CLI:

```bash
# Create EventBridge rule
aws events put-rule \
  --name daily-eth-buy-schedule \
  --schedule-expression "cron(0 9 * * ? *)" \
  --description "Daily ETH buy at 9:00 AM UTC"

# Add Lambda as target
aws lambda add-permission \
  --function-name daily-eth-buy \
  --statement-id allow-eventbridge \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:REGION:ACCOUNT_ID:rule/daily-eth-buy-schedule

aws events put-targets \
  --rule daily-eth-buy-schedule \
  --targets "Id=1,Arn=arn:aws:lambda:REGION:ACCOUNT_ID:function:daily-eth-buy"
```

Replace `REGION` and `ACCOUNT_ID` with your AWS region and account ID.

## Step 5: Test the Function

### Using AWS Console:

1. Go to your Lambda function
2. Click "Test"
3. Create a test event (use the default empty event)
4. Click "Test"
5. Check the execution results

### Using AWS CLI:

```bash
aws lambda invoke \
  --function-name daily-eth-buy \
  --payload '{}' \
  response.json

cat response.json
```

## Step 6: Monitor Execution

1. Go to CloudWatch → Logs → Log groups
2. Find `/aws/lambda/daily-eth-buy`
3. View execution logs to verify orders are being placed

## Updating the Function

When you need to update the code:

1. Rebuild the deployment package (Step 1)
2. Update the function:
   ```bash
   aws lambda update-function-code \
     --function-name daily-eth-buy \
     --zip-file fileb://lambda-deployment.zip
   ```

## Cost Estimate

- Lambda: First 1M requests/month are free, then $0.20 per 1M requests
- EventBridge: First 1M custom events/month are free
- **Estimated cost: ~$0/month** (well within free tier for daily execution)

## Troubleshooting

### Common Issues:

1. **Timeout errors**: Increase timeout in Lambda configuration (default 3s, try 60s)
2. **Memory errors**: Increase memory allocation (try 256 MB or 512 MB)
3. **Import errors**: Ensure all dependencies are included in the deployment package
4. **Authentication errors**: Verify API credentials are set correctly in environment variables
5. **Order failures**: Check CloudWatch logs for detailed error messages

### Viewing Logs:

```bash
aws logs tail /aws/lambda/daily-eth-buy --follow
```

## Security Best Practices

1. **Use AWS Secrets Manager** for API credentials instead of environment variables
2. **Restrict IAM permissions** - Lambda role should only have necessary permissions
3. **Enable VPC** if you need additional network security (optional)
4. **Enable AWS X-Ray** for better monitoring and debugging
5. **Set up CloudWatch alarms** for failed executions

## Using AWS Secrets Manager (Recommended)

Instead of environment variables, store credentials in Secrets Manager:

1. Create secret:
```bash
aws secretsmanager create-secret \
  --name coinbase-api-credentials \
  --secret-string '{"COINBASE_API_KEY":"your_key","COINBASE_API_SECRET":"your_secret"}'
```

2. Update Lambda execution role to allow reading the secret
3. Update `lambda_function.py` to fetch from Secrets Manager (modify code accordingly)
