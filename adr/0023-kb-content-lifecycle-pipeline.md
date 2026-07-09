---
id: ADR-0023
title: "KB Content Lifecycle Pipeline — Unified Processing, Linkage Weaving, and Quality Flywheel"
status: accepted
date: 2026-07-08
deciders: "Architecture Team"
domain: Architecture
---

# ADR-0023: KB Content Lifecycle Pipeline — Unified Processing, Linkage Weaving, and Quality Flywheel

- **Status**: Accepted
- **Date**: 2026-07-08
- **Deciders**: Architecture Team
- **Domain**: Architecture

## Context

The Knowledge Base design currently spans three accepted ADRs and several architecture sections:

- **ADR-0013** established storage (PG-First + Interface Abstraction — pgvector + recursive CTE + S3).
- **`docs/03-architecture.md` §10** defined the seven knowledge domains and the PG-First storage matrix.
- **FR34 / §KB Write Paths** defined three write paths (user explicit / AI extraction + human confirmation / system automatic) with confidence-priority conflict resolution.
- **FR35 / §KB Read Paths** defined hybrid retrieval four steps (semantic → keyword → relationship expansion → fusion ranking).
- **§12.1 / FR17** defined the Email Ingestion Pipeline end-to-end (SMTP → parse → AI fact extraction → human confirmation gate).

However, three areas that span *all* heterogeneous content sources (DOCX, Excel, Email, user uploads, API pushes) are **not systematically defined**:

1. **Content Processing Pipeline is implicit.** Each ingestion channel (Email, Sandbox code, KB Write) processes content differently. There is no unified definition of how raw content becomes a retrieval-grade artifact: how it is chunked, how embeddings are produced, how multiple indexes are written atomically, and how provenance is stamped. Per-channel ad-hoc pipelines inevitably fragment retrieval quality and make cross-source correlation impossible.

2. **Linkage Weaving is undefined.** The KB already declares edge types (RELATED_TO / MAPS_TO / TRANSFORMS / REFERENCES / EXTRACTED_TO / REQUIRES — see `docs/01-facts.md` §KB Storage Architecture), but there is no mechanism defining *how heterogeneous content automatically produces these edges*. Without entity co-reference linking, structural lineage edges, and semantic-similarity edges, content lives in isolated islands — the Agent cannot reason across "the email that mentioned this metric + the DOCX that defined it + the Excel that computed it."

3. **Quality governance lacks a closed loop.** Write paths (FR34) and governance (FR36) exist, but there is no freshness decay, no near-duplicate detection across channels, no automated conflict detection between newly-ingested and existing facts, and no offline retrieval-quality evaluation feeding back into re-chunking or re-embedding decisions. Without this, KB quality drifts silently over time.

The 2024-2026 industry consensus on production RAG systems converges on three architectural patterns that directly address these gaps: **Contextual Retrieval** (Anthropic, 2024), **lazy GraphRAG-lite edge creation** (vs full community-hierarchy GraphRAG), and **RAGAS-style retrieval evaluation flywheels**.

## Options Considered

### Option A: Per-Channel Pipelines (Rejected)

Each ingestion channel (Email / Sandbox / Upload / API) implements its own chunking, embedding, and indexing logic, optimized for its content type.

- **Pro**: Each channel can use type-specific optimizations (e.g., Excel keeps table rows intact; Email splits header/body).
- **Con**: Format and retrieval quality fragment across channels; no single place to enforce provenance, dedup, or conflict rules; cross-channel linkage becomes impossible because chunk schemas diverge; the team maintains N pipelines instead of one. This is the anti-pattern Databricks and Unstructured.io explicitly warn against in their 2025 production guidance.

### Option B: Full GraphRAG Community Hierarchy (Rejected)

Adopt Microsoft GraphRAG wholesale — extract a complete entity-relationship graph from all content, build community hierarchies with LLM-generated summaries, and retrieve via community-level global search.

- **Pro**: State-of-the-art for "connect the dots" reasoning over large unstructured corpora; community summaries give strong global context.
- **Con**: Directly conflicts with ADR-0013's "Boring Technology Wins" philosophy and the zero-CDC, single-engine (PostgreSQL) decision. Community hierarchy construction is LLM-expensive, hard to update incrementally (a single new document can trigger community re-partitioning), and operationally heavy. The KB's projected scale (~720K records, 5-year) is two orders of magnitude below GraphRAG's sweet spot. This is premature optimization that re-introduces exactly the operational complexity ADR-0013 rejected.

### Option C: Unified Pipeline + Lazy Linkage Weaving + Quality Flywheel (Chosen)

All heterogeneous sources funnel through one five-stage Content Processing Pipeline; cross-content edges are created lazily (on ingest and on query) rather than via upfront full-graph construction; a Quality Flywheel governs freshness, dedup, conflict, and retrieval evaluation.

