#!/usr/bin/env bash
# do-cc-forge installer
# Copies hooks and agents into ~/.claude/ and wires hooks into ~/.claude/settings.json
# Safe to re-run — existing docc- entries are replaced, not duplicated.
set -euo pipefail

DOCC_DIR="$HOME/.claude/do-cc-forge"
AGENTS_DIR="$HOME/.claude/agents"
SETTINGS="$HOME/.claude/settings.json"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "-> Installing do-cc-forge..."

# 1. Copy hooks
mkdir -p "$DOCC_DIR/hooks"
cp "$SCRIPT_DIR/hooks/"*.py "$DOCC_DIR/hooks/"
echo "   hooks copied to $DOCC_DIR/hooks/"

# 2. Copy agents
mkdir -p "$AGENTS_DIR"
cp "$SCRIPT_DIR/agents/"*.md "$AGENTS_DIR/"
echo "   agents copied to $AGENTS_DIR/"

# 3. Patch settings.json
mkdir -p "$(dirname "$SETTINGS")"
[ -f "$SETTINGS" ] || echo '{}' > "$SETTINGS"

python3 - << PYEOF
import json
from pathlib import Path

settings_path = Path("$SETTINGS")
docc_dir      = "$DOCC_DIR"
hooks_json    = Path("$SCRIPT_DIR/hooks.json")

with open(settings_path) as f:
    settings = json.load(f)

with open(hooks_json) as f:
    template = json.load(f)

hooks_str  = json.dumps(template).replace("\$DOCC_DIR", docc_dir)
new_hooks  = json.loads(hooks_str)["hooks"]
existing   = settings.get("hooks", {})

for event, matchers in new_hooks.items():
    if event not in existing:
        existing[event] = []
    # Remove stale docc- entries so re-install is idempotent
    existing[event] = [
        m for m in existing[event]
        if not any("docc-" in h.get("command", "") for h in m.get("hooks", []))
    ]
    existing[event].extend(matchers)

settings["hooks"] = existing

with open(settings_path, "w") as f:
    json.dump(settings, f, indent=2)

print(f"   hooks wired into {settings_path}")
PYEOF


echo ""
echo "do-cc-forge installed."
echo ""
echo "   Hooks:  docc-health-check  docc-danger-guard  docc-commit-guard"
echo "           docc-context-monitor  docc-todo-guard"
echo "   Agents: docc-librarian  docc-reviewer  docc-auditor"
echo ""
echo "   Restart Claude Code to activate."
echo ""
echo "   Optional env vars (add to ~/.zshrc or ~/.bashrc):"
echo "     DOCC_HEALTH_WARN_LINES=120       warn when CLAUDE.md exceeds N lines"
echo "     DOCC_HEALTH_COMPRESS_LINES=200   auto-compress above N lines"
echo "     DOCC_AUTO_COMPRESS=0             disable auto-compress"
echo "     DOCC_CONTEXT_WARN_PCT=70         context window warn threshold (%)"
echo "     DOCC_CONTEXT_CRIT_PCT=85         context window critical threshold (%)"
echo "     DOCC_DANGER_GUARD=0              disable risky-command warnings"
echo "     DOCC_DEBUG=1                     verbose hook logging to stderr"
