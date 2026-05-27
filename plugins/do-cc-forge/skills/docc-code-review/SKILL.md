---
name: docc-code-review
description: "Run an independent AI code review on the current git branch using a second model via OpenRouter. Use before merging any story branch. Triggers on: 'run code review', 'review this branch', 'code review'. Always run this before merge — do NOT self-review in the same session."
---

# docc-code-review

Independent code review via a second AI model (OpenRouter) to catch what self-review in the same session misses.

## Tools required
- Bash (git commands)
- openrouterai MCP (`chat_completion`)

## Configuration via env vars

| Var | Default | Purpose |
|-----|---------|---------|
| `DOCC_REVIEW_MODEL` | `deepseek/deepseek-v4-pro` | Primary review model |
| `DOCC_REVIEW_FALLBACK` | `qwen/qwen3-coder-next` | Fallback model |
| `DOCC_REVIEW_STACK` | *(empty)* | Extra stack context injected into system prompt |

Set `DOCC_REVIEW_STACK` to describe your project's tech stack for more relevant feedback:
```bash
export DOCC_REVIEW_STACK="Next.js 15 App Router, TypeScript strict, tRPC v11, Drizzle ORM"
```

---

## Workflow

### Step 1: Get the diff

```bash
git branch --show-current

# On a feature/story branch:
git diff origin/main...HEAD
# or against dev:
git diff origin/dev...HEAD

# Already merged — diff the merge commit:
git log --merges --oneline -5
git diff <merge-commit>^1 <merge-commit>
```

Also look for a story/spec file if the project uses BMAD:
```bash
ls _bmad-output/implementation-artifacts/ 2>/dev/null | grep <story-id>
```
If found, read it for acceptance criteria context.

### Step 2: Build system prompt

Base prompt:
```
You are a senior software engineer doing a thorough code review.
Focus on correctness, security, and maintainability.

Rules:
- No type-unsafe code without justification
- Auth/permission checks on all mutations
- No hardcoded secrets or credentials
- DB migrations must be additive only — never modify existing migrations
- Error handling must be explicit

Output — skip style nitpicks, be direct:
## 🔴 Bugs / Logic Errors
## 🟠 Security / Auth Issues
## 🟡 Code Quality Issues
## 🟢 Looks Good
## ⚪ Out of Scope

For each issue: file + line + description + suggested fix.
If nothing critical — say so explicitly.
```

If `DOCC_REVIEW_STACK` is set, append: `Stack: <value>`
If story ACs were found, append them to the user message.

### Step 3: Call OpenRouter

Call `openrouterai:chat_completion` with:
- `model`: `DOCC_REVIEW_MODEL` (default `deepseek/deepseek-v4-pro`)
- `messages`: system prompt + user message with full diff (+ ACs if available)

If primary model errors, retry once with `DOCC_REVIEW_FALLBACK`.

### Step 4: Report

Present model output as-is. Prepend one-line summary:
```
Review (<model>): X critical, Y warnings. [Fix before merge / Clear to merge]
```

Categorize findings:
- **Fix before merge** — bugs, security holes, broken migrations, business rule violations
- **Backlog** — non-blocking improvements worth tracking

Do not auto-fix. Wait for human decision.
