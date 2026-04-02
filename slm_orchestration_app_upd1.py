# slm_orchestration_app_upd1.py - Put flan_t5 first in ORCHESTRATOR_CHOICES
path = r'projects\slm_orchestration_legal_rag\slm_orchestration_app.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()
old = '"iterative_small", "iterative_base", "iterative_large", "flan_t5"'
new = '"flan_t5", "iterative_small", "iterative_base", "iterative_large"'
if old in content:
    content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('slm_orchestration_app_upd1: ORCHESTRATOR_CHOICES updated')
else:
    print('slm_orchestration_app_upd1: flan_t5 already first (no change)')
