# Verified Path Catalog, Governance & Concurrency

> **Origin**: §22F, §22G, §22H, §22K, §22L, §22M of [`docs/03-architecture.md`](../../03-architecture.md) | **Sub-project**: [agent-platform](README.md)

## Purpose

This module is the **governance spine** of the Agent Platform. It consolidates the mechanisms that make dual-mode orchestration ([`dual-mode-orchestration.md`](dual-mode-orchestration.md), §22A, ADR-0016) safe enough for regulated financial workloads. It covers six interlocking concerns:

1. **§22F — Multi-Tenant Isolation**: the four-layer mechanism ensuring Tenant A's Agent queries never leak Tenant B's data.
2. **§22G — Summary of Agent ADRs**: the three core architecture decisions (Agent SDK, Skill+MCP two-layer composition, pre-execution Permission Gate) recorded in ADR format.
3. **§22H — Verified Path Catalog**: the six predefined fixed Skill sequences (VP-001 through VP-006) implemented as Saga compensation transactions, plus the Exploration fallback table and the reverse-lookup index.
4. **§22K — Agent Cost Governance & Model Degradation Detection** (ADR-0020): tiered token budgets, graduated execution (DEGRADE not DENY), loop detection, and the four-stage model rollout funnel.
5. **§22L — VP Promotion & Multi-Agent Concurrency** (ADR-0021): how Exploration patterns get promoted to Verified Paths, and the three-layer concurrency control plus priority preemption.
6. **§22M — Agent Capability Discovery** (ADR-0021): the three-layer progressive reveal, Starter Prompt cards, context-aware suggestions, and clarification-over-guessing that together solve the "Blank Canvas Problem."

Together these make the Agent Platform auditable (SOX), cost-bounded, conflict-free under concurrency, and discoverable for non-technical users — without sacrificing the flexibility of Exploration Mode.

## Boundaries

**In-scope:**
- §22F.1–§22F.5 — Tenant Context injection (immutable Session Context), MCP-level tenant filtering (Header/Query/Index/Graph/Object/Log), optional model isolation (Shared/Dedicated/On-Prem), log & audit isolation, cross-tenant isolation verification (CI/CD, quarterly pentest, monthly audit sampling).
- §22G — ADR-A1 (Agent SDK seven-step pipeline), ADR-A2 (Skill + MCP two-layer composition), ADR-A3 (pre-execution Permission Gate).
- §22H — Verified Path Saga execution guarantees (compensation declaration, idempotency key, state machine, audit event stream), the VP-001 through VP-006 definitions, Exploration Fallback table, and Verified Path Index (reverse lookup by Skill).
- §22K.1–§22K.6 — Tiered Token Budget System, Graduated Execution, Loop Detection (three detectors), Model Degradation Detection four-stage funnel, Auto-Rollback triggers, CI Regression Gate.
- §22L.1–§22L.3 — VP Risk-Level Promotion (Read-Only / Config-Modify / Data-Modify), automatic candidate detection, staging silent run, promotion state machine, Three-Layer Concurrency Control (optimistic / pessimistic advisory lock / semantic conflict), Priority Preemption.
- §22M.1–§22M.4 — Three-Layer Progressive Capability Reveal (Surface / Intermediate / Power), Starter Prompt cards, Context-Aware Suggestions rule engine, Clarification-Instead-of-Guessing when S01 confidence < 0.5.

**Delegated / out-of-scope:**
- The Agent SDK runtime internals (ReAct loop, Evidence Packet, seven-step pipeline) → [`dual-mode-orchestration.md`](dual-mode-orchestration.md) (§22A).
- Skill and MCP definitions → [`skill-catalog.md`](skill-catalog.md) (§22B) and [`mcp-catalog.md`](mcp-catalog.md) (§22C).
- The 7-layer security defense (input/tool-gate/output/response/action/audit/sandbox) → [`agent-security.md`](agent-security.md) (§22D). This document covers the *tenant-isolation dimension* of security (§22F) and the *permission-gate placement* decision (ADR-A3), which are complements to the defense layers.
- Agent Memory (L1–L4) and the Evaluation Framework (six-dimension scoring, Golden Dataset) → [`memory-and-evaluation.md`](memory-and-evaluation.md) (§22I, §22J).
- RBAC enforcement at the data/store boundary (row-level security, column masking) → [`../platform-core/domain-services.md`](../platform-core/domain-services.md) and [`../query-serving/query-service.md`](../query-serving/query-service.md) (Query Rewriter).
- Auth Service, mTLS, IAM Policy → [`../platform-core/`](../platform-core/).

**Upstream/downstream neighbors:**
- *Upstream*: dual-mode orchestration decides whether a request runs in Exploration or VP mode; this module governs both (VP definitions + cost/loop guards for Exploration).
- *Downstream*: state-mutating VPs are executed by the Unified Workflow Engine ([`../workflow-engine/`](../workflow-engine/)) and audited via the platform-core Audit Trail.

## Interfaces

### VP Execution Interface (§22H)

| Aspect | Specification |
| --- | --- |
| **VP invocation** | `agent.execute(verified_path_id, params) → result`. The LLM reasons within each step but cannot skip, reorder, or replace steps. Missing steps → reject execution (ADR-0016). |
| **Non-Diversion** | When a user asks follow-up questions mid-VP, they are saved as Pending Questions — VPs cannot be paused or forked. After completion the Agent proactively reminds the user; a separate Exploration may then be initiated. This guarantees immutable audit-trail integrity. See [adr/0021](../../../adr/0021-vp-promotion-concurrency.md). |
| **Saga guarantees** | Each Step registers compensation *before* executing forward. On failure, compensation executes in reverse order (3 retries with exponential backoff). Idempotency Key ensures safe duplicate execution. |
| **Idempotency Key** | `{path_id}_{date}_{entity_id}` — deterministically generated, reproducible. Three-layer idempotency at Path level, Step level, and Skill level. |
| **Audit event stream** | Each Path instance produces an immutable event stream — the `verified_path_step_events` table records forward/compensation status for each step. SOX audit can prove "the system cleaned up all side effects in reverse order." |