## Decision

Adopt **Option C** (Unified Pipeline + Lazy Linkage Weaving + Quality Flywheel). This fills the three gaps above while fully respecting the existing PG-First, zero-CDC, confidence-priority-write foundations.

### 1. Content Processing Pipeline (five-stage unified funnel)

All content — regardless of source (Email SMTP / user upload DOCX-XLSX-PDF / API push / Excel import / paste) — passes through the same five deterministic-to-AI-assisted stages. Stage 1 reuses the existing parsing MCPs (MCP-11 email-parser, MCP-12 ocr, MCP-16 excel-parser); it does **not** duplicate them.

```
┌─────────────────────────────────────────────────────────────────────┐
│  Heterogeneous sources (all converge into one funnel)               │
│  Enterprise SMTP │ User upload DOCX/XLSX/PDF │ API push │ Paste      │
└──────────────────────────────┬──────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 1 — Parse & Normalize (deterministic, reuse existing MCPs)   │
│  .docx → Apache POI / Unstructured → structured text + tables +     │
│          heading hierarchy                                          │
│  .xlsx → MCP-16 excel-parser → tables + formula logic               │
│  .pdf  → PDFBox + Camelot → text + tables; scanned → MCP-12 OCR     │
│  email → MCP-11 email-parser → EmailRecord (per §12.1)              │
│  Output: ContentUnit { type, raw_text, structure, blob_ref }        │
│  Key: preserve structure (heading levels, table rows) — these are   │
│  the anchors used by linkage weaving in Stage 3 / §10.3             │
└──────────────────────────────┬──────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 2 — Semantic Chunking (structure-aware, not fixed-length)    │
│  • Split on structural boundaries (headings, paragraphs, row groups)│
│  • Tables stay intact as single chunks (never split across rows)    │
│  • Email: header = one chunk; body split by topic; each attachment  │
│    = independent chunk                                              │
└──────────────────────────────┬──────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 3 — Contextual Retrieval Enhancement (key quality uplift)    │
│  • For each chunk, a small model generates a short context summary  │
│    prepended to the chunk text before embedding.                    │
│    Example: "The following excerpt is from Chapter 3 of the         │
│    '2025 Q3 Gross Margin Analysis Report', discussing the East-     │
│    China margin decline."                                           │
│  • Industry evidence: this step alone reduces retrieval failure by  │
│    35%; combined with reranking by 67% (Anthropic, 2024).           │
│  • The same context summary is also indexed into the BM25 keyword   │
│    index (keyword retrieval benefits too, not only semantic).       │
└──────────────────────────────┬──────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 4 — Vectorize + Multi-Index Write (single ACID transaction)  │
│  • Embedding → pgvector HNSW index (semantic retrieval)             │
│  • Raw text + context summary → PG tsvector GIN index (BM25)        │
│  • Structured fields → PG native tables (exact metadata match)      │
│  • Relationship edges → PG edge tables (graph traversal, §10.3)     │
│  • Original blob → S3; PG row stores the object key                 │
│  All four indexes written in one ACID transaction (ADR-0013 zero-   │
│  CDC advantage — no synchronization window, no partial-write state) │
└──────────────────────────────┬──────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 5 — Provenance Tagging (immutable audit chain)               │
│  • Each chunk records: source_doc_id, source_span, ingest_time,     │
│    ingest_channel (email/upload/api), extractor, confidence          │
│  • Provenance classes align with ADR-0019:                          │
│      user_uploaded / email_received / api_pushed                    │
│  • Immutable + bitemporal — satisfies FR17.5 ("every KB fact traces │
│    to its source") and SOX audit requirements                       │
└─────────────────────────────────────────────────────────────────────┘
```

**How this integrates with existing ingestion channels** — Stage 1 is a *dispatch* layer over existing MCPs, not a replacement: Email Pipeline (§12.1) output flows into the same funnel after its own AI fact-extraction and human-confirmation gate; Sandbox Python code and Compute Specs enter via the code-ingestion events defined in ADR-0024. No existing pipeline is bypassed.

### 2. Linkage Weaving Layer (three linkage edges + conflict detection)

