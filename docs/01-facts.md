# 01 - Facts & Background

> Records project background, confirmed facts, and key decisions. This document should be continuously updated throughout the design process.
>
> ⚠️ **Note**: There is a timeliness risk between the main body of this document and supplementary sections added later. The main body should be treated as the authoritative source and periodically reviewed; supplementary sections may become outdated as the design iterates. If contradictions arise, the main body takes precedence.
>
> **📋 Related Documents**: Requirements → [02-requirement.md](02-requirement.md) | Architecture → [03-architecture.md](03-architecture.md) | Roadmap → [04-timeline.md](04-timeline.md) | Cost → [05-cost.md](05-cost.md) | Glossary → [glossary.md](glossary.md) (101 terms) | ADR → [adr/](../adr/) (24 records)

---

## Project Background

- **Sponsor Background**: A financial accounting practitioner who handles financial report generation, ETL data pipelines, and accounting adjustments (adjustment entries) on a daily basis.
- **Project Vision**: Design a general-purpose data analysis / BI tool for the LLM era. The long-term goal is to replace previous-generation products such as Excel and PowerBI.
- **Project Positioning**: A comprehensive design project — covering technical architecture, product design, and methodology.

## Industry & Technology Premises

### LLM Current State Awareness
- **Assumption**: Continued improvement in LLM capabilities is the high-probability trend, but drift and hallucination issues (unreliable reasoning) still exist today.
- Invoking an LLM for every task leads to cost explosion.
- LLM success rates for data inference are limited (structured data inference accuracy ~60-70%, complex business metric inference below 50%, based on industry experience estimates, not rigorous experimental data). Human-provided additional context is required.
- **Therefore**: LLMs are suitable for the exploration phase, not suitable for direct use in production deterministic tasks. This does not mean AI is completely absent in production — the Intelligence Plane provides AI read-only analysis (ad-hoc Q&A, attribution analysis), with answers returned directly to the user and not written into system state, achieving "zero AI side effects" rather than "zero AI participation."

### Enterprise Environment Constraints
- Enterprise users have strict **SDLC process** and **entitlement control** requirements.
- Various industries have strict **regulation requirements** (SOX, HIPAA, GDPR, etc.).
- Enterprise environments contain many legacy systems that the new system needs to integrate/interact with.
- Enterprises use diverse authentication systems: OAuth, Kerberos, SSO, etc.

## Core Design Philosophy (Confirmed)

### Flexibility During Exploration → Deterministic After Maturation
- Users can freely explore, use natural language interaction, and receive AI assistance during the exploration phase.
- Once a flow is validated and proven correct → one-click "freeze" into a deterministic script.
- After freezing, no LLM inference dependency → zero hallucination, low-cost execution.
- **Freeze is reversible**: Freezing is not a one-way irreversible operation — you can "unfreeze" at any time to return to exploration mode, modify, and re-freeze, supporting iterative evolution.
- **Freeze Bridge**: The core architectural component connecting the Design Plane and Runtime Plane. Its responsibility is to assist in transforming AI exploration artifacts into deterministic scripts — not auto-compilation. Flow: scan fuzzy nodes → propose deterministic solutions → **mandatory human Sign-off** → validate → test → approve → deploy.

### System Observation + Proactive Suggestions
- The system observes user repeatable operation patterns.
- Proactive suggestion: "Detected a repeatable pattern, would you like to create a reusable workflow?"
- User operational behavior is a source of requirements mining.

### Human-in-the-loop Knowledge
- Users explicitly provide: data source mappings, business metric definitions, table relationships, adjustment rules.
- The system does not blindly guess; it reasons on a foundation of trusted knowledge.
- The more background information the user provides, the higher the AI's accuracy.

### Knowledge Base as System Foundation
- Storage: business semantics, data dictionary, historical adjustment reasons, workflow templates.
- Compute layer: LLM (reasoning/generation); Storage layer: PostgreSQL + pgvector (Vector + Graph + Relational unified) + S3/MinIO (Object Store). Dedicated engines (Milvus/Neo4j) are reserved via interface abstraction and introduced only when four gating conditions are met.
- New requests first retrieve relevant knowledge before reasoning, significantly improving accuracy.

## Key Design Decisions

> The following decisions use ADR (Architecture Decision Record) summary format. Complete ADRs (MADR format with Context / Options / Decision / Rationale / Consequences / Linked Modules) are in the `adr/` directory.

### Decision #1: AI Positioned for Exploration, Deterministic for Production
- **Status**: Accepted (2026-07-04)
- **Background**: LLMs are creative but unreliable — multiple runs on the same input can produce different results. Financial-grade production requires determinism and auditability. The project must leverage LLM capabilities without creating hallucination risks.
- **Decision**: Strictly separate Design Plane (AI-assisted exploration, free-form interaction) and Runtime Plane (deterministic script execution, zero LLM dependency). The Freeze Bridge converts AI-assisted designs into deterministic scripts with mandatory human sign-off — no auto-compilation.
- **Alternatives Considered**: End-to-End AI pipeline (Rejected: LLM hallucination in production financial data is unacceptable); Pure traditional approach (Rejected: misses the LLM era entirely)
- **Consequences**: Dual-plane architecture increases system complexity; Freeze Bridge becomes a critical conversion component; Intelligence Plane provides AI read-only ad-hoc Q&A and attribution without crossing the bridge
- **References**: → 03-architecture §2, §4, §5, §7, §8

### Decision #2: Separation of Concerns — Design Plane, Freeze Bridge, Runtime Plane, Intelligence Plane
- **Status**: Accepted (2026-07-04, Refined 2026-07-04)
- **Background**: Need for clear operational boundaries between exploration and production to prevent AI side effects from entering the deterministic Runtime Plane.
- **Decision**: Four independent planes with strict separation: Design Plane (AI-assisted authoring, all artifacts are drafts), Freeze Bridge (scans → proposes → requires human sign-off, not automatic), Runtime Plane (deterministic, zero AI side-effect production execution), Intelligence Plane (read-only AI analysis across Design and Runtime Planes, ad-hoc Q&A + attribution, answers return to the user without bridging to Runtime)
- **Consequences**: Freeze Bridge is an independent transition plane, not a simple pipeline; Intelligence Plane ensures AI has read-only production visibility
- **References**: → 03-architecture §2

### Decision #3: Compute Spec (YAML) as Unified IR
- **Status**: Accepted (2026-07-04)
- **Background**: Reporting, ETL, Adjustment are traditionally treated as independent products. However, at the computation level, all three share a common structure: data source → transform → output. Unifying them can reduce complexity and achieve unified versioning, testing, and deployment.
- **Decision**: Use YAML-based Compute Spec as the unified computation definition. Reporting, ETL, and Adjustment all describe computation logic through Compute Spec, each differing only in Job Type and rendering layer.
- **Alternatives Considered**: Independent specifications per domain (Rejected: triples maintenance cost); JSON format (Rejected: no comment support, code embedding requires escaping)
- **Rationale**: YAML supports comments, human-readable; code embedding doesn't require escaping; industry direction (GitHub Actions, Kubernetes, Ansible, etc. all use YAML)
- **Consequences**: Need to design unified Job Type system; Format System handles rendering layer differences; Version control applies uniformly
- **References**: → 03-architecture §3.2, §6

### Decision #4: AI Knowledge Agent — read-only, never writes
- **Status**: Accepted (2026-07-04)
- **Background**: AI Agents have powerful reasoning capabilities but granting write access to Agents carries risk. In a financial environment, every write must be auditable.
- **Decision**: AI Knowledge Agent can only read KB, Code Graph, and logs; answers natural language queries; performs attribution analysis — but NEVER directly writes to any system state. All write operations go through human confirmation in the Design Plane. Intelligence Plane output directly returns to the user, temporary answers don't cross the bridge.
- **Consequences**: AI Knowledge Agent is purely a "consultant" — can answer "why is there a Recon break" but can't modify adjustment rules
- **References**: → 03-architecture §9.3, §22

