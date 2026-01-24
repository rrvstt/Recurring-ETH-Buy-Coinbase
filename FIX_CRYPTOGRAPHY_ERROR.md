# Fix: Cryptography Import Error in Lambda

## Problem
The error `cannot import name 'exceptions' from 'cryptography.hazmat.bindings._rust'` occurs because dependencies were built for Windows, but Lambda runs on Linux.

## Solution Options

### Option 1: Use Docker Build (Recommended - Easiest)

**Prerequisites:** Docker Desktop installed and running

1. Run the Docker-based build script:
   ```powershell
   .\build-lambda-package-docker.ps1
   ```

2. This will create a Linux-compatible package automatically.

3. Upload the new `lambda-deployment.zip` to Lambda.

### Option 2: Use AWS Lambda Layers (Alternative)

If Docker isn't available, you can use a pre-built cryptography layer:

1. **Add Lambda Layer:**
   - Go to your Lambda function → Layers
   - Click "Add a layer"
   - Choose "Specify an ARN"
   - Use this ARN (for Python 3.11):
     ```
     arn:aws:lambda:us-east-1:770693421928:layer:Klayers-p311-cryptography:1
     ```
   - Replace `us-east-1` with your AWS region
   - Click "Add"

2. **Update lambda-requirements.txt** to exclude cryptography:
   ```
   coinbase-advanced-py == 1.8.2
   requests >= 2.31.0
   urllib3 >= 2.2.2
   PyYAML >= 6.0.1
   # cryptography >= 42.0.4  # Provided by Lambda Layer
   cffi
   alphasquared-py >= 0.3.0
   fear-and-greed-crypto >= 0.1.0
   PyJWT >= 2.8.0
   websockets < 14.0, >= 12.0
   backoff >= 2.2.1
   ```

3. Rebuild and redeploy.

### Option 3: Use WSL2 (Windows Subsystem for Linux)

If you have WSL2 installed:

1. Open WSL2 terminal
2. Navigate to your project:
   ```bash
   cd /mnt/c/Users/sandu/OneDrive/Documents/Cursor/CB/coinbase-advancedtrade-python-main
   ```
3. Run the Linux build script:
   ```bash
   chmod +x build-lambda-package.sh
   ./build-lambda-package.sh
   ```

### Option 4: Manual Fix - Remove and Rebuild

1. Delete `lambda-deployment.zip`
2. Use Option 1 (Docker) or Option 3 (WSL2) to rebuild
3. Upload the new package

## Quick Fix Steps (Docker Method)

```powershell
# 1. Make sure Docker Desktop is running
# 2. Run the Docker build script
.\build-lambda-package-docker.ps1

# 3. Upload the new lambda-deployment.zip to Lambda
# 4. Test again
```

## Verify the Fix

After rebuilding and uploading:

1. Go to Lambda → Test
2. Run a test
3. Should see successful order placement (or a different error if credentials/config are wrong)

## Finding Lambda Layer ARNs

If you need a layer for a different region, search for "Klayers cryptography" or visit:
- https://github.com/keithrozario/Klayers
- Search for your region and Python version
