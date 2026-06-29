"""Custom CSS styles for the Tactical Knowledge Assistant Streamlit UI."""

CUSTOM_CSS = """
<style>
/* ── Global ─────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Sidebar ────────────────────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    border-right: 1px solid #334155;
}

section[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}

section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #38bdf8 !important;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    font-size: 0.75rem;
    margin-top: 1.5rem;
    margin-bottom: 0.5rem;
}

/* ── Main header ────────────────────────── */
.main-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
    border: 1px solid #1e40af;
    border-radius: 12px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 24px rgba(14, 165, 233, 0.15);
}

.main-header h1 {
    color: #38bdf8 !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
    margin: 0 !important;
    letter-spacing: -0.02em;
}

.main-header p {
    color: #94a3b8 !important;
    font-size: 0.9rem !important;
    margin: 0.25rem 0 0 0 !important;
}

/* ── Chat messages ──────────────────────── */
.chat-container {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin-bottom: 1.5rem;
}

.user-message {
    background: linear-gradient(135deg, #1e3a5f, #1e40af);
    border: 1px solid #3b82f6;
    border-radius: 12px 12px 4px 12px;
    padding: 1rem 1.25rem;
    margin-left: 3rem;
    color: #e2e8f0 !important;
    box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
}

.assistant-message {
    background: linear-gradient(135deg, #0f2027, #1a2a3a);
    border: 1px solid #334155;
    border-radius: 12px 12px 12px 4px;
    padding: 1rem 1.25rem;
    margin-right: 3rem;
    color: #e2e8f0 !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.message-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
    opacity: 0.7;
}

.user-message .message-label { color: #93c5fd !important; }
.assistant-message .message-label { color: #6ee7b7 !important; }

/* ── Source cards ───────────────────────── */
.source-card {
    background: #0f172a;
    border: 1px solid #1e3a5f;
    border-left: 3px solid #38bdf8;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    font-size: 0.85rem;
}

.source-card .source-name {
    color: #38bdf8 !important;
    font-weight: 600;
    font-size: 0.8rem;
}

.source-card .source-excerpt {
    color: #94a3b8 !important;
    margin-top: 0.3rem;
    line-height: 1.5;
}

/* ── Status badges ──────────────────────── */
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.25rem 0.75rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
}

.status-online  { background: #052e16; color: #4ade80; border: 1px solid #166534; }
.status-offline { background: #450a0a; color: #f87171; border: 1px solid #7f1d1d; }
.status-warning { background: #431407; color: #fb923c; border: 1px solid #9a3412; }

/* ── Metric cards ───────────────────────── */
.metric-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 0.85rem 1rem;
    text-align: center;
}

.metric-card .metric-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: #38bdf8 !important;
}

.metric-card .metric-label {
    font-size: 0.7rem;
    color: #64748b !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 0.1rem;
}

/* ── Buttons ────────────────────────────── */
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
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4) !important;
}

/* ── Dividers ───────────────────────────── */
hr {
    border-color: #1e293b !important;
    margin: 1rem 0 !important;
}

/* ── Log viewer ─────────────────────────── */
.log-viewer {
    background: #020617;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 1rem;
    font-family: 'Fira Code', 'Courier New', monospace;
    font-size: 0.75rem;
    color: #94a3b8;
    max-height: 300px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-break: break-all;
}

/* ── Latency bar ────────────────────────── */
.latency-info {
    font-size: 0.75rem;
    color: #64748b;
    text-align: right;
    margin-top: 0.5rem;
    font-style: italic;
}

/* ── Input area ─────────────────────────── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
}

/* ── File uploader ──────────────────────── */
[data-testid="stFileUploader"] {
    background: #1e293b !important;
    border: 2px dashed #334155 !important;
    border-radius: 10px !important;
}

/* ── Expander ───────────────────────────── */
details summary {
    color: #38bdf8 !important;
    font-weight: 500 !important;
    cursor: pointer;
}

/* ── Scrollbar ──────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0f172a; }
::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #475569; }
</style>
"""
