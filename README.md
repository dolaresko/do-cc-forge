# do-cc-forge

Quality guardrails for Claude Code, built for [BMAD](https://github.com/bmad-code-org/BMAD-METHOD) workflows.

Hooks that enforce standards automatically + skills and agents that keep your context clean.

Install once globally — works in every project.

---

## Why not just use oh-my-claude or caveman?

Both are great projects. This repo exists because neither fits well with BMAD-based workflows out of the box.

**[oh-my-claude](https://github.com/TechDufus/oh-my-claude)** ships useful hooks but also `ultrawork` mode and delegation hooks that conflict with BMAD's phase structure. do-cc-forge takes only the parts that complement BMAD: commit quality, context monitoring, todo enforcement, and the agent definitions.

**[caveman](https://github.com/JuliusBrussee/caveman)** compresses Claude's output tokens — not context window usage. The real bottleneck in long BMAD sessions is the context window, which `/clear` and `/compact` already handle structurally. Caveman's one useful idea here is `caveman-compress` — shrinking `CLAUDE.md` to save input tokens. do-cc-forge bakes that logic into `docc-health-check` as an autonomous background hook, with no extra CLI dependency.

**In short:** do-cc-forge is a curated subset designed to complement BMAD, not replace it.

---

## Install

```
/plugin marketplace add YOUR_GITHUB_USERNAME/do-cc-forge
/plugin install do-cc-forge@do-cc-forge
```

Restart Claude Code. Done.

### Update

```
/plugin marketplace update do-cc-forge
/plugin update do-cc-forge@do-cc-forge
```

---

## What's inside

### Hooks (automatic — fire in the background)

| Hook | Fires | What it does |
|---|---|---|
| `docc-health-check` | Session start | Checks `CLAUDE.md` size. Warns at 120 lines, auto-compresses at 200. |
| `docc-danger-guard` | Before bash | Warns on `curl\|sh`, `wget\|sh` and similar risky patterns. |
| `docc-commit-guard` | Before `git commit` | Enforces conventional commits, subject ≤50 chars, body depth scaled to diff size. |
| `docc-context-monitor` | After every tool | Warns at 70% context usage, critical alert at 85%. |
| `docc-todo-guard` | Before session stop | Blocks stop if `TodoWrite`/`TaskList` has open items. |

### Skills (trigger by phrase or invoke manually)

| Skill | Trigger | What it does |
|---|---|---|
| `docc-code-review` | `run code review` | Independent AI review of the current branch via OpenRouter before merge. |
| `docc-wrap-story` | `wrap story` | Captures decisions and gotchas into persistent memory before `/clear`. |

### Agents (invoke manually in prompts)

| Agent | How to invoke | What it does |
|---|---|---|
| `docc-librarian` | `Agent(subagent_type="docc-librarian", prompt="...")` | Reads large files/diffs, returns concise summaries — keeps main context clean. |
| `docc-reviewer` | `Agent(subagent_type="docc-reviewer", prompt="...")` | Post-implementation code review with `file:line` evidence. |
| `docc-auditor` | `Agent(subagent_type="docc-auditor", prompt="...")` | Security audit — OWASP issues, secrets, injection flaws, lock-file risks. |

---

## Configuration

All settings via env vars. Add to `~/.zshrc` or `~/.bashrc`:

```bash
# CLAUDE.md health
export DOCC_HEALTH_WARN_LINES=120        # warn when CLAUDE.md grows past this
export DOCC_HEALTH_COMPRESS_LINES=200    # auto-compress above this
export DOCC_AUTO_COMPRESS=1              # set 0 to disable auto-compress

# Context window monitoring
export DOCC_CONTEXT_WARN_PCT=70          # warn threshold (percent)
export DOCC_CONTEXT_CRIT_PCT=85          # critical threshold (percent)

# Guards
export DOCC_DANGER_GUARD=1               # set 0 to disable risky-command warnings

# Code review (docc-code-review skill)
export DOCC_REVIEW_MODEL=deepseek/deepseek-v4-pro
export DOCC_REVIEW_FALLBACK=qwen/qwen3-coder-next
export DOCC_REVIEW_STACK="Next.js 15, TypeScript strict, tRPC"  # injected into review prompt

# Session memory (docc-wrap-story skill)
export DOCC_PROJECT_LOG=./docs/project-log.md       # default
export DOCC_MEMORY_FILE=./.claude/memory/MEMORY.md  # default

# Debug
export DOCC_DEBUG=1                      # verbose hook output to stderr
```

---

## How auto-compress works

When `CLAUDE.md` grows beyond `DOCC_HEALTH_COMPRESS_LINES` (default 200 lines), `docc-health-check` compresses it at the start of the next session automatically:

- Drops filler words and phrases (`just`, `really`, `in order to`, `make sure to`, etc.)
- Preserves code blocks, inline code, URLs, paths, and headings **exactly**
- Creates `CLAUDE.md.original.md` backup before overwriting
- Non-blocking: on any error, session continues with a warning

Typical savings: 30–50% of prose. Code and structure untouched.

**First time?** Set `DOCC_AUTO_COMPRESS=0`, let it warn for a few sessions, and review what it would compress before enabling.

---

## docc-code-review: requires OpenRouter

The `docc-code-review` skill uses a second AI model via [OpenRouter](https://openrouter.ai) to catch what self-review in the same Claude Code session misses. Requires the `openrouterai` MCP to be connected.

Set `DOCC_REVIEW_STACK` to your project's tech stack for more relevant feedback.

---

## docc-wrap-story: BMAD session memory

Run at the end of every story before `/clear`. The skill scans the session for decisions, gotchas, and patterns, then writes them to:

- `./.claude/memory/MEMORY.md` — per-session notes (read by future sessions)
- `./docs/project-log.md` — project-wide log grouped by epic

Both paths are configurable via env vars.

---

## Requirements

- macOS or Linux
- Python 3.11+
- Claude Code with plugin and hooks support
- OpenRouter MCP connected (for `docc-code-review` only)

---

## Credits

Built on ideas and code from two MIT-licensed projects:

- **[oh-my-claude](https://github.com/TechDufus/oh-my-claude)** by TechDufus — hook architecture, commit quality enforcer, context monitor, todo enforcer, danger guard, and agent definitions. `hook_utils.py` is adapted directly from this project.
- **[caveman](https://github.com/JuliusBrussee/caveman)** by Julius Brussee — the `caveman-compress` concept: compressing memory files to reduce input tokens while preserving code and structure exactly. The auto-compress logic in `docc-health-check` is inspired by this approach, reimplemented as a standalone Python function.

---

## License

MIT — see [LICENSE](./LICENSE).
