"""Sidebar UI components for document management and settings."""

from pathlib import Path

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
            <div style="text-align:center; padding: 0.5rem 0 1rem 0;">
                <span style="font-size:2rem;">🎯</span>
                <div style="color:#38bdf8; font-weight:700; font-size:1rem; letter-spacing:0.05em;">
                    TACTICAL KA
                </div>
                <div style="color:#475569; font-size:0.7rem;">v1.0.0 • Fully Offline</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        # ── System Status ──────────────────────────────────────────────────
        st.markdown("### 🔌 System Status")
        _render_status(state)

        st.divider()

        # ── Model Selection ────────────────────────────────────────────────
        st.markdown("### 🤖 Model Selection")
        _render_model_selector(state)

        st.divider()

        # ── Vector DB & Embedding ──────────────────────────────────────────
        st.markdown("### 🗃️ Vector DB & Embeddings")
        _render_vectordb_selector(state)

        st.divider()

        # ── Document Upload ────────────────────────────────────────────────
        st.markdown("### 📁 Upload Documents")
        _render_upload(state)

        st.divider()

        # ── Knowledge Base Controls ────────────────────────────────────────
        st.markdown("### 🗄️ Knowledge Base")
        _render_kb_controls(state)

        st.divider()

        # ── Statistics ────────────────────────────────────────────────────
        st.markdown("### 📊 Statistics")
        _render_stats(state)

        st.divider()

        # ── Settings ──────────────────────────────────────────────────────
        st.markdown("### ⚙️ Settings")
        _render_settings(state)

        st.divider()

        # ── Logs ──────────────────────────────────────────────────────────
        with st.expander("📋 Application Logs", expanded=False):
            log_text = read_log_tail(config.logging_cfg["file"], n_lines=50)
            st.markdown(
                f'<div class="log-viewer">{log_text}</div>',
                unsafe_allow_html=True,
            )
            if st.button("🔄 Refresh Logs", use_container_width=True):
                st.rerun()


# ── Private helpers ──────────────────────────────────────────────────────────

def _render_status(state: dict) -> None:
    from app.llm import is_ollama_running, is_model_available

    ollama_ok = is_ollama_running()
    model_name = state.get("settings", {}).get("model", config.llm["model"])
    model_ok = is_model_available(model_name) if ollama_ok else False
    kb_ready = state.get("vector_store") is not None

    def badge(label: str, ok: bool, warn: bool = False) -> str:
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
        st.warning("Ollama server not running. Start it with: `ollama serve`")
    elif not model_ok:
        st.warning(f"Model `{model_name}` not found. Run: `ollama pull {model_name}`")


def _render_model_selector(state: dict) -> None:
    settings = state.setdefault("settings", {})
    available = get_available_models()

    if not available:
        st.warning("No Ollama models found. Pull one first.")
        st.caption("e.g. `ollama pull qwen2.5:3b`")
        return

    current = settings.get("model", config.llm["model"])
    # Default to first available if current not found
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
        # Invalidate the chain so it's rebuilt with the new model
        state["rag_chain"] = None
        st.caption(f"✅ Model changed to `{selected}` — will apply on next query.")
    else:
        settings["model"] = selected

    st.caption(f"Selected: `{selected}`")


def _render_vectordb_selector(state: dict) -> None:
    settings = state.setdefault("settings", {})

    # ── Vector DB ──────────────────────────────────────────────────────────
    store_keys = list(AVAILABLE_STORES.keys())
    store_labels = list(AVAILABLE_STORES.values())
    current_store = settings.get("vector_db", DEFAULT_STORE_TYPE)
    if current_store not in store_keys:
        current_store = DEFAULT_STORE_TYPE

    selected_store = st.selectbox(
        "Vector Database",
        options=store_keys,
        format_func=lambda k: AVAILABLE_STORES[k],
        index=store_keys.index(current_store),
        help="Choose where to store document embeddings",
    )

    if selected_store != settings.get("vector_db"):
        settings["vector_db"] = selected_store
        # KB was built with a different backend — must rebuild
        if state.get("vector_store") is not None:
            state["vector_store"] = None
            state["rag_chain"] = None
            st.warning("⚠️ Vector DB changed — please rebuild the Knowledge Base.")

    settings["vector_db"] = selected_store

    # ── Embedding Model ────────────────────────────────────────────────────
    emb_keys = list(AVAILABLE_EMBEDDING_MODELS.keys())
    current_emb = settings.get("embedding_model", DEFAULT_EMBEDDING_MODEL)
    if current_emb not in emb_keys:
        current_emb = DEFAULT_EMBEDDING_MODEL

    selected_emb = st.selectbox(
        "Embedding Model",
        options=emb_keys,
        format_func=lambda k: AVAILABLE_EMBEDDING_MODELS[k],
        index=emb_keys.index(current_emb),
        help="Model used to convert text to vectors",
    )

    if selected_emb != settings.get("embedding_model"):
        settings["embedding_model"] = selected_emb
        if state.get("vector_store") is not None:
            state["vector_store"] = None
            state["rag_chain"] = None
            st.warning("⚠️ Embedding model changed — please rebuild the Knowledge Base.")

    settings["embedding_model"] = selected_emb


