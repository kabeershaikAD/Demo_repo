import ast

files = [
    'projects/slm_orchestration_legal_rag/answering_agent.py',
    'projects/slm_orchestration_legal_rag/slm_orchestration_app.py',
    'projects/slm_orchestration_legal_rag/retriever_agent.py',
    'projects/api_interfaces/ui/legal_ui.py',
]

for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as fh:
            ast.parse(fh.read())
        print(f'  OK: {f}')
    except SyntaxError as e:
        print(f'  SYNTAX ERROR in {f}: {e}')

with open('projects/slm_orchestration_legal_rag/answering_agent.py', 'r') as fh:
    a = fh.read()
    print(f'\n  _build_citations_from_docs present: {"_build_citations_from_docs" in a}')
    print(f'  sleep removed: {"_time.sleep(2)" not in a}')

with open('projects/slm_orchestration_legal_rag/slm_orchestration_app.py', 'r') as fh:
    s = fh.read()
    print(f'  claims_verified in return: {"claims_verified" in s}')

with open('projects/slm_orchestration_legal_rag/retriever_agent.py', 'r') as fh:
    r = fh.read()
    print(f'  Updated prompt: {"Do NOT refine" in r}')

with open('projects/api_interfaces/ui/legal_ui.py', 'r') as fh:
    u = fh.read()
    print(f'  Verification section: {"Verification Results" in u}')
    print(f'  Web icon: {"is_web" in u}')
    print(f'  Source link: {"Open Source Link" in u}')
