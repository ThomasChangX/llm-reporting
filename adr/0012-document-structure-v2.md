---
id: ADR-0012
title: "Document Structure v2 (Supersedes ADR-0004)"
status: accepted
date: 2026-07-04
deciders: "Project Sponsor"
domain: Process
supersedes: ADR-0004
---

# ADR-0012: Document Structure v2 (Supersedes ADR-0004)

- **Status**: Accepted
- **Date**: 2026-07-04
- **Deciders**: Project Sponsor
- **Supersedes**: [ADR-0004: Document Structure](./0004-document-structure.md)

## Context

ADR-0004 established the original document structure: `facts → requirement → architecture → timeline → cost` + `adr/` + `components/`.

Since then, the project has evolved significantly:
1. The architecture doc grew to 5000+ lines, making standalone extraction of key sections necessary
2. Industry best practice audit (2026-07-04) identified gaps: no root README, no LICENSE, no SECURITY.md, numbered docs at root level violate conventions
3. The `components/` directory was referenced but empty, conflicting with the new `docs/` directory structure
4. The project needs diagrams-as-code, expanded glossary, and a cross-reference verification checklist

## Options Considered

### Option A: Keep ADR-0004 structure, add docs/ as supplementary (Rejected)
Add `docs/` alongside `components/` without resolving the conflict.
- **Pro**: Minimal change to existing docs
- **Con**: Two overlapping directories (docs/ vs components/); root clutter with 5 numbered files; no alignment with industry standards

### Option B: Full arc42 Migration (Rejected)
Restructure all documentation into arc42's 12-section format.
- **Pro**: Full standards compliance
- **Con**: Would break every cross-reference (500+ references across 11 ADRs — at time of writing; currently 24); over-engineering for a pre-implementation design phase

### Option C: Document Structure v2 (Chosen)
Evolutionary update that aligns with industry best practices while preserving all cross-references.

## Decision

Adopt the following document structure (v2):

```
llm-reporting/
├── README.md                          # Project entry point
├── CONTRIBUTING.md                    # Documentation contribution guidelines
├── SECURITY.md                        # Vulnerability reporting process
├── LICENSE                            # MIT
├── .gitignore
│
├── docs/                              # All design documentation
│   ├── README.md                      # docs/ navigation hub
│   ├── 01-facts.md                    # (moved from root)
│   ├── 02-requirement.md              # (moved from root)
│   ├── 03-architecture.md             # (moved from root; §15/§16/§18/§19 extracted)
│   ├── 04-timeline.md                 # (moved from root)
│   ├── 05-cost.md                     # (moved from root)
│   ├── glossary.md                    # 102 terms (extracted + expanded)
│   ├── cross-reference-checklist.md   # Manual verification checklist
│   ├── security/
│   │   └── threat-model.md            # STRIDE + OWASP LLM Top 10
│   ├── operations/
│   │   └── slo-sli.md                 # 5 critical user journey SLOs
│   ├── architecture/
│   │   ├── c4-model.md                # C4 System Context + Container diagrams
│   │   └── entity-erd.md              # 8 core entities DDL + relationships
│   ├── diagrams/
│   │   ├── README.md
│   │   ├── system-context.mmd
│   │   ├── four-plane-arch.mmd
│   │   └── freeze-bridge-flow.mmd
│   └── api/
│       └── README.md
│
├── adr/                               # Architecture Decision Records
│   ├── README.md                      # ADR index + MADR template
│   ├── 0001-...0011-... (11 original)
│   └── 0012-document-structure-v2.md  # This ADR
│
└── components/                        # Future: detailed component specs
    └── README.md
```

### Key Design Decisions

1. **Numbered docs moved to `docs/`**: Root directory reserved for governance files (README, LICENSE, SECURITY, CONTRIBUTING) per GitHub/industry convention
2. **Architecture sections extracted**: §15 (C4 Model), §16 (STRIDE), §18 (ERD), §19 (SLO/SLI) moved to standalone files under `docs/architecture/`, `docs/security/`, `docs/operations/`. Original section headers retained in 03-architecture.md with summaries + pointers — zero cross-reference breakage
3. **Glossary expanded**: From 11 terms to 102 terms, extracted from 02-requirement.md to `docs/glossary.md`
4. **`components/` retained**: Reserved for future detailed component specifications (API specs, data model DDLs, security policies). `docs/api/` and `docs/security/` hold architecture-level documents; `components/` holds implementation-level specifications
5. **Diagrams as code**: Mermaid (.mmd) source files version-controlled in `docs/diagrams/`

### Cross-Reference Convention (Updated)

All cross-document references use fully-qualified paths:
- `docs/03-architecture.md §N` for architecture sections
- `adr/NNNN-title.md` for ADRs
- `docs/glossary.md` for terms
- Within `docs/` directory, relative paths are used (e.g., `../03-architecture.md` from `docs/security/threat-model.md`)

## Rationale

1. **Root cleanliness**: Root-level `01-05.md` files violated industry conventions observed in Kubernetes, TensorFlow, VS Code, and other major projects
2. **Extraction reduces cognitive load**: 03-architecture.md was 5000+ lines; extracted sections are independently readable by security auditors (threat model), SRE teams (SLO/SLI), and database architects (ERD)
3. **Cross-reference preservation**: Section headers retained with summary+pointer pattern ensures all existing `→ §N` references continue to resolve
4. **Glossary as shared vocabulary**: 50+ term glossary enables consistent terminology across all documents and future implementation

## Consequences

- **Positive**: Industry-standard root structure; independently readable security/operations/architecture documents; expanded glossary; diagrams-as-code enable diff review
- **Negative**: Path updates required across 15+ files (completed via automated sed); cross-reference verification now requires periodic manual checks (checklist created)
- **Neutral**: `components/` directory retained but empty — to be populated when implementation phase begins (Phase 1+ of timeline)

## Linked Modules

- `adr/0004-document-structure.md` — Superseded by this ADR
- `adr/0005-four-layer-architecture.md` — Architecture design
- `docs/01-facts.md` — Updated header banner
- `docs/03-architecture.md` — Architecture doc with extracted sections
- `docs/cross-reference-checklist.md` — Verification checklist
