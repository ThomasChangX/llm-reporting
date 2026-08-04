# Query Service

> **Origin**: §5.1, §5.2, §5.3 of [`docs/03-architecture.md`](../../03-architecture.md) | **Sub-project**: [query-serving](README.md)

## Purpose

This module covers the **Query Service** — the core bridge connecting "what data the user wants to see" with "how the system retrieves data from data sources." Admin configures data source metadata, AI assists in generating optimal queries, and Runtime executes them deterministically, ensuring query pushdown to data sources to reduce data transfer and guarantee correctness.

Query Service comprises three internal components — the **Metadata Manager** (§5.3.1), the **Query Generator** (§5.3.2), and the **Pushdown Optimizer** (§5.3.3) — plus a **Query Execution Delegate**, **Query Cache** (§5.3.5), and the **Collaboration matrix** with existing components (§5.3.4). It collaborates with the KB Data Catalog, AI Copilot, Query Rewriter, Data Connector Adapter, Compute Engine, and Code Graph.

This module also owns two cross-cutting concerns that govern Query Service behavior and every other service in the platform:

- **§5.1 Resilience Patterns** — Circuit Breaker, Bulkhead, Retry with Backoff, Graceful Degradation, Timeout Propagation, Dead Letter Queue.
- **§5.2 Data Classification Tiers** — T0 Public / T1 Internal / T2 Confidential / T3 Restricted, with the masking, retention, and export controls enforced across the classification flow.

## Boundaries

**In-scope:**
- §5.1 Resilience Patterns (Bulkhead, Circuit Breaker, Retry with Backoff, Graceful Degradation, Timeout Propagation, Dead Letter Queue).
- §5.2 Data Classification Tiers (T0–T3) and the Classification Flow.
- §5.3 Query Service: the three-component core (Metadata Manager, Query Generator, Pushdown Optimizer) plus the Query Execution Delegate.
- §5.3.1 Metadata Manager — Schema Discovery (Connection Test, Schema Scan, PK/FK Detection, Index Detection, Data Sampling) and Relationship Declaration (IT manual configuration).
- §5.3.2 Query Generator — Schema Resolution, JOIN Path Selection, SQL Generation, Query Validation.
- §5.3.3 Pushdown Optimizer — Pushdown Decision Matrix, `pushdown_policy` YAML, Pushdown Plan visualization.
- §5.3.4 Collaboration with Existing Components (KB Data Catalog, AI Copilot, Query Rewriter, Data Connector Adapter, Compute Engine, Code Graph).
- §5.3.5 Query Cache (L1 Result / L2 Schema / L3 Relationship caches and invalidation triggers).

**Delegated / out-of-scope:**
- **§5.4 Large-Scale Data Architecture** (Partitioning, Incremental, Pre-Aggregation, CBO, Federated) → [`large-scale-data.md`](large-scale-data.md).
- **Data Connector Adapter (5 Levels)** mechanics, **Compute Engine (Light/Heavy)** internals, and **KB Data Catalog** storage → other sub-projects (cross-referenced in §5.3.4).
- **Query Rewriter** RLS/CLS/masking engine mechanics → [`platform-core`](../platform-core/) (the Query Service consumes its rewritten SQL).

**Upstream/downstream neighbors:**
- *Read path*: AI Copilot (Design Plane) NL→Intent → Query Generator → ValidatedSQL → Query Rewriter (RLS/CLS/masking) → Data Connector Adapter → ResultSet → Compute Engine post-processing → FinalResult.
- *Metadata path*: Data Connector Adapter → Metadata Manager (scan) + IT Workbench (declaration) → KB Data Catalog → Query Generator reads back for Schema resolution.
- *Cache path*: Schema change detected by Data Connector → `SchemaChangeEvent` → Query Service invalidates L1/L3 → notifies Workflow Owners (via FR40 Dependency Manager).

## Interfaces

