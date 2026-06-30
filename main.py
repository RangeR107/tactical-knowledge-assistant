"""
Tactical Knowledge Assistant — Streamlit entry point.

Run with:
    streamlit run main.py
"""

import os
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
    any_store_exists,
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

    # Auto-load persisted vector store on startup
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


# ── Action handler ────────────────────────────────────────────────────────────

def handle_actions() -> None:
    action = st.session_state.get("action")
    if not action:
        return
    st.session_state["action"] = None

    if action == "build_kb":
        _build_knowledge_base()
    elif action == "reset_kb":
        _reset_knowledge_base()
    elif action == "clear_chat":
        _clear_chat()


def _build_knowledge_base() -> None:
    pending = st.session_state.get("pending_docs", [])
    if not pending:
        st.warning("No documents to index. Upload files first.")
        return

    s = st.session_state["settings"]
    vdb = s.get("vector_db", DEFAULT_STORE_TYPE)
    emb = s.get("embedding_model", DEFAULT_EMBEDDING_MODEL)

    chunk_count_estimate = len(pending) * 8  # rough estimate
    time_estimate = max(1, chunk_count_estimate // 50)

    st.info(f"⏳ Embedding and indexing documents using **{vdb.upper()}** + `{emb.split('/')[-1]}`.\nThis may take ~{time_estimate} minute(s) for large documents.")

    progress = st.progress(0.0, text="Chunking documents…")

    try:
        chunks = chunk_documents(pending)
        progress.progress(0.05, text=f"Created {len(chunks)} chunks — starting embedding…")

        def on_progress(frac: float, msg: str) -> None:
            progress.progress(frac, text=msg)

        vs = build_vector_store(
            chunks,
            store_type=vdb,
            embedding_model=emb,
            progress_callback=on_progress,
        )

        progress.progress(1.0, text="✅ Done!")
        progress.empty()

        st.session_state["vector_store"] = vs
        st.session_state["rag_chain"] = _make_chain(vs)
        st.session_state["kb_stats"] = get_store_stats(vs, vdb)
        st.session_state["pending_docs"] = []

        n = st.session_state["kb_stats"].get("total_vectors", 0)
        st.success(f"✅ Knowledge base built — {n} vectors indexed ({vdb.upper()}).")
        logger.info(f"KB built: {n} vectors, backend={vdb}, embedding={emb}")
        st.rerun()

    except Exception as exc:
        progress.empty()
        st.error(f"Failed to build knowledge base: {exc}")
        logger.error(f"KB build failed: {exc}", exc_info=True)


def _reset_knowledge_base() -> None:
    try:
        s = st.session_state["settings"]
        vdb = s.get("vector_db", DEFAULT_STORE_TYPE)
        delete_vector_store(vdb)
        st.session_state.update({
            "vector_store": None, "rag_chain": None, "kb_stats": {},
            "pending_docs": [], "loaded_file_names": set(),
            "documents_loaded": False, "last_answer": "", "last_docs": [],
        })
        st.session_state["chat_history_obj"].clear()
        st.success("🗑️ Knowledge base reset.")
        logger.info("KB reset by user")
        st.rerun()
    except Exception as exc:
        st.error(f"Failed to reset: {exc}")


def _clear_chat() -> None:
    st.session_state["chat_history_obj"].clear()
    st.session_state["last_answer"] = ""
    st.session_state["last_docs"] = []
    st.rerun()


# ── Query handler ─────────────────────────────────────────────────────────────

def handle_query(question: str) -> None:
    rag: RAGChain | None = st.session_state.get("rag_chain")
    if rag is None:
        # Rebuild chain in case model/temperature changed
        vs = st.session_state.get("vector_store")
        if vs is None:
            st.error("Knowledge base not ready. Build it first.")
            return
        rag = _make_chain(vs)
        st.session_state["rag_chain"] = rag

    history: ChatHistory = st.session_state["chat_history_obj"]

    with st.spinner("Thinking…"):
        try:
            result = rag.run(question=question, chat_history=history.as_list())
            answer = result["answer"]
            docs = result["source_documents"]
            latency = result["latency_seconds"]

            history.add(human=question, assistant=answer)
            st.session_state.update({
                "last_answer": answer,
                "last_latency": latency,
                "last_docs": docs,
            })
            logger.info(f"Query answered in {latency:.2f}s")
            st.rerun()
        except Exception as exc:
            st.error(f"Error generating response: {exc}")
            logger.error(f"Query failed: {exc}", exc_info=True)


# ── Main layout ───────────────────────────────────────────────────────────────

def main() -> None:
    render_sidebar(st.session_state)
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

    if st.session_state["vector_store"] is None:
        st.info(
            "👋 **Getting started:** Upload documents in the sidebar → select your Vector DB & Embedding model → click **⚡ Build KB** → ask questions below."
        )

    st.divider()

    render_chat_history(st.session_state["chat_history_obj"])

    last_answer = st.session_state.get("last_answer", "")
    last_docs = st.session_state.get("last_docs", [])
    last_latency = st.session_state.get("last_latency", 0.0)

    if last_answer:
        st.divider()
        st.markdown("#### Latest Response")
        render_answer_card(
            answer=last_answer,
            docs=last_docs,
            latency=last_latency,
            settings=st.session_state.get("settings", {}),
        )

    st.divider()

    question = render_query_input(st.session_state)
    if question:
        handle_query(question)

    render_action_buttons(st.session_state)

    if st.session_state.get("action") == "clear_chat":
        st.session_state["action"] = None
        _clear_chat()


if __name__ == "__main__":
    main()
