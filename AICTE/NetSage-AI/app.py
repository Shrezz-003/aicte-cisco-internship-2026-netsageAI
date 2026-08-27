import streamlit as st
import os
import html
import pandas as pd
from dotenv import load_dotenv
from src.diagnostic_engine import run_diagnosis

# Load backend environment variables silently
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")


def render_command(cmd: str):
    """
    Renders a command as plain styled HTML in the main page (NOT st.code()).
    st.code() draws its text inside Streamlit's own embedded widget frame with a
    fixed light theme baked in — no page-level CSS can ever reach that text, which
    is why the commands stayed unreadable no matter how the stylesheet changed.
    This renders straight into the page DOM instead, so our colors always apply.
    """
    safe_cmd = html.escape(cmd or "")
    st.markdown(f'<div class="ns-code">{safe_cmd}</div>', unsafe_allow_html=True)

# ----------------- State Management for Live Dashboard -----------------
# This keeps track of our metrics dynamically while the app runs
if "metrics" not in st.session_state:
    st.session_state.metrics = {"total": 0, "accepted": 0, "rejected": 0}
if "ai_log" not in st.session_state:
    st.session_state.ai_log = []

# ----------------- UI Configuration -----------------
st.set_page_config(page_title="NetSage AI", page_icon="🛰️", layout="wide")

# ----------------- Visual Design Layer -----------------
# Pure presentation: "signal-lab / night-market circuit" aesthetic.
# No app logic lives below this block — safe to skip on read-through.
NETSAGE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700;800&family=IBM+Plex+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root{
  --void:#120B1E;
  --panel:#1D1330;
  --panel-raised:#281A42;
  --trace:#4A376880;
  --trace-strong:#5C4380;
  --text:#F5EFFF;
  --text-muted:#B8A8D9;

  /* Signature palette — deliberately not the usual teal/amber pairing */
  --magenta:#FF3B7F;   /* primary accent (was amber) */
  --magenta-dim:#7A2B4E;
  --lime:#C6FF3D;      /* secondary accent (was teal) */
  --violet:#8A5CFF;    /* tertiary accent (was blue) */
  --danger:#FF5C5C;    /* reject / error */
}

/* ---- base canvas: dot-grid on deep indigo ---- */
[data-testid="stAppViewContainer"]{
  background-color: var(--void);
  background-image:
    radial-gradient(var(--trace) 1px, transparent 1px);
  background-size: 26px 26px;
}
[data-testid="stHeader"]{ background: transparent; }
.block-container{ padding-top: 2.4rem; max-width: 1180px; }

html, body, [data-testid="stAppViewContainer"], p, span, li, label, div{
  color: var(--text);
  font-family: 'IBM Plex Sans', sans-serif;
}

/* ---- nameplate header ---- */
.ns-kicker{
  font-family:'JetBrains Mono', monospace;
  font-size:.72rem;
  letter-spacing:.22em;
  color: var(--lime);
  text-transform:uppercase;
  margin-bottom:.35rem;
  opacity:.95;
}
h1{
  font-family:'Sora', sans-serif !important;
  font-weight:800 !important;
  letter-spacing:-.01em;
  color: var(--text) !important;
  margin-bottom:.3rem !important;
}
h2, h3{
  font-family:'Sora', sans-serif !important;
  font-weight:600 !important;
  color: var(--text) !important;
}

/* signature element: live signal trace under the nameplate — violet/magenta sweep */
.ns-trace{
  position:relative;
  height:10px;
  margin:.6rem 0 1.6rem 0;
  border-bottom:1px solid var(--trace-strong);
}
.ns-trace::before{
  content:"";
  position:absolute; left:0; right:0; bottom:-1px; height:2px;
  background: linear-gradient(90deg,
    transparent 0%, var(--violet) 8%, transparent 16%,
    transparent 40%, var(--magenta) 48%, transparent 56%,
    transparent 78%, var(--lime) 86%, transparent 94%);
  background-size: 220% 100%;
  animation: ns-signal 3.4s linear infinite;
}
@keyframes ns-signal{
  0%{ background-position: 0% 0; }
  100%{ background-position: -220% 0; }
}
@media (prefers-reduced-motion: reduce){
  .ns-trace::before{ animation: none; background-position: -60% 0; }
}