### Tenant Isolation Interface (§22F)

| Aspect | Specification |
| --- | --- |
| **Session Context** | Immutable XML block injected into the system Prompt at session start: `tenant_id`, `user_id`, `role`, `permissions`, `tenant_data_region`, `model_preference`. SHA-256 verified; auto-carried on all MCP calls (Gateway extracts `tenant_id` → Headers); auto-injected on all LLM calls (permission summary in `<system_instruction>`). |
| **MCP Header Extraction** | MCP Gateway extracts tenant ID from the request's `X-Tenant-ID` Header + mTLS certificate SAN, and injects it into gRPC metadata. |
| **Cross-tenant call detection** | All MCP call records include `caller_tenant_id` + `target_tenant_id`. A mismatch automatically triggers a security alert (unless cross-tenant authorization is pre-configured). |

### Cost Governance Interface (§22K)

| Aspect | Specification |
| --- | --- |
| **Budget metering** | Configured by tenant Admin; metered by actual API-returned `usage.prompt_tokens + usage.completion_tokens`. Budget hierarchy: Organization → Tenant → User → {VP, Exploration}. |
| **Graduated response** | 50% WARN → 75% THROTTLE (+300ms/step) → 85% DEGRADE (cheaper model) → 90% CRITICAL → 100% KILL. Core principle: **DEGRADE not DENY** (hard blocking could interrupt critical financial analysis). |
| **Auto-rollback (model upgrade)** | Pre-authorized; no human approval required. Triggers: guardrail trip rate, rubric regression, p99 latency, candidate-only error cluster. |

### Capability Discovery Interface (§22M)

| Aspect | Specification |
| --- | --- |
| **Starter Prompts** | Welcome Screen displays 6–8 categorized clickable Prompt cards covering ~80% of daily scenarios; click auto-fills the input. |
| **Context-aware suggestions** | A rule engine (not LLM free-form) detects trigger conditions in conversation; on match the LLM generates specific suggestion text. |
| **Clarification threshold** | When S01 IntentParser `confidence < 0.5`, the Agent proactively offers multiple-choice clarification instead of falling back to default behavior. |

## Dependencies

- **ADR-0017** ([adr/0017](../../../adr/0017-verified-path-saga-semantics.md)) — Verified Path Saga Semantics & Durable Execution: the foundation for compensation, idempotency, and the state machine.
- **ADR-0020** ([adr/0020](../../../adr/0020-agent-cost-governance.md)) — Agent Cost Governance & Model Degradation Detection: tiered budgets, loop detection, four-stage rollout.
- **ADR-0021** ([adr/0021](../../../adr/0021-vp-promotion-concurrency.md)) — VP Promotion & Multi-Agent Concurrency Control: promotion state machine, three-layer locking, priority preemption, capability discovery.
- **ADR-0016** ([adr/0016](../../../adr/0016-dual-mode-agent-orchestration.md)) — Dual-Mode: defines Exploration vs VP and the "missing steps → reject" rule.
- **Skill catalog (§22B)** — VPs compose Skills S02, S03, S04, S05, S08, S09. See [`skill-catalog.md`](skill-catalog.md).
- **Agent Memory (§22J)** — Session Resume and episodic memory depend on the isolation guarantees in §22F. See [`memory-and-evaluation.md`](memory-and-evaluation.md).
- **Evaluation Framework (§22I)** — the CI Regression Gate (§22K.6) and Golden Dataset feed back into VP scoring. See [`memory-and-evaluation.md`](memory-and-evaluation.md).
- **PostgreSQL** — Advisory Locks (§22L.2 Layer 2) and the `verified_path_step_events` audit table. See [`../platform-core/domain-services.md`](../platform-core/domain-services.md).
- **Redis** — Permission decision cache (TTL 60s, ADR-A3) and VP execution state. See [`../platform-core/domain-services.md`](../platform-core/domain-services.md).
- **MCP Gateway** — enforces tenant filtering at the protocol layer (§22F.2). See [`mcp-catalog.md`](mcp-catalog.md).
- **Query Rewriter / DB Proxy** — MCP-04 pg-query auto-appends `WHERE tenant_id = $injected_tenant_id` (non-bypassable RLS). See [`../query-serving/query-service.md`](../query-serving/query-service.md).

## Data Model

This section is organized by origin §N so readers can locate content by its original anchor.

### §22F — Multi-Tenant Isolation

#### §22F.1 Tenant Context Injection (Session Context)

When each Agent session starts, immutable tenant context is injected into the system Prompt:

```
<session_context immutable="true">
  <tenant_id>tenant_abc123</tenant_id>
  <user_id>user_xyz789</user_id>
  <role>analyst</role>
  <permissions>
    <kb:read domains="glossary,catalog,mapping"/>
    <code_graph:read scope="owned"/>
    <spec:write scope="draft_only"/>
    <log:read level="business"/>
  </permissions>
  <tenant_data_region>eu-west-1</tenant_data_region>
  <model_preference>claude-sonnet</model_preference>
</session_context>
```

This context:
- **Immutable**: Agent cannot modify during the session (SHA-256 verified)
- **Auto-carried on all MCP calls**: MCP Gateway extracts `tenant_id` from Session Context and injects it into Headers
- **Auto-injected on all LLM calls**: Tenant permission summary included in the `<system_instruction>` block

