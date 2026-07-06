# ADR-0004: Document Structure

> ⚠️ **This ADR has been superseded by [ADR-0012: Document Structure v2](./0012-document-structure-v2.md).** The document structure was reorganized on 2026-07-04. See ADR-0012 for the current structure.

- **Status**: Superseded by [ADR-0012](./0012-document-structure-v2.md)
- **Date**: 2026-07-04 (Superseded: 2026-07-04)
- **Deciders**: Project Sponsor

## Context

A documentation system is needed that supports iterative design, is maintainable, and is traceable. Documentation must cover: background facts, requirements, architecture, roadmap, cost analysis, Architecture Decision Records (ADRs), component design, and more.

## Options Considered

### Option A: Monolithic Document (Rejected)
All content in a single document.
- **Pro**: Simple structure, no cross-document references
- **Con**: Too long (currently exceeding 5,000+ lines), difficult for multiple people to collaboratively maintain; changes have a wide impact radius

### Option B: Per-Module Independent Documents (Rejected)
Each module as an independent document, maintained separately.
- **Pro**: Module autonomy, suitable for large teams
- **Con**: Cross-module references and consistency maintenance are difficult; lacks a global view

### Option C: Numbered Pipeline + Sub-Directories (Chosen)
Documents organized by design flow: `01-facts` → `02-requirement` → `03-architecture` → `04-timeline` → `05-cost`, plus `adr/` (Architecture Decision Records) and `components/` (component design).

## Decision

Adopt **Option C**: `facts → requirement → architecture → timeline → cost` + `adr/` (complete ADRs) + `components/` (component design, API specifications, etc., populated on demand).

## Rationale

1. Numbered documents naturally express the sequential dependency of the design — starting from background facts, deriving requirements, architecture, roadmap, and cost in order.
2. The independent `adr/` directory conforms to industry standards (mainstream practice in Google, AWS, and GitHub open-source projects); each ADR can be independently reviewed and referenced.
3. Cross-document references use explicit filename + section numbers (e.g., `docs/03-architecture.md §5.3`), allowing maintainers to quickly locate content.

## Consequences

- **Positive**: Clear division of responsibilities, allowing parallel maintenance; newcomers can understand the full system by reading in numbered order.
- **Negative**: Cross-document references require manual consistency maintenance — cross-validation is needed after every major change.
- **Neutral**: The `components/` directory can currently be used to archive detailed design documents (e.g., API specifications, data model DDL, security policies, etc.).

## Linked Modules

- All `.md` files in this repository
- `adr/README.md` → ADR Index