### Decision #5: Python as Logic Script Language
- **Status**: Accepted (2026-07-04)
- **Background**: Need to choose a language for transform logic in Compute Spec. It must be LLM-generation-friendly and also production-ready.
- **Decision**: Python is the logic script language (not Java): dominates the data ecosystem, LLM-generated Python quality is higher, analysts can read and write it. Runtime Plane execution engine can be implemented in Go/Rust for performance and isolation. Hybrid mode: Python (logic) + SQL (queries) + YAML (orchestration definition).
- **Alternatives Considered**: Java (Rejected: data ecosystem not dominant, verbose); SQL only (Rejected: can't express complex transform logic; still use SQL for data queries)
- **Consequences**: Multi-language hybrid architecture; Compute Engine needs embedded Python runtime; Runtime Plane may need transpile/compilation
- **References**: → 03-architecture §6, §7.2

### Decision #6: PG-First Knowledge Base Storage
- **Status**: Accepted (2026-07-04)
- **Background**: KB covers 9 domains with different retrieval patterns, but introducing dedicated engines too early adds operational complexity.
- **Decision**: MVP uses PostgreSQL + pgvector for all three roles (Vector/Graph/Relational) + S3/MinIO for Blob. Dedicated engines (Milvus/Neo4j) reserved via interface abstraction, introduced only when four gating conditions are met.
- **Consequences**: Unified operational model; pgvector may have ceiling on vector recall at 100M+ scale; design includes clean migration path
- **References**: → 03-architecture §11

### Decision #7: Design Order — Architecture First, KB Co-Evolution
- **Status**: Accepted (2026-07-04)
- **Background**: Designing a complex system requires clear priorities and dependency relationships to avoid "draw the UI first, patch the architecture later." The timing of building the Knowledge Base has significant impact on design quality.
- **Decision**: Architectural Blueprint → Core Engine → Thin KB + Basic Design Plane evolving in parallel (KB starts from PG+pgvector, Design Plane user interactions drive organic KB growth) → Full KB. This explicitly rejects UI-first and full-parallel approaches.
- **Alternatives Considered**: UI First → Engine Later (Rejected: castles in the air); Full Parallel (Rejected: strong inter-module dependencies)
- **Consequences**: Phase 0-3 roadmap follows this order; KB starts thin and grows organically; Design Plane exploration directly feeds KB enrichment
- **References**: → adr/0003-design-order.md, 04-timeline §Phases 0-3

## Three Core Concepts

> **Cross-Cutting Capabilities**: Reconciliation and Data Quality Check are cross-cutting capabilities spanning all three core concepts — Reporting depends on DQ for output trustworthiness, ETL embeds DQ checkpoints at each step, and Adjustment is often triggered by differences discovered through Reconciliation. See supplemental sections below.

### Reporting
- Traditional: define data sources → select fields → configure aggregations → format → publish.
- New Model: user describes intent → AI assists in locating data / generating visualizations → user reviews / fine-tunes → freeze and publish.
- Advanced: AI proactively pushes anomaly insights.

### ETL Workflow
- Traditional: ETL engineers code/configure data extraction → transformation → loading.
- New Model: AI assists in discovering data sources → infers schema → intelligent mapping → user confirms → frozen script.
- Key: complex transform logic is drafted by AI, reviewed by humans, then frozen.

### Adjustment
- Traditional: manually create adjustment entries, note reasons, go through approval.
- New Model: AI detects anomalies → reasons with KB context (metric differences? data entry errors? exchange rate fluctuations?) → suggests adjustment proposals → auto-generates audit trail → human approval.
- Key: complete reason chain is retained.
- Trigger Sources: Adjustments can be auto-triggered by Reconciliation (recon breaks), triggered by DQ Check anomaly detection, or manually initiated by users.

## Key Insights Record

1. **"LLM is suitable for exploration, not production"** — This is the core contradiction of the entire design, and also the differentiator.
2. **"Not replacing people, making people more efficient"** — Workflow execution is deterministic after freezing; this is the foundation of enterprise trust.
3. **"Knowledge-driven > Data-driven"** — Rather than letting AI guess data meanings, let users provide knowledge.
4. **"Compliance is not a feature, it's a foundation"** — Must be built in from day one.
5. **"Export as standard"** — All data, scripts, and audit records need to be exportable as standard file formats.

---

## 2026-07-04 Supplemental Decisions

> **Note**: Decisions #3 and #5 are restated here for supplemental context; see the Key Design Decisions section above for the primary record.

### Script Language Selection
- Python as logic script language (not Java): dominates the data ecosystem, LLM-generated Python quality is higher, analysts can read and write.
- Runtime Plane execution engine can be implemented in Go/Rust for performance and isolation.
- Hybrid mode: Python (logic) + SQL (queries) + YAML (orchestration definition).

### Unified Compute Definition: Compute Spec (YAML)
- Core Insight: Reporting, ETL, and Adjustment can share a single compute definition.
- Format selection: YAML (not JSON): supports comments, code embedding without escaping, industry-standard direction.
- Engine-independent design: the same YAML spec → Design Plane uses Light Engine → Runtime Plane uses Heavy Engine.
- The system internally uses a standardized data structure; YAML/JSON are just serialization formats.

### Dual-Engine Compute Strategy
- **Light Engine (Design Plane)**: DuckDB (zero-config, sub-second startup for sampled data) + Polars (high-performance DataFrame for in-memory transformation).
- **Heavy Engine (Runtime Plane)**: Spark (Post-MVP for production, large-scale scenarios); Trino (MPP for federated queries across heterogeneous sources) and Ray (distributed Python for ML-heavy transforms) deferred to Phase 7+ evaluation.
- **Core Principle**: Same Compute Spec (using Common Compute Subset), Light for development, Heavy for production. Workflows containing Python transforms must be transpiled before Heavy Engine execution (see Architecture §6.1).

### Multi-Tenancy & Data Masking
- Three-tier permission hierarchy (Tenant → Group → Role).
- Static masking (storage layer) + Dynamic masking (inject masking functions at query time based on role).
- Runtime Plane's Query Rewriter is responsible for permission predicate injection and data masking.

### Legacy System Integration
- Five-level integration framework: File-Based → DB Protocol → API/Service → Message/Stream → Custom Plugin.
- Unified DataSource Interface: connect → discover → query → write.
- Don't need native support for every legacy system, just cover common integration methods.

---

## 2026-07-04 Supplement: Knowledge Base Detailed Design

### KB Nine Knowledge Domains (+ Email Records as cross-domain storage)

| # | Domain | Description |
|---|--------|-------------|
| 1 | **Business Glossary** | Terms, aliases, definitions, formulas, business context, data source mappings, owner, approval source, version |
| 2 | **Data Catalog** | Data asset metadata (tables/APIs/files/streams), Schema details, column-level business meaning, PII markers, relationships, quality scores, usage statistics |
| 3 | **Mapping Registry** | Legacy → new system field mappings, cross-currency conversion rules, transform logic (reversible), change history |
| 4 | **Workflow Template Library** | Template definitions, categorization, prerequisite KB requirements, parameters, usage statistics, ratings |
| 5 | **Adjustment History** | Anomaly details, root cause analysis (primary + secondary + residual), adjustment entries, approval chain, immutable at point-in-time |
| 6 | **User Behavior Pattern Store** | Operation sequences, temporal patterns, derived suggestions, confidence scores |
| 7 | **Report/Metric Catalog** | Report definitions, metric formulas, calculation granularity, certification status, relationships with data sources and Workflows |
| 8 | **Diagnostic Playbooks** *(ADR-0024)* | Expert-encoded diagnostic decision trees (IF/THEN investigation paths) acting as a "soft skeleton" for Agent reasoning in Exploration Mode — the read-only counterpart to Verified Paths. Three sources: system-builtin / incident-distilled / user-defined |
| 9 | **Code Knowledge** *(ADR-0024)* | Three-layer index over code artifacts (Compute Spec YAML, Sandbox Python, Git history, external repos): structural (Code Graph nodes/edges), semantic (function-level embeddings), change (commits/blame/diffs). Enables semantic code search and code-logic reasoning |

### KB Storage Architecture
- **Vector DB** (semantic retrieval): All entities produce Embeddings; supports hybrid search (semantic + keyword + metadata filtering).
- **Graph DB** (relationship reasoning): KB internal relationships + KB↔Code Graph bridge edges. Edge types: RELATED_TO, MAPS_TO, TRANSFORMS, REFERENCES, EXTRACTED_TO, REQUIRES.
- **Relational DB** (structured metadata): Complete JSON documents, version history, permission mappings, approval records.
- **Object Store** (large objects): Email .eml, attachments, LLM Prompt/Response full text, archived Workflow Specs.

### KB Write Paths (three paths) → FR34
1. **User Explicit Input** (confidence 1.0): Schema scan during Onboarding, Workbench sidebar "Add to KB", AI conversation confirmations.
2. **AI Extraction + Human Confirmation** (confidence 0.7-0.95): Email fact extraction, Data Profiling inference, Adjustment pattern learning.
3. **System Automatic** (confidence tagged, overridable): behavior observation → BehaviorPattern, workflow freeze → template extraction, DQ results → quality score, execution logs → usage statistics.

All writes pass five gates: Permission Check → Versioning → Notification → Embedding Update → Graph Update.

Write conflict resolution: (a) User explicit input is highest priority, overwrites AI-extracted and system content; (b) AI-extracted content with confidence ≥0.9 auto-overwrites system content with lower confidence, prompts user for confirmation if conflicting with other AI extractions; (c) System auto-content is lowest priority; (d) All overwrite/merge operations are recorded as a new version in KB version history.

### KB Read Paths (Hybrid Retrieval Four Steps) → FR35
1. Semantic Search (Vector DB, top_k=20).
2. Keyword Filtering (tenant/domain/status/date metadata).
3. Relationship Expansion (Graph DB traverse related nodes).
4. Fusion Ranking → inject into AI Prompt as context.

### KB Governance
- Each entry has independent version history; changes are traceable.
- Glossary/Mapping changes require Business Owner approval + auto-notify affected Workflow Owners.
- Auto-detect Staleness (over 6 months without update → mark, Schema change → mark related, Pattern mismatch → lower Confidence).
- KB↔Code Graph inconsistency triggers auto-alert.

### KB & Code Graph Relationship
- Code Graph stores system structure (Workflow → Job → DataSource DAG).
- KB stores the business semantic layer (business meaning of data sources, metrics, mapping rules).
- The two are linked via bridge edges: KB.DataAsset IS CodeGraph.DataSource, KB.GlossaryEntry DEFINED_IN CodeGraph.Job.

---

## 2026-07-04 Supplement: Job Model / Format / Writer / Sandbox / Log / Change Intelligence

### Compute Spec YAML — Complete Job Model
- Workflow = an ordered set of Job Groups → each Group = an ordered set of Jobs with shared defaults (concurrency, retry policy, SLA, on_failure).
- 9 Job Types: `source`, `transform`, `output`, `quality`, `workflow_ref`, `data_writer`, `decision`, `wait`, `materialize`.
- Dependencies between Groups specified via `depends_on`; within a Group, Jobs execute sequentially with shared defaults.
- Variables (runtime-injected, e.g., date ranges — cannot change DAG topology) vs Parameters (config-level, e.g., connection strings).

### Format System
- Global Format definitions decoupled from Jobs, supporting reuse.
- Format types: Report (page layout, header/body/footer, conditional_format, sorting, charts), Excel (multi-sheet, frozen panes, auto_filter, pivot_table, sparkline), Dashboard (kpi_card, heatmap, trend widgets), Data Export (parquet/csv/json, compression, partition_by), writeback (destination connector, write_mode, transaction).

### Writer Job Type
- Writes computed results to data sources registered in the Data Catalog (DB/Cache/File).
- write_mode: append | upsert | overwrite | merge. Transactional writes (all-or-nothing) with pre-write checks + post-write verification.

### Execution Sandbox
- Each Job executes in an isolated Sandbox: CPU/Mem/Disk/Net resource isolation + FS/Network/seccomp security boundaries.
- Sandbox Pool with pre-warming; directory structure: /workspace/, /input/, /output/, /secrets/.
- Network whitelist (allowed hosts/ports only); seccomp profile (restrict syscalls); SaaS mode enforces network isolation per tenant.
- Design Plane uses lightweight Sandboxes (DuckDB/Polars, second-level startup, sampled data).
- Sandbox lifecycle: Acquire → Inject → Execute → Collect → Verify → Release.

### Log System (AI-Era Logging)
- **Structured Event Log**: unified Schema, all system events include event_id, timestamp, type, tenant, workflow, job, actor, data, result, error.
- **Execution Trace**: detailed per-step metrics (rows read/written, duration, memory), integrated with OpenTelemetry.
- **LLM Interaction Log**: each LLM call records prompt_hash, kb_retrieved, tokens, cost, latency, outcome, with Prompt/Response full text stored in Object Store (cold/hot configurable).
- **AI-Powered Log Analysis**: real-time anomaly detection, auto Incident Diagnosis Assistant, Cost Tracking Dashboard.
- **Tiered Storage**: Hot 7 days (ES real-time query) → Warm 90 days (S3+Parquet) → Cold 7 years (Glacier compliance retention). Sampling, truncation, and aggregation for cost control.

### Change Intelligence System
- **Pre-Change Impact Report**: auto-generated on Freeze/PR, includes Diff, scope of impact, data impact preview, test results, Approver list.
- **Post-Change Summary**: auto-generated after Merge, includes actual vs. design comparison, DAG visualization (change nodes highlighted), Change Log, linked documentation (BRD/ADR/KB/Incident), Cost Profile.
- **AI Knowledge Agent**: answers any system question based on Code Graph + KB + Log (business logic, code logic, data flow, dependencies, history, incidents).
- **Underlying Infrastructure — Code Graph**: Nodes (Workflow/Job/DataSource/KB/BRD/ADR/User/Tenant/Jira/Incident) + Edges (DEPENDS_ON/READS_FROM/WRITES_TO/IMPLEMENTS/JUSTIFIED_BY/OWNED_BY/TRIGGERS etc.). Continuously incrementally updated; triggers Commit/Freeze/Merge events.

---

## 2026-07-04 Supplement: Email Ingestion / Recon / Data Quality

### Email → Knowledge Base Information Extraction
- System provides dedicated inbox (kb@[tenant].system.com); supports forwarding rules + manual .eml/.msg uploads + paste body.
- Structured parsing: From/To/CC/Date/Subject/Body + attachment extraction.
- AI extracts objective facts (numbers, dates, definitions, decisions); Excel attachments → tables, PDF → text, images → OCR.
- Information is not stored in KB until confirmed; explicit Confirm/Edit/Dismiss flow.

### Definition & Boundaries of Objective Facts
- Only extract "objective facts," not "subjective judgments." If the AI can't distinguish, mark as AMBIGUOUS.
- Facts are always traceable to source emails. If two emails conflict, mark as CONFLICT → surface to user.

### Reconciliation
- As a `type: recon` check in the unified Data Health Check Framework, YAML-configuration driven.
- Define Match Key + Tolerance Profile for two data sources (configurable by account type, materiality threshold, region — not fixed three-tier).
- Post-execution auto-classification: Matched / Unmatched / Partial.
- AI + KB reasoning for break causes (TIMING/MISSING/ROUNDING/MAPPING/CURRENCY/DUPLICATE/UNKNOWN).
- All finance-related Resolution suggestions must go through the Adjustment pipeline (Permission → Validation → Approval → Trigger ETL). No Auto-write-off.
- Recon Check itself can be frozen as a Compute Spec into a reusable Workflow. Recon Report exportable + stored in KB (Adjustment History domain).

### Data Quality Check
- As a `type: rule` check in the unified framework. 7 DAMA-standard dimensions: Completeness, Accuracy, Consistency, Timeliness, Uniqueness, Validity (+ Temporal Consistency as 7th dimension).
- 7th dimension: Temporal Consistency — detects ratio jumps across time, cumulative consistency issues (e.g., Line 3 vs. Line 12 accumulated validation).
- Three severity levels: Error (blocks Freeze Bridge or Runtime Pre-Exec) / Warning (annotates Report, doesn't block) / Info (log only).
- Output: Annotated Report (row-level anomaly marking + root cause summary + confidence). Does not block report publication.
- Users can click anomaly annotations → ask AI Agent (root cause analysis) → optionally create BRD → push to Jira/Rally/ServiceNow.

---

## 2026-07-04 Supplement: AI Agent Architecture / Permissions / Customization

### AI Agent Technical Architecture → FR29
- Agent uses LLM SDK + Skill + MCP three-layer architecture.
- **LLM SDK**: Pluggable layer with unified interface for switching between OpenAI/Anthropic/open-source/private models.
- **Skill Module**: Intent Parsing / KB Retrieval / Code Graph Query / Impact Analysis / Doc Generation — 18 Skills (S01-S18) planned, composable.
- **MCP**: Model Context Protocol — standard protocol for Agent interaction with external systems. 21 MCP Servers planned (18 in §22C Core Catalog: MCP-01..17 + MCP-23; plus 3 BRD-pipeline MCPs in §23.8.2: MCP-20 jira-sync, MCP-21 confluence-export, MCP-22 compliance-mapper).
- Skills can be composed into Agent Workflows (templated Skill combinations + System Prompt).

### Agent Customization
- Different Teams/Owners can pre-define multiple sets of Agent Workflows (e.g., Finance Team's "metric inquiry + adjustment suggestion").
- Agent Workflow as a Compute Spec type (meta-workflow), naturally inheriting FR8.1 version control and all FR13 Compute Spec capabilities.
- Supports different users/Teams connecting to different AI Models. Model selection three-layer preference: Tenant-level / Group-level / Individual-level. Models configurable by scenario: sensitive data uses private models, general Q&A uses SaaS models.

### Agent Permission Control (Role-Based Agent Capability)
- Agent capabilities are dynamically trimmed based on user role.
- Dev role: can query Code Graph + Log + ADR + Incident; cannot query Business Data (sales/customer data, etc.).
- Business User role: can query KB metrics + reports + data previews; cannot modify Compute Spec code.
- Reviewer role: can view full Impact Report + approve; cannot directly modify.
- Agent injects user permission context before each response, filtering invisible content.
- Agent actions (create Ticket, trigger Workflow) require operation permission checks.

---

## 2026-07-04 Supplement: DevOps / Support / Ticket / Tracking / BRD / ADR

### DevOps & CI/CD
- Pipeline: Develop → Build → Test (Lint + Static Analysis + Unit + Integration) → Review → Staged Rollout (Canary 10% → 50% → 100%) → Monitor → Deprecate.
- Compute Spec / Workflow Script versioned through Git; Sandbox environments auto-created/destroyed per PR/Branch; Infrastructure as Code manages Runtime Plane resources.
- Runtime Monitoring: Success Rate, Duration (P50/P95/P99), Data Volume Delta, Data Quality Score, SLA Compliance.
- Alert Rules: execution failure → immediate alert + auto Incident; data deviation >20% → Warning; latency >2x SLA → Warning.

### Support & Service Ticket
- Three-tier support system: L1 Self-Service (embedded Help Panel + KB search + AI troubleshooting) → L2 Ticket (auto/manual creation) → L3 Engineering Escalation (auto-create Jira Bug).
- Execution failures auto-generate Tickets with context: Workflow ID, error logs, data snapshots, recent changes, impact scope.
- Built-in lightweight Ticket System (out-of-box) + external Jira Service Management / ServiceNow / Zendesk (Webhook bidirectional sync).
- Tickets bidirectionally linked with Workflow / Compute Spec.

### Jira / Rally Integration
- Full traceability chain: BRD → Epic → User Story → Compute Spec → PR → Deployment → Prod.
- Auto-comment on Jira Story on PR commit; auto-update Story status to Done upon Prod deployment.
- Reverse traceability from Workflow: related requirements → Epic → BRD.

### BRD & ADR
- BRDs are not Word documents — they are structured system entities, bidirectionally linked to Workflows.
- BRD changes auto-flag affected Workflows (Impact Analysis).
- ADRs record architecture decisions: Context → Options → Decision → Rationale → Consequences → Linked Modules.
- ADRs bidirectionally linked with modules (view impact from decision, view basis from module).
- BRD ↔ ADR ↔ Workflow triangle traceability.
- BRD/ADR exportable as standard document formats.

### BRD/ADR as System First-Class Citizens (Complete Design) → Architecture §23

BRDs and ADRs are not merely documents — they are first-class citizen entities at parity with Workflows in the system, with complete lifecycle management and AI-assisted generation capabilities.

**BRD Lifecycle State Machine (16 states)**:
- Core 9 states: `draft` → `in_review` → `pending_fix` → `revised` → `approved` → `in_progress` → `implemented` → `verified` → `closed`
- Extension flags: `needs_revision`, `impact_pending`, `stale`, `on_hold`, `fast_track`, `requires_compliance_review`, `discussion_active`

**ADR Lifecycle State Machine (12 states)**:
- Core 7 states: `proposed` → `challenged` → `pending_validation` → `needs_revision` → `accepted` → `deprecated` → `superseded`
- Discussion attributes: `discussion_thread`, `validation_evidence`, `compliance_check`, `linked_brd`, `rejection_rationale`

**AI-Assisted Generation Pipeline**:
- BRD Generation: S15 BRDGenerator Skill (internally refined by ADR-0022 into a 6-Agent serial pipeline: BRD-IntentDeepener → ContextGatherer → VaguenessResolver → DraftWriter → Verifier → Assembler) → 6-round LLM deep verification (completeness/consistency/compliance/feasibility/impact/security) → human approval. Introduces Inline AssumptionCheck (Atomic Claim Decomposition + NLI verification) to prevent hallucination snowballing. See adr/0022.
- ADR Generation: S16 ADRGenerator Skill (auto-generates ADR drafts from design discussions and architecture changes) → human Review → immutable once accepted.
- Verification does not block generation — BRD/ADR Drafts are presented to the user first; verification results serve as auxiliary decision information.

**External Tool Integration**:
- Jira/Rally multi-layer mapping: BRD→Epic/Feature, requirement→Story/US, AC→Sub-task/Task.
- New MCPs: MCP-17 (jira-sync), MCP-18 (confluence-export), MCP-19 (compliance-mapper).
- Import capability: Legacy BRDs from Confluence/SharePoint/Word.

**Traceability Relationship Web**:
- BRD → (justifies) → ADR
- BRD → (decomposes_to) → Epic → Story → Compute Spec
- ADR → (constrains) → Module → Compute Spec
- Compute Spec → (implements) → Story → Epic → BRD
- Complete bidirectional traceability: from business requirements to code implementation, and from code changes back to impacted requirements.

---

## 2026-07-04 Supplement: Query Service / Large-Scale Data / materialize / Data Classification / Dependency Trigger Rules

### Query Service → FR15b

The Query Service is the core bridge connecting "what data the user wants to see" and "how the system retrieves data from data sources." Composed of four sub-components:

| Component | Responsibility | Key Capabilities |
|-----------|---------------|------------------|
| **Metadata Manager** | Manage Data Source connection info, Schema metadata, table relationships | Auto-discover Schema (tables, columns, types, indexes); auto-detect PK/FK (DDL declarations + naming convention inference + data distribution inference); IT can manually declare and correct relationships (including cross-database, JOIN types, cardinality) |
| **Query Generator** | Convert NL intent + Schema metadata → optimized query | Automatic JOIN path selection, aggregation, filter generation |
| **Pushdown Optimizer** | Push as much computation to the data source as possible | WHERE/JOIN/AGGREGATION executed at the data source; only necessary result sets transferred to Compute Engine; Pushdown Plan visualization |
| **Query Cache** | Cache query results to avoid repeated computation | Same SQL + parameters + Schema version → reuse cached result, configurable TTL; Schema change → auto-invalidate related caches → notify affected Workflow Owners |

**Core Principle**: The Query Service generates query plans but does not execute queries — actual execution is delegated to the Compute Engine (Light/Heavy). This ensures the Runtime Plane has zero AI side effects. The Design Plane assists with NL→SQL generation, and once the user confirms, the deterministic query plan is submitted to the Runtime Plane for execution.

### Large-Scale Data Architecture → FR15c

Architectural strategy for TB-scale data volumes and complex data source scenarios (6 subsystems):

| Strategy | Mechanism | Key Capabilities |
|----------|-----------|------------------|
| **Partitioning & Pruning** | Modern table formats (Apache Iceberg / Delta Lake / Hudi) via Data Connector plugin | Auto-detect and utilize partition info for Partition Pruning; TB-scale table queries only scan relevant partitions |
| **Incremental Processing** | Watermark (by time column) / CDC (consume Change Log) / Partition Incremental | Avoid full-table recomputation; watermark state persisted with transactional updates, not advanced on execution failure |
| **Pre-Aggregation & Materialization** | materialize Job Type | Full Refresh + Incremental Refresh strategies; Query Service auto-detects available materialized views and routes queries |
| **Cost-Based Optimization** | Table statistics (NDV, Min-Max, row count) | JOIN strategy selection (Broadcast/Shuffle/Pushdown) based on statistics |
| **Federated Query** | Heterogeneous data source federation | Small dimension tables broadcast → same-source Pushdown → cross-source materialized copies → federated query engine (auto-selection by transfer cost) |
| **Query Plan Guard** | Pre-execution estimation | Estimated scan >100M rows or >10GB → Warning; estimated execution time >30min → reject Design Plane preview |

### materialize Job Type (Materialized Aggregation) → FR13.6

The 9th Job Type for pre-computing frequently-queried aggregation results:

```yaml
job_type: materialize
materialize:
  base_query: "SELECT dept_id, month, SUM(revenue) FROM ..."
  refresh:
    strategy: incremental       # full | incremental
    incremental_key: updated_at
    schedule: "0 2 * * *"       # daily at 2 AM
  storage:
    engine: duckdb              # materialized view engine (DuckDB for Light, Spark for Heavy)
    ttl_hours: 24               # auto-refresh interval
```

- **Full Refresh** (small datasets): recompute all, suitable when base data changes and incremental is unreliable.
- **Incremental Refresh** (TB-scale): only process new/modified partitions, suitable for large-scale append-only data.
- Query Service auto-detects available materialized views and routes queries to materialized views instead of raw tables.
- Materialized views are Compute Specs — governed by the same Freeze Bridge lifecycle.

### Data Classification Tier (T0-T3)

| Tier | Sensitivity | Examples | Encryption | Masking | Export Control |
|------|------------|----------|------------|---------|----------------|
| **T0** | Public | Public reports, open datasets | Not required | Not required | Unrestricted |
| **T1** | Internal | Internal dashboards, dept analytics | TLS 1.3 in transit | Optional | Audit log |
| **T2** | Confidential | Financial reports, PII, salary data | AES-256 at rest + TLS 1.3 | Dynamic masking (role-based) | Approval required |
| **T3** | Restricted | PHI, trade secrets, merger data | AES-256 + HSM key mgmt | K-anonymity / Differential Privacy | Blocked by default |

Classification Flow: Data Catalog records Tier metadata → Query Rewriter injects RLS predicates + dynamic masking functions based on Tier+Role → Log all T3 access, alert T3 export attempts → Export Gate blocks unauthorized T3 exports.

### Dependency Trigger Rules

The default behavior for `depends_on` is `all_success`. Supports 5 trigger rule overrides:

| Rule | Behavior | Use Case |
|------|----------|----------|
| `all_success` | Trigger when all upstream Jobs succeed (default) | Standard sequential pipeline |
| `all_failed` | Trigger when all upstream Jobs fail | Error handling / notification workflow |
| `all_done` | Trigger when all upstream Jobs complete (regardless of outcome) | Cleanup / comprehensive report |
| `one_success` | Trigger when any one upstream Job succeeds | Race-condition data fetching |
| `none_failed` | Trigger as long as no upstream Job fails | Tolerant pipeline with optional upstream steps |

---

## 2026-07-04 Supplement: Intelligence Plane / Freeze Bridge Evolution / Dual-Model Strategy

### Intelligence Plane
- Cross-plane AI read-only analysis layer, independent from Design Plane and Runtime Plane.
- Does not execute LLM reasoning — queries pre-generated structured analysis results. Core capabilities: AI Knowledge Agent (NL Q&A over Code Graph + KB + Log), Log Analysis (anomaly detection, cost tracking), Observability (SLO dashboards), Usage Pattern Mining (behavior pattern → Design Plane suggestions).
- Core constraint: read-only, never writes — answers directly returned to the user without persistence; if the user wants to act on insights, they must explicitly go through the Design Plane.

### Freeze Bridge Evolution Notes
- Canary deployment will be fully enabled Post-MVP alongside the Heavy Engine.
- MVP uses simplified flow: Design Plane output → manual Sign-off → Light Engine execution.

### Agent Dual-Model Strategy
- **China Region**: Default DeepSeek V4 Pro (cost-priority, ~$0.50/M input + $2.00/M output).
- **US Region**: Default Claude Sonnet 5 (capability-priority, ~$3.00/M input + $15.00/M output).
- Sonnet 5 approximately 14% effective throughput advantage (rate-limit compensated); capability difference matters most on Tier 3-4 complex tasks.
- Tenant/Group/User three-tier model preference override. LLM SDK unified invocation layer transparently manages switching.

---

## 2026-07-04 Supplemental Decisions (ADR #7-#21)

### Decision #7b: Query Service Independent Component (ADR-0007)
- **Status**: Accepted (2026-07-04)
- **Background**: Natural language queries over databases require NL→SQL conversion + query optimization + caching. Existing architecture lacked a dedicated component.
- **Decision**: Four-component Query Service — Metadata Manager, Query Generator, Pushdown Optimizer, Query Cache. Generation and execution are separated — Design Plane assists with NL→SQL, Runtime Plane executes deterministic query plans.
- **Alternatives Considered**: All-in-one database solution (Rejected: vendor lock-in); LLM handles all query optimization (Rejected: cost, latency, correctness — deterministic optimization superior).
- **References**: → FR15b, → 03-architecture §7

### Decision #8: Large-Scale Data Architecture Strategy
- **Status**: Accepted (2026-07-04)
- **Background**: TB-scale data volumes require Partition Pruning, Incremental Processing, Pre-Aggregation capabilities beyond simply upgrading the Compute Engine.
- **Decision**: Six-pronged strategy — Partitioning & Pruning (Iceberg/Delta Lake), Incremental Processing (Watermark/CDC/Partition), Pre-Aggregation & Materialization (materialize Job Type), Cost-Based Optimization (table statistics + JOIN strategy), Federated Query (heterogeneous sources), Query Plan Guard (query protection). Heavy Engine is Spark only (Post-MVP); Trino/Ray deferred to Phase 7+.
- **Alternatives Considered**: Only upgrade Compute Engine to Spark (Rejected: no partition pruning → full table scans, no incremental → full recomputation, no materialization → repeated computation); Full Trino+Ray+Spark (Rejected: over-engineering for MVP).
- **References**: → FR15c, → FR13.6, → 03-architecture §5.4

### Decision #9: Dual-Model Pricing Strategy
- **Status**: Accepted (2026-07-04)
- **Background**: LLM costs are a major operational expense. Different regional customers have different price sensitivity, and different tasks have different model capability requirements.
- **Decision**: China region defaults to DeepSeek V4 Pro (cost-first), US region defaults to Claude Sonnet 5 (capability-first). Tenant/Group/User three-tier model preference override supported. LLM SDK unified invocation layer abstracts model differences.
- **Alternatives Considered**: Single model globally (Rejected: China customers sensitive to overseas model latency/compliance, US customers have trust concerns with domestic models); Fully customer-selected (Rejected: increases operational complexity, focus on dual-model initially).
- **References**: → 04-timeline, → 05-cost

### Decision #10: BRD/ADR as System First-Class Citizens
- **Status**: Accepted (2026-07-04)
- **Background**: BRDs/ADRs are traditionally standalone documents disconnected from the system. They need to be elevated to first-class citizen entities at parity with Workflows for bidirectional traceability, AI-assisted generation, and complete lifecycle management.
- **Decision**: BRD 16 lifecycle states, ADR 12 lifecycle states; AI-assisted generation + 6-round LLM deep verification; multi-layer mapping with Jira/Rally/ServiceNow (via MCP-17 external-ticketing unified adapter); BRD↔ADR↔Workflow triangle traceability; 3 new Skills (S15 BRDGenerator internally refined by ADR-0022 into 6 Agents, S16 ADRGenerator, S17 TraceabilityAnalyzer).
- **References**: → FR23, → 03-architecture §23

### Decision #11: materialize as 9th Job Type
- **Status**: Accepted (2026-07-04)
- **Background**: Repeated aggregation queries on TB-scale data waste compute resources. Pre-aggregation mechanism needed to materialize frequently-queried results.
- **Decision**: New `materialize` Job Type. Supports Full Refresh (small data/Schema changes) and Incremental Refresh (TB-scale). Query Service auto-detects available materialized views and routes queries. Materialized views are Compute Specs included in Freeze Bridge validation.
- **Alternatives Considered**: Database materialized views (Rejected: coupled to specific database, not portable across engines); Query Service cache only (Rejected: cache is passively populated, less reliable than active materialization).
- **References**: → FR13.6, → FR15c.4, → 03-architecture §6

### Decision #12: Unified Data Health Check Framework
- **Status**: Accepted (2026-07-04)
- **Background**: The system needs three data health check capabilities — rule-driven (DQ Rule), ML-driven (Anomaly Detection), cross-source (Reconciliation). The original design modeled them as independent engines, but users don't care whether an anomaly was discovered by rules or ML — they only care "what's wrong with my data?" Industry trends (Monte Carlo, Soda, Great Expectations 2024-2026) favor unified frameworks.
- **Decision**: Unified Data Health Check Framework, YAML-configuration driven. Three check types (`rule` / `anomaly` / `recon`) share common scope/severity/schedule/output configuration. Execution modes: auto (after Report generation) / scheduled (cron) / manual / on_recon_complete. Output: Annotated Report (anomaly annotations without blocking publication) + AI Agent attribution analysis + BRD→Jira/Rally/ServiceNow closed loop.
- **Core Principle**: Any operation modifying financial data, regardless of amount, must pass Permission → Validation → Approval → Trigger ETL pipeline — no Auto-write-off exists.
- **References**: → FR18, FR19, → 03-architecture §12.2, → adr/0014

### Decision #13: Adjustment Form Builder
- **Status**: Accepted (2026-07-04)
- **Background**: Different Teams have varying Adjustment needs — some need Excel templates (with dropdown options and validation rules), others prefer pure Web UI operations. A unified Form Builder is needed to define Adjustment entry methods rather than preset Excel templates.
- **Decision**: Dev/Admin defines Form Definition YAML through Adjustment Form Builder (column definitions, validation rules, approval chain). Submitters can use Web UI / Excel download-upload / API submission — all three go through the same pipeline: Permission → Validation → Approval → Trigger ETL. Distinguishes Repeat Adjustments (scheduled, pre-populated, simplified approval) and Daily Manual Adjustments (event-driven, blank form, full approval chain).
- **References**: → FR7, → 03-architecture §3.4, → adr/0014

### Decision #14: Agent Triage & Layered Remediation Gateway
- **Status**: Accepted (2026-07-04)
- **Background**: There's a gap between Data Health Check Framework output and user action — high alert volume (tens to hundreds daily), inconsistent Agent intervention (only Recon has auto-analysis), uniform approval granularity (all operations follow the same approval chain). Industry best practice (Monte Carlo 2025-2026) adds an Agent Triage Layer above the detection layer.
- **Decision**: (a) Agent Triage Layer (Intelligence Plane): auto-classification, false positive prediction, dedup-merge, proactive Health Summary push. severity=error auto-triggers S07 parallel diagnosis; severity=warning proactively pushes summary with predicted confidence. (b) L0-L3 four-tier Remediation Gateway: zero-risk auto-execute (L0) → low-risk one-click confirm (L1) → medium-risk single approval (L2) → high-risk dual approval + Impact Report (L3). (c) S08 DataQualityAdvisor (Closed-Loop Learning): auto-suggests rule optimization based on user signals. (d) Phase 7+ evolution: Hierarchical Multi-Agent (Central Reasoner + 5 Sub-Agents).
- **Core Constraint**: All Agent Triage operations are read-only. Any config or data modification must pass through the Remediation Gateway with human confirmation.
- **References**: → adr/0015, → 03-architecture §9, §12.2, §22A.5, §22B S08

### Decision #15: Dual-Mode Agent Orchestration
- **Status**: Accepted (2026-07-04)
- **Background**: Agent Skill orchestration has a conflict between flexibility and auditability — Exploration scenarios need LLM dynamic Skill composition, while compliance scenarios need proof that "critical steps were not skipped." SOX audits require reproducible, provable change paths. All six major industry Agent frameworks don't natively support dual-mode.
- **Decision**: (a) Exploration Mode: LLM free orchestration (read-only operations), guarded by tool_budget + max_rounds + Permission Gate. (b) Verified Path Mode: predefined fixed step sequence (mutating operations), LLM reasons within each step but cannot skip/reorder/replace steps — missing steps → reject execution. (c) Mode switch rules: IntentParser matches Verified Path → forced Path; mutation but no matching Path → reject; otherwise → Exploration. (d) Skill metadata enhancement: each Skill carries prerequisites / compatible_with / side_effects / fallback. (e) Verified Path Catalog: 6 initial paths (VP-001 through VP-006).
- **Core Principle**: Explore with AI (Exploration Mode), Execute without AI Side Effects (Verified Path Mode + Remediation Gateway).
- **References**: → adr/0016, → 03-architecture §22A, §22B, §22G

### Decision #16: Verified Path — Saga Semantics & Durable Execution
- **Status**: Accepted (2026-07-04)
- **Background**: ADR-0016 defined Verified Path's success path but didn't define failure semantics. What happens to completed step outputs after Step N times out? How does audit trace failure causes? Industry best practice (Stripe/PayPal 2025) requires Saga compensation + idempotency + durable execution.
- **Decision**: (a) Saga reverse compensation — each Step registers compensation before executing forward, compensates in reverse order on failure. (b) Three-layer idempotency — Path-level (Redis SET NX), Step-level (Redis+PG dual-write), Skill-level (PG ON CONFLICT). (c) Durable execution — verified_path_executions + verified_path_step_events tables, crash recovery resumes from current_step. (d) DLQ — after 3 failed compensation retries → create Incident → escalate to Data Owner. (e) GATE compensation does not delete approval records — marks as voided, retains audit trail.
- **References**: → adr/0017, → 03-architecture §22A.4, §22G

### Decision #17: Agent Evaluation Framework
- **Status**: Accepted (2026-07-04)
- **Background**: The architecture lacked a systematic Agent evaluation framework. Financial compliance scenarios require measurable, auditable quality metrics — "users feel it works" isn't sufficient. Industry 2025-2026 consensus: evaluating Agents means evaluating the entire execution trajectory, not single model outputs.
- **Decision**: (a) Six-Dimension Trajectory Scoring — Task Completion, Tool Selection, Argument Accuracy, Result Utilization, Plan Coherence, Error Recovery — auto-scored after each Agent execution. (b) Compound Error tracking — per-step 95% × 8 steps ≈ 66% end-to-end, making this common failure mode visible. (c) Evaluation Flywheel — every production failure permanently converted into Golden Dataset regression test. (d) Golden Dataset organized per VP, versioned immutable, CI Gate blocks regression. (e) Three-layer monitoring dashboard: Business KPIs / System Health / Cost & Resources.
- **References**: → adr/0018, → 03-architecture §22H

### Decision #18: Agent Memory Architecture
- **Status**: Accepted (2026-07-04)
- **Background**: Agents had no cross-session continuity. Financial analysis naturally spans multiple days (discover anomaly → wait for data → come back to continue). Industry consensus (LangGraph Store, Mem0, ENGRAM 2025-2026): Agent memory is a four-layer cognitive architecture.
- **Decision**: (a) L1 Working Memory — current session context, Context Window + LangGraph Checkpointer. (b) L2 Episodic Memory — cross-session episodic storage, PostgreSQL + pgvector semantic retrieval, recording session summaries + continuation_point. (c) L3 Semantic Memory — permanent user-level facts (preferences, relationships), with provenance tags (user_stated/model_inferred/tool_output) and bitemporal validity. (d) L4 Procedural Memory — VP Catalog + Skill Registry (already exists). (e) Promotion rules: same fact observed 3 independent times + confidence ≥0.7 → LLM extracts candidate → user confirms → written to L3. All model_inferred facts must pass human confirmation. (f) Financial compliance constraint: strict tenant isolation, no cross-tenant knowledge flow.
- **References**: → adr/0019, → 03-architecture §22I

### Decision #19: Agent Cost Governance & Model Degradation Detection
- **Status**: Accepted (2026-07-04)
- **Background**: LLM Agent costs are unpredictable (500-50,000 tokens/query), Exploration Mode may trigger runaway loops. LLM provider model upgrades may change outputs. Real industry incidents: $47K loop, 442K tokens single burst. Hierarchical cost governance and systematic model upgrade validation needed.
- **Decision**: (a) Hierarchical Token Quota — Organization→Tenant→User→VP/Exploration nested budgets, Admin-configured. (b) Tiered Enforcement — 50% WARN → 75% THROTTLE → 85% DEGRADE (auto-downgrade cheaper model) → 90% CRITICAL → 100% KILL. Core principle: DEGRADE rather than DENY. (c) Three loop detectors — Identical-Call/Ping-Pong/Context-Growth, any trigger → Circuit Breaker. (d) Four-Stage Model Deployment Funnel — Shadow(0%)→Canary(1-5%)→Percentage(10→50%)→Full(100%), each stage armed with auto-rollback triggers. (e) CI Regression Gate — Model upgrade validated on Golden Dataset before deployment, blocked on degradation.
- **References**: → adr/0020, → 03-architecture §22J

### Decision #20: Verified Path Promotion & Multi-Agent Concurrency
- **Status**: Accepted (2026-07-04)
- **Background**: (a) Skill sequences validated as effective in Exploration Mode should be promotable to Verified Paths, but financial SOX compliance requires full SDLC. (b) Multiple users/Agents may launch conflicting operations on the same resource (double adjustment, semantic conflicts), current Saga+idempotency only covers intra-path consistency.
- **Decision**: (a) VP risk-graded promotion — Read-Only auto-promote, Config-Modify platform-internal Admin approval, Data-Modify requires full BRD→Jira/Rally dual approval. (b) Shadow Promotion — candidate VP runs silently in production for 30 days (success rate>95%, compensation rate<5%, rejection rate<10%) → auto-generates Promotion Proposal. (c) Three-layer concurrency control — optimistic lock (version field, default) → pessimistic lock (PG Advisory Lock, high-conflict resources) → semantic conflict detection (ResourceConflictCheck before Gateway approval). (d) Priority preemption — Recon > Month-End Close > Ad-hoc, Recon can preempt Ad-hoc locks. (e) VP execution non-diversible — follow-up questions saved as Pending Questions, handled after VP completion in separate Exploration.
- **References**: → adr/0021, → 03-architecture §22G, §22K, §22L

### Decision #21: BRD Generation Agent Pipeline Redesign
- **Status**: Accepted (2026-07-04)
- **Background**: ADR-0010 established BRD as system first-class citizen + AI-assisted generation direction, but S15 BRDGenerator was modeled as a monolithic Skill. Deep-dive grilling found five gaps: insufficient vague requirement disambiguation, LLM confident hallucinations undetectable (fuzzy_nodes relies on LLM self-reporting), Post-hoc verification can't prevent Hallucination Snowballing, coarse context retrieval, Jira bidirectional sync causing state conflicts.
- **Decision**: (a) S15 refined into 6 prefix-named Agent serial pipeline — BRD-IntentDeepener (Five Whys elicitation) → BRD-ContextGatherer (three-source RAG + Schema Bootstrap cold-start fallback) → BRD-VaguenessResolver (Experience Typology Tree + Gating/Pruning precise questioning) → BRD-DraftWriter (chapter-by-chapter generation + soft lock + bounded backtracking + Inline AssumptionCheck) → BRD-Verifier (6-round verification, conflict detection without adjudication) → BRD-Assembler (three-format output + Pre-Sync Gate). All Agent outputs are independent JSON, Web UI renders progressively. (b) Inline AssumptionCheck — Atomic Claim Decomposition + NLI verification (FGL 2025: 90%+ accuracy), distinguishes directly_supported/inferred_assumption/business_assumption, unconfirmed assumptions split into Blocker/Non-blocker. (c) Jira unidirectional sync — BRD is single Source of Truth, Webhook read-only progress sync. (d) Event-driven Suspect Flag for multi-BRD conflict detection (AroTrace pattern). (e) Compliance mapping — tenant Compliance Profile (Admin config at onboarding) + MCP-19 RAG within activated frameworks. (f) BRD product quality — human reviewer four-dimension scoring (Clarity/Completeness/Feasibility/Compliance). (g) Phase 2 reservation: BRD-approved → SDD Pipeline.
- **References**: → adr/0022, → adr/0010, → 03-architecture §23.5-§23.12

### Decision #22: KB Content Lifecycle Pipeline
- **Status**: Accepted (2026-07-08)
- **Background**: KB storage (ADR-0013), write/read paths (FR34/FR35), and Email ingestion (§12.1) exist, but three areas spanning all heterogeneous content (DOCX/Excel/Email/upload) are not systematically defined: the content processing pipeline (chunking, Contextual Retrieval, multi-index write), linkage weaving (how heterogeneous content interconnects), and the quality flywheel (dedup/conflict/freshness/eval). Per-channel ad-hoc pipelines fragment retrieval quality and make cross-source correlation impossible.
- **Decision**: (a) Unified five-stage Content Processing Pipeline — Parse & Normalize (reuse MCP-11/12/16) → Semantic Chunking (structure-aware, not fixed-length) → Contextual Retrieval Enhancement (small model generates context summary prepended to each chunk before embedding; Anthropic 2024: -35% retrieval failure alone, -67% with reranking) → Four-index single-ACID-transaction PG write (pgvector HNSW + tsvector GIN + native tables + edge tables; ADR-0013 zero-CDC advantage) → Provenance Tagging (immutable, aligns ADR-0019 provenance classes). (b) Linkage Weaving Layer — three edge-generation strategies: MENTIONS_ENTITY (entity co-reference, low-risk auto), SIMILAR_TO (semantic similarity >0.85 + NLI non-contradiction, low-risk auto), DERIVED_FROM (structural lineage, high-risk L2 human confirm), CONFLICTS_WITH (NLI contradiction, frozen + human adjudication). Lazy edge creation over full GraphRAG community hierarchy (respects Boring Technology + PG-First scale). (c) Quality Flywheel — Dedup (SimHash/MinHash) → Conflict Detection (NLI) → Freshness Decay (half_life by content type: definitions 2yr / snapshots 30d / email 180d; decay = down-rank not delete, aligns ADR-0019 bitemporal) → Retrieval Quality Evaluation (RAGAS metrics on ADR-0018 Golden Dataset; regression → re-embed/re-chunk).
- **References**: → adr/0023, → adr/0013, → adr/0019, → 03-architecture §10.2-§10.4

### Decision #23: KB Reasoning Support — Diagnostic Playbooks & Code Knowledge Domains
- **Status**: Accepted (2026-07-08)
- **Background**: Scenario 6 (§22E) proves complex cross-content diagnostics are possible, but Agent orchestration relies on S01 routing + Skill metadata + free ReAct — no explicit knowledge encodes expert investigation paths, so diagnostic quality is unstable. Also, code-repo knowledge has no ingestion/indexing path: Code Graph models structural relationships (not source code), MCP-06 does diff/blame (not semantic code search), so the Agent cannot fulfill "check the code logic for bugs". Two gaps undermine the highest-value queries ("why did this report generate this value?").
- **Decision**: (a) KB 8th domain — Diagnostic Playbooks: IF/THEN diagnostic decision trees encoding expert investigation methodology, acting as a "soft skeleton" the LLM reasons within (Exploration-Mode counterpart to ADR-0016 Verified Paths). Three sources (system-builtin conf 1.0 / incident-distilled model_inferred 0.7-0.9 promoted after ≥3 recurrences / user-defined conf 1.0). Two routing paths (explicit via S01 trigger-match / implicit via S02 retrieval). Closed-loop learning reuses ADR-0019 promotion rules + S08 pattern. (b) KB 9th domain — Code Knowledge: three-layer index over code artifacts (Compute Spec / Sandbox Python / Git / external repos): structural (existing Code Graph nodes/edges) + semantic (function-level embeddings via ADR-0023 Stage 4) + change (existing Git/MCP-06). Event-driven ingestion (Freeze merge / Sandbox exec / git webhook / PR merge). Bridge edges link functions↔Jobs↔GlossaryEntries. (c) New Skill S18 PlaybookRouter + new MCP-23 code-knowledge-search. KB grows from 7 to 9 domains, all on existing PG-First stack. Industry basis: Devin/Monte Carlo 2025 convergence on playbook skeletons; Cursor/Cody 2025 dual-index code RAG.
- **References**: → adr/0024, → adr/0016, → adr/0019, → adr/0023, → 03-architecture §10 (domain table), §22B (S18), §22C (MCP-23), §22E Scenario 6

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-04 | Initial version: project background, design philosophy, 6 ADRs, core concepts, KB design, Job model, Email Ingestion, Recon, Data Quality, AI Agent, DevOps, BRD/ADR basics |
| 1.1 | 2026-07-04 | Added: Query Service, Large-Scale Data Architecture, materialize Job Type, Data Classification (T0-T3), Dependency Trigger Rules, Intelligence Plane, Freeze Bridge evolution notes, BRD/ADR complete lifecycle (16/12 state machine), AI-assisted generation pipeline, external tool integration, Agent dual-model strategy, ADR #7-#11, KB 7th domain (Report/Metric Catalog). Fixed: Heavy Engine description (Trino/Ray deferred), Decision #3 Consequences vs Rationale contradiction, Job Type enumeration outdated |
| 1.2 | 2026-07-04 | Core philosophy refinement + four-layer model + ADR #5 rewrite + ADR #12-#16: Data Health Check Framework, Adjustment Form Builder, KB PG-First strategy, Agent Triage + L0-L3 Remediation Gateway + S08 Closed-Loop Learning, Dual-Mode Agent Orchestration + Verified Path Catalog |
| 1.3 | 2026-07-04 | ADR #17-#20: Agent Evaluation Framework (six-dimension trajectory scoring + evaluation flywheel), Agent Memory Architecture (four-layer memory model), Agent Cost Governance (hierarchical token budgeting + tiered enforcement + four-stage model deployment funnel), VP Promotion & Multi-Agent Concurrency (risk-graded promotion + three-layer concurrency control + priority preemption). Architecture doc added §22H-§22L |
| 1.4 | 2026-07-04 | ADR #21 + ADR-0022: BRD Generation Agent Pipeline Redesign — S15 refined from monolithic to 6-Agent serial pipeline, Inline AssumptionCheck, Experience Typology Tree, Suspect Flag, Pre-Sync Gate, Jira unidirectional sync. Architecture doc §23 major update (new §23.5.1-§23.5.8 + §23.11-§23.12). Glossary added 10 BRD generation terms |
| 1.5 | 2026-07-08 | ADR #22 + ADR-0023: KB Content Lifecycle Pipeline — unified 5-stage Content Processing Pipeline (Contextual Retrieval), Linkage Weaving Layer (lazy edges vs full GraphRAG), Quality Flywheel (dedup/conflict/freshness/RAGAS). ADR #23 + ADR-0024: KB Reasoning Support — 8th domain Diagnostic Playbooks (soft skeleton for Exploration-Mode diagnostics), 9th domain Code Knowledge (three-layer code index). New Skill S18 PlaybookRouter, new MCP-23 code-knowledge-search. KB grows from 7 to 9 domains. Architecture doc new §10.2-§10.4. Bug-fix: §10 domain table was missing 7th domain (Report/Metric Catalog) — now consistent with rest of project. Glossary added 7 terms (102→109). New FR43-FR46 |

---

*Last Updated: 2026-07-04 | Version: 1.4 | Next Review: 2026-07-17*
*Review Process: The project sponsor reviews this document to verify it accurately reflects all confirmed design decisions; after review, update the review date and increment the version number*
