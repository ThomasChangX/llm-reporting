# 04 - Timeline & Estimation

> Development roadmap, timeline, and resource estimation.
>
> **Estimation Baseline (Token-Speed Methodology)**: Replacing traditional person-day estimation with LLM token throughput.
> Core formula: `Wall-Clock = (Input Tokens ÷ Prefill Speed + Output Tokens ÷ Decode Speed) ÷ Parallelism Factor`
> **Default Model (China Team)**: **DeepSeek V4 Pro** (~80 tps decode, ~400 tps prefill, Input $0.50/M, Output $2.00/M).
> **Default Model (US Team)**: **Claude Sonnet 5** (~80 tps decode, ~350 tps prefill, Input $3.00/M, Output $15.00/M).
> **Parallel Strategy**: Superpowers Sub-Agent parallel development (Orchestrator → N× Worker Agents → Reviewer).

---

## Estimation Methodology: Token-Speed Estimation

### A. Token Throughput Model

The traditional "1 day = 8 effective development hours" assumption no longer holds in AI-assisted development. LLM code generation speed is determined by **Token Throughput Rate**, not human typing speed. This project uses the Token-Speed model in place of person-day estimation.

#### A.1 Model Parameters (Dual-Model Dual-Region Baseline)

| Parameter | DeepSeek V4 Pro (China Team) | Claude Sonnet 5 (US Team) |
|------|---------------------------|---------------------------|
| **Decode Speed** | ~80 tokens/sec | ~80 tokens/sec |
| **Prefill Speed** | ~400 tokens/sec | ~350 tokens/sec |
| **Context Window** | 128K | 200K |
| **Thinking Overhead** | ~1.5× (CoT internal) | ~1.2× (extended thinking) |
| **Input Price** ($/M) | $0.50 | $3.00 |
| **Output Price** ($/M) | $2.00 | $15.00 |
| **Effective Throughput** | `elapsed = input/400 + output/80 + overhead` | `elapsed = input/350 + output/80 + overhead` |

> DeepSeek V4 Pro provides comparable generation speed at ~14% of Sonnet 5's price, suitable for China team large-scale parallel development. Sonnet 5 has stronger deep reasoning on complex multi-step tasks (Tier 3-4), potentially reducing iteration rounds.

#### A.2 Task Complexity Tiers (Token Profiles)

Each development task is classified into 4 Tiers by complexity, each with a corresponding Token consumption profile:

| Tier | Complexity | Typical Tasks | Input Tokens | Output Tokens | Iterations | Per-Task Token Total |
| --------------------- | ------ | ------------------------------------------------ | ------------ | ------------- | -------- | ----------------- |
| **Tier 1** (Simple) | Low | CRUD endpoints, config files, Schema definitions, constant enums | ~5K | ~2K | 1 | ~7K |
| **Tier 2** (Moderate) | Medium | Service implementation, API integration, test generation, middleware | ~15K | ~8K | 2-3 | ~35K-55K |
| **Tier 3** (Complex) | High | Engine design, distributed systems, security modules, data Pipeline | ~40K | ~20K | 3-5 | ~140K-300K |
| **Tier 4** (Novel) | Extreme | Architecture design, new algorithms, multi-system integration, cross-module protocols | ~80K | ~40K | 5-8 | ~520K-1,040K |

**Iteration Notes**: Each iteration includes "Generate → Review → Fix → Regenerate". Higher Tiers have lower first-pass correctness probability and require more iterations.

#### A.3 Single-Task Time Estimation Formula

```
Wall-Clock (minutes) = (Input_Tokens / 300 + Output_Tokens / 60) × Iterations / Parallelism_Factor / 60
```

Where:
- `Input_Tokens / 300` = Prefill phase duration (seconds). Note: Uses ~300 tps effective prefill (vs. stated 350-400 tps raw) to account for context-switching, prompt assembly, and tool-call round-trip overhead.
- `Output_Tokens / 60` = Decode phase duration (seconds). Note: Uses ~60 tps effective decode (vs. stated 80 tps raw) to account for thinking/CoT overhead, stream buffering, and review-fix cycles within each iteration.
- `Iterations` = Tier-corresponding iteration count (median)
- `Parallelism_Factor` = Internal parallelization degree of the task (see Section B)

**Example Calculation**:

| Task | Tier | Input | Output | Iter | Parallelism | Wall-Clock |
| --------------------- | ---- | ----- | ------ | ---- | ----------- | ---------- |
| CRUD endpoint (single resource) | T1 | 5K | 2K | 1 | 1× | ~50 sec |
| REST API Integration Service | T2 | 15K | 8K | 2.5 | 2× | ~4 min |
| DuckDB Engine Integration | T3 | 40K | 20K | 4 | 1× | ~31.1 min |
| Cross-system Recon Engine | T4 | 80K | 40K | 6.5 | 1× | ~101.1 min |

---

### B. Sub-Agent Parallel Model

The core acceleration from AI-assisted development comes from **Sub-Agent Parallelism** — multiple Worker Agents simultaneously process independent sub-tasks.

#### B.1 Agent Hierarchy Architecture

```
                    ┌─────────────┐
                    │ Orchestrator │  ← Task decomposition, assignment, merging
                    │   Agent      │     Overhead: ~15-20% of total Tokens
                    └──────┬──────┘
           ┌───────────────┼───────────────┐
    ┌──────┴──────┐ ┌──────┴──────┐ ┌──────┴──────┐
    │  Worker #1  │ │  Worker #2  │ │  Worker #N  │  ← N=3-8 parallel execution
    │  (Sub-Task) │ │  (Sub-Task) │ │  (Sub-Task) │
    └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
           └───────────────┼───────────────┘
                    ┌──────┴──────┐
                    │  Reviewer   │  ← Consistency review, merge conflicts
                    │   Agent     │     Overhead: ~10% of total Tokens
                    └─────────────┘
```

**Total Agent Overhead**: Orchestrator (~17.5%) + Reviewer (~10%) ≈ **+27.5% additional Token consumption**. This overhead has been factored into the Token estimates for all Phases below (Agent scheduling tax).

### B.2 Parallel Efficiency Matrix

> **Status**: Structure defined; efficiency calibrations pending empirical measurement from Phase 0-2 pilot runs.

**Purpose**: This matrix quantifies how Sub-Agent parallelism reduces wall-clock time across different task types. Each cell represents the effective Parallelism Factor (actual speedup relative to single-agent execution) given the number of Worker Agents and task characteristics (dependency graph shape, shared context requirements, merge complexity).

#### B.2.1 Efficiency Factor Components

The effective parallelism factor is decomposed into:

```
Effective_Parallelism = N_workers × Coupling_Penalty × Merge_Overhead × Context_Reuse_Bonus
```

