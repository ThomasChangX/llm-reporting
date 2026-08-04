# knowledge-services — Knowledge, Metadata & Change Intelligence

> **Origin**: §2.1, §9, §10, §20 of `docs/03-architecture.md`
> **Key ADRs**: [ADR-0013](../../adr/0013-kb-storage-strategy.md) (PG-First), [ADR-0023](../../adr/0023-kb-content-lifecycle-pipeline.md) (Content Lifecycle), [ADR-0024](../../adr/0024-kb-reasoning-support-playbooks-code.md) (Reasoning Support)

## Positioning

The **Knowledge Services** sub-project is the system's institutional memory — a unified, queryable model of all artifacts, their relationships, and the processes that keep that knowledge fresh. It owns the Knowledge Base (9 domains), the Code Graph (structural DAG), the CDC pipeline that syncs relational data into Vector/Graph stores, and the Change Intelligence layer that reasons about system modifications.

Storage follows ADR-0013's **PG-First with Interface Abstraction** strategy: PostgreSQL + pgvector handles Vector/Graph/Relational roles during MVP; dedicated engines (Milvus/Neo4j) are reserved via interface abstraction and introduced only when four gating conditions are met.

## Boundaries

**In-scope:**
- Knowledge Base storage (9 domains: Business Glossary, Data Catalog, Mapping Registry, Workflow Templates, Adjustment History, Behavior Patterns, Report/Metric Catalog, Diagnostic Playbooks, Code Knowledge)
- Code Graph API (structural knowledge graph, 15+ edge types, GraphQL read interface)
- KB Consistency Model and Read/Write Paths
- Content Processing Pipeline (5-stage funnel: Parse → Chunk → Contextual Retrieval → ACID Write → Provenance)
- Linkage Weaving Layer (cross-content relationship edges: MENTIONS_ENTITY, SIMILAR_TO, DERIVED_FROM, CONFLICTS_WITH)
- Quality Flywheel (Freshness Decay, Entity Linking, bitemporal retention)
- CDC Pipeline (Debezium + Kafka Connect, per-target transformation, backfill strategy)
- Change Intelligence (Pre-Change Impact Report, Post-Change Verification, AI Knowledge Agent)

**Delegated to other sub-projects:**
- Agent reasoning over KB content → [`agent-platform`](../agent-platform/)
- Query execution against data sources → [`query-serving`](../query-serving/) / [`workflow-engine`](../workflow-engine/)
- Audit trail for KB writes → [`platform-core`](../platform-core/)

## Module List

| Module | Origin | Document |
|--------|--------|----------|
| Code Graph API | §2.1 | [`code-graph.md`](code-graph.md) |
| Knowledge Base (9 domains, Consistency Model, Read/Write Paths) | §10 | [`knowledge-base.md`](knowledge-base.md) |
| CDC Pipeline (Debezium + Kafka Connect) | §20 | [`cdc-pipeline.md`](cdc-pipeline.md) |
| Change Intelligence & Agent Triage | §9 | [`change-intelligence.md`](change-intelligence.md) |

## External Interface Contract

| Interface | Consumer | Contract |
|-----------|----------|----------|
| `kb.query(domain, filter) → entries` | Agent Platform, Query Serving | Hybrid search (semantic + keyword + graph expansion) |
| `kb.write(domain, entry, provenance) → entry_id` | Agent Platform (kb_write capability), Data Health | ACID write with provenance tag; bitemporal validity |
| `code_graph.query(graphql_or_cypher) → subgraph` | Agent Platform, Change Intelligence | RBAC-filtered structural query |
| `cdc.status(source_table) → lag_metrics` | Platform Core (observability) | Replication lag, throughput, error rates |

## Related ADRs

- [ADR-0013](../../adr/0013-kb-storage-strategy.md) — KB Storage: PG-First with Interface Abstraction
- [ADR-0023](../../adr/0023-kb-content-lifecycle-pipeline.md) — KB Content Lifecycle Pipeline (Processing, Linkage Weaving, Quality Flywheel)
- [ADR-0024](../../adr/0024-kb-reasoning-support-playbooks-code.md) — KB Reasoning Support (Diagnostic Playbooks & Code Knowledge)
