"""Local embedding models using SentenceTransformers via LangChain."""

from langchain_huggingface import HuggingFaceEmbeddings

from app.config import config
from app.logger import logger


# All available embedding models shown in the UI
AVAILABLE_EMBEDDING_MODELS: dict[str, str] = {
    "all-MiniLM-L6-v2":        "all-MiniLM-L6-v2  — fast & lightweight (384 dim)",
    "BAAI/bge-small-en-v1.5":  "BGE-small-en-v1.5 — balanced speed/quality (384 dim)",
    "BAAI/bge-base-en-v1.5":   "BGE-base-en-v1.5  — high quality (768 dim)",
    "all-mpnet-base-v2":       "all-mpnet-base-v2 — strong semantic search (768 dim)",
}

DEFAULT_EMBEDDING_MODEL = config.embeddings.get("model", "all-MiniLM-L6-v2")

# Module-level cache keyed by model name
_model_cache: dict[str, HuggingFaceEmbeddings] = {}


def get_embedding_model(model_name: str | None = None) -> HuggingFaceEmbeddings:
    """Return a cached HuggingFaceEmbeddings instance for the given model.

    Args:
        model_name: HuggingFace model name/path. Defaults to config value.
    """
    if model_name is None:
        model_name = DEFAULT_EMBEDDING_MODEL

    if model_name not in _model_cache:
        device = config.embeddings.get("device", "cpu")
        logger.info(f"Loading embedding model '{model_name}' on device '{device}'")

        _model_cache[model_name] = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": device},
            encode_kwargs={"normalize_embeddings": True},
        )
        logger.info(f"Embedding model '{model_name}' loaded successfully")

    return _model_cache[model_name]
