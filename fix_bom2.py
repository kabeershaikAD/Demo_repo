bom = b'\xef\xbb\xbf'
files = [
    "projects/slm_orchestration_legal_rag/core/base_react_agent.py",
    "projects/slm_orchestration_legal_rag/citation_verifier.py",
]
for f in files:
    with open(f, "rb") as fh:
        raw = fh.read()
    if raw.startswith(bom):
        with open(f, "wb") as fh:
            fh.write(raw[3:])
        print(f"Fixed BOM: {f}")
    else:
        print(f"No BOM: {f}")
import ast
for f in files:
    with open(f, "r", encoding="utf-8") as fh:
        ast.parse(fh.read())
    print(f"Syntax OK: {f}")
