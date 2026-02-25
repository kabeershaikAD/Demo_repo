# Training Setup - Install Dependencies

## 🔧 Required Dependencies

The training script needs PyTorch and Transformers libraries.

### Install Dependencies

```powershell
# Activate your virtual environment first
# (legal_rag_env) PS> 

# Install PyTorch (CPU version - lighter)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Or if you have CUDA GPU:
# pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install Transformers and other dependencies
pip install transformers datasets accelerate
pip install sentencepiece protobuf
```

### Quick Install (All at Once)

```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install transformers datasets accelerate sentencepiece protobuf
```

---

## ✅ Verify Installation

```powershell
python -c "import torch; import transformers; print('✅ PyTorch:', torch.__version__); print('✅ Transformers:', transformers.__version__)"
```

---

## 🚀 After Installation, Run Training

```powershell
python training/knowledge_distillation.py --data data/expert_traces/training_data.jsonl --output models/flan_t5_orchestrator --epochs 3 --batch_size 8 --lr 5e-5
```

---

## 📝 Note

- **CPU Training**: Works but slower (~1-2 hours)
- **GPU Training**: Much faster (~20-30 minutes) if you have CUDA
- **Memory**: Needs ~4-8GB RAM for Flan-T5-small

---

**Install dependencies first, then run training!** 🚀