### §5.3 Query Service — component topology

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         QUERY SERVICE                                     │
│                                                                          │
│  ┌───────────────────┐  ┌───────────────────┐  ┌──────────────────────┐ │
│  │  METADATA MANAGER  │  │  QUERY GENERATOR   │  │  PUSHDOWN OPTIMIZER  │ │
│  │                    │  │                    │  │                      │ │
│  │ • Schema Discovery │  │ • NL→SQL Translation│  │ • Predicate Pushdown │ │
│  │ • FK/PK Detection   │  │ • JOIN Path Selection│  │ • Aggregation Pushdown│ │
│  │ • IT Manual Relations│  │ • Optimal Table/Col  │  │ • JOIN Order Optimize │ │
│  │ • Schema Versioning  │  │ • Query Plan Gen     │  │ • Dialect Adaptation  │ │
│  │                    │  │                    │  │ • Query Cost Estimate │ │
│  └────────┬───────────┘  └────────┬───────────┘  └──────────┬───────────┘ │
│           │                       │                          │             │
│           ▼                       ▼                          ▼             │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                     QUERY EXECUTION DELEGATE                         │ │
│  │                                                                      │ │
│  │  • Direct Pushdown (WHERE/JOIN/AGG completed at data source)          │ │
│  │  • Federated Execution (cross-source JOIN coordinated by Compute Engine)│ │
│  │  • Post-Query Processing (Light/Heavy Engine post-processing)          │ │
│  │  • Result Cache (reuse cache for same query params, TTL configurable)  │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
  ┌──────────┐     ┌──────────────┐     ┌──────────────────┐
  │   KB     │     │ Data Connector│     │ Compute Engine   │
  │  Data    │     │   Adapter     │     │ (Light / Heavy)  │
  │ Catalog  │     │  (5 Levels)   │     │                  │
  └──────────┘     └──────────────┘     └──────────────────┘
