from typing import Any, Protocol


class ChatProvider(Protocol):
    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> Any:
        """Return one model response that may contain tool calls."""
