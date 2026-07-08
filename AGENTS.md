# AGENTS.md

> Instructions for AI agents (and human collaborators) working on this repository.

This is a **documentation-only repository** for the llm-reporting project (a design-phase next-gen BI system). All artifacts are Markdown (`docs/`, `adr/`) plus Mermaid diagram sources (`docs/diagrams/`). There is no application code, build step, or test suite — "correctness" here means **internal consistency**: cross-references resolve, counts agree across files, ADR conventions are followed, and the design is technically coherent.

## Repository Conventions

- **ADR format**: MADR (Markdown Architecture Decision Records). Each ADR lives in `adr/NNNN-slug.md` with sections: Context / Options Considered (with Pro/Con) / Decision / Rationale / Consequences / Industry References / Linked Modules. See `adr/README.md` and existing ADRs (e.g. `adr/0019`, `adr/0022`) for the canonical structure. **ADRs are immutable once Accepted** — corrections require a superseding ADR, not an edit to the original.
- **Counts must stay in sync across files**. When a count changes (number of ADRs, KB domains, MCPs, Skills, glossary terms), sweep every file that references it. Known count references live in: `README.md`, `docs/README.md`, `docs/01-facts.md`, `docs/02-requirement.md`, `docs/03-architecture.md`, `docs/04-timeline.md`, `docs/glossary.md`, `docs/architecture/entity-erd.md`, `docs/cross-reference-checklist.md`. Before claiming a PR is complete, grep for the old value across the whole repo.
- **Glossary footer** tracks the term count — update it when adding terms.
- **All content is in English.**

## Processing PR Review Comments and CI Failures

When addressing PR review feedback (CodeQL, Copilot, human reviewers) and CI failures, follow these three rules **in order**:

### 1. Validate locally before pushing

Before pushing any review-fix commit, run the project's validation. For this docs-only repo:

```bash
# No build/tests exist — the "check" is a cross-reference consistency sweep:
grep -rn "<stale-count>" docs/ README.md adr/     # confirm no stale counts remain
# Verify every Linked Modules target in any new/edited ADR actually exists.
```

Do not push until all checks pass locally. (For code repos, the equivalent is `just check` / `ruff check . && ruff format --check . && mypy && pytest`.)

### 2. Collect all failures before fixing

Pull **ALL** CodeQL comments, **ALL** Copilot comments, and **ALL** CI failure annotations at once. Produce a complete inventory (table of file:line / issue / valid? / action) **before writing any code**. Never fix one error, push, and repeat — related comments often share a root cause (e.g. a stale count referenced in 4 files), and fixing them together avoids multiple push cycles and drift.

```bash
gh api repos/<owner>/<repo>/pulls/<n>/comments --paginate      # all review comments
gh api repos/<owner>/<repo>/pulls/<n>/reviews                  # review summaries
gh pr checks <n>                                               # CI status
```

### 3. Close review threads after fixing code

Fixing code ≠ closing a review comment. After every fix is pushed, **reply individually to each review thread** explaining what changed (with the commit SHA), then **resolve the conversation**. Confirm zero unresolved threads before reporting completion.

```bash
# Reply to a review thread (use the comment id from the inventory)
gh api repos/<owner>/<repo>/pulls/<n>/comments/<comment_id>/replies \
  -f body="Fixed in <commit-sha>: <what changed>"
# Then resolve the thread via the GraphQL API (REST has no direct "resolve" endpoint)
```

A PR is not "review-handling complete" until: fixes pushed ✓, every thread replied to ✓, every thread resolved ✓, CI green ✓.

## When You're Stuck or Unsure

- If a review comment is **wrong**, push back with technical reasoning (cite the file/line that proves it) — do not blindly implement.
- If a review comment is **unclear**, ask for clarification before implementing.
- If a count conflict traces to a **pre-existing** inconsistency (not introduced by your change), fix it anyway if it's in scope, but call it out explicitly in the PR description so the root cause is visible.
