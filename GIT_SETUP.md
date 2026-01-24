# Git Repository Setup Guide

## Step 1: Install Git (if not already installed)

1. Download Git for Windows from: https://git-scm.com/download/win
2. Run the installer and follow the setup wizard
3. Restart your terminal/PowerShell after installation

## Step 2: Initialize Git Repository

After Git is installed, run these commands in PowerShell:

```powershell
cd "c:\Users\sandu\OneDrive\Documents\Cursor\CB\coinbase-advancedtrade-python-main"

# Initialize git repository
git init

# Configure your Git identity (if not already configured globally)
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Coinbase Advanced Trade Lambda function with daily ETH buy automation"
```

## Step 3: (Optional) Connect to Remote Repository

If you want to push to GitHub, GitLab, or another remote:

```powershell
# Add remote repository (replace with your repository URL)
git remote add origin https://github.com/yourusername/your-repo-name.git

# Push to remote
git branch -M main
git push -u origin main
```

## Important Notes

- The `.gitignore` file is already configured to exclude:
  - `.env` (contains sensitive API keys)
  - `lambda-deployment.zip` (build artifacts)
  - `lambda-package-temp/` (temporary build files)
  - Python cache files and virtual environments

- **Never commit `.env`** - it contains your Coinbase API credentials!

## Useful Git Commands

```powershell
# Check status
git status

# View commit history
git log

# Create a new branch
git checkout -b feature-name

# Switch branches
git checkout main

# View differences
git diff
```
