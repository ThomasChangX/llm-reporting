# Large-Scale Data Architecture

> **Origin**: §5.4 of [`docs/03-architecture.md`](../../03-architecture.md) | **Sub-project**: [query-serving](README.md)

## Purpose

When data volume reaches TB scale and data sources span multiple heterogeneous systems, **Pushdown alone cannot guarantee performance and functional completeness**. This module designs the large-scale data processing architecture following industry best practices, covering table format selection, partitioning strategy, incremental processing, pre-aggregation, and cost-based optimization.

It extends the Query Service read path (see [`query-service.md`](query-service.md) §5.3, especially the Pushdown Optimizer) with the strategies required to keep queries performant and correct at the 1000-tenant scale:

- **§5.4.1 Industry Best Practice Comparison** — Iceberg/Delta/Hudi, Parquet+ZSTD, CDC+watermark, materialized views, data skipping, CBO, federated query.
- **§5.4.2 Partitioning & Pruning** — partition detection/declaration, partition pruning, partition evolution.
- **§5.4.3 Incremental Processing** — watermark / CDC / partition incremental modes, watermark state store.
- **§5.4.4 Pre-Aggregation & Materialization** — `materialize` Job type, materialization strategy comparison, materialized view dependency graph, automatic MV detection.
- **§5.4.5 Cost-Based Optimization** — table statistics collection, JOIN strategy selection, query plan protection, cost model formula.
- **§5.4.6 Federated Heterogeneous Data Source Strategy** — cross-source JOIN scenarios and the federated query decision tree.

## Boundaries

