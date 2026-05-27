#!/usr/bin/env python3
"""
docc-danger-guard.py — PreToolUse hook.
Warns on risky bash patterns (curl|sh, wget|sh, etc).
Adapted from oh-my-claude by TechDufus (MIT).

Env: DOCC_DANGER_GUARD=0 to disable.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from hook_utils import (
    log_debug, output_empty, output_context,
    parse_bool_env, parse_hook_input, read_stdin_safe,
)

WARN_PATTERNS = [
    (r'\bcurl\s+.*\|\s*(ba)?sh',
     "piping curl to shell executes remote code — download first, inspect, then run"),
    (r'\bwget\s+.*\|\s*(ba)?sh',
     "piping wget to shell executes remote code — download first, inspect, then run"),
    (r'\bwget\s+.*&&\s*(ba)?sh',
     "wget followed by shell execution — download first, inspect, then run"),
    (r'\bcurl\s+.*\|\s*base64\s+-d\s*\|\s*(ba)?sh',
     "obfuscated remote code execution via base64 — download first, inspect, then run"),
]


def main() -> None:
    if not parse_bool_env("DOCC_DANGER_GUARD", default=True):
        output_empty()

    data = parse_hook_input(read_stdin_safe())
    if not data or data.get("tool_name") != "Bash":
        output_empty()

    command = data.get("tool_input", {}).get("command", "")
    if not command:
        output_empty()

    for pattern, reason in WARN_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            log_debug(f"danger pattern matched: {reason}")
            output_context("PreToolUse", f"SECURITY WARNING: {reason}. Proceed with caution.")

    output_empty()


if __name__ == "__main__":
    main()
