# Agent Workflow Composition — Skill Chaining

> **Origin**: §22E of [`docs/03-architecture.md`](../../03-architecture.md) | **Sub-project**: [agent-platform](README.md)

## Purpose

This module illustrates how **Skills are orchestrated into Agent Workflows** across seven end-to-end user scenarios. It is the worked-example companion to the dual-mode architecture ([`dual-mode-orchestration.md`](dual-mode-orchestration.md), §22A): each scenario shows the Skill invocation order, data flow, and user interaction points, making concrete how the Skill catalog ([`skill-catalog.md`](skill-catalog.md), §22B) and MCP server catalog ([`mcp-catalog.md`](mcp-catalog.md), §22C) cooperate under the 7-layer security defense ([`agent-security.md`](agent-security.md), §22D).

The seven scenarios collectively demonstrate the two execution modes:

- **Exploration Mode** — read-only, LLM-free orchestration of Skills and MCP calls (Scenarios 2, 3, 6, and the read-only legs of 1, 5, 7). Flexible reasoning with guardrails, no state-mutating side effects.
- **Verified Path (VP) Mode** — predefined fixed-step Skill sequences for any state-mutating operation (Scenario 7 onboarding activates VP-006; the Recon follow-up in Scenario 5 leads into VP-001/VP-005; the BRD/ticket creation in Scenario 6 is a VP-eligible promotion candidate). See [`verified-path-and-governance.md`](verified-path-and-governance.md) for the full VP catalog.

Every scenario below is preserved verbatim from the source so the original step tables, parallel-execution blocks, and user-interaction turns remain the load-bearing reference.

## Boundaries

**In-scope:**
- §22E Scenario 1 — "Create a Monthly Revenue Report" (SpecGenerator two-round refine → Freeze handoff).
- §22E Scenario 2 — "Why did this Workflow fail yesterday?" (IncidentDiagnostician three-round ReAct loop with evidence chain).
- §22E Scenario 3 — "What is the impact of changing the exchange rate data source?" (ImpactAnalyzer parallel execution + DocGenerator Impact Report).
- §22E Scenario 4 — "Review whether this PR is safe to deploy" (CodeReviewer parallel git-diff + static-analysis + CodeGraphQuery synthesis).
- §22E Scenario 5 — "Reconcile ERP vs Bank Statement for March" (Recon Workflow execution → ReconBreakAnalyzer classification → consolidated recommendations → DocGenerator Recon Report).
- §22E Scenario 6 — "Why did Line 3 jump 30%?" (Anomaly → Attribution → BRD → Jira ticket, full traceability chain).
- §22E Scenario 7 — "Help me finish initial setup" (Agent Onboarding Interview cold start, strict tenant isolation, Anomaly Detection Learning Period state machine).

**Delegated / out-of-scope:**
- The Skill definitions (S01 IntentParser, S02 KBRetriever, S03 CodeGraphQuery, S04 ImpactAnalyzer, S05 SpecGenerator, S06 DocGenerator, S07 IncidentDiagnostician, S08 DataQualityAdvisor, S09 ReconBreakAnalyzer, S12 CodeReviewer) → [`skill-catalog.md`](skill-catalog.md) (§22B).
- The MCP server definitions (MCP-04 pg-query, MCP-05 log-search, MCP-06 git-diff, MCP-07 template search, MCP-09 incident lookup, MCP-13 static-analysis/data-profile, MCP-17 external-ticketing, etc.) → [`mcp-catalog.md`](mcp-catalog.md) (§22C).
- The 7-layer security defense applied at every tool boundary → [`agent-security.md`](agent-security.md) (§22D).
- The dual-mode Planner-Executor-Responder pipeline, Evidence Packet, and Permission Gate mechanics → [`dual-mode-orchestration.md`](dual-mode-orchestration.md) (§22A).
- The Verified Path definitions (VP-001 through VP-006), Saga compensation, state machine, and the Exploration fallback table → [`verified-path-and-governance.md`](verified-path-and-governance.md) (§22H).
- Freeze Pipeline full flow (referenced by Scenario 1) → [`../workflow-engine/freeze-pipeline.md`](../workflow-engine/freeze-pipeline.md) (§4).
- The Recon Workflow deterministic runtime (referenced by Scenario 5) → [`../workflow-engine/compute-spec.md`](../workflow-engine/compute-spec.md) (§6) and [`../data-health/health-check-framework.md`](../data-health/health-check-framework.md).
- KB storage / Business Glossary / Mapping Registry → [`../knowledge-services/knowledge-base.md`](../knowledge-services/knowledge-base.md).
- Code Graph lineage queries referenced throughout → [`../knowledge-services/code-graph.md`](../knowledge-services/code-graph.md).

**Upstream/downstream neighbors:**
- *Upstream*: Exploration Environment UI ([`exploration-runtime.md`](exploration-runtime.md), §3.1–§3.5) captures the natural-language user input that starts every scenario.
- *Downstream*: state-mutating outcomes (Adjustments, DQ Rules, KB entries, BRDs, Jira Epics) are realized through Verified Paths governed in [`verified-path-and-governance.md`](verified-path-and-governance.md), and executed by the Unified Workflow Engine in [`../workflow-engine/`](../workflow-engine/).

