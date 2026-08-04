# CDC Pipeline — Change Data Capture

> **Origin**: §20 of [`docs/03-architecture.md`](../../03-architecture.md) | **Sub-project**: [knowledge-services](README.md)

## Purpose

The CDC (Change Data Capture) Pipeline is the mechanism that keeps the knowledge-services derived stores — the Vector DB (Milvus), the Graph DB (Neo4j), and the cache (Redis) — consistent with PostgreSQL, the system's source of truth. It expands on the CDC mechanism referenced in §10.1 Consistency Model of the parent architecture document, providing a complete technical solution built on Debezium and Kafka Connect.

Every write committed to PostgreSQL for the knowledge-base tables (`kb_entry`, `workflow`, `job`, `data_source`, `kb_entry_relation`) is captured from the WAL, published as a structured change event to Apache Kafka (Redpanda), and fanned out to N independent sink connectors. Each sink applies a target-specific transformation (text→embed→upsert for Milvus, row→node/edge for Neo4j, key extraction→DEL for Redis) so that semantic search, lineage / impact-analysis queries, and cached reads always reflect the latest relational state.

## Boundaries

**In scope**

- Reading the PostgreSQL WAL via a logical replication slot (`pgoutput` plugin).
- Emitting Debezium change events (CDC records) with Avro serialization through Schema Registry.
- Per-table Kafka topics partitioned by row primary key for per-entity ordering.
- Three sink categories:
  - **Vector DB Sink** — `kb_entry` → Milvus collection `kb_embeddings` (see §20.3.1).
  - **Graph DB Sink** — `workflow`, `job`, `kb_entry`, `data_source` → Neo4j Code Graph + KB subgraph (see §20.3.2).
  - **Cache Invalidation Sink** — key extraction → `DEL` against Redis Sentinel.
- Initial population / backfill of Milvus and Neo4j from the relational DB via Debezium initial snapshot mode (see §20.5).
- Lag monitoring, retry, and Dead Letter Queue (DLQ) handling per sink.
- Failure detection and recovery for Kafka brokers, the Debezium connector, sink JVMs, and target DBs (see §20.4).

**Out of scope**

- Embedding computation itself — the `content_vector` is produced by a PostgreSQL-side trigger (`text-embedding-ada-002`) *before* the CDC event is emitted; the Vector Sink only passes the precomputed vector through (see §20.3.1 step 2b).
- The Kafka / Redpanda cluster's internal operation — it is shared infrastructure also required for the internal Event Bus (§15.2) and is not provisioned by this pipeline.
- Consumer-facing query semantics against Milvus / Neo4j / Redis — those belong to the Retrieval and Code Graph service modules.
- Source-of-truth schema design for `kb_entry`, `workflow`, etc. — owned by the relational model.

## Interfaces

**Upstream (inputs)**

- **PostgreSQL WAL** — consumed through a logical replication slot using the `pgoutput` plugin. Publication is `FOR ALL TABLES`, filtered per target by the sink connectors.
- **Debezium Source Connector** — runs inside Kafka Connect; reads WAL → Debezium Change Events; integrates with Schema Registry for Avro serialization; snapshot mode `initial` is used for backfill.

**Internal topics (Apache Kafka / Redpanda)**

- Per-table topics, partitioned by row primary key for ordering:
  - `cdc.public.kb_entry`
  - `cdc.public.workflow`
  - `cdc.public.data_source`
  - `cdc.public.kb_entry_relation`
- Dead Letter Queues (per sink):
  - `cdc.dlq.vector`
  - `cdc.dlq.graph`

**Downstream (sinks / outputs)**

- **Vector DB Sink → Milvus** — upserts/deletes on collection `kb_embeddings`, partitioned by `tenant_id`.
- **Graph DB Sink → Neo4j** — node and edge merges/deletes on the Code Graph + KB subgraph.
- **Cache Invalidation Sink → Redis Sentinel** — `DEL` of derived cache keys.

**Operational interfaces**

