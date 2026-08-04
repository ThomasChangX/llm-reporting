# Agent Memory & Evaluation Framework

> **Origin**: §22I and §22J of [`docs/03-architecture.md`](../../03-architecture.md) | **Sub-project**: [agent-platform](README.md)

## Purpose

This module covers the two feedback and cognition mechanisms that make the Agent Platform improve over time and across sessions:

- **§22I — Agent Evaluation Framework (ADR-0018)**: not single-output scoring, but evaluation of the *entire execution trajectory* — every step from intent recognition to task completion. It defines six-dimension trajectory scoring, compound-error tracking, the Evaluation Flywheel, the Golden Dataset, the three-layer monitoring dashboard, and evaluation frequency. Industry consensus (Amazon Bedrock AgentCore, Future AGI, NVIDIA NeMo 2025–2026) holds that Agent evaluation requires multi-dimensional trajectory scoring plus an evaluation flywheel closing the production feedback loop.
- **§22J — Agent Memory Architecture (ADR-0019)**: Agent memory is not a single database, but a **four-layer cognitive architecture** mapping human cognitive psychology models to technical implementation. Industry consensus (LangGraph Store, Mem0, ENGRAM, Letta/MemGPT 2025–2026) informs the L1 Working / L2 Episodic / L3 Semantic / L4 Procedural split. Financial scenarios additionally require **bitemporal validity tracking** and **provenance marking**.

Together these two sections close the loop: the Evaluation Framework scores trajectories and feeds failures into the Golden Dataset, while the Memory Architecture gives the Agent cross-session continuity (L2 Episodic) and durable distilled facts (L3 Semantic) that improve future trajectories. The two are tightly coupled — the §22K.6 CI Regression Gate in [`verified-path-and-governance.md`](verified-path-and-governance.md) runs the Golden Dataset against every model upgrade, and Session Resume (§22J.3) depends on the tenant-isolation guarantees in [`verified-path-and-governance.md`](verified-path-and-governance.md) §22F.

The two topics are presented as clearly distinguished subsections throughout this document (prefixed **§22I — Evaluation** and **§22J — Memory**).

## Boundaries

**In-scope:**

- **§22I — Evaluation Framework:**
  - §22I.1 Six-Dimension Trajectory Scoring (Task Completion, Tool Selection, Argument Accuracy, Result Utilization, Plan Coherence, Error Recovery) and the scoring pipeline (Deterministic Validation first, LLM-as-Judge as supplement).
  - §22I.2 Compound Error Tracking (per-step 95% → 8-step ≈ 66%) — the most common production Agent failure pattern.
  - §22I.3 Evaluation Flywheel (offline eval → deploy → online monitoring → failure analysis → expand Golden Dataset → optimization → loop).
  - §22I.4 Golden Dataset (source, annotation, versioning, VP-organized, CI Gate).
  - §22I.5 Three-Layer Monitoring Dashboard (L1 Business KPIs, L2 System Health, L3 Cost & Resources).
  - §22I.6 Evaluation Frequency (CI/CD, daily, weekly, pre-model-upgrade).

- **§22J — Memory Architecture:**
  - §22J.1 Four-Layer Model (L1 Working, L2 Episodic, L3 Semantic, L4 Procedural) with cognitive analogy, storage, implementation, and persistence scope.
  - §22J.2 L1 Working Memory (Context Window + LangGraph Checkpointer / PostgresSaver; `thread_id`).
  - §22J.3 L2 Episodic Memory (new): the `agent_episodic_memory` schema and Session Resume.
  - §22J.4 L3 Semantic Memory (new): the `agent_semantic_memory` schema.
  - §22J.5 Provenance Marking (`user_stated` / `tool_output` / `model_inferred` and their graduation rules).
  - §22J.6 Graduation Rules (Episodic → Semantic; must-never-auto-graduate cases; financial compliance constraint).
  - §22J.7 Bitemporal Validity (`valid_from` / `valid_to` / `superseded_by`).