```

### §5.3.4 Collaboration with Existing Components

| Collaborating Component      | Interaction Method                                                                                                                       | Data Flow                |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| **KB Data Catalog**          | Metadata Manager writes scanned Schema + IT-declared relationships → Data Catalog. Query Generator reads Data Catalog for Schema resolution | Bidirectional            |
| **AI Copilot (Design Plane)** | Conversation Interface's Intent Parser passes NL→Intent to Query Generator; Query Generator returns ValidatedSQL for Preview execution   | NL Intent → SQL          |
| **Query Rewriter**           | SQL generated by Query Generator passes through Query Rewriter for RLS/CLS/masking injection before submission to Data Connector        | SQL → RewrittenSQL       |
| **Data Connector Adapter**   | Executes RewrittenSQL, returns result set. Pushdown Optimizer decides which operations complete on the Connector side                    | RewrittenSQL → ResultSet |
| **Compute Engine**           | Receives intermediate results after pushdown, completes post-processing (computed columns, cross-source JOIN, Python UDF)               | ResultSet → FinalResult  |
| **Code Graph**               | Records Pushdown Plan, referenced tables and columns, JOIN paths for each query → used for Impact Analysis                              | Query → Code Graph edges |

## Dependencies

- **Metadata Manager**: Data Connector Adapter (JDBC `DatabaseMetaData`, `INFORMATION_SCHEMA`); KB Data Catalog (stores schema + relationships as first-class entities); Code Graph (`REFERENCES` edges for declared relationships); IT Workbench (manual declaration entry point).
- **Query Generator**: KB Retrieval (Business Glossary formulas, dimension lookups); Data Catalog (table/column location); Mapping Registry (cross-system mapping); Relationship Graph (JOIN paths); Design Plane fallback for `AMBIGUOUS_JOIN_PATH`.
- **Pushdown Optimizer**: Data Connector Adapter (dialect capability probes, file-level stats); Compute Engine fallback (DuckDB/Spark) when pushdown is not viable.
- **Query Cache**: Redis (L1/L3), PostgreSQL (L2 schema snapshot).
- **Resilience (§5.1)**: per-data-source connections (Circuit Breaker); cgroups (Bulkhead CPU/memory limits); Workflow Executor + API Gateway (Retry); Event Bus / DLQ infrastructure (Notification, KB Write, Integration).
- **Data Classification (§5.2)**: Data Catalog (tags columns with sensitivity tier); Query Rewriter (enforces masking per tier + role); Log system (redacts T3 before write); Export gate (blocks T3 without approval).
- Cross-sub-project: [`knowledge-services`](../knowledge-services/) (Data Catalog, Business Glossary), [`workflow-engine`](../workflow-engine/) (Compute Spec, `data_writer`/`source` Jobs), [`platform-core`](../platform-core/) (Query Rewriter, Notification/DLQ).

## Data Model

- **§5.3.1 Metadata Manager outputs**:
  - `ConnectionStatus { ok, version, features }` — connection test result.
  - Complete table/column listing (types, nullable, defaults) — Schema Scan via `INFORMATION_SCHEMA` + JDBC `DatabaseMetaData`.
  - `RelationshipCandidate { confidence, evidence }` — PK/FK detection (DDL extraction → naming-convention inference → data-distribution inference).
  - `IndexInfo { columns, type, cardinality }` — index detection.
  - `SampleData { rows, column_stats }` — data sampling for type inference and preview.
- **`table_relationships` (§5.3.1 YAML)** — IT-declared relationships: `name`, `left`/`right` (data_source/schema/table/column), `join_type` (LEFT/INNER/RIGHT), `cardinality` (ONE_TO_ONE / ONE_TO_MANY / MANY_TO_ONE / MANY_TO_MANY), `business_rule`, `confidence` (1.0 for manual), `declared_by`, `declared_at`. Stored as first-class KB Data Catalog entities linked via Code Graph `REFERENCES` edges.
- **§5.3.2 Query Generator outputs**:
  - `ResolvedSchema { tables[], cols[], mappings[], confidence }` — Step 1 Schema Resolution.
  - `JoinPath { path[], estimated_cost, alternatives[], ambiguous }` — Step 2 JOIN Path Selection.
  - `ParameterizedSQL { sql, params[], referenced_tables[], dialect }` — Step 3 SQL Generation (ANSI SQL:2003 compliant, formulas translated, `$1`/`$2` parameterization).
  - `ValidatedSQL` with `validation_report` — Step 4 (AST + schema + permission + performance pre-check).
- **§5.3.3 Pushdown Optimizer**: `pushdown_policy` YAML + Pushdown Plan artifact (per-query, showing data-source-side vs Compute-Engine-side operations).
- **§5.3.5 Query Cache**: L1 Result Cache (SQL hash + params + schema version), L2 Schema Cache (Data Catalog snapshot), L3 Relationship Cache (resolved JOIN paths).
- **§5.2 Data Classification** — tier-tagged columns (T0–T3) flowing through the Classification Flow: Catalog tag → Rewriter masking → Log redaction → Export gate.

## Failure Modes & Recovery

The resilience posture for this module is defined by §5.1. Every resilience pattern below also applies to the Query Service read path and its collaborators.

### §5.1 Resilience Patterns

| Pattern                  | Implementation                                                                                                                                                                                                                                                                                                          | Scope                               |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------- |
| **Circuit Breaker**      | Per-data-source connection. 5 consecutive failures → circuit opens (30s). Half-open probe after cooldown. Prevents cascading failures from unhealthy upstream systems.                                                                                                                                                  | All Data Connectors                 |
| **Bulkhead**             | Per-tenant Sandbox pool isolation. One tenant's resource exhaustion cannot starve other tenants. Per-Job memory/CPU limits enforced by cgroups.                                                                                                                                                                         | Sandbox Pool, Tenant                |
| **Retry with Backoff**   | Failed transient operations (network timeout, connection refused): exponential backoff (1s→2s→4s→8s, max 3 retries). Non-transient errors (schema mismatch, auth failure): no retry, immediate Incident.                                                                                                                | Workflow Executor, API Gateway      |
| **Graceful Degradation** | **Opt-in per Workflow** (`fallback_to_light_engine: true`, must be explicitly declared, default false). When Heavy Engine is unavailable → eligible Workflows auto-degrade to Light Engine (must satisfy: within `max_estimated_rows` threshold + no Python transform or already transpiled). KB Vector search degradation → auto-switch to keyword search. All degradations trigger notifications and SLA degradation markers. | Compute Engine, KB Retrieval        |
| **Timeout Propagation**  | Every operation has a defined timeout. Timeouts propagate up the call chain (not reset). Parent operation timeout = sum of child timeouts + buffer.                                                                                                                                                                     | All Services                        |
| **Dead Letter Queue**    | Failed notifications, failed KB write-backs, and failed external API calls are routed to a DLQ with configurable retry policies. Prevents data loss during transient outages.                                                                                                                                           | Notification, KB Write, Integration |

### Query Service-specific failure handling

| Failure | Impact | Recovery |
| --- | --- | --- |
| Data source unhealthy (Query Service read path) | Pushdown fails / query stalls | Circuit Breaker opens after 5 consecutive failures (30s), half-open probe after cooldown; `fallback_on_pushdown_failure: true` routes post-processing to Compute Engine. |
| Pushdown guardrail breach (`max_rows_transferred` / `max_bytes_transferred`) | Unbounded data transfer | Pushdown Optimizer paginates / samples / rejects per `pushdown_policy`; falls back to Compute Engine coordination. |
| `AMBIGUOUS_JOIN_PATH` (Query Generator Step 2) | Cannot auto-select JOIN path | Fallback to Design Plane for user selection. |
| Query validation failure (Step 4) | Invalid/insecure SQL blocked | `validation_report` returned; rejected at AST/schema/permission/performance pre-check. |
| Schema change at source | Stale cache, wrong results | `SchemaChangeEvent` → L1/L3 invalidation → notify affected Workflow Owners (FR40). |
| Heavy Engine unavailable (degradable Workflow) | Slower execution | Graceful Degradation to Light Engine if `fallback_to_light_engine: true` and within `max_estimated_rows` (notification + SLA marker emitted). |
| T3 data export without approval | Compliance violation blocked | §5.2 Export gate blocks; requires Data Owner / explicit legal approval. |

## Non-Functional Requirements

### §5.1 Resilience — quantitative targets

- Circuit Breaker: 5 consecutive failures → open for 30s; half-open probe after cooldown.
- Retry: exponential backoff 1s→2s→4s→8s, max 3 retries (transient only); non-transient → immediate Incident.
- Timeout: every operation defined; parent = sum(child) + buffer; timeouts propagate, never reset.
- Graceful Degradation: opt-in per Workflow (`fallback_to_light_engine: true`, default false); degradation emits notification + SLA marker.
- DLQ: configurable retry policies for notifications, KB write-backs, external API calls.

### §5.2 Data Classification — controls per tier

All data in the system is classified into four sensitivity tiers. Controls are applied at each tier:

| Tier                 | Label                           | Examples                                                                                                    | Encryption                                                                 | Masking                                                | Retention                                                        | Export Control                             |
| -------------------- | ------------------------------- | ----------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- | ------------------------------------------------------ | ---------------------------------------------------------------- | ------------------------------------------ |
| **T0: Public**       | Non-sensitive metadata          | Workflow templates, public KB glossary terms                                                                | At-rest only                                                               | None                                                   | Permanent                                                        | Unrestricted                               |
| **T1: Internal**     | Operational data                | Workflow definitions, execution metrics, format templates, agent configurations                             | At-rest + Transit                                                          | None                                                   | 7 years                                                          | Tenant-admin approved                      |
| **T2: Confidential** | Business data                   | Report outputs, aggregated metrics, KB business terms, data catalog (non-PII columns)                       | At-rest + Transit + Application-level (AEAD)                               | Dynamic (role-based)                                   | Per policy (default 7 years)                                     | Data Owner approval                        |
| **T3: Restricted**   | PII, financial details, secrets | Customer names, financial transaction amounts, adjustment entries with reasons, email bodies containing PII | At-rest + Transit + Application-level + Column-level (envelope encryption) | Dynamic (default: redact/hash) + Audit on every access | Per regulation (GDPR: on-request deletion; SOX: 7 years minimum) | Prohibited without explicit legal approval |

**Classification Flow**: Data Catalog tags columns with sensitivity tier → Query Rewriter enforces masking per tier + role → Log system redacts T3 fields before writing → Export gate blocks T3 data in exports without approval.

### §5.3.5 Query Cache — layers and TTLs

| Cache Layer                | Hit Condition                                                        | TTL                        | Storage    |
| -------------------------- | -------------------------------------------------------------------- | -------------------------- | ---------- |
| **L1: Result Cache**       | Same SQL hash + same params + data source unchanged (schema version match) | 5 min (configurable)       | Redis      |
| **L2: Schema Cache**       | Schema snapshot in Data Catalog                                      | 6 hours (background refresh) | PostgreSQL |
| **L3: Relationship Cache** | Resolved JOIN paths                                                  | 1 hour (invalidated on Schema change) | Redis      |

> Cache invalidation trigger: Data Connector detects Schema change → sends `SchemaChangeEvent` → Query Service receives → invalidates L1/L3 cache → notifies affected Workflow Owners (via FR40 Dependency Manager).

- **Query pushdown SLO**: maximize computation at the data source; only the necessary result set returns to the Compute Engine (see §5.4 for TB-scale guarantees). Sub-project SLOs (NL→Preview P95 ≤ 15s) are owned here — see the [query-serving README](README.md).

## Key Flows

### §5.3.1 Metadata Manager — Schema Discovery & Relationship Declaration

IT administrators use the Metadata Manager to register enterprise data assets into the system.

**Schema Discovery (Automatic Scanning)**:

| Capability               | Mechanism                                                                                            | Output                                                |
| ------------------------ | ---------------------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| **Connection Test**      | Verify connection info and permissions via Data Connector Adapter                                    | `ConnectionStatus { ok, version, features }`          |
| **Schema Scan**          | `INFORMATION_SCHEMA` queries + JDBC `DatabaseMetaData`                                               | Complete table/column listing (types, nullable, defaults) |
| **PK/FK Detection**      | (a) PK/FK declared in DDL → deterministic extraction (b) naming convention inference (c) data distribution inference (column name + cardinality analysis) | `RelationshipCandidate { confidence, evidence }`      |
| **Index Detection**      | Extract existing index information for query optimization                                            | `IndexInfo { columns, type, cardinality }`            |
| **Data Sampling**        | Randomly sample N rows for type inference and data preview                                           | `SampleData { rows, column_stats }`                   |

**Relationship Declaration (IT Manual Configuration)**:

Auto-detected FK/PK relationships have limited confidence (especially across databases, and for legacy systems without DDL constraints). IT can manually declare relationships via Workbench:

```yaml
table_relationships:
  - name: "orders_to_customers"
    left: { data_source: "erp_prod", schema: "public", table: "orders", column: "customer_id" }
    right: { data_source: "crm_prod", schema: "public", table: "accounts", column: "id" }
    join_type: LEFT  # LEFT / INNER / RIGHT
    cardinality: MANY_TO_ONE  # ONE_TO_ONE / ONE_TO_MANY / MANY_TO_ONE / MANY_TO_MANY
    business_rule: "ERP orders.customer_id maps to CRM customer master data id"
    confidence: 1.0  # Manual declaration → highest confidence
    declared_by: "it:zhang-san"
    declared_at: "2026-07-04"
