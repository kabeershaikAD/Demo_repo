# Complete GitHub Push Script

Write-Host "========================================"
Write-Host "PEARL Project - GitHub Push"
Write-Host "========================================"
Write-Host ""

cd "C:\Users\Lenovo\Downloads\Collage_Materials\Major project\projects\slm_orchestration_legal_rag"

# Step 1: Verify config.py is ignored
Write-Host "[1/5] Verifying security..." -ForegroundColor Cyan
$currentConfig = "projects/slm_orchestration_legal_rag/config.py"
if (Test-Path $currentConfig) {
    $ignored = git check-ignore $currentConfig
    if ($ignored) {
        Write-Host "[OK] config.py is properly ignored" -ForegroundColor Green
    } else {
        Write-Host "[WARNING] config.py is NOT ignored!" -ForegroundColor Yellow
        Write-Host "Adding to .gitignore..." -ForegroundColor Yellow
        Add-Content -Path ".gitignore" -Value "`nconfig.py"
        git add .gitignore
    }
}

# Step 2: Add all files
Write-Host "`n[2/5] Staging files..." -ForegroundColor Cyan
git add .
$staged = (git diff --cached --name-only | Measure-Object).Count
Write-Host "[OK] $staged files staged" -ForegroundColor Green

# Step 3: Remove any config.py from staging (safety check)
Write-Host "`n[3/5] Security check..." -ForegroundColor Cyan
$configFiles = git diff --cached --name-only | Where-Object { $_ -like "*config.py" -and $_ -notlike "*example*" -and $_ -notlike "*slm_config.py" }
if ($configFiles) {
    Write-Host "[WARNING] Found config.py files in staging - removing..." -ForegroundColor Yellow
    $configFiles | ForEach-Object { git reset HEAD $_ }
    Write-Host "[OK] Removed config.py files from staging" -ForegroundColor Green
} else {
    Write-Host "[OK] No sensitive config files in staging" -ForegroundColor Green
}

# Step 4: Commit
Write-Host "`n[4/5] Committing changes..." -ForegroundColor Cyan
$commitMsg = "PEARL Framework Implementation Complete

- SLM orchestration with Flan-T5-small (80M params)
- Collected 1,200 GPT-4 expert traces
- Trained orchestrator model
- Evaluation with RAS/WAI metrics (300 queries)
- Base model: 14.0% RAS, 64.9% WAI
- GPT-4 ground truth validation: 95.3%
- Cleaned up redundant files
- Added .gitignore for security"

git commit -m $commitMsg

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Committed successfully" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Commit failed" -ForegroundColor Red
    exit 1
}

# Step 5: Push
Write-Host "`n[5/5] Pushing to GitHub..." -ForegroundColor Cyan
Write-Host "Remote: origin (https://github.com/kabeershaikAD/Demo_repo.git)" -ForegroundColor Cyan
Write-Host "Branch: clean-main" -ForegroundColor Cyan
Write-Host "`nRun this command to push:" -ForegroundColor Yellow
Write-Host "  git push origin clean-main" -ForegroundColor White
Write-Host "`nOr push now? (y/n): " -NoNewline -ForegroundColor Yellow
$response = Read-Host
if ($response -eq "y" -or $response -eq "Y") {
    git push origin clean-main
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n[OK] Pushed to GitHub successfully!" -ForegroundColor Green
    } else {
        Write-Host "`n[ERROR] Push failed. Check your credentials." -ForegroundColor Red
    }
} else {
    Write-Host "`n[INFO] Skipped push. Run 'git push origin clean-main' when ready." -ForegroundColor Cyan
}

Write-Host "`n========================================"
Write-Host "Done!" -ForegroundColor Green
Write-Host "========================================"