**Delegated / out-of-scope:**
- The Agent SDK runtime, dual-mode orchestration, and the trajectory that evaluation scores → [`dual-mode-orchestration.md`](dual-mode-orchestration.md) (§22A). The Evidence Packet cross-validation referenced in Dimension 4 (Result Utilization) is defined there (§22A.4).
- Skill and MCP catalogs → [`skill-catalog.md`](skill-catalog.md) (§22B) and [`mcp-catalog.md`](mcp-catalog.md) (§22C).
- The L4 Procedural memory implementation (Skill Registry + VP Catalog) → [`skill-catalog.md`](skill-catalog.md) and [`verified-path-and-governance.md`](verified-path-and-governance.md) (§22H). L4 is "already exists" in the four-layer model; this document defines it only as a memory layer.
- Cost governance (which consumes the L3 Cost & Resources dashboard and enforces budgets) → [`verified-path-and-governance.md`](verified-path-and-governance.md) §22K.
- The CI Regression Gate mechanics (model upgrade, Golden Dataset pass/fail) → [`verified-path-and-governance.md`](verified-path-and-governance.md) §22K.4–§22K.6; this document defines the Golden Dataset that the gate runs.
- Tenant isolation for memory tables (all memory is per-tenant, per-user) → [`verified-path-and-governance.md`](verified-path-and-governance.md) §22F.
- PostgreSQL + pgvector physical storage and Knowledge Graph → [`../knowledge-services/knowledge-base.md`](../knowledge-services/knowledge-base.md) and [`../knowledge-services/code-graph.md`](../knowledge-services/code-graph.md).

**Upstream/downstream neighbors:**
- *Upstream*: every Agent execution (Exploration or VP) produces an Execution Trace that the Evaluation Framework scores, and a session summary that L2 Episodic Memory stores.
- *Downstream*: scoring failures become Golden Dataset regression tests; L3 Semantic facts and L4 Procedural patterns feed back into future Agent trajectories, improving the scores.

## Interfaces

### §22I — Evaluation Framework Interfaces

| Aspect | Specification |
| --- | --- |
| **Scoring input** | An Execution Trace (VP or Exploration) from the Agent SDK. Each trace covers every step from intent recognition to task completion. |
| **Scoring pipeline** | Execution Trace → Deterministic Validation (Dimensions 3, 5 partially) → LLM-as-Judge (Dimensions 1, 2, 4, 6) → Six-Dimension Scoring Report. |
| **Principle** | Deterministic validation first, LLM-as-Judge as supplement. Schema validation, parameter type checking, and cycle detection are faster and cheaper than LLM Judge (~70% of checks do not require an LLM). |
| **Cross-family Judge** | The LLM Judge model **must be from a different model family** than the Agent model (to prevent self-family bias). |
| **CI Gate output** | Model upgrade / Agent code change → run full Golden Dataset → any dimension degradation > threshold → block release. Each VP has independent pass/fail criteria. |
| **Monitoring** | Three dashboards: L1 Business KPIs (PM/Business), L2 System Health (SRE/Eng), L3 Cost & Resources (FinOps/Admin). |

### §22J — Memory Architecture Interfaces

| Aspect | Specification |
| --- | --- |
| **L1 Working** | Conversation turns in the Context Window; LangGraph Checkpointer (PostgresSaver) persists state snapshots at each super-step. `thread_id` distinguishes sessions. Supports breakpoint resume, time-travel rollback, Human-in-the-Loop pause/resume. Persistence: single session. |
| **L2 Episodic** | `agent_episodic_memory` table (PostgreSQL + pgvector). Session summaries + `key_findings` + `continuation_point`. Session Resume query injects top-3 open memories into L1. TTL: 90 days. Persistence: cross-session, user-level. |
| **L3 Semantic** | `agent_semantic_memory` table (PostgreSQL JSONB + Knowledge Graph). User preferences, entity relationships, distilled facts. Bitemporal validity (`valid_from`/`valid_to`/`superseded_by`). Persistence: permanent, user-level. |
| **L4 Procedural** | Skill Registry + VP Catalog (existing). Skill sequences and workflow patterns. Persistence: permanent, tenant-level. |
| **Graduation** | Episodic → Semantic when the same fact is independently observed N ≥ 3 times across different sessions with weighted confidence ≥ 0.7 → LLM extracts as Semantic candidate → **user confirmation** → written to L3. |

