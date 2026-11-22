from typing import Any

from openai import OpenAI

from ..config import Settings


class OpenAICompatibleProvider:
    """Adapter for endpoints that implement OpenAI Chat Completions tool calls."""

    def __init__(self, settings: Settings):
        self.client = OpenAI(
            api_key=settings.api_key,
            base_url=settings.base_url,
            timeout=90.0,
            max_retries=1,
        )
        self.model = settings.model

    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> Any:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        return response.choices[0].message
