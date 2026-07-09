---
id: ADR-0013
title: "KB Storage — PG-First with Interface Abstraction"
status: accepted
date: 2026-07-04
deciders: "Project Sponsor"
domain: Architecture
---

# ADR-0013: KB Storage — PG-First with Interface Abstraction

- **Status**: Accepted
- **Date**: 2026-07-04
- **Deciders**: Project Sponsor

## Context

The Knowledge Base requires four storage capabilities: semantic retrieval (Vector), relationship traversal (Graph), structured metadata (Relational), and large objects (Blob). The initial plan presupposed four dedicated engines (Milvus/Qdrant + Neo4j/Neptune + PostgreSQL + S3), but the following issues exist:

1. **Operational Complexity**: The MVP team would need to operate 4 stateful services simultaneously, each requiring backup, monitoring, and CDC pipelines
2. **Scale Mismatch**: The BI system's KB data volume (tens to hundreds of thousands of records) is far below the design targets of dedicated engines (tens of millions+), resulting in over-engineering
3. **Industry Trend**: The 2024-2026 industry consensus has shifted to "Boring Technology Wins" — Notion, Linear, Vercel, and Shopify have all migrated back from multi-engine architectures to PostgreSQL as the primary store
4. **CDC Pipeline Fragility**: Multiple incremental sync pipelines (PG→Vector, PG→Graph, PG→Object) increase the system failure surface and debugging difficulty

## Options Considered

### Option A: Four Dedicated Engines Day One (Rejected)
Deploy 4 dedicated engines from day one of MVP.
- **Pro**: Each engine optimized for its domain, maximizing performance
- **Con**: Operational complexity explosion; MVP-stage data volume is far below dedicated engine thresholds; the team must master four technology stacks simultaneously

### Option B: PostgreSQL Unified (Rejected)
Use only PostgreSQL forever, without introducing any other engines.
- **Pro**: Simplest operations, single technology stack
- **Con**: PG is unsuitable for Object Store scenarios (large binary objects); no expansion path after future scale growth

### Option C: PG-First + Interface Abstraction (Chosen)
In the MVP phase, PG handles the three roles of Vector/Graph/Relational, while S3/MinIO handles the Blob role. Interface abstraction reserves plug-and-play capability for introducing dedicated engines in the future.

## Decision

Adopt **Option C** (PG-First + Interface Abstraction):

### Storage Interface Definitions

```python
# Four abstract interfaces. In the MVP phase, PG implements the first three and S3 implements the fourth.

class VectorStore(Protocol):
    """Semantic retrieval interface"""
    def search(query_embedding: ndarray, top_k: int, filters: dict) -> list[SearchResult]: ...
    def upsert(entries: list[VectorEntry]) -> None: ...
    def delete(ids: list[str]) -> None: ...

class GraphStore(Protocol):
    """Relationship traversal interface"""
    def traverse(start_node: str, relation: str, max_depth: int) -> TraversalResult: ...
    def upsert_edges(edges: list[Edge]) -> None: ...
    def detect_cycles(root: str) -> list[Cycle]: ...

class RelationalStore(Protocol):
    """Structured metadata interface"""
    def query(sql: str, params: dict) -> ResultSet: ...
    def upsert(table: str, rows: list[dict]) -> None: ...

class BlobStore(Protocol):
    """Large object storage interface"""
    def put(key: str, data: bytes, metadata: dict) -> None: ...
    def get(key: str) -> bytes: ...
    def delete(key: str) -> None: ...
```

### MVP Implementation Matrix

| Interface | MVP Implementation | Scale Limit (Performance Threshold) | Future Optional Replacement |
|---|---|---|---|
| `VectorStore` | **pgvector (HNSW)** | ~1M embeddings, <200ms | Milvus / Qdrant |
| `GraphStore` | **PG Recursive CTE** | ~100K nodes / 1M edges, <200ms | Neo4j / Neptune |
| `RelationalStore` | **PostgreSQL** (native) | No upper limit | — (PG is sufficient) |
| `BlobStore` | **S3 / MinIO** | No upper limit | — (Standard solution) |

### Four Gating Criteria for Introducing Dedicated Engines

Only introduce a dedicated engine when **all** of the following conditions are met:
1. PG implementation consistently exceeds p95 latency targets under production load
2. Data volume has exceeded the "Scale Limit" and is still growing
3. PG-level optimizations have been exhausted (index tuning, partitioning, connection pooling, read/write separation)
4. TCO after introduction (license + operations + learning cost) < PG scaling cost

**Explicit non-triggers**: "Just in case", "Big Company X uses it", "makes the tech stack look advanced"

### CDC Pipeline Simplification

MVP has zero CDC pipelines — Vector and Graph queries go directly through PG with no additional synchronization needed. Post-MVP: only after dedicated engine introduction do CDC pipelines activate.

### KB Data Scale Estimate

| KB Domain | Record Type | Estimated Scale (5 years) |
|---|---|---|
| Business Glossary | Term definitions | ~5,000 records |
| Data Catalog | Table/column-level metadata | ~50,000 columns |
| Mapping Registry | Field mapping rules | ~10,000 records |
| Workflow Templates | Compute Spec | ~1,000 records |
| Adjustment History | Adjustment records | ~100,000 records |
| Behavior Patterns | User behavior sequences | ~500,000 records |
| Report/Metric Catalog | Report/metric definitions | ~5,000 records |
| **Total** | | **~670,000 records** |

Far below the thresholds of pgvector (1M embeddings) and PG CTE (100K nodes).

## Rationale

1. **"Boring Technology Wins"**: PostgreSQL has been the most reliable database of the past decade. Introducing dedicated engines early is premature optimization.
2. **Vast Operational Cost Difference**: Operating one PG instance vs. four stateful services — the latter requires 3-4x the workload for on-call, backup strategy, disaster recovery, and version upgrades.
3. **Interface Abstraction Preserves Flexibility**: Business code depends on interfaces, not implementations — PG today, Milvus tomorrow, without changing a single line of business code.
4. **CDC Risk Elimination**: Zero CDC pipelines in the MVP phase means zero sync latency, zero consistency issues.
5. **Team Focus**: A small team mastering one database (PG) in depth is far better than shallow mastery of four databases.

## Consequences

- **Positive**: MVP operational complexity reduced from 4 stateful services to 2 (PG + S3); zero CDC pipelines eliminate synchronization failures; interface abstraction ensures future extensibility.
- **Negative**: If business growth far exceeds expectations, a one-time dedicated engine migration cost must be paid — but sufficient resources will be available by then.
- **Neutral**: pgvector HNSW index construction takes a few seconds at million-scale data volumes — completely acceptable for KB update frequency.

## Linked Modules

- `docs/03-architecture.md` → §10 (Knowledge Base Storage Architecture)
- `docs/02-requirement.md` → FR4.5 (KB Technical Foundation)
- `docs/01-facts.md` → §Core Design Philosophy #4 (Knowledge Base as System Foundation)
- `adr/0008-large-scale-data-strategy.md` → Decision #8