## Dependencies

- **ADR-0018** ([adr/0018](../../../adr/0018-agent-evaluation-framework.md)) — Agent Evaluation Framework.
- **ADR-0019** ([adr/0019](../../../adr/0019-agent-memory-architecture.md)) — Agent Memory Architecture.
- **Agent SDK / Execution Trace** — the scored artifact. See [`dual-mode-orchestration.md`](dual-mode-orchestration.md) (§22A) and the Evidence Packet (§22A.4) used by Dimension 4.
- **LangGraph** — Checkpointer (PostgresSaver) backs L1 Working Memory snapshots.
- **PostgreSQL + pgvector** — backs L2 Episodic Memory (semantic retrieval of session summaries).
- **PostgreSQL JSONB + Knowledge Graph** — backs L3 Semantic Memory.
- **Skill Registry + VP Catalog** — L4 Procedural Memory. See [`skill-catalog.md`](skill-catalog.md) and [`verified-path-and-governance.md`](verified-path-and-governance.md) (§22H).
- **Cost Governance (ADR-0020)** — consumes the L3 Cost & Resources dashboard; the CI Regression Gate runs the Golden Dataset. See [`verified-path-and-governance.md`](verified-path-and-governance.md) §22K.
- **Tenant Isolation (§22F)** — all memory tables are scoped by `tenant_id` + `user_id`; L2/L3 persistence and graduation are bound by the same isolation guarantees. See [`verified-path-and-governance.md`](verified-path-and-governance.md) §22F.
- **LLM-as-Judge provider** — a different model family than the Agent model (anti-bias requirement).

## Data Model

### §22I — Evaluation Framework

#### §22I.1 Six-Dimension Trajectory Scoring

Each Agent execution (VP or Exploration) is scored across six dimensions:

| Dimension | What It Measures | Scoring Method |
|-----------|------------------|----------------|
| **1. Task Completion** | Was the user intent ultimately resolved? | LLM-as-Judge + human-annotated ground truth |
| **2. Tool Selection** | Were the right tools selected? Was none selected when appropriate? | Compare against optimal tool-call sequence |
| **3. Argument Accuracy** | Are tool parameter schemas valid and semantically correct? | Deterministic validation + LLM semantic judgment |
| **4. Result Utilization** | Was tool-returned data used or fabricated? | Evidence Packet cross-validation (see §22A.4) |
| **5. Plan Coherence** | No loops, no dead ends, reasonable step depth? | Cycle detector + step efficiency ratio |
| **6. Error Recovery** | On tool failure, retry/degrade/escalate rather than crash? | Saga compensation success rate + degradation path coverage |

**Scoring Pipeline**: Execution Trace → Deterministic Validation (Dimensions 3, 5 partially) → LLM-as-Judge (Dimensions 1, 2, 4, 6) → Six-Dimension Scoring Report.

**Principle**: Deterministic validation first, LLM-as-Judge as supplement. Schema validation, parameter type checking, and cycle detection are faster and cheaper than LLM Judge (~70% of checks do not require an LLM). The LLM Judge model must be from a different model family than the Agent model (to prevent self-family bias).

#### §22I.2 Compound Error Tracking

```
Per-step success rate 95% → 8-step chain end-to-end success rate ≈ 0.95^8 ≈ 66%
```

**This is the most common failure mode for production Agents**: per-step all green but end-to-end red. Cross-analyze per-step scores + end-to-end scores; automatically alert when compound error exceeds threshold.

VP Catalog advantage: fixed step count enables precise pre-computation of end-to-end success rate.

#### §22I.3 Evaluation Flywheel

