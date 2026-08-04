# Code Graph API

> **Origin**: §2.1 of [`docs/03-architecture.md`](../../03-architecture.md) (lines 107–119) and §2 panoramic diagram (lines 92–97) | **Sub-project**: [knowledge-services](README.md)

## Purpose

The Code Graph is the system's **structural knowledge graph** — a unified, queryable model of all artifacts (Workflows, Jobs, DataSources, Formats, KB entries) and their relationships. It is the backbone for **impact analysis**, **lineage tracing**, and **AI context retrieval**.

As depicted in the §2 panoramic diagram, the Code Graph sits directly atop the Knowledge Base storage layer (PostgreSQL + pgvector, S3/MinIO) and exposes a single graph surface over all artifacts:

```
               ┌──────────────┬──────────────┐
               │  Report/Metric Catalog │ Diagnostic Playbooks│
               │  Code Knowledge                               │
               │  ──────────────────────────────────────────── │
               │  PostgreSQL + pgvector (Vector/Graph/Relational)   │
               │  + S3/MinIO (Object Store)                     │
               └──────────────┬────────────────────────────────┘
                              │
               ┌──────────────┴──────────────┐
               │        CODE GRAPH            │
               │   (System Knowledge Graph)   │
               │   Nodes: Workflow/Job/DS/... │
               │   Edges: DEPENDS_ON/READS... │
               └──────────────────────────────┘
```

Nodes represent system artifacts (Workflow, Job, DataSource, Format, KB Entry, BRD, ADR, Jira Epic, Regulation, Deployment, Change, Component); edges represent their structural, semantic, and lifecycle relationships. The Code Graph is **read-optimized**: it is a projection built from authoritative sources, not a write target for users.

## Boundaries

**In-scope:**
- The structural DAG over all system artifacts (nodes + edges) and its 15+ edge-type catalog.
- GraphQL read interface (and Cypher/Gremlin for deep traversals) with parameterized, logged queries.
- Event-sourced write path: domain events are the only mutation source.
- RBAC filtering at row-level (tenant), column-level (PII), and edge-level (cross-tenant).
- Cache strategy: hot subgraph in Redis, full graph in Graph DB, read replicas for analytics.
- Consistency bounds relative to the Relational DB source of truth.

**Out of scope (delegated):**
- Authoritative storage of artifact metadata → Relational DB (PostgreSQL); the Code Graph is a derived projection.
- KB vector/relational content storage and the nine knowledge domains → [`knowledge-base.md`](knowledge-base.md).
- Agent reasoning that *consumes* graph query results → [`agent-platform`](../agent-platform/).
- The CDC mechanism that feeds dedicated graph stores post-MVP → [`cdc-pipeline.md`](cdc-pipeline.md).

## Interfaces

| Aspect | Specification |
| --- | --- |
| **Query Protocol** | GraphQL read interface; Cypher/Gremlin for deep graph traversals. All queries are parameterized and logged. |
| **Write Triggers** | Event-sourced: Freeze Bridge `merge` → node/edge upsert; Runtime `execute` → status edges; KB `confirm` → cross-graph bridge edges. **No direct user writes** — all mutations flow through domain events. |
| **RBAC Filtering** | Queries are transparently filtered by caller's entitlement context: **row-level** (tenant), **column-level** (PII fields), and **edge-level** (cross-tenant relationships denied). The graph never returns data the caller cannot see. |
| **Cache Strategy** | Hot subgraph (active Workflows, recent KB) in Redis; full graph in Graph DB; read replicas for analytical queries. |
| **Consistency** | Eventually consistent with the Relational DB (source of truth). Max staleness: **5 seconds for status edges**, **30 seconds for structural edges**. |

The GraphQL read interface is the canonical entry point for the AI Knowledge Agent and Change Intelligence. A representative RBAC-filtered query (from the shared sequence diagram §21.3):

```graphql
query {
  workflow(id: "monthly_revenue_report") {
    jobs(type: "source") {
      name
      dataSource { name, type, schema_catalog }
    }
  }
}
# headers: { X-Tenant-ID, X-User-ID, X-Role }
```

RBAC filtering is then applied inside the graph layer: row-level `WHERE tenant_id = $caller_tenant`, column-level stripping of PII columns from `schema_catalog`, and edge-level denial of cross-tenant edges.

## Dependencies

