# query-serving — Query Service & Large-Scale Data Architecture

> **Origin**: §5.1–§5.4 of `docs/03-architecture.md`
> **Key ADRs**: [ADR-0007](../../adr/0007-query-service-component.md) (Query Service), [ADR-0008](../../adr/0008-large-scale-data-strategy.md) (Large-Scale Data Strategy)

## Positioning

The **Query Serving** sub-project handles the production read path — transforming user-facing report queries into optimized, pushdown-aware execution plans against potentially massive datasets. It owns the Query Service component (Metadata Manager, Query Generator, Pushdown Optimizer, Query Cache) and the Large-Scale Data Architecture strategies that keep queries performant at the 1000-tenant scale.

This is the most performance-sensitive sub-project: its SLO targets (NL→Preview P95 ≤ 15s, report generation) directly determine user-perceived latency.

## Boundaries

**In-scope:**
- Query Service orchestration (Metadata Manager → Query Generator → Pushdown Optimizer → Query Cache)
- Large-Scale Data Architecture: Partitioning & Pruning, Incremental Processing, Pre-Aggregation & Materialization, Cost-Based Optimization, Federated Heterogeneous Data Source Strategy
- Resilience Patterns (Bulkhead, Circuit Breaker, Retry, Timeout — §5.1)
- Data Classification Tiers (Public/Internal/Confidential/Restricted — §5.2)

**Delegated to other sub-projects:**
- ETL/transform execution → [`workflow-engine`](../workflow-engine/)
- Metadata source of truth → [`knowledge-services`](../knowledge-services/) (Data Catalog domain)
- RBAC enforcement on query results → [`platform-core`](../platform-core/)

## Module List

| Module | Origin | Document |
|--------|--------|----------|
| Query Service (Metadata Manager, Query Generator, Pushdown Optimizer, Query Cache) + Resilience + Data Classification | §5.1, §5.2, §5.3 | [`query-service.md`](query-service.md) |
| Large-Scale Data Architecture (Partitioning, Incremental, Pre-Agg, CBO, Federated) | §5.4 | [`large-scale-data.md`](large-scale-data.md) |

## External Interface Contract

| Interface | Consumer | Contract |
|-----------|----------|----------|
| `query.execute(report_spec, tenant_context) → result_set` | Production Environment, Cross-Env Read-Only | Optimized query with pushdown; RBAC-filtered |
| `query.preview(natural_language, sample_data) → preview` | Exploration Environment | Sub-second preview on sampled data |
| `materialize.get(aggregation_key) → cached_result` | Workflow Engine (materialize Job) | Pre-computed aggregation lookup |

## Related ADRs

- [ADR-0007](../../adr/0007-query-service-component.md) — Query Service Component
- [ADR-0008](../../adr/0008-large-scale-data-strategy.md) — Large-Scale Data Strategy
- [ADR-0011](../../adr/0011-materialize-job-type.md) — Materialize Job Type (pre-aggregation integration)
