import json
from pathlib import Path
from typing import Any

from ..tools.edits import propose_edit
from ..tools.files import list_files, read_file
from ..tools.search import search_text
from ..tools.tests import run_tests
from .prompts import SYSTEM_PROMPT

TOOL_DEFINITIONS = [
    {"type": "function", "function": {"name": "list_files", "description": "List files in the selected project.", "parameters": {"type": "object", "properties": {"limit": {"type": "integer"}}, "required": []}}},
    {"type": "function", "function": {"name": "read_file", "description": "Read one UTF-8 text file inside the selected project.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "search_text", "description": "Search project files for a literal string.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "propose_edit", "description": "Propose the complete contents of one file. A diff is shown and user approval is required before writing.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}, "reason": {"type": "string"}}, "required": ["path", "content", "reason"]}}},
    {"type": "function", "function": {"name": "run_tests", "description": "Offer to run the fixed Python unittest discovery command. User approval is required.", "parameters": {"type": "object", "properties": {}, "required": []}}},
]


def _run_tool(root: Path, name: str, args: dict[str, Any]) -> str:
    try:
        if name == "list_files":
            return json.dumps(list_files(root, int(args.get("limit", 120))))
        if name == "read_file":
            return read_file(root, args["path"])
        if name == "search_text":
            return search_text(root, args["query"])
        if name == "propose_edit":
            return propose_edit(root, args["path"], args["content"], args["reason"])
        if name == "run_tests":
            return run_tests(root)
        return "Error: unknown tool"
    except Exception as exc:
        return f"Tool error: {type(exc).__name__}: {exc}"


class Agent:
    def __init__(self, provider, root: Path):
        self.provider = provider
        self.root = root.resolve()
        files = list_files(self.root)
        self.messages: list[dict[str, Any]] = [{
            "role": "system",
            "content": f"{SYSTEM_PROMPT}\n\nSelected project: {self.root.name}\nInitial file list:\n" + "\n".join(files),
        }]

    def ask(self, prompt: str) -> str:
        self.messages.append({"role": "user", "content": prompt})
        for _ in range(8):
            try:
                message = self.provider.complete(self.messages, TOOL_DEFINITIONS)
            except Exception as exc:
                self.messages.pop()
                return f"Provider request failed: {exc}"
            self.messages.append(message.model_dump(exclude_none=True))
            calls = message.tool_calls or []
            if not calls:
                return message.content or "(The model returned an empty response.)"
            for call in calls:
                try:
                    args = json.loads(call.function.arguments or "{}")
                    result = _run_tool(self.root, call.function.name, args)
                except (json.JSONDecodeError, KeyError) as exc:
                    result = f"Invalid tool arguments: {exc}"
                self.messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
        return "Stopped after the eight-step tool-call limit. Ask a follow-up to continue."

    def reset(self) -> None:
        self.messages = self.messages[:1]