- Kafka Connect REST API, e.g. `GET /connectors/pg-connector/status`, `POST /connectors/pg-connector/restart`, `POST /connectors/{name}/pause`.
- JMX metrics from Kafka brokers and Connect, scraped by Prometheus (lag, throughput, error rates, JVM heap).
- Audit Trail — backfill consistency reports and recovery actions are logged here.

**Architecture diagram (§20.1)**

```
 ┌─────────────────────┐
 │ PostgreSQL (Source  │
 │ of Truth)           │
 │ ┌─────────────────┐ │
 │ │ WAL (Write-Ahead │ │
 │ │      Log)        │ │
 │ └────────┬────────┘ │
 └──────────┼──────────┘
           │ Logical Replication Slot (pgoutput plugin)
           ▼
 ┌──────────────────────────────────────────────────────────┐
 │              Debezium Connector (Kafka Connect)            │
 │  ┌───────────────────────────────────────────────────────┐│
 │  │ • PostgreSQL Source Connector                          ││
 │  │ • Reads WAL → Debezium Change Events (CDC Record)     ││
 │  │ • Schema Registry integration for Avro serialization  ││
 │  │ • Snapshot mode: initial (for backfill)               ││
 │  │ • Publication: FOR ALL TABLES (filtered per target)   ││
 │  └───────────────────────┬───────────────────────────────┘│
 └──────────────────────────┼────────────────────────────────┘
                           │
                           ▼
 ┌──────────────────────────────────────────────────────────┐
 │                  Apache Kafka (Redpanda)                    │
 │  ┌───────────────────────────────────────────────────────┐│
 │  │ Topic: cdc.public.kb_entry                             ││
 │  │ Topic: cdc.public.workflow                              ││
 │  │ Topic: cdc.public.data_source                          ││
 │  │ Topic: cdc.public.kb_entry_relation                    ││
 │  │ (per-table topics; partition by row PK for ordering)   ││
 │  └───────────────────────┬───────────────────────────────┘│
 └──────────────────────────┼────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
 ┌─────────────────┐ ┌──────────────┐ ┌──────────────────┐
 │ Vector DB Sink   │ │Graph DB Sink │ │ Cache Invalidation│
 │ (Milvus)         │ │(Neo4j)       │ │ (Redis)          │
 │                  │ │              │ │                   │
 │ Transform:       │ │Transform:    │ │ Transform:        │
 │ text→embed→upsert│ │row→node/edge │ │ key extraction    │
 │                  │ │              │ │ → DEL key         │
 └────────┬─────────┘ └──────┬───────┘ └────────┬──────────┘
         │                  │                   │
         ▼                  ▼                   ▼
  [Milvus Cluster]   [Neo4j Cluster]    [Redis Sentinel]
```

## Dependencies

- **PostgreSQL** — source of truth; must run with `wal_level=logical` and a `pgoutput` publication `FOR ALL TABLES`. A PG-side trigger precomputes `content_vector` so the Vector Sink does not re-embed.
- **Apache Kafka / Redpanda** — durable CDC event buffer; the same cluster used by the internal Event Bus (§15.2), so no additional infrastructure is introduced.
- **Kafka Connect + Strimzi operator** — runtime for the Debezium source connector and the sink connectors; battle-tested at scale (Netflix, Uber, Zendesk).
- **Schema Registry** — Avro schema evolution with backward/forward compatibility enforcement.
- **Debezium PostgreSQL Source Connector** — WAL reader; `snapshot.mode=initial` for backfill.
- **Milvus** — Vector DB target (collection `kb_embeddings`).
- **Neo4j** — Graph DB target (Code Graph + KB subgraph).
- **Redis Sentinel** — cache invalidation target.
- **Prometheus** — scrapes JMX metrics for lag, throughput, error rates, and JVM heap.
- **KB Governance dashboard / incident management** — consumer of lag alerts (warning / P3 / P2 / P1).

### Technology justification — Debezium + Kafka Connect vs. PG Logical Replication Directly (§20.2)

