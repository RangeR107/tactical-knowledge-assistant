"""FAISS vector store management with persistence between sessions."""

from pathlib import Path
from typing import Optional

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from app.config import config
from app.embeddings import get_embedding_model
from app.logger import logger


def _store_path() -> Path:
    return Path(config.vector_store["path"])


def _index_name() -> str:
    return config.vector_store["index_name"]


def store_exists() -> bool:
    """Return True if a persisted FAISS index exists on disk."""
    p = _store_path() / _index_name()
    return (p.with_suffix(".faiss")).exists() or (
        (_store_path() / "index.faiss").exists()
    )


def load_vector_store() -> Optional[FAISS]:
    """Load the persisted FAISS index from disk.

    Returns:
        FAISS instance or None if no persisted index found.
    """
    if not store_exists():
        logger.info("No persisted vector store found.")
        return None

    embeddings = get_embedding_model()
    store = FAISS.load_local(
        folder_path=str(_store_path()),
        embeddings=embeddings,
        index_name=_index_name(),
        allow_dangerous_deserialization=True,
    )
    logger.info(f"Loaded vector store from '{_store_path()}'")
    return store


def build_vector_store(chunks: list[Document]) -> FAISS:
    """Build a new FAISS index from document chunks and persist it.

    Args:
        chunks: List of chunked LangChain Document objects.

    Returns:
        The newly built FAISS vector store.
    """
    if not chunks:
        raise ValueError("Cannot build vector store: no document chunks provided.")

    embeddings = get_embedding_model()
    logger.info(f"Building FAISS index from {len(chunks)} chunks…")

    store = FAISS.from_documents(chunks, embeddings)

    _store_path().mkdir(parents=True, exist_ok=True)
    store.save_local(folder_path=str(_store_path()), index_name=_index_name())
    logger.info(f"Vector store saved to '{_store_path()}'")
    return store


def add_documents_to_store(
    existing_store: Optional[FAISS], new_chunks: list[Document]
) -> FAISS:
    """Add new chunks to an existing store or create a fresh one.

    Args:
        existing_store: An existing FAISS store, or None to create a new one.
        new_chunks: New document chunks to add.

    Returns:
        Updated FAISS vector store.
    """
    if existing_store is None:
        return build_vector_store(new_chunks)

    embeddings = get_embedding_model()
    logger.info(f"Adding {len(new_chunks)} new chunks to existing vector store…")

    new_store = FAISS.from_documents(new_chunks, embeddings)
    existing_store.merge_from(new_store)

    _store_path().mkdir(parents=True, exist_ok=True)
    existing_store.save_local(folder_path=str(_store_path()), index_name=_index_name())
    logger.info("Updated vector store saved.")
    return existing_store


def delete_vector_store() -> None:
    """Remove all persisted vector store files from disk."""
    p = _store_path()
    for f in p.glob("*"):
        if f.is_file():
            f.unlink()
    logger.info("Vector store deleted.")


def get_store_stats(store: FAISS) -> dict:
    """Return basic statistics about the vector store."""
    try:
        doc_count = store.index.ntotal
    except Exception:
        doc_count = 0
    return {"total_vectors": doc_count}
