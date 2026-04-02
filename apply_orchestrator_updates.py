#!/usr/bin/env python3
"""Helper script to update orchestrator defaults and options in legal_ui.py and slm_orchestration_app.py"""

import re

LEGAL_UI_PATH = r"c:\Users\Lenovo\Downloads\Collage_Materials\Major project\projects\api_interfaces\ui\legal_ui.py"
SLM_APP_PATH = r"c:\Users\Lenovo\Downloads\Collage_Materials\Major project\projects\slm_orchestration_legal_rag\slm_orchestration_app.py"


def update_legal_ui():
    with open(LEGAL_UI_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Change default from iterative_small to flan_t5 everywhere
    content = content.replace('st.session_state.selected_orchestrator = "iterative_small"',
                              'st.session_state.selected_orchestrator = "flan_t5"')
    content = content.replace('st.session_state.get("selected_orchestrator", "iterative_small")',
                              'st.session_state.get("selected_orchestrator", "flan_t5")')
    content = content.replace('values.index(st.session_state.get("selected_orchestrator", "iterative_small"))',
                              'values.index(st.session_state.get("selected_orchestrator", "flan_t5"))')

    # 2. Update ORCH_OPTIONS dropdown
    old_options = '''        ORCH_OPTIONS = [
            ("Iterative SLM (trained 80M)", "iterative_small"),
            ("Flan-T5 classifier", "flan_t5"),
            ("Rule-based", "rule"),
            ("No orchestration", "none"),
            
        ]'''
    new_options = '''        ORCH_OPTIONS = [
            ("SLM Classifier (Flan-T5-base 250M)", "flan_t5"),
            ("Iterative SLM (80M)", "iterative_small"),
            ("Rule-based", "rule"),
            ("GPT-4 (reference)", "gpt4"),
            ("No orchestration", "none"),
        ]'''
    content = content.replace(old_options, new_options)

    # 3. Update _orch_label dict
    old_label = '{"iterative_small": "Iterative SLM (80M)", "flan_t5": "Flan-T5-small", "rule": "Rule-based", "none": "No orchestration"}'
    new_label = '{"iterative_small": "Iterative SLM (80M)", "flan_t5": "SLM Classifier (250M)", "rule": "Rule-based", "none": "No orchestration", "gpt4": "GPT-4 (reference)"}'
    content = content.replace(old_label, new_label)

    # 4. Update fallback in metric when orchestrator not in values
    content = content.replace('else "Iterative SLM"', 'else "SLM Classifier (250M)"')

    # 5. Sidebar About section: Flan-T5-small -> Flan-T5-base, 80M -> 250M for orchestrator
    content = content.replace(
        "This system uses a **Small Language Model (Flan-T5-small) Orchestrator** to intelligently control multiple agents:",
        "This system uses a **Small Language Model (Flan-T5-base) Orchestrator** to intelligently control multiple agents:"
    )
    content = content.replace(
        "- **SLM Orchestrator (Flan-T5-small)**: Analyzes queries and decides which agents to use",
        "- **SLM Orchestrator (Flan-T5-base 250M)**: Analyzes queries and decides which agents to use"
    )
    content = content.replace(
        "- **Prompt Booster Agent**: Enhances vague queries using Flan-T5-small",
        "- **Prompt Booster Agent**: Enhances vague queries using Flan-T5-base"
    )

    # Decision Model in expander
    content = content.replace(
        '"Decision Model": "Flan-T5-small (80M parameters)"',
        '"Decision Model": "Flan-T5-base (250M parameters)"'
    )

    with open(LEGAL_UI_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated legal_ui.py")


def update_slm_orchestration_app():
    with open(SLM_APP_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. ORCHESTRATOR_CHOICES - put flan_t5 first
    old_choices = '''ORCHESTRATOR_CHOICES = [
    "iterative_small", "iterative_base", "iterative_large",
    "flan_t5", "gpt4", "gpt35", "rule", "none",
]'''
    new_choices = '''ORCHESTRATOR_CHOICES = [
    "flan_t5", "iterative_small", "iterative_base", "iterative_large",
    "gpt4", "gpt35", "rule", "none",
]'''
    content = content.replace(old_choices, new_choices)

    # 2. __init__ default
    content = content.replace(
        'def __init__(self, orchestrator_type: str = "iterative_small"):',
        'def __init__(self, orchestrator_type: str = "flan_t5"):'
    )

    # 3. argparse default
    content = content.replace(
        'default="iterative_small",',
        'default="flan_t5",'
    )

    with open(SLM_APP_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated slm_orchestration_app.py")


if __name__ == "__main__":
    update_legal_ui()
    update_slm_orchestration_app()
    print("Done.")
