# Domain Services

> **Origin**: §12.1, §12.3, §12.4, §12.5, §12.7 of [`docs/03-architecture.md`](../../03-architecture.md) | **Sub-project**: [platform-core](README.md)

## Purpose

This module groups the platform-level domain services that are not owned by any single plane: the **Email Ingestion Pipeline** (FR17, §12.1), **Backup & Disaster Recovery** (FR41, §12.3), the **Notification Service** (FR37, §12.4), the **Runtime Dependency Manager** (FR40, §12.5), and the end-to-end **Data Flow Panorama** (§12.7). These services ingest external content into the Knowledge Base, protect platform data across stores, deliver notifications across channels, manage cross-workflow dependencies, and describe how user intent flows through Design → Freeze → Runtime. They are shared infrastructure consumed by workflow-engine, knowledge-services, agent-platform, and query-serving.

## Boundaries

**In-scope:**
- Email Ingestion Gateway, deterministic Parsing Engine, AI Fact Extraction, and Human Confirmation Gate (§12.1 / FR17).
- Per-store Backup & DR matrix, recovery procedure, and testing cadence (§12.3 / FR41).
- Notification Engine (Priority Router, Template Engine, Suppression Engine) and Channel Dispatcher (§12.4 / FR37).
- Dependency Discovery Engine and Dependency Services (topology, change-impact alerts, snapshots, deprecation, execution orchestration) (§12.5 / FR40).
- The Data Flow Panorama from User Intent through Runtime output sinks (§12.7).

**Delegated / out-of-scope:**
- **Observation Engine (§12.6 / FR3)** → [observability.md](observability.md).
- **Scheduler (FR39)** and **Workflow Executor mechanics** → workflow-engine sub-project (cross-referenced by Runtime Dependency Manager).
- **KB Write Pipeline (FR34)** and **Change Intelligence (FR28)** → knowledge-services / workflow-engine sub-projects (cross-referenced).
- **Operational backup/DR procedures and platform-level RPO/RTO** → [operational-architecture.md](operational-architecture.md) §24.1–§24.2 (this document holds the §12.3 per-store matrix).

**Upstream/downstream neighbors:**
- *Email ingestion*: External SMTP / user upload / paste → Ingestion Gateway → Parsing Engine → AI Fact Extraction → Human Confirmation Gate → KB Write Pipeline.
- *Backup & DR*: all data stores (PostgreSQL, Elasticsearch, S3/MinIO, Neo4j, Milvus/pgvector, Git, Vault) → cross-region backups → recovery procedure.
- *Notification*: Event Bus producers (Workflow Executor, Incident Manager, KB Governance, Scheduler, Freeze Bridge, Support/Ticket, User Actions, System) → Notification Engine → channels.
- *Runtime Dependency*: Compute Spec YAMLs → Code Graph `WORKFLOW_DEPENDS_ON` edges → Scheduler and Change Intelligence.

## Interfaces

### §12.1 Email Ingestion Pipeline (FR17) — stages

| Stage | Function |
| --- | --- |
| Ingestion Gateway | SMTP Server (`kb@[tenant].system.com`, per-tenant inbox); Rate Limiting (max 100 emails/hr per tenant); Spam/Phishing Filter → Quarantine; Attachment Size Limit (25MB per email, 100MB for upload) |
| Parsing Engine (Deterministic) | Structured extraction (From/To/CC/Date/Subject/Body/Attachment List); `.eml`/`.msg` parser (Apache James / custom); Attachment Router (`.xlsx`/`.xls` → Excel Table Recognizer; `.pdf` → PDF Text+Table Extractor via Apache PDFBox / Camelot; `.png`/`.jpg` → OCR via Tesseract + LLM vision). Output: Normalized `EmailRecord` (JSON). |
| AI Fact Extraction (LLM-Assisted) | Extraction types: NumericFacts, DateFacts, DefinitionFacts, DecisionFacts, RelationshipFacts, EntityFacts. Confidence scoring (High >0.9 / Medium 0.7–0.9 / Low <0.7) + source span annotation. Conflict detection → `CONFLICT` flag for human adjudication. Output: `List<ExtractedFact>` with confidence + source pointers. |
| Human Confirmation Gate | Per-user/per-tenant Extracted Facts Queue. Actions per fact: `[Confirm] [Edit & Confirm] [Dismiss (with reason)]`. Batch-confirm for high-confidence (>0.9). Confirmed facts → KB Write Pipeline (→ FR34); dismissed → logged for model improvement; unresolved after 7 days → auto-escalate. |