| Component | Symbol | Definition | Range |
|-----------|--------|------------|-------|
| Worker Count | N | Number of parallel Worker Agents | 3–8 |
| Coupling Penalty | C | Loss from inter-task dependencies forcing serialization | 0.5 (tightly coupled) – 1.0 (embarrassingly parallel) |
| Merge Overhead | M | Reviewer Agent cost to reconcile N outputs | 0.85 (N=3) – 0.65 (N=8) |
| Context Reuse Bonus | R | Gain from shared KB context across workers | 1.0 (no reuse) – 1.25 (high reuse) |

#### B.2.2 Efficiency Matrix by Task Type

| Task Profile | Dependency Shape | N=3 | N=4 | N=5 | N=6 | N=7 | N=8 | Optimal N | Notes |
|-------------|-----------------|-----|-----|-----|-----|-----|-----|-----------|-------|
| **Independent CRUD endpoints** | None (fan-out) | 2.7× | 3.5× | 4.2× | 4.8× | 5.3× | 5.7× | 6–8 | High context reuse possible (shared schema) |
| **Service implementation (shared schema)** | Light (shared DB) | 2.5× | 3.2× | 3.8× | 4.3× | 4.7× | 5.0× | 5–6 | Merge overhead grows with schema coupling |
| **Test generation (per module)** | None (per-file) | 2.8× | 3.6× | 4.4× | 5.1× | 5.7× | 6.1× | 6–8 | Embarrassingly parallel; minimal merge |
| **ETL pipeline components** | DAG (sequential stages) | 2.1× | 2.6× | 2.9× | 3.1× | 3.2× | 3.3× | 3–5 | Stage dependencies limit parallelism |
| **KB domain entry population** | Independent domains | 2.7× | 3.5× | 4.2× | 4.8× | 5.3× | 5.7× | 6–8 | 9 KB domains map naturally to workers |
| **Design Plane component build** | Moderate (UI+Engine) | 2.3× | 2.9× | 3.4× | 3.7× | 3.9× | 4.0× | 4–5 | Frontend/backend coupling limits parallelism |
| **Cross-cutting concerns (auth, audit)** | High (penetrates all) | 1.5× | 1.7× | 1.8× | 1.9× | 1.9× | 2.0× | 3–4 | Cross-cutting; best done sequentially or with 2-3 workers |
| **Architecture/ADR generation** | Sequential (depends on prior decisions) | 1.3× | 1.4× | 1.5× | 1.5× | 1.5× | 1.5× | 1–2 | Decisions cascade; parallelism limited |

> **Values above are theoretical baselines** derived from dependency graph analysis and industry benchmarks for AI-assisted parallel development. To be empirically calibrated from Phase 0-2 pilot data and updated monthly thereafter.

#### B.2.3 Orchestrator Overhead Breakdown

| Overhead Type | % of Total Tokens | Description |
|---------------|-------------------|-------------|
| Task Decomposition | ~8% | Orchestrator analyzes epic → generates N sub-task specs |
| Context Assembly | ~5% | Per-worker KB context retrieval and assembly |
| Assignment & Dispatch | ~2% | Routing sub-tasks to available workers |
| Progress Monitoring | ~2.5% | Polling worker status, detecting stalls |
| **Total Orchestrator** | **~17.5%** | Already factored into phase Token estimates |

#### B.2.4 Merge Conflict Matrix

Probability of merge conflicts requiring Reviewer rework, by number of workers modifying overlapping artifacts:

| Artifact Type | N=3 | N=4 | N=5 | N=6 | N=7 | N=8 |
|---------------|-----|-----|-----|-----|-----|-----|
| Compute Spec YAML (single file) | 15% | 25% | 38% | 50% | 62% | 72% |
| Python service modules (separate files) | 5% | 10% | 15% | 22% | 30% | 38% |
| KB entries (separate domains) | 3% | 8% | 12% | 18% | 24% | 30% |
| Frontend components (separate files) | 8% | 15% | 22% | 30% | 38% | 45% |
| Configuration files | 20% | 35% | 50% | 62% | 72% | 80% |

> **Values above are theoretical baselines** derived from merge conflict probability modeling. To be empirically calibrated from Phase 0-2 Git merge statistics and updated monthly thereafter.

#### B.2.5 Recommended Parallelism Strategy by Phase

| Phase | Dominant Task Type | Recommended N | Rationale |
|-------|-------------------|---------------|-----------|
| 0: Foundation | Cross-cutting + Architecture | 2–3 | High coupling; ADRs cascade |
| 1: Core Compute | ETL + Service (moderate coupling) | 4–5 | Balance speed vs. merge cost |
| 2: KB | Independent domain population | 5–7 | 9 domains are loosely coupled |
| 3: Design Plane | UI + Engine (moderate coupling) | 4–5 | Frontend/backend split |
| 4: Freeze Bridge | Pipeline (sequential stages) | 3–4 | Stage dependencies |
| 5: Runtime | Independent services | 5–6 | Runtime components loosely coupled |
| 6: Enterprise | Cross-cutting (high coupling) | 3–4 | Auth, audit, compliance penetrate all |
| 7: Advanced | Feature modules (moderate) | 4–6 | Feature independence after core stable |
| 8: Polish | Independent refinements | 6–8 | Maximum fan-out for polish tasks |

---

## Phase 3-8 Development Roadmaps

> **Global Status**: Phase structure and FR-to-phase mapping defined (see traceability matrix in docs/02-requirement.md). Detailed task breakdowns, week boundaries, and staffing assignments below have been estimated using the Token-Speed methodology; values will be calibrated further upon Phase 0-2 velocity data.

---

### Phase 3: Design Plane (Weeks 13–18)

> **Status**: Structure defined; detailed task breakdown pending Phase 2 completion and Architecture Review sign-off.

**Phase Objective**: Build the AI-assisted exploration and authoring layer — the Conversation Interface, Visual Designer, Workbench, and AI Copilot Engine. This is where users spend 80%+ of their interaction time.

| Milestone | Target Week | Deliverables | Dependencies |
|-----------|-------------|-------------|--------------|
| M3.1: Conversation Interface MVP | W14 | Intent Parser (50+ intent catalog), Context Resolver with KB integration, basic Plan Generator → Artifact Builder pipeline | Phase 2: KB operational (FR4, FR32-FR36) |
| M3.2: Visual Designer — Report + ETL | W15 | Report Designer (drag-drop canvas), ETL Designer (node-edge graph), Design Artifact YAML generation | M3.1 (Conversation Interface for hybrid workflow) |
| M3.3: AI Copilot Engine — Core | W15 | Pluggable LLM Provider (DeepSeek + Claude adapters), KB Retriever (hybrid search), Reasoning Engine (CoT + confidence scoring) | M3.1 (needs Conversation Interface as client), ADR-0009 (dual-model), ADR-0016 (orchestration) |
| M3.4: Workbench + VCS Integration | W16 | Session = Branch model, Diff Preview, PR Workflow integration, Conflict Resolution UI | M3.2 (Designer produces artifacts to manage), ADR-0006 (freeze bridge independence) |
| M3.5: Light Engine Integration | W17 | DuckDB + Polars sandbox, sampled data preview, sub-second query feedback loop | Phase 1: Compute Spec engine interface (FR14), ADR-0011 (materialize) |
| M3.6: Prompt Injection Defense | W18 | Input Sanitization, Instruction Boundary wrapping, KB Content Sanitization, Output Guard | M3.3 (all LLM calls pass through this) |

