# What Happens If Training Is Stopped?

## ✅ Good News: Checkpoints Are Saved!

The training script is configured to **save checkpoints automatically**:

- **Save Frequency**: Every 100 steps (`save_steps=100`)
- **Checkpoint Location**: `models/flan_t5_orchestrator/checkpoint-XXX/`
- **Checkpoints Kept**: Last 3 checkpoints (`save_total_limit=3`)

---

## 📁 What Gets Saved

When training runs, checkpoints are saved to:
```
models/flan_t5_orchestrator/
├── checkpoint-100/     (after 100 steps)
├── checkpoint-200/     (after 200 steps)
├── checkpoint-300/     (after 300 steps)
└── checkpoint-400/     (after 400 steps - oldest gets deleted)
```

Each checkpoint contains:
- ✅ Model weights (`pytorch_model.bin`)
- ✅ Tokenizer files
- ✅ Training state (`trainer_state.json`)
- ✅ Optimizer state

---

## 🛑 If You Stop Training

### Scenario 1: Stop Mid-Training (Ctrl+C)

**What Happens**:
- ✅ Last checkpoint is saved (if it was time to save)
- ✅ Model weights up to that point are preserved
- ❌ Training doesn't complete
- ❌ Final model save might not happen

**What You Have**:
- Latest checkpoint (e.g., `checkpoint-300/`)
- Can use this checkpoint as the trained model
- Or resume training from this checkpoint

---

## 🔄 How to Resume Training

### Option 1: Resume from Checkpoint

The HuggingFace Trainer supports resuming. You would need to modify the script to add:

```python
trainer.train(resume_from_checkpoint="models/flan_t5_orchestrator/checkpoint-300")
```

**Note**: Current script doesn't have resume functionality built-in, but checkpoints are saved.

### Option 2: Use Latest Checkpoint as Final Model

If you stop training, you can use the latest checkpoint:

```python
from transformers import T5ForConditionalGeneration, T5Tokenizer

# Load from latest checkpoint
model = T5ForConditionalGeneration.from_pretrained("models/flan_t5_orchestrator/checkpoint-300")
tokenizer = T5Tokenizer.from_pretrained("models/flan_t5_orchestrator/checkpoint-300")

# Save as final model
model.save_pretrained("models/flan_t5_orchestrator")
tokenizer.save_pretrained("models/flan_t5_orchestrator")
```

---

## ⏱️ Checkpoint Schedule

With **450 total steps** (3 epochs × 150 steps/epoch):

| Step | Checkpoint | Progress | Time (approx) |
|------|-----------|----------|---------------|
| 100 | ✅ Saved | 22% | ~27 minutes |
| 200 | ✅ Saved | 44% | ~54 minutes |
| 300 | ✅ Saved | 67% | ~82 minutes |
| 400 | ✅ Saved | 89% | ~109 minutes |
| 450 | ✅ Final | 100% | ~122 minutes |

**Note**: Checkpoints are saved every 100 steps, so you won't lose more than ~27 minutes of progress.

---

## 💡 Best Practices

### 1. **Let It Complete** (Recommended)
- Full training takes ~2 hours
- You get the fully trained model
- All 3 epochs complete

### 2. **If You Must Stop**
- Wait for a checkpoint to save (every 100 steps)
- Note which checkpoint was last saved
- You can use that checkpoint as your model

### 3. **Monitor Progress**
- Watch the progress bar
- Checkpoints save at: 100, 200, 300, 400 steps
- Training completes at step 450

---

## 📊 What You Lose If You Stop

| If Stopped At | Checkpoint Available | Progress Lost | Can Resume? |
|---------------|---------------------|---------------|-------------|
| Step 50 | ❌ None yet | 50 steps | ❌ No |
| Step 150 | ✅ checkpoint-100 | 50 steps | ✅ Yes |
| Step 250 | ✅ checkpoint-200 | 50 steps | ✅ Yes |
| Step 350 | ✅ checkpoint-300 | 50 steps | ✅ Yes |

**Worst Case**: Lose up to 100 steps (~27 minutes) if stopped right before a checkpoint.

---

## ✅ Summary

**If Training Stops**:
- ✅ Checkpoints are saved every 100 steps
- ✅ You can use the latest checkpoint as your model
- ⚠️ You lose progress since last checkpoint (max 100 steps)
- ⚠️ Current script doesn't auto-resume (but checkpoints exist)

**Recommendation**: 
- **Best**: Let it complete (~2 hours)
- **If needed**: Stop after a checkpoint saves (steps 100, 200, 300, 400)
- **Use checkpoint**: Latest checkpoint can serve as your trained model

---

## 🔧 Future Improvement

To add resume functionality, modify the training script to:
1. Check for existing checkpoints
2. Resume from latest checkpoint if found
3. Continue training from that point

But for now, **checkpoints are saved automatically** - you won't lose everything! ✅



