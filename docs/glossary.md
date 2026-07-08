# Glossary

> Core domain terminology and technical concepts for the llm-reporting project. Terms are organized by category.
>
> **Related Documents**: Requirements → [02-requirement.md](02-requirement.md) | Architecture → [03-architecture.md](03-architecture.md)

## Core Architecture Concepts

| Term | Definition |
|------|------------|
| Design Plane | The AI-assisted exploration and authoring layer. All artifacts are "design drafts" with no production side effects. Includes Conversation UI, Visual Designer, Workbench, and AI Copilot Engine. |
| Freeze Bridge | The independent transition plane connecting Design Plane and Runtime Plane. Core principle: no auto-compilation — scan fuzzy nodes → propose deterministic solutions → **mandatory human sign-off** → validate → test → approve → deploy. Freeze is reversible. |
| Runtime Plane | The deterministic, zero AI side-effect production execution layer. Includes Workflow Executor, Data Connectors, Output Renderer, Scheduler, Query Rewriter (executes pre-generated deterministic SQL), and Incident Manager. The Intelligence Plane provides AI read-only analysis (ad-hoc Q&A, attribution) without crossing the bridge. |
| Intelligence Plane | Cross-plane AI read-only analysis layer (AI Knowledge Agent, NL Q&A, attribution analysis, Log Analysis, Observability). Core constraint: read-only, never writes — AI outputs are returned directly to the user without persistence unless the user explicitly confirms and goes through the Design Plane flow. |
| Compute Spec | Unified YAML-based computation definition covering Reporting/ETL/Adjustment/Reconciliation. 9 Job Types: source, transform, output, quality, workflow_ref, data_writer, decision, wait, materialize. |
| Light Engine | Lightweight compute engine for the Design Plane: DuckDB (zero-config, sub-second startup) + Polars (high-performance DataFrames). Used for sample data and development/debugging. |
| Heavy Engine | Production compute engine for the Runtime Plane: **Spark** (Post-MVP). Trino and Ray deferred to Phase 7+. |
| Common Compute Subset | The minimal set of operations guaranteed to be portable between Light Engine and Heavy Engine. Workflows using only this subset can switch between engines seamlessly. |

## Knowledge Base

