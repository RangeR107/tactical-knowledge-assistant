"""Chat interface UI components."""

import streamlit as st

from app.utils import truncate, unique_sources


def render_chat_history(chat_history_obj) -> None:
    """Render all previous chat turns as styled message bubbles."""
    if not chat_history_obj or len(chat_history_obj) == 0:
        st.markdown(
            """
            <div style="text-align:center; padding:3rem; color:#475569;">
                <div style="font-size:3rem; margin-bottom:1rem;">💬</div>
                <div style="font-size:1rem; font-weight:500; color:#64748b;">
                    Ask a question to get started
                </div>
                <div style="font-size:0.8rem; margin-top:0.5rem; color:#475569;">
                    Upload documents and build the knowledge base first
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    for turn in chat_history_obj:
        # User bubble
        st.markdown(
            f"""
            <div class="user-message">
                <div class="message-label">You</div>
                {turn.human}
            </div>
            """,
            unsafe_allow_html=True,
        )
        # Assistant bubble
        st.markdown(
            f"""
            <div class="assistant-message">
                <div class="message-label">Assistant</div>
                {turn.assistant.replace(chr(10), "<br>")}
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_query_input(state: dict) -> str | None:
    """Render the query input row and return the submitted question or None."""
    kb_ready = state.get("vector_store") is not None

    placeholder = (
        "Ask a question about your documents…"
        if kb_ready
        else "Build the knowledge base first to enable querying…"
    )

    with st.form(key="query_form", clear_on_submit=True):
        col_input, col_btn = st.columns([5, 1])
        with col_input:
            question = st.text_input(
                "Query",
                placeholder=placeholder,
                disabled=not kb_ready,
                label_visibility="collapsed",
            )
        with col_btn:
            submitted = st.form_submit_button(
                "Send",
                type="primary",
                disabled=not kb_ready,
                use_container_width=True,
            )

    if submitted and question.strip():
        return question.strip()
    return None


def render_answer_card(answer: str, docs: list, latency: float, settings: dict) -> None:
    """Render the latest answer with sources and context.

    Args:
        answer: The LLM-generated answer string.
        docs: Retrieved LangChain Document objects.
        latency: Response generation time in seconds.
        settings: UI settings dict (show_context, show_sources).
    """
    # Latest answer display
    st.markdown(
        f"""
        <div class="assistant-message" style="margin-bottom:1rem;">
            <div class="message-label">Assistant</div>
            {answer.replace(chr(10), "<br>")}
            <div class="latency-info">⏱ {latency:.2f}s</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Sources
    if settings.get("show_sources") and docs:
        sources = unique_sources(docs)
        st.markdown(
            "**Sources:** " + " &nbsp;·&nbsp; ".join(f"`{s}`" for s in sources),
            unsafe_allow_html=True,
        )

    # Retrieved context expander
    if settings.get("show_context") and docs:
        with st.expander(f"📄 Retrieved Context ({len(docs)} chunk(s))", expanded=False):
            for i, doc in enumerate(docs, 1):
                source = doc.metadata.get("source", "Unknown")
                chunk_idx = doc.metadata.get("chunk_index", "?")
                excerpt = truncate(doc.page_content.strip(), 400)
                st.markdown(
                    f"""
                    <div class="source-card">
                        <div class="source-name">📌 [{i}] {source} &nbsp;·&nbsp; chunk {chunk_idx}</div>
                        <div class="source-excerpt">{excerpt}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def render_action_buttons(state: dict) -> None:
    """Render action buttons below the chat (clear history, etc.)."""
    col1, col2, col3 = st.columns([1, 1, 4])

    with col1:
        if st.button("🗑️ Clear Chat", help="Clear conversation history"):
            state["action"] = "clear_chat"

    with col2:
        if st.button("📋 Copy Last", help="Copy the last answer to clipboard (manual)"):
            last = state.get("last_answer", "")
            st.code(last, language=None)
