# ViveCopilot

ViveCopilot is a learning project for building a repository-aware coding assistant. It is an original implementation, not a reproduction of Claude or GitHub Copilot. It uses a configurable OpenAI-compatible model API and requires review before applying edits.

## Status

The first milestone is implemented as a local command-line agent. It can inspect and search a selected project, propose a change with a diff, and run an explicitly approved test command.

## Safety and privacy

- Start with `demo/sample_project`, which contains synthetic code.
- The configured provider receives the prompt and any file contents used as context. Use only code you are allowed to share with that provider.
- Review diffs before accepting edits. Test runs execute code in the selected project.
- The test runner recognizes Python `unittest`, Maven, and Gradle projects. For Java builds it prefers the repository's Maven or Gradle wrapper when present; otherwise the runner must be installed. It asks before executing project tests.
- Ask `review my changes` to inspect staged and unstaged Git diffs. It skips common secret-looking paths and does not run project code.
- For edits, ViveCopilot prefers a focused unique-section patch to an existing file; full-file proposals are available for creating files. Every change requires your approval.
- Never commit API keys. `.env.example` contains placeholders only.

## Setup

Python 3.10 or newer is required.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
$env:OPENAI_API_KEY = "your-provider-key"
$env:OPENAI_BASE_URL = "https://api.openai.com/v1"
$env:VIVECOPILOT_MODEL = "gpt-4o-mini"
python -m vivecopilot --project demo/sample_project
```

Replace the endpoint and model with values from a provider you are authorized to use. The first version reads credentials from environment variables. Do not put real secrets in `.env.example` or commit them to Git.

## Example task

Ask: `Reject a task with a blank title and add tests for that behavior.` ViveCopilot should inspect the sample, propose focused changes, show a diff, and ask before writing or running tests.

## Commands

In the interactive prompt: `/help`, `/files`, `/reset`, `/quit`.

## GitHub

Commit and push from the repository folder after reviewing the files. Keep client or employer code and credentials out of this public showcase.