| Term | Definition |
|------|------------|
| Knowledge Base (KB) | 9 knowledge domains: Business Glossary, Data Catalog, Mapping Registry, Workflow Templates, Adjustment History, Behavior Patterns, Report/Metric Catalog, Diagnostic Playbooks (ADR-0024), Code Knowledge (ADR-0024). Storage: PG-First + Interface Abstraction — PostgreSQL + pgvector handles Vector/Graph/Relational roles during MVP; S3/MinIO handles Blob. Dedicated engines (Milvus/Neo4j) reserved via interface abstraction, introduced only when four gating conditions are met. Content enters via the unified Content Processing Pipeline (ADR-0023). |
| Code Graph | System structure knowledge graph (Workflow → Job → DataSource DAG) with 15+ edge types. Powers Change Intelligence and the AI Knowledge Agent. |
| Business Glossary | KB domain: terms, aliases, definitions, formulas, business context, data source mappings. |
| Data Catalog | KB domain: data asset metadata (tables/APIs/files/streams), schema details, PII markers, quality scores. |
| Mapping Registry | KB domain: legacy-to-new field mappings, cross-currency conversion rules, transform logic. |
| Report/Metric Catalog | KB domain (7th domain): report definitions, metric formulas, calculation granularity, certification status, relationships with data sources and Workflows. |
| Diagnostic Playbooks | KB domain (8th domain, ADR-0024): expert-encoded IF/THEN diagnostic decision trees that guide Agent reasoning in Exploration Mode — the read-only "soft skeleton" counterpart to Verified Paths. Three sources: system-builtin (conf 1.0), incident-distilled (promoted after ≥3 recurrences), user-defined. See adr/0024. |
| Code Knowledge | KB domain (9th domain, ADR-0024): three-layer index over code artifacts — structural (Code Graph nodes/edges), semantic (function-level embeddings), change (commits/blame/diffs). Enables semantic code search and code-logic reasoning. See adr/0024. |
| Content Processing Pipeline | Unified 5-stage funnel (ADR-0023) through which all heterogeneous content (Email, DOCX, Excel, upload, API) is processed: Parse & Normalize → Semantic Chunking → Contextual Retrieval Enhancement → Four-index ACID write → Provenance Tagging. See adr/0023. |
| Contextual Retrieval | Technique (Anthropic 2024) where a small model generates a short context summary prepended to each chunk before embedding, reducing retrieval failure by 35% alone (67% with reranking). Core of Content Processing Pipeline Stage 3. See adr/0023. |
| Linkage Weaving | The layer (ADR-0023) that generates cross-content relationship edges: MENTIONS_ENTITY (entity co-reference), SIMILAR_TO (semantic similarity), DERIVED_FROM (structural lineage, L2-confirmed), CONFLICTS_WITH (contradiction). Lazy edge creation over full GraphRAG community hierarchy. See adr/0023. |
| Entity Linking | The process of extracting named entities from content (via small-model NER) and linking them to KB GlossaryEntries, producing MENTIONS_ENTITY edges. Part of Linkage Weaving. See adr/0023. |
| Freshness Decay | Quality-flywheel mechanism (ADR-0023) where each chunk carries a half_life by content type; beyond half_life the chunk is marked stale and down-ranked at retrieval (not deleted — bitemporal retention per ADR-0019). See adr/0023. |
| Playbook Router (S18) | Skill that matches a user's diagnostic intent against the Diagnostic Playbooks domain and injects the matched playbook as a guided plan into the Skill Planner. Exploration-Mode counterpart to Verified Path enforcement. See adr/0024. |

## Jobs & Execution

| Term | Definition |
|------|------------|
| Execution Sandbox | Per-Job isolated execution environment: CPU/Memory/Disk/Network resource isolation + FS/Network/seccomp security boundaries. Sandbox Pool pre-warming <100ms. |
| Data Writer (data_writer) | Job type that writes computed results back to a Data Catalog-registered data source (write_mode: append/upsert/overwrite/merge). Distinct from output (file/notification distribution). |
| Materialize | The 9th Job Type. Pre-computes and persists frequently-queried aggregation results (Full Refresh or Incremental Refresh) for automatic routing by the Query Service. |
| Dependency Trigger Rules | 5 trigger coverage modes for `depends_on`: all_success (default), all_failed, all_done, one_success, none_failed. |
| Workflow Reference (workflow_ref) | Nested Workflow execution exposing a summary DAG to the parent Workflow but with isolated execution context (grey-box, not pure black-box). |

## AI Agent