### §12.3 Backup & DR (FR41) — per-store matrix

| Layer | Component | Backup Method | RPO | RTO | Storage |
| --- | --- | --- | --- | --- | --- |
| **Core Data** | PostgreSQL (KB + Metadata) | Continuous WAL archiving + daily full snapshot | < 1 hour | < 4 hours | Cross-region S3 + Immutable (Object Lock) |
| **Search** | Elasticsearch (Hot Logs) | Daily snapshot to S3 | 24 hours | < 8 hours | Cross-region S3 |
| **Objects** | S3/MinIO (Warm/Cold Logs, Attachments, LLM Transcripts) | Cross-region replication (async) | < 1 hour | < 4 hours | Cross-region bucket |
| **Graph** | Neo4j (Code Graph + KB Relations) | Daily dump + CDC log replay | < 1 hour | < 4 hours | Cross-region S3 |
| **Vector** | Milvus/pgvector (Embeddings) | Derived from Relational DB → re-embed on restore | N/A (rebuildable) | < 8 hours | Relational DB backup → re-index |
| **Config** | Git Repository (Specs, KB, Formats) | Git is inherently distributed | < 5 min | Immediate (re-clone) | Multiple remotes |
| **Secrets** | HashiCorp Vault | Automated encrypted snapshot | < 1 hour | < 2 hours | Cross-region storage |

### §12.4 Notification Service (FR37) — engine components

| Component | Behavior |
| --- | --- |
| Event Producers | Workflow Executor, Incident Manager, KB Governance, Scheduler, Freeze Bridge, Support/Ticket, User Actions, System (via Event Bus / Kafka) |
| Priority Router | Critical → Instant; Warning → Digest; Info → Batch |
| Template Engine | Variable substitution; i18n localization; Rich HTML + Text |
| Suppression Engine | Deduplication (5min); Quiet hours per user; Rate limiting per channel |
| Channel Dispatcher | Email (SMTP), Slack/Teams, In-App Inbox, Webhook (custom), SMS (Twilio) |

Delivery Guarantee: At-least-once for Critical; best-effort for Info. Failure Escalation: Critical delivery fails → create Incident → try alt channel.

### §12.5 Runtime Dependency Manager (FR40) — services

| Service | Behavior |
| --- | --- |
| Dependency Discovery Engine | Static analysis of all Compute Spec YAMLs (`data_writer` write targets, `source` read targets, `workflow_ref` invocations) → match reads to writes → cross-workflow dependency DAG stored in Code Graph as `WORKFLOW_DEPENDS_ON` edges |
| Topology Visualization | DAG of cross-workflow data flows; filter by upstream/downstream, data source, team/owner; impact highlighting |
| Change Impact Alerts (→ FR28) | Upstream Workflow/Schema change → notify downstream owners with what changed, impact scope, suggested actions |
| Dependency Snapshot (per execution) | Record workflow version, data source schema version, execution time; answers "what version of X was used when Y ran on 2026-03-15?" |
| Deprecation Detection | Flag dependencies on deprecated/outdated workflows; suggest migration paths from KB Mapping Registry |
| Execution Orchestration (→ FR39 Scheduler) | On Workflow A completion → auto-trigger downstream Workflow B, conditional on A success AND output data meeting quality gate |

## Dependencies

