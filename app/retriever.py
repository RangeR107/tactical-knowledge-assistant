"""Retrieval logic wrapping the FAISS vector store."""

from typing import Any

from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever

from app.config import config
from app.logger import logger


def get_retriever(store: Any, top_k: int | None = None) -> VectorStoreRetriever:
    """Create a LangChain retriever from any supported vector store.

    Args:
        store: Vector store instance (FAISS, Chroma, or Qdrant).
        top_k: Number of chunks to retrieve. Defaults to config value.

    Returns:
        A LangChain VectorStoreRetriever.
    """
    k = top_k or config.retrieval.get("top_k", 5)
    retriever = store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k},
    )
    logger.debug(f"Retriever configured: top_k={k}")
    return retriever


def retrieve_relevant_docs(store: Any, query: str) -> list[Document]:
    """Directly retrieve the most relevant document chunks for a query.

    Args:
        store: FAISS vector store instance.
        query: User query string.

    Returns:
        List of relevant Document objects.
    """
    ret_cfg = config.retrieval
    top_k = ret_cfg.get("top_k", 5)

    docs = store.similarity_search(query, k=top_k)
    logger.info(f"Retrieved {len(docs)} chunks for query: '{query[:60]}…'")
    return docs
