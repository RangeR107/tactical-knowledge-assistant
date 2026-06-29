"""Document loading for PDF, DOCX, TXT, and Markdown files using LangChain loaders."""

from pathlib import Path
from typing import IO

from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
)
from langchain_core.documents import Document

from app.logger import logger


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".markdown"}


def load_document(file_path: str | Path) -> list[Document]:
    """Load a single document from disk and return LangChain Document objects.

    Args:
        file_path: Path to the document file.

    Returns:
        List of LangChain Document objects with page_content and metadata.

    Raises:
        ValueError: If the file extension is not supported.
        FileNotFoundError: If the file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{suffix}'. Supported: {SUPPORTED_EXTENSIONS}"
        )

    logger.info(f"Loading document: {path.name} ({suffix})")

    if suffix == ".pdf":
        loader = PyPDFLoader(str(path))
    elif suffix == ".docx":
        loader = Docx2txtLoader(str(path))
    elif suffix in {".txt", ".md", ".markdown"}:
        # TextLoader handles plain text and Markdown equally well; no extra package needed
        loader = TextLoader(str(path), encoding="utf-8", autodetect_encoding=True)
    else:
        raise ValueError(f"Unhandled extension: {suffix}")

    docs = loader.load()

    # Ensure source metadata is set to the filename (not full path)
    for doc in docs:
        doc.metadata["source"] = path.name
        doc.metadata["file_path"] = str(path)

    logger.info(f"Loaded {len(docs)} page(s) from '{path.name}'")
    return docs


def load_from_uploaded_file(uploaded_file: IO[bytes], filename: str) -> list[Document]:
    """Save a Streamlit UploadedFile to a temp location and load it.

    Args:
        uploaded_file: Streamlit UploadedFile object (file-like).
        filename: Original filename including extension.

    Returns:
        List of LangChain Document objects.
    """
    import tempfile

    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {suffix}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    try:
        docs = load_document(tmp_path)
        # Override source with original filename
        for doc in docs:
            doc.metadata["source"] = filename
            doc.metadata["file_path"] = filename
        return docs
    finally:
        Path(tmp_path).unlink(missing_ok=True)