- **PostgreSQL (source of truth)** — the Relational DB holds authoritative artifact metadata; the Code Graph is an eventually-consistent projection of it. During MVP, the graph itself is materialized via PG recursive CTE (see [ADR-0013](../../../adr/0013-kb-storage-strategy.md)).
- **Event bus** — Freeze Bridge `merge`, Runtime `execute`, and KB `confirm` events are the only write triggers. The graph cannot be mutated outside the event-sourced path.
- **Redis** — hot-subgraph cache for active Workflows and recent KB entries.
- **KB Linkage Weaving Layer** — produces the cross-graph bridge edges (`DEFINED_IN`, `IS`, `MENTIONS_ENTITY`, `DERIVED_FROM`) that connect KB nodes to Code Graph nodes (see §10.3 in [`knowledge-base.md`](knowledge-base.md)).
- **Auth Service** — supplies the caller's entitlement context that drives RBAC filtering.

## Data Model

The Code Graph is a typed, directed multigraph. Node types include `Workflow`, `Job`, `DataSource`, `Format`, `KB Entry`, `BRD`, `ADR`, `Jira Epic`, `Regulation`, `Deployment`, `Change`, and `Component`. The full relation edge catalog (§23.6.2 of [`docs/03-architecture.md`](../../03-architecture.md)) defines 15+ typed edges:

| Source Node Type | Edge Type | Target Node Type | Meaning | Example Query |
| --- | --- | --- | --- | --- |
| BRD | `REQUIRES` | Workflow | BRD requirements are implemented via Workflow | "Which Workflows implement BRD-2026-001?" |
| BRD | `JUSTIFIES` | ADR | BRD business requirements justify the architecture decision | "Which BRD does this ADR satisfy?" |
| BRD | `TRACKS_BY` | Jira Epic | BRD is tracked by Jira Epic | "Which Jira Epic corresponds to BRD-2026-001?" |
| BRD | `COMPLIES_WITH` | Regulation | Compliance requirements the BRD must satisfy | "Which SOX provisions does this BRD satisfy?" |
| BRD | `DEFINED_BY` | KB Entry | Definition/calculation logic used in the BRD | "Which KB entry defines the revenue calculation logic?" |
| BRD | `READS_FROM` | Data Source | Data sources the BRD depends on | "Which BRDs would be affected by changing this data source?" |
| ADR | `IMPLEMENTED_BY` | Code Graph Component | Which components implement the ADR decision | "Which components are affected by the Kafka CDC decision?" |
| ADR | `TRIGGERED_BY` | Incident | The incident that triggered this decision | "Which incidents led to this architecture decision?" |
| ADR | `SUPERSEDES` | ADR | This ADR supersedes a prior decision | "What is the historical evolution chain of this decision?" |
| ADR | `CONSTRAINS` | Workflow | Architecture decision imposes constraints on Workflow | "Which Workflows are constrained by the CDC decision?" |
| ADR | `RELATED_TO` | KB Entry | ADR references this knowledge entry | |
| Workflow | `REALIZES` | BRD | Workflow realizes BRD requirements | |
| Workflow | `CONSTRAINED_BY` | ADR | Workflow is constrained by ADR decision | |
| Change | `IMPACTS` | BRD | Change impacts BRD → triggers `needs_update` | |
| Change | `MAY_SUPERSEDE` | ADR | Change may render ADR obsolete | |

Additional runtime/structural edges (referenced in the §2 diagram) include `DEPENDS_ON`, `READS`, and the status edges written by Runtime `execute` events. Bridge edges from the KB (`MENTIONS_ENTITY`, `DERIVED_FROM`, `DEFINED_IN`, `IS`) connect KB nodes into the structural graph (detailed in §10.3).

Natural-language queries over the graph are served by the AI Knowledge Agent (S01 → S03 `CodeGraphQuery`) and translated to Cypher/Gremlin traversal logic. Representative examples (§23.6.3):

| Question | Cypher Query Logic |
| --- | --- |
| "Which BRDs would be affected by switching the exchange rate source from ECB to Fed?" | `MATCH (brd:BRD)-[:READS_FROM]->(ds:DataSource {name:'ECB'}) RETURN brd` |
| "Which ADRs influenced the Reconciliation Engine design?" | `MATCH (adr:ADR)-[:IMPLEMENTED_BY]->(comp:Component)-[:BELONGS_TO*1..3]->(w:Workflow {name:'Reconciliation Engine'}) RETURN adr` |
| "Which compliance requirements does this Workflow satisfy?" | `MATCH (w:Workflow)<-[:REQUIRES]-(brd:BRD)-[:COMPLIES_WITH]->(r:Regulation) RETURN r` |
| "Show the complete traceability chain from BRD-2026-001 to final deployment" | `MATCH path = (brd:BRD {id:'BRD-2026-001'})-[*1..6]-(deploy:Deployment) RETURN path` |
| "Which ADRs may be outdated due to no review in 12+ months?" | `MATCH (adr:ADR {status:'accepted'}) WHERE adr.accepted_at < date() - duration('P12M') RETURN adr` |

