#!/usr/bin/env python3
"""
docc-todo-guard.py — Stop hook.
Blocks session stop when TodoWrite/TaskList items are still open.
Adapted from oh-my-claude by TechDufus (MIT).
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from hook_utils import (
    is_agent_session, log_debug,
    output_empty, output_stop_block,
    parse_hook_input, read_stdin_safe,
)


def analyze_transcript(transcript: list[dict]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "last_todo_write": None,
        "last_task_list": None,
    }
    for entry in transcript[:1000]:
        t = entry.get("type", "")
        if t == "tool_result":
            tool = entry.get("tool", "")
            if tool == "TodoWrite":
                todos = entry.get("todos")
                if todos is not None:
                    result["last_todo_write"] = todos
            elif tool == "TaskList":
                tasks = entry.get("tasks")
                if tasks is not None:
                    result["last_task_list"] = tasks
    return result


def count_incomplete(items: list[dict] | None) -> tuple[int, list[str]]:
    if not items:
        return 0, []
    incomplete = [
        i.get("subject") or i.get("content") or "untitled"
        for i in items
        if i.get("status") in ("pending", "in_progress")
    ]
    return len(incomplete), incomplete


def main() -> None:
    data = parse_hook_input(read_stdin_safe())

    if is_agent_session(data):
        output_empty()

    stop_reason = data.get("stopReason") or data.get("stop_reason") or ""
    if stop_reason in ("user_interrupt", "explicit_stop", "user_cancelled", "abort"):
        output_empty()

    transcript = data.get("transcript") or []
    analysis = analyze_transcript(transcript)

    source = analysis["last_task_list"] or analysis["last_todo_write"]
    incomplete, subjects = count_incomplete(source)

    if incomplete == 0:
        output_empty()

    subjects_text = ", ".join(subjects[:10])
    log_debug(f"blocking stop: {incomplete} open items")

    context = f"""[WORK INCOMPLETE — CANNOT STOP]

{incomplete} open task(s): {subjects_text}

Rules:
- Do NOT stop until ALL tasks are marked completed
- Do NOT ask for permission — just continue working
- "I'll come back later" = you lose context. Finish now.

Continue working on the first open task."""

    output_stop_block("Open tasks remain", context)


if __name__ == "__main__":
    main()
