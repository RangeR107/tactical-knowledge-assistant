"""Retrieval logic wrapping the FAISS vector store."""

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever

from app.config import config
from app.logger import logger


def get_retriever(store: FAISS) -> VectorStoreRetriever:
    """Create a LangChain retriever from a FAISS vector store.

    Args:
        store: FAISS vector store instance.

    Returns:
        A LangChain VectorStoreRetriever configured from config.yaml.
    """
    ret_cfg = config.retrieval
    top_k = ret_cfg.get("top_k", 5)

    # Use plain similarity search — score_threshold is omitted because FAISS
    # returns L2 distances that are not comparable to a cosine-similarity threshold.
    retriever = store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": top_k},
    )
    logger.debug(f"Retriever configured: top_k={top_k}, search_type=similarity")
    return retriever


def retrieve_relevant_docs(store: FAISS, query: str) -> list[Document]:
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
