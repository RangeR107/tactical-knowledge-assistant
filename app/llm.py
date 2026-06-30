"""Local LLM interface using Ollama via LangChain."""

import requests
from langchain_ollama import OllamaLLM

from app.config import config
from app.logger import logger


# Module-level cache keyed by model name
_llm_cache: dict[str, OllamaLLM] = {}


def is_ollama_running() -> bool:
    """Check if the Ollama server is reachable."""
    try:
        resp = requests.get(config.llm["base_url"] + "/api/tags", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


def get_available_models() -> list[str]:
    """Return a list of all model names currently available in Ollama."""
    try:
        resp = requests.get(config.llm["base_url"] + "/api/tags", timeout=5)
        if resp.status_code != 200:
            return []
        return [m["name"] for m in resp.json().get("models", [])]
    except Exception:
        return []


def is_model_available(model_name: str | None = None) -> bool:
    """Check whether a specific model is downloaded in Ollama."""
    model = model_name or config.llm["model"]
    available = get_available_models()
    return any(model.split(":")[0] in m for m in available)


def get_llm(model_name: str | None = None, temperature: float | None = None) -> OllamaLLM:
    """Return a cached OllamaLLM for the given model name.

    Args:
        model_name: Ollama model name (e.g. "qwen2.5:3b"). Defaults to config.
        temperature: Override temperature. Defaults to config value.
    """
    llm_cfg = config.llm
    model = model_name or llm_cfg["model"]
    temp = temperature if temperature is not None else llm_cfg.get("temperature", 0.1)

    cache_key = f"{model}::{temp}"
    if cache_key not in _llm_cache:
        logger.info(f"Initialising Ollama LLM: model='{model}', temperature={temp}")
        _llm_cache[cache_key] = OllamaLLM(
            model=model,
            base_url=llm_cfg["base_url"],
            temperature=temp,
            top_p=llm_cfg.get("top_p", 0.9),
            top_k=llm_cfg.get("top_k", 40),
            num_predict=llm_cfg.get("num_predict", 512),
            timeout=llm_cfg.get("timeout", 120),
        )
        logger.info(f"Ollama LLM '{model}' ready")

    return _llm_cache[cache_key]