| Criterion                  | Debezium + Kafka Connect                                                                                                                                                                                           | PG Logical Replication Direct (pgoutput → custom consumer)                                            |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------- |
| **Operational Maturity**   | Battle-tested at scale (Netflix, Uber, Zendesk); Kubernetes operator available (Strimzi)                                                                                                                         | Requires custom consumer logic; fewer production references for multi-target sync                   |
| **Multi-Target Fan-out**   | Kafka topic consumed by N independent sink connectors; backpressure managed per consumer group                                                                                                                   | Single replication slot → single consumer; fan-out requires custom fan-out broker (adds complexity) |
| **Schema Evolution**       | Avro + Schema Registry; backward/forward compatibility enforced; schema evolution tracked                                                                                                                        | Manual schema mapping; breaking changes can crash consumer silently                                 |
| **Fault Recovery**         | Kafka acts as durable buffer; connector restarts replay from last committed offset                                                                                                                               | Replication slot advance is manual; crash risks slot bloat and WAL accumulation                     |
| **Monitoring**             | JMX metrics + Prometheus exporter; lag, throughput, error rates out-of-box                                                                                                                                       | Must be built from scratch                                                                          |
| **Initial Snapshot**       | Built-in snapshot mode with lock coordination                                                                                                                                                                    | Manual pg_dump + re-import script                                                                   |
| **Operational Complexity** | Medium (Kafka + Connect cluster to manage)                                                                                                                                                                       | Low (single consumer), but fragile at scale                                                           |
| **Decision**               | **Debezium + Kafka Connect selected** for resilience, multi-target fan-out, and schema evolution support. Kafka cluster is already required for the internal Event Bus (§15.2), so no additional infrastructure. | —                                                                                                     |

## Data Model

This pipeline does not own a persistent data model; it transforms relational rows into derived-store entities. The shape of the data is defined by the per-target transformation logic below.

### CDC event envelope (Debezium)

```
CDC Event { op: "c|u|d", before: {...}, after: {...} }
```

- `op` — `c` create / `u` update / `d` delete.
- `before` / `after` — row state before and after the change (delete carries only `before`).
- Serialized as Avro via Schema Registry; topic name follows `cdc.public.<table>`, partitioned by row primary key to guarantee per-entity ordering.

### §20.3.1 Vector DB Sink (`kb_entry` → Milvus)

```
Input: CDC Event { op: "c|u|d", before: {...}, after: {...} }
Source Table: kb_entry
Target Collection: kb_embeddings (Milvus)

Transformation:
  1. Filter: only rows WHERE domain IN ('business_glossary','data_catalog','mapping_registry')
     AND status = 'confirmed' AND content_vector IS NOT NULL
  2. On INSERT (op='c') or UPDATE (op='u'):
     a. Extract: id, title, content, domain, tags, tenant_id
     b. Embedding: content_vector already computed by PG-side trigger (text-embedding-ada-002)
        → no re-embed needed at sink side; vector passed as field in CDC event
     c. Milvus Upsert: collection="kb_embeddings", partition=tenant_id
        Fields: {id, title, content (text), domain, tags, vector}
  3. On DELETE (op='d'):
     a. Milvus Delete: by primary key id

Lag Monitoring:
  - Metric: cdc_vector_lag_seconds (prometheus gauge)
  - Calculation: now() - max(event_ts) from last committed offset
  - Alert: >60s lag → KB Governance dashboard warning; >300s → P3 incident

Retry Strategy:
  - Transient (Milvus timeout, network): Exponential backoff 1s→2s→4s→8s, max 5 retries
  - Persistent (schema mismatch, auth failure): Dead Letter Queue topic: cdc.dlq.vector
    DLQ consumer alerts → P2 incident within 5 minutes
```

**Fields landed in Milvus collection `kb_embeddings`:** `id`, `title`, `content` (text), `domain`, `tags`, `vector` — partitioned by `tenant_id`.

### §20.3.2 Graph DB Sink (`workflow`, `job`, `kb_entry`, `data_source` → Neo4j)

