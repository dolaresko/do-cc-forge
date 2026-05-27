# do-cc-forge

Opinionated Claude Code guardrails for developers who use [BMAD](https://github.com/bmadcode/BMAD-METHOD) or structured agentic workflows.

Hooks that enforce quality standards automatically + lean agents that protect your context window.

---

## Why not just use oh-my-claude or caveman?

Both are great projects. This repo exists because neither is a perfect fit for BMAD-based workflows:

**[oh-my-claude](https://github.com/TechDufus/oh-my-claude)** ships a lot of value, but also `ultrawork` mode and delegation hooks that actively conflict with BMAD's phase structure (`create-epic → create-story → dev-story`). Installing the full plugin risks the coder ignoring BMAD skills and doing things its own way. do-cc-forge takes only the parts that complement BMAD: commit quality, context monitoring, todo enforcement, and the agent definitions.

**[caveman](https://github.com/JuliusBrussee/caveman)** solves output token compression — useful if Claude's verbosity is costing you money. But it affects what Claude *says to you*, not how much context it consumes. The real bottleneck in long BMAD sessions is the context window, which `/clear` and `/compact` already handle structurally. Caveman's one genuinely useful idea here is `caveman-compress` — compressing `CLAUDE.md` to save input tokens every session. do-cc-forge bakes that logic directly into the `docc-health-check` hook as an autonomous background process.

**In short:** do-cc-forge is a curated subset, not a superset. Fewer moving parts, no conflicts, works out of the box with BMAD.

---

## What's inside

### Hooks (run automatically)

| Hook | Fires | What it does |
|---|---|---|
| `docc-health-check` | Session start | Checks CLAUDE.md size. Warns at 120 lines, auto-compresses at 200. |
| `docc-danger-guard` | Before bash | Warns on `curl\|sh`, `wget\|sh` and similar risky patterns. |
| `docc-commit-guard` | Before git commit | Enforces conventional commits, subject ≤50 chars, body depth scaled to diff size. |
| `docc-context-monitor` | After every tool | Warns at 70% context usage, critical alert at 85%. |
| `docc-todo-guard` | Before session stop | Blocks stop if TodoWrite/TaskList has open items. |

### Agents (invoke manually)

| Agent | How to invoke | What it does |
|---|---|---|
| `docc-librarian` | `Agent(subagent_type="docc-librarian", prompt="...")` | Reads large files/diffs, returns concise summaries. Keeps main context clean. |
| `docc-reviewer` | `Agent(subagent_type="docc-reviewer", prompt="...")` | Post-implementation code review with `file:line` evidence. |
| `docc-auditor` | `Agent(subagent_type="docc-auditor", prompt="...")` | Security audit — OWASP issues, secrets, injection flaws, lock-file risks. |

---

## Install

```bash
git clone https://github.com/YOUR_USERNAME/do-cc-forge
cd do-cc-forge
chmod +x install.sh
./install.sh
```

Restart Claude Code. Done.

Re-running `./install.sh` is safe — existing docc entries are replaced, not duplicated.

---

## Update

```bash
cd do-cc-forge
git pull
./install.sh
```

---

## Configuration

All settings via env vars. Add to `~/.zshrc` or `~/.bashrc`:

```bash
# CLAUDE.md health
export DOCC_HEALTH_WARN_LINES=120       # warn when CLAUDE.md grows past this
export DOCC_HEALTH_COMPRESS_LINES=200   # auto-compress above this (default: 200)
export DOCC_AUTO_COMPRESS=1             # set 0 to disable auto-compress

# Context window
export DOCC_CONTEXT_WARN_PCT=70         # warn threshold (percent)
export DOCC_CONTEXT_CRIT_PCT=85         # critical threshold (percent)

# Guards
export DOCC_DANGER_GUARD=1              # set 0 to disable risky-command warnings

# Debug
export DOCC_DEBUG=1                     # verbose hook output to stderr
```

---

## How auto-compress works

When `CLAUDE.md` grows beyond `DOCC_HEALTH_COMPRESS_LINES` (default 200 lines), `docc-health-check` compresses it at session start — no manual step needed:

- Drops filler words/phrases (`just`, `really`, `in order to`, `make sure to`, etc.)
- Preserves code blocks, inline code, URLs, paths, and headings **exactly**
- Creates `CLAUDE.md.original.md` backup before overwriting
- Non-blocking: on any error, session continues with a warning

Typical savings: 30–50% of prose content. Code and structure untouched.

**First time?** Set `DOCC_AUTO_COMPRESS=0`, let it warn for a few sessions, and review what it would compress before enabling.

---

## Per-project agents

Hooks are global — no per-project setup needed.

Agents are installed to `~/.claude/agents/` (global). To override an agent for a specific project, copy the relevant `.md` to `.claude/agents/` in that project's root — Claude Code will prefer the local version.

---

## Requirements

- macOS or Linux
- Python 3.11+
- Claude Code with hooks support

---

## Credits

do-cc-forge is built on ideas and code from two open-source projects, both MIT licensed:

- **[oh-my-claude](https://github.com/TechDufus/oh-my-claude)** by TechDufus — hook architecture, commit quality enforcer, context monitor, todo enforcer, danger guard, and agent definitions (librarian, reviewer, security auditor). The hook runner utilities (`hook_utils.py`) are adapted directly from this project.

- **[caveman](https://github.com/JuliusBrussee/caveman)** by Julius Brussee — the `caveman-compress` concept: compressing natural language memory files to reduce input tokens while preserving code and structure exactly. The auto-compress logic in `docc-health-check` is inspired by this approach, reimplemented as a standalone Python function without the caveman CLI dependency.

Both projects are worth checking out if you want the full experience they offer.

---

## License

MIT — see [LICENSE](./LICENSE).
