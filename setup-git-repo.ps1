# Git Repository Setup Script
# Run this script after installing Git for Windows

Write-Host "Setting up Git repository..." -ForegroundColor Green

# Check if git is available
try {
    $gitVersion = git --version
    Write-Host "Git found: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Git is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please install Git from: https://git-scm.com/download/win" -ForegroundColor Yellow
    Write-Host "After installation, restart PowerShell and run this script again." -ForegroundColor Yellow
    exit 1
}

# Navigate to project directory
$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectDir

# Initialize git repository
Write-Host "`nInitializing Git repository..." -ForegroundColor Cyan
git init

# Check if user name/email are configured
$userName = git config user.name
$userEmail = git config user.email

if (-not $userName -or -not $userEmail) {
    Write-Host "`nGit user identity not configured." -ForegroundColor Yellow
    Write-Host "Please configure your Git identity:" -ForegroundColor Yellow
    Write-Host "  git config user.name `"Your Name`"" -ForegroundColor Gray
    Write-Host "  git config user.email `"your.email@example.com`"" -ForegroundColor Gray
    Write-Host "`nOr configure globally:" -ForegroundColor Yellow
    Write-Host "  git config --global user.name `"Your Name`"" -ForegroundColor Gray
    Write-Host "  git config --global user.email `"your.email@example.com`"" -ForegroundColor Gray
    Write-Host "`nPress Enter after configuring to continue..." -ForegroundColor Yellow
    Read-Host
}

# Add all files
Write-Host "`nAdding files to Git..." -ForegroundColor Cyan
git add .

# Show what will be committed
Write-Host "`nFiles staged for commit:" -ForegroundColor Cyan
git status --short

# Create initial commit
Write-Host "`nCreating initial commit..." -ForegroundColor Cyan
$commitMessage = "Initial commit: Coinbase Advanced Trade Lambda function with daily ETH buy automation"
git commit -m $commitMessage

Write-Host "`n✅ Git repository initialized successfully!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. (Optional) Add a remote repository:" -ForegroundColor Gray
Write-Host "   git remote add origin https://github.com/yourusername/your-repo-name.git" -ForegroundColor DarkGray
Write-Host "2. (Optional) Push to remote:" -ForegroundColor Gray
Write-Host "   git push -u origin main" -ForegroundColor DarkGray
Write-Host "`nView commit history:" -ForegroundColor Gray
Write-Host "   git log" -ForegroundColor DarkGray
