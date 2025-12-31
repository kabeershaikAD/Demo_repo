# PowerShell Script to Push Project to GitHub

Write-Host "========================================"
Write-Host "GitHub Push Script for PEARL Project"
Write-Host "========================================"
Write-Host ""

# Navigate to project directory
cd "C:\Users\Lenovo\Downloads\Collage_Materials\Major project\projects\slm_orchestration_legal_rag"

# Check git status
Write-Host "[1/4] Checking git status..." -ForegroundColor Cyan
git status --short | Select-Object -First 10

# Verify config.py is ignored
Write-Host "`n[2/4] Verifying config.py is ignored..." -ForegroundColor Cyan
$configIgnored = git check-ignore config.py
if ($configIgnored) {
    Write-Host "[OK] config.py is properly ignored (will NOT be committed)" -ForegroundColor Green
} else {
    Write-Host "[WARNING] config.py is NOT ignored! Check .gitignore" -ForegroundColor Yellow
    exit 1
}

# Add all files
Write-Host "`n[3/4] Adding files to staging..." -ForegroundColor Cyan
git add .
$stagedCount = (git diff --cached --name-only | Measure-Object).Count
Write-Host "[OK] $stagedCount files staged for commit" -ForegroundColor Green

# Show what will be committed (first 20 files)
Write-Host "`nFiles to be committed (first 20):" -ForegroundColor Cyan
git diff --cached --name-only | Select-Object -First 20

# Commit
Write-Host "`n[4/4] Committing changes..." -ForegroundColor Cyan
$commitMessage = @"
PEARL Framework Implementation Complete

- Implemented SLM orchestration with Flan-T5-small (80M params)
- Collected 1,200 GPT-4 expert traces for knowledge distillation
- Trained orchestrator model with balanced dataset
- Comprehensive evaluation with RAS/WAI metrics on 300 queries
- Base model performance: 14.0% RAS, 64.9% WAI
- GPT-4 ground truth validation: 95.3% accuracy
- Cleaned up redundant files and documentation
- Added proper .gitignore for security (API keys protected)
"@

git commit -m $commitMessage

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Changes committed successfully" -ForegroundColor Green
    Write-Host "`nNext step: Push to GitHub" -ForegroundColor Cyan
    Write-Host "Run: git push origin clean-main" -ForegroundColor Yellow
} else {
    Write-Host "[ERROR] Commit failed" -ForegroundColor Red
    exit 1
}

Write-Host "`n========================================"
Write-Host "Ready to push!" -ForegroundColor Green
Write-Host "========================================"