```

These relationships are stored as first-class entities in the KB Data Catalog and linked via `REFERENCES` edges in the Code Graph.

### §5.3.2 Query Generator — 4-step generation flow

When a user requests data via NL or Compute Spec, Query Generator generates optimal SQL:

```
User Intent ("Q3 gross margin by region")
        │
        ▼
┌─────────────────────────────────────────────┐
│ STEP 1: Schema Resolution                          │
│                                              │
│ • KB Retrieval: Look up from Business Glossary │
│   "gross margin" → formula: (revenue-cogs)/revenue │
│   "region" → dimension: region_code           │
│ • Data Catalog: Locate the tables and columns for│
│   revenue, cogs, region_code                  │
│ • Mapping Registry: Check if cross-system       │
│   mapping is needed                            │
│                                              │
│ Output: ResolvedSchema { tables[], cols[],  │
│          mappings[], confidence }            │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│ STEP 2: JOIN Path Selection                  │
│                                              │
│ • Find join paths for target tables from the     │
│   Relationship Graph                              │
│ • When multiple paths exist → select optimal based│
│   on cost estimate:                               │
│   - Path length (JOIN count)                      │
│   - Intermediate table size (cardinality estimate)│
│   - Index availability                            │
│   - JOIN type efficiency (HASH/MERGE/NESTED LOOP) │
│ • If unable to determine automatically → mark     │
│   AMBIGUOUS_JOIN_PATH, fallback to Design Plane   │
│   for user selection                              │
│                                              │
│ Output: JoinPath { path[], estimated_cost,   │
│          alternatives[], ambiguous }          │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│ STEP 3: SQL Generation                        │
│                                              │
│ • Generate ANSI SQL:2003 compliant standard SQL  │
│ • Structure: SELECT [cols] FROM [path]            │
│         WHERE [filters] GROUP BY [dims]           │
│         HAVING [conditions]                       │
│ • Formula Translation: KB formulas → SQL          │
│   expressions                                    │
│   "(revenue - cogs) / revenue"                   │
│   → "SUM(r.revenue - r.cogs) / SUM(r.revenue)"   │
│ • Parameterization: date ranges, filter criteria  │
│   → $1, $2                                       │
│                                              │
│ Output: ParameterizedSQL { sql, params[],    │
│          referenced_tables[], dialect }       │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│ STEP 4: Query Validation                      │
│                                              │
│ • SQL AST validation (syntax correctness)        │
│ • Schema validation (column/table existence)      │
│ • Permission validation (user access to tables    │
│   /columns)                                      │
│ • Performance pre-check (JOIN depth, estimated    │
│   scan rows)                                     │
│                                              │
│ Output: ValidatedSQL with validation_report  │
└─────────────────────────────────────────────┘
```

### §5.3.3 Pushdown Optimizer — decision matrix, policy & plan

Ensures that computation completes at the data source side whenever possible, returning only the necessary result set to the Compute Engine:

**Pushdown Decision Matrix**:

| Operation Type             | Pushdown Strategy       | Condition                                                       | Fallback When Not Pushed Down                         |
| -------------------------- | ----------------------- | --------------------------------------------------------------- | ----------------------------------------------------- |
| **WHERE / Filter**         | Always push down        | Unconditional (simplest optimization)                            | —                                                     |
| **LIMIT / OFFSET**         | Always push down        | —                                                               | —                                                     |
| **GROUP BY / Aggregation** | Always push down        | Aggregation function has native support at data source           | Compute Engine execution (e.g. DuckDB/Spark re-aggregation) |
| **JOIN (same source)**     | Always push down        | JOIN tables are in the same data source instance                 | Compute Engine execution                              |
| **JOIN (cross-source)**    | Conditional push down   | Small tables → broadcast to each data source for local JOIN; large tables → Compute Engine coordination | Compute Engine as federated query engine              |
| **Window Functions**       | Conditional push down   | Data source supports (PG 9.3+, MySQL 8.0+, Snowflake ✓, BigQuery ✓) | Compute Engine execution                              |
| **Python UDF**             | Never push down         | Data source cannot execute Python code                          | Data fetched back and executed by Compute Engine      |
| **ORDER BY**               | Always push down (with index)| Sort column has available index                                | Compute Engine execution (sortable but slower)         |
| **DISTINCT**               | Always push down        | —                                                               | —                                                     |

**Pushdown Validation & Performance Protection**:

```yaml
pushdown_policy:
  max_rows_transferred: 10_000_000    # Max rows transferred per query (exceeded → paginate/sample/reject)
  max_bytes_transferred: 10GB         # Byte-budget guardrail (caps wide-row scans that would pass the row limit; see §6.3 federated-query ≤10GB threshold). Both limits enforced — whichever is hit first triggers fallback.
  assumed_avg_row_width: 1KB          # Reference width for rows↔bytes reconciliation (10M rows × 1KB ≈ 10GB; wide rows exceed bytes-first, narrow rows exceed rows-first)
  max_query_timeout_source: 300s     # Max execution time on data source side
  prefer_source_agg: true             # Prefer aggregation at data source side
  cross_source_join_strategy: auto    # auto | broadcast_small | compute_engine
  fallback_on_pushdown_failure: true  # Auto-fallback to Compute Engine when pushdown fails