```
Offline Evaluation → Deploy → Online Monitoring → Failure Analysis → Expand Golden Dataset → Agent Optimization → Loop
                ↑
        Every production failure permanently becomes a regression test
```

**Core Principle: The same mistake should never happen twice.** Every production incident → corresponding Execution Trace manually annotated with ground truth → permanently added to Golden Dataset → CI will never let it pass again.

#### §22I.4 Golden Dataset

| Property | Description |
|----------|-------------|
| **Source** | Production Execution Traces (especially cases with compensation/Gateway rejection) + manually designed edge cases |
| **Annotation** | Manually annotated ground truth (optimal Skill sequence + expected output) |
| **Versioning** | Immutable; each new case addition produces a new version |
| **VP-Organized** | Each VP has its own Golden Dataset subset |
| **CI Gate** | Model upgrade/Agent code change → automatically run full Golden Dataset; any dimension degradation > threshold → block release |

#### §22I.5 Three-Layer Monitoring Dashboard

| Layer | What to Watch | Audience |
|-------|---------------|----------|
| **L1 Business KPIs** | Task Success Rate, User Satisfaction, Cost per Task | PM, Business Owners |
| **L2 System Health** | Success rates per VP/Exploration, Tool Failure Rate, Hallucination Rate, Compound Error Rate | SRE, Engineering Team |
| **L3 Cost & Resources** | Daily consumption, Model distribution, Token efficiency | FinOps, Admin |

#### §22I.6 Evaluation Frequency

| Trigger Condition | Evaluation Scope | Action |
|-------------------|------------------|--------|
| Every CI/CD | Full Golden Dataset | Degradation → block release |
| Daily | 10% sample of past 24h production Executions | Trend report |
| Weekly | Full past 7-day Executions | Six-dimension scoring trends + degradation warnings |
| Before Model Upgrade | Full Golden Dataset × old vs. new model comparison | Degradation → block upgrade |

### §22J — Memory Architecture

> Agent memory is not a single database, but a four-layer cognitive architecture. Industry consensus (LangGraph Store, Mem0, ENGRAM, Letta/MemGPT 2025-2026) maps human cognitive psychology models to technical implementation. Financial scenarios additionally require bitemporal validity tracking and provenance marking.

#### §22J.1 Four-Layer Model

| Layer | Cognitive Analogy | What It Stores | Technical Implementation | Persistence Scope |
|-------|-------------------|----------------|--------------------------|-------------------|
| **L1 Working** | Working Memory | Current session conversation turns, tool outputs, temporary drafts | Context Window + LangGraph Checkpointer (PostgresSaver) | Single session |
| **L2 Episodic** | Episodic Memory | "What happened last time" — session summaries, key findings, continuation_point | PostgreSQL + pgvector semantic retrieval | Cross-session, user-level |
| **L3 Semantic** | Semantic Memory | "What is true" — user preferences, entity relationships, distilled facts | PostgreSQL JSONB + Knowledge Graph | Permanent, user-level |
| **L4 Procedural** | Procedural Memory | "How to do it" — Skill sequences, workflow patterns | Skill Registry + VP Catalog (existing) | Permanent, tenant-level |

#### §22J.2 L1 Working Memory

- All conversation turns reside in the Context Window
- LangGraph Checkpointer persists state snapshots at each super-step
- Supports: breakpoint resume, time-travel rollback, Human-in-the-Loop pause/resume
- `thread_id` distinguishes sessions

#### §22J.3 L2 Episodic Memory (New)

```sql
CREATE TABLE agent_episodic_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    user_id UUID NOT NULL,
    session_id UUID NOT NULL,
    session_type VARCHAR(32) NOT NULL,  -- 'exploration' | 'verified_path'
    vp_id VARCHAR(16),
    summary TEXT NOT NULL,               -- LLM-generated structured summary
    key_findings JSONB,
    continuation_point JSONB,            -- {step, state_snapshot, pending_actions}
    status VARCHAR(16) DEFAULT 'open',   -- 'open' | 'resolved' | 'archived'
    created_at TIMESTAMPTZ DEFAULT now(),
    expires_at TIMESTAMPTZ,              -- TTL: 90 days
    embedding VECTOR(1536)
);
```

