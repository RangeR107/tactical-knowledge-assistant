"""Local embedding model using SentenceTransformers via LangChain."""

from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings

from app.config import config
from app.logger import logger


@lru_cache(maxsize=1)
def get_embedding_model() -> HuggingFaceEmbeddings:
    """Return a cached HuggingFaceEmbeddings instance (SentenceTransformers under the hood).

    The model is downloaded on first call and cached for the process lifetime.
    """
    emb_cfg = config.embeddings
    model_name = emb_cfg["model"]
    device = emb_cfg.get("device", "cpu")

    logger.info(f"Loading embedding model '{model_name}' on device '{device}'")

    model_kwargs = {"device": device}
    encode_kwargs = {"normalize_embeddings": True}  # cosine similarity

    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs,
    )

    logger.info(f"Embedding model '{model_name}' loaded successfully")
    return embeddings
