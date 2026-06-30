"""Custom CSS styles for the Tactical Knowledge Assistant Streamlit UI."""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Sidebar ──────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0f1e 0%, #0f172a 60%, #1a1f35 100%);
    border-right: 1px solid #1e293b;
}
section[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
section[data-testid="stSidebar"] h3 {
    color: #38bdf8 !important;
    font-size: 0.7rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    margin: 1.2rem 0 0.4rem 0 !important;
}

/* ── Header ───────────────────────────────────────────── */
.main-header {
    background: linear-gradient(135deg, #0f172a 0%, #0c1f3f 50%, #0f2027 100%);
    border: 1px solid #1e3a5f;
    border-radius: 16px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
    box-shadow: 0 4px 32px rgba(14,165,233,0.12), 0 1px 0 rgba(56,189,248,0.1) inset;
}
.main-header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, transparent, #38bdf8, #818cf8, transparent);
}
.main-header h1 {
    color: #f1f5f9 !important;
    font-size: 1.7rem !important;
    font-weight: 700 !important;
    margin: 0 !important;
    letter-spacing: -0.02em;
}
.main-header p {
    color: #64748b !important;
    font-size: 0.85rem !important;
    margin: 0.3rem 0 0 0 !important;
}
.header-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    background: rgba(56,189,248,0.1);
    border: 1px solid rgba(56,189,248,0.3);
    border-radius: 999px;
    padding: 0.15rem 0.6rem;
    font-size: 0.65rem;
    color: #38bdf8 !important;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-top: 0.6rem;
    margin-right: 0.4rem;
}

/* ── Welcome / onboarding ─────────────────────────────── */
.welcome-card {
    background: linear-gradient(135deg, #0f172a, #1e293b);
    border: 1px dashed #334155;
    border-radius: 16px;
    padding: 2.5rem;
    text-align: center;
    margin: 1rem 0;
}
.welcome-card .icon { font-size: 3rem; margin-bottom: 0.8rem; }
.welcome-card h3 { color: #94a3b8 !important; font-size: 1.1rem !important; margin: 0 0 0.4rem 0 !important; }
.welcome-card p { color: #475569 !important; font-size: 0.85rem !important; margin: 0 !important; }

/* ── Suggestion buttons ───────────────────────────────── */
.suggestion-label {
    font-size: 0.72rem;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 600;
    margin-bottom: 0.6rem;
}

/* ── Source / context cards ───────────────────────────── */
.source-card {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-left: 3px solid #38bdf8;
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin-bottom: 0.6rem;
    font-size: 0.82rem;
}
.source-card .source-title {
    color: #38bdf8 !important;
    font-weight: 600;
    font-size: 0.78rem;
    margin-bottom: 0.3rem;
}
.source-card .source-text {
    color: #94a3b8 !important;
    line-height: 1.55;
}

/* ── Status badges ────────────────────────────────────── */
.status-badge {
    display: inline-flex; align-items: center; gap: 0.3rem;
    padding: 0.2rem 0.65rem; border-radius: 999px;
    font-size: 0.72rem; font-weight: 600;
}
.status-online  { background:#052e16; color:#4ade80; border:1px solid #166534; }
.status-offline { background:#450a0a; color:#f87171; border:1px solid #7f1d1d; }
.status-warning { background:#431407; color:#fb923c; border:1px solid #9a3412; }

/* ── Indexed docs ─────────────────────────────────────── */
.indexed-doc {
    display: flex; align-items: center; gap: 0.5rem;
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 6px;
    padding: 0.4rem 0.7rem;
    margin-bottom: 0.3rem;
    font-size: 0.78rem;
    color: #94a3b8 !important;
}
.indexed-doc .doc-icon { color: #38bdf8 !important; }

/* ── Log viewer ───────────────────────────────────────── */
.log-viewer {
    background: #020617;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 0.75rem;
    font-family: 'Fira Code', monospace;
    font-size: 0.72rem;
    color: #64748b;
    max-height: 250px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-break: break-all;
}

/* ── Latency ──────────────────────────────────────────── */
.latency-tag {
    display: inline-block;
    font-size: 0.7rem;
    color: #475569;
    background: #1e293b;
    border-radius: 4px;
    padding: 0.1rem 0.45rem;
    margin-top: 0.5rem;
}

/* ── Buttons ──────────────────────────────────────────── */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em !important;
    transition: all 0.2s ease !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
    border: none !important;
    color: white !important;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(37,99,235,0.4) !important;
}

/* ── Streamlit chat messages ──────────────────────────── */
[data-testid="stChatMessage"] {
    background: transparent !important;
}

/* ── Inputs ───────────────────────────────────────────── */
.stTextInput > div > div > input,
[data-testid="stChatInputTextArea"] textarea {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
}

/* ── File uploader ────────────────────────────────────── */
[data-testid="stFileUploader"] {
    background: #1e293b !important;
    border: 2px dashed #334155 !important;
    border-radius: 10px !important;
}

/* ── Expanders ────────────────────────────────────────── */
details summary { color: #38bdf8 !important; font-weight: 500 !important; }

/* ── Dividers ─────────────────────────────────────────── */
hr { border-color: #1e293b !important; margin: 0.8rem 0 !important; }

/* ── Scrollbar ────────────────────────────────────────── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #0f172a; }
::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #475569; }
</style>
"""
