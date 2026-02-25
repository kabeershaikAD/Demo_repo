# PowerShell script to train Flan-T5 model
# Run this from the project directory

python training/knowledge_distillation.py `
    --data data/expert_traces/training_data.jsonl `
    --output models/flan_t5_orchestrator `
    --epochs 3 `
    --batch_size 8 `
    --lr 5e-5



