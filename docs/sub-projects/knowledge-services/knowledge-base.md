# Knowledge Base

> **Origin**: §10 of [`docs/03-architecture.md`](../../03-architecture.md) (lines 1166–1334) | **Sub-project**: [knowledge-services](README.md)

## Purpose

The Knowledge Base is the system's **long-term memory**, spanning **nine knowledge domains**. It holds the institutional knowledge that makes the system legible to both humans and AI: terms, definitions, data catalogs, field mappings, workflow templates, adjustment history, behavior patterns, report/metric definitions, diagnostic playbooks, and a three-layer index over code artifacts.

**Semantic Layer Alignment** (§10 overview): the **Business Glossary** + **Report/Metric Catalog** together constitute the system's semantic layer, following the dimension-metric-entity modeling paradigm of dbt Semantic Layer and MetricFlow. This supports exposure of a unified semantic interface to external analysis tools (Tableau, PowerBI, Excel) via JDBC/ODBC in the Post-MVP Phase 7+.

The KB is governed by three architectural decisions: [ADR-0013](../../../adr/0013-kb-storage-strategy.md) (PG-First strategy), [ADR-0023](../../../adr/0023-kb-content-lifecycle-pipeline.md) (Content Lifecycle Pipeline), and [ADR-0024](../../../adr/0024-kb-reasoning-support-playbooks-code.md) (Playbooks + Code Knowledge as domains 8 and 9).

## Boundaries

**In-scope:**
- The nine KB domains and their content (table below).
- Storage architecture: PG-First + Interface Abstraction (VectorStore / GraphStore / RelationalStore / BlobStore).
- Layered consistency model — Relational DB (PostgreSQL) as the sole authoritative source.
- Read/Write paths: provenance-tagged writes, hybrid reads (semantic + keyword + graph expansion), governance.
- Content Processing Pipeline (5-stage funnel, §10.2 → [ADR-0023](../../../adr/0023-kb-content-lifecycle-pipeline.md)).
- Linkage Weaving Layer (cross-content edges: `MENTIONS_ENTITY`, `SIMILAR_TO`, `DERIVED_FROM`, `CONFLICTS_WITH`, §10.3).
- Quality Flywheel (Dedup → Conflict Detection → Freshness Decay → Retrieval Quality Evaluation, §10.4).
- Bridge edges into the Code Graph.

**Out of scope (delegated):**
- The structural DAG over Workflows/Jobs/DataSources → [`code-graph.md`](code-graph.md).
- CDC replication mechanics into dedicated Vector/Graph stores post-MVP → [`cdc-pipeline.md`](cdc-pipeline.md).
- Agent reasoning that consumes KB query results → [`agent-platform`](../agent-platform/).
- Email ingestion pipeline's own AI fact-extraction → §12.1 of [`docs/03-architecture.md`](../../03-architecture.md).

## Interfaces

| Interface | Consumer | Contract |
| --- | --- | --- |
| `kb.query(domain, filter) → entries` | Agent Platform, Query Serving | Hybrid search (semantic + keyword + graph expansion), fusion ranking, RBAC-filtered |
| `kb.write(domain, entry, provenance) → entry_id` | Agent Platform (`kb_write` capability), Data Health | ACID write with provenance tag; bitemporal validity; versioned |
| KB Storage (`VectorStore`/`GraphStore`/`RelationalStore`/`BlobStore`) | KB internals, Code Graph | PG-First MVP (see Data Model) |

**The nine knowledge domains** (§10 overview table — domains 8 and 9 per [ADR-0024](../../../adr/0024-kb-reasoning-support-playbooks-code.md)):

| Domain | Content |
| --- | --- |
| **Business Glossary** | Terms, definitions, formulas, definition sources, change history |
| **Data Catalog** | Data asset metadata, Schema, column-level business meaning, PII, quality scores |
| **Mapping Registry** | Cross-system field mappings, transformation rules (reversible), change history |
| **Workflow Templates** | Template definitions, categorization, prerequisite KB requirements, usage statistics |
| **Adjustment History** | Anomaly root cause analysis, adjustment entries, approval chain (immutable) |
| **Behavior Patterns** | User action sequences, temporal patterns, derived suggestions |
| **Report/Metric Catalog** | Report definitions, metric formulas, calculation granularity, certification status, relationships with data sources and Workflows |
| **Diagnostic Playbooks** *(ADR-0024)* | Expert-encoded diagnostic decision trees (IF/THEN investigation paths) that act as a "soft skeleton" guiding Agent reasoning in Exploration Mode — the read-only counterpart to Verified Paths |
| **Code Knowledge** *(ADR-0024)* | Three-layer index over code artifacts (Compute Spec YAML, Sandbox Python, Git history, external repos): structural (Code Graph nodes/edges), semantic (function-level embeddings), change (commits/blame/diffs) |