**Key FR Coverage**: FR1 (AI-Assisted Exploration), FR5 (Reporting), FR6 (ETL Workflow), FR29 (AI Agent Architecture), FR30.1-30.2 (Agent Customization basics)
**NFR Coverage**: NFR3.1 (NL→Preview P95 ≤ 3s), NFR6.2 (first-report < 15 min), NFR1.2 (critical paths independent of LLM)
**Architecture Reference**: docs/03-architecture.md §3 (Design Plane), §3.1 (Conversation Interface), §3.2 (Design Artifact Schema), §3.3 (Workbench), §3.4 (Component Architecture)
**ADR References**: ADR-0002 (LLM Role Positioning), ADR-0009 (Dual-Model Pricing), ADR-0015 (Agent Triage), ADR-0016 (Dual-Mode Orchestration), ADR-0019 (Memory Architecture)
**Team**: 3 engineers (1 frontend + 1 backend + 1 AI/LLM) | **Budget**: See docs/05-cost.md §2.1, §2.2

**Task Token Profile** (per §A.2 methodology):

| Component | Tier | Est. Tasks | Input/Output per Task | Est. Total Tokens | Parallelism Factor |
|-----------|------|------------|----------------------|-------------------|-------------------|
| Intent Parser + Catalog | T2 | 8 | 15K/8K per intent | 360K | 3× |
| Context Resolver | T3 | 4 | 40K/20K | 880K | 2× |
| Plan Generator + Artifact Builder | T3 | 5 | 40K/20K | 1,100K | 2× |
| Report Designer (frontend) | T2 | 12 | 15K/8K | 540K | 4× |
| ETL Designer (frontend) | T2 | 10 | 15K/8K | 450K | 4× |
| LLM Provider Adapters | T2 | 4 | 15K/8K per adapter | 180K | 2× |
| KB Retriever + Ranking | T3 | 3 | 40K/20K | 660K | 2× |
| Reasoning Engine | T3 | 3 | 40K/20K | 660K | 1× |
| Workbench VCS Integration | T2 | 6 | 15K/8K | 270K | 3× |
| Light Engine Sandbox | T2 | 5 | 15K/8K | 225K | 2× |
| Prompt Injection Defense | T3 | 4 | 40K/20K | 880K | 2× |
| **Phase 3 Total** | — | **64** | — | **7,911K** (incl. +27.5% agent overhead) | — |

---

### Phase 4: Freeze Bridge (Weeks 19–23)

> **Status**: Structure defined; detailed task breakdown pending Phase 3 Design Artifact schema finalization.

**Phase Objective**: Build the independent transition plane — the Spec Refinement Assistant, Validation Engine, Test Runner, CI/CD Pipeline, and Release Manager. This is the critical governance boundary between AI exploration and deterministic production.

| Milestone | Target Week | Deliverables | Dependencies |
|-----------|-------------|-------------|--------------|
| M4.1: Spec Refinement Assistant | W20 | Fuzzy Node Scanner, Determinization Proposal Engine, Resolution Recorder (immutable audit) | Phase 3: Design Artifact schema stable (FR13), ADR-0006 (freeze bridge independence) |
| M4.2: Validation Engine | W20 | Schema Validator, DQ Gate (inline checks from Data Health framework), Logical Integrity Checker | M4.1 (refined specs enter validation), ADR-0014 (data health framework) |
| M4.3: Test Runner (Sandbox) | W21 | Isolated Sandbox execution, Snapshot comparison engine, Regression test framework, Baseline management | M4.2 (validated specs enter testing), FR26 (Execution Sandbox) |
| M4.4: CI/CD Pipeline | W22 | Build → Test → Deploy pipeline, Per-PR sandbox environments, Infrastructure as Code base | M4.3 (testing integrated), FR20 (DevOps & CI/CD) |
| M4.5: Canary Gating & Auto-Rollback | W22 | 4-stage canary (1%→10%→50%→100%), Gating criteria engine, Auto-rollback mechanism, Quarantine system | M4.4 (deployment pipeline), FR8.4 (Canary Deployment) |
| M4.6: Release Manager + Pre/Post-Change Docs | W23 | Release workflow, Pre-Change Impact Report auto-generation, Post-Change Summary auto-generation | M4.5 (canary gating), FR28.1-28.2 (Change Intelligence) |

**Key FR Coverage**: FR2 (Workflow Freeze & Script), FR8 (Enterprise SDLC), FR20 (DevOps & CI/CD), FR23 (BRD & ADR), FR28 (Change Intelligence basics)
**NFR Coverage**: NFR1.1 (deterministic frozen scripts), NFR3.2 (1M rows P95 < 5min)
**Architecture Reference**: docs/03-architecture.md §4 (Freeze Bridge), §4.1 (Spec Refinement Assistant), §4.2 (Canary Gating), §4.3 (Fuzzy Node Detection)
**ADR References**: ADR-0006 (Freeze Bridge Independence), ADR-0014 (Data Health Check Framework), ADR-0017 (Verified Path Saga Semantics), ADR-0021 (VP Promotion & Concurrency), ADR-0022 (BRD Generation Pipeline)
**Team**: 2 engineers (1 backend + 1 DevOps) | **Budget**: See docs/05-cost.md §2.1, §2.2

**Task Token Profile**:

| Component | Tier | Est. Tasks | Input/Output per Task | Est. Total Tokens | Parallelism Factor |
|-----------|------|------------|----------------------|-------------------|-------------------|
| Fuzzy Node Scanner | T2 | 4 | 15K/8K | 180K | 2× |
| Proposal Engine (per fuzzy type) | T3 | 5 | 40K/20K | 1,100K | 3× |
| Schema Validator | T2 | 3 | 15K/8K | 135K | 2× |
| DQ Gate Integration | T3 | 3 | 40K/20K | 660K | 2× |
| Sandbox Test Runner | T3 | 5 | 40K/20K | 1,100K | 2× |
| Snapshot Comparison Engine | T2 | 3 | 15K/8K | 135K | 2× |
| CI/CD Pipeline (Build/Test/Deploy) | T2 | 8 | 15K/8K | 360K | 3× |
| Canary Gating Engine | T3 | 4 | 40K/20K | 880K | 1× |
| Auto-Rollback Mechanism | T3 | 3 | 40K/20K | 660K | 1× |
| Release Manager | T2 | 5 | 15K/8K | 225K | 2× |
| Impact Report Generation | T3 | 3 | 40K/20K | 660K | 2× |
| **Phase 4 Total** | — | **46** | — | **7,771K** (incl. +27.5% agent overhead) | — |

