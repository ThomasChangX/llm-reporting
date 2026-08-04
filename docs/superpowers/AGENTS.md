# docs/superpowers/ — Local Agent Instructions

> **Language exception**: The content in this directory is intentionally written in **Chinese (中文)**. This is an exception to the root `AGENTS.md` rule ("all content is in English") because these documents are **agent-facing operational tooling** (audit prompts, execution plans, spec tracking) used by AI agents during design-review workflows, not user-facing product documentation.
>
> The English-language rule in the root `AGENTS.md` applies to all product design docs (`01-facts.md` through `05-cost.md`, `glossary.md`, `03-architecture.md`, `adr/`, and `docs/sub-projects/`). This directory is tooling metadata, not product design.
>
> If these documents are ever promoted to product-facing status, they must be translated to English first.

## Directory Contents

- `design-audit-prompt.md` — The full-design-audit prompt template (v4). Covers 4 categories × 20 dimensions.
- `specs/` — Individual spec files tracking audit findings (C-NNN / I-NNN / M-NNN), each with metadata, fix plan, and acceptance criteria.
- `specs/INDEX.md` — Spec execution index (progress tracking).
- `specs/audit-NNNNNNNN-*.md` — Audit run reports and finding↔spec indices.
- `plans/` — Execution plans for multi-step tasks (e.g., ADR-0025 alignment).
- `plans/INDEX.md` — Plan execution index.