#### §22F.2 MCP-Level Tenant Filtering

Every MCP server enforces tenant boundaries at the protocol layer:

| MCP Layer              | Filtering Mechanism                                                                                                                                                                       |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Header Extraction**  | MCP Gateway extracts tenant ID from the request's `X-Tenant-ID` Header + mTLS certificate SAN, and injects it into gRPC metadata                                                          |
| **Query Injection**    | MCP-04 (pg-query): DB Proxy layer auto-appends `WHERE tenant_id = $injected_tenant_id` to all SQL queries (if the query lacks this condition) — this is non-bypassable database row-level security |
| **Index Partitioning** | MCP-01 (vector-search): Each tenant's embeddings are stored in an independent Vector DB Partition/Collection. During search, `tenant_id` is a mandatory top-level filter                   |
| **Graph Isolation**    | MCP-02/03 (graph-traverse/graph-query): Each tenant's graph nodes and edges are stored in independent subgraphs. Cypher queries auto-inject `WHERE node.tenant_id = $tenant_id`           |
| **Object Storage**     | All Object Store keys are prefixed with `{tenant_id}/...`. IAM Policy restricts the Agent service account to only access its own tenant's key prefix                                      |
| **Log Isolation**      | MCP-05 (log-search): Elasticsearch indices are partitioned by `tenant_id`. The `tenant_id` filter is a required parameter during queries — full-index queries are not allowed              |

#### §22F.3 Model Isolation (Optional — Regulated Tenants)

For highly regulated industries (finance, healthcare, government), optional physical model isolation is available:

| Isolation Level                 | Description                                                                                                                                                                                            | Applicable Scenario                   |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------- |
| **Shared Model (Default)**      | All tenants share the same model instance (e.g., shared OpenAI API Key or shared vLLM cluster). Data from different tenants is never mixed in prompts — each request is independent and stateless.      | SaaS mode, SMB customers              |
| **Dedicated Model**             | Tenant receives an independent model instance: dedicated API Key (OpenAI/Anthropic Enterprise) or dedicated vLLM Pod. Ensures tenant data is not mixed with other tenants even at the model provider side. | Regulated industries, large enterprises |
| **On-Premises Model**           | Model deployed within the tenant's VPC/private cloud. Data never leaves the tenant network. Agent Runtime deployed on the tenant side, with only MCP calls routed back to central services via dedicated line. | Finance/government, highest security requirements |

#### §22F.4 Log & Audit Isolation

| Dimension                    | Isolation Mechanism                                                                                                                                                                              |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Agent Interaction Logs**   | Elasticsearch indices are sharded by `tenant_id`. Cross-tenant queries are rejected by the ES query filter — even an Admin cannot simultaneously query two tenants' logs (unless both tenants have explicitly authorized cross-tenant access) |
| **LLM Interaction Log**      | Every LLM call record includes `tenant_id` + `user_id` + `prompt_hash`. Tenant Admins can export logs for their own tenant (compliance requirement). Cross-tenant log aggregation is rejected at the API layer               |
| **MCP Call Audit**           | All MCP call records include `caller_tenant_id` + `target_tenant_id`. A mismatch between the two automatically triggers a security alert (unless cross-tenant authorization is pre-configured)                             |
| **Cost Attribution**         | Model call costs are attributed by `tenant_id`. Tenant-level monthly cost reports are auto-generated. Cross-tenant costs cannot be conflated                                                                                      |

#### §22F.5 Cross-Tenant Isolation Verification

| Verification Method            | Frequency        | Description                                                                                                                                                           |
| ------------------------------ | ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Automated Integration Test** | Every CI/CD      | Simulate Tenant A's Agent attempting to access Tenant B's data (using special test tenants). Verify: (a) MCP rejection, (b) Permission Gate rejection, (c) audit log recording, (d) security alert triggering |
| **Penetration Test**           | Quarterly        | External security team attempts to escape from tenant context: Prompt injection, parameter tampering, Header forgery                                                  |
| **Audit Sampling**             | Monthly          | Randomly sample 1000 Agent interaction logs, manually verify `tenant_id` consistency                                                                                  |

### §22G — Summary: Agent Architecture Decision Records

> Core design decisions of this section, recorded in ADR format.

#### ADR-A1: Agent SDK Architecture

| Attribute | Description |
| --------- | ----------- |
| **Context** | The Agent needs a unified runtime framework to orchestrate LLM reasoning, tool calls, security checks, and response generation |
| **Decision** | Adopt a Planner-Executor-Responder seven-step pipeline (ReAct variant), with all tool calls going through the MCP protocol and Permission Gate pre-checks |
| **Rationale** | Clear phase separation makes security boundaries verifiable; MCP provides standardized tool abstraction; Permission Gate pre-checking avoids the lag of post-hoc auditing |
| **Consequences** | Requires development of Agent Runtime (Go/Rust implementation for performance); MCP Gateway becomes critical infrastructure; each step adds ~50-200ms latency (acceptable, as LLM reasoning already takes 1-30s) |

#### ADR-A2: Skill + MCP Two-Layer Composition Pattern

| Attribute | Description |
| --------- | ----------- |
| **Context** | Agent capabilities need modularity and composability — different scenarios combine different capabilities |
| **Decision** | Skill (coarse-grained capability module, business-scenario-oriented) + MCP (fine-grained tool endpoint, system-capability-oriented). Skills compose MCP calls; Agent Workflows compose multiple Skills |
| **Rationale** | Two-layer abstraction allows reuse at different granularities: Skill-level reuse (e.g., ImpactAnalyzer shared by CodeReviewer and DocGenerator) and MCP-level reuse (e.g., vector-search shared by KBRetriever and TemplateSearch) |
| **Consequences** | Skill registry requires maintenance; inter-Skill dependencies must be explicitly declared; Skill versions must coordinate with MCP versions |

