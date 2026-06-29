"""Utility functions for the Tactical Knowledge Assistant."""

import hashlib
from pathlib import Path


def file_hash(file_bytes: bytes) -> str:
    """Compute a SHA-256 hex digest for a byte string (used to detect duplicate uploads)."""
    return hashlib.sha256(file_bytes).hexdigest()


def human_readable_size(num_bytes: int) -> str:
    """Convert a byte count to a human-readable string."""
    for unit in ("B", "KB", "MB", "GB"):
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024  # type: ignore[assignment]
    return f"{num_bytes:.1f} TB"


def truncate(text: str, max_chars: int = 300) -> str:
    """Truncate a string and append ellipsis if it exceeds max_chars."""
    return text[:max_chars] + "…" if len(text) > max_chars else text


def unique_sources(docs: list) -> list[str]:
    """Return deduplicated source names from a list of LangChain Documents."""
    seen: set[str] = set()
    sources: list[str] = []
    for doc in docs:
        src = doc.metadata.get("source", "Unknown")
        if src not in seen:
            seen.add(src)
            sources.append(src)
    return sources


def safe_filename(name: str) -> str:
    """Sanitise a filename by replacing unsafe characters."""
    return "".join(c if c.isalnum() or c in "._- " else "_" for c in name)


def read_log_tail(log_path: str | Path, n_lines: int = 100) -> str:
    """Read the last n lines from the application log file."""
    path = Path(log_path)
    if not path.exists():
        return "No log file found."
    with open(path, "r", errors="replace") as f:
        lines = f.readlines()
    return "".join(lines[-n_lines:])
