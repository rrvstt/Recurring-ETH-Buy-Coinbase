# PowerShell script to build Lambda deployment package
# Run this script from the project root directory

Write-Host "Building Lambda deployment package..." -ForegroundColor Green

# Create temporary directory
$tempDir = "lambda-package-temp"
if (Test-Path $tempDir) {
    Remove-Item -Recurse -Force $tempDir
}
New-Item -ItemType Directory -Path $tempDir | Out-Null

Write-Host "Copying Lambda function..." -ForegroundColor Yellow
Copy-Item "lambda_function.py" -Destination "$tempDir\lambda_function.py"

Write-Host "Copying coinbase_advanced_trader package..." -ForegroundColor Yellow
Copy-Item -Recurse "coinbase_advanced_trader" -Destination "$tempDir\coinbase_advanced_trader"

Write-Host "Installing dependencies..." -ForegroundColor Yellow
python -m pip install -r lambda-requirements.txt -t $tempDir --quiet

Write-Host "Creating zip file..." -ForegroundColor Yellow
if (Test-Path "lambda-deployment.zip") {
    Remove-Item "lambda-deployment.zip"
}
Compress-Archive -Path "$tempDir\*" -DestinationPath "lambda-deployment.zip" -Force

Write-Host "Cleaning up..." -ForegroundColor Yellow
Remove-Item -Recurse -Force $tempDir

Write-Host "✅ Lambda deployment package created: lambda-deployment.zip" -ForegroundColor Green
Write-Host "Package size: $((Get-Item lambda-deployment.zip).Length / 1MB) MB" -ForegroundColor Cyan
