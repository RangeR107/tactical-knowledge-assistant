"""In-memory chat history management with a configurable window size."""

from dataclasses import dataclass, field
from typing import Iterator

from app.config import config
from app.logger import logger


@dataclass
class ChatTurn:
    human: str
    assistant: str


class ChatHistory:
    """Stores and manages the rolling conversation history."""

    def __init__(self, max_turns: int | None = None) -> None:
        self._max = max_turns or config.chat.get("max_history", 10)
        self._turns: list[ChatTurn] = []

    def add(self, human: str, assistant: str) -> None:
        self._turns.append(ChatTurn(human=human, assistant=assistant))
        # Keep only the most recent max_turns
        if len(self._turns) > self._max:
            self._turns = self._turns[-self._max :]
        logger.debug(f"Chat history: {len(self._turns)} turn(s) stored")

    def as_list(self) -> list[dict[str, str]]:
        """Return history as a list of {"human": ..., "assistant": ...} dicts."""
        return [{"human": t.human, "assistant": t.assistant} for t in self._turns]

    def clear(self) -> None:
        self._turns.clear()
        logger.info("Chat history cleared")

    def __len__(self) -> int:
        return len(self._turns)

    def __iter__(self) -> Iterator[ChatTurn]:
        return iter(self._turns)