- **Email Ingestion**: SMTP server, Apache James (`.eml`/`.msg`), Apache PDFBox / Camelot (PDF), Tesseract + LLM vision (OCR), KB Write Pipeline (FR34).
- **Backup & DR**: PostgreSQL WAL + PITR, Elasticsearch snapshot API, S3 cross-region replication + Object Lock, Neo4j dump + CDC, Vault snapshot, Milvus re-index from PG.
- **Notification**: Kafka/Event Bus, SMTP, Slack/Teams APIs, Twilio (SMS), webhook targets.
- **Runtime Dependency**: Compute Spec YAMLs, Code Graph (Neo4j), KB Mapping Registry, Scheduler (FR39), Change Intelligence (FR28).
- Cross-sub-project: knowledge-services (KB), workflow-engine (Executor, Scheduler), query-serving (data sources).

## Data Model

- **EmailRecord (JSON)** — normalized output of the Parsing Engine: From/To/CC/Date/Subject/Body/Attachment List.
- **ExtractedFact** — typed (Numeric/Date/Definition/Decision/Relationship/Entity) with confidence (High/Medium/Low), source span annotation, and optional `CONFLICT` flag. Confirmed facts enter the KB Write Pipeline.
- **Backup artifacts** — WAL archives, daily snapshots, Neo4j dumps, CDC logs, Vault encrypted snapshots; all on cross-region S3 with Object Lock.
- **Notification envelope** — event payload from producers, routed by priority, rendered through templates, dispatched to channels with dedup/rate-limit metadata.
- **`WORKFLOW_DEPENDS_ON` edges** — stored in the Code Graph; encode cross-workflow data-flow dependencies.
- **Dependency Snapshot record** — `(workflow_version, data_source_schema_version, execution_time)` per execution.

## Failure Modes & Recovery

| Failure | Impact | Recovery |
| --- | --- | --- |
| Email ingestion Gateway rate-limit/quarantine | Legitimate email quarantined | Quarantine review; rate limit tunable (100/hr/tenant). |
| AI Fact Extraction conflict / low confidence | Fact flagged `CONFLICT` or awaits adjudication | Human Confirmation Gate; batch-confirm >0.9; auto-escalate after 7 days. |
| Primary store failure (PG/ES/Neo4j/S3/Vault) | Data unavailability for that store | Per-store recovery procedure below; RPO/RTO per §12.3 matrix. |
| Critical notification delivery failure | Alert not received | Create Incident → try alternate channel (Failure Escalation). |
| Missed cross-workflow dependency | Downstream workflow runs on stale/missing data | Dependency Discovery DAG + change-impact alerts notify downstream owners; Snapshot enables forensics. |
| Deprecated workflow still referenced | Hidden technical debt | Deprecation Detection flags dependencies; suggests migration from KB Mapping Registry. |

### §12.3 Recovery Procedure

1. Restore PostgreSQL from latest snapshot + replay WAL to point-in-time.
2. Restore Elasticsearch from latest snapshot.
3. Restore Neo4j from dump + replay CDC log.
4. Re-index Vector DB from restored PostgreSQL (bulk embed).
5. Verify integrity: checksum validation on restored data.
6. Switch traffic to recovered stack.

**Testing Cadence**: Quarterly full recovery test; monthly partial (single-store) recovery test. All results auto-logged to Audit Trail.

For platform-level RPO/RTO by data tier (T0–T3) and DR failover procedure, see [operational-architecture.md](operational-architecture.md) §24.1–§24.2.

## Non-Functional Requirements

- **Email ingestion**: 100 emails/hr/tenant rate limit; 25MB per email (100MB upload); spam/phishing quarantine.
- **Backup RPO/RTO**: per the §12.3 matrix (PG <1h/<4h; ES 24h/<8h; S3 <1h/<4h; Neo4j <1h/<4h; Vector rebuildable/<8h; Git <5min/immediate; Vault <1h/<2h).
- **Notification**: At-least-once for Critical; best-effort for Info; 5min dedup; per-user quiet hours; per-channel rate limiting.
- **Dependency DAG freshness**: tracks Compute Spec changes; change-impact alerts aligned with KB sync lag SLO (<60s, §11.4).
- **Recovery testing**: Quarterly full; monthly partial (single-store).
- **Security**: backups encrypted AES-256 (SSE-KMS); immutable (Object Lock) for Core Data. See [docs/security/threat-model.md](../../security/threat-model.md) and [operational-architecture.md](operational-architecture.md) §24.1.
- **SLOs**: ingestion confirmation latency, notification delivery success rate — see [docs/operations/slo-sli.md](../../operations/slo-sli.md).

