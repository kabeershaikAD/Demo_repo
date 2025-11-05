# GitHub Push Script with Authentication
# This script will help you push to GitHub with proper authentication

Write-Host "🚀 GitHub Push Script" -ForegroundColor Green
Write-Host "====================" -ForegroundColor Green
Write-Host ""

$repoPath = "C:\Users\Lenovo\Downloads\Collage_Materials\Major project"
Set-Location $repoPath

# Check if we're in the right directory
if (-not (Test-Path ".git")) {
    Write-Host "❌ Error: Not a git repository!" -ForegroundColor Red
    exit 1
}

# Check remote
$remoteUrl = git remote get-url origin 2>$null
if (-not $remoteUrl) {
    Write-Host "❌ Error: No remote configured!" -ForegroundColor Red
    exit 1
}

Write-Host "📋 Repository: $remoteUrl" -ForegroundColor Cyan
Write-Host ""

# Check if already authenticated
Write-Host "Checking authentication..." -ForegroundColor Yellow
$testAuth = git ls-remote origin 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Already authenticated!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
    git push -u origin main
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Successfully pushed to GitHub!" -ForegroundColor Green
        Write-Host "View your repository at: https://github.com/shaik-kabeer/Major_project-" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "❌ Push failed. Please check the error above." -ForegroundColor Red
    }
    exit
}

# Need authentication
Write-Host "🔐 Authentication Required" -ForegroundColor Yellow
Write-Host ""
Write-Host "GitHub requires a Personal Access Token for authentication." -ForegroundColor Cyan
Write-Host ""
Write-Host "To get your token:" -ForegroundColor Yellow
Write-Host "1. Open: https://github.com/settings/tokens/new" -ForegroundColor Cyan
Write-Host "2. Token name: 'Major Project Push'" -ForegroundColor Cyan
Write-Host "3. Select scope: ✅ repo" -ForegroundColor Cyan
Write-Host "4. Click 'Generate token'" -ForegroundColor Cyan
Write-Host "5. COPY THE TOKEN (you won't see it again!)" -ForegroundColor Red
Write-Host ""

# Open browser to token page
$response = Read-Host "Open GitHub token page in browser? (Y/n)"
if ($response -ne "n" -and $response -ne "N") {
    Start-Process "https://github.com/settings/tokens/new"
    Write-Host ""
    Write-Host "✅ Opened browser. Please create your token." -ForegroundColor Green
}

Write-Host ""
Write-Host "After creating your token, you have two options:" -ForegroundColor Yellow
Write-Host ""
Write-Host "Option 1: Use token in URL (one-time)" -ForegroundColor Cyan
Write-Host "  git remote set-url origin https://YOUR_TOKEN@github.com/shaik-kabeer/Major_project-.git" -ForegroundColor Gray
Write-Host "  git push -u origin main" -ForegroundColor Gray
Write-Host ""
Write-Host "Option 2: Use token when prompted (recommended)" -ForegroundColor Cyan
Write-Host "  When prompted for username: shaik-kabeer" -ForegroundColor Gray
Write-Host "  When prompted for password: PASTE YOUR TOKEN" -ForegroundColor Gray
Write-Host ""

$token = Read-Host "Enter your GitHub Personal Access Token (or press Enter to try push with prompt)"

if ($token) {
    # Use token in URL
    Write-Host ""
    Write-Host "Setting up authentication..." -ForegroundColor Yellow
    git remote set-url origin "https://$token@github.com/shaik-kabeer/Major_project-.git"
    
    Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
    git push -u origin main
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Successfully pushed to GitHub!" -ForegroundColor Green
        Write-Host "View your repository at: https://github.com/shaik-kabeer/Major_project-" -ForegroundColor Cyan
        
        # Remove token from URL for security
        git remote set-url origin "https://github.com/shaik-kabeer/Major_project-.git"
        Write-Host ""
        Write-Host "🔒 Removed token from URL for security." -ForegroundColor Yellow
        Write-Host "Windows Credential Manager has saved your credentials." -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "❌ Push failed. Please check:" -ForegroundColor Red
        Write-Host "  - Token is correct and has repo scope" -ForegroundColor Yellow
        Write-Host "  - You have push access to the repository" -ForegroundColor Yellow
        Write-Host "  - Internet connection is working" -ForegroundColor Yellow
    }
} else {
    # Try push and let Windows prompt for credentials
    Write-Host ""
    Write-Host "Attempting push (Windows will prompt for credentials)..." -ForegroundColor Yellow
    Write-Host "When prompted:" -ForegroundColor Cyan
    Write-Host "  Username: shaik-kabeer" -ForegroundColor Gray
    Write-Host "  Password: YOUR_GITHUB_TOKEN (not your GitHub password!)" -ForegroundColor Gray
    Write-Host ""
    
    git push -u origin main
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Successfully pushed to GitHub!" -ForegroundColor Green
        Write-Host "View your repository at: https://github.com/shaik-kabeer/Major_project-" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "❌ Push failed. Please run this script again and provide your token." -ForegroundColor Red
    }
}