**Session Resume**: User says "continue the last Recon" → query `agent_episodic_memory` WHERE user_id = ? AND status='open' → inject top-3 into L1 → Agent resumes from `continuation_point`.

#### §22J.4 L3 Semantic Memory (New)

```sql
CREATE TABLE agent_semantic_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    user_id UUID NOT NULL,
    fact_type VARCHAR(32) NOT NULL,       -- 'preference' | 'relationship' | 'constraint'
    fact_key VARCHAR(256) NOT NULL,
    fact_value JSONB NOT NULL,
    provenance VARCHAR(16) NOT NULL,      -- 'user_stated' | 'model_inferred' | 'tool_output'
    confidence FLOAT DEFAULT 1.0,
    observation_count INT DEFAULT 1,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ,                 -- NULL = currently valid
    superseded_by UUID,
    UNIQUE (tenant_id, user_id, fact_key)
);
```

#### §22J.5 Provenance Marking

| Provenance | Meaning | Graduation Rule |
|-----------|--------|----------------|
| `user_stated` | User explicitly stated | Trusted after 1 observation |
| `tool_output` | System data from tool output | Trusted after 1 observation |
| `model_inferred` | LLM-inferred conclusion | Requires ≥3 observations + human confirmation + must not conflict with other sources |

#### §22J.6 Graduation Rules

**Episodic → Semantic**: Same fact independently observed N ≥ 3 times (across different sessions) with weighted confidence ≥ 0.7 → LLM extracts as Semantic candidate → **user confirmation** → written to L3.

**Must never auto-graduate**: `provenance = model_inferred` with observation_count = 1; temporary session preferences (`fact_type = 'session_preference'`).

**Financial compliance constraint**: All `model_inferred` fact graduations **must** pass human confirmation; automatic graduation is forbidden.

#### §22J.7 Bitemporal Validity

Each Semantic fact carries `valid_from` / `valid_to` / `superseded_by`. When a fact changes, the old fact is not overwritten — instead, the old fact is marked `valid_to = now()`, a new fact is written with `superseded_by` pointing to the old ID. An audit three months later can trace back to the exact fact state at the time of the decision.

## Failure Modes & Recovery

| Failure | Impact | Recovery |
| --- | --- | --- |
| **Compound error exceeds threshold (§22I.2)** | Per-step green but end-to-end red — most common production Agent failure | Cross-analyze per-step + end-to-end scores; automatic alert when compound error exceeds threshold. VP fixed step count allows pre-computed end-to-end success-rate budgets. |
| **Self-family bias in LLM Judge (§22I.1)** | Judge model favors Agent model's outputs | Enforced by design: the LLM Judge model must be from a different model family than the Agent model. |
| **Production incident not captured (§22I.3)** | Same mistake recurs; flywheel stalls | Every production incident → Execution Trace annotated with ground truth → permanently added to Golden Dataset → CI blocks future regressions. Core principle: "the same mistake should never happen twice." |
| **Model upgrade degrades a dimension (§22I.4/§22I.6)** | Silent quality regression reaches production | Golden Dataset CI Gate: any dimension degradation > threshold → block release/upgrade. Pre-upgrade comparison runs old vs. new on the full Golden Dataset. |
| **L2 Episodic memory missed resume (§22J.3)** | User says "continue last Recon" but no memory found | Query `agent_episodic_memory WHERE user_id = ? AND status='open'`; if none, Agent asks for clarification rather than fabricating prior state. Top-3 injected into L1 by semantic relevance. |
| **L2 memory exceeds 90-day TTL** | Old session context lost | `expires_at` TTL auto-archives; L3 Semantic holds any graduated durable facts, so nothing load-bearing is lost. |
| **`model_inferred` fact auto-graduated (§22J.6)** | Unverified LLM conclusion becomes a permanent "fact" | Forbidden by financial compliance constraint: all `model_inferred` graduations require human confirmation. Single-observation inferred facts and session preferences never auto-graduate. |
| **Conflicting L3 Semantic facts (§22J.7)** | Stale fact misleads a future decision | Bitemporal validity: old fact marked `valid_to = now()`, new fact written with `superseded_by` chain; a later audit can trace the exact fact state at the decision time. |
| **Cross-tenant memory leakage** | Tenant A's distilled facts surface for Tenant B | All memory tables are scoped `tenant_id` + `user_id`; isolation enforced per §22F (see [`verified-path-and-governance.md`](verified-path-and-governance.md)). L4 Procedural is tenant-level; L1–L3 are user-level. |
| **LLM fabrication in Dimension 4 (§22I.1)** | Agent cites data not returned by tools | Evidence Packet cross-validation (§22A.4) detects fabrication; flagged in the Result Utilization score. |

