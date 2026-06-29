"""Intelligent text chunking using LangChain text splitters."""

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import config
from app.logger import logger


def chunk_documents(documents: list[Document]) -> list[Document]:
    """Split documents into overlapping chunks using LangChain's RecursiveCharacterTextSplitter.

    Args:
        documents: List of LangChain Document objects to chunk.

    Returns:
        List of chunked Document objects with enriched metadata.
    """
    chunk_cfg = config.chunking

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_cfg["chunk_size"],
        chunk_overlap=chunk_cfg["chunk_overlap"],
        separators=chunk_cfg["separators"],
        length_function=len,
        is_separator_regex=False,
    )

    chunks = splitter.split_documents(documents)

    # Enrich metadata with chunk index per source document
    source_counters: dict[str, int] = {}
    for chunk in chunks:
        source = chunk.metadata.get("source", "unknown")
        idx = source_counters.get(source, 0)
        chunk.metadata["chunk_index"] = idx
        source_counters[source] = idx + 1

    logger.info(
        f"Chunked {len(documents)} document(s) into {len(chunks)} chunks "
        f"(size={chunk_cfg['chunk_size']}, overlap={chunk_cfg['chunk_overlap']})"
    )
    return chunks
