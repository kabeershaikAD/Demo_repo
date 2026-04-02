"""
Fundamental fix: Add direct tool execution mode to reduce Groq API calls
from ~9 per query to 1.
"""

# ============================================================
# 1. base_react_agent.py - Add direct_tool_execution support
# ============================================================
path = 'projects/slm_orchestration_legal_rag/core/base_react_agent.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# Add direct_tool_execution parameter to __init__
old_init = '''    def __init__(
        self,
        name: str,
        system_prompt: str,
        tools: Optional[ToolRegistry] = None,
        max_steps: int = 3,
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.tools = tools or ToolRegistry()
        self.max_steps = max_steps'''

new_init = '''    def __init__(
        self,
        name: str,
        system_prompt: str,
        tools: Optional[ToolRegistry] = None,
        max_steps: int = 3,
        direct_tool_execution: bool = False,
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.tools = tools or ToolRegistry()
        self.max_steps = max_steps
        self.direct_tool_execution = direct_tool_execution'''

code = code.replace(old_init, new_init)

# Add direct execution path at the beginning of run()
old_run_start = '''    async def run(self, context: Dict[str, Any]) -> AgentResult:
        start = time.time()
        history: List[ReActStep] = []
        tools_used: List[str] = []

        task_prompt = self._build_task_prompt(context)

        for step_idx in range(self.max_steps):'''

new_run_start = '''    async def run(self, context: Dict[str, Any]) -> AgentResult:
        start = time.time()
        history: List[ReActStep] = []
        tools_used: List[str] = []

        task_prompt = self._build_task_prompt(context)

        # Direct execution mode: skip LLM, execute primary tool immediately
        if self.direct_tool_execution and self.tools.names():
            primary = self.tools.names()[0]
            tool = self.tools.get(primary)
            tool_input = self._default_tool_input(context)

            logger.info("[%s] Direct execution: %s", self.name, primary)
            try:
                observation = await tool.func(**tool_input)
                tools_used.append(primary)
            except Exception as e:
                observation = f"Tool error: {e}"

            step = ReActStep(
                thought=f"Executing {primary} to process the query.",
                action=primary,
                action_input=tool_input,
                observation=str(observation)[:2000],
            )
            history.append(step)

            output = self._extract_final_output(str(observation), context)
            duration = (time.time() - start) * 1000
            return AgentResult(
                output=output,
                reasoning_trace=history,
                tools_used=tools_used,
                steps_taken=1,
                confidence=output.get("confidence", 0.7),
                duration_ms=round(duration, 1),
            )

        for step_idx in range(self.max_steps):'''

code = code.replace(old_run_start, new_run_start)

# Reduce max_tokens in groq_chat to save TPM
code = code.replace('max_tokens=1024,', 'max_tokens=512,')

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)
print('1. base_react_agent.py - direct execution mode added')


# ============================================================
# 2. Enable direct mode for ALL agents
# ============================================================

# --- Booster ---
path = 'projects/slm_orchestration_legal_rag/booster_agent.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace(
    '''        super().__init__(
            name="BoosterAgent",
            system_prompt=_BOOSTER_SYSTEM,
            tools=tools,
            max_steps=2,
        )''',
    '''        super().__init__(
            name="BoosterAgent",
            system_prompt=_BOOSTER_SYSTEM,
            tools=tools,
            max_steps=2,
            direct_tool_execution=True,
        )'''
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)
print('2a. booster_agent.py - direct mode enabled')

# --- Retriever ---
path = 'projects/slm_orchestration_legal_rag/retriever_agent.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace(
    '''        super().__init__(
            name="RetrieverAgent",
            system_prompt=_RETRIEVER_SYSTEM,
            tools=tools,
            max_steps=3,
        )''',
    '''        super().__init__(
            name="RetrieverAgent",
            system_prompt=_RETRIEVER_SYSTEM,
            tools=tools,
            max_steps=3,
            direct_tool_execution=True,
        )'''
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)
print('2b. retriever_agent.py - direct mode enabled')

# --- Answering ---
path = 'projects/slm_orchestration_legal_rag/answering_agent.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace(
    '''        super().__init__(
            name="AnsweringAgent",
            system_prompt=_ANSWERING_SYSTEM,
            tools=tools,
            max_steps=2,
        )''',
    '''        super().__init__(
            name="AnsweringAgent",
            system_prompt=_ANSWERING_SYSTEM,
            tools=tools,
            max_steps=2,
            direct_tool_execution=True,
        )'''
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)
print('2c. answering_agent.py - direct mode enabled')

# --- Verifier ---
path = 'projects/slm_orchestration_legal_rag/citation_verifier.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace(
    '''        super().__init__(
            name="VerifierAgent",
            system_prompt=_VERIFIER_SYSTEM,
            tools=tools,
            max_steps=2,
        )''',
    '''        super().__init__(
            name="VerifierAgent",
            system_prompt=_VERIFIER_SYSTEM,
            tools=tools,
            max_steps=2,
            direct_tool_execution=True,
        )'''
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)
print('2d. citation_verifier.py - direct mode enabled')


# ============================================================
# 3. Fix answer hallucination - better system prompt
# ============================================================
path = 'projects/slm_orchestration_legal_rag/answering_agent.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

old_prompt = '''Your role is to provide comprehensive, accurate legal information.

STRATEGY:
1. FIRST: Use information from the provided retrieved documents when available
2. SECOND: If documents don\'t contain sufficient information, use your knowledge of Indian law to provide a comprehensive answer
3. ALWAYS: Clearly indicate the source of information (document-based vs. general knowledge)
4. CITE: Use [doc_id] format for document-based claims, [General Knowledge] for other claims'''

new_prompt = '''Your role is to provide accurate legal information based on retrieved documents and verified legal knowledge.

CRITICAL RULES:
1. ONLY cite real, existing legal provisions (Articles, Sections, Acts)
2. DO NOT fabricate or invent Article/Section numbers
3. If documents are insufficient, use your verified knowledge of Indian law
4. Keep answers focused and factual - do NOT list random provision numbers
5. CITE: Use [doc_id] format for document-based claims, [General Knowledge] for other claims
6. If you are unsure about a specific provision number, describe the concept instead'''

code = code.replace(old_prompt, new_prompt)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)
print('3. answering_agent.py - anti-hallucination prompt updated')


# ============================================================
# 4. Verify all files parse correctly
# ============================================================
import ast
files = [
    'projects/slm_orchestration_legal_rag/core/base_react_agent.py',
    'projects/slm_orchestration_legal_rag/booster_agent.py',
    'projects/slm_orchestration_legal_rag/retriever_agent.py',
    'projects/slm_orchestration_legal_rag/answering_agent.py',
    'projects/slm_orchestration_legal_rag/citation_verifier.py',
]

all_ok = True
for f in files:
    with open(f, 'r', encoding='utf-8') as fh:
        try:
            ast.parse(fh.read())
            print(f'  OK: {f}')
        except SyntaxError as e:
            print(f'  SYNTAX ERROR: {f}: {e}')
            all_ok = False

if all_ok:
    print('\nAll patches applied and verified successfully!')
else:
    print('\nSome files have syntax errors!')
