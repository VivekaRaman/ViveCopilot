# Architecture

ViveCopilot is split into four simple layers:

1. `cli.py` owns the interactive command line and selected project root.
2. `agent/loop.py` sends conversation turns and tool results to the configured provider.
3. `providers/` adapts the model API. The initial adapter uses OpenAI-compatible Chat Completions tool calls.
4. `tools/` reads and searches project text, proposes edits, and offers one fixed test command. `safety/` keeps paths inside the chosen root and asks before edits or test execution.

The model proposes actions; the host code enforces path checks and user approvals. File access skips generated folders and common credential paths, and individual file reads are capped. This is a showcase baseline, not a secure sandbox for running untrusted code. Test execution recognizes Python `unittest`, Maven, and Gradle markers, prefers Maven or Gradle wrappers when available, and runs one fixed command only after approval. Other test ecosystems can be added as separate, explicit adapters.