```

**Pushdown Plan Visualization**:

Each generated query is accompanied by a Pushdown Plan, showing which operations are completed at the data source and which at the Compute Engine:

```
Query: "Q3 gross margin by region"

┌──────────────────────────────────────────────────────┐
│ DATA SOURCE: erp_prod (PostgreSQL)                   │
│ ✅ WHERE quarter = 'Q3' AND year = 2026              │
│ ✅ GROUP BY region_code                              │
│ ✅ Aggregation: SUM(revenue), SUM(cogs)              │
│ Result: 50 rows × 3 cols (~2KB)                     │
└──────────────────────────────────────────────────────┘
                    │ (50 rows transferred)
                    ▼
┌──────────────────────────────────────────────────────┐
│ COMPUTE ENGINE: Light Engine (DuckDB)                │
│ • Compute: (SUM(revenue) - SUM(cogs)) / SUM(revenue) │
│ • ORDER BY margin_pct DESC                           │
│ Result: 50 rows × 2 cols (~1KB)                     │
└──────────────────────────────────────────────────────┘
```

### Shared runtime sequence

The Query Service read path participates in the end-to-end runtime sequence — in particular, the **Query Rewriter** (which consumes Query Generator output and injects RLS/CLS/masking before the Data Connector Adapter executes) is shown in action under failure in the shared sequence diagram: see [`../_shared/sequence-diagrams.md`](../_shared/sequence-diagrams.md) **§21.2 Runtime Execution with Failure**. The §5.1 resilience patterns (Circuit Breaker, Retry, Timeout Propagation, DLQ) shown above govern the failure handling depicted there.

## Design References

- **Original sections**: §5.1 (Resilience Patterns), §5.2 (Data Classification Tiers), §5.3 (Query Service), §5.3.1 (Metadata Manager), §5.3.2 (Query Generator), §5.3.3 (Pushdown Optimizer), §5.3.4 (Collaboration with Existing Components), §5.3.5 (Query Cache) of [`docs/03-architecture.md`](../../03-architecture.md).
- **Related query-serving doc**: [`large-scale-data.md`](large-scale-data.md) (§5.4 — Partitioning, Incremental, Pre-Aggregation, CBO, Federated strategy that extends pushdown to TB scale).
- **Shared sequence diagram**: [`../_shared/sequence-diagrams.md`](../_shared/sequence-diagrams.md) §21.2 Runtime Execution with Failure (Query Rewriter + Resilience Patterns).
- **ADRs** ([index](../../adr-index.md)): [ADR-0007 Query Service Component](../../../adr/0007-query-service-component.md). See also [ADR-0011 Materialize Job Type](../../../adr/0011-materialize-job-type.md) (pre-aggregation integration with the Query Service read path).
- **Glossary** ([../../glossary.md](../../glossary.md)): Query Service, Metadata Manager, Query Generator, Pushdown Optimizer, Query Rewriter, Compute Engine (Light/Heavy), Data Connector Adapter, Code Graph, Data Classification Tiers.
- **Cross-references retained from source**: §6.3 (federated-query ≤10GB threshold, referenced by `pushdown_policy.max_bytes_transferred`); FR40 (Dependency Manager, referenced by cache invalidation flow).