| Term | Definition |
|------|------------|
| MCP (Model Context Protocol) | Standard protocol for Agent interaction with external systems. This project plans 21 MCP Servers (18 in the §22C Core Catalog: MCP-01..17 + MCP-23; plus 3 BRD-pipeline MCPs defined in §23.8.2: MCP-20 jira-sync, MCP-21 confluence-export, MCP-22 compliance-mapper). |
| Skill | Pre-defined Agent capability module (e.g., Intent Parsing, KB Retrieval, Impact Analysis). This project plans 18 composable Skills (S01-S18). |
| LLM SDK | Unified model invocation layer with pluggable switching between DeepSeek V4 Pro / Claude Sonnet 5 / private models. |
| Prompt Injection | OWASP LLM01 threat. Maliciously crafted prompts that bypass system instructions or leak data. This architecture employs 5-layer defense. |
| DeepSeek V4 Pro | Default LLM model for China region (~80 tps decode, Input $0.50/M, Output $2.00/M). |
| Claude Sonnet 5 | Default LLM model for US region (~80 tps decode, Input $3.00/M, Output $15.00/M). |
| Hierarchical Multi-Agent | Phase 7+ evolution direction: Central Reasoner + 5 Sub-Agents (Pipeline Change / Data Anomaly / Infrastructure / Upstream Dependency / Historical Pattern) reasoning in parallel with consolidated judgment. Aligned with Monte Carlo 2025-2026 production architecture. |
| Six-Dimension Trajectory Scoring | Core metric of the Agent Evaluation Framework. Each Agent execution is scored across six dimensions: Task Completion, Tool Selection, Argument Accuracy, Result Utilization, Plan Coherence, Error Recovery. Deterministic checks first, LLM-as-Judge supplementary. See adr/0018. |
| Evaluation Flywheel | Closed-loop evaluation process: offline eval → deploy → online monitoring → failure analysis → expand Golden Dataset → Agent optimization → repeat. Every production failure permanently converted into a regression test. See adr/0018. |
| Golden Dataset | Immutable, versioned, annotated test set sourced from production Execution Traces (especially compensation/rejected cases) + hand-crafted boundary cases. Organized per VP. CI Gate blocks any regression. See adr/0018. |
| Compound Error | Single-step 95% success rate → 8-step chain end-to-end ≈ 66%. The most common production Agent failure pattern: per-step all-green but end-to-end red. See adr/0018. |
| Four-Layer Memory | Cognitive architecture for Agent memory: L1 Working (within-session), L2 Episodic (cross-session), L3 Semantic (permanent facts), L4 Procedural (Skills/VPs, already exists). Each layer has independent storage strategy and promotion rules. See adr/0019. |
| Provenance Tag | Memory source classification: user_stated (user assertion) / tool_output (system data) / model_inferred (LLM reasoning). Determines promotion confidence and whether human confirmation is required. See adr/0019. |
| Bitemporal Validity | Each fact carries valid_from / valid_to / superseded_by. Changes do not overwrite old facts, forming a traceable evolution chain. SOX audits can retroactively inspect the exact state at decision time. See adr/0019. |
| Tiered Enforcement | Token budget consumption strategy: 50% WARN → 75% THROTTLE → 85% DEGRADE (auto-downgrade to cheaper model) → 90% CRITICAL → 100% KILL. Core principle: DEGRADE rather than DENY. See adr/0020. |
| Loop Detection | Three-detector combination preventing runaway Exploration: Identical-Call (repeated input), Ping-Pong (mutual invocation), Context-Growth (context bloat). Any trigger → Circuit Breaker. See adr/0020. |
| Four-Stage Rollout Funnel | Model upgrade deployment strategy: Shadow (0% users) → Canary (1-5%) → Percentage (10→50%) → Full (100%). Each stage armed with auto-rollback triggers. See adr/0020. |
| Auto-Rollback | Pre-authorized model rollback conditions (guardrail trip rate exceeding threshold / rubric regression / latency spike / new error cluster). Triggered rollback to previous model without human approval. See adr/0020. |
| Three-Layer Concurrency Control | Multi-Agent concurrency conflict resolution: L1 optimistic lock (version CAS, default) → L2 pessimistic lock (PG Advisory Lock, hot resources) → L3 semantic conflict detection (Gateway pre-approval check). See adr/0021. |
| Priority Preemption | Financial business priority ordering: Recon > Month-End Close > Ad-hoc. Higher-priority operations can preempt locks held by lower-priority ones. Preempted party enters wait queue. See adr/0021. |
| Shadow Promotion | Candidate VP runs silently in production traffic for 30 days (without blocking real flow), collecting success/compensation/rejection metrics. Auto-generates Promotion Proposal when thresholds met. See adr/0021. |
| Starter Prompt | Clickable capability cards on the Welcome Screen covering 80% of daily scenarios. Solves the "Blank Canvas Problem" for non-technical users. See adr/0021. |
| Blank Canvas Problem | The UX challenge where stronger Agent capabilities paradoxically make users less certain where to begin. Solved through four mechanisms: three-layer progressive disclosure + Starter Prompts + context-aware suggestions + proactive questioning when intent is vague. See adr/0021. |

## Data Health Check

