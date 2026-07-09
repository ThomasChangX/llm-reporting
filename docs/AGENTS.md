# docs/AGENTS.md

> Documentation-specific rules — merge with the root [AGENTS.md](../AGENTS.md).

## Numbered Pipeline

The five core docs form a strict pipeline that must stay internally consistent:

```
01-facts.md → 02-requirement.md → 03-architecture.md → 04-timeline.md → 05-cost.md
```

`01-facts.md` is the **authoritative source** for counts (glossary terms, ADR records). If a count appears elsewhere, it must agree with 01-facts (and with reality).

## §N Section References

References to architecture sections use the `§N` sigil: `§5.4.4`, `§22A`, `§22A.3`. Grammar: `§[0-9]+[A-Z]?(\.[0-9]+)*`. The checker resolves these against `##`/`###`/`####` headings in `03-architecture.md`.

- When you add/rename a heading in `03-architecture.md`, grep for its `§N` token across the repo and update references.
- `§N` tokens that reference regulatory clauses (HIPAA 45 CFR §164, SOX §302/§404) or a doc's own internal sections (e.g. cost doc's §2.2.1) are NOT architecture cross-refs — the checker scopes these out, but keep them stylistically distinct to avoid confusion.

## Glossary Format

`docs/glossary.md` uses multiple `| Term | Definition |` tables (one per category). The footer's `Total Terms: N` is a **derived count** — it must equal the number of data rows. The checker recomputes it; do not hand-maintain a number that disagrees with the table.

Rules:
- One term per row. Avoid literal `|` inside definitions (breaks the row count).
- When adding a term, update the footer count AND any `complete glossary (N terms)` mentions.

## Decision ↔ ADR Mapping

The `### Decision #N` entries in `01-facts.md` form a **narrative sequence** (the order decisions were recorded for the reader), NOT a 1:1 correspondence with ADR numbers — `Decision #3` covers Compute Spec (ADR-0011), `Decision #7` covers Design Order (ADR-0003), etc. The invariant the checker enforces is **count parity**: the number of `### Decision #N` entries must equal the number of ADR files. Decision numbers must be unique plain integers (no `#7b`-style suffixes).

When you add an ADR, add a `### Decision #N` entry to `01-facts.md` (next sequential `#N`) — the checker enforces the count matches.

## Cross-Reference Checklist

`docs/cross-reference-checklist.md` holds manual verification baselines (extracted-file line counts, etc.). When an extracted file grows, update the baseline in section 3 — stale baselines undermine trust in the checklist.
