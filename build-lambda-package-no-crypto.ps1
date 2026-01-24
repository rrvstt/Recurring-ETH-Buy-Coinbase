# PowerShell script to build Lambda deployment package WITHOUT cryptography
# Cryptography will be provided by a Lambda Layer instead
# Run this script from the project root directory

Write-Host "Building Lambda deployment package (without cryptography)..." -ForegroundColor Green
Write-Host "Note: Cryptography will be provided by Lambda Layer" -ForegroundColor Cyan

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

Write-Host "Installing dependencies (excluding cryptography)..." -ForegroundColor Yellow
python -m pip install -r lambda-requirements-no-crypto.txt -t $tempDir --quiet

Write-Host "Creating zip file..." -ForegroundColor Yellow
if (Test-Path "lambda-deployment.zip") {
    Remove-Item "lambda-deployment.zip"
}
Compress-Archive -Path "$tempDir\*" -DestinationPath "lambda-deployment.zip" -Force

Write-Host "Cleaning up..." -ForegroundColor Yellow
Remove-Item -Recurse -Force $tempDir

Write-Host "✅ Lambda deployment package created: lambda-deployment.zip" -ForegroundColor Green
Write-Host "Package size: $([math]::Round((Get-Item lambda-deployment.zip).Length / 1MB, 2)) MB" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  IMPORTANT: Don't forget to add the cryptography Lambda Layer!" -ForegroundColor Yellow
Write-Host "See LAMBDA_LAYER_SETUP.md for instructions" -ForegroundColor Cyan