| Term | Definition |
|------|------------|
| Data Health Check Framework | Unified YAML-configuration-driven framework with three check types: `rule` (rule-driven), `anomaly` (ML-driven), `recon` (cross-source reconciliation). All three share common scope/severity/schedule/output configuration. See adr/0014. |
| Anomaly Detection | `type: anomaly` — ML-driven detection without explicit rules. Methods: ratio_change / z_score / seasonal_decomp / distribution_shift / trend_change. Users only specify scope + sensitivity. Execution modes: auto / cron / manual / on_recon_complete. |
| Temporal Consistency | The 7th DQ dimension (beyond the 6 traditional dimensions). Detects ratio jumps and cumulative consistency issues across time dimensions (e.g., a specific business line's Month-over-Month variance >15%). Scoped under `type: anomaly` or `type: rule`. |
| Annotated Report | Report output with anomaly annotations (row-level/cell-level), including check_name / severity / variance magnitude / confidence. Does not block report publication. |
| Reconciliation (Recon) | `type: recon` — matching two independent data sources by match key with three-tier routing (Matched/Unmatched/Partial). Break Analysis assisted by AI Agent (Intelligence Plane) for classification (TIMING/MISSING/ROUNDING/MAPPING/CURRENCY/DUPLICATE/UNKNOWN). All finance-related Resolutions must go through the Adjustment pipeline (Permission → Validation → Approval → Trigger ETL). No Auto-write-off. |
| Data Quality Check | `type: rule` — explicit conditional expressions. 7 dimensions (completeness/accuracy/consistency/timeliness/uniqueness/validity/temporal_consistency), three severity levels (Error/Warning/Info). |
| Adjustment Form | Standardized data entry form defined by Dev/Admin via Form Builder (column definitions, validation rules, approval chain). Business Users can submit via Web UI / Excel upload / API — all three go through the same pipeline: Permission → Validation → Approval → Trigger ETL. |
| Agent Triage Layer | Auto-alert classification layer within the Intelligence Plane. Runs automatically after Data Health Check results are produced but before the user sees them: severity=error auto-triggers S07 parallel diagnosis; severity=warning proactively pushes Health Summary (dedup + pattern match + predicted confidence). All operations are read-only — configuration changes must go through Remediation Gateway. |
| Remediation Gateway | L0-L3 four-tier risk-graded approval: L0 (zero risk, auto-execute) → L1 (low risk, Agent suggestion + one-click confirm) → L2 (medium risk, single Approver + DQ Gate) → L3 (high risk, dual approval + Impact Report + Canary). L3 interfaces with the Freeze Bridge. |
| Closed-Loop Learning | S08 DataQualityAdvisor receives user action signals (false positive markings, repeated drill-downs, coverage gaps) → auto-suggests rule optimization. Does not auto-modify rules — suggestions take effect after human confirmation through the Remediation Gateway. |
| Learning Period | Initial state for `type: anomaly` checks. New tenants or newly created anomaly checks automatically enter a 30-day learning period: no alert generation, no Triage push, baseline statistics establishment only. Progressive timeline activation (Day 7 ratio_change → Day 30 seasonal_decomp → Day 90 trend_change). Strict tenant isolation — uses only tenant's own data. Anomaly rate >30% or consecutive false positives → degraded to degraded status. |
| Agent Onboarding Interview | Auto-triggered on new tenant first login. Agent scans tenant Data Source Schema → infers initial DQ Rules + Anomaly Checks from column types/DDL constraints → infers Business Glossary draft from naming conventions → conversational refinement → generates Data Health Profile YAML. All inference based solely on tenant's own data, strict isolation. |
| Dual-Mode Orchestration | Agent Skill orchestration split by operational risk: Exploration Mode (read-only operations, LLM free orchestration + guardrails) and Verified Path Mode (mutating operations, predefined fixed step sequence — LLM reasons within each step but cannot skip/reorder/replace steps). Missing steps → reject execution. See adr/0016. |
| Verified Path | Predefined fixed Skill sequence using Saga semantics: register compensation before executing forward, compensate in reverse order on failure. Three-layer idempotency (Path/Step/Skill) ensures safe re-execution. Initial catalog of 6 paths (VP-001 through VP-006). See adr/0017. |
| Saga Compensation | Industry-standard pattern for distributed transactions. Each step has a forward action + compensating action. On failure, compensations execute in reverse order. Compensations are idempotent and retryable (3 retries with exponential backoff); terminal failure enters DLQ for human handling. |
| Idempotency Key | Deterministically generated unique identifier (`{path_id}_{date}_{entity_id}`). The same key's Path instance executes only once. Three-layer protection: Path-level Redis SET NX, Step-level Redis+PG dual-write, Skill-level PG ON CONFLICT. Crash-recovery safety net. |
| DLQ (Dead Letter Queue) | Final destination after 3 failed compensation retries. Auto-creates Incident → escalates to Data Owner → human cleanup of residual state. Periodic scanning of unresolved entries → weekly summary report. |

## BRD & ADR

| Term | Definition |
|------|------------|
| BRD (Business Requirements Document) | First-class entity at parity with Workflow in the system. 16 lifecycle states, AI-assisted generation (S15 internally refined by ADR-0022 into a 6-Agent serial pipeline). |
| ADR (Architecture Decision Record) | MADR format (Context → Options → Decision → Rationale → Consequences). First-class entity with 12 lifecycle states. |
| Impact Report | Auto-generated pre-change impact analysis: what changed, impact scope graph, data impact preview, required approver list. |
| Atomic Claim Verification | Decomposing each business assertion into atomic claims, then verifying via NLI (Natural Language Inference) whether the KB source actually supports the claim — not merely checking that the KB reference exists. Solves LLM "correct citation, wrong inference" confident hallucinations. See adr/0022. |
| Business Assumption Inventory | Output of Inline AssumptionCheck within BRD-DraftWriter: explicitly listing premises the LLM inferred but which lack direct KB support. Split into Blocker (blocks subsequent generation) and Non-blocker (marked conditional, generation continues). See adr/0022. |
| Soft Lock + Bounded Backtracking | Conflict handling mechanism in BRD-DraftWriter's chapter-by-chapter generation. Each chapter is soft-locked after generation (not immutable); when downstream work discovers upstream defects, localized rollback follows the dependency graph (max 2 times), affecting only the impacted chapters. See adr/0022. |
| Suspect Flag | Multi-BRD conflict detection mechanism: when entities change, traverse the Code Graph dependency graph and automatically mark affected BRDs as needs_update. Detection automated (ARTIAS 99% accuracy), judgment human-driven. See adr/0022. |
| Experience Typology Tree | Core data structure of BRD-VaguenessResolver. Automatically induces a hierarchical tree of requirements dimensions from the tenant's own Schema + BRD history, guiding precise questioning and dimension pruning (TypoAgent, RE 2026). Three-layer progressive construction (Schema → BRD → Cross-BRD pattern mining), strict tenant isolation. See adr/0022. |
| Five Whys Elicitation | Core mechanism of BRD-IntentDeepener: tracing business requirement root causes through "Why?" questioning. Semantic gating (answer mappable to Given/When/Then → stop) + hard depth cap of 3 layers (O'Hara, IEEE 2025). See adr/0022. |
| Compliance Profile | One-time Admin configuration at tenant onboarding listing applicable regulations (jurisdiction/industry/company type/data regions/data types). Drives MCP-19 RAG matching within activated frameworks only, not full regulation library search. Reference: Drata/Sprinto 2025. See adr/0022. |
| Pre-Sync Gate | BRD-Assembler pre-check: blocks Jira/Rally creation when unresolved blockers exist (fuzzy_nodes blocking + unconfirmed Blocking assumptions + Verifier P0 issues). Markdown/PDF export unaffected. See adr/0022. |
| Cascade Refresh | BRD incremental revision mode: after modifying a Section, auto-refresh downstream Sections affected via the dependency graph, leaving unrelated sections untouched. Prevents the "slot machine effect" (FSE Companion '25). See adr/0022. |
| SDD Pipeline (Spec-Driven Development Pipeline) | Phase 2 reserved capability: upon BRD approval, auto-trigger Specify (technical spec) → Plan (task breakdown) → Implement (Workflow/Compute Spec generation). References: GitHub Spec Kit, code_minions, SYNTACT (EMNLP 2025). See adr/0022. |

## Data & Compliance

| Term | Definition |
|------|------------|
| Data Classification Tier | T0 (Public) → T1 (Internal) → T2 (Confidential) → T3 (Restricted). Four-tier data sensitivity classification driving encryption, masking, and export control policies. |
| Query Rewriter | Runtime Plane middleware: injects row-level security predicates (RLS) + column-level dynamic masking functions, dynamically tailoring queries by T0-T3 tier and user role. |
| SLO (Service Level Objective) | 5 critical user journeys defined (NL→Preview ≤15s p95, Freeze→Deploy ≤4h p95, etc.). |
| SLI (Service Level Indicator) | Service level indicator (e.g., p95 Latency, Success Rate). Collected via Prometheus histograms, computed over a 28-day rolling window. |
| Error Budget | The allowable failure margin under SLO (e.g., 5% ≈ 33.6h/month). Budget exhaustion triggers tiered gating policies (degrade → throttle → freeze). |

## Development & Operations

| Term | Definition |
|------|------------|
| Token-Speed Estimation | Methodology replacing traditional person-day estimation with LLM token throughput: Wall-Clock = (Input/Prefill + Output/Decode) / Parallelism. |
| Sub-Agent Parallelism | Orchestrator → N×Worker Agents → Reviewer parallel development pattern, effective parallelism ~0.7N. |
| Canary Deployment | 1%→10%→50%→100% progressive rollout. Simplified during MVP (direct deploy); fully enabled Post-MVP alongside Heavy Engine. |
| Query Service | Four-component service: Metadata Manager + Query Generator + Pushdown Optimizer + Query Cache. Design Plane assists NL→SQL; Runtime Plane executes deterministic query plans. |
| Pushdown Optimization | Pushing WHERE/JOIN/AGGREGATION operations as close to the data source as possible, reducing data transfer while ensuring correctness. |
| CDC (Change Data Capture) | Incremental sync pipeline from PG → Vector/Graph for KB (30s latency) (post-MVP only; MVP has zero CDC pipelines per ADR-0013). |
| STRIDE | Microsoft threat modeling framework: Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege. |

## Regulations & Standards

| Term | Definition |
|------|------------|
| SOX (Sarbanes-Oxley Act) | US public company financial reporting compliance act. Requires immutable audit trails, separation of duties, documented change approvals. |
| GDPR (General Data Protection Regulation) | EU data protection regulation. Requires data minimization, right to erasure, data portability, DPO appointment. |
| HIPAA (Health Insurance Portability and Accountability Act) | US healthcare privacy act. Requires PHI encryption, access controls, audit logging. |
| OWASP LLM Top 10 | Top 10 security threat categories specific to LLM applications (v1.0, 2023). This project assesss each item. |
| arc42 | Software architecture documentation standard (12-section template). This project's document structure aligns with it but does not enforce section-by-section mapping. |
| MADR (Markdown Any Decision Records) | Markdown format standard for ADRs, adopted by this project. |
| C4 Model | Software architecture visualization layered model: System Context → Container → Component → Code. |
| RLS (Row-Level Security) | Row-level security — injecting permission predicates at query compilation stage, ensuring users can only access authorized rows. Implemented by the Query Rewriter. |
| DQ Gate (Data Quality Gate) | Data quality gating — automatically checks data quality rules during Freeze Bridge validation stage; blocks promotion if standards are not met. |

---

*Last Updated: 2026-07-08 | Total Terms: 109 | Sources: docs/01-facts.md, docs/03-architecture.md, adr/0022, adr/0023, adr/0024*
