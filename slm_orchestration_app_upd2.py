# slm_orchestration_app_upd2.py - Change default from iterative_small to flan_t5
path = r'projects\slm_orchestration_legal_rag\slm_orchestration_app.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('orchestrator_type: str = "iterative_small"', 'orchestrator_type: str = "flan_t5"')
content = content.replace('default="iterative_small"', 'default="flan_t5"')
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('slm_orchestration_app_upd2: defaults updated')
