# GitHub Publishing Script
# This script helps you publish your repository to GitHub

Write-Host "GitHub Publishing Script" -ForegroundColor Green
Write-Host "========================" -ForegroundColor Green

# Refresh PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Check if git is available
try {
    $gitVersion = git --version
    Write-Host "`nGit found: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Git is not installed or not in PATH." -ForegroundColor Red
    exit 1
}

# Navigate to project directory
$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectDir

# Check if .env is tracked (should not be)
Write-Host "`nChecking for sensitive files..." -ForegroundColor Cyan
$envFiles = git ls-files | Select-String ".env"
if ($envFiles) {
    Write-Host "WARNING: .env file is tracked in Git!" -ForegroundColor Red
    Write-Host "This file contains your API credentials and should NOT be published." -ForegroundColor Yellow
    Write-Host "`nTo remove it:" -ForegroundColor Yellow
    Write-Host "  git rm --cached .env" -ForegroundColor Gray
    Write-Host "  git commit -m 'Remove .env file'" -ForegroundColor Gray
    Write-Host "`nPress Enter to continue anyway, or Ctrl+C to cancel..." -ForegroundColor Yellow
    Read-Host
} else {
    Write-Host "✅ .env file is properly excluded" -ForegroundColor Green
}

# Check current branch
$currentBranch = git branch --show-current
Write-Host "`nCurrent branch: $currentBranch" -ForegroundColor Cyan

# Check if remote exists
$remote = git remote get-url origin 2>$null
if ($remote) {
    Write-Host "`nRemote repository already configured: $remote" -ForegroundColor Yellow
    $push = Read-Host "Push to existing remote? (y/n)"
    if ($push -eq 'y' -or $push -eq 'Y') {
        Write-Host "`nPushing to GitHub..." -ForegroundColor Cyan
        git push -u origin $currentBranch
        Write-Host "`n✅ Successfully pushed to GitHub!" -ForegroundColor Green
        exit 0
    }
}

# Get repository details
Write-Host "`nGitHub Repository Setup" -ForegroundColor Cyan
Write-Host "========================" -ForegroundColor Cyan
Write-Host "`nBefore continuing, make sure you have:" -ForegroundColor Yellow
Write-Host "1. Created a repository on GitHub (https://github.com/new)" -ForegroundColor Gray
Write-Host "2. Chosen a repository name" -ForegroundColor Gray
Write-Host "3. Decided if it should be Public or Private" -ForegroundColor Gray
Write-Host "`nDO NOT initialize the repository with README, .gitignore, or license!" -ForegroundColor Yellow

$repoName = Read-Host "`nEnter your GitHub repository name (e.g., coinbase-advancedtrade-python)"
$username = Read-Host "Enter your GitHub username"

if (-not $repoName -or -not $username) {
    Write-Host "Repository name and username are required!" -ForegroundColor Red
    exit 1
}

$repoUrl = "https://github.com/$username/$repoName.git"
Write-Host "`nRepository URL: $repoUrl" -ForegroundColor Cyan

# Add remote
Write-Host "`nAdding remote repository..." -ForegroundColor Cyan
git remote add origin $repoUrl

# Rename branch to main if needed
if ($currentBranch -ne "main") {
    Write-Host "`nRenaming branch from $currentBranch to main..." -ForegroundColor Cyan
    git branch -M main
    $currentBranch = "main"
}

# Push to GitHub
Write-Host "`nPushing to GitHub..." -ForegroundColor Cyan
try {
    git push -u origin $currentBranch
    Write-Host "`n✅ Successfully published to GitHub!" -ForegroundColor Green
    Write-Host "`nRepository URL: https://github.com/$username/$repoName" -ForegroundColor Cyan
} catch {
    Write-Host "`n❌ Error pushing to GitHub" -ForegroundColor Red
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "1. Repository doesn't exist - create it at https://github.com/new" -ForegroundColor Gray
    Write-Host "2. Authentication required - you may need to use a Personal Access Token" -ForegroundColor Gray
    Write-Host "3. Wrong repository URL - check the username and repository name" -ForegroundColor Gray
    Write-Host "`nYou can manually push using:" -ForegroundColor Yellow
    Write-Host "  git push -u origin $currentBranch" -ForegroundColor Gray
}
