# legal_ui_upd2.py - Update dropdown: SLM Classifier (Flan-T5-base 250M) for flan_t5
path = r'projects\api_interfaces\ui\legal_ui.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()
old_opts = [
    ('("Flan-T5-small (80M)", "flan_t5")', '("SLM Classifier (Flan-T5-base 250M)", "flan_t5")'),
    ('("SLM Classifier (Flan-T5-small 80M)", "flan_t5")', '("SLM Classifier (Flan-T5-base 250M)", "flan_t5")'),
]
for old, new in old_opts:
    content = content.replace(old, new)
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('legal_ui_upd2: dropdown options updated')