---

### Phase 5: Runtime Plane (Weeks 24–28)

> **Status**: Structure defined; detailed task breakdown pending Phase 4 Freeze Bridge stabilization.

**Phase Objective**: Build the deterministic, zero-AI-side-effect production execution layer — Workflow Executor, Scheduler, Data Connectors, Output Renderer, Incident Manager, and Heavy Engine integration (Spark, post-MVP).

| Milestone | Target Week | Deliverables | Dependencies |
|-----------|-------------|-------------|--------------|
| M5.1: Workflow Executor Core | W25 | DAG execution engine, Job Sandbox isolation (per FR26), State machine with retry/rollback, Immutable inter-job state passing | Phase 4: Freeze Bridge produces validated Specs to execute |
| M5.2: Scheduler | W25 | Cron/Event/Manual/API/Webhook triggers, Timezone-aware scheduling, Concurrency control (three-tier), Missed-execution compensation | M5.1 (executor is the target) |
| M5.3: Data Connector Adapters (L1-L3) | W26 | File connectors (S3/SFTP/HDFS), DB connectors (JDBC/ODBC PG/MySQL/Oracle), API connectors (REST/GraphQL), Unified DataSource Interface | Phase 1: Integration Framework interface (FR15), ADR-0007 (Query Service) |
| M5.4: Output Renderer | W26 | PDF/Excel/CSV/JSON/Parquet renderers, Email/Slack/Webhook delivery channels, Format System binding (FR24) | M5.1 (executor triggers output) |
| M5.5: Query Service — Runtime | W27 | Metadata Manager (schema discovery + versioning), Query Generator (NL→SQL), Pushdown Optimizer (predicate/aggregation/JOIN pushdown), Result Cache | Phase 1: Query Service component (FR15b), ADR-0007 |
| M5.6: Incident Manager | W27 | Auto-incident creation on failure, Context assembly (workflow ID, logs, snapshots), Auto-routing, Resolution tracking | M5.1 (executor emits failures) |
| M5.7: Resilience Patterns | W28 | Circuit Breaker (per data source), Bulkhead (per-tenant sandbox pools), Retry with Backoff, Graceful Degradation (opt-in Light→Heavy fallback), Timeout Propagation, Dead Letter Queue | M5.1-M5.4 (components to protect) |
| M5.8: Heavy Engine — Spark (Post-MVP) | W28 | Spark integration for TB/PB-scale processing, Distributed execution, Engine switching in Compute Spec (FR14.3) | M5.1 (executor), ADR-0008 (Large-Scale Data Strategy) |

**Key FR Coverage**: FR13 (Compute Spec execution), FR14.2 (Heavy Engine), FR15 (Integration Framework L1-L3), FR15b (Query Service), FR15c (Large-Scale Data), FR25 (Writeback Job), FR26 (Execution Sandbox), FR27 (Log System), FR39 (Scheduler)
**NFR Coverage**: NFR3.2 (1M rows P95 < 5min), NFR5.1 (elastic scaling), NFR7.2 (Runtime availability ≥ 99.95%)
**Architecture Reference**: docs/03-architecture.md §5 (Runtime Plane), §5.1 (Resilience Patterns), §5.2 (Data Classification Tiers), §5.3 (Query Service)
**ADR References**: ADR-0007 (Query Service Component), ADR-0008 (Large-Scale Data Strategy), ADR-0011 (Materialize Job Type), ADR-0017 (Verified Path Saga)
**Team**: 3 engineers (2 backend + 1 data) | **Budget**: See docs/05-cost.md §2.1, §2.2

**Task Token Profile**:

| Component | Tier | Est. Tasks | Input/Output per Task | Est. Total Tokens | Parallelism Factor |
|-----------|------|------------|----------------------|-------------------|-------------------|
| Workflow Executor Core | T4 | 3 | 80K/40K | 2,340K | 1× |
| DAG Engine | T3 | 3 | 40K/20K | 660K | 1× |
| Job Sandbox (cgroups) | T2 | 4 | 15K/8K | 180K | 2× |
| Scheduler (all trigger types) | T3 | 5 | 40K/20K | 1,100K | 2× |
| File Connectors (5 formats) | T1-T2 | 10 | 5K-15K/2K-8K | 250K | 5× |
| DB Connectors (5 targets) | T2 | 10 | 15K/8K each | 450K | 5× |
| API Connectors (3 protocols) | T2 | 6 | 15K/8K each | 270K | 3× |
| Output Renderers (5 formats) | T2 | 10 | 15K/8K each | 450K | 5× |
| Pushdown Optimizer | T3 | 4 | 40K/20K | 880K | 1× |
| Result Cache | T2 | 3 | 15K/8K | 135K | 1× |
| Incident Manager | T2 | 5 | 15K/8K | 225K | 2× |
| Resilience Patterns (6 patterns) | T2-T3 | 8 | 15K-40K/8K-20K | 1,040K | 3× |
| Spark Integration | T4 | 2 | 80K/40K | 1,560K | 1× |
| **Phase 5 Total** | — | **73** | — | **12,163K** (incl. +27.5% agent overhead) | — |

---

### Phase 6: Enterprise Readiness (Weeks 29–32)

> **Status**: Structure defined; detailed task breakdown pending Phase 5 Runtime stabilization.

**Phase Objective**: Build the enterprise governance layer — Entitlement Control (RBAC/RLS/CLS), Audit & Compliance, Multi-tenancy isolation, API Gateway, Notification System, Backup & DR, and the Data Health Check Framework (Reconciliation + Quality Rules).