#### ADR-A3: Pre-Execution Permission Gate

| Attribute | Description |
| --------- | ----------- |
| **Context** | If the Agent's tool-calling capability is not controlled, it could be exploited by Prompt Injection to bypass permissions |
| **Decision** | Perform four-dimensional permission checks (Role/Tenant/Resource/Parameter) **before execution** of all tool calls, rather than checking during LLM reasoning or post-hoc auditing |
| **Rationale** | Checks during LLM reasoning can be bypassed by Prompt Injection; post-hoc auditing can only discover problems, not prevent them; only pre-execution checks can truly prevent unauthorized operations |
| **Consequences** | Each tool call adds ~20-50ms permission-check latency; Permission Gateway becomes a performance-critical path → requires Redis caching of permission decisions (TTL 60s) |

### §22H — Verified Path Catalog

> Verified Path = predefined fixed Skill sequences. Uses **Saga compensation transactions + idempotency + durable execution** (see [adr/0017](../../../adr/0017-verified-path-saga-semantics.md) for details). Each Step registers compensation before executing forward. On failure, compensation executes in reverse order. Idempotency Key ensures safe duplicate execution.
>
> **VP Execution Non-Diversion**: When a user has follow-up questions mid-VP execution, the questions are saved as Pending Questions — VPs cannot be paused or forked. After VP completion, the Agent proactively reminds the user of unanswered questions; the user can initiate a separate Exploration. This guarantees the immutable audit trail integrity of VPs. See [adr/0021](../../../adr/0021-vp-promotion-concurrency.md).

#### Saga Execution Guarantees — Compensation Declaration (Carried by Each Skill)

| Skill | Forward Effect | Compensation | Idempotency Check |
|---|---|---|---|
| S02 KBRetriever (Verified Path) | Write KB draft | `delete_draft(kb_entry_id)` | Check if already deleted |
| S05 SpecGenerator | Write draft Spec/Form | `delete_draft(artifact_id)` | Check if already deleted |
| GATE (any level, L0-L3) | Write approval_request | `mark_voided(approval_id, reason)` | Check if already voided |

Other Skills (S03, S04, S08, S09) are read-only operations, no compensation needed.

**Idempotency Key**: `{path_id}_{date}_{entity_id}` — Deterministically generated, reproducible. Three-layer idempotency at Path level, Step level, and Skill level.

#### §22H State Machine

```
┌─────────┐  Step-by-step  ┌──────────┐  Step N fails  ┌──────────────┐
│ running │──────────→│ running  │─────────────→│ compensating │
└─────────┘           └──────────┘              └──────┬───────┘
                             │                         │
                             │                         ▼
                             │                  Execute compensation in reverse order (3 retries)
                             │                         │
                             │                  ┌──────┴──────┐
                             │                  │ All succeeded?    │
                             │                  └──────┬──────┘
                             │                    │        │
                             │                   Yes      No → DLQ
                   All Steps completed                    │
                             │                    ▼
                             ▼               ┌────────┐
                   ┌──────────────┐           │aborted │
                   │awaiting_gate │           └────────┘
                   └──────┬───────┘
                  ┌───────┴───────┐
                  ▼               ▼
            ┌──────────┐    ┌──────────┐
            │completed │    │rejected  │
            └──────────┘    └──────────┘
```

**Audit Event Stream**: Each Path instance produces an immutable event stream — `verified_path_step_events` table records forward/compensation status for each step. SOX audit can prove "the system cleaned up all side effects in reverse order."

#### §22H VP Definitions (VP-001 through VP-006)

**VP-001: create_adjustment_from_recon**

```
Risk: L3 | Gate: L3_REMEDIATION
Create Adjustment from Recon Discrepancy

Step 1: S09 ReconBreakAnalyzer → read-only, comp: noop
Step 2: S02 KBRetriever → read-only (Exploration Mode), comp: noop
Step 3: S04 ImpactAnalyzer → read-only, comp: noop
Step 4: S05 SpecGenerator → comp: delete_draft(artifact_id)
Step 5: GATE L3_REMEDIATION → comp: mark_voided(approval_id)
```

**VP-002: modify_dq_rule_threshold**

```
Risk: L2 | Gate: L2_REMEDIATION
Modify DQ Rule threshold / severity

Step 1: S08 DataQualityAdvisor
  → Analyze modification reason: false_positive / business_change / coverage_gap
  → LLM decision point: Suggested new threshold value?
Step 2: S04 ImpactAnalyzer
  → Modification impact: Which Reports use this rule? Downstream dependencies?
Step 3: S05 SpecGenerator
  → Generate updated Data Health Profile YAML
Step 4: GATE L2_REMEDIATION
  → Single Approver + DQ Gate auto-validation
```

**VP-003: create_adjustment_daily**

```
Risk: L3 | Gate: L3_REMEDIATION
Daily Manual Adjustment (blank form, full approval chain)

Step 1: S02 KBRetriever
  → Retrieve Adjustment Reason Catalog + historically similar adjustments
Step 2: S04 ImpactAnalyzer
  → Impact scope
Step 3: S05 SpecGenerator
  → Generate Adjustment Form (blank, with recommended reason_code)
Step 4: GATE L3_REMEDIATION
  → Dual approval + Impact Report
```

**VP-004: update_kb_glossary**

```
Risk: L2 | Gate: L2_REMEDIATION
Modify Business Glossary definition

Step 1: S02 KBRetriever
  → Retrieve current definition + associated Reports/Metrics
Step 2: S03 CodeGraphQuery
  → Lineage: Which Workflows use this definition?
Step 3: S04 ImpactAnalyzer
  → Downstream impact of definition change
Step 4: S05 SpecGenerator
  → Generate KB entry update draft
Step 5: GATE L2_REMEDIATION
  → Single Approver
```

