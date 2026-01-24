#!/bin/bash
# Bash script to build Lambda deployment package
# Run this script from the project root directory

echo "Building Lambda deployment package..."

# Create temporary directory
TEMP_DIR="lambda-package-temp"
rm -rf "$TEMP_DIR"
mkdir "$TEMP_DIR"

echo "Copying Lambda function..."
cp lambda_function.py "$TEMP_DIR/"

echo "Copying coinbase_advanced_trader package..."
cp -r coinbase_advanced_trader "$TEMP_DIR/"

echo "Installing dependencies..."
pip install -r lambda-requirements.txt -t "$TEMP_DIR" --quiet

echo "Creating zip file..."
rm -f lambda-deployment.zip
cd "$TEMP_DIR"
zip -r ../lambda-deployment.zip . -q
cd ..

echo "Cleaning up..."
rm -rf "$TEMP_DIR"

echo "✅ Lambda deployment package created: lambda-deployment.zip"
echo "Package size: $(du -h lambda-deployment.zip | cut -f1)"
