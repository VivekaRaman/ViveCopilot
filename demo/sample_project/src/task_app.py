"""A tiny synthetic task-list module for the ViveCopilot demo."""


def create_task(title: str) -> dict:
    return {"title": title, "done": False}


def complete_task(task: dict) -> dict:
    return {**task, "done": True}