/* ---- tabs styled as a device port selector ---- */
[data-testid="stTabs"] [role="tablist"]{
  gap:.4rem;
  border-bottom:1px solid var(--trace-strong);
}
[data-testid="stTabs"] button[role="tab"]{
  font-family:'JetBrains Mono', monospace;
  font-size:.85rem;
  color: var(--text-muted);
  background: var(--panel);
  border:1px solid var(--trace-strong);
  border-bottom:none;
  border-radius:6px 6px 0 0;
  padding:.55rem 1.1rem;
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"]{
  color: var(--magenta);
  background: var(--panel-raised);
  box-shadow: inset 0 2px 0 var(--magenta);
}

/* ---- chat console ---- */
[data-testid="stChatMessage"]{
  background: var(--panel);
  border:1px solid var(--trace-strong);
  border-left:3px solid var(--violet);
  border-radius:10px;
  padding:.9rem 1.1rem;
  margin-bottom:.75rem;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]){
  border-left-color: var(--magenta);
}

/* chat input: subtle violet ring on focus instead of a harsh solid line */
[data-testid="stChatInput"]{
  border-radius: 10px;
}
[data-testid="stChatInput"] textarea{
  font-family:'JetBrains Mono', monospace;
  background: var(--panel-raised) !important;
  border:1px solid var(--trace-strong) !important;
  border-radius: 10px !important;
  color: var(--text) !important;
}
[data-testid="stChatInput"]:focus-within{
  box-shadow: 0 0 0 2px var(--violet), 0 0 14px -2px var(--magenta);
  outline: none;
  border-radius: 10px;
}

/* ---- code / command output panels ---- */
[data-testid="stCodeBlock"]{
  border:1px solid var(--trace-strong) !important;
  border-left:3px solid var(--lime) !important;
  border-radius:8px !important;
  background: var(--panel-raised) !important;
  overflow:hidden;
}
[data-testid="stCodeBlock"] pre,
[data-testid="stCodeBlock"] div,
[data-testid="stCodeBlock"][data-testid="stCodeBlock"] pre{
  background: var(--panel-raised) !important;
  background-color: var(--panel-raised) !important;
}
[data-testid="stCodeBlock"] code,
[data-testid="stCodeBlock"] code *,
[data-testid="stCodeBlock"] pre code span,
[data-testid="stCodeBlock"][data-testid="stCodeBlock"] code *{
  background: transparent !important;
  background-color: transparent !important;
  color: #120B1E !important; /* CHANGED: Dark void color so it is readable on the white background */
  -webkit-text-fill-color: #120B1E !important;
  font-family:'JetBrains Mono', monospace !important;
  text-shadow: none !important;
  opacity: 1 !important;
}
[data-testid="stCodeBlock"] button{
  color: var(--text-muted) !important;
}

/* CHANGED: Fix for inline code snippets (like IP addresses) inside Markdown */
.stMarkdown code {
  color: #120B1E !important;
  -webkit-text-fill-color: #120B1E !important;
  font-weight: 700 !important;
}

/* ---- command line — plain page-level element, not st.code() ---- */
.ns-code{
  font-family:'JetBrains Mono', monospace !important;
  background: var(--panel-raised) !important;
  color: var(--lime) !important;
  border: 1px solid var(--trace-strong);
  border-left: 3px solid var(--lime);
  border-radius: 8px;
  padding: .75rem 1rem;
  margin: .4rem 0 .9rem 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: .92rem;
}