**VP-005: resolve_recon_mapping**

```
Risk: L2 | Gate: L2_REMEDIATION
Update Mapping Registry to Resolve Recon Key Mismatch

Step 1: S09 ReconBreakAnalyzer
  → Analyze MAPPING type discrepancy
Step 2: S02 KBRetriever
  → Retrieve Mapping Registry existing rules
Step 3: S05 SpecGenerator
  → Suggest new mapping rule
Step 4: GATE L2_REMEDIATION
  → Single Approver
```

**VP-006: onboard_new_tenant**

```
Risk: L0 | Gate: NONE
Agent Onboarding Interview (Cold Start Guidance)

Step 1: MCP-04 pg-query → Scan tenant schema
Step 2: S08 DataQualityAdvisor → Schema→Rules inference
Step 3: S02 KBRetriever → Initialize KB terminology draft
Step 4: S05 SpecGenerator → Generate Data Health Profile YAML
Status: all anomaly checks → status: learning
```

#### §22H Exploration Fallback

The following scenarios remain in Exploration Mode (free LLM orchestration), without defining a Verified Path:

| Scenario | Rationale |
|---|---|
| Attribution Analysis ("Why did Line 3 jump?") | Read-only operation, no side effects. Flexible LLM exploration is more effective |
| Ad-hoc Data Exploration | User questions are unpredictable |
| KB Query | Read-only, no compliance risk |
| Incident Diagnosis | Root cause diversity — fixed paths may miss causes |
| Dashboard Creation | Personal view, no production impact (L0) |

#### §22H Verified Path Index (Reverse Lookup by Skill)

| Skill | Participating Verified Paths |
|---|---|
| S02 KBRetriever | VP-001, VP-003, VP-004, VP-005, VP-006 |
| S03 CodeGraphQuery | VP-004 |
| S04 ImpactAnalyzer | VP-001, VP-002, VP-003, VP-004 |
| S05 SpecGenerator | VP-001, VP-002, VP-003, VP-004, VP-005, VP-006 |
| S08 DataQualityAdvisor | VP-002, VP-006 |
| S09 ReconBreakAnalyzer | VP-001, VP-005 |

### §22K — Agent Cost Governance & Model Degradation Detection (→ adr/0020)

> LLM Agent costs are unpredictable — a single user question may consume 500 or 50,000 tokens. Exploration Mode's ReAct Loop may trigger runaway cycles. Additionally, LLM provider model upgrades may change outputs, requiring systematic upgrade validation. Real industry incidents exist: $47K LangChain loop, 442K tokens single burst.

#### §22K.1 Tiered Token Budget System

```
Organization: $10,000/month (Admin configured)
  ├── Tenant A: $2,000/month
  │     ├── User 1: $500/month
  │     │     ├── Verified Path: $400/month  (predictable, generous quota)
  │     │     └── Exploration: $100/month    (unpredictable, strict quota)
  │     └── User 2: $300/month
  ├── Tenant B: $3,000/month
  └── System (cron/background): $500/month
```

Configured by tenant Admin; metered by actual API-returned `usage.prompt_tokens + usage.completion_tokens`.

#### §22K.2 Graduated Execution (Non-Binary Blocking)

```
Usage at 50%: WARN     → Slack/Email notify user and Admin
Usage at 75%: THROTTLE  → Agent response artificially delayed (adds +300ms delay per step, increasing total step latency from ~200ms to ~500ms)
Usage at 85%: DEGRADE   → Auto-switch to cheaper model (Opus→Sonnet, GPT-4o→GPT-4o-mini)
Usage at 90%: CRITICAL  → Notify Admin, "10% remaining"
Usage at 100%: KILL     → Hard block, return friendly message
```

**Core Principle: DEGRADE not DENY.** In financial scenarios, hard blocking could interrupt critical analysis.

#### §22K.3 Loop Detection (Runaway Exploration Prevention)

Three detectors combined, any triggered → Circuit Breaker opens → return "Loop detected, interrupted" + preserve completed results:

| Detector | Principle | Trigger Condition |
|--------|------|---------|
| Identical-Call | Hash each Step input → same input appears repeatedly | 3 consecutive times |
| Ping-Pong | Two tools calling each other A→B→A→B | Same pair ≥ 4 times |
| Context-Growth | Context continuously expanding without convergence | 5 consecutive rounds with no tool output change |

#### §22K.4 Model Degradation Detection: Four-Stage Funnel

```
Shadow (0% user impact)  →  Canary (1-5% stratified traffic)  →  Percentage (10→25→50%)  →  Full (100%)
   24-72h dwell               24-72h dwell                 Each step 12-24h             48-72h armed
```

| Stage | What It Does | Question It Answers |
|------|--------|------------|
| **Shadow** | Production traffic mirrored to new model, not shown to users | "Does it behave reasonably on real traffic distribution?" |
| **Canary** | 1-5% real users, stratified by tenant (avoid whale customers) | "With users in the loop, is it at least as good as the old model?" |
| **Percentage** | Gradual expansion to 50% | "Are improvements/regressions per dimension statistically significant?" |
| **Full** | 100%, armed with auto-rollback | "Is it stable under sustained load?" |

#### §22K.5 Auto-Rollback Triggers

```yaml
# Pseudocode — values would be quoted strings in production
rollback_triggers:
  guardrail_trip_rate:     > 1.5x baseline    # 15-minute window
  rubric_regression:       > -0.5 point drop  # 1-hour window, p<0.05
  p99_latency:             > 1.3x baseline    # 10-minute window
  candidate_only_cluster:  new_error_cluster  # Error type not present in old model appears
```