def _render_upload(state: dict) -> None:
    ext_list = ", ".join(sorted(SUPPORTED_EXTENSIONS))
    uploaded_files = st.file_uploader(
        f"Supported: {ext_list}",
        type=[e.lstrip(".") for e in SUPPORTED_EXTENSIONS],
        accept_multiple_files=True,
        key="file_uploader",
    )

    if uploaded_files:
        st.info(f"{len(uploaded_files)} file(s) selected")
        for uf in uploaded_files:
            size_str = human_readable_size(uf.size)
            st.markdown(
                f"<small>📄 **{uf.name}** &nbsp;·&nbsp; {size_str}</small>",
                unsafe_allow_html=True,
            )
        if st.button("📥 Load Selected Files", type="primary", use_container_width=True):
            _load_uploaded_files(uploaded_files, state)


def _load_uploaded_files(uploaded_files: list, state: dict) -> None:
    pending = state.setdefault("pending_docs", [])
    loaded_names = state.setdefault("loaded_file_names", set())
    errors = []

    progress = st.progress(0, text="Loading documents…")
    total = len(uploaded_files)

    for i, uf in enumerate(uploaded_files):
        if uf.name in loaded_names:
            st.warning(f"Skipping duplicate: {uf.name}")
            continue
        try:
            docs = load_from_uploaded_file(uf, uf.name)
            pending.extend(docs)
            loaded_names.add(uf.name)
        except Exception as exc:
            errors.append(f"{uf.name}: {exc}")
            logger.error(f"Failed to load {uf.name}: {exc}")
        progress.progress((i + 1) / total, text=f"Loading {uf.name}…")

    progress.empty()
    if errors:
        st.error("Failed to load:\n" + "\n".join(errors))
    else:
        st.success(f"✅ {len(loaded_names)} file(s) loaded — {len(pending)} page(s) ready")

    state["documents_loaded"] = bool(pending)


def _render_kb_controls(state: dict) -> None:
    has_pending = bool(state.get("pending_docs"))
    has_store = state.get("vector_store") is not None

    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            "⚡ Build KB",
            disabled=not has_pending,
            type="primary" if has_pending else "secondary",
            use_container_width=True,
        ):
            state["action"] = "build_kb"
    with col2:
        if st.button(
            "🗑️ Reset KB",
            disabled=not has_store,
            use_container_width=True,
        ):
            state["action"] = "reset_kb"

    if has_pending:
        st.caption(f"⏳ {len(state['pending_docs'])} page(s) awaiting indexing")

    # Show current KB backend
    if has_store:
        vdb = state.get("settings", {}).get("vector_db", DEFAULT_STORE_TYPE)
        emb = state.get("settings", {}).get("embedding_model", DEFAULT_EMBEDDING_MODEL)
        st.caption(f"KB: **{vdb.upper()}** · `{emb.split('/')[-1]}`")


def _render_stats(state: dict) -> None:
    store = state.get("vector_store")
    stats = state.get("kb_stats", {})
    history = state.get("chat_history_obj")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Vectors", stats.get("total_vectors", 0) if store else 0)
    with col2:
        st.metric("Documents", len(state.get("loaded_file_names", set())))

    col3, col4 = st.columns(2)
    with col3:
        st.metric("Chat Turns", len(history) if history else 0)
    with col4:
        st.metric("Last Latency", f"{state.get('last_latency', 0.0):.1f}s")


def _render_settings(state: dict) -> None:
    settings = state.setdefault("settings", {})

    settings["top_k"] = st.slider(
        "Retrieved chunks (top-k)",
        min_value=1, max_value=10,
        value=settings.get("top_k", config.retrieval["top_k"]),
    )

    settings["temperature"] = st.slider(
        "Temperature",
        min_value=0.0, max_value=1.0,
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
