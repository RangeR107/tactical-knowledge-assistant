"""Chat interface UI components using native Streamlit chat primitives."""

from datetime import datetime

import streamlit as st

from app.utils import truncate, unique_sources


# ── History renderer ─────────────────────────────────────────────────────────

def render_chat_history(chat_history_obj, settings: dict, last_docs: list, last_latency: float) -> None:
    """Render all previous chat turns using st.chat_message bubbles.

    Sources and context are shown only under the most recent assistant turn.
    """
    if not chat_history_obj or len(chat_history_obj) == 0:
        return

    turns = list(chat_history_obj)
    for i, turn in enumerate(turns):
        with st.chat_message("user", avatar="👤"):
            st.markdown(turn.human)

        with st.chat_message("assistant", avatar="🎯"):
            st.markdown(turn.assistant)

            # Attach metadata only to the last turn
            if i == len(turns) - 1 and last_docs:
                _render_answer_meta(last_docs, last_latency, settings)


def _render_answer_meta(docs: list, latency: float, settings: dict) -> None:
    """Render latency, sources, and context expander below an answer."""
    st.markdown(
        f'<span class="latency-tag">⏱ {latency:.2f}s &nbsp;·&nbsp; {len(docs)} chunks retrieved</span>',
        unsafe_allow_html=True,
    )

    if settings.get("show_sources") and docs:
        sources = unique_sources(docs)
        st.caption("**Sources:** " + " · ".join(f"`{s}`" for s in sources))

    if settings.get("show_context") and docs:
        with st.expander(f"📄 Retrieved Context ({len(docs)} chunks)", expanded=False):
            for i, doc in enumerate(docs, 1):
                source = doc.metadata.get("source", "Unknown")
                chunk = doc.metadata.get("chunk_index", "?")
                excerpt = truncate(doc.page_content.strip(), 400)
                st.markdown(
                    f"""
                    <div class="source-card">
                        <div class="source-title">📌 [{i}] {source} · chunk {chunk}</div>
                        <div class="source-text">{excerpt}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# ── Empty / welcome state ────────────────────────────────────────────────────

def render_welcome() -> None:
    """Show onboarding card when no KB is built yet."""
    st.markdown(
        """
        <div class="welcome-card">
            <div class="icon">🗂️</div>
            <h3>No knowledge base yet</h3>
            <p>Upload your documents in the sidebar, choose your Vector DB and Embedding model, then click <strong>⚡ Build KB</strong>.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    _step_card(col1, "1️⃣", "Upload", "PDF, DOCX, TXT, or Markdown files via the sidebar")
    _step_card(col2, "2️⃣", "Build KB", "Index documents into your chosen vector database")
    _step_card(col3, "3️⃣", "Ask", "Ask questions in natural language and get grounded answers")


def _step_card(col, icon: str, title: str, desc: str) -> None:
    with col:
        st.markdown(
            f"""
            <div style="background:#1e293b; border:1px solid #334155; border-radius:12px;
                        padding:1rem; text-align:center; height:130px;">
                <div style="font-size:1.5rem;">{icon}</div>
                <div style="color:#38bdf8; font-weight:700; font-size:0.85rem; margin:0.3rem 0;">{title}</div>
                <div style="color:#64748b; font-size:0.75rem; line-height:1.4;">{desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ── Query suggestions ────────────────────────────────────────────────────────

SAMPLE_QUESTIONS = [
    "What are the key principles of tactical operations?",
    "How do I establish an observation post?",
    "What does a SALUTE report contain?",
    "What are the best practices for knowledge management?",
]


def render_suggestions() -> str | None:
    """Show example query buttons. Returns the selected question or None."""
    st.markdown(
        '<div class="suggestion-label">💡 Try asking…</div>',
        unsafe_allow_html=True,
    )
    cols = st.columns(2)
    for i, q in enumerate(SAMPLE_QUESTIONS):
        with cols[i % 2]:
            if st.button(q, key=f"suggestion_{i}", use_container_width=True):
                return q
    return None


# ── Export chat ──────────────────────────────────────────────────────────────

def build_chat_export(chat_history_obj) -> str:
    """Convert chat history to a downloadable Markdown string."""
    lines = [
        "# Tactical Knowledge Assistant — Chat Export",
        f"*Exported on {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n",
        "---\n",
    ]
    for i, turn in enumerate(chat_history_obj, 1):
        lines.append(f"**[{i}] You:** {turn.human}\n")
        lines.append(f"**Assistant:** {turn.assistant}\n")
        lines.append("---\n")
    return "\n".join(lines)
