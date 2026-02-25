# Install dependencies for training Flan-T5 model
# Run this in your virtual environment

Write-Host "Installing PyTorch and Transformers..." -ForegroundColor Green

# Install PyTorch (CPU version - works on all systems)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install Transformers and related packages
pip install transformers>=4.35.0
pip install datasets accelerate
pip install sentencepiece protobuf

Write-Host "`n✅ Installation complete!" -ForegroundColor Green
Write-Host "You can now run training with:" -ForegroundColor Yellow
Write-Host "python training/knowledge_distillation.py --data data/expert_traces/training_data.jsonl --output models/flan_t5_orchestrator --epochs 3 --batch_size 8 --lr 5e-5" -ForegroundColor Cyan



