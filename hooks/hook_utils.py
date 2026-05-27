"""
hook_utils.py — shared utilities for do-cc-forge hooks.
Adapted from oh-my-claude by TechDufus (MIT).
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def read_stdin_safe() -> str:
    try:
        return sys.stdin.read()
    except Exception:
        return ""


def parse_hook_input(raw: str) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def get_nested(data: dict, *keys: str, default: Any = None) -> Any:
    cur = data
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k, default)
        if cur is default:
            return default
    return cur


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def output_empty() -> None:
    print(json.dumps({}))
    sys.exit(0)


def output_context(event: str, message: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": event,
            "additionalContext": message,
        }
    }))
    sys.exit(0)


def output_stop_block(reason: str, context: str) -> None:
    print(json.dumps({
        "decision": "block",
        "reason": reason,
        "hookSpecificOutput": {
            "hookEventName": "Stop",
            "additionalContext": context,
        }
    }))
    sys.exit(0)


def output_deny(reason: str) -> None:
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)


# ---------------------------------------------------------------------------
# Env helpers
# ---------------------------------------------------------------------------

def parse_bool_env(name: str, default: bool = True) -> bool:
    val = os.environ.get(name, "").strip().lower()
    if val in ("0", "false", "no", "off"):
        return False
    if val in ("1", "true", "yes", "on"):
        return True
    return default


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------

def is_agent_session(data: dict) -> bool:
    return bool(data.get("agent_type") or data.get("is_subagent"))


def log_debug(msg: str) -> None:
    if parse_bool_env("DOCC_DEBUG", default=False):
        print(f"[docc debug] {msg}", file=sys.stderr)