## Dependencies

- **PostgreSQL + pgvector** — the sole authoritative store in MVP. Provides Vector (`pgvector` HNSW), Graph (recursive CTE), and Relational (native tables) roles simultaneously. See [ADR-0013](../../../adr/0013-kb-storage-strategy.md).
- **S3 / MinIO** — Blob Store for email originals, attachments, LLM transcripts. PG rows reference the object key.
- **Code Graph** — bridge edges connect KB nodes into the structural graph (§10.3); the Code Graph read interface is documented in [`code-graph.md`](code-graph.md).
- **Parsing MCPs** — Stage 1 of the Content Processing Pipeline dispatches to MCP-11 (email-parser), MCP-12 (ocr), MCP-16 (excel-parser); it does not duplicate them.
- **Email Pipeline (§12.1)** — its output (after AI fact-extraction and human-confirmation gate) flows into the content processing funnel.
- **Freeze Pipeline / Sandbox** — Sandbox Python code and Compute Specs enter via the code-ingestion events defined in [ADR-0024](../../../adr/0024-kb-reasoning-support-playbooks-code.md).
- **Golden Dataset (ADR-0018)** — used for offline RAGAS evaluation in the Quality Flywheel.

## Data Model

### Storage Architecture (§10)

KB storage adopts a **PG-First + Interface Abstraction** strategy ([ADR-0013](../../../adr/0013-kb-storage-strategy.md)). In the MVP phase, PostgreSQL takes on the Vector / Graph / Relational three roles, while S3/MinIO handles Blob. Interface abstraction reserves plug-and-play capability for future dedicated engines — dedicated engines are introduced **only when PG reaches verifiable performance thresholds**, not as a pre-planned architecture.

```
                    ┌────────────────────────────────────────────┐
                    │          KB Storage Interface               │
                    │  VectorStore │ GraphStore │ RelationalStore │ BlobStore │
                    └──────────────┴────────────┴────────────────┴───────────┘
                                   │                │               │
              ┌────────────────────┼────────────────┼───────────────┘
              │                    │                │
              ▼                    ▼                ▼
    ┌─────────────────┐  ┌──────────────────┐  ┌──────────────┐
    │ PostgreSQL       │  │ PostgreSQL        │  │ S3 / MinIO   │
    │ + pgvector       │  │ (Recursive CTE)   │  │ (Object      │
    │ (Vector +        │  │ (Graph)           │  │  Store)      │
    │  Relational)     │  │                   │  │              │
    └────────┬─────────┘  └────────┬──────────┘  └──────────────┘
             │                     │
             ▼                     ▼
    Future optional: Milvus/Qdrant    Future optional: Neo4j/Neptune
    (Only after PG reaches performance threshold)  (Only after PG reaches performance threshold)
```

| Interface | MVP Implementation | Scale Limit | Future Optional Replacement |
| --- | --- | --- | --- |
| `VectorStore` | **pgvector (HNSW)** | ~1M embeddings, <200 ms | Milvus / Qdrant |
| `GraphStore` | **PG Recursive CTE** | ~100K nodes / 1M edges, <200 ms | Neo4j / Neptune |
| `RelationalStore` | **PostgreSQL** (native) | Tens of millions of rows per table | — (PG is sufficient) |
| `BlobStore` | **S3 / MinIO** | Unlimited | — (Standard solution) |

**KB Data Scale Estimate**: a typical mid-size enterprise over 5 years of operation is projected at **~720K records** (Glossary ~5K + Data Catalog ~50K columns + Mapping ~10K + Templates ~1K + Adjustment ~100K + Behavior ~500K + Report/Metric ~5K + Diagnostic Playbooks ~500 + Code Knowledge ~50K function/Spec chunks), still far below PG's replacement threshold. See [ADR-0013](../../../adr/0013-kb-storage-strategy.md).

**Three-Gate Conditions for Introducing Dedicated Engines**: dedicated engines are introduced only when **all** of the following are simultaneously met: (a) PG stably exceeds p95 latency target, (b) data volume consistently exceeds scale limit, (c) PG-level optimizations are exhausted, (d) TCO cost-benefit is positive. There is no "deploy as backup" strategy.

