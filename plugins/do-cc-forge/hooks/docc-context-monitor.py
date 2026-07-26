#!/usr/bin/env python3
"""
docc-context-monitor.py — PostToolUse hook.
Warns when context window usage crosses thresholds.
Adapted from oh-my-claude by TechDufus (MIT).

Env:
  DOCC_CONTEXT_WARN_PCT   — warning threshold, default 70
  DOCC_CONTEXT_CRIT_PCT   — critical threshold, default 85
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from hook_utils import (
    get_nested, log_debug, output_context, output_empty,
    parse_hook_input, read_stdin_safe,
)

DEFAULT_WARN_PCT = 70
DEFAULT_CRIT_PCT = 85
CONTEXT_LIMIT   = 1000000
_DEDUP_DIR      = Path("/tmp")


def _threshold(env: str, default: int) -> float:
    try:
        return max(0, min(100, int(os.environ.get(env, default)))) / 100.0
    except ValueError:
        return default / 100.0


def _warned(session_id: str, level: str) -> bool:
    return (_DEDUP_DIR / f"docc_ctx_{session_id}_{level}").exists()


def _mark(session_id: str, level: str) -> None:
    try:
        (_DEDUP_DIR / f"docc_ctx_{session_id}_{level}").touch()
    except OSError:
        pass


def _usage(data: dict) -> float:
    transcript_path = get_nested(data, "transcript_path")
    if not transcript_path:
        return 0.0
    try:
        size = Path(transcript_path).stat().st_size
    except OSError:
        return 0.0
    return (size // 4) / CONTEXT_LIMIT


def main() -> None:
    data = parse_hook_input(read_stdin_safe())
    if not data:
        output_empty()

    session_id = get_nested(data, "session_id", default="unknown")
    pct = _usage(data)
    warn = _threshold("DOCC_CONTEXT_WARN_PCT", DEFAULT_WARN_PCT)
    crit = _threshold("DOCC_CONTEXT_CRIT_PCT", DEFAULT_CRIT_PCT)

    log_debug(f"context {pct:.0%} (warn={warn:.0%} crit={crit:.0%})")

    if pct >= crit:
        if _warned(session_id, "crit"):
            output_empty()
        _mark(session_id, "crit")
        output_context("PostToolUse",
            f"[CONTEXT CRITICAL: ~{pct*100:.0f}% used]\n"
            "Delegate large file reads to subagents. Consider /compact to recover space.")

    if pct >= warn:
        if _warned(session_id, "warn"):
            output_empty()
        _mark(session_id, "warn")
        output_context("PostToolUse",
            f"[Context: ~{pct*100:.0f}% used — approaching limit]\n"
            "Prefer subagent delegation for remaining reads.")

    output_empty()


if __name__ == "__main__":
    main()
