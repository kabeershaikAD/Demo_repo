# Training Flan-T5 Model - Instructions

## ✅ Trace Collection Complete!

You have **1,200 expert traces** ready for training.

---

## 🚀 Training Command

### Option 1: Single Line (Easiest for PowerShell)

```powershell
python training/knowledge_distillation.py --data data/expert_traces/training_data.jsonl --output models/flan_t5_orchestrator --epochs 3 --batch_size 8 --lr 5e-5
```

### Option 2: PowerShell with Backticks (Multi-line)

```powershell
python training/knowledge_distillation.py `
    --data data/expert_traces/training_data.jsonl `
    --output models/flan_t5_orchestrator `
    --epochs 3 `
    --batch_size 8 `
    --lr 5e-5
```

### Option 3: Use the Script File

```powershell
.\TRAIN_MODEL.ps1
```

---

## 📋 Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `--data` | `data/expert_traces/training_data.jsonl` | Training data (1,200 examples) |
| `--output` | `models/flan_t5_orchestrator` | Where to save trained model |
| `--epochs` | `3` | Number of training epochs |
| `--batch_size` | `8` | Batch size for training |
| `--lr` | `5e-5` | Learning rate (0.00005) |

---

## ⏱️ Expected Training Time

- **With GPU**: ~20-30 minutes
- **CPU Only**: ~1-2 hours

---

## 📊 Expected Results

After training with 1,200 traces:

| Metric | Before (10 traces) | Expected After |
|--------|---------------------|----------------|
| **RAS** | 35.7% | **70-85%** |
| **WAI** | 88.6% | **90-93%** |

---

## ✅ What to Expect

1. **Loading**: Model and data loading
2. **Training**: 3 epochs with progress bars
3. **Saving**: Model saved to `models/flan_t5_orchestrator/`
4. **Completion**: Training complete message

---

## 🎯 Next Steps After Training

1. **Evaluate Model**:
   ```powershell
   python evaluation/run_orchestration_evaluation.py
   ```

2. **Test with Sample Queries**:
   ```powershell
   python slm_orchestration_app.py
   ```

---

**Ready to train! Use the single-line command above.** 🚀



