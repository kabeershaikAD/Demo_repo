# Quick Push Script - Simple and Easy
# Just enter your token when asked, and you're done!

Write-Host "`n🚀 Quick GitHub Push`n" -ForegroundColor Green
Write-Host "You're pushing to: shaik-kabeer/Major_project-" -ForegroundColor Cyan
Write-Host "Your email: kabeer.shaik@adqura.com`n" -ForegroundColor Cyan

$repoPath = "C:\Users\Lenovo\Downloads\Collage_Materials\Major project"
Set-Location $repoPath

# Get token from user
Write-Host "To get your GitHub Personal Access Token:" -ForegroundColor Yellow
Write-Host "1. Open: https://github.com/settings/tokens/new" -ForegroundColor Cyan
Write-Host "2. Name: 'Major Project Push'" -ForegroundColor Cyan
Write-Host "3. Select: ✅ repo scope" -ForegroundColor Cyan
Write-Host "4. Click Generate, then COPY the token`n" -ForegroundColor Cyan

# Open browser to help
$open = Read-Host "Open GitHub token page in browser? (Y/n)"
if ($open -ne "n" -and $open -ne "N") {
    Start-Process "https://github.com/settings/tokens/new"
    Write-Host "`n✅ Browser opened. Create your token and come back here.`n" -ForegroundColor Green
}

Write-Host "Paste your token below (it will be hidden for security):" -ForegroundColor Yellow
$secureToken = Read-Host "Token" -AsSecureString
$token = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureToken))

if (-not $token) {
    Write-Host "`n❌ No token provided. Exiting." -ForegroundColor Red
    exit
}

Write-Host "`n📤 Setting up and pushing...`n" -ForegroundColor Yellow

# Update remote with token
git remote set-url origin "https://$token@github.com/shaik-kabeer/Major_project-.git"

# Push
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ SUCCESS! Code pushed to GitHub!`n" -ForegroundColor Green
    Write-Host "View your repo: https://github.com/shaik-kabeer/Major_project-" -ForegroundColor Cyan
    
    # Remove token from URL (Windows Credential Manager will remember it)
    git remote set-url origin "https://github.com/shaik-kabeer/Major_project-.git"
    Write-Host "`n🔒 Token removed from URL. Windows saved your credentials." -ForegroundColor Yellow
    Write-Host "✅ Next time you push, you won't need to enter the token again!`n" -ForegroundColor Green
} else {
    Write-Host "`n❌ Push failed. Please check:" -ForegroundColor Red
    Write-Host "  - Token is correct" -ForegroundColor Yellow
    Write-Host "  - Token has 'repo' scope" -ForegroundColor Yellow
    Write-Host "  - You have access to shaik-kabeer/Major_project-" -ForegroundColor Yellow
}





