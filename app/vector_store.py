"""Multi-backend vector store management: FAISS, ChromaDB, and Qdrant."""

from pathlib import Path
from typing import Any, Callable, Optional

from langchain_core.documents import Document

from app.config import config
from app.embeddings import get_embedding_model
from app.logger import logger


# All supported vector store backends shown in the UI
AVAILABLE_STORES: dict[str, str] = {
    "faiss":  "FAISS  — local file, no server needed",
    "chroma": "ChromaDB — local file, no server needed",
    "qdrant": "Qdrant — local file, no server needed",
}

DEFAULT_STORE_TYPE = "faiss"
_COLLECTION_NAME = config.vector_store.get("index_name", "tactical_kb")


def _base_path() -> Path:
    return Path(config.vector_store["path"])


def _store_dir(store_type: str) -> Path:
    """Each backend gets its own subdirectory."""
    return _base_path() / store_type


# ── Existence checks ─────────────────────────────────────────────────────────

def store_exists(store_type: str = DEFAULT_STORE_TYPE) -> bool:
    d = _store_dir(store_type)
    if store_type == "faiss":
        return (d / f"{_COLLECTION_NAME}.faiss").exists()
    elif store_type == "chroma":
        return (d / "chroma.sqlite3").exists()
    elif store_type == "qdrant":
        return (d / "meta.json").exists()
    return False


def any_store_exists() -> bool:
    """True if at least one backend has a persisted index."""
    return any(store_exists(t) for t in AVAILABLE_STORES)


# ── Build ─────────────────────────────────────────────────────────────────────

def build_vector_store(
    chunks: list[Document],
    store_type: str = DEFAULT_STORE_TYPE,
    embedding_model: str | None = None,
    progress_callback: Callable[[float, str], None] | None = None,
) -> Any:
    """Embed chunks in batches (with progress) and persist the vector store.

    Args:
        chunks: Chunked LangChain documents.
        store_type: One of "faiss", "chroma", "qdrant".
        embedding_model: HuggingFace model name. Defaults to config value.
        progress_callback: Called as (fraction 0–1, message) during embedding.

    Returns:
        The built vector store instance.
    """
    if not chunks:
        raise ValueError("No chunks provided.")

    emb = get_embedding_model(embedding_model)
    d = _store_dir(store_type)
    d.mkdir(parents=True, exist_ok=True)

    # ── Batched embedding with progress ──────────────────────────────────────
    batch_size = 32
    texts = [c.page_content for c in chunks]
    metadatas = [c.metadata for c in chunks]
    all_embeddings: list[list[float]] = []

    logger.info(f"Embedding {len(chunks)} chunks with '{embedding_model}' → {store_type}")
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        all_embeddings.extend(emb.embed_documents(batch))
        done = min(i + batch_size, len(texts))
        if progress_callback:
            # Reserve 0.0–0.7 for embedding, 0.7–1.0 for indexing
            progress_callback(0.05 + 0.65 * done / len(texts), f"Embedding {done}/{len(texts)} chunks…")

    if progress_callback:
        progress_callback(0.72, "Building index…")

    store = _build_from_embeddings(
        store_type, texts, all_embeddings, metadatas, emb, d
    )

    if progress_callback:
        progress_callback(0.95, "Saving to disk…")

    logger.info(f"Vector store ({store_type}) saved to '{d}'")
    return store