/* ---- alerts as status panels ---- */
[data-testid="stAlert"]{
  border:1px solid var(--trace-strong);
  border-radius:8px;
  font-family:'IBM Plex Sans', sans-serif;
}

/* ---- metrics as indicator cards ---- */
[data-testid="stMetric"]{
  background: var(--panel);
  border:1px solid var(--trace-strong);
  border-top:2px solid var(--magenta);
  border-radius:10px;
  padding:1rem 1.2rem;
}
[data-testid="stMetricLabel"]{
  font-family:'JetBrains Mono', monospace;
  font-size:.72rem;
  letter-spacing:.14em;
  text-transform:uppercase;
  color: var(--text-muted) !important;
}
[data-testid="stMetricValue"]{
  font-family:'JetBrains Mono', monospace !important;
  color: var(--magenta) !important;
}

/* ---- accept / reject relay switches ---- */
.stButton > button{
  font-family:'JetBrains Mono', monospace;
  border-radius:6px;
  border:1px solid var(--trace-strong);
  background: var(--panel-raised);
  color: var(--text);
  transition: border-color .15s ease, color .15s ease, background .15s ease;
}
.stButton > button:hover{
  border-color: var(--violet);
  color: var(--violet);
}
[data-testid="stHorizontalBlock"] [data-testid="column"]:nth-of-type(1) .stButton > button{
  border-color: var(--lime);
  color: var(--lime);
}
[data-testid="stHorizontalBlock"] [data-testid="column"]:nth-of-type(1) .stButton > button:hover{
  background: var(--lime);
  color: var(--void);
}
[data-testid="stHorizontalBlock"] [data-testid="column"]:nth-of-type(3) .stButton > button{
  border-color: var(--danger);
  color: var(--danger);
}
[data-testid="stHorizontalBlock"] [data-testid="column"]:nth-of-type(3) .stButton > button:hover{
  background: var(--danger);
  color: var(--void);
}

/* ---- dataframe / responsible-AI log ---- */
[data-testid="stDataFrame"]{
  border:1px solid var(--trace-strong);
  border-radius:8px;
  overflow:hidden;
}

/* ---- scrollbar detail ---- */
::-webkit-scrollbar{ width:10px; height:10px; }
::-webkit-scrollbar-track{ background: var(--void); }
::-webkit-scrollbar-thumb{ background: var(--magenta-dim); border-radius:8px; }