## Interfaces

Each scenario is entered through the Agent SDK's Planner-Executor-Responder pipeline. The reusable interface contract is:

| Aspect | Specification |
| --- | --- |
| **Entry point** | Natural-language user query (from Conversation Interface) OR an annotated Report event (Scenario 6: anomaly annotation click). |
| **Intent routing** | S01 IntentParser decomposes the query into `intent` + `entities` + `routed_skill`. When `confidence < 0.5`, the Agent asks for clarification instead of guessing (see §22M.4 in [`verified-path-and-governance.md`](verified-path-and-governance.md)). |
| **Skill composition** | Skills invoke other Skills and MCP tools in sequence or parallel; parallel branches are merged by a Synthesize step. Read-only operations stay in Exploration; mutating operations hand off to a Verified Path. |
| **User interaction points** | Mid-flow checkpoints for review/refinement (Scenario 1 Round 2), confirmation of inferred configuration (Scenario 7), and selection of suggested actions (Scenario 5 follow-up menu, Scenario 6 `[Create BRD]`). |
| **Exit artifacts** | Design Artifact / Spec (Scenario 1), diagnosis with evidence chain (Scenario 2), Impact Report MD (Scenario 3), Review Summary (Scenario 4), Recon Report (Scenario 5), BRD + Jira Epic (Scenario 6), Data Health Profile YAML + KB drafts (Scenario 7). |
| **Traceability** | Scenario 6 produces the canonical closed loop: `Anomaly Event → Agent Query → BRD → Jira Epic → Spec → PR → Deploy → Monitor`. |

## Dependencies

- **Skill catalog (§22B)** — every scenario composes Skills S01–S09, S12. See [`skill-catalog.md`](skill-catalog.md).
- **MCP server catalog (§22C)** — Scenarios invoke MCP-04 (pg-query), MCP-05 (log-search), MCP-06 (git-diff), MCP-07 (template search), MCP-09 (incident lookup), MCP-13 (static-analysis + data-profile), MCP-17 (external-ticketing). See [`mcp-catalog.md`](mcp-catalog.md).
- **Code Graph (§2.1)** — S03 CodeGraphQuery drives lineage/impact in Scenarios 2, 3, 4, 6. See [`../knowledge-services/code-graph.md`](../knowledge-services/code-graph.md).
- **Knowledge Base** — S02 KBRetriever supplies business definitions, historical patterns, and Mapping Registry in Scenarios 1, 3, 5, 6, 7. See [`../knowledge-services/knowledge-base.md`](../knowledge-services/knowledge-base.md).
- **Unified Workflow Engine (§6, ADR-0025)** — Scenario 5 triggers the deterministic Recon Workflow runtime; Scenario 1 hands the frozen Spec to the Freeze Pipeline. See [`../workflow-engine/compute-spec.md`](../workflow-engine/compute-spec.md) and [`../workflow-engine/freeze-pipeline.md`](../workflow-engine/freeze-pipeline.md).
- **Data Health Check Framework (§13, ADR-0014)** — Scenario 7's auto-inferred DQ Rules and anomaly detection are authored here. See [`../data-health/health-check-framework.md`](../data-health/health-check-framework.md).
- **External ticketing (MCP-17)** — Scenario 6 pushes the BRD to Jira. See [`mcp-catalog.md`](mcp-catalog.md).
- **Tenant isolation (§22F)** — Scenario 7 explicitly relies on strict per-tenant isolation; all inference uses only the tenant's own Schema. See [`verified-path-and-governance.md`](verified-path-and-governance.md).

## Data Model

The scenarios are illustrative flows rather than persistent entities, but they produce and consume these artifacts (cross-referenced to their authoritative modules):

