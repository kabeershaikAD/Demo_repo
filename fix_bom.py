import codecs

files = [
    'projects/slm_orchestration_legal_rag/slm_orchestration_app.py',
    'projects/api_interfaces/ui/legal_ui.py',
]

for f in files:
    with open(f, 'rb') as fh:
        raw = fh.read()
    # Strip BOM if present
    if raw.startswith(b'\xef\xbb\xbf'):
        raw = raw[3:]
        with open(f, 'wb') as fh:
            fh.write(raw)
        print(f'  Fixed BOM: {f}')
    else:
        print(f'  No BOM: {f}')

# Verify syntax
import ast
for f in files:
    with open(f, 'r', encoding='utf-8') as fh:
        code = fh.read()
    try:
        ast.parse(code)
        print(f'  Syntax OK: {f}')
    except SyntaxError as e:
        print(f'  SYNTAX ERROR: {f}: {e}')

# Also check UI file has the right content
with open('projects/api_interfaces/ui/legal_ui.py', 'r', encoding='utf-8') as fh:
    u = fh.read()
print(f'\n  Verification section: {"Verification Results" in u}')
print(f'  Web icon: {"is_web" in u}')
print(f'  Source link: {"Open Source Link" in u}')