```
Input: CDC Events from multiple topics
Source Tables: workflow, job, kb_entry, data_source
Target: Neo4j Graph (Code Graph + KB subgraph)

Transformation (per table):

  workflow event:
    INSERT → MERGE (w:Workflow {id, name, type, status, tenant_id})
    UPDATE → MATCH (w:Workflow {id}) SET w += {changed_fields}
    DELETE → DETACH DELETE (w:Workflow {id})  -- removes all related edges

  job event:
    INSERT → MERGE (j:Job {id, name, type, workflow_id, config})
            + MATCH (w:Workflow {id: workflow_id})
              MERGE (w)-[:CONTAINS]->(j)
            + For each dep_id in dependencies:
              MATCH (dep:Job {id: dep_id})
              MERGE (j)-[:DEPENDS_ON]->(dep)

  kb_entry event:
    INSERT + domain='mapping_registry':
      MERGE (kb:KBEntry {id, title, domain})
      + Parse metadata->>'mappings' JSON array:
        For each mapping {from_ds, from_col, to_ds, to_col}:
          MATCH (src:DataSource {name: from_ds})
          MATCH (tgt:DataSource {name: to_ds})
          MERGE (src)-[:MAPS_TO {from_col, to_col}]->(tgt)

  data_source event:
    INSERT → MERGE (ds:DataSource {id, name, type, tenant_id})
    UPDATE → SET += changed_fields
    DELETE → DETACH DELETE

Lag Monitoring:
  - Per-table lag: cdc_graph_lag_seconds{table="workflow|job|kb_entry|data_source"}
  - Alert: >60s → warning; >300s → P3 incident

Retry Strategy:
  - All writes in a single transaction (per event batch) for consistency
  - Transient: retry 3x with 2s backoff
  - Persistent: DLQ topic cdc.dlq.graph
  - IMPORTANT: Ordering within same entity ID must be preserved
    → Partition Kafka topic by entity PK to guarantee order
```

**Idempotency Guarantee**: The Graph DB Sink uses Neo4j `MERGE` instead of `CREATE`, ensuring CDC event replay does not produce duplicate nodes. The Vector DB Sink uses Milvus upsert (key-based insert-or-update, analogous to a document-store upsert rather than a SQL MERGE), which is natively idempotent.

## Failure Modes & Recovery

From §20.4 — the canonical failure-mode matrix for this pipeline.

| Failure Mode                         | Detection                                                                       | Impact                                                                              | Recovery Procedure                                                                                                                                                                                                                                                                                                   |
| ------------------------------------ | ------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Kafka Broker Down** (1 of 3)       | Kafka JMX `kafka.server:type=ReplicaManager,name=UnderReplicatedPartitions > 0` | No impact (RF=3, minISR=2): producer and consumer continue on remaining brokers     | (1) Alert to Platform team automatically. (2) Investigate broker logs. (3) If broker unrecoverable, decommission and add replacement node → Kafka rebalances. (4) If 2 of 3 down, Kafka unavailable: CDC events buffer in WAL (PG replication slot holds). Slot monitored for bloat — if >10GB, alert P1.            |
| **Kafka Broker Down** (2 of 3)       | Same as above; minISR violated if 2 down                                        | Producers blocked (minISR=2 not met) → WAL accumulation on PG side                  | (1) P1 Incident auto-created. (2) Immediate restore of at least 1 broker. (3) If >30min, temporarily reduce minISR to 1 (risk accepted, documented). (4) PG replication slot monitoring: if slot LSN lag exceeds 5GB, consider pausing non-critical Debezium connectors to reduce WAL pressure.                      |
| **Debezium Connector Crash**         | Kafka Connect REST API: `GET /connectors/pg-connector/status` → `state: FAILED` | No new CDC events published; PG WAL accumulates                                     | (1) Kafka Connect auto-restarts the connector (config: `restart.on.failure.enable=true`). (2) On persistent failure (>3 restarts in 5min): P2 incident. (3) Manual recovery: `POST /connectors/pg-connector/restart`. (4) Last committed offset preserved in Kafka — catch-up replays from offset; no data loss.     |
| **Transformation OOM**               | Sink connector JVM heap usage >90% → GC thrashing → processing lag spikes       | That sink only (Vector or Graph); other sinks unaffected (consumer group isolation) | (1) Auto-detected by Prometheus: `jvm_memory_used_bytes{area="heap"} / jvm_memory_max_bytes > 0.9`. (2) Connector auto-pauses via `/connectors/{name}/pause`. (3) P2 incident. (4) Recovery: increase `task.max` for parallelism, increase heap (`-Xmx`), or implement batch size cap. Reprocess from last offset.   |
| **Target DB Write Failure** (Milvus) | Milvus SDK returning gRPC UNAVAILABLE or DEADLINE_EXCEEDED                      | Vector index stale; KB semantic search degraded per Graceful Degradation (§5.1)     | (1) Retry with backoff (Section 20.3.1). (2) After retries exhausted → DLQ. (3) Graceful Degradation activates: KB Retrieval falls back to keyword-only (§5.1). (4) Recovery: resolve Milvus issue → drain DLQ (replay messages in order). (5) If DLQ depth >1000, trigger backfill instead of drain (Section 20.5). |
| **Target DB Write Failure** (Neo4j)  | Neo4j Bolt driver throwing TransientException or SessionExpired                 | Graph stale; impact analysis and lineage queries return incomplete results          | (1) Retry 3x. (2) DLQ. (3) Code Graph queries served from last-good snapshot; warning banner in Workbench. (4) Recovery: resolve Neo4j → drain DLQ. (5) Consistency check: compare node counts between PG and Neo4j; if discrepancy >1%, trigger selective backfill.                                                 |