| Milestone | Target Week | Deliverables | Dependencies |
|-----------|-------------|-------------|--------------|
| M6.1: Entitlement Control — RBAC | W30 | Role-Permission model (Viewer/Analyst/Approver/Admin/Developer), Custom role support, OAuth 2.0/Kerberos/SAML/SSO integration | Phase 0: Auth Gateway foundation |
| M6.2: Data Masking & RLS | W30 | Static Masking (ingestion-time), Dynamic Masking (query-time, role-based), Row-Level Security predicates, Aggregation Restrictions, Query Rewriter integration | M6.1 (roles define masking rules), FR16 |
| M6.3: Audit & Compliance | W31 | Complete audit log (who/when/what/changes), Data lineage tracking (source→transform→destination), Exportable audit files, SOX/HIPAA/GDPR controls | M5.1 (Runtime executions need auditing), FR10 |
| M6.4: Multi-Tenancy Isolation | W31 | Tenant data isolation (process/node/cluster levels), Tenant-aware API Gateway routing, Per-tenant configuration, Tiered feature/compute/storage model | M6.1 (RBAC per tenant), FR12, FR38 |
| M6.5: Data Health Check Framework | W31 | type: rule — 7 dimensions (Completeness/Accuracy/Consistency/Timeliness/Uniqueness/Validity/Temporal_Consistency), type: recon — Match Key + Tolerance Profile + 3-way triage, type: anomaly — 5 ML methods, Severity levels (Error/Warning/Info), Execution modes (auto/scheduled/manual/on_recon_complete) | M5.1 (Runtime generates data to validate), ADR-0014 |
| M6.6: API Gateway | W32 | Unified entry (REST/gRPC), Rate Limiting (burst + quota), Tenant isolation enforcement, API versioning (URL + Header), Request/response logging, Auth integration | M6.4 (tenant isolation), FR38 |
| M6.7: Notification System | W32 | Multi-channel (Email/Slack/Teams/Webhook/SMS), Notification templating, Priority & tiering (Critical/Warning/Info), User preference config, Delivery guarantee (at-least-once) | M5.6 (Incident Manager triggers notifications), FR37 |
| M6.8: Backup & Disaster Recovery | W32 | Backup scope (Spec/KB/Audit/Config), RPO < 1hr (core) / < 24hr (audit), RTO < 4hr (core) / < 24hr (non-critical), Offsite multi-copy, Immutable backups, Tenant-level backup | M6.3 (audit logs need backup), FR41 |
| M6.9: Support & Ticket Integration | W32 | Embedded Support Portal, External ticketing integration (Jira SM/ServiceNow/Zendesk), Auto-ticket from failures, Bidirectional artifact linking | M5.6 (Incident Manager), FR21 |

**Key FR Coverage**: FR7 (Adjustment — enterprise approval chains), FR9 (Entitlement Control), FR10 (Audit & Compliance), FR10b (Privacy & Data Subject Rights), FR12 (Multi-Tenancy), FR16 (Data Masking & RLS), FR18 (Reconciliation), FR19 (Data Quality), FR21 (Support & Ticket), FR22 (Project Tracking), FR23 (BRD & ADR), FR31 (Agent Permission Control), FR36 (KB Governance), FR37 (Notification), FR38 (API Gateway), FR41 (Backup & DR), FR42 (Config Management)
**NFR Coverage**: NFR4 (Security), NFR5.1 (scalability), NFR9 (Data Governance & Compliance)
**Architecture Reference**: docs/03-architecture.md §5.2 (Data Classification Tiers), §5.1 (Resilience Patterns), and cross-cutting layer components
**ADR References**: ADR-0014 (Data Health Check Framework), ADR-0015 (Agent Triage), ADR-0020 (Agent Cost Governance)
**Team**: 3 engineers (1 backend + 1 security + 1 DevOps) | **Budget**: See docs/05-cost.md §2.1, §2.2

**Task Token Profile**:

| Component | Tier | Est. Tasks | Input/Output per Task | Est. Total Tokens | Parallelism Factor |
|-----------|------|------------|----------------------|-------------------|-------------------|
| RBAC Engine | T3 | 4 | 40K/20K | 880K | 1× |
| Auth Integration (4 protocols) | T2 | 4 | 15K/8K each | 180K | 4× |
| Query Rewriter (masking + RLS) | T3 | 3 | 40K/20K | 660K | 1× |
| Static Masking (ingestion) | T2 | 3 | 15K/8K | 135K | 2× |
| Dynamic Masking (query-time) | T3 | 3 | 40K/20K | 660K | 1× |
| Audit Trail (full pipeline) | T3 | 4 | 40K/20K | 880K | 2× |
| Data Lineage Engine | T3 | 3 | 40K/20K | 660K | 1× |
| Multi-Tenant Isolation (3 levels) | T3 | 5 | 40K/20K | 1,100K | 2× |
| Data Health — Rule Engine (7 dims) | T3 | 5 | 40K/20K | 1,100K | 2× |
| Data Health — Recon Engine | T4 | 3 | 80K/40K | 2,340K | 1× |
| Data Health — Anomaly (5 methods) | T3 | 5 | 40K/20K | 1,100K | 2× |
| API Gateway | T3 | 5 | 40K/20K | 1,100K | 1× |
| Notification System | T2 | 6 | 15K/8K | 270K | 2× |
| Backup & DR | T2 | 5 | 15K/8K | 225K | 2× |
| Support Portal + Ticketing | T2 | 6 | 15K/8K | 270K | 3× |
| **Phase 6 Total** | — | **64** | — | **14,739K** (incl. +27.5% agent overhead) | — |

---

### Phase 7: Advanced Features (Weeks 33–35)

> **Status**: Structure defined; detailed task breakdown pending Phase 6 Enterprise stabilization. Many Phase 7 features can be parallelized.

**Phase Objective**: Deliver advanced features that differentiate the product — Observation & Suggestion, Dashboard, Email Ingestion, Change Intelligence (full), Agent Customization, Dependency Manager, Hierarchical Multi-Agent Architecture, and Heavy Engine expansion (Trino/Ray if demanded).

