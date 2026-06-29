"""Configuration management for the Tactical Knowledge Assistant."""

import os
from pathlib import Path
from typing import Any

import yaml


BASE_DIR = Path(__file__).parent.parent
CONFIG_PATH = BASE_DIR / "config.yaml"


class AppConfig:
    """Loads and exposes application configuration from config.yaml."""

    def __init__(self, config_path: Path = CONFIG_PATH) -> None:
        with open(config_path, "r") as f:
            self._cfg: dict[str, Any] = yaml.safe_load(f)

        # Resolve relative paths to absolute paths based on BASE_DIR
        vs_path = self._cfg["vector_store"]["path"]
        if not os.path.isabs(vs_path):
            self._cfg["vector_store"]["path"] = str(BASE_DIR / vs_path)

        log_file = self._cfg["logging"]["file"]
        if not os.path.isabs(log_file):
            self._cfg["logging"]["file"] = str(BASE_DIR / log_file)

    # ── top-level section accessors ─────────────────────────────────────────

    @property
    def app(self) -> dict[str, Any]:
        return self._cfg["app"]

    @property
    def llm(self) -> dict[str, Any]:
        return self._cfg["llm"]

    @property
    def embeddings(self) -> dict[str, Any]:
        return self._cfg["embeddings"]

    @property
    def chunking(self) -> dict[str, Any]:
        return self._cfg["chunking"]

    @property
    def vector_store(self) -> dict[str, Any]:
        return self._cfg["vector_store"]

    @property
    def retrieval(self) -> dict[str, Any]:
        return self._cfg["retrieval"]

    @property
    def chat(self) -> dict[str, Any]:
        return self._cfg["chat"]

    @property
    def logging_cfg(self) -> dict[str, Any]:
        return self._cfg["logging"]

    @property
    def ui(self) -> dict[str, Any]:
        return self._cfg["ui"]

    def get(self, key: str, default: Any = None) -> Any:
        return self._cfg.get(key, default)


# Singleton instance used throughout the application
config = AppConfig()
