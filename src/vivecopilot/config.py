from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    api_key: str
    model: str
    base_url: str | None

    @classmethod
    def from_environment(cls) -> "Settings":
        key = os.getenv("OPENAI_API_KEY", "").strip()
        if not key:
            raise ValueError("Set OPENAI_API_KEY to the key for your approved model provider.")
        return cls(
            api_key=key,
            model=os.getenv("VIVECOPILOT_MODEL", "gpt-4o-mini").strip(),
            base_url=os.getenv("OPENAI_BASE_URL", "").strip() or None,
        )