| Milestone | Target Week | Deliverables | Dependencies |
|-----------|-------------|-------------|--------------|
| M7.1: Observation & Suggestion Engine | W34 | User behavior pattern detection, Repetitive task identification, Proactive workflow template suggestion, Confidence-scored recommendations | Phase 6: KB fully populated (FR32.6), User Behavior Pattern Store |
| M7.2: Dashboard System | W34 | Drag-drop Dashboard construction, Widget types (KPI cards, trend, bar/line/pie, heatmap, table, text), Cross-Widget linking, Parameterization (global/local), Drill-down/Roll-up | Phase 3: Report Designer foundation, FR5b |
| M7.3: Email Ingestion Pipeline | W34 | Dedicated inbox (kb@[tenant]), Auto-ingestion via forwarding rules, .eml/.msg upload, Structured parsing (From/To/CC/Date/Subject/Body), AI fact extraction, Attachment parsing (Excel→tables, PDF→text, images→OCR), Confirm/Edit/Dismiss workflow | Phase 2: KB Email Record domain, FR17 |
| M7.4: Change Intelligence — Full | W34 | Pre-Change Impact Report (Diff + Why + impact graph + data preview), Post-Change Summary (actual vs. design + DAG diff + Cost Profile), AI Knowledge Agent (NL queries on Code Graph + KB + Log), Code Graph incremental updates | Phase 4: Pre/Post-Change doc generation basics, FR28 |
| M7.5: Agent Customization & Workflow | W35 | Agent Workflow as Compute Spec type (meta-workflow), Per-team Agent Workflow definitions, Model selection three-layer preference (Tenant/Group/Individual), Scenario-based model routing (sensitive→private, general→SaaS) | Phase 3: AI Copilot Engine, FR30, ADR-0016 |
| M7.6: Dependency Manager | W35 | Auto-discovery of cross-Workflow data dependencies, Dependency topology visualization (DAG), Upstream change impact alerting, Version snapshots per execution, Deprecation marking + migration suggestions | Phase 5: Runtime operational, FR40 |
| M7.7: Vendor Promotion & Concurrency | W35 | Verified Path promotion with saga semantics, Concurrency control for parallel VP execution, Compensation transactions on failure | ADR-0017 (Verified Path Saga), ADR-0021 (VP Promotion & Concurrency) |
| M7.8: Hierarchical Multi-Agent (Evolution) | W35 | Central Reasoner + Sub-Agent layered architecture, MVP's 18 Skills (S01-S18) become Sub-Agent tool library, Monte Carlo-aligned 2025-2026 production architecture | All prior phases, ADR-0016, Architecture §22A.6 |
| M7.9: Heavy Engine — Trino/Ray (if demanded) | W35 | Trino for federated queries across heterogeneous sources, Ray for distributed Python/Polars transforms | M5.8 (Spark), clear customer demand signal, ADR-0008 |

**Key FR Coverage**: FR3 (Observation & Suggestion), FR5b (Dashboard), FR17 (Email Ingestion), FR28 (Change Intelligence — full), FR30 (Agent Customization), FR40 (Dependency Manager), FR15.4 (Message/Stream connectors), FR15.5 (Custom Plugin SDK), FR27.4 (AI-Powered Log Analysis)
**NFR Coverage**: NFR5.2 (plugin extensibility), NFR8.4 (hot-loading plugins)
**Architecture Reference**: docs/03-architecture.md §22A.6 (Hierarchical Multi-Agent Architecture)
**ADR References**: ADR-0016 (Dual-Mode Agent Orchestration), ADR-0017 (Verified Path Saga), ADR-0021 (VP Promotion & Concurrency), ADR-0022 (BRD Generation Pipeline)
**Team**: 3 engineers (1 full-stack + 1 AI + 1 data) | **Budget**: See docs/05-cost.md §2.1, §2.2

**Task Token Profile**:

| Component | Tier | Est. Tasks | Input/Output per Task | Est. Total Tokens | Parallelism Factor |
|-----------|------|------------|----------------------|-------------------|-------------------|
| Pattern Detection Engine | T3 | 4 | 40K/20K | 880K | 1× |
| Suggestion Generator | T2 | 4 | 15K/8K | 180K | 2× |
| Dashboard Canvas + Widgets | T3 | 6 | 40K/20K | 1,320K | 3× |
| Cross-Widget Linking | T3 | 3 | 40K/20K | 660K | 1× |
| Email Ingestion (7 sub-capabilities) | T2-T3 | 10 | 15K-40K/8K-20K | 1,300K | 4× |
| Change Intelligence — Full | T4 | 3 | 80K/40K | 2,340K | 2× |
| AI Knowledge Agent | T4 | 2 | 80K/40K | 1,560K | 1× |
| Agent Workflow System | T3 | 4 | 40K/20K | 880K | 2× |
| Dependency Manager | T3 | 3 | 40K/20K | 660K | 1× |
| VP Promotion Engine | T4 | 3 | 80K/40K | 2,340K | 1× |
| Hierarchical Multi-Agent | T4 | 2 | 80K/40K | 1,560K | 1× |
| Trino/Ray Integration | T4 | 1 | 80K/40K | 780K | 1× |
| **Phase 7 Total** | — | **45** | — | **18,437K** (incl. +27.5% agent overhead) | — |

---

### Phase 8: Polish & Launch (Weeks 35–36)

> **Status**: Structure defined; detailed task breakdown pending Phase 7 stabilization. Phase 8 is inherently "fan-out" — many independent polish tasks can execute in parallel.

**Phase Objective**: Hardening, performance optimization, documentation, accessibility, i18n, long-tail integrations, and production launch preparation. This phase assumes all P0/P1 features are complete and shifts focus to quality and completeness.

| Milestone | Target Week | Deliverables | Dependencies |
|-----------|-------------|-------------|--------------|
| M8.1: Performance Optimization | W35 | Profile and optimize hot paths (Query Service, KB Retrieval, Workflow Executor), Target: NFR3.1 (P95 ≤ 3s), NFR3.2 (1M rows P95 < 5min), KB vector search latency < 200ms | All prior phases |
| M8.2: Accessibility (WCAG 2.1 AA) | W35 | Full accessibility audit, Remediation of all AA violations, Screen reader testing, Keyboard navigation audit, Color contrast compliance | Phase 3: Design Plane UI, Phase 7: Dashboard UI |
| M8.3: Internationalization (i18n) | W35 | Chinese/English bilingual interface, i18n framework extensible to additional languages, RTL support consideration | All UI surfaces (Phase 3, 6, 7) |
| M8.4: Long-Tail Connectors (L4-L5) | W36 | Message/Stream connectors (Kafka/RabbitMQ/MQ/Pulsar), Custom Plugin SDK, Plugin marketplace foundation | Phase 5: L1-L3 connectors, FR15.4-15.5 |
| M8.5: Documentation & Training | W36 | User documentation (Analyst/Approver/Admin/Developer guides), API documentation, Deployment guides (AWS/Azure/GCP/K8s), Video tutorials, In-app guided tours | All features complete |
| M8.6: Security Hardening | W36 | Penetration testing, Vulnerability scanning, Dependency audit, Secret rotation, Security review sign-off | Phase 6: Enterprise security base |
| M8.7: Production Launch Prep | W36 | Load testing (target: 100 tenants, 1000 concurrent workflows), DR failover drill, SLA monitoring dashboards, Runbook creation, On-call rotation setup, Go/No-Go checklist | All prior phases, FR41.5 (recovery drills) |
| M8.8: Feature Flags & Config Management | W36 | Feature flag system (per-tenant/group/user), Runtime hot-update configuration, Environment variable layered management, Git-backed config versioning | Phase 6: Config base, FR42 |
| M8.9: Feedback Loop & Telemetry | W36 | Usage analytics (opt-in), User satisfaction scoring, Error rate dashboards, Cost-per-workflow tracking, Model quality monitoring (CI Regression Gate from ADR-0020) | All phases, ADR-0018 (Evaluation Framework), ADR-0020 (Cost Governance) |

