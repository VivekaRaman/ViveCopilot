import json
from pathlib import Path
from typing import Any

from ..tools.edits import apply_patch, propose_edit
from ..tools.files import list_files, read_file
from ..tools.git_review import review_changes
from ..tools.search import search_text
from ..tools.tests import run_tests
from .prompts import SYSTEM_PROMPT

TOOL_DEFINITIONS = [
    {"type": "function", "function": {"name": "list_files", "description": "List files in the selected project.", "parameters": {"type": "object", "properties": {"limit": {"type": "integer"}}, "required": []}}},
    {"type": "function", "function": {"name": "read_file", "description": "Read a UTF-8 text file inside the selected project. Use start_line and line_count for a targeted excerpt from a longer file.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "start_line": {"type": "integer"}, "line_count": {"type": "integer"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "search_text", "description": "Search project files for a literal string.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "review_changes", "description": "Inspect staged and unstaged Git diffs for a code review. Secret-looking paths are skipped. This does not run project code.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "apply_patch", "description": "Replace one unique literal section in an existing project file. Shows a focused diff and requires user approval.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "old_text": {"type": "string"}, "new_text": {"type": "string"}, "reason": {"type": "string"}}, "required": ["path", "old_text", "new_text", "reason"]}}},
    {"type": "function", "function": {"name": "propose_edit", "description": "Propose the complete contents of one file. A diff is shown and user approval is required before writing.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}, "reason": {"type": "string"}}, "required": ["path", "content", "reason"]}}},
    {"type": "function", "function": {"name": "run_tests", "description": "Offer to run an allowlisted Python unittest, Maven, or Gradle test command based on project files. User approval is required.", "parameters": {"type": "object", "properties": {}, "required": []}}},
]


def _run_tool(root: Path, name: str, args: dict[str, Any]) -> str:
    try:
        if name == "list_files":
            return json.dumps(list_files(root, int(args.get("limit", 120))))
        if name == "read_file":
            return read_file(root, args["path"], args.get("start_line", 1), args.get("line_count"))
        if name == "search_text":
            return search_text(root, args["query"])
        if name == "review_changes":
            return review_changes(root)
        if name == "apply_patch":
            return apply_patch(root, args["path"], args["old_text"], args["new_text"], args["reason"])
        if name == "propose_edit":
            return propose_edit(root, args["path"], args["content"], args["reason"])
        if name == "run_tests":
            return run_tests(root)
        return "Error: unknown tool"
    except Exception as exc:
        return f"Tool error: {type(exc).__name__}: {exc}"


class Agent:
    # Keep a modest conversation window so long sessions do not grow requests forever.
    MAX_HISTORY_CHARS = 50_000

    def __init__(self, provider, root: Path):
        self.provider = provider
        self.root = root.resolve()
        files = list_files(self.root)
        self.messages: list[dict[str, Any]] = [{
            "role": "system",
            "content": f"{SYSTEM_PROMPT}\n\nSelected project: {self.root.name}\nInitial file list:\n" + "\n".join(files),
        }]

    def ask(self, prompt: str) -> str:
        self._trim_history()
        turn_start = len(self.messages)
        completed_actions: list[str] = []
        self.messages.append({"role": "user", "content": prompt})
        for _ in range(8):
            try:
                message = self.provider.complete(self.messages, TOOL_DEFINITIONS)
            except Exception as exc:
                # Roll back the incomplete turn, including any tool calls already made.
                del self.messages[turn_start:]
                failure = f"Provider request failed ({type(exc).__name__}). Check the endpoint, model, key, and network, then try again."
                if completed_actions:
                    failure += "\nActions completed before the provider error:\n- " + "\n- ".join(completed_actions)
                return failure
            self.messages.append(message.model_dump(exclude_none=True))
            calls = message.tool_calls or []
            if not calls:
                return message.content or "(The model returned an empty response.)"
            for call in calls:
                try:
                    args = json.loads(call.function.arguments or "{}")
                    self._show_tool_progress(call.function.name, args)
                    result = _run_tool(self.root, call.function.name, args)
                    if ((call.function.name == "propose_edit" and result.startswith("Applied edit to "))
                            or (call.function.name == "apply_patch" and result.startswith("Applied patch to "))
                            or (call.function.name == "run_tests" and (result.startswith("Exit code:") or result.startswith("Test command timed out")))):
                        completed_actions.append(f"{call.function.name}: {result[:500]}")
                except (json.JSONDecodeError, KeyError) as exc:
                    result = f"Invalid tool arguments: {exc}"
                self.messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
        return "Stopped after the eight-step tool-call limit. Ask a follow-up to continue."

    @staticmethod
    def _show_tool_progress(name: str, args: dict[str, Any]) -> None:
        if name == "list_files":
            print("\n[Scanning project files]")
        elif name == "read_file":
            detail = str(args.get("path", "file"))
            if args.get("start_line"):
                detail += f" from line {args['start_line']}"
            print(f"\n[Reading {detail[:160]}]")
        elif name == "search_text":
            print(f"\n[Searching project for {str(args.get('query', 'text'))[:100]!r}]")
        elif name == "review_changes":
            print("\n[Reviewing Git changes]")
        elif name == "propose_edit":
            print("\n[Preparing a change for your review]")
        elif name == "apply_patch":
            print("\n[Preparing a focused change for your review]")
        elif name == "run_tests":
            print("\n[Preparing the approved test command]")

    def _trim_history(self) -> None:
        """Drop oldest complete turns while preserving valid tool-call/result groups."""
        def size() -> int:
            return sum(len(json.dumps(message, ensure_ascii=False)) for message in self.messages)

        while size() > self.MAX_HISTORY_CHARS:
            # Find the next user turn after the first one, then drop the entire oldest turn.
            next_user = next((i for i, item in enumerate(self.messages[2:], start=2)
                              if item.get("role") == "user"), None)
            if next_user is None:
                break
            del self.messages[1:next_user]

    def reset(self) -> None:
        self.messages = self.messages[:1]
