"""Centralised logging setup for the Tactical Knowledge Assistant."""

import logging
import logging.handlers
from pathlib import Path

from app.config import config


def _get_log_level(level_str: str) -> int:
    return getattr(logging, level_str.upper(), logging.INFO)


def setup_logger(name: str = "tactical_ka") -> logging.Logger:
    """Create and configure the application logger."""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # already configured

    log_cfg = config.logging_cfg
    level = _get_log_level(log_cfg.get("level", "INFO"))
    logger.setLevel(level)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # Rotating file handler
    log_path = Path(log_cfg["file"])
    log_path.parent.mkdir(parents=True, exist_ok=True)
    fh = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=log_cfg.get("max_bytes", 10_485_760),
        backupCount=log_cfg.get("backup_count", 3),
    )
    fh.setLevel(level)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    logger.propagate = False
    return logger


logger = setup_logger()