## Key Flows

### §12.1 Email Ingestion Pipeline (FR17)

```
External Email (SMTP)          User Upload (.eml/.msg)        Paste Body+Attachment
        │                              │                              │
        ▼                              ▼                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        INGESTION GATEWAY                                 │
│  • SMTP Server (kb@[tenant].system.com, per-tenant inbox)               │
│  • Rate Limiting (max 100 emails/hr per tenant)                         │
│  • Spam/Phishing Filter → Quarantine                                    │
│  • Attachment Size Limit (25MB per email, 100MB for upload)             │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        PARSING ENGINE (Deterministic)                    │
│  • Structured Extraction: From/To/CC/Date/Subject/Body/Attachment List  │
│  • .eml/.msg Parser (Apache James / custom)                             │
│  • Attachment Router:                                                    │
│    - .xlsx/.xls → Excel Table Recognizer (identifies data tables)       │
│    - .pdf       → PDF Text+Table Extractor (Apache PDFBox / Camelot)    │
│    - .png/.jpg  → OCR Pipeline (Tesseract + LLM vision for structured)  │
│  • Output: Normalized EmailRecord (JSON)                                 │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     AI FACT EXTRACTION (LLM-Assisted)                    │
│  • Prompt: "Extract objective facts from this email. Facts = numbers,   │
│    dates, definitions, decisions with stated rationale. Ignore opinions, │
│    predictions, and subjective language. For each fact, cite the source  │
│    sentence. Confidence: High (>0.9) / Medium (0.7-0.9) / Low (<0.7)." │
│  • Extraction Types: NumericFacts, DateFacts, DefinitionFacts,          │
│    DecisionFacts, RelationshipFacts, EntityFacts                         │
│  • Confidence Scoring + Source Span Annotation                          │
│  • Conflict Detection: if extracted fact contradicts existing KB entry  │
│    → flag CONFLICT, present both for human adjudication                 │
│  • Output: List<ExtractedFact> with confidence + source pointers        │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     HUMAN CONFIRMATION GATE                               │
│  • Workbench UI: Extracted Facts Queue (per user/per tenant)            │
│  • Each Fact: [Confirm] [Edit & Confirm] [Dismiss (with reason)]        │
│  • Batch confirm mode for high-confidence facts (>0.9, grouped)         │
│  • Confirmed facts → KB Write Pipeline (→ FR34)                         │
│  • Dismissed facts → logged with reason for model improvement           │
│  • Unresolved after 7 days → auto-escalate notification                 │
└─────────────────────────────────────────────────────────────────────────┘
```

### §12.4 Notification Service (FR37)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     EVENT PRODUCERS                                       │
│  Workflow Executor │ Incident Manager │ KB Governance │ Scheduler │     │
│  Freeze Bridge     │ Support/Ticket   │ User Actions   │ System    │     │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │ (Event Bus / Kafka)
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     NOTIFICATION ENGINE                                   │
│                                                                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │ PRIORITY ROUTER  │  │ TEMPLATE ENGINE  │  │ SUPPRESSION ENGINE      │  │
│  │ Critical→Instant │  │ Variable subst.  │  │ Deduplication (5min)    │  │
│  │ Warning→Digest   │  │ i18n localization│  │ Quiet hours per user    │  │
│  │ Info→Batch       │  │ Rich HTML+Text   │  │ Rate limiting per chan. │  │
│  └────────┬─────────┘  └────────┬─────────┘  └───────────┬─────────────┘  │
│           └──────────────────────┼────────────────────────┘               │
│                                  ▼                                        │
│                     CHANNEL DISPATCHER                                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │  Email    │ │  Slack/  │ │  In-App  │ │ Webhook  │ │  SMS     │       │
│  │ (SMTP)   │ │  Teams   │ │ Inbox    │ │ (custom) │ │ (Twilio) │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────────────────┘

