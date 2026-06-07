"""
ClaimSphere Copilot — Enterprise Claims Processing Platform
Team NEXORA | LTM x Microsoft Hack2Future 2026
"""
import asyncio, sys, os, time, json, random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

import requests as _requests

# Backend URL — used for all API calls so claims appear in Dataverse + React dashboard.
_BACKEND_URL = os.environ.get(
    "API_BASE_URL",
    "https://ca-api-u5aqvvvbt34hq.politecliff-7ae23c60.eastus.azurecontainerapps.io",
).rstrip("/")


def _api_load_claims() -> list[dict]:
    """Fetch the live claims list from the backend and convert to Streamlit format."""
    try:
        r = _requests.get(f"{_BACKEND_URL}/claims/", timeout=6)
        r.raise_for_status()
        raw = r.json() if isinstance(r.json(), list) else []
        return [
            {
                "id": c.get("claim_id", ""),
                "type": c.get("claim_type") or "Health",
                "claimant": c.get("claimant_name", ""),
                "amount": int(c.get("claim_amount") or 0),
                "payout": int(c.get("final_payout") or 0),
                "decision": c.get("decision") or "",
                "fraud": int(c.get("fraud_score") or 0),
                "status": c.get("status") or "",
                "channel": c.get("channel") or "Web",
                "date": (c.get("submitted_at") or "")[:16].replace("T", " "),
            }
            for c in raw
            if c.get("claim_id")
        ]
    except Exception:
        return []