Any triggered → auto-rollback to old model. Rollback does not require human approval (pre-authorized).

#### §22K.6 CI Regression Gate

Before model upgrade, all VP LLM inference points run on Golden Dataset (Temperature=0.0). Any dimension degradation > threshold → block release. Each VP has independent pass/fail criteria.

### §22L — VP Promotion & Multi-Agent Concurrency (→ adr/0021)

> Two independent problems: (a) How do verified Skill sequences in Exploration Mode get promoted to Verified Paths (balancing flexibility and SOX compliance) (b) How to detect and resolve conflicts when multiple users/Agents initiate conflicting operations on the same resource.

#### §22L.1 VP Risk-Level Promotion

Reuses the L0-L3 Gateway pattern, determining the promotion process by path risk:

| Path Risk | Promotion Process | Approver | Example |
|---------|---------|--------|------|
| **Read-Only** | Auto-promotion, no approval required | System | "Check PnL + Generate chart" Exploration sequence |
| **Config-Modify** | In-platform Admin approval | 1 Admin | Newly discovered DQ Rule tuning path |
| **Data-Modify** | Full BRD → Jira/Rally → Dual approval | Admin + Data Owner | Newly discovered Adjustment creation pattern |

**Automatic Candidate Detection**: When the same Skill sequence successfully completes N=5 consecutive times in Exploration, it is automatically registered as a `staging` candidate.

**Staging Period Silent Run (Shadow Promotion)**: Candidate VP shadow-runs in production traffic for 30 days (without blocking the real process), collecting metrics: success rate > 95%, compensation rate < 5%, rejection rate < 10% → generate Promotion Proposal.

**Promotion State Machine**:

```
exploration_pattern → staging (shadow run 30d) → proposed (proposal pending approval) → production
                         ↓ metrics not met                    ↓ approval rejected
                       discarded                       rejected
                                                           ↓
                                                  production → deprecated → archived
```

#### §22L.2 Multi-Layer Concurrency Control

##### Layer 1: Entity-Level Optimistic Locking (Default)

All mutable entities carry a `version` field (`dq_rule`, `kb_glossary`, `data_health_profile`, `adjustment_form`). CAS write failure → return `409 Conflict`.

##### Layer 2: Pessimistic Locking (High-Contention Resources)

Same GL Account + PnL Date with two Agents simultaneously creating Adjustments → use PostgreSQL Advisory Lock:

```sql
SELECT pg_try_advisory_lock(hash(tenant_id, gl_account, pnl_date));
-- false → 409 Conflict + holder info
```

PG Advisory Lock is natively bound to session, auto-released on disconnect, no additional Fencing Token needed.

##### Layer 3: Semantic Conflict Detection

Gateway adds `ResourceConflictCheck` step before approval: query executing VPs → check resource cluster overlap + intent contradictions (e.g., "modify DQ Rule" vs "review Report depending on this Rule") → block submission on conflict.

#### §22L.3 Priority Preemption

Financial business priority: **Recon > Close Operations > Ad-hoc Analysis**

```yaml
priority_preemption:
  recon:
    can_preempt: [adhoc_analysis]
  month_end_close:
    can_preempt: [adhoc_analysis]
  adhoc_analysis:
    can_preempt: []
```

Recon-triggered VP-001 can preempt Ad-hoc VP-003. Preempted party receives notification → wait queue → preemption complete → auto-wake.

### §22M — Agent Capability Discovery (→ adr/0021)

> "Blank Canvas Problem": Non-technical users facing an empty input box don't know what the Agent can do. 21 MCPs, 18 Skills, 6 VPs — the stronger the capability, the harder the discovery.

#### §22M.1 Three-Layer Progressive Capability Reveal

| Layer | Strategy | Content |
|---|------|------|
| **Surface** (Visible at a glance) | Welcome Screen + 6-8 clickable Starter Prompts | Covers 80% of daily scenarios: Check PnL, View DQ alerts, Run Recon |
| **Intermediate** (Suggested in conversation) | Agent proactively suggests: "Would you like me to create an Adjustment for this discrepancy?" | Context-aware, triggered by rule engine (not LLM free-form) |
| **Power** (Not actively promoted) | Advanced capabilities exist in Skill Catalog but are not proactively displayed | Users discover naturally or unlock after Admin assigns permissions |

#### §22M.2 Starter Prompt Cards

Welcome Screen displays categorized Prompt cards; users click to auto-fill:

```
┌──────────────────────────────────────────────────┐
│  👋 I'm your financial analysis assistant. I can help with:  │
│                                                    │
│  📊 View PnL   │ 🔍 Investigate │ ⚠️ Check DQ    │
│  📝 Create Adj  │ 📈 Gen Report  │ 💬 Query Terms │
│                                                    │
│  Type your question, or click a card above to start ↓                  │
└──────────────────────────────────────────────────┘
```

#### §22M.3 Context-Aware Suggestions

The rule engine detects trigger conditions in conversation (not LLM free-form thinking); upon match, the LLM generates specific suggestion text:

| User's Current Action | Agent Suggestion |
|------------|-----------|
| Viewed DQ alerts for a PnL Date | "Would you like me to run a full Recon for this PnL Date?" |
| Recon result discrepancy > threshold | "Would you like me to create this discrepancy as an Adjustment Form?" |
| Manually queried the same GL Account 3 times consecutively | "Would you like me to set up an automatic DQ monitoring rule?" |
| Created an Adjustment Form | "Would you like me to submit it to Jira and link it to a BRD?" |

#### §22M.4 Clarification Instead of Guessing When Intent is Ambiguous

When S01 IntentParser confidence < 0.5, do not fall back to default behavior — instead proactively ask for clarification:

