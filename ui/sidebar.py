"""Sidebar UI components."""

import streamlit as st

from app.config import config
from app.document_loader import load_from_uploaded_file, SUPPORTED_EXTENSIONS
from app.embeddings import AVAILABLE_EMBEDDING_MODELS, DEFAULT_EMBEDDING_MODEL
from app.llm import get_available_models
from app.logger import logger
from app.utils import human_readable_size, read_log_tail
from app.vector_store import AVAILABLE_STORES, DEFAULT_STORE_TYPE


def render_sidebar(state: dict) -> None:
    with st.sidebar:
        # ── Brand ──────────────────────────────────────────────────────────
        st.markdown(
            """
            <div style="text-align:center; padding:0.5rem 0 1rem;">
                <div style="font-size:2.2rem;">🎯</div>
                <div style="color:#38bdf8;font-weight:700;font-size:1rem;letter-spacing:0.06em;">TACTICAL KA</div>
                <div style="color:#475569;font-size:0.68rem;margin-top:0.1rem;">v1.0.0 &nbsp;·&nbsp; Fully Offline</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()
        st.markdown("### 🔌 Status")
        _render_status(state)

        st.divider()
        st.markdown("### 🤖 Model")
        _render_model_selector(state)

        st.divider()
        st.markdown("### 🗃️ Vector DB & Embeddings")
        _render_vectordb_selector(state)

        st.divider()
        st.markdown("### 📁 Upload Documents")
        _render_upload(state)

        st.divider()
        st.markdown("### 🗄️ Knowledge Base")
        _render_kb_controls(state)

        # Indexed documents list
        _render_indexed_docs(state)

        st.divider()
        st.markdown("### 📊 Statistics")
        _render_stats(state)

        st.divider()
        st.markdown("### ⚙️ Settings")
        _render_settings(state)

        st.divider()
        with st.expander("📋 Application Logs", expanded=False):
            log_text = read_log_tail(config.logging_cfg["file"], n_lines=50)
            st.markdown(f'<div class="log-viewer">{log_text}</div>', unsafe_allow_html=True)
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()


# ── Helpers ──────────────────────────────────────────────────────────────────

def _render_status(state: dict) -> None:
    from app.llm import is_ollama_running, is_model_available

    ollama_ok = is_ollama_running()
    model_name = state.get("settings", {}).get("model", config.llm["model"])
    model_ok = is_model_available(model_name) if ollama_ok else False
    kb_ready = state.get("vector_store") is not None

    def badge(label, ok, warn=False):
        cls = "status-online" if ok else ("status-warning" if warn else "status-offline")
        icon = "●" if ok else ("◐" if warn else "○")
        return f'<span class="status-badge {cls}">{icon} {label}</span>&nbsp;'

    st.markdown(
        badge("Ollama", ollama_ok)
        + badge("Model", model_ok, warn=not model_ok and ollama_ok)
        + badge("KB", kb_ready),
        unsafe_allow_html=True,
    )

    if not ollama_ok:
        st.warning("Ollama not running. Run: `ollama serve`")
    elif not model_ok:
        st.warning(f"`{model_name}` not found. Run: `ollama pull {model_name}`")


def _render_model_selector(state: dict) -> None:
    settings = state.setdefault("settings", {})
    available = get_available_models()

    if not available:
        st.warning("No Ollama models found.")
        st.caption("Pull one: `ollama pull qwen2.5:3b`")
        return

    current = settings.get("model", config.llm["model"])
    if current not in available:
        current = available[0]

    selected = st.selectbox(
        "Ollama Model",
        options=available,
        index=available.index(current),
        help="All models currently downloaded in Ollama",
    )

    if selected != settings.get("model"):
        settings["model"] = selected
        state["rag_chain"] = None  # rebuild on next query
    else:
        settings["model"] = selected


def _render_vectordb_selector(state: dict) -> None:
    settings = state.setdefault("settings", {})

    store_keys = list(AVAILABLE_STORES.keys())
    current_store = settings.get("vector_db", DEFAULT_STORE_TYPE)
    if current_store not in store_keys:
        current_store = DEFAULT_STORE_TYPE

    selected_store = st.selectbox(
        "Vector Database",
        options=store_keys,
        format_func=lambda k: AVAILABLE_STORES[k],
        index=store_keys.index(current_store),
    )
    if selected_store != settings.get("vector_db"):
        settings["vector_db"] = selected_store
        if state.get("vector_store") is not None:
            state["vector_store"] = None
            state["rag_chain"] = None
            st.warning("⚠️ Vector DB changed — rebuild the KB.")
    settings["vector_db"] = selected_store

    emb_keys = list(AVAILABLE_EMBEDDING_MODELS.keys())
    current_emb = settings.get("embedding_model", DEFAULT_EMBEDDING_MODEL)
    if current_emb not in emb_keys:
        current_emb = DEFAULT_EMBEDDING_MODEL

    selected_emb = st.selectbox(
        "Embedding Model",
        options=emb_keys,
        format_func=lambda k: AVAILABLE_EMBEDDING_MODELS[k],
        index=emb_keys.index(current_emb),
    )
    if selected_emb != settings.get("embedding_model"):
        settings["embedding_model"] = selected_emb
        if state.get("vector_store") is not None:
            state["vector_store"] = None
            state["rag_chain"] = None
            st.warning("⚠️ Embedding model changed — rebuild the KB.")
    settings["embedding_model"] = selected_emb


def _render_upload(state: dict) -> None:
    uploaded_files = st.file_uploader(
        f"PDF, DOCX, TXT, MD",
        type=[e.lstrip(".") for e in SUPPORTED_EXTENSIONS],
        accept_multiple_files=True,
        key="file_uploader",
    )
    if uploaded_files:
        st.info(f"{len(uploaded_files)} file(s) selected")
        for uf in uploaded_files:
            st.caption(f"📄 {uf.name} · {human_readable_size(uf.size)}")
        if st.button("📥 Load Files", type="primary", use_container_width=True):
            _load_uploaded_files(uploaded_files, state)


def _load_uploaded_files(uploaded_files, state: dict) -> None:
    pending = state.setdefault("pending_docs", [])
    loaded_names = state.setdefault("loaded_file_names", set())
    errors = []
    progress = st.progress(0, text="Loading…")

    for i, uf in enumerate(uploaded_files):
        if uf.name in loaded_names:
            continue
        try:
            docs = load_from_uploaded_file(uf, uf.name)
            pending.extend(docs)
            loaded_names.add(uf.name)
        except Exception as exc:
            errors.append(f"{uf.name}: {exc}")
            logger.error(f"Failed to load {uf.name}: {exc}")
        progress.progress((i + 1) / len(uploaded_files), text=f"Loading {uf.name}…")

    progress.empty()
    if errors:
        st.error("\n".join(errors))
    else:
        st.success(f"✅ {len(loaded_names)} file(s) ready to index")
    state["documents_loaded"] = bool(pending)


def _render_kb_controls(state: dict) -> None:
    has_pending = bool(state.get("pending_docs"))
    has_store = state.get("vector_store") is not None

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⚡ Build KB", disabled=not has_pending,
                     type="primary" if has_pending else "secondary",
                     use_container_width=True):
            state["action"] = "build_kb"
    with col2:
        if st.button("🗑️ Reset KB", disabled=not has_store, use_container_width=True):
            state["action"] = "reset_kb"

    if has_pending:
        st.caption(f"⏳ {len(state['pending_docs'])} page(s) queued")


def _render_indexed_docs(state: dict) -> None:
    indexed = state.get("indexed_files", [])
    if not indexed:
        return
    st.markdown("**Indexed documents:**")
    for name in indexed:
        ext = name.rsplit(".", 1)[-1].upper() if "." in name else "?"
        st.markdown(
            f'<div class="indexed-doc"><span class="doc-icon">📄</span>{name} &nbsp;<span style="color:#334155;font-size:0.65rem;">[{ext}]</span></div>',
            unsafe_allow_html=True,
        )


def _render_stats(state: dict) -> None:
    store = state.get("vector_store")
    stats = state.get("kb_stats", {})
    history = state.get("chat_history_obj")

    c1, c2 = st.columns(2)
    c1.metric("Vectors", stats.get("total_vectors", 0) if store else 0)
    c2.metric("Documents", len(state.get("indexed_files", [])))

    c3, c4 = st.columns(2)
    c3.metric("Chat Turns", len(history) if history else 0)
    c4.metric("Last Latency", f"{state.get('last_latency', 0.0):.1f}s")


def _render_settings(state: dict) -> None:
    settings = state.setdefault("settings", {})

    settings["top_k"] = st.slider(
        "Retrieved chunks (top-k)", 1, 10,
        value=settings.get("top_k", config.retrieval["top_k"]),
    )
    settings["temperature"] = st.slider(
        "Temperature", 0.0, 1.0,
        value=float(settings.get("temperature", config.llm["temperature"])),
        step=0.05,
    )
    settings["show_context"] = st.toggle(
        "Show retrieved context",
        value=settings.get("show_context", True),
    )
    settings["show_sources"] = st.toggle(
        "Show source documents",
        value=settings.get("show_sources", True),
    )

    # Export chat
    history = state.get("chat_history_obj")
    if history and len(history) > 0:
        from ui.chat import build_chat_export
        export_md = build_chat_export(history)
        st.download_button(
            "⬇️ Export Chat",
            data=export_md,
            file_name="chat_export.md",
            mime="text/markdown",
            use_container_width=True,
        )