This layer answers: *how does heterogeneous content get connected so the Agent can reason across it?* Three linkage edge types connect content; one conflict edge type freezes contradictions. All four are generated by the strategies below, mapped to the existing Remediation Gateway tiers (ADR-0015 L0-L3). (The `CONFLICTS_WITH` edge and the Quality Flywheel's Conflict Detection stage describe the same mechanism from the edge-creation and governance perspectives, respectively.)

| Edge Type | Relation | Risk | Generation Strategy | Confirmation |
|---|---|---|---|---|
| **Entity Co-reference** | `MENTIONS_ENTITY` (chunk → GlossaryEntry) | Low (read-path use) | Small-model NER + KB entity matching (exact-first) + candidate disambiguation | High-confidence auto-created; low-confidence enters review queue |
| **Semantic Similarity** | `SIMILAR_TO` (chunk ↔ chunk) | Low | On ingest: vector near-neighbor query (top-5); similarity > 0.85 AND passes NLI non-contradiction check → edge created | Auto-created; dismissable from KB Governance Dashboard |
| **Structural Lineage** | `DERIVED_FROM` (ReportCell → ExcelRange → DataSource) | **High (audit-impacting)** | LLM proposes only; never auto-created — wrong lineage in financial scenarios is catastrophic | **Mandatory human confirm** (L2 approval) |
| **Conflict** | `CONFLICTS_WITH` (fact ↔ fact) | High | NLI contradiction detection between new and existing facts | Detected → marked `conflict` → **frozen, human adjudication** (ADR-0022 pattern generalized) |

**Why not full GraphRAG (Microsoft)?** The project's scale (~720K records) and PG-First / zero-CDC philosophy make full community-hierarchy construction a poor fit: it is LLM-expensive, hard to update incrementally, and re-introduces exactly the operational complexity ADR-0013 rejected. **Lazy edge creation** (created on ingest and on query, not via upfront full-graph build) is the engineering-appropriate middle ground — it delivers the "connect the dots" benefit of GraphRAG at a fraction of the cost and with incremental-update friendliness. Dedicated community detection can be introduced later only if a measurable retrieval-quality gap justifies it.

**Bridge edges to Code Graph** (cross-graph linking, extends §2.1):

```
KB.GlossaryEntry  —DEFINED_IN→  CodeGraph.Job
KB.DataAsset      —IS→           CodeGraph.DataSource
KB.Chunk          —MENTIONS_ENTITY→  KB.GlossaryEntry
KB.Chunk          —DERIVED_FROM→  CodeGraph.Spec   (lineage, L2-confirmed)
```

These bridge edges are what let the Agent in Scenario 6 (§22E) join "the email about gross margin" + "the Job that computes gross margin" + "the report that displays it" into one causal chain.

### 3. Quality Flywheel (closed-loop governance)

```
        ┌───────────────────────────────────────────┐
        │  New content ingested (Stages 1–5)        │
        └──────────────────┬────────────────────────┘
                           ▼
   ┌───────────────────────────────────────────────────┐
   │  Dedup                                              │
   │  • Content hashing (SimHash / MinHash) for near-    │
   │    duplicate detection                              │
   │  • Same email forwarded along a chain → merged into │
   │    one canonical record + reference list            │
   └──────────────────┬──────────────────────────────┘
                      ▼
   ┌───────────────────────────────────────────────────┐
   │  Conflict Detection                                 │
   │  • New fact vs existing KB fact → NLI contradiction │
   │  • Contradiction → marked conflict, frozen, human   │
   │    adjudication (never auto-overwrite)              │
   │  • This generalizes ADR-0022's BRD conflict pattern │
   └──────────────────┬──────────────────────────────┘
                      ▼
   ┌───────────────────────────────────────────────────┐
   │  Freshness Decay                                    │
   │  • Each chunk carries a half_life by content type:  │
   │    - Business definitions: long (2 years; expire    │
   │      only on explicit change)                       │
   │    - Data snapshots / report figures: short (30 d)  │
   │    - Email facts: medium (180 d)                    │
   │  • Fusion-ranking Freshness weight (S02 already     │
   │    has 0.10) scales with decay                      │
   │  • Beyond half_life → marked stale → triggers       │
   │    "still valid?" re-review                         │
   └──────────────────┬──────────────────────────────┘
                      ▼
   ┌───────────────────────────────────────────────────┐
   │  Retrieval Quality Evaluation (offline)             │
   │  • RAGAS-family metrics monitored: context_         │
   │    precision / context recall / faithfulness        │
   │  • Uses ADR-0018 Golden Dataset for A/B evaluation  │
   │  • Quality regression → triggers re-embedding or    │
   │    re-chunking of the affected domain               │
   └───────────────────────────────────────────────────┘
```

**Decay is not deletion.** Consistent with ADR-0019's bitemporal validity: old values are retained as historical version-chain entries (auditable), only down-ranked at retrieval time, never lost.

## Rationale

1. **Single funnel prevents quality fragmentation.** Per-channel pipelines (Option A) are the most-cited failure mode in 2025 production-RAG post-mortems (Databricks, Unstructured.io). A unified Stage 1–5 pipeline is the only way to guarantee uniform provenance, dedup, and linkage across all content types.
2. **Contextual Retrieval is the highest-ROI single technique.** Anthropic's 2024 study shows chunk-context loss is the dominant RAG failure mode; prepending an LLM-generated context summary cuts retrieval failures by 35% alone and 67% with reranking — far cheaper than swapping embedding models or scaling infrastructure.
3. **Lazy edge creation respects Boring Technology.** PG-First (ADR-0013) already gives us graph traversal via recursive CTE. Creating edges on-demand (on ingest + on query) delivers GraphRAG's "connect the dots" benefit without the LLM-expensive community-hierarchy build and its incremental-update difficulty. Full GraphRAG is reserved as a future option *only if* a measurable retrieval-quality gap justifies it — mirroring ADR-0013's four-gating-criteria discipline.
4. **Quality Flywheel prevents silent drift.** KB content without freshness decay and conflict detection degrades invisibly; the RAGAS evaluation loop (fed by ADR-0018's Golden Dataset) makes quality regressions visible and actionable before they affect users.
5. **Zero-CDC advantage is amplified.** Writing all four indexes (vector / keyword / relational / edge) in one ACID transaction — only possible because ADR-0013 chose PG-First — eliminates the entire class of "vector index updated but graph not yet synced" inconsistencies that plague multi-engine RAG systems.

## Consequences

- **Positive**: Uniform retrieval quality across all content types; heterogeneous content (email + DOCX + Excel + upload) becomes cross-queryable as one connected graph via linkage weaving; freshness decay keeps the KB from silently rotting; the RAGAS flywheel turns KB quality into a measurable, improvable metric. All of this is built on the existing PG-First stack with zero new stateful services.
- **Negative**: Stage 3 (Contextual Retrieval) adds one small-model LLM call per chunk at ingest time — a one-time cost amortized over every future retrieval of that chunk (favorable trade-off given Anthropic's measured quality uplift). Linkage weaving's L2-confirmation requirement for `DERIVED_FROM` edges adds human effort for high-stakes lineage, which is intentional and non-negotiable for financial auditability.
- **Neutral**: The Quality Flywheel's RAGAS evaluation is an offline batch job; its cadence (daily vs weekly per domain) is a tuning parameter, not a design decision. Half-life values per content type are configurable defaults, adjustable per tenant.

## Industry References

| Reference | Year | Key Insight |
|-----------|------|-------------|
| Anthropic — Contextual Retrieval | 2024 | Prepending an LLM-generated context summary to each chunk before embedding reduces retrieval failure by 35% alone, 67% with reranking — the single highest-ROI RAG technique |
| Microsoft — GraphRAG | 2024-2025 | Extracting a knowledge graph from text + community summaries enables "connect the dots" reasoning; but full community hierarchy is expensive and hard to update incrementally — motivating our lazy-edge variant |
| Unstructured.io — Production RAG Best Practices | 2025 | Production RAG requires a unified ingestion → chunking → retrieval → reranking pipeline; per-source ad-hoc pipelines are the top failure mode |
| Databricks — Unstructured Data Pipeline for RAG | 2025 | End-to-end unstructured-data-to-RAG pipeline guidance covering ingestion, processing, and quality gates |
| Atlan — Chunking Strategies for RAG | 2025 | Structure-aware (heading/paragraph/table) chunking outperforms fixed-length chunking; tables must stay intact |
| AWS — Securing the RAG Ingestion Pipeline | 2025 | Filtering mechanisms for untrusted external documents entering a RAG knowledge base — informs Stage 5 provenance and the §3.2 KB Content Sanitization layer |
| RAGAS / RAG Evaluation frameworks | 2024-2025 | context_precision / context_recall / faithfulness metrics enable offline retrieval-quality measurement, turning KB quality into a tunable metric |

## Linked Modules

- `docs/03-architecture.md` → §10.2 (Content Processing Pipeline), §10.3 (Linkage Weaving Layer), §10.4 (Quality Flywheel)
- `docs/03-architecture.md` → §10 (Knowledge Base domain table — adds domains 8 & 9 per ADR-0024, fixes missing 7th domain)
- `adr/0013-kb-storage-strategy.md` → PG-First storage foundation this ADR builds upon (Stage 4 single-transaction write exploits ADR-0013's zero-CDC advantage)
- `adr/0019-agent-memory-architecture.md` → Provenance tags (user_uploaded / email_received / api_pushed) align with provenance classification; bitemporal validity aligns with freshness decay
- `adr/0024-kb-reasoning-support-playbooks-code.md` → Code Knowledge domain ingestion reuses this pipeline's Stage 1–5 funnel
- `docs/01-facts.md` → Decision #22
- `docs/glossary.md` → Content Processing Pipeline, Contextual Retrieval, Linkage Weaving, Entity Linking, Freshness Decay
- `docs/02-requirement.md` → FR43 (KB Content Processing Pipeline), FR44 (KB Linkage & Quality)