**Key FR Coverage**: FR15.4-15.5 (L4-L5 Connectors), FR27.4 (AI-Powered Log Analysis), FR42 (Config Management), plus hardening of all P0/P1 FRs
**NFR Coverage**: NFR3.1-3.2 (performance targets), NFR6.1 (WCAG 2.1 AA), NFR6.3 (bilingual i18n), NFR6.4 (≤ 3 clicks), NFR7.1 (Design Plane 99.9%), NFR7.2 (Runtime 99.95%), NFR7.3 (DR), NFR8.2 (multi-cloud deployment)
**Architecture Reference**: All architecture sections — final integration validation
**ADR References**: ADR-0018 (Agent Evaluation Framework), ADR-0020 (Agent Cost Governance)
**Team**: 4 engineers (1 full-stack + 1 QA + 1 docs + 1 SRE) | **Budget**: See docs/05-cost.md §2.1, §2.2

**Task Token Profile**:

| Component | Tier | Est. Tasks | Input/Output per Task | Est. Total Tokens | Parallelism Factor |
|-----------|------|------------|----------------------|-------------------|-------------------|
| Performance Profiling & Tuning | T2-T3 | 8 | 15K-40K/8K-20K | 1,040K | 3× |
| Accessibility Remediation | T1-T2 | 12 | 5K-15K/2K-8K | 240K | 6× |
| i18n Framework + Translation | T1-T2 | 10 | 5K-15K/2K-8K | 200K | 8× |
| L4-L5 Connectors | T2 | 8 | 15K/8K each | 360K | 4× |
| Documentation (4 guides) | T2 | 8 | 15K/8K per guide | 360K | 4× |
| Security Audit + Remediation | T2 | 6 | 15K/8K | 270K | 2× |
| Load Testing + DR Drill | T2 | 4 | 15K/8K | 180K | 2× |
| Feature Flags System | T2 | 4 | 15K/8K | 180K | 2× |
| Telemetry + Dashboards | T2 | 6 | 15K/8K | 270K | 3× |
| **Phase 8 Total** | — | **66** | — | **3,953K** (incl. +27.5% agent overhead) | — |

---

## Appendix

> **Status**: Structure defined; content to be populated as each phase completes detailed planning.

### A. Phase Checkpoint Definitions

Each phase boundary is gated by a formal checkpoint review. The following criteria must be satisfied before the next phase can begin resource allocation.

| Checkpoint | Gate Criteria | Evidence Required | Sign-off Authority |
|-----------|---------------|-------------------|-------------------|
| **CP0: Foundation Complete** | (a) Architecture docs approved (ADR-0002/0005/0006), (b) Dev environment operational for all engineers, (c) Token-Speed baseline measured from Phase 0 tasks, (d) CI/CD skeleton passing, (e) Phase 1 task breakdown approved | Architecture doc sign-off, CI dashboard (green), Velocity report | Architecture Lead + Project Sponsor |
| **CP1: Core Compute Complete** | (a) Compute Spec YAML schema stable (all 9 Job types defined), (b) Dual Engine interface validated with DuckDB MVP, (c) Integration Framework (L1-L2) operational, (d) Query Service metadata manager operational, (e) Format System (5 format types) defined | Integration test suite passing, Demo of Compute Spec → DuckDB execution, Schema review sign-off | Tech Lead + Architecture Lead |
| **CP2: KB Complete** | (a) All 9 KB domains populated with sample data, (b) Hybrid search (semantic + keyword + graph) returning results < 200ms P95, (c) KB Write Governance (5 gates) operational, (d) KB ↔ Code Graph bridge edges functional | Search benchmark report, Write governance test suite, Demo of KB context retrieval for sample NL query | Tech Lead + Domain Expert |
| **CP3: Design Plane Complete** | (a) Conversation Interface handling 50+ intents, (b) Visual Designer producing valid Design Artifact YAML, (c) AI Copilot Engine with both LLM adapters operational, (d) Prompt injection defense passing security review, (e) Design Artifact confidence ≥ 0.7 on sample workflows | Intent coverage report, Security review sign-off, UX usability test (NFR6.2: first-report < 15 min) | Product Lead + Security Lead + UX Lead |
| **CP4: Freeze Bridge Complete** | (a) Spec Refinement Assistant resolving all 5 fuzzy node types, (b) Validation Engine passing 100% of well-formed specs, (c) CI/CD pipeline deploying to sandbox, (d) Canary gating (4-stage) operational, (e) Pre/Post-Change doc generation accurate | Canary demo (1%→100%), Fuzzy node resolution test suite, CI/CD dashboard (green) | Tech Lead + DevOps Lead |
| **CP5: Runtime Complete** | (a) Workflow Executor running 100 concurrent workflows, (b) Scheduler handling all 4 trigger types with timezone correctness, (c) L1-L3 connectors passing integration tests, (d) Output Renderer producing all 5 formats, (e) Resilience patterns (6/6) operational, (f) Incident Manager auto-creating tickets | Load test report (100 workflows), Connector integration test suite, Chaos engineering test (circuit breaker + bulkhead), Renderer output validation | Tech Lead + SRE Lead |
| **CP6: Enterprise Complete** | (a) RBAC + RLS + CLS operational with 5 roles, (b) Audit trail capturing all mutation operations, (c) Multi-tenant isolation validated (3 levels), (d) Data Health Framework running all 3 check types, (e) Backup & DR drill passed, (f) API Gateway enforcing rate limits per tenant | Security audit report, Tenant isolation test, DR drill report, Data Health demo (rule + recon + anomaly) | Security Lead + Compliance Lead + Tech Lead |
| **CP7: Advanced Complete** | (a) Observation engine detecting ≥ 3 pattern types, (b) Dashboard with all 6 widget types, (c) Email ingestion pipeline (7 sub-capabilities), (d) Change Intelligence full reports accurate, (e) Agent Customization (3-tier model selection) | Pattern detection accuracy report, Dashboard UX test, Email pipeline integration test, Change Intelligence demo | Product Lead + Tech Lead |
| **CP8: Launch Ready** | (a) All NFR targets met (performance, accessibility, availability), (b) Documentation complete (4 guides), (c) Security hardening signed off, (d) Load test passed (100 tenants, 1000 workflows), (e) DR drill passed, (f) Go/No-Go checklist signed | Performance benchmark report, Accessibility audit (WCAG 2.1 AA), Security scan (clean), Load test report, DR drill report, Signed Go/No-Go | All Leads + Project Sponsor |

### B. Risk Register Template

> Each risk entry should include: Risk ID, Description, Likelihood (1-5), Impact (1-5), Risk Score, Mitigation Strategy, Owner, Review Cadence.