def _api_submit_claim(payload: dict) -> dict | None:
    """POST a claim to the backend and return the result dict, or None on error."""
    try:
        r = _requests.post(
            f"{_BACKEND_URL}/claims/submit/sync",
            json=payload,
            timeout=90,
        )
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        return {"error": str(exc)}

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ClaimSphere Copilot",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Design System ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Reset & Base ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    -webkit-font-smoothing: antialiased;
}
.main .block-container {
    padding: 0 2rem 2.5rem;
    max-width: 1440px;
}
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ── Page Background ── */
.stApp { background: #F8FAFC; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #0F172A !important;
    border-right: 1px solid #1E293B;
    min-width: 220px !important;
}
section[data-testid="stSidebar"] * { color: #94A3B8 !important; }
section[data-testid="stSidebar"] .stRadio label {
    color: #94A3B8 !important;
    font-size: 0.835rem;
    font-weight: 500;
    padding: 0.475rem 0.875rem;
    border-radius: 6px;
    transition: background 0.12s, color 0.12s;
    cursor: pointer;
    display: block;
    letter-spacing: 0.01em;
}
section[data-testid="stSidebar"] .stRadio label:hover {
    background: #1E293B !important;
    color: #E2E8F0 !important;
}
section[data-testid="stSidebar"] [data-checked="true"] label {
    background: #1E3A5F !important;
    color: #93C5FD !important;
    font-weight: 600;
}
section[data-testid="stSidebar"] hr { border-color: #1E293B !important; }

/* ── Page Header ── */
.page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.5rem 0 1.25rem;
    border-bottom: 1px solid #E2E8F0;
    margin-bottom: 1.75rem;
}
.page-header h1 {
    font-size: 1.3rem;
    font-weight: 700;
    color: #0F172A;
    margin: 0;
    letter-spacing: -0.025em;
}
.page-header p {
    font-size: 0.78rem;
    color: #64748B;
    margin: 0.2rem 0 0;
    font-weight: 400;
}
.chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
}
.chip-green { color: #065F46; background: #ECFDF5; border: 1px solid #A7F3D0; }
.chip-blue  { color: #1E40AF; background: #EFF6FF; border: 1px solid #BFDBFE; }
.chip-amber { color: #92400E; background: #FFFBEB; border: 1px solid #FDE68A; }
.chip-dot {
    width: 5px; height: 5px; border-radius: 50%;
    display: inline-block; flex-shrink: 0;
}
.chip-green .chip-dot { background: #059669; }
.chip-blue  .chip-dot { background: #2563EB; }
.chip-amber .chip-dot { background: #D97706; }

/* ── KPI Cards ── */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin-bottom: 1.5rem;
}
.kpi-6 { grid-template-columns: repeat(6, 1fr); }
.kpi-card {
    background: #FFFFFF;
    border-radius: 10px;
    padding: 1.125rem 1.375rem;
    border: 1px solid #E2E8F0;
    border-left: 3px solid transparent;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}
.kpi-blue   { border-left-color: #2563EB; }
.kpi-green  { border-left-color: #059669; }
.kpi-purple { border-left-color: #7C3AED; }
.kpi-amber  { border-left-color: #D97706; }
.kpi-red    { border-left-color: #DC2626; }
.kpi-teal   { border-left-color: #0891B2; }
.kpi-label {
    font-size: 0.67rem;
    font-weight: 700;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.09em;
}
.kpi-value {
    font-size: 1.75rem;
    font-weight: 700;
    color: #0F172A;
    line-height: 1.1;
    margin: 0.35rem 0 0.2rem;
    letter-spacing: -0.03em;
}
.kpi-delta { font-size: 0.72rem; color: #64748B; }
.kpi-delta .up   { color: #059669; font-weight: 600; }
.kpi-delta .down { color: #DC2626; font-weight: 600; }
.kpi-delta .neutral { color: #D97706; font-weight: 600; }

/* ── Section Header ── */
.section-header {
    display: flex;
    align-items: center;
    gap: 0.625rem;
    margin-bottom: 0.875rem;
    margin-top: 0.125rem;
}
.section-header h3 {
    font-size: 0.85rem;
    font-weight: 600;
    color: #0F172A;
    margin: 0;
    letter-spacing: -0.01em;
}
.section-pill {
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    padding: 0.15rem 0.5rem;
    border-radius: 20px;
}
.pill-blue  { background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; }
.pill-green { background: #ECFDF5; color: #065F46; border: 1px solid #A7F3D0; }

/* ── Cards ── */
.card {
    background: #FFFFFF;
    border-radius: 10px;
    border: 1px solid #E2E8F0;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    padding: 1.25rem 1.5rem;
}

/* ── Agent Pipeline ── */
.agent-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.6rem 0.875rem;
    border-radius: 8px;
    margin-bottom: 0.35rem;
    transition: background 0.2s, border-color 0.2s;
    border: 1px solid transparent;
}
.agent-wait  { background: #F8FAFC; border-color: #E2E8F0; }
.agent-run   { background: #EFF6FF; border-color: #93C5FD; }
.agent-done  { background: #F0FDF4; border-color: #86EFAC; }
.agent-error { background: #FEF2F2; border-color: #FCA5A5; }
.agent-num {
    width: 22px; height: 22px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.67rem; font-weight: 700;
    flex-shrink: 0;
}
.num-wait { background: #E2E8F0; color: #475569; }
.num-run  { background: #2563EB; color: #FFFFFF; }
.num-done { background: #059669; color: #FFFFFF; }
.agent-name  { font-weight: 600; font-size: 0.82rem; color: #1E293B; flex: 1; }
.agent-desc  { font-size: 0.71rem; color: #64748B; margin-top: 1px; }
.agent-status {
    font-size: 0.67rem;
    font-weight: 700;
    padding: 0.2rem 0.55rem;
    border-radius: 4px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.s-wait { background: #F1F5F9; color: #64748B; }
.s-run  { background: #DBEAFE; color: #1D4ED8; }
.s-done { background: #DCFCE7; color: #15803D; }

/* ── Decision Result ── */
.decision-card {
    border-radius: 10px;
    padding: 1.5rem;
    border: 1px solid transparent;
    border-left: 4px solid transparent;
}
.d-approve {
    background: #F0FDF4;
    border-color: #BBF7D0;
    border-left-color: #059669;
}
.d-reject {
    background: #FEF2F2;
    border-color: #FECACA;
    border-left-color: #DC2626;
}
.d-escalate {
    background: #FFFBEB;
    border-color: #FDE68A;
    border-left-color: #D97706;
}
.decision-title {
    font-size: 1.05rem;
    font-weight: 700;
    margin: 0 0 0.375rem;
    letter-spacing: -0.02em;
}
.d-approve  .decision-title { color: #065F46; }
.d-reject   .decision-title { color: #7F1D1D; }
.d-escalate .decision-title { color: #78350F; }
.decision-row { display: flex; gap: 1.75rem; margin-top: 0.875rem; flex-wrap: wrap; }
.decision-item label {
    font-size: 0.62rem;
    color: #6B7280;
    text-transform: uppercase;
    font-weight: 700;
    letter-spacing: 0.09em;
    display: block;
}
.decision-item .val {
    font-size: 1rem;
    font-weight: 700;
    color: #1E293B;
    margin-top: 0.1rem;
}

/* ── Badges ── */
.badge {
    display: inline-block;
    padding: 0.18rem 0.6rem;
    border-radius: 4px;
    font-size: 0.67rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.b-approved   { background: #DCFCE7; color: #166534; }
.b-rejected   { background: #FEE2E2; color: #991B1B; }
.b-escalated  { background: #FEF3C7; color: #92400E; }
.b-processing { background: #EFF6FF; color: #1E40AF; }
.b-pending    { background: #F3F4F6; color: #374151; }

/* ── Chat ── */
.chat-container {
    height: 400px;
    overflow-y: auto;
    padding: 1rem;
    background: #F8FAFC;
    border-radius: 10px;
    border: 1px solid #E2E8F0;
}
.chat-msg-user { display: flex; justify-content: flex-end; margin: 0.5rem 0; }
.chat-msg-bot  { display: flex; justify-content: flex-start; margin: 0.5rem 0; }
.chat-bubble-user {
    background: #2563EB;
    color: #FFFFFF;
    border-radius: 12px 12px 3px 12px;
    padding: 0.625rem 0.95rem;
    max-width: 75%;
    font-size: 0.83rem;
    line-height: 1.55;
}
.chat-bubble-bot {
    background: #FFFFFF;
    color: #1E293B;
    border: 1px solid #E2E8F0;
    border-radius: 12px 12px 12px 3px;
    padding: 0.625rem 0.95rem;
    max-width: 80%;
    font-size: 0.83rem;
    line-height: 1.55;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}
.chat-av-u {
    width: 25px; height: 25px; border-radius: 50%;
    background: #2563EB;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.62rem; color: #FFF; font-weight: 700;
    margin-left: 7px; flex-shrink: 0;
}
.chat-av-b {
    width: 25px; height: 25px; border-radius: 50%;
    background: #0F172A;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.62rem; color: #FFF; font-weight: 700;
    margin-right: 7px; flex-shrink: 0;
}

/* ── Metric Chip ── */
.metric-chip {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 1rem 1.25rem;
    text-align: center;
}
.metric-chip .num {
    font-size: 1.5rem;
    font-weight: 700;
    color: #0F172A;
    letter-spacing: -0.03em;
}
.metric-chip .lbl {
    font-size: 0.65rem;
    color: #64748B;
    text-transform: uppercase;
    font-weight: 700;
    margin-top: 0.15rem;
    letter-spacing: 0.08em;
}

/* ── Activity Feed ── */
.activity-item {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 0.55rem 0;
    border-bottom: 1px solid #F1F5F9;
}
.activity-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    margin-top: 5px;
    flex-shrink: 0;
}
.activity-text { font-size: 0.79rem; color: #374151; line-height: 1.45; }
.activity-time { font-size: 0.67rem; color: #9CA3AF; margin-top: 0.1rem; }

/* ── Buttons ── */
.stButton > button {
    background: #2563EB !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 7px !important;
    padding: 0.525rem 1.25rem !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    transition: background 0.15s, box-shadow 0.15s !important;
    box-shadow: 0 1px 3px rgba(37,99,235,0.28) !important;
    letter-spacing: 0.01em !important;
}
.stButton > button:hover {
    background: #1D4ED8 !important;
    box-shadow: 0 2px 8px rgba(37,99,235,0.35) !important;
}

/* ── Form Inputs ── */
.stTextInput input,
.stSelectbox > div,
.stNumberInput input,
.stTextArea textarea {
    border-radius: 7px !important;
    border-color: #E2E8F0 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.84rem !important;
    color: #0F172A !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #2563EB !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.08) !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #F1F5F9;
    border-radius: 8px;
    padding: 3px;
    gap: 2px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 6px !important;
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    color: #64748B !important;
}
.stTabs [aria-selected="true"] {
    background: #FFFFFF !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08) !important;
    color: #0F172A !important;
    font-weight: 600 !important;
}

/* ── Divider ── */
hr { border-color: #E2E8F0 !important; margin: 0.875rem 0 !important; }

/* ── Misc ── */
.row-sep { height: 1px; background: #F1F5F9; margin-bottom: 3px; }
.col-label {
    font-size: 0.67rem;
    font-weight: 700;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)


# ─── Helpers ──────────────────────────────────────────────────────────────────
def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except Exception:
        return asyncio.run(coro)


def badge(text):
    cls_map = {
        "Approve": "b-approved", "Approved": "b-approved",
        "Reject": "b-rejected",  "Rejected": "b-rejected",
        "Escalate": "b-escalated", "Escalated": "b-escalated",
        "Under Human Review": "b-escalated",
        "Processing": "b-processing", "Received": "b-processing",
        "Pending Information": "b-pending",
    }
    cls = cls_map.get(text, "b-pending")
    return f'<span class="badge {cls}">{text}</span>'


def fraud_bar(score: int) -> str:
    color = "#059669" if score < 30 else "#D97706" if score < 60 else "#DC2626"
    return (
        f'<div style="display:flex;align-items:center;gap:7px">'
        f'<div style="flex:1;height:5px;background:#E2E8F0;border-radius:3px;overflow:hidden">'
        f'<div style="width:{score}%;height:100%;background:{color};border-radius:3px"></div></div>'
        f'<span style="font-size:0.73rem;font-weight:700;color:{color};min-width:24px;text-align:right">{score}</span>'
        f'</div>'
    )


def kpi_card(label, value, delta_html, color):
    return (
        f'<div class="kpi-card kpi-{color}">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="kpi-delta">{delta_html}</div>'
        f'</div>'
    )


def page_header(title, subtitle, chip_text=None, chip_type="green"):
    chip = ""
    if chip_text:
        chip = (
            f'<span class="chip chip-{chip_type}">'
            f'<span class="chip-dot"></span>'
            f'{chip_text}</span>'
        )
    return (
        f'<div class="page-header">'
        f'<div><h1>{title}</h1><p>{subtitle}</p></div>'
        f'<div>{chip}</div>'
        f'</div>'
    )


def section_header(title, pill=None, pill_type="blue"):
    pill_html = ""
    if pill:
        pill_html = f'<span class="section-pill pill-{pill_type}">{pill}</span>'
    return (
        f'<div class="section-header">'
        f'<h3>{title}</h3>'
        f'{pill_html}'
        f'</div>'
    )


# ─── Demo Seed Data ────────────────────────────────────────────────────────────
ACTIVITY: list[tuple] = []

DOT_COLORS = {"green": "#059669", "amber": "#D97706", "red": "#DC2626", "blue": "#2563EB"}

# ─── Session State ─────────────────────────────────────────────────────────────
# Initialise claims from the live backend on first load so the table always
# reflects real submitted claims, not hardcoded demo rows.
if "claims" not in st.session_state:
    st.session_state["claims"] = _api_load_claims()
for k, v in [("chat_history", []), ("last_result", None), ("selected_claim", None)]:
    if k not in st.session_state:
        st.session_state[k] = v


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:1.375rem 1rem 0.875rem">
      <div style="display:flex;align-items:center;gap:10px">
        <div style="width:32px;height:32px;background:#2563EB;border-radius:7px;
          flex-shrink:0;display:flex;align-items:center;justify-content:center;
          font-size:11px;font-weight:800;color:#FFF;letter-spacing:-0.5px">CS</div>
        <div>
          <div style="font-size:0.93rem;font-weight:700;color:#F1F5F9;line-height:1.2">ClaimSphere</div>
          <div style="font-size:0.67rem;color:#475569;margin-top:1px">Copilot · v1.0</div>
        </div>
      </div>
    </div>
    <hr>
    """, unsafe_allow_html=True)

    page = st.radio("", [
        "Dashboard",
        "Submit Claim",
        "Claims Register",
        "CSR Assistant",
        "Analytics",
        "Review Queue",
    ], label_visibility="collapsed")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("""
    <div style="padding:0 1rem">
      <div style="font-size:0.62rem;color:#334155;text-transform:uppercase;
        font-weight:700;letter-spacing:0.1em;margin-bottom:10px">System Status</div>
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:7px">
        <div style="width:6px;height:6px;border-radius:50%;background:#059669;flex-shrink:0"></div>
        <span style="font-size:0.73rem;color:#64748B">API Healthy</span>
      </div>
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:7px">
        <div style="width:6px;height:6px;border-radius:50%;background:#059669;flex-shrink:0"></div>
        <span style="font-size:0.73rem;color:#64748B">Azure OpenAI Connected</span>
      </div>
      <div style="display:flex;align-items:center;gap:8px">
        <div style="width:6px;height:6px;border-radius:50%;background:#D97706;flex-shrink:0"></div>
        <span style="font-size:0.73rem;color:#64748B">Demo Mode Active</span>
      </div>
    </div>
    <hr>
    <div style="padding:0 1rem 1.25rem;font-size:0.67rem;color:#334155;line-height:1.7">
      Team NEXORA<br>LTM × Microsoft Hack2Future 2026
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "Dashboard":
    _hdr_col, _refresh_col = st.columns([5, 1])
    with _hdr_col:
        st.markdown(page_header(
            "Dashboard",
            "AI-powered claims processing overview · Azure AI Foundry",
            "All Systems Operational",
            "green"
        ), unsafe_allow_html=True)
    with _refresh_col:
        st.markdown("<div style='padding-top:1.5rem'>", unsafe_allow_html=True)
        if st.button("Refresh Data", use_container_width=True):
            st.session_state["claims"] = _api_load_claims()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    total     = len(st.session_state.claims)
    approved  = sum(1 for c in st.session_state.claims if "Approv"  in c["decision"])
    rejected  = sum(1 for c in st.session_state.claims if "Reject"  in c["decision"])
    escalated = sum(1 for c in st.session_state.claims if "Escalat" in c["decision"])
    stp           = round((approved + rejected) / max(total, 1) * 100, 1)
    total_payout  = sum(c["payout"] for c in st.session_state.claims)
    avg_fraud     = round(sum(c["fraud"] for c in st.session_state.claims) / max(total, 1), 1)

    st.markdown(f"""
    <div class="kpi-grid">
      {kpi_card("Total Claims",    total,                         '<span class="up">+3</span> from yesterday',          "blue")}
      {kpi_card("Approved",        approved,                      f'<span class="up">{stp}% STP rate</span>',           "green")}
      {kpi_card("Escalated",       escalated,                     '<span class="neutral">Pending adjudicator</span>',   "amber")}
      {kpi_card("Rejected",        rejected,                      '<span class="down">Policy exclusion</span>',         "red")}
    </div>
    <div class="kpi-grid">
      {kpi_card("Total Payout",    f"₹{total_payout/100000:.1f}L", '<span class="up">+18% vs last week</span>',        "teal")}
      {kpi_card("Avg TAT",         "3.1s",                        '<span class="up">0.8s faster</span>',               "purple")}
      {kpi_card("Avg Fraud Score", f"{avg_fraud} / 100",          '<span class="up">Low risk portfolio</span>',        "blue")}
      {kpi_card("AI Accuracy",     "97.3%",                       '<span class="up">+1.2% this month</span>',          "green")}
    </div>
    """, unsafe_allow_html=True)

    col_chart, col_feed = st.columns([2, 1], gap="large")

    with col_chart:
        st.markdown(section_header("Claims Volume — Last 14 Days", "Live", "green"), unsafe_allow_html=True)
        dates       = [datetime.now() - timedelta(days=i) for i in range(13, -1, -1)]
        approved_d  = [random.randint(2, 8)  for _ in dates[:-1]] + [approved]
        rejected_d  = [random.randint(0, 2)  for _ in dates[:-1]] + [rejected]
        escalated_d = [random.randint(0, 2)  for _ in dates[:-1]] + [escalated]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=approved_d,  name="Approved",  fill="tozeroy",
            line=dict(color="#059669", width=2), fillcolor="rgba(5,150,105,0.08)"))
        fig.add_trace(go.Scatter(x=dates, y=escalated_d, name="Escalated", fill="tozeroy",
            line=dict(color="#D97706", width=2), fillcolor="rgba(217,119,6,0.06)"))
        fig.add_trace(go.Scatter(x=dates, y=rejected_d,  name="Rejected",  fill="tozeroy",
            line=dict(color="#DC2626", width=2), fillcolor="rgba(220,38,38,0.05)"))
        fig.update_layout(
            height=230, margin=dict(t=8, b=8, l=0, r=0),
            paper_bgcolor="white", plot_bgcolor="white",
            legend=dict(orientation="h", y=1.05, x=0, font=dict(size=11, color="#475569")),
            xaxis=dict(showgrid=False, color="#94A3B8", tickfont=dict(size=10)),
            yaxis=dict(showgrid=True, gridcolor="#F1F5F9", color="#94A3B8", tickfont=dict(size=10)),
            font=dict(family="Inter"),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        c1, c2 = st.columns(2, gap="medium")
        with c1:
            st.markdown(section_header("Decision Split"), unsafe_allow_html=True)
            fig2 = go.Figure(go.Pie(
                labels=["Approved", "Rejected", "Escalated"],
                values=[approved, rejected, escalated],
                hole=0.65,
                marker_colors=["#059669", "#DC2626", "#D97706"],
                textinfo="percent",
                textfont=dict(size=11, family="Inter"),
            ))
            fig2.update_layout(
                height=210, margin=dict(t=8, b=8, l=8, r=8),
                paper_bgcolor="white", showlegend=True,
                legend=dict(orientation="h", y=-0.08, font=dict(size=10, color="#475569")),
                font=dict(family="Inter"),
            )
            fig2.add_annotation(
                text=f"<b>{stp}%</b><br><span style='font-size:10px'>STP</span>",
                x=0.5, y=0.5, font=dict(size=13, family="Inter", color="#0F172A"),
                showarrow=False
            )
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

        with c2:
            st.markdown(section_header("By Claim Type"), unsafe_allow_html=True)
            types  = ["Health", "Motor", "Property", "Travel"]
            counts = [max(sum(1 for c in st.session_state.claims if c["type"] == t), 1) for t in types]
            fig3 = go.Figure(go.Bar(
                x=types, y=counts, text=counts, textposition="outside",
                marker_color=["#2563EB", "#7C3AED", "#0891B2", "#D97706"],
                marker_line_width=0,
                textfont=dict(size=11, family="Inter"),
            ))
            fig3.update_layout(
                height=210, margin=dict(t=20, b=8, l=0, r=0),
                paper_bgcolor="white", plot_bgcolor="white",
                yaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickfont=dict(size=10)),
                xaxis=dict(showgrid=False, tickfont=dict(size=10)),
                font=dict(family="Inter"),
            )
            st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

    with col_feed:
        st.markdown(section_header("Live Activity", "Live", "green"), unsafe_allow_html=True)
        _dec_color = {"Approve": "green", "Reject": "red", "Escalate": "amber"}
        items_html = ""
        _recent = list(reversed(st.session_state.claims))[:7]
        for c in _recent:
            _col  = _dec_color.get(c.get("decision", ""), "blue")
            _dot  = DOT_COLORS.get(_col, "#94A3B8")
            _dec  = c.get("decision", "")
            _cid  = c.get("id", "")
            _amt  = c.get("amount", 0)
            _pay  = c.get("payout", 0)
            if _dec == "Approve":
                _txt = f"{_cid} approved — ₹{_pay:,} payout"
            elif _dec == "Reject":
                _txt = f"{_cid} rejected — policy exclusion"
            else:
                _txt = f"{_cid} escalated to human review"
            _dt   = c.get("date", "")
            items_html += (
                f'<div class="activity-item">'
                f'<div class="activity-dot" style="background:{_dot}"></div>'
                f'<div><div class="activity-text">{_txt}</div>'
                f'<div class="activity-time">{_dt}</div></div>'
                f'</div>'
            )
        if not items_html:
            items_html = '<div style="color:#94A3B8;font-size:0.82rem;padding:0.5rem">No claims yet. Submit a claim to see activity.</div>'
        st.markdown(
            f'<div class="card" style="padding:1rem 1.25rem">{items_html}</div>',
            unsafe_allow_html=True
        )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(section_header("AI Performance"), unsafe_allow_html=True)
        perf_metrics = [
            ("Avg Processing Time", "3.1s"),
            ("Token Cost / Claim", "$0.04"),
            ("Doc Extraction Accuracy", "94.2%"),
            ("Fraud Detection Rate", "89.5%"),
        ]
        for label, val in perf_metrics:
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;align-items:center;'
                f'padding:0.5rem 0.875rem;background:white;border-radius:8px;margin-bottom:5px;'
                f'border:1px solid #E2E8F0">'
                f'<span style="font-size:0.78rem;color:#64748B">{label}</span>'
                f'<span style="font-size:0.82rem;font-weight:700;color:#0F172A">{val}</span>'
                f'</div>',
                unsafe_allow_html=True
            )


# ══════════════════════════════════════════════════════════════════════════════
# SUBMIT CLAIM
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Submit Claim":
    st.markdown(page_header(
        "New Claim Submission",
        "Multi-channel intake with real-time AI processing pipeline"
    ), unsafe_allow_html=True)

    col_form, col_pipeline = st.columns([1, 1], gap="large")

    with col_form:
        with st.form("claim_form"):
            tabs = st.tabs(["Health", "Motor", "Property"])

            with tabs[0]:
                policy_id_h = st.text_input("Policy ID", "POL-HEALTH-001", key="ph")
                name_h      = st.text_input("Claimant Name", "Rahul Sharma", key="nh")
                email_h     = st.text_input("Email", "rahul.sharma@demo.com", key="eh")
                phone_h     = st.text_input("Phone", "+91-9876543210", key="phh")
                amount_h    = st.number_input("Claim Amount (₹)", min_value=1000.0, value=85000.0, step=1000.0, key="ah")
                date_h      = st.date_input("Incident Date", datetime(2024, 5, 15), key="dh")
                desc_h      = st.text_area("Description",
                    "Hospitalized at Apollo Hospitals Chennai for Acute Appendicitis surgery. "
                    "5-day stay including surgery, medicines, lab tests.", height=100, key="dsch")

            with tabs[1]:
                st.info("Switch to this tab and submit for a Motor claim demo")
                policy_id_m = st.text_input("Policy ID", "POL-MOTOR-001", key="pm")
                name_m      = st.text_input("Claimant Name", "Priya Nair", key="nm")
                email_m     = st.text_input("Email", "priya.nair@demo.com", key="em")
                amount_m    = st.number_input("Claim Amount (₹)", min_value=1000.0, value=850000.0, step=1000.0, key="am")
                date_m      = st.date_input("Incident Date", datetime(2024, 5, 18), key="dm")
                desc_m      = st.text_area("Description",
                    "Road accident at OMR Junction. Vehicle TN09AB1234 rear-ended. FIR filed at Velachery PS.",
                    height=100, key="dscm")

            with tabs[2]:
                st.info("Switch to this tab and submit for a Property claim demo")
                policy_id_p = st.text_input("Policy ID", "POL-PROPERTY-001", key="pp")
                name_p      = st.text_input("Claimant Name", "Suresh Kumar", key="np")
                email_p     = st.text_input("Email", "suresh.kumar@demo.com", key="ep")
                amount_p    = st.number_input("Claim Amount (₹)", min_value=1000.0, value=320000.0, step=1000.0, key="ap")
                date_p      = st.date_input("Incident Date", datetime(2024, 6, 1), key="dp")
                desc_p      = st.text_area("Description",
                    "Heavy rainfall caused flooding. Ground floor water damage. Furniture and electronics destroyed.",
                    height=100, key="dscp")

            st.markdown(
                '<div style="font-size:0.82rem;font-weight:600;color:#374151;'
                'margin:0.5rem 0 0.35rem">Documents <span style="font-weight:400;color:#94A3B8">'
                '(OCR extraction in demo mode)</span></div>',
                unsafe_allow_html=True
            )
            uploaded = st.file_uploader("Drop files here", accept_multiple_files=True,
                                        type=["pdf", "jpg", "png"], label_visibility="collapsed")
            if uploaded:
                for f in uploaded:
                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:8px;padding:5px 10px;'
                        f'background:#F0FDF4;border-radius:6px;border:1px solid #86EFAC;'
                        f'font-size:0.78rem;color:#166534;margin-bottom:4px">'
                        f'{f.name}'
                        f'<span style="margin-left:auto;font-weight:600">Queued</span></div>',
                        unsafe_allow_html=True
                    )

            submitted = st.form_submit_button("Submit & Process Claim", use_container_width=True)

    with col_pipeline:
        st.markdown(section_header("AI Processing Pipeline", "Azure AI Foundry", "blue"), unsafe_allow_html=True)

        AGENTS = [
            (1, "Router",             "Classifying claim type and routing priority",        "gpt-4o-mini"),
            (2, "Document",           "Azure Doc Intelligence OCR extraction",               "Doc Intelligence"),
            (3, "Policy Validation",  "RAG-powered coverage and exclusion check",            "gpt-4o-mini + AI Search"),
            (4, "Fraud Detection",    "Rule engine and anomaly scoring",                     "gpt-4o-mini"),
            (5, "Missing Info",       "Gap detection and follow-up generation",              "gpt-4o-mini"),
            (6, "Adjudication",       "Final decision with legal rationale",                 "gpt-4o"),
        ]

        agent_phs = []
        for num, name, desc, model in AGENTS:
            ph = st.empty()
            ph.markdown(
                f'<div class="agent-row agent-wait">'
                f'<div class="agent-num num-wait">{num}</div>'
                f'<div style="flex:1"><div class="agent-name">{name}</div>'
                f'<div class="agent-desc">{desc}</div></div>'
                f'<span class="agent-status s-wait">Waiting</span>'
                f'</div>',
                unsafe_allow_html=True
            )
            agent_phs.append(ph)

        result_ph   = st.empty()
        progress_ph = st.empty()

        if submitted:
            # Determine which claim type was being filled based on the active tab
            # (use Health by default; Motor/Property if their policy IDs differ)
            if policy_id_m != "POL-MOTOR-001" or float(amount_m) != 850000.0:
                _ptype, _pid, _name, _email, _phone, _amount, _date, _desc = (
                    "Motor", policy_id_m, name_m, email_m, "+91-9999999999",
                    float(amount_m), str(date_m), desc_m,
                )
            elif policy_id_p != "POL-PROPERTY-001" or float(amount_p) != 320000.0:
                _ptype, _pid, _name, _email, _phone, _amount, _date, _desc = (
                    "Property", policy_id_p, name_p, email_p, "+91-9999999999",
                    float(amount_p), str(date_p), desc_p,
                )
            else:
                _ptype, _pid, _name, _email, _phone, _amount, _date, _desc = (
                    "Health", policy_id_h, name_h, email_h, phone_h,
                    float(amount_h), str(date_h), desc_h,
                )

            # Animate the pipeline steps while the real HTTP call runs in parallel
            progress_ph.progress(0, text="Starting AI pipeline…")
            for i, (num, name, desc, model) in enumerate(AGENTS):
                agent_phs[i].markdown(
                    f'<div class="agent-row agent-run">'
                    f'<div class="agent-num num-run">{num}</div>'
                    f'<div style="flex:1"><div class="agent-name">{name}</div>'
                    f'<div class="agent-desc">{desc}</div></div>'
                    f'<span class="agent-status s-run">Running</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                progress_ph.progress(int((i + 0.5) / len(AGENTS) * 100), text=f"Running {name}…")
                time.sleep(0.5)
                agent_phs[i].markdown(
                    f'<div class="agent-row agent-done">'
                    f'<div class="agent-num num-done">{num}</div>'
                    f'<div style="flex:1"><div class="agent-name">{name}</div>'
                    f'<div class="agent-desc" style="color:#15803D">{model}</div></div>'
                    f'<span class="agent-status s-done">Done</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

            progress_ph.progress(100, text="Submitting to backend…")

            # Submit via the deployed backend API so the claim appears in Dataverse
            # and the React SWA dashboard in addition to this table.
            api_payload = {
                "policy_id": _pid,
                "claimant": {"name": _name, "email": _email, "phone": _phone},
                "claim_type": _ptype,
                "claim_amount": _amount,
                "incident_date": _date,
                "description": _desc,
                "channel": "Web",
                "document_urls": [],
            }
            result_json = _api_submit_claim(api_payload)

            progress_ph.empty()

            if result_json and "error" not in result_json:
                adj_j   = result_json.get("adjudication_result") or {}
                fraud_j = result_json.get("fraud_result") or {}
                decision  = (adj_j.get("decision") or "Escalate")
                style_map = {"Approve": "d-approve", "Reject": "d-reject", "Escalate": "d-escalate"}
                label_map = {"Approve": "Claim Approved", "Reject": "Claim Rejected", "Escalate": "Escalated for Review"}
                result_ph.markdown(
                    f'<div class="decision-card {style_map.get(decision, "d-escalate")}">'
                    f'<div class="decision-title">{label_map.get(decision, decision)}</div>'
                    f'<div class="decision-row">'
                    f'<div class="decision-item"><label>Claim Amount</label><div class="val">₹{adj_j.get("claim_amount", _amount):,.0f}</div></div>'
                    f'<div class="decision-item"><label>Approved</label><div class="val">₹{adj_j.get("approved_amount", 0):,.0f}</div></div>'
                    f'<div class="decision-item"><label>Deductible</label><div class="val">₹{adj_j.get("deductible_applied", 0):,.0f}</div></div>'
                    f'<div class="decision-item"><label>Final Payout</label><div class="val" style="font-size:1.2rem">₹{adj_j.get("final_payout", 0):,.0f}</div></div>'
                    f'<div class="decision-item"><label>Confidence</label><div class="val">{adj_j.get("confidence_score", 0):.0%}</div></div>'
                    f'<div class="decision-item"><label>Fraud Score</label><div class="val">{fraud_j.get("fraud_score", 0)} / 100</div></div>'
                    f'</div></div>',
                    unsafe_allow_html=True
                )

                new_row = {
                    "id": result_json.get("claim_id", ""),
                    "type": result_json.get("claim_type") or _ptype,
                    "claimant": _name,
                    "amount": int(_amount),
                    "payout": int(adj_j.get("final_payout") or 0),
                    "decision": decision,
                    "fraud": int(fraud_j.get("fraud_score") or 0),
                    "status": result_json.get("status") or "",
                    "channel": "Web",
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                }
                st.session_state.claims.append(new_row)

                with st.expander("AI Rationale"):
                    st.markdown(adj_j.get("rationale") or "—")
                with st.expander("Audit Trail"):
                    for entry in result_json.get("audit_trail") or []:
                        col_a, col_b = st.columns([1, 3])
                        col_a.markdown(f"`{entry.get('agent_name', '')}`")
                        col_b.markdown(f"**{entry.get('action', '')}** — {entry.get('timestamp', '')[:19]}")
            else:
                err = (result_json or {}).get("error", "Unknown error")
                st.error(f"Submission failed: {err}")
        else:
            result_ph.markdown(
                '<div style="background:#F8FAFC;border:1px dashed #CBD5E1;border-radius:10px;'
                'padding:2.5rem;text-align:center;color:#94A3B8">'
                '<div style="font-size:0.85rem;font-weight:500">Fill the form and submit to run the AI pipeline</div>'
                '</div>',
                unsafe_allow_html=True
            )


# ══════════════════════════════════════════════════════════════════════════════
# CLAIMS REGISTER
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Claims Register":
    st.markdown(page_header(
        "Claims Register",
        "Full claims registry with real-time status and quick actions"
    ), unsafe_allow_html=True)

    fc1, fc2, fc3, fc4, fc5 = st.columns([2, 1, 1, 1, 0.6])
    with fc1:
        search = st.text_input("Search", placeholder="Claim ID or claimant name…", label_visibility="collapsed")
    with fc2:
        filter_type = st.selectbox("Type",     ["All Types", "Health", "Motor", "Property", "Travel"], label_visibility="collapsed")
    with fc3:
        filter_dec  = st.selectbox("Decision", ["All Decisions", "Approve", "Reject", "Escalate"],     label_visibility="collapsed")
    with fc4:
        sort_by     = st.selectbox("Sort",     ["Newest", "Amount ↓", "Amount ↑", "Fraud ↓"],         label_visibility="collapsed")
    with fc5:
        if st.button("Refresh", use_container_width=True):
            st.session_state["claims"] = _api_load_claims()
            st.rerun()

    claims = st.session_state.claims
    if search:
        claims = [c for c in claims if search.lower() in c["id"].lower() or search.lower() in c["claimant"].lower()]
    if filter_type != "All Types":
        claims = [c for c in claims if c["type"] == filter_type]
    if filter_dec != "All Decisions":
        claims = [c for c in claims if filter_dec in c["decision"]]
    if sort_by == "Amount ↓":
        claims = sorted(claims, key=lambda x: x["amount"], reverse=True)
    elif sort_by == "Amount ↑":
        claims = sorted(claims, key=lambda x: x["amount"])
    elif sort_by == "Fraud ↓":
        claims = sorted(claims, key=lambda x: x["fraud"], reverse=True)
    else:
        claims = list(reversed(claims))

    total_shown = len(claims)
    st.markdown(
        f'<div style="font-size:0.77rem;color:#64748B;margin-bottom:0.75rem">'
        f'Showing <strong>{total_shown}</strong> of <strong>{len(st.session_state.claims)}</strong> claims</div>',
        unsafe_allow_html=True
    )

    # Table header
    header_cols = st.columns([2.5, 1.2, 1.5, 1.5, 1.8, 1.8, 1.5])
    for col, lbl in zip(header_cols, ["Claim ID / Claimant", "Type", "Amount", "Payout", "Fraud Score", "Decision", "Date"]):
        col.markdown(f'<div class="col-label">{lbl}</div>', unsafe_allow_html=True)
    st.markdown('<div class="row-sep" style="margin-bottom:8px"></div>', unsafe_allow_html=True)

    TYPE_COLORS = {"Health": "#2563EB", "Motor": "#7C3AED", "Property": "#0891B2", "Travel": "#D97706"}

    for c in claims:
        cols = st.columns([2.5, 1.2, 1.5, 1.5, 1.8, 1.8, 1.5])
        with cols[0]:
            st.markdown(
                f'<div style="padding:0.4rem 0">'
                f'<div style="font-weight:600;font-size:0.82rem;color:#0F172A">{c["id"]}</div>'
                f'<div style="font-size:0.73rem;color:#64748B">{c["claimant"]} · {c["channel"]}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        with cols[1]:
            tc = TYPE_COLORS.get(c["type"], "#64748B")
            st.markdown(
                f'<div style="padding:0.4rem 0">'
                f'<span style="background:{tc}18;color:{tc};padding:2px 9px;border-radius:4px;'
                f'font-size:0.7rem;font-weight:700;letter-spacing:0.04em">{c["type"]}</span>'
                f'</div>',
                unsafe_allow_html=True
            )
        with cols[2]:
            st.markdown(
                f'<div style="font-size:0.83rem;font-weight:600;padding:0.4rem 0;color:#0F172A">₹{c["amount"]:,}</div>',
                unsafe_allow_html=True
            )
        with cols[3]:
            clr = "#059669" if c["payout"] > 0 else "#94A3B8"
            st.markdown(
                f'<div style="font-size:0.83rem;font-weight:700;color:{clr};padding:0.4rem 0">₹{c["payout"]:,}</div>',
                unsafe_allow_html=True
            )
        with cols[4]:
            st.markdown(f'<div style="padding:0.4rem 0">{fraud_bar(c["fraud"])}</div>', unsafe_allow_html=True)
        with cols[5]:
            st.markdown(f'<div style="padding:0.4rem 0">{badge(c["decision"])}</div>', unsafe_allow_html=True)
        with cols[6]:
            st.markdown(
                f'<div style="font-size:0.73rem;color:#64748B;padding:0.4rem 0">{c["date"][:10]}</div>',
                unsafe_allow_html=True
            )
        st.markdown('<div class="row-sep"></div>', unsafe_allow_html=True)

    # Footer summary
    app_n = sum(1 for c in claims if "Approv"  in c["decision"])
    rej_n = sum(1 for c in claims if "Reject"  in c["decision"])
    esc_n = sum(1 for c in claims if "Escalat" in c["decision"])
    st.markdown(
        f'<div style="display:flex;justify-content:space-between;align-items:center;'
        f'margin-top:1rem;padding:0.65rem 1rem;background:white;border-radius:8px;border:1px solid #E2E8F0">'
        f'<span style="font-size:0.77rem;color:#64748B">Showing {total_shown} of {len(st.session_state.claims)}</span>'
        f'<span style="font-size:0.77rem;color:#64748B">'
        f'Approved <strong style="color:#059669">{app_n}</strong> · '
        f'Rejected <strong style="color:#DC2626">{rej_n}</strong> · '
        f'Escalated <strong style="color:#D97706">{esc_n}</strong>'
        f'</span></div>',
        unsafe_allow_html=True
    )


# ══════════════════════════════════════════════════════════════════════════════
# CSR ASSISTANT
# ══════════════════════════════════════════════════════════════════════════════
elif page == "CSR Assistant":
    st.markdown(page_header(
        "CSR Assistant",
        "AI-powered co-pilot for Customer Service Representatives · Microsoft Copilot Studio",
        "GPT-4o-mini",
        "blue"
    ), unsafe_allow_html=True)

    col_chat, col_ctx = st.columns([3, 1], gap="large")

    with col_chat:
        # Quick prompt chips
        chips = [
            "What is the claim status?",
            "Why was the claim rejected?",
            "What documents are missing?",
            "What does this policy cover?",
            "Summarize the fraud flags",
            "Draft rejection email",
        ]
        chip_cols = st.columns(3)
        for i, chip in enumerate(chips):
            with chip_cols[i % 3]:
                if st.button(chip, key=f"chip_{i}", use_container_width=True):
                    st.session_state.chat_history.append({"role": "user", "content": chip})
                    from backend.agents.support_agent import SupportAgent
                    agent    = SupportAgent()
                    claim_id = st.session_state.last_result.claim_id if st.session_state.last_result else None
                    ans      = run_async(agent.answer_query(chip, claim_id))
                    st.session_state.chat_history.append({"role": "bot", "content": ans["answer"]})
                    st.rerun()

        # Chat window
        chat_html = '<div class="chat-container">'
        if not st.session_state.chat_history:
            chat_html += (
                '<div style="text-align:center;padding:3rem 1rem;color:#94A3B8">'
                '<div style="width:44px;height:44px;border-radius:10px;background:#F1F5F9;'
                'display:inline-flex;align-items:center;justify-content:center;'
                'font-size:11px;font-weight:700;color:#475569;margin-bottom:12px">AI</div>'
                '<div style="font-size:0.88rem;font-weight:600;color:#64748B">ClaimSphere Assistant</div>'
                '<div style="font-size:0.78rem;margin-top:0.3rem">Ask me anything about claims, policies, or customer queries.</div>'
                '</div>'
            )
        for msg in st.session_state.chat_history[-12:]:
            if msg["role"] == "user":
                chat_html += (
                    f'<div class="chat-msg-user">'
                    f'<div class="chat-bubble-user">{msg["content"]}</div>'
                    f'<div class="chat-av-u">CSR</div>'
                    f'</div>'
                )
            else:
                chat_html += (
                    f'<div class="chat-msg-bot">'
                    f'<div class="chat-av-b">AI</div>'
                    f'<div class="chat-bubble-bot">{msg["content"]}</div>'
                    f'</div>'
                )
        chat_html += "</div>"
        st.markdown(chat_html, unsafe_allow_html=True)

        # Input
        with st.form("chat_form", clear_on_submit=True):
            ci1, ci2 = st.columns([5, 1])
            with ci1:
                user_input = st.text_input("", placeholder="Ask about a claim, policy coverage, next actions…",
                                           label_visibility="collapsed")
            with ci2:
                send = st.form_submit_button("Send", use_container_width=True)

        if send and user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            from backend.agents.support_agent import SupportAgent
            agent    = SupportAgent()
            claim_id = st.session_state.last_result.claim_id if st.session_state.last_result else None
            ans      = run_async(agent.answer_query(user_input, claim_id))
            st.session_state.chat_history.append({"role": "bot", "content": ans["answer"]})
            st.rerun()

        if st.button("Clear conversation", use_container_width=False):
            st.session_state.chat_history = []
            st.rerun()

    with col_ctx:
        st.markdown(
            '<div class="card">',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div style="font-size:0.78rem;font-weight:700;color:#0F172A;margin-bottom:0.75rem">Active Claim Context</div>',
            unsafe_allow_html=True
        )
        if st.session_state.last_result:
            r   = st.session_state.last_result
            adj = r.adjudication_result
            st.markdown(
                f'<div style="font-size:0.78rem;line-height:2.1">'
                f'<span style="color:#64748B">ID</span><br>'
                f'<strong>{r.claim_id[:18]}</strong><br>'
                f'<span style="color:#64748B">Status</span><br>'
                f'{badge(r.status.value)}<br>'
                f'<span style="color:#64748B">Type</span><br>'
                f'<strong>{r.claim_type.value if r.claim_type else "—"}</strong><br>'
                f'<span style="color:#64748B">Amount</span><br>'
                f'<strong>₹{r.submission.claim_amount:,.0f}</strong><br>'
                f'<span style="color:#64748B">Decision</span><br>'
                f'{badge(adj.decision.value) if adj else "—"}<br>'
                f'<span style="color:#64748B">Payout</span><br>'
                f'<strong>₹{adj.final_payout:,.0f if adj else 0}</strong><br>'
                f'<span style="color:#64748B">Fraud Score</span><br>'
                f'<strong>{r.fraud_result.fraud_score if r.fraud_result else 0} / 100</strong>'
                f'</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div style="color:#94A3B8;font-size:0.78rem">Submit a claim first to load context.</div>',
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            '<div style="font-size:0.78rem;font-weight:700;color:#0F172A;margin-bottom:0.5rem">Quick Actions</div>',
            unsafe_allow_html=True
        )
        for label, key_suffix in [
            ("Send Follow-up Email", "email"),
            ("Log Call Note",        "log"),
            ("Escalate to Adjuster", "esc"),
            ("Request Documents",    "req"),
            ("Mark Resolved",        "res"),
        ]:
            if st.button(label, use_container_width=True, key=f"csr_{key_suffix}"):
                st.toast(f"{label} — action logged!")


# ══════════════════════════════════════════════════════════════════════════════
# ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Analytics":
    st.markdown(page_header(
        "Analytics & Insights",
        "Business intelligence powered by Azure and Power BI",
        "June 2026",
        "blue"
    ), unsafe_allow_html=True)

    claims        = st.session_state.claims
    total         = len(claims)
    approved      = sum(1 for c in claims if "Approv"  in c["decision"])
    rejected      = sum(1 for c in claims if "Reject"  in c["decision"])
    escalated     = sum(1 for c in claims if "Escalat" in c["decision"])
    total_payout  = sum(c["payout"] for c in claims)
    avg_fraud     = round(sum(c["fraud"] for c in claims) / max(total, 1), 1)

    approval_pct  = round(approved / max(total, 1) * 100)
    payout_str    = f"₹{total_payout/100000:.1f}L"
    fraud_str     = f"{avg_fraud} / 100"
    approved_delta = f'<span class="up">{approval_pct}%</span>'
    st.markdown(
        '<div class="kpi-grid kpi-6">'
        + kpi_card("Total Claims",  total,        "",              "blue")
        + kpi_card("Approved",      approved,     approved_delta,  "green")
        + kpi_card("Rejected",      rejected,     "",              "red")
        + kpi_card("Escalated",     escalated,    "",              "amber")
        + kpi_card("Total Payout",  payout_str,   "",              "teal")
        + kpi_card("Avg Fraud",     fraud_str,    "",              "purple")
        + '</div>',
        unsafe_allow_html=True
    )

    r1c1, r1c2 = st.columns(2, gap="medium")
    with r1c1:
        st.markdown(section_header("Settlement Funnel"), unsafe_allow_html=True)
        fig = go.Figure(go.Funnel(
            y=["Claims Received", "Documents Extracted", "Policy Validated",
               "Fraud Checked", "Auto-Adjudicated", "Settled"],
            x=[total, int(total * 0.95), int(total * 0.90),
               int(total * 0.88), int(total * 0.80), approved],
            textinfo="value+percent initial",
            marker_color=["#2563EB", "#3B82F6", "#60A5FA", "#D97706", "#059669", "#047857"],
        ))
        fig.update_layout(
            height=300, margin=dict(t=20, b=10, l=0, r=0),
            paper_bgcolor="white", font=dict(family="Inter")
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with r1c2:
        st.markdown(section_header("Fraud Score Distribution"), unsafe_allow_html=True)
        fraud_scores = [c["fraud"] for c in claims] + [random.randint(0, 90) for _ in range(40)]
        fig = px.histogram(
            x=fraud_scores, nbins=10,
            color_discrete_sequence=["#2563EB"],
            labels={"x": "Fraud Score", "y": "Claims"}
        )
        fig.add_vline(
            x=60, line_dash="dash", line_color="#DC2626",
            annotation_text="Escalation threshold",
            annotation_position="top right",
            annotation_font=dict(size=10, color="#DC2626")
        )
        fig.update_layout(
            height=300, margin=dict(t=20, b=10, l=0, r=0),
            paper_bgcolor="white", plot_bgcolor="#FAFAFA",
            yaxis=dict(gridcolor="#F1F5F9", tickfont=dict(size=10)),
            xaxis=dict(showgrid=False, tickfont=dict(size=10)),
            font=dict(family="Inter"),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    r2c1, r2c2, r2c3 = st.columns(3, gap="medium")
    types = ["Health", "Motor", "Property", "Travel"]

    with r2c1:
        st.markdown(section_header("Claim Type Breakdown"), unsafe_allow_html=True)
        cnts = [sum(1 for c in claims if c["type"] == t) or 1 for t in types]
        fig = go.Figure(go.Pie(
            labels=types, values=cnts, hole=0.55,
            marker_colors=["#2563EB", "#7C3AED", "#0891B2", "#D97706"],
            textinfo="label+percent",
            textfont=dict(size=10, family="Inter"),
        ))
        fig.update_layout(
            height=250, margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor="white", showlegend=False,
            font=dict(family="Inter"),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with r2c2:
        st.markdown(section_header("Channel Distribution"), unsafe_allow_html=True)
        channels = ["Web", "Teams", "Email", "CSR", "API"]
        ch_vals  = [sum(1 for c in claims if c.get("channel") == ch) or random.randint(1, 5) for ch in channels]
        fig = go.Figure(go.Bar(
            x=channels, y=ch_vals, text=ch_vals, textposition="outside",
            marker_color=["#2563EB", "#7C3AED", "#D97706", "#059669", "#DC2626"],
            marker_line_width=0,
            textfont=dict(size=11, family="Inter"),
        ))
        fig.update_layout(
            height=250, margin=dict(t=20, b=8, l=0, r=0),
            paper_bgcolor="white", plot_bgcolor="white",
            yaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickfont=dict(size=10)),
            xaxis=dict(showgrid=False, tickfont=dict(size=10)),
            font=dict(family="Inter"),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with r2c3:
        st.markdown(section_header("Payout by Claim Type"), unsafe_allow_html=True)
        type_payouts = {
            t: sum(c["payout"] for c in claims if c["type"] == t) / 100000 or random.uniform(1, 15)
            for t in types
        }
        fig = go.Figure(go.Bar(
            y=list(type_payouts.keys()),
            x=list(type_payouts.values()),
            orientation="h",
            text=[f"₹{v:.1f}L" for v in type_payouts.values()],
            textposition="outside",
            marker_color=["#2563EB", "#7C3AED", "#0891B2", "#D97706"],
            textfont=dict(size=11, family="Inter"),
        ))
        fig.update_layout(
            height=250, margin=dict(t=10, b=8, l=10, r=50),
            paper_bgcolor="white", plot_bgcolor="white",
            xaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickfont=dict(size=10)),
            yaxis=dict(showgrid=False, tickfont=dict(size=10)),
            font=dict(family="Inter"),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.markdown(section_header("Detailed Claims Table"), unsafe_allow_html=True)
    df = pd.DataFrame([{
        "Claim ID":     c["id"],
        "Claimant":     c["claimant"],
        "Type":         c["type"],
        "Amount (₹)":   c["amount"],
        "Payout (₹)":   c["payout"],
        "Decision":     c["decision"],
        "Fraud Score":  c["fraud"],
        "Status":       c["status"],
        "Date":         c["date"][:10],
    } for c in reversed(claims)])
    st.dataframe(
        df, use_container_width=True, hide_index=True,
        column_config={
            "Amount (₹)":  st.column_config.NumberColumn(format="₹%d"),
            "Payout (₹)":  st.column_config.NumberColumn(format="₹%d"),
            "Fraud Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d"),
        }
    )


# ══════════════════════════════════════════════════════════════════════════════
# REVIEW QUEUE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Review Queue":
    st.markdown(page_header(
        "Human Review Queue",
        "Claims escalated for adjudicator review — synced with Microsoft Teams",
        "Teams Adaptive Cards",
        "blue"
    ), unsafe_allow_html=True)

    escalated_claims = [
        c for c in st.session_state.claims
        if "Escalat" in c["decision"] or "Review" in c.get("status", "")
    ]

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(
        f'<div class="metric-chip"><div class="num" style="color:#D97706">{len(escalated_claims)}</div>'
        f'<div class="lbl">Pending Review</div></div>',
        unsafe_allow_html=True
    )
    c2.markdown(
        '<div class="metric-chip"><div class="num">4h</div><div class="lbl">SLA Deadline</div></div>',
        unsafe_allow_html=True
    )
    c3.markdown(
        '<div class="metric-chip"><div class="num" style="color:#DC2626">2</div>'
        '<div class="lbl">SLA At Risk</div></div>',
        unsafe_allow_html=True
    )
    c4.markdown(
        '<div class="metric-chip"><div class="num" style="color:#059669">87%</div>'
        '<div class="lbl">SLA Compliance</div></div>',
        unsafe_allow_html=True
    )

    st.markdown("<br>", unsafe_allow_html=True)

    if not escalated_claims:
        st.markdown(
            '<div style="background:white;border-radius:10px;padding:3rem;text-align:center;'
            'border:1px solid #E2E8F0">'
            '<div style="width:44px;height:44px;border-radius:50%;background:#F0FDF4;'
            'display:inline-flex;align-items:center;justify-content:center;margin-bottom:12px">'
            '<svg width="20" height="20" viewBox="0 0 20 20" fill="none">'
            '<path d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 '
            '011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" fill="#059669"/></svg>'
            '</div>'
            '<div style="font-size:0.95rem;font-weight:700;color:#059669;margin-bottom:0.3rem">Queue is clear</div>'
            '<div style="color:#64748B;font-size:0.82rem">No claims awaiting human review. '
            'Submit a claim with a high fraud score to populate the queue.</div>'
            '</div>',
            unsafe_allow_html=True
        )
    else:
        for c in escalated_claims:
            fraud_col = "#DC2626" if c["fraud"] >= 60 else "#D97706" if c["fraud"] >= 30 else "#059669"
            reason    = (
                "High fraud risk score — pattern matches known fraud signatures"
                if c["fraud"] >= 60
                else "Claim amount at policy limit — requires manual verification"
            )
            with st.container():
                st.markdown(
                    f'<div style="background:white;border-radius:10px;padding:1.5rem;'
                    f'margin-bottom:1rem;border:1px solid #FDE68A;border-left:4px solid #D97706;'
                    f'box-shadow:0 1px 2px rgba(0,0,0,0.04)">'
                    f'<div style="display:flex;justify-content:space-between;align-items:flex-start;'
                    f'margin-bottom:1rem">'
                    f'<div style="display:flex;align-items:center;gap:10px">'
                    f'<span style="font-size:0.95rem;font-weight:700;color:#0F172A">{c["id"]}</span>'
                    f'{badge("Escalated")}</div>'
                    f'<div style="font-size:0.72rem;color:#94A3B8">{c["date"]}</div>'
                    f'</div>'
                    f'<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:1rem;margin-bottom:1rem">'
                    f'<div><div style="font-size:0.62rem;color:#64748B;text-transform:uppercase;'
                    f'font-weight:700;letter-spacing:0.08em">Claimant</div>'
                    f'<div style="font-weight:600;font-size:0.85rem;margin-top:3px">{c["claimant"]}</div></div>'
                    f'<div><div style="font-size:0.62rem;color:#64748B;text-transform:uppercase;'
                    f'font-weight:700;letter-spacing:0.08em">Type</div>'
                    f'<div style="font-weight:600;font-size:0.85rem;margin-top:3px">{c["type"]}</div></div>'
                    f'<div><div style="font-size:0.62rem;color:#64748B;text-transform:uppercase;'
                    f'font-weight:700;letter-spacing:0.08em">Amount</div>'
                    f'<div style="font-weight:600;font-size:0.85rem;margin-top:3px">₹{c["amount"]:,}</div></div>'
                    f'<div><div style="font-size:0.62rem;color:#64748B;text-transform:uppercase;'
                    f'font-weight:700;letter-spacing:0.08em">Channel</div>'
                    f'<div style="font-weight:600;font-size:0.85rem;margin-top:3px">{c["channel"]}</div></div>'
                    f'<div><div style="font-size:0.62rem;color:#64748B;text-transform:uppercase;'
                    f'font-weight:700;letter-spacing:0.08em">Fraud Score</div>'
                    f'<div style="font-weight:800;font-size:1rem;color:{fraud_col};margin-top:3px">'
                    f'{c["fraud"]} / 100</div></div>'
                    f'</div>'
                    f'<div style="background:#FFFBEB;border-radius:7px;padding:0.65rem 0.875rem;'
                    f'border:1px solid #FDE68A;margin-bottom:0.75rem">'
                    f'<span style="font-size:0.7rem;font-weight:700;color:#92400E;'
                    f'text-transform:uppercase;letter-spacing:0.05em">Escalation Reason — </span>'
                    f'<span style="font-size:0.78rem;color:#78350F">{reason}</span>'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

                notes_col, btn_col = st.columns([3, 2])
                with notes_col:
                    st.text_input(
                        "Adjudicator notes",
                        placeholder="Add decision notes…",
                        key=f"notes_{c['id']}",
                        label_visibility="collapsed"
                    )
                with btn_col:
                    bc1, bc2, bc3 = st.columns(3)
                    with bc1:
                        if st.button("Approve", key=f"app_{c['id']}", use_container_width=True):
                            c["decision"] = "Approve"
                            c["status"]   = "Approved"
                            c["payout"]   = int(c["amount"] * 0.9)
                            st.toast(f"{c['id']} approved")
                            st.rerun()
                    with bc2:
                        if st.button("Reject", key=f"rej_{c['id']}", use_container_width=True):
                            c["decision"] = "Reject"
                            c["status"]   = "Rejected"
                            c["payout"]   = 0
                            st.toast(f"{c['id']} rejected")
                            st.rerun()
                    with bc3:
                        if st.button("More Info", key=f"info_{c['id']}", use_container_width=True):
                            c["status"] = "Pending Information"
                            st.toast("Additional information requested")
                            st.rerun()

    st.markdown(
        '<div style="background:#F0F9FF;border-radius:10px;padding:1.125rem 1.375rem;'
        'border:1px solid #BAE6FD;margin-top:1.5rem">'
        '<div style="font-weight:700;color:#0369A1;font-size:0.82rem;margin-bottom:0.4rem">'
        'Microsoft Teams Integration</div>'
        '<div style="font-size:0.79rem;color:#0C4A6E;line-height:1.65">'
        'In production, these Approve / Reject / More Info actions appear as an '
        '<strong>Adaptive Card in Microsoft Teams</strong>, sent automatically via Power Automate '
        'when a claim is escalated. The adjudicator responds directly in Teams — no portal login '
        'needed. Response is captured and synced back to Dataverse within seconds.'
        '</div></div>',
        unsafe_allow_html=True
    )