### Consistency Model (§10.1)

The Knowledge Base adopts a layered consistency model, with the Relational DB (PostgreSQL) as the **sole authoritative data source**.

**MVP Phase** (zero CDC pipelines — the [ADR-0013](../../../adr/0013-kb-storage-strategy.md) advantage):

| Store | Role | Consistency | Implementation |
| --- | --- | --- | --- |
| **PostgreSQL + pgvector** | **Sole Source of Truth** — Vector / Graph / Relational capabilities all provided by PG | Strong (ACID) | Single repository: embeddings stored in PG columns, graph traversal via recursive CTE, metadata in native tables |
| **S3 / MinIO** | Blob Store — email originals, attachments, LLM transcripts | Immediate (write-once) | Direct write; PG row references object key |

**Post-MVP** (only after dedicated engines are introduced):

| Store | Role | Consistency | Sync Mechanism |
| --- | --- | --- | --- |
| **PostgreSQL** | **Source of Truth** — authoritative version of all KB entries | Strong (ACID) | N/A — sole write entry point |
| **Vector DB** (Milvus/Qdrant) | Semantic search index, derived from PG | Eventually Consistent (max 30 s) | CDC from PG → re-embed → upsert |
| **Graph DB** (Neo4j/Neptune) | Relationship index, KB internal edges + Code Graph bridging | Eventually Consistent (max 30 s) | CDC from PG + Code Graph events → edge upsert |
| **S3 / MinIO** | Blob Store | Immediate | Direct write; PG row references object key |

**Conflict Resolution** (Post-MVP):
- PostgreSQL is always authoritative. Vector/Graph are read-optimized projections.
- If Vector or Graph return results inconsistent with PG (detected by **version watermark comparison**), the query layer falls back to PG and triggers a re-sync.
- KB Governance dashboard displays sync lag per store; alerts fire at **>60 s lag**.

## Failure Modes & Recovery

- **Vector/Graph drift from PG (Post-MVP).** Detected via version watermark comparison; the query layer falls back to PG and triggers a re-sync. Sync-lag alerts fire at >60 s.
- **Conflict between new and existing facts.** NLI contradiction detection marks the fact `conflict` → frozen → human adjudication. The system **never auto-overwrites** (generalizes ADR-0022 BRD conflict pattern). See §10.4 Conflict Detection.
- **Freshness decay.** Each chunk carries a `half_life` by content type; beyond half-life the chunk is marked stale and triggers a "still valid?" re-review. **Decay is not deletion** — old values are retained as historical version-chain entries (auditable), only down-ranked at retrieval time, consistent with ADR-0019's bitemporal validity.
- **Retrieval quality regression.** RAGAS metrics on the Golden Dataset (ADR-0018) detect regressions offline; affected domains trigger re-embedding or re-chunking.
- **Provenance gap.** Every chunk carries an immutable provenance tag (source_doc_id, source_span, ingest_time, ingest_channel, extractor, confidence). A missing provenance tag fails the Stage 5 write and is rejected.

## Non-Functional Requirements

- **Write latency** — single ACID transaction across all four indexes (Stage 4 of §10.2); no sync window, no partial-write state (the [ADR-0013](../../../adr/0013-kb-storage-strategy.md) zero-CDC advantage).
- **Vector search** — p95 < 200 ms for pgvector HNSW at ~1M embeddings.
- **Graph traversal** — p95 < 200 ms for PG recursive CTE at ~100K nodes / 1M edges.
- **Scale** — ~720K projected records over 5 years; far below PG replacement threshold.
- **Auditability** — immutable provenance chain (satisfies FR17.5 + SOX); version history for every entry; approval workflow for audit-impacting lineage (L2).
- **Provenance classes** (align ADR-0019): `user_uploaded` / `email_received` / `api_pushed`.

## Key Flows

### Read/Write Paths (§10.1 Read/Write Paths)

- **Write**: User explicit → AI extraction + confirmation → system automated. All pass through **Permission → Versioning → Notification → Embedding → Graph**.
- **Read**: Semantic search → keyword filtering → relationship expansion → fusion ranking → inject into AI Prompt.
- **Governance**: Version history, approval workflow, expiration detection, **KB↔Code Graph inconsistency alerts**.

### Content Processing Pipeline (§10.2 → [ADR-0023](../../../adr/0023-kb-content-lifecycle-pipeline.md))