- **Intent parse (S01 output)** — `{intent, entities, routed_skill}`. E.g. Scenario 1: `intent: create_report`, `entities: {metric, period, dimensions, calculations}`, `routed_skill: S05`.
- **Design Artifact (S05 SpecGenerator output)** — YAML carrying the spec draft + `fuzzy_nodes` + `confidence_summary.overall`. See [`../workflow-engine/design-artifact.md`](../workflow-engine/design-artifact.md) (§3.3). Scenario 1 reaches `confidence_summary.overall: 0.91` after refinement.
- **Evidence chain (S07 IncidentDiagnostician output)** — ordered list `[Log ERROR → Trace → Code Graph dependency → Data Catalog schema diff]` with a root-cause statement and confidence (Scenario 2: 0.94).
- **Impact DAG JSON (S04 ImpactAnalyzer output)** — upstream/downstream/indirect impact scope, affected owners, risk level (Scenario 3: MEDIUM). Consumed by S06 DocGenerator.
- **Review Summary (S12 CodeReviewer output)** — severity-tagged findings (`🔴 BLOCKING` / `🟡 WARNING` / `🟢 OK`) plus a `📋 Recommendation` (Scenario 4: `REQUEST_CHANGES`).
- **Recon break classification (S09 ReconBreakAnalyzer output)** — per-item categories: `TIMING`, `MISSING`, `ROUNDING`, `MAPPING`, `UNKNOWN`, plus `Partial`. Scenario 5 tally: 5 TIMING, 8 MISSING, 6 ROUNDING, 3 MAPPING, 1 UNKNOWN, 8 Partial.
- **Attribution analysis (Scenario 6 synthesizer output)** — root cause with confidence (0.92), impact scope (direct/indirect/downstream), and suggested actions (`[Create Dashboard]`, `[Create BRD]`, `[Adjust Threshold]`).
- **Data Health Profile YAML (Scenario 7 S05 output)** — `profile: "monthly_close"`, bound to reports, with check counts (e.g. 55 = 5 rule + 50 anomaly) and anomaly checks at `status: learning`.
- **Business Glossary drafts (Scenario 7 S02 output)** — inferred definitions (e.g. "Operating Revenue ← gl_transactions WHERE account_code BETWEEN '4000' AND '4999'"), pending user confirmation.
- **Anomaly Detection Learning Period state machine** — `learning → active → stable`, with a `degraded` branch on high anomaly rate or persistent false positives (full state machine in Key Flows below).
- **Traceability chain (Scenario 6)** — `Anomaly Event → Agent Query → BRD → Jira Epic → Spec → PR → Deploy → Monitor`.

## Failure Modes & Recovery

| Failure | Impact | Recovery |
| --- | --- | --- |
| **Fuzzy node unresolved (Scenario 1)** | Spec cannot be frozen; ambiguous authoritative source | SpecGenerator marks `fuzzy_nodes`; user review round resolves each (Scenario 1 confirms `erp_finance.monthly_sales`). Freeze Pipeline rejects any Spec with unresolved fuzzy nodes — see [`../workflow-engine/freeze-pipeline.md`](../workflow-engine/freeze-pipeline.md) §4. |
| **Diagnosis needs more context (Scenario 2)** | Round 1 evidence insufficient to confirm root cause | ReAct loop: the Agent observes the gap and launches Round 2 (upstream dependency query) before synthesizing in Round 3. Bounded by the Loop Detection circuit breaker in [`verified-path-and-governance.md`](verified-path-and-governance.md) §22K.3. |
| **Code review blocking finding (Scenario 4)** | PR cannot deploy (e.g. `statistics` import not in allowlist) | CodeReviewer emits `🔴 BLOCKING` + `REQUEST_CHANGES` with concrete remediation (replace with allowlisted `numpy`, add `PARTITION BY`, add unit tests). Deploy is gated until resolved. |
| **Recon UNKNOWN classification (Scenario 5)** | 1 item cannot be auto-classified | Escalated to Data Owner; a BRD may be created to track the unknown issue (Scenario 5 follow-up menu). All financial operations follow `Permission → Validation → Approval → Trigger ETL` — no auto-write-off. |
| **Anomaly attribution low confidence (Scenario 6)** | Root cause uncertain | Synthesizer emits confidence (0.92 in the example); when below threshold the Agent offers multiple hypotheses and asks the user to choose rather than asserting a single cause. |
| **Onboarding learning-period false positives (Scenario 7)** | Anomaly checks noisy during baseline establishment | Checks start at `status: learning` (no alerts); if anomaly rate >30% or persistent false positives after activation, state transitions to `degraded` → human review → restart learning or convert to `type: rule`. |
| **Intent ambiguous (S01 confidence < 0.5)** | Wrong Skill routing | Per §22M.4, the Agent asks for clarification (multiple-choice) rather than falling back to default behavior — prevents silent misrouting. |
| **Mid-VP follow-up question (cross-cutting)** | VP audit trail at risk if paused/forked | Per VP Execution Non-Diversion (§22H), follow-ups are saved as Pending Questions; the VP runs to completion, then the Agent reminds the user. See [`verified-path-and-governance.md`](verified-path-and-governance.md). |

## Non-Functional Requirements

- **Latency budget** — each Agent step adds ~50–200ms (Permission Gate + MCP call); LLM reasoning dominates at 1–30s. Parallel Skill branches (Scenarios 3, 4, 6, 7) keep wall-clock time bounded by the slowest branch, not the sum. See ADR-A1 in [`verified-path-and-governance.md`](verified-path-and-governance.md) §22G.
- **Tenant isolation** — Scenario 7 onboarding is the strict-isolation reference: all inference uses solely the tenant's own Schema and data dictionary; learning-period baselines are permanently isolated from other tenants. The four-layer isolation mechanism (Session Context, MCP-level filtering, optional model isolation, log/audit isolation) is specified in [`verified-path-and-governance.md`](verified-path-and-governance.md) §22F.
- **Cost governance** — Exploration scenarios (2, 3, 6) are subject to the tiered token budget and Loop Detection circuit breaker in [`verified-path-and-governance.md`](verified-path-and-governance.md) §22K. VP-mode scenarios (the mutating legs of 1, 5, 7) draw from the more generous, predictable VP quota.
- **Auditability** — every Skill/MCP invocation is logged with `tenant_id` + `user_id` + `prompt_hash`; the Scenario 6 traceability chain is the canonical example of end-to-end audit from anomaly to deployed fix.
- **Human-in-the-loop** — Scenarios 1, 5, 6, 7 all pause for explicit user confirmation before any state-mutating action, operationalizing the "Execute without AI side effects" half of dual-mode (ADR-0016).