| Risk ID | Description | L | I | Score | Mitigation | Owner | Review |
|---------|-------------|---|---|-------|------------|-------|--------|
| R01 | LLM output quality drift after provider model upgrade breaks Design Plane artifact generation | 3 | 4 | 12 | CI Regression Gate (ADR-0020), Golden Dataset validation, Four-stage model deployment funnel | AI/ML Lead | Monthly |
| R02 | Token cost overrun during Sub-Agent parallel development exceeding phase budget | 4 | 3 | 12 | Hierarchical token quotas (ADR-0020), Tiered enforcement (WARN→THROTTLE→DEGRADE→KILL), Per-phase budget caps | Tech Lead | Weekly |
| R03 | Freeze Bridge fuzzy node resolution rate too low (< 80%), causing reviewer bottleneck | 3 | 4 | 12 | Continuous improvement of Proposal Engine, KB enrichment to reduce fuzzy nodes at source, Fuzzy Node Type coverage monitoring | Architecture Lead | Per sprint |
| R04 | DeepSeek V4 Pro availability degradation in China region affecting development velocity | 2 | 3 | 6 | Dual-model fallback (ADR-0009), Local model cache for common prompts, Staggered sprint schedules to reduce peak concurrency | DevOps Lead | Weekly |
| R05 | Compute Spec schema instability causing cascading rework across phases | 3 | 5 | 15 | Schema versioning from Phase 1, Backward compatibility requirement until Phase 8, Comprehensive integration test suite | Architecture Lead | Per milestone |
| R06 | KB quality insufficient for reliable AI context retrieval (garbage-in-garbage-out) | 3 | 4 | 12 | KB Write Governance (5 gates from Phase 2), Domain Expert review cycles, Staleness Detection (FR36.3), KB health scoring dashboard | Domain Expert | Per sprint |
| R07 | Multi-tenant isolation failure causing cross-tenant data leakage | 2 | 5 | 10 | Three-level isolation (process/node/cluster), Automated isolation tests, Penetration testing in Phase 8, Audit trail monitoring | Security Lead | Monthly |
| R08 | Heavy Engine (Spark) integration complexity delaying Phase 5 beyond schedule | 3 | 2 | 6 | Spark is post-MVP — Phase 5 can ship with DuckDB only, Graceful Degradation pattern (ADR-0008), Clear MVP vs. post-MVP boundary | Tech Lead | Per milestone |
| R09 | API Gateway becoming performance bottleneck under multi-tenant load | 2 | 3 | 6 | Load testing from Phase 5, Horizontal scaling design, Rate limiting prevents cascade, Monitoring dashboards | DevOps Lead | Per milestone |
| R10 | Team velocity below Token-Speed estimates due to unfamiliarity with AI-assisted parallel development | 4 | 3 | 12 | Phase 0-2 pilot calibrates velocity model, Weekly velocity retro, Adjust parallelism factors based on empirical data (B.2 matrix) | Project Manager | Weekly (Phase 0-2), Bi-weekly thereafter |

### C. Milestone Criteria Quick Reference

| Phase | Entrance Criteria | Exit Criteria |
|-------|-------------------|---------------|
| 0: Foundation | Project charter approved | Checkpoint CP0 passed |
| 1: Core Compute | CP0 passed | Checkpoint CP1 passed |
| 2: KB | CP1 passed | Checkpoint CP2 passed |
| 3: Design Plane | CP2 passed | Checkpoint CP3 passed |
| 4: Freeze Bridge | CP3 passed | Checkpoint CP4 passed |
| 5: Runtime | CP4 passed | Checkpoint CP5 passed |
| 6: Enterprise | CP5 passed | Checkpoint CP6 passed |
| 7: Advanced | CP6 passed | Checkpoint CP7 passed |
| 8: Polish & Launch | CP7 passed | Checkpoint CP8 passed → Production Launch |

### D. Token Budget Summary by Phase (Placeholder)

| Phase | Est. Total Tokens (DeepSeek) | Est. LLM Cost (DeepSeek) | Est. Total Tokens (Claude) | Est. LLM Cost (Claude) | Est. Wall-Clock (Calendar Weeks) |
|-------|------------------------------|--------------------------|----------------------------|------------------------|----------------------------------|
| 0: Foundation | 1,020K | $0.95 | 1,020K | $6.60 | 3 |
| 1: Core Compute | 8,288K | $8.35 | 8,288K | $58.50 | 5 |
| 2: KB | 4,080K | $4.15 | 4,080K | $29.10 | 4 |
| 3: Design Plane | 7,911K | $7.85 | 7,911K | $54.90 | 6 |
| 4: Freeze Bridge | 7,771K | $7.80 | 7,771K | $54.60 | 5 |
| 5: Runtime | 12,163K | $12.25 | 12,163K | $85.80 | 5 |
| 6: Enterprise | 14,739K | $14.70 | 14,739K | $102.90 | 4 |
| 7: Advanced | 18,437K | $18.35 | 18,437K | $128.40 | 3 |
| 8: Polish & Launch | 3,953K | $3.90 | 3,953K | $27.30 | 2 |
| **Total** | **78,362K** | **$78.30** | **78,362K** | **$548.10** | **36** (Phases 7 & 8 overlap W35) |

> **Pricing**: DeepSeek V4 Pro — Input $0.50/M, Output $2.00/M (China). Claude Sonnet 5 — Input $3.00/M, Output $15.00/M (US). See ADR-0009.
> **Overhead**: Agent scheduling tax (+27.5%) included in all Token estimates. See §B.1.
> **Calibration**: Values to be populated after Phase 0-2 pilot establishes empirical token-to-wall-clock ratio for this codebase and team.

### E. Key Assumptions & Dependencies Log

| ID | Assumption / Dependency | Holder | Valid Until | Status |
|----|------------------------|--------|-------------|--------|
| A01 | DeepSeek V4 Pro availability and pricing remain stable through project timeline | External (DeepSeek) | 2026-12-31 | Active |
| A02 | Claude Sonnet 5 availability and pricing remain stable through project timeline | External (Anthropic) | 2026-12-31 | Active |
| A03 | Sub-Agent parallelism factor matches B.2 matrix predictions within ±20% | Internal (Team velocity) | Phase 2 completion | To Be Validated |
| A04 | DuckDB + Polars sufficient for MVP; Spark deferred to post-MVP | Internal (Architecture) | Phase 5 start | Active |
| A05 | PostgreSQL + pgvector sufficient for KB until Phase 7+ (no dedicated Vector/Graph DB needed at MVP) | Internal (Architecture) | Phase 7 start | Accepted (ADR-0013) |
| A06 | Four-person core team (2 full-stack + 1 backend/data + 0.5 domain expert + 0.5 DevOps) available full-time for duration | Internal (Staffing) | Project start | To Be Confirmed |
| A07 | All third-party integrations (OAuth, SAML, ticketing systems) have stable APIs | External (Vendors) | Phase 6 start | Active |

---

*Last Updated: 2026-07-04*