```
User: "This month's data seems odd"
Agent: "Would you like to: A) Compare with last month's PnL? B) Check data quality alerts? C) Check Recon discrepancies?"
```

This is far better than silently routing to the wrong capability — users won't abandon the Agent after one bad experience.

## Failure Modes & Recovery

| Failure | Impact | Recovery |
| --- | --- | --- |
| **VP Step N fails** (§22H state machine) | Partial side effects written | Saga compensation executes in reverse order (3 retries with exponential backoff); all succeed → `aborted` (clean); any fail → DLQ for human cleanup. `verified_path_step_events` records the full forward/compensation trail for SOX audit. |
| **Compensation retries exhausted** | Residual state remains | Terminal failure enters DLQ → auto-creates Incident → escalates to Data Owner → human cleanup of residual state. Periodic scanning of unresolved entries → weekly summary report. |
| **Cross-tenant data leak attempt** (§22F) | Tenant boundary violation | MCP-level filtering rejects the call; Permission Gate rejects; audit log records; security alert triggers. Verified every CI/CD, quarterly pentest, monthly 1000-log sampling. |
| **Tenant Context tampering** | Agent attempts to modify session context | SHA-256 verification fails; session is terminated. Context is immutable by construction. |
| **Exploration runaway loop** (§22K.3) | Token burn / hung Agent | One of three detectors (Identical-Call ≥3, Ping-Pong ≥4, Context-Growth 5 rounds) trips → Circuit Breaker opens → "Loop detected, interrupted" + completed results preserved. |
| **Tenant budget exhausted** (§22K.2) | Agent cannot complete task | Graduated: WARN → THROTTLE → DEGRADE (cheaper model) → CRITICAL → KILL. DEGRADE-not-DENY preserves critical financial analysis. |
| **Model upgrade regression** (§22K.4–§22K.6) | New model degrades output quality | Four-stage funnel (Shadow → Canary → Percentage → Full); auto-rollback on guardrail trip / rubric regression / latency / new error cluster. Pre-authorized, no human approval. |
| **Concurrent conflicting VP submissions** (§22L.2) | Lost update / inconsistent state | Layer 1 optimistic CAS → `409 Conflict`; Layer 2 PG Advisory Lock for hot resources; Layer 3 semantic conflict detection blocks submission before approval. |
| **Priority resource contention** (§22L.3) | Recon blocked by lower-priority Ad-hoc work | Recon/month-end-close preempts Ad-hoc; preempted party is notified and queued, auto-wakes when the preemptor completes. |
| **VP promotion metrics not met** (§22L.1) | Candidate not ready for production | Staging candidate is `discarded` after 30-day shadow run if success ≤95%, compensation ≥5%, or rejection ≥10%. Re-detected after another N=5 successful Exploration runs. |
| **Ambiguous intent misrouting** (§22M.4) | User routed to wrong capability | S01 confidence < 0.5 triggers proactive multiple-choice clarification instead of silent default routing. |
| **VP paused/forked by mid-flow question** (Non-Diversion) | Audit-trail integrity at risk | By design: follow-ups are saved as Pending Questions; VP runs to completion; Agent reminds user afterward. VPs cannot be paused or forked. |

## Non-Functional Requirements

- **Permission Gate latency** — ADR-A3: each tool call adds ~20–50ms for the four-dimensional (Role/Tenant/Resource/Parameter) check; mitigated by Redis-cached permission decisions (TTL 60s).
- **Step latency budget** — ADR-A1: each Agent step adds ~50–200ms; acceptable because LLM reasoning already takes 1–30s. The Agent Runtime is implemented in Go/Rust for performance.
- **VP determinism** — fixed step count enables pre-computation of end-to-end success rate (the compound-error formula in [`memory-and-evaluation.md`](memory-and-evaluation.md) §22I.2). This is the VP catalog's advantage over free Exploration.
- **Tenant isolation strength** — non-bypassable: DB Proxy row-level security (MCP-04), mandatory Vector DB partition filter (MCP-01), required ES `tenant_id` query parameter (MCP-05), IAM key-prefix restriction (Object Store). Cross-tenant log aggregation is rejected at the API layer.
- **Cost predictability** — VP quotas are generous and predictable; Exploration quotas are strict. Metering is on actual API-returned token counts. Organization/Tenant/User/{VP,Exploration} hierarchy prevents any single user or runaway loop from consuming the org budget.
- **Auditability (SOX)** — every VP instance produces an immutable `verified_path_step_events` stream; every MCP call records `caller_tenant_id` + `target_tenant_id`; every LLM call records `tenant_id` + `user_id` + `prompt_hash`. Tenant Admins can export their own tenant's logs.
- **Concurrency correctness** — three-layer locking (optimistic CAS default; PG Advisory Lock for hot resources; semantic conflict pre-check) prevents lost updates and inconsistent state under multi-agent contention.
- **Discovery usability** — the three-layer progressive reveal ensures non-technical users encounter the 80% common case via Starter Prompts without being overwhelmed by the full 21-MCP / 18-Skill / 6-VP surface area.

## Key Flows

### VP Execution Flow (§22H state machine)

A Verified Path runs as a fixed, immutable sequence. The lifecycle is: `running` (step-by-step forward execution, each Step registering compensation before its forward action) → on Step N failure → `compensating` (reverse-order compensation, 3 retries each) → branch on success: all succeed → `aborted` (clean rollback); any fail → DLQ → `aborted`. If all Steps complete forward → `awaiting_gate` → Gate approves → `completed`; Gate rejects → `rejected`. The full trail is written to `verified_path_step_events` for SOX audit.

### VP Promotion Flow (§22L.1)

