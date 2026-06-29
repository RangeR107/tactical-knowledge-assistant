"""Local LLM interface using Ollama via LangChain."""

from functools import lru_cache

import requests
from langchain_ollama import OllamaLLM

from app.config import config
from app.logger import logger


def is_ollama_running() -> bool:
    """Check if the Ollama server is reachable."""
    try:
        resp = requests.get(
            config.llm["base_url"] + "/api/tags", timeout=3
        )
        return resp.status_code == 200
    except Exception:
        return False


def is_model_available(model_name: str | None = None) -> bool:
    """Check if the configured Ollama model is downloaded and available."""
    model = model_name or config.llm["model"]
    try:
        resp = requests.get(config.llm["base_url"] + "/api/tags", timeout=5)
        if resp.status_code != 200:
            return False
        models = [m["name"] for m in resp.json().get("models", [])]
        # Accept both "qwen2.5:3b" and "qwen2.5:3b-instruct" etc.
        return any(model.split(":")[0] in m for m in models)
    except Exception:
        return False


@lru_cache(maxsize=1)
def get_llm() -> OllamaLLM:
    """Return a cached OllamaLLM instance configured from config.yaml."""
    llm_cfg = config.llm
    model = llm_cfg["model"]

    logger.info(f"Initialising Ollama LLM: model='{model}'")

    llm = OllamaLLM(
        model=model,
        base_url=llm_cfg["base_url"],
        temperature=llm_cfg.get("temperature", 0.1),
        top_p=llm_cfg.get("top_p", 0.9),
        top_k=llm_cfg.get("top_k", 40),
        num_predict=llm_cfg.get("num_predict", 512),
        timeout=llm_cfg.get("timeout", 120),
    )

    logger.info(f"Ollama LLM '{model}' ready")
    return llm