All heterogeneous content sources — enterprise email (SMTP), user uploads (DOCX/XLSX/PDF), API pushes, Excel imports, pasted text — converge into a **single five-stage processing funnel** so that retrieval quality, provenance, and linkage are uniform regardless of origin. Stage 1 dispatches to the existing parsing MCPs (MCP-11 email-parser, MCP-12 ocr, MCP-16 excel-parser); it does not duplicate them.

```
Heterogeneous sources (SMTP / upload / API / paste)
   │
   ▼
STAGE 1 — Parse & Normalize (deterministic, reuse MCP-11/12/16)
   │   .docx → POI/Unstructured; .xlsx → MCP-16; .pdf → PDFBox+Camelot / MCP-12 OCR;
   │   email → MCP-11 → EmailRecord (per §12.1)
   │   Output: ContentUnit { type, raw_text, structure, blob_ref }  (structure preserved — anchors for §10.3)
   ▼
STAGE 2 — Semantic Chunking (structure-aware, not fixed-length)
   │   Split on structural boundaries; tables stay intact; email header/body/attachment split
   ▼
STAGE 3 — Contextual Retrieval Enhancement (key quality uplift)
   │   Small model generates a context summary prepended to each chunk before embedding
   │   (Anthropic 2024: -35% retrieval failure alone, -67% with reranking)
   │   Same summary also indexed into BM25 (keyword retrieval benefits too)
   ▼
STAGE 4 — Vectorize + Multi-Index Write (single ACID transaction — ADR-0013 zero-CDC advantage)
   │   Embedding → pgvector HNSW; raw+summary → tsvector GIN; fields → native tables;
   │   edges → edge tables (§10.3); blob → S3 (PG stores key)
   │   All four indexes in one transaction — no sync window, no partial-write state
   ▼
STAGE 5 — Provenance Tagging (immutable audit chain, satisfies FR17.5 + SOX)
   source_doc_id, source_span, ingest_time, ingest_channel, extractor, confidence
   Provenance classes (align ADR-0019): user_uploaded / email_received / api_pushed
```

**Relationship to existing ingestion channels**: the Email Pipeline (§12.1) output flows into this funnel after its own AI fact-extraction and human-confirmation gate; Sandbox Python code and Compute Specs enter via the code-ingestion events defined in [ADR-0024](../../../adr/0024-kb-reasoning-support-playbooks-code.md). **No existing pipeline is bypassed** — Stage 1 is a dispatch layer over existing MCPs.

### Linkage Weaving Layer (§10.3 → [ADR-0023](../../../adr/0023-kb-content-lifecycle-pipeline.md))