## Failure Modes & Recovery

- **Stale graph vs. Relational DB.** Because the graph is eventually consistent, a window exists where the graph lags PG. Bounds: ≤5 s for status edges, ≤30 s for structural edges. Consumers that require strict freshness should fall back to PG directly.
- **RBAC filter misconfiguration.** If the entitlement context is missing or malformed, the graph defaults to **deny** — returning no cross-tenant/PII data rather than risking leakage.
- **Event-sourced write lag.** If the event bus falls behind, node/edge upserts are delayed but not lost; on catch-up the graph converges to the Relational DB state. No manual reconciliation is required for transient lag.
- **Cache invalidation gap.** Hot-subgraph cache entries are invalidated on `merge`/`execute`/`confirm` events; a missed invalidation self-heals on TTL expiry (bounded by the 5 s/30 s staleness caps above).

## Non-Functional Requirements

- **Query latency** — GraphQL reads target p95 < 200 ms for the PG recursive-CTE materialization (matches the GraphStore scale limit in [ADR-0013](../../../adr/0013-kb-storage-strategy.md)); deep Cypher/Gremlin traversals are routed to read replicas.
- **Scale** — MVP GraphStore ceiling ~100K nodes / 1M edges before a dedicated engine (Neo4j/Neptune) is considered, per the three-gate conditions in [`knowledge-base.md`](knowledge-base.md).
- **Security** — all queries are parameterized (no string-interpolated Cypher), logged for audit, and transparently RBAC-filtered at row/column/edge levels.
- **Auditability** — every query is logged with caller identity and effective permission set; the Code Graph is referenced as the single source of traceability truth (ADR-012, §23.6.2 of [`docs/03-architecture.md`](../../03-architecture.md)).

## Key Flows

1. **Read (impact analysis / lineage).** Caller issues a GraphQL or Cypher query → Auth Service attaches the entitlement context → graph layer applies row/column/edge RBAC filters → hot-subgraph cache is checked, then full Graph DB, then read replicas for analytical traversals → filtered subgraph returned. See the shared sequence diagram §21.3 AI Agent Query with Permission Gating at [`../_shared/sequence-diagrams.md`](../_shared/sequence-diagrams.md) for the full participant flow (`AGENT → CG` with RBAC filtering at steps 7–9).
2. **Write (event-sourced).** A domain event fires — Freeze Bridge `merge` upserts structural nodes/edges, Runtime `execute` writes status edges, KB `confirm` writes cross-graph bridge edges → the graph applies the upsert → cache is invalidated → readers converge within the 5 s/30 s staleness bounds.
3. **Bridge-edge creation.** KB ingestion produces bridge edges (`KB.GlossaryEntry —DEFINED_IN→ CodeGraph.Job`, `KB.DataAsset —IS→ CodeGraph.DataSource`, `KB.Chunk —MENTIONS_ENTITY→ KB.GlossaryEntry`, `KB.Chunk —DERIVED_FROM→ CodeGraph.Spec`). These are L2-confirmed where they assert audit-impacting lineage (see §10.3 in [`knowledge-base.md`](knowledge-base.md)).
4. **Change Intelligence consumption.** Pre-Change Impact Reports and Post-Change Verification traverse the graph to compute upstream/downstream/indirect impact scope (see [`change-intelligence.md`](change-intelligence.md)).

## Design References

- **§2.1 Code Graph API** — [`docs/03-architecture.md`](../../03-architecture.md) (lines 107–119): the canonical specification table.
- **§2 panoramic diagram** — [`docs/03-architecture.md`](../../03-architecture.md) (lines 92–97): Code Graph's position atop the KB storage layer.
- **§23.6.2 Code Graph Relation Edge Catalog** — [`docs/03-architecture.md`](../../03-architecture.md): the full 15+ edge-type catalog.
- **§23.6.3 Natural Language Query Examples** — [`docs/03-architecture.md`](../../03-architecture.md): NL-to-Cypher translation patterns.
- **ADR-012** — Code Graph as Single Source of Traceability Truth (referenced from §23.6.2).
- [ADR-0013](../../../adr/0013-kb-storage-strategy.md) — KB Storage: PG-First with Interface Abstraction (GraphStore MVP = PG recursive CTE).
- Shared sequence diagram §21.3 — [`../_shared/sequence-diagrams.md`](../_shared/sequence-diagrams.md): AI Agent Query with Permission Gating.
- Cross-references: [`knowledge-base.md`](knowledge-base.md) (KB domains and bridge edges), [`change-intelligence.md`](change-intelligence.md) (graph-driven impact analysis).
- Glossary: [`../../glossary.md`](../../glossary.md).