## Key Flows

The seven scenarios follow, preserved verbatim from §22E of [`docs/03-architecture.md`](../../03-architecture.md). Original §N references and ASCII flow diagrams are kept intact.

### Scenario 1: "Create a Monthly Revenue Report" (§22E)

```
User: "Help me create a monthly revenue report, broken down by region and product line, including period-over-period growth"
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│ S01: IntentParser                                               │
│     intent: create_report                                       │
│     entities: {                                                 │
│       metric: "revenue",                                        │
│       period: "monthly",                                        │
│       dimensions: ["region", "product_line"],                   │
│       calculations: ["MoM_growth"]                              │
│     }                                                           │
│     routed_skill: S05 (SpecGenerator)                           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ S05: SpecGenerator (Round 1)                                    │
│     • Call S02 (KBRetriever) → Look up "revenue" business definition        │
│     • Call S02 → Look up associated Data Catalog tables                       │
│     • Call MCP-07 → Search monthly report templates                            │
│     • Output: Initial Design Artifact YAML                           │
│     • Mark fuzzy_nodes: "Which table is the authoritative source for revenue?"           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ User Review & Refine                                            │
│     • User confirms data source: "erp_finance.monthly_sales"              │
│     • User adds: "Period-over-period = (current_month - prev_month)/prev_month"                      │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ S05: SpecGenerator (Round 2 - Refine)                           │
│     • Update Design Artifact based on user feedback                          │
│     • fuzzy_nodes all resolved                                    │
│     • confidence_summary.overall: 0.91                          │
│     • Present final Spec + data preview                           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ User: [Freeze] → Freeze Pipeline takes over                         │
│     See Section 4 for full Freeze Pipeline flow                   │
└─────────────────────────────────────────────────────────────────┘
```

### Scenario 2: "Why did this Workflow fail yesterday?" (Diagnose Workflow Failure) (§22E)

```
User: "daily_sales_report failed during last night's execution — help me figure out why"
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│ S01: IntentParser                                               │
│     intent: diagnose_incident                                   │
│     entities: { workflow_name: "daily_sales_report",            │
│                time: "yesterday" }                              │
│     routed_skill: S07 (IncidentDiagnostician)                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ S07: IncidentDiagnostician (Round 1)                            │
│     • Call MCP-09 → Find the latest Incident for "daily_sales_report" │
│     • Call MCP-05 → Query error logs for the failed Job (level=ERROR) │
│     • Call MCP-05 → Retrieve execution Trace (trace_id)          │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Observation → diagnosis needs more context
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ S07: IncidentDiagnostician (Round 2)                            │
│     • Call S03 (CodeGraphQuery) → Query upstream dependencies   │
│     • Call S03 → "Upstream DataSource recent_changes?"            │
│     • Discovered: upstream ERP data source schema change          │
│       (column "unit_price" was renamed)                           │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Observation → root cause confirmed
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ S07: IncidentDiagnostician (Round 3 - Synthesize)               │
│     • Root cause: ERP database schema change caused the           │
│       transform Job to reference the non-existent column          │
│       "unit_price"                                                │
│     • Evidence chain: [Log ERROR → Trace → Code Graph dependency  │
│       → Data Catalog schema diff]                                 │
│     • Suggested fix: Update column mapping in Spec + re-run       │
│     • Confidence: 0.94                                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
User received diagnosis: "daily_sales_report failed because the upstream
ERP database column `unit_price` was renamed to `unit_price_usd`.
Impact scope: 1 transform Job. Suggestion: update the column mapping
in the Spec. Would you like me to create a fix draft?"
```

### Scenario 3: "What is the impact of changing the exchange rate data source?" (Impact Analysis) (§22E)

