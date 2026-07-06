# ADR-0003: Design Order

- **Status**: Accepted
- **Date**: 2026-07-04
- **Deciders**: Project Sponsor

## Context

Designing a complex system requires clear priorities and dependency relationships to avoid rework caused by "draw the UI first, patch the architecture later." Additionally, the timing of building the Knowledge Base (KB) — as the foundation for trustworthy AI reasoning — has a significant impact on design quality.

## Options Considered

### Option A: Architecture → Core Engine → Thin KB + Basic Design Plane (Co-Evolve) → Full KB (Chosen)
Start from the architectural blueprint, build the core engine layer by layer, then let the thin KB and basic Design Plane evolve in parallel, and finally expand into a full KB.

### Option B: UI First → Engine Later (Rejected)
Complete the UI design first, then consider the backend engine.
- **Pro**: Quickly obtain a visual prototype, facilitating communication with non-technical stakeholders
- **Con**: Prone to generating technical debt; UI design may be castles in the air before core computational capabilities are validated (e.g., designed interactions may be impossible to implement at terabyte-scale data volumes)

### Option C: Full Parallel (Rejected)
Design all modules in parallel simultaneously.
- **Pro**: Theoretically fastest
- **Con**: Strong dependencies exist between modules (Engine depends on Compute Spec definitions, Design Plane depends on KB providing trustworthy knowledge)

## Decision

Adopt **Option A**: Architectural Blueprint → Core Engine → **Thin KB + Basic Design Plane evolving in parallel** (KB starts from PG+pgvector, with Design Plane user interactions driving organic KB growth) → Full KB.

## Rationale

1. **Necessity of Architecture First**: The isolation of the three planes (Design / Freeze / Runtime) is the most critical architectural decision and must be established before any component design.
2. **KB Should Not Be Built in an Ivory Tower**: Building a KB without user validation easily encodes incorrect assumptions (e.g., wrong business definitions, outdated data source mappings). User interactions in the Design Plane (defining metrics, associating data sources) naturally populate the KB, ensuring its content is validated through actual use.
3. **Operability of the "Thin KB"**: Starting from PG+pgvector (rather than going straight to a full Vector+Graph+Relational+Object Store) reduces initial complexity and allows the KB Schema to evolve with actual usage needs.

## Consequences

- **Positive**: The thin KB starts early and co-evolves with the basic Design Plane — users naturally populate the KB through design exploration (defining metrics, associating data sources); KB content is validated through actual use before expanding into a full KB. This parallel strategy yields user feedback faster than "full KB first, then Design Plane," while avoiding encoding incorrect assumptions in the KB.
- **Negative**: Migration from "thin KB" to "full KB" requires data migration and Schema upgrades; a dedicated task must be reserved in Phase 2.
- **Neutral**: The quality of the architectural blueprint determines the quality of all subsequent designs — the blueprint phase requires the most review and iteration.

## Linked Modules

- `docs/03-architecture.md` (Architecture design follows this order)
- `docs/04-timeline.md` → Phase 0-3
- `adr/0005-dual-plane-architecture.md` → Decision #5