## Non-Functional Requirements

**Reliability / durability**

- Kafka replication factor `RF=3`, `minISR=2` — tolerates one broker loss with no impact, two brokers loss blocks producers but PG WAL buffers the events.
- Kafka offsets are the source of progress: connector restarts replay from the last committed offset (no data loss).
- All sinks are idempotent — Vector via Milvus upsert, Graph via Neo4j `MERGE` — so event replay is safe.
- Per-entity ordering is guaranteed by partitioning Kafka topics on the row primary key.
- Graph DB writes are committed as a single transaction per event batch for consistency.

**Performance / freshness (lag SLAs)**

- Vector Sink: `cdc_vector_lag_seconds` — warning at >60s, P3 incident at >300s.
- Graph Sink: `cdc_graph_lag_seconds{table=...}` — warning at >60s, P3 incident at >300s.
- Backfill throughput baseline (per 1M rows): PG→Kafka snapshot ~5–10 min; Kafka→Milvus upsert ~15–20 min (embedding pre-computed in PG); Kafka→Neo4j node+edge creation ~10–15 min; total ~30–45 min per 1M rows.

**Observability**

- JMX metrics + Prometheus exporter: lag, throughput, error rates out-of-box for Kafka, Connect, and sinks.
- JVM heap monitor: auto-pause sink when `jvm_memory_used_bytes{area="heap"} / jvm_memory_max_bytes > 0.9`.
- DLQ depth thresholds drive operational response (e.g. DLQ depth >1000 triggers backfill rather than drain).

**Capacity / backfill**

- Kafka topics provisioned with 7-day retention during the backfill window.
- Milvus / Neo4j provisioned for the full dataset before backfill begins.
- PostgreSQL replication slot monitored for bloat (alert P1 if >10GB; consider pausing non-critical connectors if slot LSN lag >5GB).

## Key Flows

### Steady-state CDC flow

1. Application commits a write to PostgreSQL for `kb_entry` / `workflow` / `job` / `data_source` / `kb_entry_relation`.
2. The row change lands in the WAL; a PG-side trigger precomputes `content_vector` for `kb_entry` where applicable.
3. The Debezium PostgreSQL Source Connector reads the WAL via the logical replication slot (`pgoutput`) and emits a Debezium change event (`op` = `c`/`u`/`d`, with `before`/`after`).
4. The event is Avro-serialized through Schema Registry and published to the per-table topic `cdc.public.<table>`, partitioned by row primary key.
5. Each sink consumes independently from its own consumer group and applies its transformation (see §20.3.1 Vector DB Sink, §20.3.2 Graph DB Sink, and Redis key-extraction → `DEL`).
6. Transient failures are retried (Vector: exponential backoff 1s→2s→4s→8s, max 5; Graph: 3x with 2s backoff). Persistent failures route to the per-sink DLQ (`cdc.dlq.vector`, `cdc.dlq.graph`).
7. Lag metrics are exported to Prometheus and surfaced against the 60s / 300s SLA thresholds.