```
User: "If I switch the exchange rate data source from ECB to Fed, which reports will be affected?"
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│ S01: IntentParser                                               │
│     intent: analyze_impact                                      │
│     entities: {                                                 │
│       change: "datasource",                                     │
│       old_source: "ECB",                                        │
│       new_source: "Fed",                                        │
│       change_type: "exchange_rate"                              │
│     }                                                           │
│     routed_skill: S04 (ImpactAnalyzer)                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ S04: ImpactAnalyzer (parallel execution)                                  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────┐     │
│  │ S03 (CodeGraphQuery):                                 │     │
│  │ "All Workflows/Jobs referencing the ECB rate source"              │     │
│  │ → 12 Workflows, 34 Jobs directly reference it                      │     │
│  └───────────────────────────────────────────────────────┘     │
│  (parallel)                                                         │
│  ┌───────────────────────────────────────────────────────┐     │
│  │ S02 (KBRetriever):                                    │     │
│  │ "Business impact of ECB vs Fed rate differences"                        │     │
│  │ → KB entry: "ECB uses daily midpoint, Fed uses close, ~0.1% difference"│     │
│  └───────────────────────────────────────────────────────┘     │
│  (parallel)                                                         │
│  ┌───────────────────────────────────────────────────────┐     │
│  │ MCP-06 (git-diff):                                    │     │
│  │ Compare change history of similar source migrations                         │     │
│  │ → Found 2025-Q3 similar migration (Bloomberg→ECB) impact record    │     │
│  └───────────────────────────────────────────────────────┘     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ S04: ImpactAnalyzer (Synthesize)                                │
│     • Upstream impact: ECB source config → 1 DataSource definition change      │
│     • Downstream impact: 12 Workflows, 34 Jobs, 45 Reports               │
│     • Indirect impact: rate difference (0.1%) → may affect cross-currency Recon           │
│     • Affected Owners: [8 users]                                   │
│     • Risk level: MEDIUM                                          │
│     • Generate Impact DAG JSON                                      │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ S06: DocGenerator                                               │
│     doc_type: "impact_report"                                   │
│     • Render: Impact Report (MD)                                  │
│     • Includes: Executive Summary, Impact DAG diagram (Mermaid),            │
│       affected Workflow list, affected Owner list,               │
│       historical similar migration reference, suggested Review process                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
User receives complete Impact Report (previewable, exportable PDF, shareable)
```

### Scenario 4: "Review whether this PR is safe to deploy" (Code Review for Deployment) (§22E)

```
User: "PR #2347 modified the revenue transform logic — help me review whether it is safe to deploy"
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│ S01: IntentParser                                               │
│     intent: review_code                                         │
│     entities: { pr_id: "2347" }                                 │
│     routed_skill: S12 (CodeReviewer)                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ S12: CodeReviewer (parallel execution)                                    │
│                                                                 │
│  ┌───────────────────────────────────────────────────────┐     │
│  │ MCP-06 (git-diff): Full Diff of PR #2347               │     │
│  │ → transform Python code block of revenue transform Job     │     │
│  │   Added: window function + CASE WHEN branch               │     │
│  └───────────────────────────────────────────────────────┘     │
│  (parallel)                                                         │
│  ┌───────────────────────────────────────────────────────┐     │
│  │ MCP-13 (static-analysis): AST analysis + security check         │     │
│  │ → ✅ No eval/exec                                               │     │
│  │ → ⚠️ New import: `statistics` (not in allowlist)         │     │
│  │ → ⚠️ Window function missing PARTITION BY → potential full table scan   │     │
│  └───────────────────────────────────────────────────────┘     │
│  (parallel)                                                         │
│  ┌───────────────────────────────────────────────────────┐     │
│  │ S03 (CodeGraphQuery): Affected upstream/downstream                   │     │
│  │ → Upstream: raw_revenue source (no change)                    │     │
│  │ → Downstream: monthly_report (3), dashboard (2)          │     │
│  └───────────────────────────────────────────────────────┘     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ S12: CodeReviewer (Synthesize)                                  │
│                                                                 │
│  Review Summary:                                                │
│  ├── 🔴 BLOCKING: import `statistics` not in allowlist, needs approval       │
│  ├── 🟡 WARNING: Window function missing PARTITION BY,             │
│  │   may produce unintended full-table aggregation, performance risk                         │
│  ├── 🟢 OK: Code logic is correct (matches BRD-2026-078 description)           │
│  ├── 🟢 OK: Downstream impact scope is clear, no unexpected dependencies                       │
│  └── 📋 Recommendation: REQUEST_CHANGES                        │
│      - Replace `statistics` with allowlisted `numpy`                  │
│      - Add PARTITION BY region to improve performance and avoid logic ambiguity        │
│      - Add unit tests covering the new CASE WHEN branch                      │
└─────────────────────────────────────────────────────────────────┘
```

### Scenario 5: "Reconcile ERP vs Bank Statement for March" (Reconcile ERP vs Bank) (§22E)

