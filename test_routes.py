import torch, sys
from transformers import T5ForConditionalGeneration, T5Tokenizer
from pathlib import Path

model_path = Path('projects/slm_orchestration_legal_rag/models/flan_t5_orchestrator')
tokenizer = T5Tokenizer.from_pretrained('google/flan-t5-small')
model = T5ForConditionalGeneration.from_pretrained(str(model_path))
model.eval()

TOKEN_MAP = {650: 'simple', 17087: 'verified', 8358: 'enhanced', 423: 'full_pipeline'}
ROUTES = {
    'simple': 'retriever -> answering',
    'verified': 'retriever -> answering -> verifier',
    'enhanced': 'booster -> retriever -> answering',
    'full_pipeline': 'booster -> retriever -> answering -> verifier',
}

queries = [
    'What is Article 21?',
    'What is Section 302 IPC?',
    'Define habeas corpus',
    'What are fundamental rights?',
    'bail',
    'rights',
    'help me understand dowry law',
    'tenant eviction rules',
    'What are the legal precedents for Article 21?',
    'Analyze the implications of Section 498A IPC on matrimonial disputes',
    'Compare Article 14 and Article 19 of the Constitution',
    'What are the differences between CrPC and BNSS',
    'Evaluate Supreme Court interpretation of right to privacy under Article 21',
    'Is Section 377 still valid after Navtej Singh Johar judgment?',
    'How does anticipatory bail work under Section 438 CrPC?',
    'What is the punishment for cybercrime under IT Act 2000?',
    'Explain the doctrine of basic structure',
    'What remedies are available under consumer protection act?',
]

print(f'{"CLASS":<15} {"ROUTE":<45} {"QUERY"}')
print('-' * 120)
for q in queries:
    prompt = 'classify: ' + q
    inputs = tokenizer(prompt, return_tensors='pt', max_length=256, truncation=True)
    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=4, num_beams=4, early_stopping=True, do_sample=False)
    token_id = outputs[0][1].item()
    label = TOKEN_MAP.get(token_id, 'unknown(' + str(token_id) + ')')
    route = ROUTES.get(label, '?')
    print(f'{label:<15} {route:<45} {q}')