```
exploration_pattern
   │ (same Skill sequence succeeds N=5 consecutive times in Exploration)
   ▼
staging  ──── 30-day shadow run in production traffic ────┐
   │     metrics: success >95%, compensation <5%,          │
   │     rejection <10%                                    │
   │                                                       ▼
   │ (metrics not met)                              proposed (promotion proposal)
   ▼                                                       │
discarded                                                  │ (approval rejected)
                                                           ▼
                                                     rejected
                                                           │ (approval accepted)
                                                           ▼
                                              production → deprecated → archived
```

Risk level (Read-Only / Config-Modify / Data-Modify) determines the approver: System auto-promotion / 1 Admin / Admin + Data Owner (full BRD → Jira).

### Concurrency Control Flow (§22L.2)

1. **Layer 1 (default)** — entity write compares `version` (CAS); mismatch → `409 Conflict`.
2. **Layer 2 (hot resources)** — same `(tenant_id, gl_account, pnl_date)` contested → `pg_try_advisory_lock(hash(...))`; `false` → `409 Conflict` + holder info. Lock is session-bound, auto-released on disconnect.
3. **Layer 3 (semantic)** — before Gate approval, `ResourceConflictCheck` queries executing VPs for resource-cluster overlap and intent contradictions; conflicting submission is blocked.

### Cost Governance Flow (§22K.2)

Each Agent step meters `usage.prompt_tokens + usage.completion_tokens` against the user's VP or Exploration sub-budget. As cumulative usage crosses thresholds: 50% → WARN (Slack/Email); 75% → THROTTLE (+300ms/step); 85% → DEGRADE (auto-switch to cheaper model); 90% → CRITICAL (notify Admin); 100% → KILL (hard block, friendly message).

### Model Upgrade Funnel (§22K.4)

`Shadow` (mirror production traffic, 0% user impact, 24–72h dwell) → `Canary` (1–5% stratified real users, 24–72h) → `Percentage` (10→25→50%, each step 12–24h) → `Full` (100%, armed with auto-rollback, 48–72h). Any rollback trigger fires → automatic, pre-authorized revert to the old model.

### Capability Discovery Flow (§22M)

A new user lands on the Welcome Screen → sees 6–8 Starter Prompt cards (Surface layer). During conversation, the rule engine matches the user's current action against trigger conditions → the LLM generates a specific suggestion (Intermediate layer). Advanced capabilities live in the Skill Catalog but are not promoted (Power layer). Whenever S01 IntentParser confidence < 0.5, the Agent offers multiple-choice clarification rather than guessing.

## Design References

- **Original sections**: §22F (Agent Multi-Tenant Isolation), §22G (Summary: Agent ADRs), §22H (Verified Path Catalog), §22K (Agent Cost Governance & Model Degradation Detection), §22L (VP Promotion & Multi-Agent Concurrency), §22M (Agent Capability Discovery) of [`docs/03-architecture.md`](../../03-architecture.md). All tables, state machines, pseudocode, and ASCII diagrams are preserved verbatim above.
- **agent-platform docs**: [`dual-mode-orchestration.md`](dual-mode-orchestration.md) (§22A — ADR-A1/A2/A3 runtime context, Exploration vs VP switching), [`skill-catalog.md`](skill-catalog.md) (§22B — Skills S02–S09 composed by VPs), [`mcp-catalog.md`](mcp-catalog.md) (§22C — MCP-level tenant filtering), [`agent-security.md`](agent-security.md) (§22D — 7-layer defense, of which §22F is the tenant-isolation dimension), [`workflow-composition.md`](workflow-composition.md) (§22E — scenarios that invoke VPs), [`memory-and-evaluation.md`](memory-and-evaluation.md) (§22I/§22J — Golden Dataset feeds the CI Regression Gate in §22K.6).
- **ADRs** ([index](../../adr-index.md)): [ADR-0016](../../../adr/0016-dual-mode-agent-orchestration.md) (Dual-Mode — VP "missing steps → reject" rule), [ADR-0017](../../../adr/0017-verified-path-saga-semantics.md) (Verified Path Saga Semantics & Durable Execution), [ADR-0020](../../../adr/0020-agent-cost-governance.md) (Agent Cost Governance & Model Degradation Detection), [ADR-0021](../../../adr/0021-vp-promotion-concurrency.md) (VP Promotion & Multi-Agent Concurrency Control; also covers Capability Discovery). ADR-A1/A2/A3 are summarized in §22G and recorded in the ADR index.
- **Cross-sub-project references**: [`../platform-core/domain-services.md`](../platform-core/domain-services.md) (PostgreSQL Advisory Locks, Redis permission cache, Audit Trail), [`../platform-core/compliance-architecture.md`](../platform-core/compliance-architecture.md) (SOX obligations underpinning VP audit), [`../query-serving/query-service.md`](../query-serving/query-service.md) (Query Rewriter / DB Proxy enforcing tenant RLS), [`../knowledge-services/knowledge-base.md`](../knowledge-services/knowledge-base.md) (KB drafts written/compensated by VPs), [`../workflow-engine/compute-spec.md`](../workflow-engine/compute-spec.md) (ETL trigger after Gate approval).
- **Glossary** ([../../glossary.md](../../glossary.md)): Verified Path, Saga Compensation, DLQ, Dual-Mode Orchestration, Loop Detection, Three-Layer Concurrency Control, Shadow Promotion, Starter Prompt, Blank Canvas Problem, Evaluation Flywheel, Golden Dataset, Compound Error.
- **Cross-references retained from source**: §22A (Evidence Packet, Permission Gate — ADR-A1/A3 context), §22B/§22C (Skill + MCP catalogs composed by VPs), §22I/§22J (Evaluation and Memory — feed the CI Regression Gate and depend on tenant isolation).