def _build_from_embeddings(store_type, texts, embeddings_list, metadatas, emb, d):
    """Build a store from pre-computed embeddings."""
    if store_type == "faiss":
        from langchain_community.vectorstores import FAISS
        pairs = list(zip(texts, embeddings_list))
        store = FAISS.from_embeddings(pairs, emb, metadatas=metadatas)
        store.save_local(folder_path=str(d), index_name=_COLLECTION_NAME)
        return store

    elif store_type == "chroma":
        from langchain_chroma import Chroma
        # Chroma doesn't support from_embeddings cleanly; rebuild from docs
        # Wrap pre-computed embeddings via a custom embedding fn
        store = Chroma(
            collection_name=_COLLECTION_NAME,
            embedding_function=emb,
            persist_directory=str(d),
        )
        # Add in batches using pre-computed embeddings
        batch_size = 100
        for i in range(0, len(texts), batch_size):
            store._collection.add(
                ids=[f"doc_{i+j}" for j in range(len(texts[i:i+batch_size]))],
                documents=texts[i:i+batch_size],
                embeddings=embeddings_list[i:i+batch_size],
                metadatas=metadatas[i:i+batch_size],
            )
        return store

    elif store_type == "qdrant":
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams
        from langchain_qdrant import QdrantVectorStore

        dim = len(embeddings_list[0])
        client = QdrantClient(path=str(d))

        # Recreate collection
        existing = [c.name for c in client.get_collections().collections]
        if _COLLECTION_NAME in existing:
            client.delete_collection(_COLLECTION_NAME)

        client.create_collection(
            collection_name=_COLLECTION_NAME,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )

        store = QdrantVectorStore(
            client=client,
            collection_name=_COLLECTION_NAME,
            embedding=emb,
        )
        # Add in batches
        from langchain_core.documents import Document as LCDoc
        batch_size = 100
        for i in range(0, len(texts), batch_size):
            docs = [
                LCDoc(page_content=texts[i+j], metadata=metadatas[i+j])
                for j in range(len(texts[i:i+batch_size]))
            ]
            store.add_documents(docs)
        return store

    raise ValueError(f"Unknown store_type: {store_type}")


# ── Load ─────────────────────────────────────────────────────────────────────

def load_vector_store(
    store_type: str = DEFAULT_STORE_TYPE,
    embedding_model: str | None = None,
) -> Optional[Any]:
    """Load a persisted vector store from disk.

    Returns None if no persisted store exists.
    """
    if not store_exists(store_type):
        return None

    emb = get_embedding_model(embedding_model)
    d = _store_dir(store_type)

    if store_type == "faiss":
        from langchain_community.vectorstores import FAISS
        store = FAISS.load_local(
            folder_path=str(d),
            embeddings=emb,
            index_name=_COLLECTION_NAME,
            allow_dangerous_deserialization=True,
        )

    elif store_type == "chroma":
        from langchain_chroma import Chroma
        store = Chroma(
            collection_name=_COLLECTION_NAME,
            embedding_function=emb,
            persist_directory=str(d),
        )

    elif store_type == "qdrant":
        from qdrant_client import QdrantClient
        from langchain_qdrant import QdrantVectorStore
        client = QdrantClient(path=str(d))
        store = QdrantVectorStore(
            client=client,
            collection_name=_COLLECTION_NAME,
            embedding=emb,
        )
    else:
        raise ValueError(f"Unknown store_type: {store_type}")

    logger.info(f"Loaded {store_type} vector store from '{d}'")
    return store


# ── Delete ────────────────────────────────────────────────────────────────────

def delete_vector_store(store_type: str = DEFAULT_STORE_TYPE) -> None:
    """Delete all files for the given backend."""
    import shutil
    d = _store_dir(store_type)
    if d.exists():
        shutil.rmtree(d)
    logger.info(f"Vector store ({store_type}) deleted.")


def delete_all_stores() -> None:
    """Delete all persisted stores across all backends."""
    for t in AVAILABLE_STORES:
        delete_vector_store(t)


# ── Stats ─────────────────────────────────────────────────────────────────────

def get_store_stats(store: Any, store_type: str = DEFAULT_STORE_TYPE) -> dict:
    """Return basic statistics about the vector store."""
    try:
        if store_type == "faiss":
            return {"total_vectors": store.index.ntotal}
        elif store_type == "chroma":
            return {"total_vectors": store._collection.count()}
        elif store_type == "qdrant":
            info = store.client.get_collection(_COLLECTION_NAME)
            count = getattr(info, "points_count", None) or getattr(info, "vectors_count", None) or 0
            return {"total_vectors": count}
    except Exception:
        pass
    return {"total_vectors": 0}
