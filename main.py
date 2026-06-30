"""
Tactical Knowledge Assistant — Streamlit entry point.

Run with:
    streamlit run main.py
"""

import os
import time

import streamlit as st

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")  # suppress chromadb telemetry

from app.config import config
from app.chat_history import ChatHistory
from app.chunker import chunk_documents
from app.embeddings import DEFAULT_EMBEDDING_MODEL
from app.logger import logger
from app.rag_chain import RAGChain
from app.vector_store import (
    DEFAULT_STORE_TYPE,
    build_vector_store,
    delete_vector_store,
    get_store_stats,
    load_vector_store,
    store_exists,
)
from ui.chat import (
    _render_answer_meta,
    build_chat_export,
    render_chat_history,
    render_suggestions,
    render_welcome,
)
from ui.sidebar import render_sidebar
from ui.styles import CUSTOM_CSS


# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title=config.ui["page_title"],
    page_icon=config.ui["page_icon"],
    layout=config.ui["layout"],
    initial_sidebar_state="expanded",
)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────

def _init_state() -> None:
    defaults: dict = {
        "vector_store": None,
        "rag_chain": None,
        "chat_history_obj": ChatHistory(),
        "pending_docs": [],
        "loaded_file_names": set(),
        "indexed_files": [],
        "documents_loaded": False,
        "kb_stats": {},
        "last_answer": "",
        "last_latency": 0.0,
        "last_docs": [],
        "action": None,
        "settings": {
            "model": config.llm["model"],
            "vector_db": DEFAULT_STORE_TYPE,
            "embedding_model": DEFAULT_EMBEDDING_MODEL,
            "top_k": config.retrieval["top_k"],
            "temperature": config.llm["temperature"],
            "show_context": True,
            "show_sources": True,
        },
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

    # Auto-load persisted store on startup
    if st.session_state["vector_store"] is None:
        s = st.session_state["settings"]
        vdb = s.get("vector_db", DEFAULT_STORE_TYPE)
        emb = s.get("embedding_model", DEFAULT_EMBEDDING_MODEL)
        if store_exists(vdb):
            try:
                vs = load_vector_store(store_type=vdb, embedding_model=emb)
                if vs:
                    st.session_state["vector_store"] = vs
                    st.session_state["rag_chain"] = _make_chain(vs)
                    st.session_state["kb_stats"] = get_store_stats(vs, vdb)
                    logger.info(f"Auto-loaded {vdb} KB on startup")
            except Exception as exc:
                logger.warning(f"Could not auto-load KB: {exc}")


def _make_chain(vs) -> RAGChain:
    s = st.session_state["settings"]
    return RAGChain(
        vector_store=vs,
        model_name=s.get("model"),
        temperature=s.get("temperature"),
        top_k=s.get("top_k"),
    )


_init_state()


# ── Actions ───────────────────────────────────────────────────────────────────

def handle_actions() -> None:
    action = st.session_state.get("action")
    if not action:
        return
    st.session_state["action"] = None

    if action == "build_kb":
        _build_knowledge_base()
    elif action == "reset_kb":
        _reset_knowledge_base()


def _build_knowledge_base() -> None:
    pending = st.session_state.get("pending_docs", [])
    if not pending:
        st.warning("No documents to index. Upload files first.")
        return

    s = st.session_state["settings"]
    vdb = s.get("vector_db", DEFAULT_STORE_TYPE)
    emb = s.get("embedding_model", DEFAULT_EMBEDDING_MODEL)

    chunk_estimate = len(pending) * 8
    time_estimate = max(1, chunk_estimate // 50)
    st.info(
        f"⏳ Indexing with **{vdb.upper()}** + `{emb.split('/')[-1]}` "
        f"— ~{time_estimate} minute(s) for large docs."
    )

    progress = st.progress(0.0, text="Chunking…")
    try:
        chunks = chunk_documents(pending)
        progress.progress(0.05, text=f"Created {len(chunks)} chunks — embedding…")

        vs = build_vector_store(
            chunks,
            store_type=vdb,
            embedding_model=emb,
            progress_callback=lambda frac, msg: progress.progress(frac, text=msg),
        )

        progress.progress(1.0, text="✅ Done!")
        progress.empty()

        st.session_state["vector_store"] = vs
        st.session_state["rag_chain"] = _make_chain(vs)
        st.session_state["kb_stats"] = get_store_stats(vs, vdb)
        st.session_state["indexed_files"] = sorted(st.session_state.get("loaded_file_names", set()))
        st.session_state["pending_docs"] = []

        n = st.session_state["kb_stats"].get("total_vectors", 0)
        st.success(f"✅ KB built — {n} vectors indexed ({vdb.upper()}).")
        logger.info(f"KB built: {n} vectors, backend={vdb}, embedding={emb}")
        st.rerun()

    except Exception as exc:
        progress.empty()
        st.error(f"Failed to build KB: {exc}")
        logger.error(f"KB build failed: {exc}", exc_info=True)


def _reset_knowledge_base() -> None:
    try:
        s = st.session_state["settings"]
        vdb = s.get("vector_db", DEFAULT_STORE_TYPE)
        delete_vector_store(vdb)
        st.session_state.update({
            "vector_store": None,
            "rag_chain": None,
            "kb_stats": {},
            "pending_docs": [],
            "loaded_file_names": set(),
            "indexed_files": [],
            "documents_loaded": False,
            "last_answer": "",
            "last_docs": [],
        })
        st.session_state["chat_history_obj"].clear()
        st.success("🗑️ Knowledge base reset.")
        logger.info("KB reset by user")
        st.rerun()
    except Exception as exc:
        st.error(f"Failed to reset: {exc}")


# ── Streaming query ───────────────────────────────────────────────────────────

def _handle_stream_query(question: str) -> None:
    state = st.session_state
    rag: RAGChain | None = state.get("rag_chain")
    if rag is None:
        vs = state.get("vector_store")
        if vs is None:
            st.error("Knowledge base not ready. Build it first.")
            return
        rag = _make_chain(vs)
        state["rag_chain"] = rag

    history: ChatHistory = state["chat_history_obj"]
    settings: dict = state["settings"]

    with st.chat_message("user", avatar="👤"):
        st.markdown(question)

    with st.chat_message("assistant", avatar="🎯"):
        try:
            start = time.perf_counter()
            retrieved_docs, token_gen = rag.stream(
                question, chat_history=history.as_list()
            )
            answer = st.write_stream(token_gen)
            latency = time.perf_counter() - start
            _render_answer_meta(retrieved_docs, latency, settings)
        except Exception as exc:
            answer = ""
            retrieved_docs = []
            latency = 0.0
            st.error(f"Error generating response: {exc}")
            logger.error(f"Stream query failed: {exc}", exc_info=True)

    if answer:
        history.add(human=question, assistant=str(answer))
        state.update({
            "last_answer": str(answer),
            "last_latency": latency,
            "last_docs": retrieved_docs,
        })
        logger.info(f"Query answered in {latency:.2f}s")


# ── Main layout ───────────────────────────────────────────────────────────────

def main() -> None:
    state = st.session_state
    render_sidebar(state)
    handle_actions()

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="main-header">
            <h1>🎯 Tactical Knowledge Assistant</h1>
            <p>Fully offline AI assistant powered by local LLM + RAG</p>
            <span class="header-badge">🔒 Offline</span>
            <span class="header-badge">⚡ Local LLM</span>
            <span class="header-badge">🗂️ RAG</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    history: ChatHistory = state["chat_history_obj"]
    kb_ready: bool = state["vector_store"] is not None
    settings: dict = state["settings"]

    # Consume pending question from suggestion click (set in previous rerun)
    pending_q: str | None = state.pop("pending_question", None)

    # ── Main content area ─────────────────────────────────────────────────────
    if len(history) > 0:
        render_chat_history(
            history,
            settings,
            state.get("last_docs", []),
            state.get("last_latency", 0.0),
        )
    elif kb_ready and not pending_q:
        # KB ready but no chat yet — show suggestion chips
        clicked = render_suggestions()
        if clicked:
            state["pending_question"] = clicked
            st.rerun()
    elif not kb_ready:
        render_welcome()

    # ── Chat input ────────────────────────────────────────────────────────────
    typed_q: str | None = None
    if kb_ready:
        typed_q = st.chat_input("Ask a question about your documents…")
    elif not kb_ready and len(history) == 0:
        pass  # welcome card already shown, no input needed
    else:
        st.info("Build a knowledge base first — upload documents and click **⚡ Build KB** in the sidebar.")

    question = typed_q or pending_q

    if question:
        if kb_ready:
            _handle_stream_query(question)
        else:
            st.warning("Build a knowledge base first!")

    # ── Toolbar (shown when there's chat history) ─────────────────────────────
    if len(history) > 0:
        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                history.clear()
                state.update({"last_answer": "", "last_docs": [], "last_latency": 0.0})
                st.rerun()


if __name__ == "__main__":
    main()