```
User: "Help me reconcile March ERP General Ledger against the bank statement"
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│ S01: IntentParser                                               │
│     intent: reconcile                                          │
│     entities: { period: "2026-03", sources: ["ERP_GL",         │
│                "Bank_Statement"] }                              │
│     Note: Reconciliation itself is Compute Spec → Runtime execution    │
│     Agent role here: trigger execution + assist analysis + guide follow-up actions        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Agent triggers Recon Workflow (type: recon)                          │
│ Data Health Check Framework — Runtime (deterministic):          │
│ • Load Recon Check: ERP_GL↔Bank_Statement                      │
│ • Match key: transaction_id + amount + date (tolerance: ±1 day)│
│ • Result: 1,247 Matched, 23 Unmatched, 8 Partial                │
│ • Also triggers type: anomaly trending check (match rate trend)            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ S09: ReconBreakAnalyzer (Cross-Environment Read-Only Mode, parallel)              │
│                                                                 │
│  ┌───────────────────────────────────────────────────────┐     │
│  │ S02 (KBRetriever): Historical Recon records + common break patterns      │     │
│  │ → History: March bank fees typically post 4/1 (TIMING)    │     │
│  │ → History: 0.5% FX fluctuation causes rounding differences (ROUNDING)     │     │
│  └───────────────────────────────────────────────────────┘     │
│  (parallel)                                                         │
│  ┌───────────────────────────────────────────────────────┐     │
│  │ S09: Item-by-item analysis of 23 Unmatched + 8 Partial                │     │
│  │ • 5 TIMING: Bank side 3/31 transaction → ERP posts 4/1          │     │
│  │ • 8 MISSING: ERP only (possibly uncleared items)              │     │
│  │ • 6 ROUNDING: Amount difference < $0.50 (rounding)                │     │
│  │ • 3 MAPPING: Transaction code mismatch → check Mapping Registry   │     │
│  │ • 1 UNKNOWN: Unclassifiable → manual review                      │     │
│  │ • 8 Partial: minor differences in compared fields                  │     │
│  └───────────────────────────────────────────────────────┘     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ S09: Consolidated Recommendations (no auto-execution)                                    │
│ • TIMING (5): Auto-create reminder → verify next cycle (zero financial impact, automatable) │
│ • ROUNDING (6): Suggest write-off → open Adjustment Form, pre-fill amounts      │
│ • MISSING (8): Suggest creating Adjustment → open Adjustment Form      │
│ • MAPPING (3): Suggest updating Mapping Registry → KB Update Request   │
│ • UNKNOWN (1): Escalated to Data Owner                             │
│                                                                 │
│ ⚠️ All operations involving financial data follow:                                  │
│    Permission → Validation → Approval → Trigger ETL             │
│    No Auto-write-off                                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ S06: DocGenerator                                               │
│     doc_type: "recon_report"                                    │
│     → Recon Report: Summary + breakdown statistics + itemized details + suggested actions      │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
User receives Annotated Recon Report → can choose:
• Approve Adjustment draft → trigger ETL Workflow
• Follow up with AI Agent: "Which accounts do the 6 ROUNDING differences come from?"
• Create Dashboard to monitor match rate trend
• Create BRD to track UNKNOWN issue → MCP-17 push to Jira
```

---

### Scenario 6: "Why did Line 3 jump 30%?" (Anomaly → Attribution → BRD → Ticket) (§22E)

```
User sees annotation in Report: ⚠️ Line 3 MoM +31.2% (threshold: 15%)
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│ Click annotation → follow up with AI Agent                                        │
│ "Why did Line 3 jump 30%?"                                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ S01: IntentParser → intent: explain_anomaly                     │
│     entities: { report: "pnl_daily", line: 3, anomaly:          │
│                "ratio_change", delta: "+31.2%" }                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Parallel Queries (Cross-Environment Read-Only Mode)                                    │
│                                                                 │
│  ┌───────────────────────────────────────────────────────┐     │
│  │ S03 (CodeGraphQuery): Full data lineage of Line 3           │     │
│  │ → Upstream ETL: revenue_transform (Job #42)               │     │
│  │ → Data source: ERP_GL.transactions (filtered)              │     │
│  │ → Downstream impact: Line 5, Line 12, Report "Margin Analysis"│     │
│  └───────────────────────────────────────────────────────┘     │
│  (parallel)                                                         │
│  ┌───────────────────────────────────────────────────────┐     │
│  │ S02 (KBRetriever): Business definition of Line 3                  │     │
│  │ → "Line 3 = Revenue from core operations (GAAP ASC 606)"              │     │
│  │ → History: Line 3 typically jumps 10-20% in quarter-end months (normal)      │     │
│  └───────────────────────────────────────────────────────┘     │
│  (parallel)                                                         │
│  ┌───────────────────────────────────────────────────────┐     │
│  │ MCP-05 (log-search): Job #42 execution history (last 7 days)           │     │
│  │ → Yesterday execution time abnormally extended (4min → 22min)                │     │
│  │ → Data volume: yesterday 45,230 rows vs prior 7-day avg 12,100 rows       │     │
│  └───────────────────────────────────────────────────────┘     │
│  (parallel)                                                         │
│  ┌───────────────────────────────────────────────────────┐     │
│  │ MCP-13 (data-profile): Yesterday's Line 3 detail distribution         │     │
│  │ → Discovered: ERP imported 30K catch-up transactions yesterday (bulk insert)  │     │
│  │ → Source: Finance Dept 2026-03 month-end adjustment                        │     │
│  └───────────────────────────────────────────────────────┘     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Response Synthesizer: Attribution Analysis + Recommendations                            │
│                                                                 │
│ 🔍 Root Cause (confidence: 0.92):                                     │
│   Line 3 MoM +31.2% caused by Finance Dept batch catch-up of 30K transactions.           │
│   Data volume surged from prior avg 12,100 rows to 45,230 rows (+273%).            │
│   This is consistent with normal quarter-end fluctuation pattern (historical quarter-end avg +18%).          │
│                                                                 │
│ 📊 Impact Scope:                                                    │
│   • Direct impact: Line 5 (Gross Profit) estimated +15-20%                        │
│   • Indirect impact: Report "Margin Analysis" → Line 2, Line 7        │
│   • Downstream consumers: 3 Dashboards + 2 downstream Reports                 │
│                                                                 │
│ 💡 Suggested Actions:                                                    │
│   [Create Dashboard] Monitor Line 3 daily data volume                        │
│   [Create BRD] Track batch catch-up process standardization                              │
│   [Adjust Threshold] Relax anomaly threshold to 25% for quarter-end months               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ User clicks [Create BRD]                                              │
│                                                                 │
│ S05 (SpecGenerator):                                            │
│     doc_type: "brd"                                             │
│     → BRD draft: Problem description + Root cause analysis + Impact scope + Proposed solution       │
│     → Link affected Workflows/Reports/Metrics                       │
│                                                                 │
│ User Review → Confirm                                           │
│                                                                 │
│ MCP-17 (external-ticketing):                                    │
│     → Jira: Create Epic "Line 3 Data Quality Monitoring"                   │
│     → Link BRD-2026-0042                                        │
│     → Assign to Data Engineering Team                           │
│                                                                 │
│ Full Traceability Chain:                                                        │
│ Anomaly Event → Agent Query → BRD → Jira Epic → Spec → PR →    │
│ Deploy → Monitor (closed loop)                                         │
└─────────────────────────────────────────────────────────────────┘
```