This layer defines *how heterogeneous content gets connected* so the Agent can reason across "the email that mentioned a metric + the DOCX that defined it + the Excel that computed it". Three linkage edge types connect content; one conflict edge type freezes contradictions. All four are generated by the strategies below, mapped to the existing Remediation Gateway tiers (L0–L3, see §12.2 of [`docs/03-architecture.md`](../../03-architecture.md)). (The `CONFLICTS_WITH` edge and the Quality Flywheel's Conflict Detection stage describe the same mechanism from the edge-creation and governance perspectives, respectively.)

| Edge Type | Relation | Risk | Generation Strategy | Confirmation |
| --- | --- | --- | --- | --- |
| **Entity Co-reference** | `MENTIONS_ENTITY` (chunk → GlossaryEntry) | Low | Small-model NER + KB entity matching (exact-first) + candidate disambiguation | High-conf auto-created; low-conf enters review queue |
| **Semantic Similarity** | `SIMILAR_TO` (chunk ↔ chunk) | Low | On ingest: vector near-neighbor query (top-5); similarity > 0.85 AND passes NLI non-contradiction → edge | Auto-created; dismissable from KB Governance Dashboard |
| **Structural Lineage** | `DERIVED_FROM` (ReportCell → ExcelRange → DataSource) | **High (audit-impacting)** | LLM proposes only — wrong lineage in financial scenarios is catastrophic | **Mandatory human confirm (L2 approval)** |
| **Conflict** | `CONFLICTS_WITH` (fact ↔ fact) | High | NLI contradiction detection between new and existing facts | Detected → `conflict` → **frozen, human adjudication** (ADR-0022 pattern generalized) |

**Why not full GraphRAG (Microsoft community hierarchy)?** The KB's projected scale (~720K records) and PG-First / zero-CDC philosophy make full community-hierarchy construction a poor fit — it is LLM-expensive, hard to update incrementally, and re-introduces the operational complexity [ADR-0013](../../../adr/0013-kb-storage-strategy.md) rejected. **Lazy edge creation** (on ingest + on query) delivers GraphRAG's "connect the dots" benefit at a fraction of the cost. Dedicated community detection is reserved as a future option only if a measurable retrieval-quality gap justifies it.

**Bridge edges to Code Graph** (cross-graph linking, extends §2.1 of [`code-graph.md`](code-graph.md)):

```
KB.GlossaryEntry  —DEFINED_IN→  CodeGraph.Job
KB.DataAsset      —IS→           CodeGraph.DataSource
KB.Chunk          —MENTIONS_ENTITY→  KB.GlossaryEntry
KB.Chunk          —DERIVED_FROM→  CodeGraph.Spec   (lineage, L2-confirmed)
```

These bridge edges are what let the Agent in Scenario 6 (§22E) join "the email about gross margin" + "the Job that computes it" + "the report that displays it" into one causal chain.

### Quality Flywheel (§10.4 → [ADR-0023](../../../adr/0023-kb-content-lifecycle-pipeline.md))

A closed-loop governance system that prevents silent KB quality drift. Four stages, each feeding the next:

```
New content ingested (Stages 1–5 of §10.2)
   │
   ▼
Dedup — SimHash/MinHash near-duplicate detection; forwarded email chains → one canonical + reference list
   │
   ▼
Conflict Detection — new fact vs existing KB fact → NLI contradiction → mark conflict → frozen → human adjudication (never auto-overwrite; generalizes ADR-0022 BRD conflict pattern)
   │
   ▼
Freshness Decay — each chunk carries a half_life by content type:
   • Business definitions: long (2 years; expire only on explicit change)
   • Data snapshots / report figures: short (30 days)
   • Email facts: medium (180 days)
   Fusion-ranking Freshness weight (S02 already has 0.10) scales with decay;
   beyond half_life → marked stale → triggers "still valid?" re-review
   │
   ▼
Retrieval Quality Evaluation (offline) — RAGAS-family metrics (context_precision / context_recall / faithfulness);
   uses ADR-0018 Golden Dataset for A/B evaluation; quality regression → triggers re-embedding or re-chunking of affected domain
```

**Decay is not deletion** — consistent with ADR-0019's bitemporal validity: old values are retained as historical version-chain entries (auditable), only down-ranked at retrieval time, never lost.

## Design References

- **§10 Knowledge Base** — [`docs/03-architecture.md`](../../03-architecture.md) (lines 1166–1334): the canonical source for overview, Storage Architecture, Consistency Model, Read/Write Paths, Content Processing Pipeline, Linkage Weaving Layer, and Quality Flywheel.
- [ADR-0013](../../../adr/0013-kb-storage-strategy.md) — **KB Storage: PG-First with Interface Abstraction**. Governs the MVP single-repository strategy (pgvector + recursive CTE), the ~720K scale estimate, the scale limits per interface, and the three-gate conditions for introducing dedicated engines. Referenced throughout Storage Architecture, Consistency Model, and Pipeline Stage 4.
- [ADR-0023](../../../adr/0023-kb-content-lifecycle-pipeline.md) — **KB Content Lifecycle Pipeline**. Full rationale for the Content Processing Pipeline (§10.2), Linkage Weaving Layer (§10.3), and Quality Flywheel (§10.4).
- [ADR-0024](../../../adr/0024-kb-reasoning-support-playbooks-code.md) — **KB Reasoning Support (Playbooks + Code Knowledge)**. Adds domains 8 (Diagnostic Playbooks) and 9 (Code Knowledge: three-layer structural/semantic/change index) and defines the code-ingestion events that feed the pipeline.
- Related ADRs referenced inline: ADR-0015 (Remediation Gateway L0–L3 tiers), ADR-0018 (Golden Dataset), ADR-0019 (bitemporal validity / provenance classes), ADR-0022 (BRD conflict pattern).
- Cross-references: [`code-graph.md`](code-graph.md) (bridge edges, structural DAG), [`cdc-pipeline.md`](cdc-pipeline.md) (Post-MVP CDC into dedicated engines), [`change-intelligence.md`](change-intelligence.md) (KB as Agent knowledge source).
- Glossary: [`../../glossary.md`](../../glossary.md).
