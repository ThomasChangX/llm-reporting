# adr/AGENTS.md

> ADR-specific rules — merge with the root [AGENTS.md](../AGENTS.md).

## Creating a New ADR

```bash
python3 scripts/new_adr.py "Decision Title" --domain Architecture --status proposed
# Then: fill Context/Options/Decision/Rationale/Consequences/Linked Modules,
#       add a `### Decision #N` entry to docs/01-facts.md,
#       regenerate index: python3 scripts/gen_adr_index.py && git add docs/adr-index.md
```

## Frontmatter Schema (MADR 4.0.0)

Every ADR MUST begin with YAML frontmatter:

```yaml
---
id: ADR-NNNN
title: "..."
status: proposed | accepted | deprecated | superseded | rejected
date: YYYY-MM-DD
deciders: "..."
domain: Architecture | Process | Product | Data | Operations | ...
supersedes: ADR-NNNN      # only if this ADR replaces an earlier one
superseded_by: ADR-NNNN   # only if this ADR is itself retired
---
```

- `status` is lowercase, matching the MADR 4.0.0 enum.
- `domain` is required and non-empty. If a decision spans domains, use `Architecture / Operations`.
- `supersedes` and `superseded_by` are a **bidirectional pair** — setting one without the other fails the consistency check.

## Immutability Rule (refined)

- **Decision content** (Context / Options Considered / Decision / Rationale / Consequences / Linked Modules) is **immutable** once `status: accepted`. Correcting a decision requires a new superseding ADR, not an edit.
- **Metadata format** (frontmatter structure, not field *values*) may be migrated once via a documented batch commit — this does not violate immutability because it changes representation, not the decision.
- Changing `status` (e.g. accepted → superseded) IS allowed: it records a lifecycle transition and MUST be accompanied by the matching `superseded_by` / `supersedes` field on both ADRs.

## Linked Modules

Every ADR's `## Linked Modules` section cross-references the rest of the design. Use `§N` references for architecture sections (e.g. `§22A`, `§5.4.4`) — the checker validates these against `docs/03-architecture.md`'s heading tree.