## Non-Functional Requirements

- **Evaluation cost efficiency (§22I.1)** — ~70% of trajectory checks are deterministic (schema validation, parameter type checking, cycle detection) and do not require an LLM; the LLM-as-Judge is reserved for Dimensions 1, 2, 4, 6. This keeps evaluation cost bounded relative to Agent execution cost.
- **Evaluation coverage (§22I.6)** — full Golden Dataset on every CI/CD and pre-model-upgrade; 10% daily sampling of production executions; full weekly scoring. Trend reports feed the L2 System Health dashboard.
- **Memory persistence scope (§22J.1)** — L1 single-session (volatile + Checkpointer snapshots); L2 cross-session/user-level (90-day TTL); L3 permanent/user-level (bitemporal); L4 permanent/tenant-level. The scope hierarchy prevents user-level state from leaking across tenants.
- **L2 retrieval latency (§22J.3)** — Session Resume uses pgvector semantic retrieval over `agent_episodic_memory.embedding` (VECTOR(1536)); top-3 open memories injected into L1. Must be fast enough to feel instantaneous at session start.
- **Auditability (§22J.7)** — bitemporal validity (`valid_from`/`valid_to`/`superseded_by`) enables point-in-time reconstruction of any user's Semantic fact state, satisfying financial compliance requirements for retroactive audit.
- **Provenance trust gradient (§22J.5)** — `user_stated` and `tool_output` are trusted after 1 observation; `model_inferred` requires ≥3 observations + human confirmation + conflict check. This gradient prevents LLM hallucinations from becoming trusted facts.
- **Tenant isolation** — all memory tables carry `tenant_id`; the L4 Procedural layer is tenant-scoped; learning-period data and graduated facts are never mixed across tenants (consistent with §22F).

## Key Flows

### §22I — Evaluation Flywheel

```
Offline Evaluation → Deploy → Online Monitoring → Failure Analysis → Expand Golden Dataset → Agent Optimization → Loop
                ↑
        Every production failure permanently becomes a regression test
```

The flywheel turns every production failure into a permanent regression test. A production incident is captured as an Execution Trace → manually annotated with ground truth (optimal Skill sequence + expected output) → added as an immutable new version to the Golden Dataset → on the next CI/CD run, the full Golden Dataset is executed and any regression on the captured scenario blocks release. Over time the Golden Dataset grows monotonically, ratcheting quality upward.

### §22I — Six-Dimension Scoring Pipeline

An Execution Trace (from a VP or Exploration run) enters the pipeline → **Deterministic Validation** scores Dimension 3 (Argument Accuracy: schema + parameter type checks) and partially Dimension 5 (Plan Coherence: cycle detection + step-efficiency ratio) — this covers ~70% of checks without an LLM → the remaining Dimensions 1 (Task Completion), 2 (Tool Selection), 4 (Result Utilization, via Evidence Packet cross-validation), and 6 (Error Recovery, via Saga compensation success rate + degradation path coverage) are scored by **LLM-as-Judge** using a *different model family* than the Agent → a Six-Dimension Scoring Report is emitted to the monitoring dashboards. Per-step and end-to-end scores are cross-analyzed for compound-error alerts.

