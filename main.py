"""
Tactical Knowledge Assistant — Streamlit entry point.

Run with:
    streamlit run main.py
"""

import streamlit as st

from app.config import config
from app.chat_history import ChatHistory
from app.chunker import chunk_documents
from app.logger import logger
from app.rag_chain import RAGChain
from app.vector_store import (
    build_vector_store,
    delete_vector_store,
    get_store_stats,
    load_vector_store,
    store_exists,
)
from ui.sidebar import render_sidebar
from ui.chat import render_answer_card, render_action_buttons, render_chat_history, render_query_input
from ui.styles import CUSTOM_CSS


# ── Page configuration ────────────────────────────────────────────────────────

st.set_page_config(
    page_title=config.ui["page_title"],
    page_icon=config.ui["page_icon"],
    layout=config.ui["layout"],
    initial_sidebar_state="expanded",
)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ── Session state initialisation ──────────────────────────────────────────────

def _init_state() -> None:
    defaults: dict = {
        "vector_store": None,
        "rag_chain": None,
        "chat_history_obj": ChatHistory(),
        "pending_docs": [],
        "loaded_file_names": set(),
        "documents_loaded": False,
        "kb_stats": {},
        "last_answer": "",
        "last_latency": 0.0,
        "action": None,
        "settings": {
            "model": config.llm["model"],
            "top_k": config.retrieval["top_k"],
            "temperature": config.llm["temperature"],
            "show_context": True,
            "show_sources": True,
        },
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

    # Auto-load persisted vector store on startup
    if st.session_state["vector_store"] is None and store_exists():
        try:
            vs = load_vector_store()
            if vs:
                st.session_state["vector_store"] = vs
                st.session_state["rag_chain"] = RAGChain(vs)
                st.session_state["kb_stats"] = get_store_stats(vs)
                logger.info("Persisted knowledge base auto-loaded on startup")
        except Exception as exc:
            logger.warning(f"Could not auto-load persisted KB: {exc}")


_init_state()


# ── Action handler ────────────────────────────────────────────────────────────

def handle_actions() -> None:
    """Process deferred actions set by sidebar/chat components."""
    action = st.session_state.get("action")
    if action is None:
        return

    st.session_state["action"] = None  # consume action

    if action == "build_kb":
        _build_knowledge_base()

    elif action == "reset_kb":
        _reset_knowledge_base()

    elif action == "clear_chat":
        history: ChatHistory = st.session_state["chat_history_obj"]
        history.clear()
        st.session_state["last_answer"] = ""
        st.success("Chat history cleared.")
        st.rerun()


def _build_knowledge_base() -> None:
    pending = st.session_state.get("pending_docs", [])
    if not pending:
        st.warning("No documents to index. Upload files first.")
        return

    with st.spinner("Chunking and embedding documents… This may take a minute."):
        try:
            progress = st.progress(0, text="Chunking documents…")
            chunks = chunk_documents(pending)
            progress.progress(0.3, text=f"Created {len(chunks)} chunks — building FAISS index…")

            vs = build_vector_store(chunks)
            progress.progress(0.9, text="Saving index to disk…")

            st.session_state["vector_store"] = vs
            st.session_state["rag_chain"] = RAGChain(vs)
            st.session_state["kb_stats"] = get_store_stats(vs)
            st.session_state["pending_docs"] = []

            progress.progress(1.0, text="Done!")
            progress.empty()

            stats = st.session_state["kb_stats"]
            st.success(
                f"✅ Knowledge base built successfully! "
                f"{stats.get('total_vectors', 0)} vectors indexed."
            )
            logger.info(f"Knowledge base built: {stats.get('total_vectors', 0)} vectors")
            st.rerun()
        except Exception as exc:
            st.error(f"Failed to build knowledge base: {exc}")
            logger.error(f"KB build failed: {exc}", exc_info=True)


def _reset_knowledge_base() -> None:
    try:
        delete_vector_store()
        st.session_state["vector_store"] = None
        st.session_state["rag_chain"] = None
        st.session_state["kb_stats"] = {}
        st.session_state["pending_docs"] = []
        st.session_state["loaded_file_names"] = set()
        st.session_state["documents_loaded"] = False
        history: ChatHistory = st.session_state["chat_history_obj"]
        history.clear()
        st.session_state["last_answer"] = ""
        st.success("🗑️ Knowledge base reset. Upload new documents to start fresh.")
        logger.info("Knowledge base reset by user")
        st.rerun()
    except Exception as exc:
        st.error(f"Failed to reset knowledge base: {exc}")
        logger.error(f"KB reset failed: {exc}", exc_info=True)


# ── Query handler ─────────────────────────────────────────────────────────────

def handle_query(question: str) -> None:
    """Run the RAG chain for a user question and update session state."""
    rag: RAGChain | None = st.session_state.get("rag_chain")
    if rag is None:
        st.error("Knowledge base not ready. Build it first.")
        return

    history: ChatHistory = st.session_state["chat_history_obj"]

    with st.spinner("Thinking…"):
        try:
            result = rag.run(
                question=question,
                chat_history=history.as_list(),
            )
            answer = result["answer"]
            docs = result["source_documents"]
            latency = result["latency_seconds"]

            history.add(human=question, assistant=answer)
            st.session_state["last_answer"] = answer
            st.session_state["last_latency"] = latency
            st.session_state["last_docs"] = docs

            logger.info(f"Query answered in {latency:.2f}s")
            st.rerun()
        except Exception as exc:
            st.error(f"Error generating response: {exc}")
            logger.error(f"Query failed: {exc}", exc_info=True)


# ── Main layout ───────────────────────────────────────────────────────────────

def main() -> None:
    # Sidebar (mutates session_state via the state dict alias)
    render_sidebar(st.session_state)

    # Handle any deferred actions from sidebar
    handle_actions()

    # ── Header ────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="main-header">
            <h1>🎯 Tactical Knowledge Assistant</h1>
            <p>Fully offline AI assistant powered by local SLM + RAG • Upload documents and ask questions</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Quick-start notice ─────────────────────────────────────────────────
    if st.session_state["vector_store"] is None:
        st.info(
            "👋 **Getting started:** Upload your documents in the sidebar, click **Build KB**, "
            "then start asking questions below."
        )

    st.divider()

    # ── Chat history ───────────────────────────────────────────────────────
    render_chat_history(st.session_state["chat_history_obj"])

    # ── Latest answer + context (shown after a fresh query) ───────────────
    last_answer = st.session_state.get("last_answer", "")
    last_docs = st.session_state.get("last_docs", [])
    last_latency = st.session_state.get("last_latency", 0.0)

    if last_answer and last_docs:
        st.divider()
        st.markdown("#### Latest Response")
        render_answer_card(
            answer=last_answer,
            docs=last_docs,
            latency=last_latency,
            settings=st.session_state.get("settings", {}),
        )

    st.divider()

    # ── Query input ────────────────────────────────────────────────────────
    question = render_query_input(st.session_state)
    if question:
        handle_query(question)

    # ── Action buttons ─────────────────────────────────────────────────────
    render_action_buttons(st.session_state)

    # Handle clear_chat from action buttons
    if st.session_state.get("action") == "clear_chat":
        st.session_state["action"] = None
        history: ChatHistory = st.session_state["chat_history_obj"]
        history.clear()
        st.session_state["last_answer"] = ""
        st.session_state["last_docs"] = []
        st.rerun()


if __name__ == "__main__":
    main()
