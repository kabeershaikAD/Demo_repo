"""
PEARL Framework - SLM Orchestration Legal RAG System
"""
import streamlit as st
import asyncio
import json
import sys
import os
from datetime import datetime
import random

_script_dir = os.path.dirname(os.path.abspath(__file__))
_repo_root = os.path.abspath(os.path.join(_script_dir, '..', '..', '..'))
slm_project_path = os.path.join(_repo_root, 'projects', 'slm_orchestration_legal_rag')
if not os.path.isdir(slm_project_path):
    slm_project_path = os.path.join(os.getcwd(), 'projects', 'slm_orchestration_legal_rag')
sys.path.insert(0, slm_project_path)

from slm_orchestration_app import SLMOrchestrationApp

st.set_page_config(page_title="PEARL | Legal RAG", page_icon="\u2696", layout="wide", initial_sidebar_state="expanded")

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
:root{
--pri:#4A6FA5;--pri-l:#EBF0F7;--pri-d:#34506F;
--acc:#10B981;--acc-l:#ECFDF5;
--sf:#FFFFFF;--bg:#F4F6FA;
--tx:#1E293B;--tx2:#64748B;--bd:#E2E8F0;
--sh:0 1px 3px rgba(0,0,0,.06),0 1px 2px rgba(0,0,0,.04);
--sh2:0 4px 12px rgba(0,0,0,.07);--r:12px;
}
html,body,[class*="css"]{font-family:'Inter',-apple-system,BlinkMacSystemFont,sans-serif}
.main .block-container{padding-top:2rem;padding-bottom:2rem;max-width:1200px}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#2D3A4E 0%,#1E293B 100%);color:#CBD5E1}
section[data-testid="stSidebar"] .stMarkdown p,section[data-testid="stSidebar"] .stMarkdown li,section[data-testid="stSidebar"] label{color:#CBD5E1!important}
section[data-testid="stSidebar"] h1,section[data-testid="stSidebar"] h2,section[data-testid="stSidebar"] h3{color:#F1F5F9!important}
section[data-testid="stSidebar"] .stSelectbox label{color:#94A3B8!important;font-size:.8rem;text-transform:uppercase;letter-spacing:.05em}
header[data-testid="stHeader"]{background:transparent}
.ph{background:linear-gradient(135deg,#4A6FA5 0%,#6B8CC7 50%,#8FA8D9 100%);border-radius:16px;padding:2rem 2.5rem;margin-bottom:1.75rem;color:#fff;position:relative;overflow:hidden}
.ph::before{content:'';position:absolute;top:-50%;right:-20%;width:400px;height:400px;background:rgba(255,255,255,.06);border-radius:50%}
.ph h1{color:#fff!important;font-size:1.8rem!important;font-weight:700!important;margin-bottom:.3rem!important;letter-spacing:-.02em}
.ph p{color:rgba(255,255,255,.85)!important;font-size:.95rem!important;margin:0!important}
.pb{display:inline-block;background:rgba(255,255,255,.18);color:#fff;padding:.25rem .75rem;border-radius:20px;font-size:.75rem;font-weight:500;margin-top:.75rem;backdrop-filter:blur(4px)}
.mr{display:flex;gap:1rem;margin-bottom:1.5rem}
.mc{flex:1;background:var(--sf);border:1px solid var(--bd);border-radius:var(--r);padding:1.2rem;text-align:center;box-shadow:var(--sh);transition:box-shadow .2s}
.mc:hover{box-shadow:var(--sh2)}
.ml{font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;color:var(--tx2);margin-bottom:.35rem;font-weight:500}
.mv{font-size:1.45rem;font-weight:700;line-height:1.2}
.mv.b{color:var(--pri)}.mv.g{color:var(--acc)}.mv.a{color:#D97706}
.plc{display:flex;align-items:center;gap:0;padding:.75rem 0;flex-wrap:wrap}
.pla{display:flex;align-items:center;gap:.4rem;background:var(--pri);border:1px solid var(--pri);border-radius:8px;padding:.45rem .9rem;font-size:.84rem;font-weight:500;color:#fff;white-space:nowrap}
.plarr{color:#94A3B8;font-size:1.1rem;padding:0 .3rem;user-select:none}
.sc{background:#FAFBFD;border:1px solid var(--bd);border-radius:10px;padding:1rem 1.25rem;margin-bottom:.75rem;transition:border-color .2s}
.sc:hover{border-color:var(--pri)}
.shd{display:flex;justify-content:space-between;align-items:center;margin-bottom:.4rem}
.stt_{font-weight:600;font-size:.88rem;color:var(--tx)}
.sb{display:inline-block;padding:.15rem .55rem;border-radius:20px;font-size:.68rem;font-weight:600;text-transform:uppercase;letter-spacing:.03em}
.sb.w{background:#EFF6FF;color:#2563EB}.sb.d{background:var(--acc-l);color:#059669}
.se{font-size:.82rem;color:var(--tx2);line-height:1.55;margin-top:.4rem}
.sli{display:inline-block;margin-top:.45rem;color:var(--pri);font-size:.82rem;font-weight:500;text-decoration:none}
.vb{display:flex;align-items:center;gap:.8rem;background:var(--sf);border:1px solid var(--bd);border-radius:var(--r);padding:.9rem 1.3rem;margin-bottom:1rem;box-shadow:var(--sh)}
.vd{width:10px;height:10px;border-radius:50%;flex-shrink:0}
.vd.g{background:var(--acc)}.vd.a{background:#F59E0B}.vd.r{background:#EF4444}
.vt{font-size:.85rem;color:var(--tx)}
.ts{background:#F8FAFC;border:1px solid var(--bd);border-radius:8px;padding:.9rem;margin-bottom:.5rem;font-size:.82rem;line-height:1.55}
.tl{font-weight:600;color:var(--pri);font-size:.72rem;text-transform:uppercase;letter-spacing:.04em}
.sth{font-size:1.05rem;font-weight:600;color:var(--tx);margin-bottom:.9rem;padding-bottom:.45rem;border-bottom:2px solid var(--pri-l);letter-spacing:-.01em}
.ac{background:var(--sf);border:1px solid var(--bd);border-radius:var(--r);padding:1.5rem 2rem;line-height:1.75;color:var(--tx);font-size:.92rem;box-shadow:var(--sh)}
.stTextInput>div>div{border-radius:10px!important;border-color:var(--bd)!important}
.stTextInput>div>div:focus-within{border-color:var(--pri)!important;box-shadow:0 0 0 2px rgba(74,111,165,.15)!important}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,#4A6FA5,#5C82B8)!important;border:none!important;border-radius:10px!important;font-weight:600!important;padding:.6rem 2rem!important;transition:all .2s!important}
.stButton>button[kind="primary"]:hover{background:linear-gradient(135deg,#3D5F8F,#4A6FA5)!important;box-shadow:0 4px 12px rgba(74,111,165,.3)!important}
.streamlit-expanderHeader{font-weight:500!important;font-size:.9rem!important;color:var(--tx)!important;background:#FAFBFD!important;border-radius:8px!important}
section[data-testid="stSidebar"] .stButton>button{background:rgba(255,255,255,.08)!important;color:#CBD5E1!important;border:1px solid rgba(255,255,255,.12)!important;border-radius:8px!important;font-size:.82rem!important;text-align:left!important;padding:.5rem .75rem!important;width:100%!important;transition:all .15s!important}
section[data-testid="stSidebar"] .stButton>button:hover{background:rgba(255,255,255,.14)!important;border-color:rgba(255,255,255,.2)!important}
.hi{background:var(--sf);border:1px solid var(--bd);border-radius:10px;padding:1rem 1.2rem;margin-bottom:.7rem}
.hi:hover{border-color:var(--pri)}
.hq{font-weight:500;font-size:.88rem;color:var(--tx);margin-bottom:.25rem}
.hm{font-size:.75rem;color:var(--tx2)}
.sd{height:1px;background:var(--bd);margin:1.5rem 0}
::-webkit-scrollbar{width:6px}::-webkit-scrollbar-track{background:transparent}::-webkit-scrollbar-thumb{background:#CBD5E1;border-radius:3px}
</style>
"""
st.markdown(_CSS, unsafe_allow_html=True)

if "slm_app" not in st.session_state:
    st.session_state.slm_app = None
if "query_history" not in st.session_state:
    st.session_state.query_history = []
if "selected_orchestrator" not in st.session_state:
    st.session_state.selected_orchestrator = "flan_t5"

def _init():
    if st.session_state.slm_app is None:
        with st.spinner("Starting PEARL system ..."):
            o = st.session_state.get("selected_orchestrator", "flan_t5")
            st.session_state.slm_app = SLMOrchestrationApp(orchestrator_type=o)
            asyncio.run(st.session_state.slm_app.initialize())

ORCH = {"flan_t5":"SLM Classifier (Flan-T5 80M)","iterative_small":"Iterative SLM (80M)","rule":"Rule-based","gpt4":"GPT-4 (reference)","none":"No orchestration"}
ICONS = {"booster":"\u26A1","retriever":"\U0001F50D","answering":"\U0001F4AC","verifier":"\u2714\uFE0F"}
COLORS = {"booster":"#F59E0B","retriever":"#3B82F6","answering":"#8B5CF6","verifier":"#10B981"}


SAMPLE_POOLS = {
    "Simple": [
        "What is Article 21 of the Indian Constitution?",
        "Define habeas corpus in Indian law",
        "What is Section 302 IPC?",
        "What are fundamental rights?",
        "Explain the doctrine of basic structure",
        "How does anticipatory bail work under Section 438 CrPC?",
        "What is the procedure for filing a PIL?",
        "What are the grounds for divorce under Hindu Marriage Act?",
        "What is contempt of court under Indian law?",
        "How to file an RTI application?",
        "What are the rights of arrested persons?",
        "What is the POCSO Act?",
        "What is the Consumer Protection Act 2019?",
        "What are sedition laws in India?",
        "What is the Domestic Violence Act 2005?",
        "What are the penalties under NDPS Act?",
        "What is the significance of Kesavananda Bharati case?",
        "What are the provisions for bail in non-bailable offences?",
        "Explain the Insolvency and Bankruptcy Code 2016",
        "How does arbitration work under Indian law?",
    ],
    "Verified": [
        "What is the punishment for cybercrime under IT Act 2000?",
        "What remedies are available under consumer protection act?",
        "What are the legal precedents for Article 21?",
        "How has the Supreme Court interpreted Article 32?",
        "Analyze impact of Vishaka guidelines on workplace harassment",
        "Evaluate the constitutional validity of reservation policy",
        "Analyze implications of Section 498A IPC on matrimonial disputes",
        "Evaluate Supreme Court interpretation of right to privacy",
    ],
    "Enhanced": [
        "rights",
        "privacy",
        "cyber crime",
        "property",
        "labor laws",
        "women rights",
        "child custody",
        "land acquisition",
        "Analyze how Supreme Court expanded Article 21",
        "Evaluate effectiveness of PIL in environmental protection",
    ],
    "Full Pipeline": [
        "Compare Article 14 and Article 19 of the Constitution",
        "Compare Article 21 and Article 14",
        "Critically examine role of judiciary in protecting civil liberties",
    ],
}

ROUTE_LABELS = {
    "Simple": "retriever \u2192 answering",
    "Verified": "retriever \u2192 answering \u2192 verifier",
    "Enhanced": "booster \u2192 retriever \u2192 answering",
    "Full Pipeline": "booster \u2192 retriever \u2192 answering \u2192 verifier",
}

ROUTE_COLORS = {
    "Simple": "#10B981",
    "Verified": "#3B82F6",
    "Enhanced": "#F59E0B",
    "Full Pipeline": "#8B5CF6",
}

def _pick_samples():
    if "sample_queries" not in st.session_state:
        picked = []
        for cat in ["Simple", "Verified", "Enhanced", "Full Pipeline"]:
            pool = SAMPLE_POOLS[cat]
            n = 2 if cat in ("Simple", "Verified") else (2 if cat == "Enhanced" else 1)
            n = min(n, len(pool))
            picked.extend([(q, cat) for q in random.sample(pool, n)])
        st.session_state.sample_queries = picked
    return st.session_state.sample_queries

def _pipe(agents):
    p = []
    for i, a in enumerate(agents):
        ic = ICONS.get(a, "")
        p.append(f'<span class="pla">{ic}&ensp;{a.title()}</span>')
        if i < len(agents) - 1:
            p.append('<span class="plarr">\u2192</span>')
    return f'<div class="plc">{"".join(p)}</div>'

def _mrow(items):
    c = []
    for lbl, val, cls in items:
        c.append(f'<div class="mc"><div class="ml">{lbl}</div><div class="mv {cls}">{val}</div></div>')
    return f'<div class="mr">{"".join(c)}</div>'

def main():
    _init()

    with st.sidebar:
        st.markdown("### \u2696\uFE0F  PEARL")
        st.caption("Performance-Efficient Agentic RAG\nthrough Learned Orchestration")
        st.markdown("---")
        okeys = list(ORCH.keys())
        olbls = list(ORCH.values())
        cur = st.session_state.get("selected_orchestrator", "flan_t5")
        idx = okeys.index(cur) if cur in okeys else 0
        ch = st.selectbox("Orchestrator", olbls, index=idx, key="os_", label_visibility="collapsed")
        ck = okeys[olbls.index(ch)]
        if ck != st.session_state.get("selected_orchestrator"):
            st.session_state.selected_orchestrator = ck
            st.session_state.slm_app = None
            st.rerun()
        st.markdown("---")
        if st.session_state.slm_app:
            st.markdown('<p style="font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;color:#94A3B8;margin-bottom:6px;">Active Agents</p>', unsafe_allow_html=True)
            for n, ic in ICONS.items():
                st.markdown(f'<p style="margin:2px 0;font-size:.85rem;">{ic}&ensp;{n.title()}</p>', unsafe_allow_html=True)
            st.markdown("---")
            if st.button("\u21BB  Reinitialize", use_container_width=True):
                st.session_state.slm_app = None
                _init()
                st.rerun()
        st.markdown("---")
        st.markdown('<p style="font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;color:#94A3B8;margin-bottom:6px;">Sample Queries</p>', unsafe_allow_html=True)
        samples = _pick_samples()
        for q, cat in samples:
            color = ROUTE_COLORS.get(cat, "#94A3B8")
            route = ROUTE_LABELS.get(cat, "")
            st.markdown(f'<p style="font-size:.62rem;color:{color};font-weight:600;margin:8px 0 2px 0;text-transform:uppercase;letter-spacing:.04em;">{cat} &ensp;\u2022&ensp; {route}</p>', unsafe_allow_html=True)
            if st.button(q, key=f"s_{hash(q)}", use_container_width=True):
                st.session_state["q_input"] = q
                st.session_state["pending_query"] = q
                st.rerun()
        st.markdown("---")
        if st.button("\u21BB  Shuffle Queries", key="shuffle", use_container_width=True):
            if "sample_queries" in st.session_state:
                del st.session_state.sample_queries
            st.rerun()

    st.markdown(f'<div class="ph"><h1>\u2696\uFE0F PEARL Legal Assistant</h1><p>Multi-Agent Legal Information Retrieval with SLM Orchestration</p><span class="pb">{ORCH.get(st.session_state.selected_orchestrator,"SLM")}</span></div>', unsafe_allow_html=True)

    pending = st.session_state.pop("pending_query", None)

    if "q_input" not in st.session_state:
        st.session_state["q_input"] = ""
    query = st.text_input("q", key="q_input", placeholder="Ask any Indian legal question ...", label_visibility="collapsed")
    bc, _ = st.columns([1, 3])
    with bc:
        go = st.button("Ask Question", type="primary", use_container_width=True)

    run_query = None
    if pending:
        run_query = pending
    elif go and query:
        run_query = query
    elif go and not query:
        st.warning("Please type a question first.")

    if run_query and st.session_state.slm_app:
        with st.spinner("Thinking ..."):
            try:
                res = asyncio.run(st.session_state.slm_app.process_query(run_query))
                st.session_state.orchestration_info = res.get("orchestration", {})
                st.session_state.query_history.append({"query": run_query, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "result": res})
                st.session_state.current_result = res
            except Exception as e:
                st.error(f"Error: {e}")
                st.session_state.current_result = None

    if not hasattr(st.session_state, "current_result") or not st.session_state.current_result:
        return
    res = st.session_state.current_result
    orch_data = getattr(st.session_state, "orchestration_info", {})
    ana = orch_data.get("analysis", {})
    seq = res.get("agent_sequence", [])

    st.markdown('<div class="sd"></div>', unsafe_allow_html=True)

    cplx = ana.get("complexity", "moderate").title()
    conf = res.get("confidence", 0)
    nsrc = len(res.get("citations", []) or res.get("documents", []))
    st.markdown(_mrow([("Complexity", cplx, "b"), ("Confidence", f"{conf:.0%}", "g" if conf >= .5 else "a"), ("Sources", str(nsrc), "b"), ("Cost", "$0.00", "g")]), unsafe_allow_html=True)

    if seq:
        st.markdown('<div class="sth">Agent Pipeline</div>', unsafe_allow_html=True)
        st.markdown(_pipe(seq), unsafe_allow_html=True)

    st.markdown('<div class="sth">Answer</div>', unsafe_allow_html=True)
    ans = res.get("answer", "No answer generated.")
    st.markdown(f'<div class="ac">{ans}</div>', unsafe_allow_html=True)

    vs = res.get("verification_score")
    cv = res.get("claims_verified", 0)
    tc = res.get("total_claims", 0)
    if vs is not None and tc > 0:
        r = cv / tc if tc else 0
        dc = "g" if r >= .6 else ("a" if r >= .3 else "r")
        sl = "Verified" if r >= .6 else ("Partially Verified" if r >= .3 else "Low Confidence")
        st.markdown(f'<div class="vb"><span class="vd {dc}"></span><span class="vt"><strong>{sl}</strong> &mdash; {cv} of {tc} claims supported &ensp;|&ensp; Score: {float(vs):.0%}</span></div>', unsafe_allow_html=True)

    cits = res.get("citations", [])
    if not cits:
        cits = res.get("documents", [])
    if cits:
        st.markdown('<div class="sth">Sources</div>', unsafe_allow_html=True)
        for i, c in enumerate(cits, 1):
            tit = c.get("title", c.get("text", "Source"))
            dt = c.get("doc_type", "document")
            iw = dt == "web_result"
            bcls = "w" if iw else "d"
            bt = "WEB" if iw else "DATABASE"
            sm = c.get("similarity_score", c.get("score", 0))
            ss = f"{float(sm):.0%}" if sm else ""
            url = c.get("url", "")
            exc = str(c.get("content", c.get("snippet", "")))[:350]
            src = c.get("source", dt)
            lh = f'<a class="sli" href="{url}" target="_blank">\u2197 Open source</a>' if url and url.startswith("http") else ""
            meta = f'<div style="font-size:.78rem;color:#64748B;margin-bottom:.3rem;">Relevance: {ss} &ensp;|&ensp; {src}</div>' if ss else ""
            exh = f'<div class="se">{exc}</div>' if exc else ""
            st.markdown(f'<div class="sc"><div class="shd"><span class="stt_">{i}. {tit}</span><span class="sb {bcls}">{bt}</span></div>{meta}{exh}{lh}</div>', unsafe_allow_html=True)

    if orch_data:
        with st.expander("Orchestration Details"):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Query Analysis**")
                st.json({"Complexity": ana.get("complexity","unknown"), "Reasoning": ana.get("reasoning_type","unknown"), "Confidence": f'{ana.get("confidence",.7):.0%}', "Enhancement": ana.get("requires_enhancement", False), "Verification": ana.get("requires_verification", False)})
            with c2:
                st.markdown("**Routing**")
                st.json({"Orchestrator": orch_data.get("orchestrator","flan_t5"), "Model": "Flan-T5-small (80M)", "Sequence": orch_data.get("agent_sequence",[]), "Cost": "$0.00"})

    trc = res.get("reasoning_traces", {})
    if trc:
        with st.expander("Agent Reasoning Traces"):
            for an, steps in trc.items():
                ic = ICONS.get(an, "")
                cl = COLORS.get(an, "#4A6FA5")
                st.markdown(f'<p style="font-weight:600;color:{cl};margin-bottom:.4rem;">{ic}&ensp;{an.title()}</p>', unsafe_allow_html=True)
                for j, s in enumerate(steps, 1):
                    th = s.get("thought", "")
                    ac_ = s.get("action", "")
                    ob = str(s.get("observation", ""))
                    if len(ob) > 300:
                        ob = ob[:300] + " ..."
                    ai = s.get("action_input", {})
                    inp = ", ".join(f"{k}={v}" for k, v in ai.items()) if isinstance(ai, dict) else str(ai)
                    st.markdown(f'<div class="ts"><span class="tl">Step {j}</span><br><strong>Thought:</strong> {th}<br><strong>Action:</strong> {ac_}<br><strong>Input:</strong> {inp}<br><strong>Obs:</strong> {ob}</div>', unsafe_allow_html=True)

    if st.session_state.query_history and len(st.session_state.query_history) > 1:
        with st.expander("Previous Queries"):
            for it in reversed(st.session_state.query_history[-6:-1]):
                qq = it["query"]
                ts = it["timestamp"]
                rr = it.get("result", {})
                ap = rr.get("answer", "")[:120]
                nc = len(rr.get("citations", []))
                co = rr.get("confidence", 0)
                st.markdown(f'<div class="hi"><div class="hq">{qq}</div><div class="hm">{ts} &ensp;|&ensp; {nc} sources &ensp;|&ensp; {co:.0%}</div><div class="se">{ap} ...</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="sd"></div>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center;font-size:.75rem;color:#94A3B8;">PEARL Framework &mdash; Performance-Efficient Agentic RAG through Learned Orchestration &ensp;|&ensp; Multi-Agent Legal RAG System</p>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