/* ---- keyboard focus visibility ---- */
a:focus-visible, button:focus-visible, textarea:focus-visible{
  outline: 2px solid var(--violet) !important;
  outline-offset: 2px;
}
</style>
"""
st.markdown(NETSAGE_CSS, unsafe_allow_html=True)

st.markdown('<div class="ns-kicker">SYS // DIAGNOSTIC CONSOLE · HUMAN-IN-THE-LOOP</div>', unsafe_allow_html=True)
st.title("NetSage AI | Network Diagnostics")
st.markdown('<div class="ns-trace"></div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🧑‍💻 Chatbot (Junior Engineer)", "📈 Dashboard (Reviewer)"])

# ================= TAB 1: Chatbot =================
with tab1:
    st.markdown("Type your network symptom, or just say hello!")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": {"is_network_issue": False,
                                              "chat_reply": "Hello! I am NetSage AI. Describe your network issue in plain English, or just chat with me!"}}
        ]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if isinstance(msg["content"], dict):
                if msg["content"].get("is_network_issue"):
                    st.success(f"**Root Cause:** {msg['content'].get('root_cause')}")
                    st.write(
                        f"**OSI Layer:** {msg['content'].get('osi_layer')} | **Confidence:** {msg['content'].get('confidence')}")
                    render_command(msg['content'].get('next_command'))

                    st.markdown("### 🧭 Step-by-Step Execution Runbook")
                    for i, step in enumerate(msg['content'].get('fix_steps', [])):
                        st.markdown(f"**Step {i + 1}:** {step.get('explanation', 'Execute command:')}")
                        render_command(step.get('command', ''))
                else:
                    st.write(msg["content"].get("chat_reply", ""))
            else:
                st.write(msg["content"])

    if prompt := st.chat_input("E.g., My two VLAN network is pinging, but can't ping the other VLAN..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        if not API_KEY:
            with st.chat_message("assistant"):
                st.error("System Error: Backend API key is missing. Check .env configuration.")
        else:
            with st.chat_message("assistant"):
                with st.spinner("Analyzing custom dataset logic..."):
                    diagnosis = run_diagnosis(symptom=prompt, show_outputs="", api_key=API_KEY)

                    if "error" in diagnosis:
                        st.error(diagnosis["error"])
                    elif diagnosis.get("is_network_issue"):
                        st.success(f"**Root Cause:** {diagnosis.get('root_cause')}")
                        st.write(
                            f"**OSI Layer:** {diagnosis.get('osi_layer')} | **Confidence:** {diagnosis.get('confidence')}")
                        st.markdown("**Evidence:**")
                        st.write(diagnosis.get('evidence'))
                        st.markdown("**Next Verification Command:**")
                        render_command(diagnosis.get('next_command'))

                        st.markdown("---")
                        st.markdown("### 🧭 Step-by-Step Execution Runbook")
                        st.info("Follow these steps in order to resolve the issue.")

                        for i, step in enumerate(diagnosis.get('fix_steps', [])):
                            st.markdown(f"**Step {i + 1}:** {step.get('explanation', 'Execute command:')}")
                            render_command(step.get('command', ''))

                        st.markdown("---")
                        st.markdown("**Engineer Verification Required:**")
                        col1, col2, col3 = st.columns(3)

                        # ---- DYNAMIC BUTTON LOGIC ----
                        msg_index = len(st.session_state.messages)
                        if col1.button("✔ Accept Fix", key=f"accept_{msg_index}"):
                            st.session_state.metrics["total"] += 1
                            st.session_state.metrics["accepted"] += 1
                            st.toast("Fix approved! Dashboard updated.")
                            st.rerun()  # Forces the UI to refresh the dashboard instantly

                        if col3.button("✖ Reject", key=f"reject_{msg_index}"):
                            st.session_state.metrics["total"] += 1
                            st.session_state.metrics["rejected"] += 1
                            # Add to the Responsible AI Log
                            st.session_state.ai_log.append({
                                "Symptom": prompt,
                                "Root Cause AI Guessed": diagnosis.get('root_cause'),
                                "Status": "Rejected for Safety Review"
                            })
                            st.toast("Diagnosis rejected. Logged to Dashboard.")
                            st.rerun()
                    else:
                        st.write(diagnosis.get("chat_reply"))

                st.session_state.messages.append({"role": "assistant", "content": diagnosis})

# ================= TAB 2: Dashboard =================
with tab2:
    st.header("📈 Live Analytics & AI Safety Dashboard")
    st.markdown("Real-time summary of human reviewer agreement rates.")

    # Calculate live percentages
    total = st.session_state.metrics["total"]
    accepted = st.session_state.metrics["accepted"]
    rejected = st.session_state.metrics["rejected"]
    approval_rate = int((accepted / total) * 100) if total > 0 else 0

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Total Cases Evaluated", f"{total}")
    col_b.metric("Human Approval Rate", f"{approval_rate}%")
    col_c.metric("Rejected (Safety Flags)", f"{rejected}")

    st.markdown("---")
    st.subheader("🗒️ Responsible AI Log")
    st.markdown("Cases where the AI output was rejected by a human engineer are logged here for retraining.")

    if len(st.session_state.ai_log) > 0:
        # Display the dynamic list as a clean table
        log_df = pd.DataFrame(st.session_state.ai_log)
        st.dataframe(log_df, use_container_width=True)
    else:
        st.info("No cases have been rejected yet during this session.")