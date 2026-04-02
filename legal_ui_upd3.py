# legal_ui_upd3.py - About section: Flan-T5-small/80M -> Flan-T5-base/250M (targeted)
path = r'projects\api_interfaces\ui\legal_ui.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('Flan-T5-small', 'Flan-T5-base')
content = content.replace('Flan-T5-base 80M', 'Flan-T5-base 250M')
content = content.replace('Flan-T5-base (80M)', 'Flan-T5-base (250M)')
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('legal_ui_upd3: About section updated')
