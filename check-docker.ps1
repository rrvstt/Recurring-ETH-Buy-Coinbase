# Check if Docker is available and running
Write-Host "Checking Docker installation..." -ForegroundColor Cyan

# Try to find Docker
$dockerPath = Get-Command docker -ErrorAction SilentlyContinue

if ($dockerPath) {
    Write-Host "✅ Docker found at: $($dockerPath.Source)" -ForegroundColor Green
    
    # Try to run docker ps to check if Docker daemon is running
    try {
        docker ps | Out-Null
        Write-Host "✅ Docker is running!" -ForegroundColor Green
        Write-Host ""
        Write-Host "You can now run: .\build-lambda-package-docker.ps1" -ForegroundColor Yellow
    } catch {
        Write-Host "❌ Docker is installed but not running." -ForegroundColor Red
        Write-Host "Please start Docker Desktop and wait for it to fully start." -ForegroundColor Yellow
        Write-Host "Look for the Docker whale icon in your system tray." -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ Docker not found in PATH." -ForegroundColor Red
    Write-Host ""
    Write-Host "Please:" -ForegroundColor Yellow
    Write-Host "1. Install Docker Desktop (if you only downloaded it)" -ForegroundColor White
    Write-Host "2. Start Docker Desktop" -ForegroundColor White
    Write-Host "3. Restart your PowerShell terminal" -ForegroundColor White
    Write-Host "4. Run this script again to verify" -ForegroundColor White
}
