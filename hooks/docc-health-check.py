#!/usr/bin/env python3
"""
docc-health-check.py — SessionStart hook.
Checks CLAUDE.md health and auto-compresses when it grows too large.

Thresholds (env-configurable):
  DOCC_HEALTH_WARN_LINES     — warn, default 120
  DOCC_HEALTH_COMPRESS_LINES — auto-compress, default 200
  DOCC_AUTO_COMPRESS         — set to 0 to disable auto-compress

Auto-compress: pure Python, no LLM.
  - Drops filler words/phrases from prose lines
  - Preserves code blocks, inline code, URLs, paths, headings EXACTLY
  - Creates CLAUDE.md.original.md backup before overwriting
  - Non-blocking: on any error, logs warning and lets session continue
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from hook_utils import (
    get_nested, log_debug, output_context, output_empty,
    parse_hook_input, parse_bool_env, read_stdin_safe,
)

WARN_LINES     = int(os.environ.get("DOCC_HEALTH_WARN_LINES", 120))
COMPRESS_LINES = int(os.environ.get("DOCC_HEALTH_COMPRESS_LINES", 200))


# ---------------------------------------------------------------------------
# Compression — pure Python, no LLM
# ---------------------------------------------------------------------------

FILLER_PHRASES = [
    "in order to", "make sure to", "make sure that", "please make sure",
    "please ensure that", "it is important to", "it is worth noting that",
    "it would be good to", "it might be worth", "you could consider",
    "you should always", "you should", "remember to", "don't forget to",
    "be sure to", "always make sure", "in addition,", "furthermore,",
    "additionally,", "however,", "essentially,", "basically,",
    "generally speaking,", "of course,", "certainly,", "obviously,",
]

FILLER_WORDS = {
    "just", "really", "actually", "simply", "essentially",
    "basically", "generally", "certainly", "obviously",
}

REPLACEMENTS = {
    "in order to":    "to",
    "utilize":        "use",
    "utilizes":       "uses",
    "utilized":       "used",
    "utilizing":      "using",
    "make sure":      "ensure",
    "implement a solution for": "fix",
}

HARDCODED_PATH_RE = re.compile(
    r'\b(?:src|lib|app|components|utils|services|api|routes|models)/'
    r'[\w/]+\.(?:ts|tsx|js|jsx|py|go)(?::\d+)?\b'
)


def _is_code_fence(line: str) -> bool:
    return bool(re.match(r'^\s*```', line))


def _compress_text(text: str) -> str:
    """Compress prose, preserve inline code and URLs."""
    segments = re.split(r'(`[^`]+`|https?://\S+)', text)
    result = []
    for i, seg in enumerate(segments):
        if i % 2 == 1:
            result.append(seg)  # code/URL — preserve exactly
        else:
            result.append(_compress_prose(seg))
    return "".join(result)


def _compress_prose(text: str) -> str:
    for phrase, replacement in REPLACEMENTS.items():
        text = re.sub(re.escape(phrase), replacement, text, flags=re.IGNORECASE)
    for phrase in FILLER_PHRASES:
        text = re.sub(r'\b' + re.escape(phrase) + r'\b', '', text, flags=re.IGNORECASE)
    words = text.split()
    words = [w for w in words if w.lower().rstrip('.,;:') not in FILLER_WORDS]
    text = " ".join(words)
    return re.sub(r'  +', ' ', text).strip()


def _compress_line(line: str) -> str:
    stripped = line.strip()
    if stripped.startswith('#'):
        return line  # preserve headings exactly
    list_match = re.match(r'^(\s*[-*+]\s+|\s*\d+\.\s+)(.*)', line)
    if list_match:
        return list_match.group(1) + _compress_text(list_match.group(2))
    return _compress_text(line)


def compress_markdown(content: str) -> str:
    lines = content.split('\n')
    output: list[str] = []
    in_code_block = False
    for line in lines:
        if _is_code_fence(line):
            in_code_block = not in_code_block
            output.append(line)
            continue
        if in_code_block:
            output.append(line)
            continue
        output.append(_compress_line(line))
    return '\n'.join(output)


# ---------------------------------------------------------------------------
# Health analysis
# ---------------------------------------------------------------------------

def analyze(filepath: Path) -> dict[str, Any]:
    try:
        content = filepath.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {"ok": True}
    lines = content.split('\n')
    hardcoded = HARDCODED_PATH_RE.findall(content)
    return {
        "ok": False,
        "line_count": len(lines),
        "hardcoded_paths": len(hardcoded),
        "content": content,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    data = parse_hook_input(read_stdin_safe())

    if get_nested(data, "agent_type"):
        output_empty()

    cwd = Path(get_nested(data, "cwd", default="."))
    claudemd = cwd / "CLAUDE.md"

    if not claudemd.exists():
        output_empty()

    info = analyze(claudemd)
    if info.get("ok"):
        output_empty()

    lc = info["line_count"]
    warnings: list[str] = []

    if info["hardcoded_paths"] > 0:
        warnings.append(f"{info['hardcoded_paths']} hardcoded file path(s) detected (may go stale)")

    if lc >= COMPRESS_LINES:
        if not parse_bool_env("DOCC_AUTO_COMPRESS", default=True):
            warnings.append(
                f"CLAUDE.md is large ({lc} lines) — auto-compress disabled (DOCC_AUTO_COMPRESS=0)"
            )
        else:
            try:
                compressed = compress_markdown(info["content"])
                compressed_lc = len(compressed.split('\n'))
                if compressed_lc < lc - 5:
                    backup = claudemd.with_name("CLAUDE.md.original.md")
                    backup.write_text(info["content"], encoding="utf-8")
                    claudemd.write_text(compressed, encoding="utf-8")
                    saved = lc - compressed_lc
                    warnings.append(
                        f"CLAUDE.md auto-compressed: {lc} -> {compressed_lc} lines "
                        f"(saved {saved}). Backup: CLAUDE.md.original.md"
                    )
                else:
                    warnings.append(
                        f"CLAUDE.md is large ({lc} lines) but compression saved <5 lines — "
                        "consider splitting into nested CLAUDE.md files per directory."
                    )
            except Exception as e:
                log_debug(f"auto-compress failed: {e}")
                warnings.append(f"CLAUDE.md is large ({lc} lines) — auto-compress failed: {e}")

    elif lc >= WARN_LINES:
        warnings.append(
            f"CLAUDE.md is growing ({lc} lines). "
            f"Auto-compress triggers at {COMPRESS_LINES} lines."
        )

    if warnings:
        output_context("SessionStart",
            "[docc health-check]\n" + "\n".join(f"- {w}" for w in warnings))
    else:
        output_empty()


if __name__ == "__main__":
    main()
