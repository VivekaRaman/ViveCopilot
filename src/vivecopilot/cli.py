import argparse
from pathlib import Path

from .agent.loop import Agent
from .config import Settings
from .providers.openai_compatible import OpenAICompatibleProvider
from .tools.files import list_files


def main() -> None:
    parser = argparse.ArgumentParser(description="Approval-based coding assistant demo")
    parser.add_argument("--project", default=".", help="Project directory the agent may inspect and edit")
    args = parser.parse_args()
    root = Path(args.project).resolve()
    if not root.is_dir():
        parser.error(f"Project directory does not exist: {root}")
    try:
        settings = Settings.from_environment()
    except ValueError as exc:
        parser.error(str(exc))
    provider = OpenAICompatibleProvider(settings)
    agent = Agent(provider, root)
    print(f"ViveCopilot | Project: {root}\nModel: {settings.model} | Type /help for commands")
    while True:
        try:
            prompt = input("\nYou> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            return
        if not prompt:
            continue
        if prompt == "/quit":
            return
        if prompt == "/help":
            print("Ask a coding question. Commands: /files, /reset, /help, /quit")
            continue
        if prompt == "/files":
            print("\n".join(list_files(root)))
            continue
        if prompt == "/reset":
            agent.reset()
            print("Conversation reset.")
            continue
        print("\nViveCopilot> " + agent.ask(prompt))


if __name__ == "__main__":
    main()
