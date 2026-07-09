---
id: ADR-0008
title: "Large-Scale Data Strategy"
status: accepted
date: 2026-07-04
deciders: "Project Sponsor"
domain: Data
---

# ADR-0008: Large-Scale Data Strategy

- **Status**: Accepted
- **Date**: 2026-07-04
- **Deciders**: Project Sponsor

## Context

The system needs to support aggregation and querying at TB-scale data volumes, with complex data sources (multiple databases, files, APIs). Simply "switching to a bigger Compute Engine" (e.g., upgrading from DuckDB to Spark) is insufficient to solve the following problems:
- Full table scans (no partition pruning) causing query timeouts
- Full recomputation (no incremental processing) wasting compute resources
- Repeated computation (no materialization) scanning detail data for every identical aggregation query
- Heterogeneous data source JOINs requiring GB-scale data transfer across networks

## Options Considered

### Option A: Upgrade Compute Engine Only (Rejected)
Only upgrade the Heavy Engine to Spark without other architectural adjustments.
- **Pro**: Simple to implement
- **Con**: No partition pruning → TB-scale tables still full-scanned; no incremental → full recomputation every time; no materialization → repeated computation; cannot solve network bottleneck for heterogeneous source JOINs

### Option B: Full Big Data Stack (Rejected)
Deploy Spark + Trino + Ray + Kafka + Flink simultaneously.
- **Pro**: Comprehensive capabilities, covering all scenarios
- **Con**: Over-engineering for MVP — operational complexity explosion, team needs to master 5 distributed systems simultaneously; most scenarios are not needed in MVP (e.g., real-time stream processing has no initial demand)

### Option C: Six-Pronged Strategy (Chosen)
A six-pronged progressive strategy, with only Spark as Heavy Engine (Post-MVP), Trino/Ray deferred to Phase 7+.

## Decision

Adopt **Option C** (Six-Pronged Strategy):

1. **Partitioning & Pruning**:
   - Support for Apache Iceberg / Delta Lake / Hudi modern table formats
   - Auto-detect partition info → partition pruning → TB-scale table queries only scan relevant partitions
   - Priority: P0

2. **Incremental Processing**:
   - Three modes: Watermark incremental (by time column), CDC incremental (consume Change Log), Partition incremental (new partitions only)
   - Watermark state persistently stored, transactionally updated, not advanced on execution failure
   - Priority: P0

3. **Pre-Aggregation & Materialization**:
   - `materialize` Job Type: Full Refresh + Incremental Refresh
   - Query Service auto-detects available materialized views → routes queries (skipping detail scans)
   - Priority: P0

4. **Cost-Based Optimization**:
   - Table statistics collection (row count/NDV/histogram/NULL ratio/file-level Min-Max)
   - Statistics-based JOIN strategy selection (Broadcast/Shuffle/Pushdown)
   - Priority: P1

5. **Federated Query**:
   - Decision tree: small dimension table broadcast → same-source Pushdown → cross-source materialized copies → federated query engine
   - Auto-select strategy by transfer cost
   - Priority: P1

6. **Query Plan Guard**:
   - Design Plane: single preview limited by `max_estimated_rows` / `max_estimated_bytes`, exceeding triggers rejection
   - Runtime Plane: no limit but alerts when cost > budget
   - Priority: P1

7. **KB Storage — PG-First Progressive Strategy**:
   - KB storage adopts PG-First + Interface Abstraction: PostgreSQL handles Vector/Graph/Relational roles during MVP
   - Dedicated engines (Milvus/Neo4j) reserved via interface abstraction, introduced only when four gating conditions are simultaneously met: (a) PG stably exceeds p95 latency target (b) data volume consistently exceeds scale limit (c) PG-level optimizations exhausted (d) TCO cost-benefit positive
   - MVP has zero CDC pipeline — Vector and Graph queries directly go through PG, eliminating synchronization failures
   - Priority: P1 (interface abstraction P0, dedicated engine implementation P2)
   - See `adr/0013-kb-storage-strategy.md`

## Rationale

1. **Partition pruning is the foundation of TB-scale performance** — without partitioning, no engine can efficiently query TB-scale data. This is a P0 hard requirement.
2. **Incremental processing avoids "using a sledgehammer to crack a nut"** — 1GB daily new data should not require recomputing 10TB in full. CDC/Watermark patterns have been widely validated in the data warehouse domain (dbt, Airbyte, Fivetran).
3. **Materialization is the classic "trade space for time" strategy** — the prerequisite for sub-second TB-scale aggregation is pre-computed results. Query Service auto-routing ensures users are unaware.
4. **Progressive**: Trino/Ray are deferred because Spark is sufficient to cover core scenarios during MVP. Future introduction is demand-driven (not pre-emptive over-engineering).

## Consequences

- **Positive**: P0-level partitioning/incremental/materialization covers TB-scale core scenarios; federated query decision tree handles heterogeneous sources; Query Plan Guard prevents Design Plane from accidentally triggering full table scans; KB storage PG-First strategy significantly reduces operational complexity (MVP has only 2 stateful services: PG + S3).
- **Negative**: Iceberg/Delta Lake support increases Data Connector complexity; materialized view refresh requires scheduling and monitoring.
- **Neutral**: Deferring Trino/Ray means cross-source federated queries in MVP can only be achieved through materialized copies — sufficient for initial scenarios, but future complex cross-source JOINs will require Trino; KB dedicated engines are similarly deferred — if business growth far exceeds expectations, a one-time migration cost is incurred, but interface abstraction keeps it transparent to business code.

## Linked Modules

- `docs/02-requirement.md` → FR15c (Large-Scale Data, 8 sub-requirements), FR13.6 (materialize Job Type)
- `docs/03-architecture.md` → §5.4 (Large-Scale Data Architecture)
- `adr/0011-materialize-job-type.md` → Decision #11 (materialize Job Type)