### §22J — Session Resume (L2 Episodic)

User says "continue the last Recon" → query `agent_episodic_memory WHERE user_id = ? AND status='open'` ordered by embedding similarity → top-3 matching open memories injected into L1 Working Memory → the Agent resumes from the stored `continuation_point` (`{step, state_snapshot, pending_actions}`), restoring prior tool outputs and drafts rather than re-deriving them.

### §22J — Episodic → Semantic Graduation

The same fact is independently observed across N ≥ 3 different sessions (in L2 Episodic Memory) with weighted confidence ≥ 0.7 → the LLM extracts it as a Semantic candidate → **user confirmation** is required → the fact is written to L3 `agent_semantic_memory` with `provenance`, `observation_count`, `valid_from = now()`, and `valid_to = NULL` (currently valid). If `provenance = model_inferred`, human confirmation is mandatory (financial compliance constraint) and the fact must not conflict with other sources. Single-observation inferred facts and session preferences never auto-graduate.

### §22J — Bitemporal Fact Update

When an L3 Semantic fact changes, the old row is **not overwritten** — it is marked `valid_to = now()` (no longer currently valid), and a new row is written with `valid_from = now()`, `valid_to = NULL`, and `superseded_by` pointing back to the old row's ID. This creates an auditable chain: a query "what did we believe about this fact at time T?" traverses the `superseded_by`/`valid_from`/`valid_to` fields to reconstruct the exact fact state at the decision time.

## Design References

- **Original sections**: §22I (Agent Evaluation Framework → adr/0018) and §22J (Agent Memory Architecture → adr/0019) of [`docs/03-architecture.md`](../../03-architecture.md). All scoring rubrics, SQL schemas, provenance/graduation tables, and the Evaluation Flywheel are preserved verbatim above.
- **agent-platform docs**: [`dual-mode-orchestration.md`](dual-mode-orchestration.md) (§22A — the Execution Trace and Evidence Packet, §22A.4, that Dimension 4 cross-validates), [`skill-catalog.md`](skill-catalog.md) (§22B — L4 Procedural memory = Skill Registry), [`verified-path-and-governance.md`](verified-path-and-governance.md) (§22F tenant isolation for all memory tables; §22H VP Catalog = L4 Procedural; §22K.4–§22K.6 CI Regression Gate consumes the Golden Dataset and the L3 Cost dashboard), [`workflow-composition.md`](workflow-composition.md) (§22E — scenarios whose traces get scored).
- **ADRs** ([index](../../adr-index.md)): [ADR-0018](../../../adr/0018-agent-evaluation-framework.md) (Agent Evaluation Framework — six-dimension scoring, Golden Dataset, flywheel), [ADR-0019](../../../adr/0019-agent-memory-architecture.md) (Agent Memory Architecture — four-layer model, bitemporal validity, provenance).
- **Cross-sub-project references**: [`../knowledge-services/knowledge-base.md`](../knowledge-services/knowledge-base.md) (PostgreSQL + pgvector storage backing L2/L3; Knowledge Graph backing L3), [`../knowledge-services/code-graph.md`](../knowledge-services/code-graph.md) (graph surface that L3 Semantic relationships project onto), [`../platform-core/domain-services.md`](../platform-core/domain-services.md) (PostgreSQL/Redis physical stores), [`../platform-core/observability.md`](../platform-core/observability.md) (monitoring dashboards hosting the three-layer view).
- **Glossary** ([../../glossary.md](../../glossary.md)): Evaluation Flywheel, Golden Dataset, Compound Error, Four-Layer Memory, Loop Detection, Saga Compensation, Verified Path, Dual-Mode Orchestration.
- **Cross-references retained from source**: §22A.4 (Evidence Packet cross-validation for Dimension 4), §22F (tenant isolation for all memory layers), §22K.6 (CI Regression Gate running the Golden Dataset).
