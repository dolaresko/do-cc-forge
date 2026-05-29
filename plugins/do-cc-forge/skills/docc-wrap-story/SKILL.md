---
name: docc-wrap-story
description: "Consolidate session knowledge into persistent memory at the end of a story, before /clear. Run after every story merge. Triggers on: 'wrap story', 'wrap up', '/wrap-story', 'end of story', 'before clear'."
---

# docc-wrap-story

Consolidate decisions, gotchas, and patterns from the current session into persistent memory before `/clear`. Prevents context loss between stories.

## When to run
- After every story merge, before `/clear`
- After any significant mid-story architectural decision

## Memory paths

| Path | Default | Override via env |
|------|---------|-----------------|
| Project log | `./docs/project-log.md` | `DOCC_PROJECT_LOG` |
| Session memory | `./.claude/memory/MEMORY.md` | `DOCC_MEMORY_FILE` |

If a target file does not exist, create it with a minimal header.

---

## Workflow

### Step 1: Extract session knowledge

Scan the current conversation for:
- Architecture or design decisions made (even small ones)
- Gotchas hit and their workarounds
- Patterns established that should apply to future stories
- Items deferred to backlog
- False positives from code review (to skip next time)

Ignore: routine implementation details, temporary debugging steps, anything already documented.

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

### Step 5: Confirm

```
Memory updated. Ready for /clear.

Added to MEMORY.md:
- <item 1>

Added to project-log.md:
- <item 1>
```

If nothing worth capturing was found:
```
Nothing significant to capture this session. Ready for /clear.
```
