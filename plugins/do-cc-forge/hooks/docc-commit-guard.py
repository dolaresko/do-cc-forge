#!/usr/bin/env python3
"""
docc-commit-guard.py — PreToolUse hook.
Enforces conventional commit format and message quality scaled to diff size.
Adapted from oh-my-claude by TechDufus (MIT).

Checks:
  1. Conventional commit format: <type>[scope]: <description>
  2. Subject <= 50 chars
  3. Body lines <= 72 chars
  4. Body detail proportional to diff size
  5. No AI attribution
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from hook_utils import (
    log_debug, output_deny, output_empty,
    parse_hook_input, read_stdin_safe,
)

CONVENTIONAL = re.compile(r'^[a-z]+(\([a-z0-9\-]+\))?!?: .+$')

AI_PATTERNS = [
    re.compile(r'generated (with|by) (claude|ai|gpt|chatgpt|anthropic)', re.I),
    re.compile(r'co-authored-by:?\s*(claude|ai|anthropic|chatgpt|copilot)', re.I),
    re.compile(r'\bai-generated\b', re.I),
    re.compile(r'\bai-assisted\b', re.I),
    re.compile(r'\bclaude generated\b', re.I),
]


def extract_message(command: str) -> str | None:
    """Return every -m message joined, in source order.

    A commit may pass several -m flags (git concatenates them as paragraphs),
    so an AI-attribution trailer riding a second -m must still be scanned —
    reading only the first -m let `-m "subject" -m "Co-Authored-By: ..."`
    slip through. Handles both the heredoc form
    (-m "$(cat <<'EOF' ... EOF )") and inline-quoted form (-m "text"/-m 'text').
    """
    found: list[tuple[int, str]] = []

    heredoc = re.compile(
        r'-m\s+"\$\(\s*cat\s+<<[\'"]?(\w+)[\'"]?\s*\n(.*?)\n\1\s*\)"',
        re.DOTALL,
    )
    for m in heredoc.finditer(command):
        found.append((m.start(), m.group(2)))
    # Blank heredoc spans (length-preserving) so the inline pass below can't
    # re-match the -m or any quotes inside a heredoc body.
    masked = heredoc.sub(lambda m: ' ' * (m.end() - m.start()), command)

    inline = re.compile(r'-m\s+"([^"]*)"|-m\s+\'([^\']*)\'')
    for m in inline.finditer(masked):
        found.append((m.start(), m.group(1) if m.group(1) is not None else m.group(2)))

    if not found:
        return None
    found.sort(key=lambda t: t[0])
    return '\n\n'.join(text for _, text in found)


def validate_format(msg: str) -> list[str]:
    errors: list[str] = []
    subject = None
    for i, line in enumerate(msg.split('\n')):
        s = line.strip()
        if s.startswith('#') or (subject is None and not s):
            continue
        if subject is None:
            subject = line
            if len(line) > 50:
                errors.append(f"Subject too long ({len(line)} chars, max 50): '{line[:50]}...'")
            if not CONVENTIONAL.match(line):
                errors.append(
                    "Use conventional commit format: <type>[scope]: <description>\n"
                    "  Examples: feat: add login, fix(auth): resolve token expiry"
                )
        else:
            if len(line) > 72:
                errors.append(f"Body line {i+1} too long ({len(line)} chars, max 72)")
    for p in AI_PATTERNS:
        if p.search(msg):
            errors.append("Remove AI attribution from commit message.")
            break
    return errors


def diff_stats() -> tuple[int, int]:
    try:
        r = subprocess.run(
            ["git", "diff", "--cached", "--numstat"],
            capture_output=True, text=True, timeout=5
        )
        if r.returncode != 0:
            return 0, 0
        added = deleted = files = 0
        for line in r.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split('\t')
            if len(parts) >= 2:
                files += 1
                if parts[0] != '-':
                    added += int(parts[0])
                if parts[1] != '-':
                    deleted += int(parts[1])
        return added + deleted, files
    except Exception:
        return 0, 0


def body_lines(msg: str) -> int:
    lines = msg.strip().split('\n')
    in_body = False
    count = 0
    for line in lines[1:]:
        if not in_body:
            if not line.strip():
                in_body = True
            continue
        if line.strip():
            count += 1
    return count


def quality_check(msg: str, lines_changed: int, files: int) -> str | None:
    bl = body_lines(msg)
    subject = msg.strip().split('\n')[0]
    if lines_changed < 10 and files <= 2:
        return None
    if lines_changed < 50 and bl == 0:
        return (f"Diff: {lines_changed} lines / {files} files — add a body explaining WHY.\n\n"
                f"{subject}\n\nBrief explanation of the problem and solution.")
    if lines_changed < 200 and bl < 2:
        return (f"Diff: {lines_changed} lines / {files} files — body needs >= 2 lines:\n"
                "- What problem this solves\n- How you approached it\n- Notable tradeoffs")
    if lines_changed >= 200 and bl < 4:
        return (f"Diff: {lines_changed} lines / {files} files — large change needs detailed body:\n"
                "- Context: what problem does this solve?\n"
                "- Approach: how did you solve it?\n"
                "- Changes: key modifications\n- Impact: what does this enable?")
    return None


def main() -> None:
    data = parse_hook_input(read_stdin_safe())
    if not data or data.get("tool_name") != "Bash":
        output_empty()

    command = data.get("tool_input", {}).get("command", "")
    if not re.search(r'\bgit\s+commit\b', command):
        output_empty()
    if '--amend' in command and '-m' not in command:
        output_empty()

    msg = extract_message(command)
    if not msg:
        output_empty()

    errors = validate_format(msg)
    if errors:
        output_deny("[Commit format] " + " | ".join(errors))

    lines_changed, files = diff_stats()
    if lines_changed == 0:
        output_empty()

    reason = quality_check(msg, lines_changed, files)
    if reason:
        output_deny("[Commit quality] " + reason)

    log_debug("commit message OK")
    output_empty()


if __name__ == "__main__":
    main()
