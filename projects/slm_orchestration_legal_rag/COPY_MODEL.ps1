# Copy Trained Model to Another Location
# Usage: .\COPY_MODEL.ps1 -DestinationPath "C:\path\to\destination"

param(
    [Parameter(Mandatory=$true)]
    [string]$DestinationPath
)

$sourceDir = "models\flan_t5_orchestrator"
$destDir = $DestinationPath

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Copying Trained Model" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Source: $sourceDir" -ForegroundColor Yellow
Write-Host "Destination: $destDir" -ForegroundColor Yellow
Write-Host ""

# Verify source exists
if (-not (Test-Path $sourceDir)) {
    Write-Host "[ERROR] Source directory not found: $sourceDir" -ForegroundColor Red
    exit 1
}

# Create destination directory
New-Item -ItemType Directory -Path $destDir -Force | Out-Null

# Essential files
$files = @(
    "model.safetensors",
    "config.json",
    "tokenizer_config.json",
    "spiece.model",
    "special_tokens_map.json",
    "added_tokens.json",
    "generation_config.json"
)

$totalSize = 0
$copiedCount = 0

foreach ($file in $files) {
    $sourceFile = Join-Path $sourceDir $file
    $destFile = Join-Path $destDir $file
    
    if (Test-Path $sourceFile) {
        Copy-Item -Path $sourceFile -Destination $destFile -Force
        $size = (Get-Item $sourceFile).Length / 1MB
        $totalSize += $size
        $copiedCount++
        Write-Host "[OK] Copied $file ($([math]::Round($size, 2)) MB)" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] File not found: $file" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Copy Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Files copied: $copiedCount/$($files.Count)" -ForegroundColor White
Write-Host "Total size: $([math]::Round($totalSize, 2)) MB" -ForegroundColor Cyan
Write-Host ""
Write-Host "Model is ready to use at: $destDir" -ForegroundColor Green