**In-scope:**
- §5.4.1 Industry Best Practice Comparison table (dimension-by-dimension mapping to this system's design).
- §5.4.2 Partitioning & Pruning — `table_partitioning` declaration (auto-detect or IT), partition pruning mapping user filters → partition columns, file-level data skipping, partition evolution (Iceberg/Delta/RDBMS).
- §5.4.3 Incremental Processing — three incremental modes (Watermark / CDC / Partition), `incremental_config` workflow YAML, Watermark State Store semantics.
- §5.4.4 Pre-Aggregation & Materialization — the `materialize` Job type, strategy comparison (Full / Incremental / Real-Time / Lazy), materialized view dependency graph, automatic MV detection by Query Service.
- §5.4.5 Cost-Based Optimization — table statistics collection, statistics-based JOIN strategy selection, query plan protection thresholds, the cost model formula and default constants.
- §5.4.6 Federated Heterogeneous Data Source Strategy — cross-source scenarios table and the federated query decision tree.

**Delegated / out-of-scope:**
- **Query Service core (Metadata Manager, Query Generator, Pushdown Optimizer, Query Cache)** and **§5.1 Resilience / §5.2 Data Classification** → [`query-service.md`](query-service.md).
- **Workflow / Job execution mechanics** (`source`, `data_writer`, `materialize` Job lifecycle) → [`workflow-engine`](../workflow-engine/).
- **Data Catalog storage** and **Code Graph** persistence → [`knowledge-services`](../knowledge-services/).

**Upstream/downstream neighbors:**
- *Statistics*: Data Connector Adapter (Iceberg manifest / Parquet footer / `pg_stats`) → Metadata Manager collects → Query Generator + Pushdown Optimizer consume for CBO and pruning.
- *Incremental*: `source` Job (`incremental` mode) reads Watermark State Store → advances watermark transactionally with Workflow execution state.
- *Materialization*: `materialize` Job writes to dedicated aggregation tables → Query Service auto-detects and routes NL queries to MVs.
- *Federated*: Pushdown Optimizer + Compute Engine (DuckDB ≤10GB / Spark >10GB) coordinate cross-source JOINs.

## Interfaces

This module does not expose new external endpoints; it configures and tunes the Query Service read path. Its "interfaces" are the configuration artifacts and decision points that govern Query Service behavior at scale.

### §5.4.1 Industry Best Practice Comparison

| Dimension         | Industry Standard                                                                     | This System's Design                                                                                    |
| ----------------- | ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| **Table Format**  | Apache Iceberg / Delta Lake / Hudi                                                    | Native Iceberg/Delta table support via Data Connector; `source` Job can specify `table_format`          |
| **Partitioning**  | Time partitioning (dt=yyyy-mm-dd), hierarchical partitioning (dt/hour), hidden partitioning (Iceberg partition transforms) | Metadata Manager auto-detects partition columns; Query Generator generates partition pruning WHERE clauses |
| **File Format**   | Parquet (columnar, high compression), ORC (Hive ecosystem)                            | `data_export` Format defaults to Parquet + ZSTD compression; Runtime intermediate results as Parquet    |
| **Incremental**   | CDC (Debezium) + watermark + incremental materialization                              | `source` Job supports `incremental` mode; `watermark` column tracks incremental boundary                |
| **Pre-Aggregation** | Materialized views (PG MATERIALIZED VIEW / ClickHouse / StarRocks)                  | New `materialize` Job Type (see below)                                                                   |
| **Data Skipping** | Iceberg metadata (min/max + bloom filter) + Parquet row group stats                   | Pushdown Optimizer leverages file-level stats at Connector layer to skip irrelevant data                |
| **Cost Optimization** | Table statistics (ANALYZE) + CBO (Cost-Based Optimizer)                           | Metadata Manager collects statistics; Query Generator selects JOIN strategy based on statistics         |
| **Federated Query** | Trino / Presto (cross-source JOIN)                                                  | Cross-source JOIN coordinated by Compute Engine (DuckDB/Spark); small table broadcast strategy          |

### §5.4.6 Federated Heterogeneous Data Source Strategy — scenarios

| Scenario                                     | Strategy                          | Data Movement                                          |
| -------------------------------------------- | --------------------------------- | ------------------------------------------------------ |
| **Small dimension table JOIN large fact table** (same source) | Pushdown JOIN                     | No movement needed                                     |
| **Small dimension table JOIN large fact table** (cross-source) | Broadcast dimension to fact engine | Dimension table (<100MB) transferred once              |
| **Large table JOIN large table** (cross-source)   | ETL pre-merge into same engine  | Incremental sync or full export                        |
| **Ad-hoc cross-source query** (low frequency)      | DuckDB/Spark federated query    | On-demand transfer (subject to `max_rows_transferred` limit) |
| **High-frequency cross-source query**              | Build materialized view in single engine | Incremental materialized refresh                      |

## Dependencies

- **Table formats**: Apache Iceberg, Delta Lake (native support via Data Connector); Hudi lineage in the comparison table.
- **File format**: Parquet + ZSTD (default for `data_export` Format and Runtime intermediate results); ORC referenced for the Hive ecosystem.
- **Incremental (§5.4.3)**: Debezium + Kafka → `change_log` table (CDC mode); PostgreSQL `watermark_state` table (watermark persistence); Workflow execution-state transaction.
- **Pre-Aggregation (§5.4.4)**: `materialize` Job type (ADR-0011); `data_writer` to dedicated aggregation tables; Scheduler cron for refresh.
- **CBO (§5.4.5)**: `ANALYZE TABLE ... COMPUTE STATISTICS` (Spark), `pg_stats` / `pg_class.reltuples` (PostgreSQL), Iceberg `snapshot.summary` / `column_stats` / `manifest.metadata`.
- **Federated (§5.4.6)**: Compute Engine — DuckDB (Light Engine, ≤10GB) and Spark (Heavy Engine, >10GB); Observation Engine (suggests future materialization).
- Cross-sub-project: [`query-serving`](README.md) (Query Service read path), [`workflow-engine`](../workflow-engine/) (`source`/`materialize`/`data_writer` Jobs, Scheduler FR39), [`knowledge-services`](../knowledge-services/) (Data Catalog statistics, Code Graph).

## Data Model

- **§5.4.2 `table_partitioning` (YAML)** — Metadata Manager auto-detection or IT declaration: `data_source`, `table`, `partition_columns` (`name`, `transform` such as Iceberg `days(posting_date)` / Delta `DATE_TRUNC('day', ...)`, `granularity`), `partition_stats` (`total_partitions`, `avg_partition_size_mb`, `max_partition_size_mb`), and `file_stats` (`column`, `min_value`, `max_value`, `null_count`, `ndv`).
- **§5.4.3 Incremental modes**:
  - Watermark Incremental — `watermark_column` + `last_executed_watermark`; `SELECT ... WHERE updated_at > :last_watermark`.
  - CDC Incremental — Debezium + Kafka → `change_log` table; consume event stream, MERGE to target.
  - Partition Incremental — process only new partitions after `last_executed_partition`.
- **§5.4.3 `incremental_config` (YAML)** — `strategy` (watermark/cdc/partition), `watermark_column`, `lookback_window`, `late_arrival_policy` (upsert/skip/alert), per-Job `incremental_filter`.
- **§5.4.3 Watermark State Store record** — `watermark_column`, `last_high_watermark`, `last_low_watermark`, `last_execution`, `watermarks_processed`; persisted in PostgreSQL `watermark_state`, committed in the same transaction as Workflow execution state (rollback-safe).
- **§5.4.4 `materialize` Job (YAML)** — `base_query`, `strategy` (full/incremental), `refresh_cron`, `destination` (`type: data_writer`, `target`, `write_mode: upsert`), `retention` (`granularity`, `daily_retention`, `monthly_retention`).
- **§5.4.5 Table statistics** — Row Count, Column NDV, Column Histogram, NULL Ratio, File-Level Stats (each with collection method, update frequency, purpose).
- **§5.4.5 Cost model** — `Total_Cost = Σ(CPU_Cost + IO_Cost + Network_Cost) × Parallelism_Factor`, with cardinality/selectivity formulas and tunable default constants.

## Failure Modes & Recovery

| Failure | Impact | Recovery |
| --- | --- | --- |
| Full re-scan of TB-scale table (no incremental) | Unacceptable runtime / resource blowout | §5.4.3 incremental modes — watermark/CDC/partition incremental avoid full scans; Watermark State Store is rollback-safe (failed run does not advance watermark). |
| Late-arriving data past watermark | Missing rows in incremental result | `lookback_window` (e.g. 3 days) + `late_arrival_policy` (upsert/skip/alert). |
| Stale table statistics → wrong JOIN strategy | Suboptimal / pathological query plan | §5.4.5 staleness detection: `last_analyzed > 24h AND row_count_delta > 20%` → trigger re-collection (ANALYZE/pg_stats/Iceberg manifest). |
| Query plan guardrail breach | Unbounded scan / Cartesian product | §5.4.5 protection thresholds: >100M rows WARN, >10GB WARN, >5-table JOIN WARN, >30min REJECT (Design Plane), no equi-JOIN REJECT. |
| Cross-source federated query exceeds 10GB | Light Engine overload | Federated decision tree: ≤10GB → DuckDB; >10GB → Spark; high-frequency → build materialized view. |
| Partition bloat (traditional RDBMS) | Pruning effectiveness degrades | `pg_partman` auto-management; Metadata Manager monitors partition bloat (§5.4.2). |
| Pushdown guardrail breach | Unbounded transfer | Inherits `pushdown_policy` from [`query-service.md`](query-service.md) §5.3.3 (`max_rows_transferred` / `max_bytes_transferred`). |

## Non-Functional Requirements

- **Scale target**: single tables at TB scale (e.g. `gl_je_lines` 5TB, 1095 daily partitions); 1000-tenant platform.
- **Partition pruning effectiveness**: example case reduces 1095 partitions → 92 (Q3) → ~30% of files → ~1.4GB scanned vs ~50GB full table.
- **Incremental freshness**: Watermark Incremental T+run; CDC Incremental near-real-time via Debezium+Kafka; Partition Incremental on new-partition arrival.
- **Materialization freshness** (§5.4.4 strategy table): Full Refresh T+1; Incremental Refresh T+10min; Real-Time MV T+1min; Lazy Materialization slow-first-then-instant.
- **CBO statistics cadence**: Row Count every 6h or >10% data change; Column NDV / NULL Ratio every 24h; Column Histogram weekly; File-Level Stats auto on write.
- **Query plan protection thresholds**: scan >100M rows WARN; scan >10GB WARN; JOIN depth >5 WARN; estimated time >30min REJECT (Design Plane); Cartesian product REJECT.
- **Cost model default constants** (tunable per deployment): `cpu_tuple_cost=0.01ms`, `seq_page_cost=0.001ms` (8KB page), `random_page_cost=0.004ms`, `network_transfer_cost=0.0001ms/KB` (intra-region), `cross_region_penalty=5.0×`, `complexity_factor` 1.0/2.0/3.0/5.0 for filter/aggregate/window/UDF.
- **Federated transfer budget**: ≤10GB → DuckDB (Light Engine); >10GB → Spark (Heavy Engine); subject to `max_rows_transferred` (see [`query-service.md`](query-service.md) §5.3.3).

## Key Flows

### §5.4.2 Partitioning & Pruning

When a single table reaches TB scale, partitioning is the foundation for ensuring query performance.

**Partition Detection & Declaration**:

```yaml
# Metadata Manager auto-detection or IT declaration
table_partitioning:
  - data_source: "erp_prod"
    table: "gl_je_lines"
    partition_columns:
      - name: "posting_date"
        transform: "day"        # Iceberg: days(posting_date) | Delta: DATE_TRUNC('day', posting_date)
        granularity: "daily"
    partition_stats:
      total_partitions: 1095    # 3 years of daily partitions
      avg_partition_size_mb: 50
      max_partition_size_mb: 200
    file_stats:                  # File-level statistics (extracted from Iceberg metadata / Parquet footer)
      - column: "amount"
        min_value: -1000000.00
        max_value: 50000000.00
        null_count: 1247
        ndv: 3420000             # Number of Distinct Values
```

**Partition Pruning**:

Query Generator automatically maps user filter conditions to partition columns:

```
User Query: "2026 Q3 Revenue" → WHERE posting_date BETWEEN '2026-07-01' AND '2026-09-30'
                                          ↓
Pushdown Optimizer: Identifies posting_date as a partition column
                                          ↓
Scan Range: 1095 partitions → only 92 partitions (Q3 = 92 days)
Data Skipping: Use file_stats.amount.min/max to filter out files not containing the target amount range
                                          ↓
Actual Scan: Only ~30% of files within 92 partitions → ~1.4GB data (vs full table ~50GB)
```

**Partition Evolution Support**:
- Iceberg: supports `ALTER TABLE ... ADD PARTITION FIELD` (online operation, no data rewrite)
- Delta Lake: `ALTER TABLE ... ADD PARTITION` (requires rewriting new data to include new partition column)
- Traditional RDBMS: auto-managed via `pg_partman`; Metadata Manager monitors partition bloat

### §5.4.3 Incremental Processing

Full re-runs of TB-scale tables are unacceptable. The system avoids full scans through three incremental modes:

| Incremental Mode           | Trigger Mechanism                              | Applicable Scenario                       | Implementation                                   |
| -------------------------- | ---------------------------------------------- | ----------------------------------------- | ------------------------------------------------ |
| **Watermark Incremental**  | `watermark_column` + `last_executed_watermark` | Fact tables (append by time)              | `SELECT ... WHERE updated_at > :last_watermark`  |
| **CDC Incremental**        | Debezium + Kafka → `change_log` table          | Transaction tables (frequent UPDATE/DELETE) | Consume CDC event stream, MERGE to target        |
| **Partition Incremental**  | Process only new partitions                    | Immutable partitioned tables (logs/events) | Scan new partitions after `last_executed_partition` |

**Incremental Workflow Configuration Example**:

```yaml
workflow:
  name: "daily_revenue_incremental"
  incremental_config:
    strategy: watermark
    watermark_column: "posting_date"
    lookback_window: "3 days"       # Allow 3 days of late data catch-up
    late_arrival_policy: upsert     # upsert | skip | alert
  jobs:
    - id: "source_revenue"
      type: source
      incremental_filter: "posting_date BETWEEN :watermark_start AND :watermark_end"
```

**Watermark Management**:

```
┌─────────────────────────────────────────────────────┐
│              WATERMARK STATE STORE                   │
│                                                      │
│  Workflow: "daily_revenue_incremental"               │
│  ┌────────────────────────────────────────────────┐ │
│  │ watermark_column: posting_date                  │ │
│  │ last_high_watermark: 2026-07-04T06:00:00Z     │ │
│  │ last_low_watermark: 2026-07-04T00:00:00Z      │ │
│  │ last_execution: 2026-07-04T02:15:00Z            │ │
│  │ watermarks_processed: 182 (successful sequences)│ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  State Persistence: PostgreSQL `watermark_state` table     │
│  Transactional Update: Committed in the same transaction   │
│  as Workflow execution state                                │
│  Rollback Safe: Execution failure → watermark not rolled   │
│  back → next run starts from last successful point          │
└─────────────────────────────────────────────────────┘
```

### §5.4.4 Pre-Aggregation & Materialization

Aggregation results for frequently-queried data should be pre-computed to avoid scanning TB-scale detail data every time.

**Materialized View Job Type** (New):

```yaml
jobs:
  - id: "mat_revenue_daily"
    type: materialize           # New Job Type: materialized aggregation
    materialize:
      base_query: |
        SELECT posting_date,
               region_code,
               SUM(revenue) as total_revenue,
               SUM(cogs) as total_cogs,
               COUNT(DISTINCT order_id) as order_count
        FROM erp_prod.gl_je_lines
        WHERE posting_date >= :watermark_start
        GROUP BY posting_date, region_code
      strategy: incremental      # full | incremental
      refresh_cron: "0 6 * * *" # Execute incremental refresh every day at 6 AM
      destination:
        type: data_writer
        target: "reporting.revenue_daily_agg"  # Write to dedicated aggregation table
        write_mode: upsert
      retention:
        granularity: "monthly"   # Monthly granularity → retain only monthly summaries
        daily_retention: "90 days"
        monthly_retention: "36 months"
```

**Materialization Strategy Comparison**:

| Strategy | Refresh Method | Applicable Scenario | Data Freshness | Compute Cost |
| ------------------------ | ------------------------- | -------------- | ---------------- | -------- |
| **Full Refresh** | Full recompute | Dimension tables (<1M rows) | T+1 | High |
| **Incremental Refresh** | Process only incremental partitions | Fact tables (TB scale) | T+10min | Low |
| **Real-Time MV** | Per micro-batch | Real-time Dashboard | T+1min | Medium |
| **Lazy Materialization** | Create on first query + scheduled refresh | Low-frequency ad-hoc queries | Slow first, instant thereafter | Low |

**Materialized View Dependency Graph**:

```
Source: gl_je_lines (5TB, daily partitions)
    │
    ├──→ mat_revenue_daily (50MB/day) ──→ mat_revenue_monthly (100MB/month)
    │                                         │
    │                                         └──→ Report: "Monthly Revenue Trend"
    │
    ├──→ mat_revenue_by_region (20MB/day) ──→ Dashboard: "Regional Revenue KPI"
    │
    └──→ mat_margin_analysis (30MB/day) ──→ Report: "Gross Margin Analysis"
```

When resolving NL queries, Query Service **automatically detects available materialized views**: if `mat_revenue_monthly` already contains all columns and aggregation levels needed for the query → directly query the materialized view (skip detail table scan).

### §5.4.5 Cost-Based Optimization

When queries involve multi-table JOINs or TB-scale aggregation, statistics-based cost optimization is critical.

**Table Statistics Collection**:

| Statistic | Collection Method | Update Frequency | Purpose |
| -------------- | ------------------------------------------------------------------------------- | --------------------- | ---------------- |
| **Row Count** | `SELECT reltuples FROM pg_class` / Iceberg `snapshot.summary['total-records']` | Every 6h or when data change >10% | Estimate scan cost |
| **Column NDV** | `SELECT approx_count_distinct(col)` / Iceberg `column_stats` | Every 24h | JOIN cardinality estimation |
| **Column Histogram** | `ANALYZE TABLE ... COMPUTE STATISTICS` (Spark) / PG `pg_stats.histogram_bounds` | Weekly | Range query selectivity |
| **NULL Ratio** | `SELECT count(*) WHERE col IS NULL / count(*)` | Every 24h | IS NULL filter estimation |
| **File-Level Stats** | Iceberg `manifest.metadata` min/max/null_count | Auto on write | Data skipping |

**JOIN Strategy Selection** (based on statistics):

```
Query Generator:
  LEFT: orders (1B rows, 2TB)  RIGHT: customers (10M rows, 500MB)

  Statistics: orders.customer_id NDV = 8M, customers.id NDV = 10M
  JOIN cardinality estimate: ~1B rows (each order row matches a customer)

  Strategy Evaluation:
  ┌──────────────────────────────────────────────────────────┐
  │ Strategy 1: Broadcast JOIN (customers → orders)          │
  │   Cost: Serialize 500MB + network transfer + distribute to Spark workers   │
  │   Estimated: ~30s                                        │
  │                                                          │
  │ Strategy 2: Shuffle Hash JOIN (both sides shuffle)       │
  │   Cost: Shuffle 2TB (orders) + 500MB (customers)         │
  │   Estimated: ~180s                                       │
  │                                                          │
│ Strategy 3: Pushdown JOIN (orders + customers same source)
│   Cost: Complete JOIN on PostgreSQL side, return aggregated result
│   Estimated: ~45s (but requires sufficient source DB resources)
  │                                                          │
  │ **Selected:** Strategy 1 (small table broadcast) + Strategy 3 (same-source pushdown)
  └──────────────────────────────────────────────────────────┘
```

**Query Plan Protection Mechanisms**:

| Protection Item                | Threshold              | Overrun Handling                                                      |
| ------------------------------ | ---------------------- | --------------------------------------------------------------------- |
| **Estimated Scan Rows**        | > 100M rows            | [WARN] + suggest adding filter conditions or using materialized view |
| **Estimated Scan Data Volume** | > 10GB                 | [WARN] + suggest using sampling or incremental processing          |
| **JOIN Depth**                 | > 5 tables             | [WARN] + suggest splitting into multiple steps or using materialized intermediate tables |
| **Estimated Execution Time**   | > 30min                | [REJECT] Design Plane preview execution (only allow Runtime Plane execution) |
| **Cartesian Product Detection**| No equi-JOIN condition | [REJECT] execution (almost certainly a query error or missing Schema relationship) |

**Cost Model Formula** (referencing PostgreSQL Cost Model + Spark CBO):

```
Total_Cost = Σ(CPU_Cost + IO_Cost + Network_Cost) × Parallelism_Factor

Where:
  CPU_Cost    = Cardinality × cpu_tuple_cost × (1 + complexity_factor)
  IO_Cost     = Pages_Read × seq_page_cost + Pages_Write × random_page_cost
  Network_Cost = Bytes_Shuffled × network_transfer_cost × (1 + cross_region_penalty)

  Cardinality  = |R| × selectivity × (1 - null_fraction) × (1 / NDV_factor)
  Selectivity  = 1/NDV for equality, histogram_range for range, 0.1 for LIKE

Default Constants (tunable per deployment):
  cpu_tuple_cost          = 0.01ms
  seq_page_cost           = 0.001ms (8KB page)
  random_page_cost        = 0.004ms
  network_transfer_cost   = 0.0001ms/KB (intra-region)
  cross_region_penalty    = 5.0× (for federated cross-region queries)
  complexity_factor       = 1.0 (filter) / 2.0 (aggregate) / 3.0 (window) / 5.0 (UDF)
```

**Statistics Collection Implementation**: Metadata Manager periodically collects (ANALYZE TABLE ... COMPUTE STATISTICS on Spark, pg_stats on PostgreSQL). Iceberg/Delta Lake manifest files provide file-level Min-Max. Statistics staleness detection: last_analyzed > 24h AND row_count_delta > 20% → trigger re-collection.

### §5.4.6 Federated Heterogeneous Data Source Strategy

When data is distributed across different types of data sources (OLTP PG + OLAP ClickHouse + Data Lake S3):

(See the federated scenarios table under [Interfaces](#interfaces) above.)

**Query Service Federated Query Decision Tree**:

```
Query involves Table A (PG), Table B (S3/Parquet), Table C (Snowflake)
        │
        ├── Do Table A and Table B frequently JOIN?
        │     YES → Suggest IT incrementally export Table A to S3 (materialized Parquet copy)
        │     NO  → Small table broadcast strategy (choose after cost estimation)
        │
        ├── Is there already a materialized view covering this query?
        │     YES → Use materialized view directly (zero cross-source overhead)
        │
        └── No materialized view + first-time query
              → DuckDB (Light Engine) federated query (≤10GB transfer)
              → Spark (Heavy Engine) federated query (>10GB transfer)
              → Record query pattern → Observation Engine suggests materialization in the future
```

## Design References

- **Original section**: §5.4 (Large-Scale Data Architecture), §5.4.1–§5.4.6 of [`docs/03-architecture.md`](../../03-architecture.md).
- **Related query-serving doc**: [`query-service.md`](query-service.md) (§5.3 Query Service — Metadata Manager, Query Generator, Pushdown Optimizer whose `pushdown_policy` and decision matrix this module extends to TB scale; §5.1 Resilience, §5.2 Data Classification).
- **Shared sequence diagram**: [`../_shared/sequence-diagrams.md`](../_shared/sequence-diagrams.md) §21.2 Runtime Execution with Failure (the runtime read path these strategies optimize).
- **ADRs** ([index](../../adr-index.md)): [ADR-0008 Large-Scale Data Strategy](../../../adr/0008-large-scale-data-strategy.md), [ADR-0011 Materialize Job Type](../../../adr/0011-materialize-job-type.md) (the `materialize` Job type introduced in §5.4.4).
- **Glossary** ([../../glossary.md](../../glossary.md)): Large-Scale Data Architecture, Partition Pruning, Incremental Processing, Materialized View, Cost-Based Optimization (CBO), Federated Query, Iceberg/Delta Lake, Watermark, NDV, Compute Engine (Light/Heavy).
- **Cross-references retained from source**: §6.3 (federated-query ≤10GB threshold, mirrored in the federated decision tree and inherited `pushdown_policy.max_bytes_transferred`).
