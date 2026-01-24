# Publishing to GitHub

## Option 1: Using GitHub CLI (gh) - Recommended

If you have GitHub CLI installed:

```powershell
# Create repository on GitHub (will prompt for visibility: public/private)
gh repo create coinbase-advancedtrade-python --source=. --public --push

# Or for private repository:
gh repo create coinbase-advancedtrade-python --source=. --private --push
```

## Option 2: Manual Steps

### Step 1: Create Repository on GitHub

1. Go to https://github.com/new
2. Repository name: `coinbase-advancedtrade-python` (or your preferred name)
3. Choose **Public** or **Private**
4. **DO NOT** initialize with README, .gitignore, or license (we already have these)
5. Click **Create repository**

### Step 2: Add Remote and Push

After creating the repository, GitHub will show you commands. Run these in PowerShell:

```powershell
cd "c:\Users\sandu\OneDrive\Documents\Cursor\CB\coinbase-advancedtrade-python-main"

# Refresh PATH to include Git
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/coinbase-advancedtrade-python.git

# Rename branch to main (GitHub's default)
git branch -M main

# Push to GitHub
git push -u origin main
```

### Step 3: Verify

Visit your repository URL:
```
https://github.com/YOUR_USERNAME/coinbase-advancedtrade-python
```

## Option 3: Use the Automated Script

Run the `publish-to-github.ps1` script (see below) which will guide you through the process.

## Security Reminder

✅ **Already protected:** Your `.gitignore` excludes:
- `.env` (API credentials)
- `lambda-deployment.zip` (build artifacts)
- Other sensitive files

⚠️ **Double-check before pushing:** Make sure `.env` is NOT in the repository:
```powershell
git ls-files | Select-String ".env"
```
If `.env` appears, it's already committed and you should remove it:
```powershell
git rm --cached .env
git commit -m "Remove .env file"
```