---

### Scenario 7: "Help me finish initial setup" (Agent Onboarding Interview) (§22E)

New tenant cold start — no KB entries, no DQ Rules, no historical data. The Agent guides the tenant through conversation to establish an initial baseline from scratch. **All inference is based solely on the tenant's own Schema and data dictionary; no cross-tenant learning.**

```
Tenant first login → auto-trigger Onboarding Agent
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│ Agent: "Welcome! I'm your data analysis assistant. I see you    │
│         have connected the following data sources:               │
│         • ERP_GL (PostgreSQL, 342 tables)                        │
│         • CRM_Sales (Snowflake, 28 tables)                       │
│                                                                 │
│         What reports or metrics does your team focus on most?"  │
│                                                                 │
│ User: "Monthly P&L, Balance Sheet, AR Aging"                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ S01: IntentParser → intent: onboarding_configure                 │
│     entities: { reports: ["pnl_monthly", "balance_sheet",       │
│                "ar_aging"] }                                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Parallel Analysis (tenant's own Schema only, strict isolation)   │
│                                                                 │
│  ┌───────────────────────────────────────────────────────┐     │
│  │ MCP-04 (pg-query): Scan tenant Schema                   │     │
│  │ → Chart of Accounts: 342 accounts                       │     │
│  │ → Column types: amount (DECIMAL), date (DATE),          │     │
│  │    account_code (VARCHAR), department (VARCHAR)         │     │
│  └───────────────────────────────────────────────────────┘     │
│  (parallel)                                                      │
│  ┌───────────────────────────────────────────────────────┐     │
│  │ S08 (DataQualityAdvisor): Schema→Rules auto-inference   │     │
│  │ → amount IS NOT NULL (completeness)                     │     │
│  │ → amount > 0 (validity, revenue accounts)               │     │
│  │   ← inferred from column name + type                    │     │
│  │ → date BETWEEN accounting_period (timeliness)           │     │
│  │ → account_code IN (SELECT code FROM gl_accounts)        │     │
│  │   (referential integrity — DDL FK detection)            │     │
│  │ → Create anomaly detection for top 50 high-frequency    │     │
│  │   accounts                                              │     │
│  └───────────────────────────────────────────────────────┘     │
│  (parallel)                                                      │
│  ┌───────────────────────────────────────────────────────┐     │
│  │ S02 (KBRetriever): Initialize KB terms                  │     │
│  │ → "Operating Revenue ← gl_transactions WHERE            │     │
│  │    account_code BETWEEN '4000' AND '4999'"              │     │
│  │    (inferred from Schema naming)                        │     │
│  │ → Suggest 23 Business Glossary drafts                   │     │
│  └───────────────────────────────────────────────────────┘     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Agent: "I analyzed your ERP Schema and suggest the following     │
│         configuration:                                            │
│                                                                 │
│  📊 Data Health Checks:                                         │
│     • 4 DQ Rules (auto-generated from column types)              │
│     • 50 Anomaly Detection rules (MoM monitoring for top        │
│       accounts)                                                  │
│     ⚠️ First 30 days are learning period — no alerts,            │
│       baseline establishment only                                │
│                                                                 │
│  📚 Knowledge Base:                                             │
│     • 23 Business Glossary drafts (pending your confirmation)    │
│     • Chart of Accounts imported to Data Catalog                │
│                                                                 │
│  ⏱️ Progressive Activation Timeline:                            │
│     Day 0:   Schema-based rules activate                        │
│     Day 7:   ratio_change check activates (MoM spikes)          │
│     Day 30:  seasonal_decomp activates (seasonal patterns)      │
│     Day 90:  trend_change activates (long-term trend deviation) │
│                                                                 │
│  Would you like me to adjust anything?"                         │
│                                                                 │
│ User: "Add an upper limit check on amount: amount < 10,000,000" │
│ Agent: "Added. Save as 'Monthly Close Profile'?"                │
│ User: "OK"                                                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ S05 (SpecGenerator): Generate Data Health Profile YAML           │
│ → profile: "monthly_close"                                       │
│ → Bound to: pnl_monthly, balance_sheet                           │
│ → 55 checks (5 rule + 50 anomaly)                                │
│   anomaly checks all status: learning                            │
│                                                                 │
│ Write to KB (draft, pending confirmation):                       │
│ → Business Glossary: 23 entries                                  │
│ → Data Catalog: ERP_GL Schema metadata                           │
└─────────────────────────────────────────────────────────────────┘
```

