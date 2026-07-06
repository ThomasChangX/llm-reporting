# ADR-0007: Query Service Component

- **Status**: Accepted
- **Date**: 2026-07-05
- **Deciders**: Project Sponsor

## Context

The Reporting system needs intelligent interaction with data sources: IT configures data source metadata → the system automatically builds relationship graphs → when users make NL requests, it automatically retrieves Schema to generate optimal query paths → ensures Pushdown to data sources for data correctness and optimal performance.

This logic belongs neither to the Data Connector (which only handles connect/read/write) nor to the Compute Engine (which only handles execution). Its architectural ownership needs to be clarified.

## Options Considered

### Option A: Embed in Compute Engine (Rejected)
Embed query planning logic within the Compute Engine.
- **Pro**: Reduces component count; query planning and execution in the same process
- **Con**: Confuses the responsibilities of query planning vs. query execution; NL→SQL translation depends on LLMs — embedding it in Compute Engine would violate the Runtime Plane zero AI side effects principle; Compute Engine becomes heavier and harder to evolve independently

### Option B: Embed in Data Connector (Rejected)
Embed query planning logic within the Data Connector Adapter.
- **Pro**: Close to the data source; Pushdown logic can deeply integrate with data source characteristics
- **Con**: Connectors should remain thin — only responsible for connect/read/write, not query planning logic; each Connector would need to implement NL→SQL translation independently, leading to duplication and inconsistency

### Option C: As Independent Component (Chosen)
Query Service as an independent component — assists NL→SQL translation in the Design Plane, while the Runtime Plane only executes pre-generated deterministic query plans.

## Decision

Adopt **Option C**: Query Service as an independent architectural component, composed of four sub-components:

1. **Metadata Manager**:
   - Schema Discovery: auto-scan DB Schema (tables/columns/types/indexes), detect PK/FK relationships (DDL declarations + naming convention inference + data distribution inference)
   - Relationship Declaration: IT manually declares and corrects table relationships (including cross-database, JOIN types, cardinality)
   - Schema Version Management

2. **Query Generator**:
   - NL→SQL translation (LLM-assisted; results frozen as deterministic query plans after human confirmation)
   - JOIN path selection (based on the relationship graph in Data Catalog)
   - Optimal table/column matching

3. **Pushdown Optimizer**:
   - WHERE/JOIN/AGGREGATION executed at the data source where possible
   - Pushdown Plan visualization (what executes at data source vs. Compute Engine)
   - Dialect adaptation (different SQL dialects for MySQL, PostgreSQL, BigQuery, etc.)

4. **Query Cache**:
   - Same SQL + parameters + Schema version → reuse cached result, configurable TTL
   - Schema change auto-invalidates related caches → notifies affected Workflow Owners

**Core Principle**: The Query Service generates query plans but does not execute queries — actual execution is delegated to the Compute Engine. This ensures the Runtime Plane has zero AI side effects (Query Service's NL→SQL translation uses LLMs in the Design Plane; the Runtime Plane only executes pre-generated deterministic SQL).

## Rationale

1. **Separation of Concerns**: Query planning (Metadata + NL→SQL + Pushdown) and query execution (Compute Engine) are fundamentally different technology stacks and workloads — the former is an AI-assisted interactive tool, the latter is deterministic high-performance computation.
2. **Clear AI Boundary**: NL→SQL translation uses LLMs, which happens in the Design Plane. The generated query plan is deterministic SQL that can execute in the Runtime Plane with zero AI side effects.
3. **Pushdown as Correctness Guarantee**: Do not rely on application-layer logic for data filtering — predicate pushdown to the data source ensures data is correctly filtered at the source, reducing transfer and guaranteeing consistency.
4. **Evolvability**: Query Service's Schema discovery, relationship inference, and query optimization algorithms can iterate independently, decoupled from Compute Engine version upgrades.

## Consequences

- **Positive**: Clear responsibility boundaries; NL→SQL AI usage is isolated in the Design Plane; Pushdown guarantees data correctness and performance.
- **Negative**: Adds an independent component, requiring additional deployment, monitoring, and operations.
- **Neutral**: Schema Discovery's automated relationship detection has limited confidence (especially for cross-database legacy systems without DDL constraints) — IT manual declaration is a necessary complement and cannot be fully replaced by AI.

## Linked Modules

- `docs/02-requirement.md` → FR15b (Query Service, 8 sub-requirements)
- `docs/03-architecture.md` → §5.3 (Query Service Detailed Design)
- `adr/0008-large-scale-data-strategy.md` → Decision #8 (Large-Scale Data)
