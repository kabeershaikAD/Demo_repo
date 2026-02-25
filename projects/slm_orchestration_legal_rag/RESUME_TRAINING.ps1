# Resume Training from Checkpoint-200
# This script resumes training from the checkpoint saved at step 200

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Resuming Training from Checkpoint-200" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to project directory
$projectDir = "C:\Users\Lenovo\Downloads\Collage_Materials\Major project\projects\slm_orchestration_legal_rag"
Set-Location $projectDir

# Check if checkpoint exists
$checkpointPath = "models\flan_t5_orchestrator\checkpoint-200"
if (Test-Path $checkpointPath) {
    Write-Host "[OK] Checkpoint found: $checkpointPath" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Checkpoint not found: $checkpointPath" -ForegroundColor Red
    Write-Host "Please verify the checkpoint path." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Resuming training with the following settings:" -ForegroundColor Yellow
Write-Host "  - Checkpoint: $checkpointPath" -ForegroundColor White
Write-Host "  - Epochs: 3 (will continue from where it stopped)" -ForegroundColor White
Write-Host "  - Batch Size: 8" -ForegroundColor White
Write-Host "  - Learning Rate: 5e-5" -ForegroundColor White
Write-Host ""
Write-Host "Estimated remaining time: ~1.5 hours (250 steps remaining)" -ForegroundColor Cyan
Write-Host ""

# Resume training
Write-Host "Starting training..." -ForegroundColor Green
Write-Host ""

python training/knowledge_distillation.py `
    --data data/expert_traces/training_data.jsonl `
    --output models/flan_t5_orchestrator `
    --epochs 3 `
    --batch_size 8 `
    --lr 5e-5 `
    --resume_from models/flan_t5_orchestrator/checkpoint-200

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Training Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan


