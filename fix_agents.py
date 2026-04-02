import pathlib

BASE = pathlib.Path(r'projects/slm_orchestration_legal_rag')

# 1. Fix base_react_agent.py
p = BASE / 'core' / 'base_react_agent.py'
c = p.read_text(encoding='utf-8')

# 1a) Throttle Groq calls with 1s delay
c = c.replace(
    'return resp.choices[0].message.content.strip()',
    'text = resp.choices[0].message.content.strip()\n        time.sleep(1.0)\n        return text',
)
print('  throttle:', 'time.sleep' in c)

# 1b) Force Final Answer on last step
old_block = '            user_msg = self._compose_user_message(task_prompt, history)\n            sys_msg = self._compose_system_message()'
new_block = (
    '            user_msg = self._compose_user_message(task_prompt, history)\n'
    '\n'
    '            if step_idx == self.max_steps - 1 and history:\n'
    '                user_msg += (\n'
    '                    "\\n\\nCRITICAL: This is your FINAL step. You MUST respond "\n'
    '                    "with Final Answer: now. Summarize your results as JSON."\n'
    '                )\n'
    '\n'
    '            sys_msg = self._compose_system_message()'
)
c = c.replace(old_block, new_block)
print('  force final:', 'CRITICAL: This is your FINAL' in c)

# 1c) System prompt - emphasize early finish
old_imp = '"IMPORTANT: Always start with Thought. "\n            "Action Input and Final Answer MUST be valid JSON."'
new_imp = (
    '"IMPORTANT: Always start with Thought. "\n'
    '            "Action Input and Final Answer MUST be valid JSON. "\n'
    '            "Prefer finishing in 1-2 steps. Use Final Answer as soon as "\n'
    '            "you have adequate results."'
)
c = c.replace(old_imp, new_imp)
print('  prompt:', 'Prefer finishing' in c)

p.write_text(c, encoding='utf-8')
print('[OK] base_react_agent.py')

# 2. Reduce max_steps
changes = {
    'retriever_agent.py':   ('max_steps=3,', 'max_steps=2,'),
    'answering_agent.py':   ('max_steps=4,', 'max_steps=2,'),
    'booster_agent.py':     ('max_steps=3,', 'max_steps=2,'),
    'citation_verifier.py': ('max_steps=3,', 'max_steps=2,'),
}
for fname, (old, new) in changes.items():
    fp = BASE / fname
    txt = fp.read_text(encoding='utf-8')
    if old in txt:
        txt = txt.replace(old, new, 1)
        fp.write_text(txt, encoding='utf-8')
        print(f'[OK] {fname}  ({old} -> {new})')
    else:
        print(f'[SKIP] {fname}  (not found)')

# 3. Better retriever task prompt
fp = BASE / 'retriever_agent.py'
txt = fp.read_text(encoding='utf-8')
old_rp = 'f"Search, evaluate the results, and refine if needed."'
new_rp = (
    'f"Search once. If results look reasonable, immediately give "\n'
    '            f"Final Answer with the documents. Only refine if nothing was found."'
)
if old_rp in txt:
    txt = txt.replace(old_rp, new_rp)
    fp.write_text(txt, encoding='utf-8')
    print('[OK] retriever task prompt')
else:
    print('[SKIP] retriever task prompt')

# 4. Better answering task prompt
fp = BASE / 'answering_agent.py'
txt = fp.read_text(encoding='utf-8')
old_ap = 'f"Draft an answer, check its coverage, and refine if needed."'
new_ap = (
    'f"Draft an answer, then immediately provide Final Answer. "\n'
    '            f"Only refine if the draft is clearly incomplete."'
)
if old_ap in txt:
    txt = txt.replace(old_ap, new_ap)
    fp.write_text(txt, encoding='utf-8')
    print('[OK] answering task prompt')
else:
    print('[SKIP] answering task prompt')

print('\n=== All fixes applied ===')
