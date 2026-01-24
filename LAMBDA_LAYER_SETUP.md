# Using Lambda Layers for Cryptography (No Docker Required)

This guide will help you fix the cryptography error using AWS Lambda Layers instead of Docker.

## Step 1: Find Your AWS Region

First, check which AWS region your Lambda function is in:
1. Go to your Lambda function in AWS Console
2. Look at the top right corner - you'll see your region (e.g., `us-east-1`, `us-west-2`, `eu-west-1`)

## Step 2: Add Cryptography Lambda Layer

1. In your Lambda function page, scroll down to **"Layers"** section
2. Click **"Add a layer"**
3. Select **"Specify an ARN"**
4. Use one of these ARNs based on your region and Python version:

### For Python 3.11:
- **us-east-1**: `arn:aws:lambda:us-east-1:770693421928:layer:Klayers-p311-cryptography:1`
- **us-east-2**: `arn:aws:lambda:us-east-2:770693421928:layer:Klayers-p311-cryptography:1`
- **us-west-1**: `arn:aws:lambda:us-west-1:770693421928:layer:Klayers-p311-cryptography:1`
- **us-west-2**: `arn:aws:lambda:us-west-2:770693421928:layer:Klayers-p311-cryptography:1`
- **eu-west-1**: `arn:aws:lambda:eu-west-1:770693421928:layer:Klayers-p311-cryptography:1`
- **eu-central-1**: `arn:aws:lambda:eu-central-1:770693421928:layer:Klayers-p311-cryptography:1`
- **ap-southeast-1**: `arn:aws:lambda:ap-southeast-1:770693421928:layer:Klayers-p311-cryptography:1`

### For Python 3.9 or 3.10:
Replace `p311` with `p39` or `p310` in the ARN above.

5. Click **"Add"**

## Step 3: Rebuild Package Without Cryptography

Now rebuild your Lambda package without cryptography (since it's provided by the layer):

**Windows:**
```powershell
.\build-lambda-package-no-crypto.ps1
```

This will create a new `lambda-deployment.zip` without cryptography.

## Step 4: Upload New Package

1. Go back to your Lambda function → **"Code"** tab
2. Click **"Upload from"** → **".zip file"**
3. Select the new `lambda-deployment.zip`
4. Click **"Save"**

## Step 5: Test Again

1. Go to **"Test"** tab
2. Run a test with empty event `{}`
3. Should work now! ✅

## Finding Layer ARNs for Other Regions

If your region isn't listed, visit:
- https://github.com/keithrozario/Klayers
- Search for "cryptography" and your Python version
- Find the ARN for your region

## Troubleshooting

- **Layer not found**: Make sure you're using the correct region and Python version
- **Still getting errors**: Verify the layer was added successfully in the Layers section
- **Different Python version**: Check your Lambda runtime version and use matching layer ARN
