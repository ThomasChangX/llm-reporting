# AGENTS.md

> Instructions for AI agents (and human collaborators) working on this repository.

This is a **documentation-only repository** for the llm-reporting project (a design-phase next-gen BI system). All artifacts are Markdown (`docs/`, `adr/`) plus Mermaid diagram sources. There is no application code, build step, or test suite — "correctness" here means **internal consistency**: cross-references resolve, counts agree across files, ADR conventions are followed, and the design is technically coherent.

## Repository Layout

- `docs/` — design docs in a numbered pipeline: `01-facts` → `02-requirement` → `03-architecture` → `04-timeline` → `05-cost`, plus `glossary.md`, `cross-reference-checklist.md`, `adr-index.md` (generated), and subdirs (`architecture/`, `security/`, `operations/`, `diagrams/`, `api/`).
- `adr/` — Architecture Decision Records (MADR 4.0.0 format with YAML frontmatter), numbered `NNNN-slug.md`. See `adr/README.md` and `docs/adr-index.md`.
- `scripts/` — consistency tooling: `check_adr_semantics.py`, `gen_adr_index.py`, `new_adr.py`, `migrate_adr_frontmatter.py` (one-time, already run).
- `.github/styles/` — Vale prose-lint rules.

Subdirectory-specific rules live in **nested** `AGENTS.md` files (they merge with this root file): [`adr/AGENTS.md`](adr/AGENTS.md), [`docs/AGENTS.md`](docs/AGENTS.md).

## Validation Commands

No build/tests exist — the "check" is a cross-reference + consistency sweep. Run before pushing:

```bash
python3 scripts/check_adr_semantics.py          # ADR semantics + counts + §N refs
python3 scripts/gen_adr_index.py --check         # ADR index drift check
npx markdownlint-cli2 '**/*.md'                  # Markdown structure (local, staged via pre-commit)
```

**Vale (prose lint) and lychee (links) run in CI only** — they are not part of the local pre-commit hook (too heavy for a docs repo) and Vale is not assumed installed locally. If you want to pre-verify them before pushing, install Vale (`brew install vale`) and run `vale docs/ adr/`; otherwise expect these two checks to run only in CI.

CI (`.github/workflows/ci.yml`) is the **authoritative gate**: markdownlint + lychee (links) + Vale (prose) + ADR semantics + index drift, aggregated by an `alls-green` job. A red CI job on these is the expected feedback loop for Vale/lychee issues that local checks don't cover.

## ADR & Count Conventions

- **ADR format**: MADR 4.0.0. Each ADR has YAML frontmatter (`id`, `title`, `status`, `date`, `deciders`, `domain`, optional `supersedes`/`superseded_by`) followed by the body (`# ADR-NNNN: Title`, then Context / Options Considered / Decision / Rationale / Consequences / Linked Modules).
- **Decision content is immutable once Accepted** (Context/Options/Decision/Rationale/Consequences). *Metadata format* (frontmatter structure) may be batch-migrated once, documented in the commit, without changing decision semantics. Corrections to a decision require a **superseding ADR**, not an edit to the original.
- **Supersession is bidirectional**: if ADR-A is superseded by ADR-B, ADR-A's frontmatter has `superseded_by: ADR-B` AND ADR-B's frontmatter has `supersedes: ADR-A`. `check_adr_semantics.py` enforces both directions.
- **Counts must stay in sync**. When a count changes (ADRs, glossary terms, etc.), every active mention across the repo must agree. The checker enforces this — do not hardcode file-path lists (they drift); find mentions dynamically:
  ```bash
  grep -rniE '(Total Terms|complete glossary|\(N terms\)|N ADRs|N records)' docs/ README.md
  ```
  Historical snapshots inside an Accepted ADR's narrative (e.g. "from 11 terms to 102 terms") are **exempt** — they record what was true at decision time.
- **Decision ↔ ADR parity**: the `### Decision #N` entries in `docs/01-facts.md` (a narrative sequence, not 1:1 with ADR numbers) must **match the ADR file count**. The checker enforces count parity + unique plain-integer numbering.

## Git & PR

- **Commit style**: [Conventional Commits](https://www.conventionalcommits.org/), scope = module (`docs(glossary):`, `adr(0025):`, `fix(cross-ref):`, `chore(ci):`).
- **Branching**: feature branch off `main` (`docs/<topic>` or `adr/<NNNN>-<slug>`); never commit directly to `main`; delete the branch after merge.
- **PR review & CI protocol**: see [PR review handling](#when-youre-stuck-or-unsure) below. When fixing review feedback: validate locally → batch-collect all comments → fix → reply to & resolve each thread → confirm CI green.

## Boundaries

- ✅ **Always**: update counts across **all** files when a count changes; run `check_adr_semantics.py` + `gen_adr_index.py --check` before claiming a PR is done; regenerate `docs/adr-index.md` when adding/editing an ADR (`python3 scripts/gen_adr_index.py && git add docs/adr-index.md`); match surrounding style.
- ⚠️ **Ask first**: editing decision **content** of an Accepted ADR (prefer a superseding ADR); large restructuring of `docs/`.
- 🚫 **Never**: hand-edit `docs/adr-index.md` (it is generated); leave a `TBD`/`TODO`/`FIXME` in a merged doc; mix languages (all content is in English).

## When You're Stuck or Unsure

- If a review comment is **wrong**, push back with technical reasoning (cite the file:line that proves it) — do not blindly implement.
- If a review comment is **unclear**, ask for clarification before implementing.
- If a count conflict traces to a **pre-existing** inconsistency (not introduced by your change), fix it anyway if it's in scope, but call it out explicitly in the PR description so the root cause is visible.
- Collect **ALL** review comments and CI annotations before fixing — related issues often share a root cause, and fixing them together avoids multiple push cycles.
