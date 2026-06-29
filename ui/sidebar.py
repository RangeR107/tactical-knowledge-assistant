"""Sidebar UI components for document management and settings."""

from pathlib import Path

import streamlit as st

from app.config import config
from app.document_loader import load_from_uploaded_file, SUPPORTED_EXTENSIONS
from app.logger import logger
from app.utils import human_readable_size, read_log_tail


def render_sidebar(state: dict) -> None:
    """Render the full sidebar including upload, stats, model info, and settings.

    Args:
        state: Mutable dict representing Streamlit session_state values.
                Keys modified: documents_loaded, pending_docs, settings.
    """
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
        return (
            f'<span class="status-badge {cls}">{icon} {label}</span>&nbsp;'
        )

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
            logger.info(f"File loaded: {uf.name} → {len(docs)} page(s)")
        except Exception as exc:
            errors.append(f"{uf.name}: {exc}")
            logger.error(f"Failed to load {uf.name}: {exc}")

        progress.progress((i + 1) / total, text=f"Loading {uf.name}…")

    progress.empty()

    if errors:
        st.error("Failed to load:\n" + "\n".join(errors))
    else:
        unique_count = len(loaded_names)
        doc_count = len(pending)
        st.success(f"✅ {unique_count} file(s) loaded — {doc_count} page(s) ready to index")

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
            help="Index all loaded documents into the knowledge base",
        ):
            state["action"] = "build_kb"

    with col2:
        if st.button(
            "🗑️ Reset KB",
            disabled=not has_store,
            use_container_width=True,
            help="Delete the current knowledge base and start fresh",
        ):
            state["action"] = "reset_kb"

    if has_pending:
        count = len(state["pending_docs"])
        st.caption(f"⏳ {count} chunk-ready page(s) awaiting indexing")


def _render_stats(state: dict) -> None:
    store = state.get("vector_store")
    stats = state.get("kb_stats", {})
    history = state.get("chat_history_obj")

    col1, col2 = st.columns(2)
    with col1:
        vectors = stats.get("total_vectors", 0) if store else 0
        st.metric("Vectors", vectors)
    with col2:
        docs = len(state.get("loaded_file_names", set()))
        st.metric("Documents", docs)

    col3, col4 = st.columns(2)
    with col3:
        turns = len(history) if history else 0
        st.metric("Chat Turns", turns)
    with col4:
        latency = state.get("last_latency", 0.0)
        st.metric("Last Latency", f"{latency:.1f}s")


def _render_settings(state: dict) -> None:
    settings = state.setdefault("settings", {
        "model": config.llm["model"],
        "top_k": config.retrieval["top_k"],
        "temperature": config.llm["temperature"],
        "show_context": True,
        "show_sources": True,
    })

    settings["top_k"] = st.slider(
        "Retrieved chunks (top-k)",
        min_value=1, max_value=10,
        value=settings.get("top_k", 5),
        help="Number of document chunks retrieved per query",
    )

    settings["temperature"] = st.slider(
        "Temperature",
        min_value=0.0, max_value=1.0,
        value=float(settings.get("temperature", 0.1)),
        step=0.05,
        help="Higher = more creative, lower = more deterministic",
    )

    settings["show_context"] = st.toggle(
        "Show retrieved context",
        value=settings.get("show_context", True),
    )

    settings["show_sources"] = st.toggle(
        "Show source documents",
        value=settings.get("show_sources", True),
    )

    st.caption(f"Model: `{settings.get('model', config.llm['model'])}`")
