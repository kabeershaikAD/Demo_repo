# legal_ui_upd1.py - Change default orchestrator from iterative_small to flan_t5
path = r'projects\api_interfaces\ui\legal_ui.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('st.session_state.selected_orchestrator = "iterative_small"', 'st.session_state.selected_orchestrator = "flan_t5"')
content = content.replace('get("selected_orchestrator", "iterative_small")', 'get("selected_orchestrator", "flan_t5")')
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('legal_ui_upd1: default orchestrator updated')
