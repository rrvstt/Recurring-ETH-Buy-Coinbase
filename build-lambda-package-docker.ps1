# PowerShell script to build Lambda deployment package using Docker
# This ensures dependencies are built for Linux (Lambda's runtime environment)
# Requires Docker Desktop to be installed and running

Write-Host "Building Lambda deployment package using Docker (Linux-compatible)..." -ForegroundColor Green

# Check if Docker is running
try {
    docker ps | Out-Null
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

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

Write-Host "Installing dependencies in Docker (Linux environment)..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Cyan

# Use Docker to install dependencies in a Linux environment
# Override entrypoint to run pip directly
docker run --rm --entrypoint="" -v "${PWD}\lambda-package-temp:/var/task" -v "${PWD}\lambda-requirements.txt:/var/requirements.txt" public.ecr.aws/lambda/python:3.11 /var/lang/bin/python3.11 -m pip install -r /var/requirements.txt -t /var/task --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install dependencies. Cleaning up..." -ForegroundColor Red
    Remove-Item -Recurse -Force $tempDir
    exit 1
}

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
Write-Host "Note: This package is now Linux-compatible for AWS Lambda!" -ForegroundColor Green