Delivery Guarantee: At-least-once for Critical; best-effort for Info
Failure Escalation: Critical delivery fails → create Incident → try alt channel
```

### §12.5 Runtime Dependency Manager (FR40)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     DEPENDENCY DISCOVERY ENGINE                           │
│  • Static Analysis: Parse all Compute Spec YAMLs → extract:              │
│    - data_writer jobs → which table/key they write to                   │
│    - source jobs → which table/key they read from                       │
│    - workflow_ref jobs → which Workflows they invoke                    │
│  • Match reads to writes → build cross-workflow dependency DAG          │
│  • Store in Code Graph: edges of type WORKFLOW_DEPENDS_ON               │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     DEPENDENCY SERVICES                                   │
│                                                                          │
│  TOPOLOGY VISUALIZATION:                                                 │
│  • DAG showing all cross-workflow data flows                             │
│  • Filter by: upstream/downstream, data source, team/owner              │
│  • Impact highlighting: "if this workflow changes, these are affected"   │
│                                                                          │
│  CHANGE IMPACT ALERTS (→ FR28 Change Intelligence):                      │
│  • Upstream Workflow/Schema change → notify all downstream owners       │
│  • Alert includes: what changed, impact scope, suggested actions        │
│                                                                          │
│  DEPENDENCY SNAPSHOT (per execution):                                    │
│  • Record: workflow version, data source schema version, execution time │
│  • Enables: "what version of X was used when Y ran on 2026-03-15?"      │
│                                                                          │
│  DEPRECATION DETECTION:                                                  │
│  • Flag dependencies on deprecated/outdated workflows                   │
│  • Suggest migration paths based on KB Mapping Registry                 │
│                                                                          │
│  EXECUTION ORCHESTRATION (→ FR39 Scheduler):                             │
│  • When Workflow A completes → auto-trigger downstream Workflow B       │
│  • Conditional: only if A succeeded AND output data meets quality gate  │
└─────────────────────────────────────────────────────────────────────────┘
```

### §12.7 Data Flow Panorama

```
User Intent (Natural Language/Manual Operation)
         │
         ▼
   Design Plane
   (AI Copilot + KB → Generate Compute Spec Draft)
         │
   User Review + Modify
         │
         ▼
   Freeze Bridge
   (Refinement → Validation → Testing → Impact Report → Review)
         │
         ▼
   Runtime Plane
   (Scheduler → Executor(Sandbox) → Heavy Engine → Output)
         │
         ├──→ Output Renderer → PDF/Excel/Dashboard/Email
         ├──→ Data Writer → Write back to data source (DB/Cache/Data Lake)
         ├──→ Log System → Structured logs → AI analysis
         ├──→ KB (Behavior Pattern / Adjustment History)
         └──→ Code Graph (Update execution status)
```

## Design References

- **Original sections**: §12.1 (FR17), §12.3 (FR41), §12.4 (FR37), §12.5 (FR40), §12.7 of [`docs/03-architecture.md`](../../03-architecture.md).
- **Related platform-core docs**: [observability.md](observability.md) (§12.6), [operational-architecture.md](operational-architecture.md) (§24 backup/DR/retention), [cross-cutting-layer.md](cross-cutting-layer.md) (§11).
- **ADRs** ([index](../../adr-index.md)): [ADR-0011 Materialize Job Type](../../../adr/0011-materialize-job-type.md), [ADR-0023 KB Content Lifecycle Pipeline](../../../adr/0023-kb-content-lifecycle-pipeline.md), [ADR-0025 Unified Workflow Engine](../../../adr/0025-unified-workflow-engine.md).
- **Glossary** ([../../glossary.md](../../glossary.md)): Compute Spec, Heavy Engine, Light Engine, Freeze Pipeline, Production Environment, Cross-Environment Read-Only Mode.
- **External procedures**: [docs/operations/backup-dr.md](../../operations/backup-dr.md), [docs/operations/slo-sli.md](../../operations/slo-sli.md), [docs/security/threat-model.md](../../security/threat-model.md).
