# ADR-0011: Materialize Job Type

- **Status**: Accepted
- **Date**: 2026-07-04
- **Deciders**: Project Sponsor

## Context

In TB-scale data scenarios, repeated aggregation queries (e.g., "monthly revenue summarized by region") scan billions of detail rows every time, wasting compute resources (each query may consume $0.50-$2.00 in Spark compute costs).

A mechanism is needed to pre-compute and persist frequently-queried aggregation results for direct use by subsequent queries.

## Options Considered

### Option A: Database Materialized Views (Rejected)
Rely on the underlying database's (PostgreSQL, ClickHouse) materialized view mechanism.
- **Pro**: Native support, no system-level development needed
- **Con**: Coupled to specific databases — different databases have different materialized view syntax and refresh mechanisms; not portable across engines (Design Plane DuckDB ↔ Runtime Plane Spark); materialized views are outside Compute Spec management scope, cannot be included in Freeze Bridge validation and CI/CD

### Option B: Query Service Cache Only (Rejected)
Only passively cache aggregation results at the Query Service's Query Cache layer.
- **Pro**: Simple to implement
- **Con**: Cache is passively populated — "cold start" queries are still slow; after cache TTL expires, queries fall back to detail scans; cache hit rate is unpredictable; inconsistent with the "proactive optimization" design philosophy

### Option C: Materialize as 9th Job Type (Chosen)
Add `materialize` Job Type as a first-class citizen of Compute Spec, enjoying the same orchestration, monitoring, and CI/CD capabilities as other Job Types.

## Decision

Adopt **Option C**: `materialize` as the 9th Job Type.

### YAML Schema
```yaml
- job: mat_revenue_monthly
  type: materialize
  materialize:
    strategy: incremental           # full_refresh | incremental
    refresh_column: order_date     # incremental watermark column
    retention: 13 months            # retention policy
    target_table: analytics.mv_revenue_monthly
    input:
      from: job_clean_orders       # upstream Job reference
```

### Refresh Strategy
| Strategy | Description | Applicable Scenario |
|----------|-------------|---------------------|
| `full_refresh` | Completely rebuild materialized table | Small data volume (<1M rows), after Schema changes, initial creation |
| `incremental` | Only process incremental data (advancing by `refresh_column` watermark) | TB-scale scenarios, daily increment <1% of total |

### Query Service Auto-Routing
Query Service automatically detects available materialized views when resolving NL queries: if `mat_revenue_monthly` already contains all columns and aggregation levels needed for the query → directly query the materialized view (skip detail table scan), reducing response time from minutes to seconds.

### CI/CD Integration
Materialized views are included in the Freeze Bridge validation process as part of Compute Spec:
- Schema changes → detect affected materialized views → auto-mark `stale`
- Upstream Job changes → auto-rebuild dependent materialized views (compare old vs. new results in Sandbox)

## Rationale

1. **Unified Compute Spec Management**: Materialized views use the same YAML definitions, scheduling, monitoring, CI/CD as source/transform/output Job Types — no need for a separate "materialized view management system."
2. **Cross-Engine Portability**: DuckDB (Design Plane, <100GB) and Spark (Runtime Plane, TB-scale) handle materialize with the same logic — unified interface for incremental refresh + full refresh.
3. **Query Service Transparent Routing**: Users don't need to know "whether data comes from a materialized view or a detail table" — Query Service auto-selects the optimal data source. This extends the "AI-assisted exploration, Runtime deterministic execution" philosophy.
4. **Proactive Optimization vs. Passive Caching**: materialize proactively pre-computes (refreshed on schedule), Query Cache passively populates (caches after first query), both complementary — materialized views cover known high-frequency queries, caching covers ad-hoc queries.

## Consequences

- **Positive**: TB-scale aggregation queries drop from minutes to seconds; CI/CD integration of materialized views ensures monitorable data freshness; unified Compute Spec management reduces operational complexity.
- **Negative**: Materialized views consume additional storage (TB-scale detail → GB-scale aggregation — increase is manageable); incremental refresh watermark management adds scheduling complexity; stale detection and auto-rebuild of materialized views require additional monitoring.
- **Neutral**: Selection of which queries merit materialization is initially manually determined by users — future Usage Pattern Mining can auto-recommend materialization candidates.

## Linked Modules

- `docs/02-requirement.md` → FR13.6 (9 Job Types), FR15c.4 (Materialized Aggregation)
- `docs/03-architecture.md` → §6 (Compute Spec), §5.4.4 (Pre-Aggregation & Materialization)
- `adr/0008-large-scale-data-strategy.md` → Decision #8 (Large-Scale Data Strategy)