**Anomaly Detection Learning Period State Machine**:

```
┌──────────┐   30-day baseline   ┌──────────┐   sustained    ┌──────┐
│ learning │────────────────────→│  active   │──────────────→│stable│
│ (no      │                     │ (normal   │               │(alert│
│ alerts)  │                     │ alerting) │               │ OK)  │
└──────────┘                     └────┬─────┘               └──────┘
                                  │
                                  │ anomaly rate >30% or
                                  │ persistent false positives
                                  ▼
                             ┌──────────┐
                             │ degraded │ → After human Review:
                             │ (degraded│    restart learning or
                             │  mode)   │    convert to type: rule
                             └──────────┘
```

**Learning Period Constraints** (strict tenant isolation):
- Anomaly checks with `status: learning` do not generate alerts, do not push Triage summaries
- Daily automatic baseline statistics update (mean, stddev, seasonal components) — using only the tenant's own data
- After learning period ends → Agent pushes summary: "50 anomaly checks activated. Key baselines: Line 3 mean $1.2M, σ=$180K."
- Users can manually activate at any time (skip learning period) or extend the learning period
- **Learning period data is permanently isolated from other tenants** — never mixed with any external data

---

## Design References

- **Original section**: §22E (Agent Workflow Composition — Skill Chaining) of [`docs/03-architecture.md`](../../03-architecture.md) (lines 3627–4149). All seven scenarios and the Anomaly Detection Learning Period state machine are preserved verbatim above.
- **agent-platform docs**: [`dual-mode-orchestration.md`](dual-mode-orchestration.md) (§22A — Planner-Executor-Responder pipeline, Evidence Packet, Permission Gate), [`skill-catalog.md`](skill-catalog.md) (§22B — Skills S01–S18), [`mcp-catalog.md`](mcp-catalog.md) (§22C — MCP servers), [`agent-security.md`](agent-security.md) (§22D — 7-layer defense), [`verified-path-and-governance.md`](verified-path-and-governance.md) (§22F–§22H, §22K–§22M — VP catalog, tenant isolation, cost governance, concurrency, capability discovery).
- **Shared sequence diagram**: [`../_shared/sequence-diagrams.md`](../_shared/sequence-diagrams.md) §21.3 AI Agent Query with Permission Gating — the canonical participant flow underpinning every scenario's tool invocations.
- **Cross-sub-project references**: [`../workflow-engine/freeze-pipeline.md`](../workflow-engine/freeze-pipeline.md) (§4 — Freeze Pipeline, referenced by Scenario 1), [`../workflow-engine/compute-spec.md`](../workflow-engine/compute-spec.md) (§6 — Recon Workflow runtime, referenced by Scenario 5), [`../data-health/health-check-framework.md`](../data-health/health-check-framework.md) (§13 — DQ Rules + anomaly detection authored in Scenario 7), [`../knowledge-services/code-graph.md`](../knowledge-services/code-graph.md) (§2.1 — lineage queries in Scenarios 2, 3, 4, 6), [`../knowledge-services/knowledge-base.md`](../knowledge-services/knowledge-base.md) (Business Glossary, Mapping Registry, Data Catalog).
- **ADRs** ([index](../../adr-index.md)): [ADR-0016](../../../adr/0016-dual-mode-agent-orchestration.md) (Dual-Mode — Exploration vs Verified Path), [ADR-0014](../../../adr/0014-data-health-check-framework.md) (Data Health Check Framework — Scenario 7 auto-inference and learning period), [ADR-0025](../../../adr/0025-unified-workflow-engine.md) (Unified Workflow Engine — Recon runtime).
- **Glossary** ([../../glossary.md](../../glossary.md)): Dual-Mode Orchestration, Verified Path, Learning Period, Skill, MCP, Evidence Packet.
- **Cross-references retained from source**: §4 (Freeze Pipeline full flow, Scenario 1), §3.3 (Design Artifact + fuzzy nodes, Scenario 1), §13 (Data Health Check Framework, Scenario 7).
