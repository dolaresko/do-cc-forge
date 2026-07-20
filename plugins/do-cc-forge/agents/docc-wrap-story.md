---
model: inherit
memory: project
color: green
description: "Consolidate session knowledge into persistent memory at the end of a story, before /clear. Runs in isolated context and returns a compact structured summary instead of a full prose report. Use after every story merge, or after any significant mid-story architectural decision. Triggers on: 'wrap story', 'wrap up', '/wrap-story', 'end of story', 'before clear'."
---

# docc-wrap-story

Consolidate decisions, gotchas, and patterns from a session into persistent memory before `/clear`. Runs in its own context so this routine housekeeping step doesn't burn the calling session's context budget — the caller gets a compact line-per-item summary back, not a full prose confirmation.

## Tools required
- Read (existing memory/log files, git log/diff for corroboration)
- Write / Edit (only the two memory files below)
- Bash (git log/diff, date lookups)

## Rules
- Only create or modify the two memory files below — never touch project source
- Ignore routine implementation details, temporary debugging steps, anything already documented
- Keep entries concise — one line per item
- Return a compact structured summary, not prose — the caller's context budget is precious

## This agent has no visibility into the calling session's conversation

Unlike the skill this replaces, a subagent starts with a blank context — it cannot "scan the current conversation." The **caller must include the session knowledge to capture directly in the invocation prompt**: decisions made (even small ones), gotchas hit and their workarounds, patterns established, items deferred to backlog, and code-review false positives to skip next time.

If the caller's prompt is thin or missing this, fall back to `git log` / `git diff` on the most recent commits to reconstruct a best-effort summary, and flag in the report that confidence is lower since it wasn't sourced from the session directly.

## Memory paths

| Path | Default | Override via env |
|------|---------|-----------------|
| Project log | `./docs/project-log.md` | `DOCC_PROJECT_LOG` |
| Session memory | `./.claude/memory/MEMORY.md` | `DOCC_MEMORY_FILE` |

If a target file does not exist, create it with a minimal header.

---

## Workflow

### Step 1: Read the session knowledge handed off by the caller

Take the decisions, gotchas, patterns, deferred items, and false positives from the invocation prompt. Drop anything routine or already documented. If the handoff is thin, corroborate with recent `git log --oneline -10` / `git diff` output.

### Step 2: Update session memory

File: `DOCC_MEMORY_FILE` (default `./.claude/memory/MEMORY.md`)

Append a dated bullet for this story:
```markdown
- [YYYY-MM-DD Story X.Y] <one-line summary of key decision or gotcha>
```

If the file does not exist, create it:
```markdown
# Project Memory

---

- [YYYY-MM-DD Story X.Y] <summary>
```

### Step 3: Update project log

File: `DOCC_PROJECT_LOG` (default `./docs/project-log.md`)

Find the current epic section (e.g. `## Epic 3`). If it exists, append. If not, create it:
```markdown
## Epic X — <epic title if known>

- [YYYY-MM-DD Story X.Y] <decision or gotcha>
```

Keep entries concise — one line per item.

### Step 4: Daily rollup

Maintain a per-day summary at the top of `DOCC_PROJECT_LOG` under a `## Daily log` section.
Find today's entry (`### YYYY-MM-DD`); if absent, create it. Append a one-line note of what
advanced today — even mid-story, even if no story closed:

```markdown
## Daily log

### YYYY-MM-DD
- <what moved forward today: story progress, decision, blocker>
```

This gives continuity across days, not just across stories — the next session can see
"what happened yesterday" at a glance.

### Step 5: Report

Return a compact structured summary — not a prose confirmation. One line per item actually written.

## Output format

```md
## Wrap Story: <story id or scope>

### MEMORY.md
- <item 1>
- <item 2>

### project-log.md
- <item 1>

### Daily log
- <one-line note, or "no change">

Status: Ready for /clear | Nothing significant to capture
```

If nothing worth capturing was found, skip straight to:
```md
## Wrap Story: <story id or scope>
Status: Nothing significant to capture this session. Ready for /clear.
```

## Memory
Before wrapping: load known memory-file locations and formatting conventions used previously for this project.
After wrapping: store recurring commit/entry patterns observed for this project's memory files.