### Backfill flow — Initial Population from Relational DB to Vector/Graph (§20.5)

```
Phase 0: PREPARATION
  - Identify all tables to be backfilled: kb_entry, workflow, job, data_source
  - Estimate row counts (query pg_stat_user_tables)
  - Provision Milvus/Neo4j with capacity for full dataset
  - Create Kafka topics with appropriate retention (7 days for backfill window)

Phase 1: FULL SNAPSHOT (Debezium Initial Snapshot Mode)
  - Debezium connector configured with snapshot.mode=initial
  - Connector acquires a SHARE UPDATE EXCLUSIVE lock briefly to establish
    a consistent point, then releases lock
  - All existing rows streamed as CDC INSERT events to Kafka
  - Sink connectors process these as normal INSERTs

Phase 2: INCREMENTAL CATCH-UP
  - After snapshot completes, connector automatically transitions to
    streaming mode (WAL tailing)
  - Any changes during snapshot are captured and applied in order
  - Sink connectors reach steady state

Phase 3: VERIFICATION
  - Row count reconciliation per table:
    Vector: SELECT COUNT(*) FROM kb_entry WHERE domain IN (...) AND status='confirmed'
           vs Milvus: num_entities('kb_embeddings')
    Graph:  SELECT COUNT(*) FROM workflow vs MATCH (w:Workflow) RETURN count(w)
  - Sampling: pick 100 random IDs, verify all fields match
  - Consistency report auto-generated and logged to Audit Trail

Backfill Time Estimates (baseline, per 1M rows):
  - PG→Kafka snapshot: ~5-10 minutes (dependent on PG IOPS and network)
  - Kafka→Milvus embedding upsert: ~15-20 minutes (embedding pre-computed in PG)
  - Kafka→Neo4j node+edge creation: ~10-15 minutes
  - Total: ~30-45 minutes per 1M rows

Resumability: If backfill fails mid-way, restart connector with
  snapshot.mode=initial — it re-snapshots. For large datasets (>10M rows),
  use snapshot.mode=initial_only then switch to a new connector for streaming
  to avoid long snapshot locks.
```

### Recovery flow (target DB write failure)

1. Target SDK returns a failure (Milvus gRPC `UNAVAILABLE`/`DEADLINE_EXCEEDED`, or Neo4j Bolt `TransientException`/`SessionExpired`).
2. Retry per the sink's strategy; on exhaustion, route the event to the per-sink DLQ.
3. Activate Graceful Degradation: KB Retrieval falls back to keyword-only (§5.1) when Milvus is the failed target; Code Graph queries are served from the last-good snapshot with a Workbench warning banner when Neo4j is the failed target.
4. Resolve the target, then drain the DLQ in order. If DLQ depth >1000 (Milvus) or node-count discrepancy >1% (Neo4j), trigger a selective backfill instead of draining (see §20.5).

## Design References

- **§10.1 Consistency Model** — the CDC mechanism this pipeline expands upon, in [`docs/03-architecture.md`](../../03-architecture.md).
- **§5.1 Graceful Degradation** — defines the keyword-only KB Retrieval fallback and the Workbench warning banner behaviour referenced in the Milvus / Neo4j failure rows.
- **§15.2 Internal Event Bus** — the shared Kafka / Redpanda cluster that this pipeline reuses, so no additional infrastructure is provisioned.
- **§20.1–§20.5** — the original CDC Pipeline Architecture Detail (this document's source) in [`docs/03-architecture.md`](../../03-architecture.md).
- **Knowledge-services glossary** — [`docs/glossary.md`](../../glossary.md) for definitions of CDC, WAL, logical replication slot, DLQ, Code Graph, and related terms.
- **Knowledge-services sub-project** — [`docs/sub-projects/knowledge-services/README.md`](README.md).
