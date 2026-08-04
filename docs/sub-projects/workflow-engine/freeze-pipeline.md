# Freeze Pipeline

> **Origin**: §4 of [`docs/03-architecture.md`](../../03-architecture.md) | **Sub-project**: [workflow-engine](README.md)

## Purpose

This module covers the **Freeze Pipeline** — the built-in operation of the Workflow Engine, `freeze(workflow_def)`, that transitions a Design Artifact from draft to frozen. Per §4, the Freeze Pipeline is **not** an independent plane; it is an engine operation. It scans all `llm_reasoning` Jobs (capabilities beyond `read_analyze`/`suggest_plan`) and `fuzzy_nodes`, presents each for human resolution, validates the result in a production-sandbox dry-run, and marks the Workflow Definition as frozen.

The pipeline replaces the traditional "Script Compiler" concept with a **Spec Refinement Assistant** that flags and proposes but never auto-compiles, plus canary-gated staged rollout with auto-rollback, and the core **Fuzzy Node Detection & Resolution Algorithm** that transforms AI-generated fuzzy design drafts into deterministic scripts.

This module owns:
- **§4.1 Spec Refinement Assistant** — scan/propose/present/decide/record for `fuzzy_nodes`.
- **§4.1b `llm_reasoning` Job Resolution During Freeze** — flag/propose/decide/record for `generate_draft`/`modify_spec`/`kb_write` Jobs.
- **§4.2 Canary Gating & Auto-Rollback** — 1% → 10% → 50% → 100% staged rollout with explicit gate criteria.
- **§4.3 Fuzzy Node Detection & Resolution Algorithm** — fuzzy node types, detection pseudocode, and resolution strategy catalog.

## Boundaries

**In-scope:**
- §4 Freeze Pipeline overview — `freeze(workflow_def)` as a built-in engine op; the end-to-end stage list (Spec Refinement → Validation → Test Runner → Impact Report → Review → Staged Rollout → Post-Change Summary).
- §4.1 Spec Refinement Assistant — the 5-step scan/propose/present/decide/record loop; "the Assistant flags and proposes; the human decides."
- §4.1b `llm_reasoning` Job Resolution During Freeze — the 4-step flag/propose/decide/record loop for `generate_draft`/`modify_spec`/`kb_write` capabilities.
- §4.2 Canary Gating & Auto-Rollback — the 4-stage rollout table (Canary 1%, Canary 10%, 50%, 100%) with gate criteria and auto-rollback triggers; rollback mechanism (redeploy previous Spec, quarantine canary data, P2 incident).
- §4.3 Fuzzy Node Detection & Resolution Algorithm — §4.3.1 Fuzzy Node Types, §4.3.2 Detection Algorithm (pseudocode), §4.3.3 Resolution Strategy Catalog.

**Delegated / out-of-scope:**
- The Compute Spec language and Job Types scanned by the pipeline → [`compute-spec.md`](compute-spec.md) (§6).
- The Sandbox used by the Test Runner for dry-runs → [`execution-sandbox.md`](execution-sandbox.md) (§7).
- The Design Artifact schema (the handoff YAML carrying `fuzzy_nodes`, `confirmed_fields`, `confidence_summary`) → [`design-artifact.md`](design-artifact.md) (§3.3).
- MCP-based LLM invocations used by the Spec Refinement Assistant → [`agent-platform`](../agent-platform/).
- Code Graph, Business Glossary, and KB fuzzy-search used during detection → [`knowledge-services`](../knowledge-services/).
- Notification, Audit Trail, Incident Manager, Release Manager → [`platform-core`](../platform-core/).

**Upstream/downstream neighbors:**
- *Input*: Design Artifact (YAML) from the Exploration Environment, carrying `fuzzy_nodes` and `llm_reasoning` Jobs.
- *Output*: frozen Workflow Definition, deployed through staged canary rollout to Production.

## Interfaces

### §4 Freeze Pipeline — stage list

```
Design Artifact (YAML)
    │
    ├── Spec Refinement Assistant: Scan `llm_reasoning` Jobs (capabilities beyond `read_analyze`/`suggest_plan`) and `fuzzy_nodes` → flag → propose deterministic solutions → mandatory human sign-off
    │   (Not auto-replacement; assists decision-making; all resolutions are recorded)
    ├── Validation Engine: Schema Validation + DQ Gate + Logical Integrity Check
    ├── Test Runner (Sandbox): Execute on sampled data → Snapshot comparison → Regression Test
    ├── Pre-Change Impact Report (Auto-generated): Diff + Why + Impact Scope Diagram + Data Preview
    ├── Review: PR → Peer Review + Business Approver + Data Owner
    ├── Staged Rollout: Canary (see Canary Gating below)
    └── Post-Change Summary (Auto-generated): Design Consistency Check + Update DAG + Change Log
```

### §4.1 Spec Refinement Assistant — 5-step loop

The Spec Refinement Assistant replaces the traditional "Script Compiler" concept. It does **not** automatically replace AI-generated fuzzy nodes with deterministic code. Instead:

| Step           | Action                                                                                                                                                                                                           | Human Involvement                                                  |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| **1. Scan**    | Parse Design Artifact; identify all `fuzzy_nodes` (markers: AMBIGUOUS_FILTER, UNRESOLVED_REFERENCE, UNCERTAIN_FORMULA, MISSING_THRESHOLD, etc.) and all `llm_reasoning` Jobs with capabilities beyond `read_analyze` or `suggest_plan` | None                                                               |
| **2. Propose** | For each fuzzy node, generate 1–3 determinization proposals with trade-off explanations (performance, correctness, edge-case behavior). Each proposal includes a confidence score and affected downstream nodes. | None                                                               |
| **3. Present** | Render proposals in the Workbench with diff preview, impact visualization, and KB evidence links. Fuzzy nodes are grouped by risk level.                                                                         | None                                                               |
| **4. Decide**  | User reviews each proposal and either: (a) accepts one, (b) edits and accepts, (c) provides a custom resolution, or (d) escalates to a Data Owner.                                                               | **Mandatory** — all fuzzy nodes must be resolved before proceeding |
| **5. Record**  | Every resolution is recorded with: who, when, which proposal, any edits, and the final deterministic Spec fragment. This record is immutable and linked to the Audit Trail.                                      | Sign-off captured automatically                                    |

**Key Principle**: The Assistant flags and proposes; the human decides. There is no "auto-compile" path from exploration artifact to production Spec.

### §4.1b `llm_reasoning` Job Resolution During Freeze — 4-step loop

In addition to `fuzzy_nodes`, the Freeze Pipeline identifies all `llm_reasoning` Jobs whose `capability` is `generate_draft`, `modify_spec`, or `kb_write`. For each:

| Step | Action | Human Involvement |
|------|--------|-------------------|
| **1. Flag** | Identify `llm_reasoning` Jobs with capabilities beyond `read_analyze`/`suggest_plan` | None |
| **2. Propose** | For each flagged Job, generate 1-3 deterministic replacement options (Python/SQL script, KB lookup, manual input placeholder) with trade-off explanations | None |
| **3. Decide** | User reviews and: (a) accepts a deterministic replacement, (b) edits and accepts, (c) provides custom logic, or (d) explicitly justifies retaining the `llm_reasoning` call with a documented rationale | **Mandatory** |
| **4. Record** | Every resolution is recorded immutably — who, when, which option, and the final artifact | Sign-off captured automatically |

This ensures that when a Workflow enters Production Environment, every step is either deterministic or has an explicitly documented and approved LLM dependency.

### §4.2 Canary Gating & Auto-Rollback — staged rollout

Staged rollout is governed by explicit canary gating criteria. The system automatically advances or rolls back based on observed metrics — no manual gate check required for standard cases.

| Stage          | Traffic              | Duration                               | Gate Criteria (all must pass)                                                                                                                     | Auto-Rollback Trigger                                          |
| -------------- | -------------------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| **Canary 1%**  | 1% of scheduled runs | 2 full cycles or 4h (whichever longer) | (a) Zero execution errors; (b) Output row count within ±5% of baseline; (c) All quality checks pass; (d) No schema drift detected                 | Any gate failure → immediate rollback; incident auto-created   |
| **Canary 10%** | 10%                  | 6 full cycles or 24h                   | All Stage-1 criteria + (e) p95 latency ≤ 1.5× baseline; (f) Cost per run ≤ 1.2× baseline; (g) Zero data-quality regressions vs. baseline snapshot | Any gate failure → rollback; notify Business Approver          |
| **50%**        | 50%                  | 12 cycles or 72h                       | All Stage-2 criteria + (h) Downstream consumers report zero issues; (i) Reconciliation pass (if applicable)                                       | Any gate failure → rollback; full post-mortem required         |
| **100%**       | Full cutover         | Permanent                              | All prior criteria sustained for 24h at 50%                                                                                                       | Manual rollback still available for 7 days via Release Manager |

**Rollback Mechanism**: Rollback redeploys the previous validated Spec version. All data written by the canary (files, DB writes) is quarantined and flagged for review. The Incident Manager creates a P2 incident with full context. After rollback, the frozen artifact is returned to `draft` status with the failed canary results attached.

## Dependencies

- **Spec Refinement Assistant**: parses the Design Artifact (§3.3); calls KB Business Glossary and KB fuzzy-search to generate proposals (routes to [`knowledge-services`](../knowledge-services/)); may invoke LLMs via MCP for proposal generation (routes to [`agent-platform`](../agent-platform/)).
- **Validation Engine**: Schema Validation + DQ Gate + Logical Integrity Check; runs the Python AST scan (§7.2) and SQL AST scan (§7.3); performs cycle detection, type checking, timeout validation, and engine-compatibility check (§6.1/§6.2).
- **Test Runner**: acquires a Sandbox from the Warm Pool (<100ms, §7); executes the frozen Spec on a 5% sample via Light Engine; captures output snapshot, execution trace, row counts.
- **Impact Report Generator**: computes diff (Spec vs base); queries the Code Graph for upstream/downstream impact; simulates data impact (old vs new on historical data); aggregates test results + approval requirements.
- **Git Platform (GitHub/GitLab)**: hosts the freeze PR (`freeze/{workflow_id}` branch); PR body carries the Impact Report.
- **Release Manager**: drives staged rollout (Canary 1% → 10% → 50% → 100%); queries Monitoring (Prometheus + Alertmanager) for gate-criteria metrics.
- **Notification / Audit / Incident Manager** ([`platform-core`](../platform-core/)): PR-created notifications, immutable resolution records, P2 incidents on rollback.
- Cross-sub-project: [`knowledge-services`](../knowledge-services/) (Code Graph, Data Catalog, Business Glossary, KB fuzzy-search), [`agent-platform`](../agent-platform/) (LLM proposals via MCP), [`platform-core`](../platform-core/) (Notification, Audit, Incident, Release Manager).

## Data Model

- **`freeze(workflow_def) → frozen_spec`** — the built-in engine operation; input is a Design Artifact, output is a frozen Workflow Definition.
- **`FuzzyNode`** — produced by §4.3.2 detection: `{ type, location (line_number), evidence, suggestions[] }`. Types include `MISSING_OR_AMBIGUOUS_SOURCE`, `IMPLICIT_JOIN`, `AMBIGUOUS_AGGREGATION`, `INFERRED_BUSINESS_LOGIC` (full list in §4.3.1).
- **`FuzzyNodeProposal`** — produced by Step 2 (Propose): 1–3 per fuzzy node, each with trade-off explanations (performance, correctness, edge-case), a confidence score, and affected downstream nodes.
- **Resolution record** — immutable: `{ who, when, which proposal, edits, final deterministic Spec fragment }`; linked to the Audit Trail.
- **`llm_reasoning` resolution record** — immutable: `{ who, when, which option, final artifact }`; captures deterministic replacement or documented rationale for retention.
- **`ValidationReport`** — `{ pass, warnings, errors }` from the Validation Engine.
- **`TestResult`** — `{ passed, snapshot_ref, trace_id }` from the Test Runner (5% sample, Light Engine).
- **`ImpactReport`** — Markdown + JSON; diff, upstream/downstream impact, data-impact simulation, test results, approval requirements.
- **Canary log** — per-stage gate-criteria metrics (error rate, row-count delta vs ±5% baseline, quality checks, schema drift, p95 latency vs 1.5× baseline, cost per run vs 1.2× baseline, DQ regressions, downstream-consumer issues, reconciliation pass).
- **`DeployResult`** — `{ success, canary_log }`.

## Failure Modes & Recovery

| Failure | Impact | Recovery |
| --- | --- | --- |
| Artifact with unresolved `fuzzy_nodes` | Cannot freeze | Freeze Pipeline rejects any artifact with unresolved fuzzy nodes (see [`design-artifact.md`](design-artifact.md) §3.3). All fuzzy nodes must be resolved before proceeding (Step 4 — Mandatory). |
| Artifact with `overall` confidence `< 0.8` | Insufficient review depth | Mandates full peer review (per §3.3 `confidence_summary` semantics). |
| Validation failure (schema / DQ / logic / cycle / type / timeout / Python AST / SQL AST / engine compat) | Spec invalid | `ValidationReport` returned; loop back to user resolution (step 9 of §21.1). |
| Test Runner failure (snapshot diff / regression) | Spec behavior wrong | Render test failure with diff; loop back to user resolution. |
| Canary 1% gate failure | Production risk | Immediate rollback; P2 incident auto-created; artifact returned to `draft` with failed canary results attached. |
| Canary 10% gate failure | Production risk | Rollback; notify Business Approver. |
| 50% gate failure | Production risk | Rollback; full post-mortem required. |
| Two fuzzy nodes suggest conflicting resolutions | Ambiguous fix | Both surfaced to user with impact comparison (Conflict Resolution Rule). |
| User mapping conflicts with KB | Override decision needed | User definition wins, recorded as KB override. |

## Non-Functional Requirements

### §4.2 Canary gating — quantitative targets

- **Canary 1%**: 1% of scheduled runs; 2 full cycles or 4h (whichever longer); gates — (a) zero execution errors, (b) output row count within ±5% of baseline, (c) all quality checks pass, (d) no schema drift.
- **Canary 10%**: 10%; 6 full cycles or 24h; adds (e) p95 latency ≤ 1.5× baseline, (f) cost per run ≤ 1.2× baseline, (g) zero DQ regressions vs baseline snapshot.
- **50%**: 50%; 12 cycles or 72h; adds (h) downstream consumers report zero issues, (i) reconciliation pass (if applicable).
- **100%**: full cutover; permanent; requires all prior criteria sustained for 24h at 50%; manual rollback available for 7 days via Release Manager.
- **Rollback SLO**: redeploy previous validated Spec version; quarantine all canary-written data (files, DB writes); P2 incident with full context.

### §4.3.1 Fuzzy node detection — confidence thresholds

- **Implicit JOIN**: any missing explicit JOIN → flag.
- **Inferred Business Logic**: confidence `< 0.9` → flag.
- **Schema resolution**: `resolved.confidence < 1.0` → flag as `MISSING_OR_AMBIGUOUS_SOURCE`.

## Key Flows

### §4.3 Fuzzy Node Detection & Resolution Algorithm

> The core algorithm of Freeze Pipeline — how to transform AI-generated fuzzy design drafts into deterministic scripts.

#### §4.3.1 Fuzzy Node Types (Fuzzy Node Classification)

| Type                        | Example                                             | Detection Method                                                                     | Confidence Threshold             |
| --------------------------- | --------------------------------------------------- | ------------------------------------------------------------------------------------ | -------------------------------- |
| **Implicit JOIN**           | "sales by region" without explicit JOIN path        | Schema graph traversal: no direct FK path found between `sales` and `region` → fuzzy | Any missing explicit JOIN → flag |
| **Ambiguous Aggregation**   | "average" without window/group specification        | AST analysis: aggregate function without GROUP BY clause                             | —                                |
| **Underspecified Filter**   | "last quarter" without date column mapping          | Temporal expression detected without concrete WHERE clause on timestamp column       | —                                |
| **Inferred Business Logic** | "revenue = sales - returns" without KB confirmation | Formula extracted from NL but no matching entry in Business Glossary                 | Confidence < 0.9 → flag          |
| **Missing Data Source**     | Reference to table/view not found in Data Catalog   | Catalog lookup failure                                                               | —                                |

#### §4.3.2 Detection Algorithm (Pseudocode)

```
function detectFuzzyNodes(computeSpec):
    fuzzyNodes = []
    
    for each job in computeSpec.jobs:
        // 1. Schema Resolution Check
        for each tableRef in job.inputs:
            resolved = dataCatalog.resolve(tableRef)
            if not resolved or resolved.confidence < 1.0:
                fuzzyNodes.add(FuzzyNode(
                    type="MISSING_OR_AMBIGUOUS_SOURCE",
                    location=tableRef.line_number,
                    evidence=f"Table '{tableRef.name}' not found in Data Catalog",
                    suggestions=dataCatalog.fuzzySearch(tableRef.name, topK=3)
                ))
        
        // 2. JOIN Path Validation
        if job.type == "transform" and job.sql:
            ast = parseSQL(job.sql)
            for each tablePair in extractTablePairs(ast):
                path = codeGraph.findShortestPath(tablePair.a, tablePair.b)
                if not path or path.hops > 2:
                    fuzzyNodes.add(FuzzyNode(
                        type="IMPLICIT_JOIN",
                        location=tablePair.line_number,
                        evidence=f"No direct FK relationship between {tablePair.a} and {tablePair.b}",
                        suggestions=codeGraph.suggestJoinPaths(tablePair.a, tablePair.b)
                    ))
        
        // 3. Aggregation Completeness
        if job.type == "transform":
            aggregates = extractAggregates(job.sql or job.ops)
            for each agg in aggregates:
                if not agg.hasGroupBy and not agg.isWindowFunction:
                    fuzzyNodes.add(FuzzyNode(
                        type="AMBIGUOUS_AGGREGATION",
                        location=agg.line_number,
                        evidence=f"Aggregate '{agg.function}' missing GROUP BY or OVER clause"
                    ))
        
        // 4. Business Logic Verification
        if job.type == "transform" and job.python_code:
            formulas = extractFormulas(job.python_code)
            for each formula in formulas:
                glossaryEntry = kb.queryBusinessGlossary(formula.name)
                if not glossaryEntry or glossaryEntry.confidence < 0.9:
                    fuzzyNodes.add(FuzzyNode(
                        type="INFERRED_BUSINESS_LOGIC",
                        location=formula.line_number,
                        evidence=f"Formula '{formula.name}' not confirmed in Business Glossary",
                        suggestions=kb.suggestGlossaryMatches(formula.name)
                    ))
    
    return fuzzyNodes
```

#### §4.3.3 Resolution Strategy Catalog

For each Fuzzy Node type, provide 1-3 deterministic options for human selection:

| Strategy                        | When Used                     | Example                                                                                                                                                                                                       |
| ------------------------------- | ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Schema Binding**              | Missing/ambiguous data source | "Select from: `sales_orders` (ERP) or `sales_orders_v2` (Data Warehouse) — [IT Admin confirmed ERP is authoritative]"                                                                                         |
| **JOIN Path Selection**         | Implicit JOIN                 | "Path A: `orders.customer_id → customers.id` (direct FK, 1 hop). Path B: `orders.region_code → regions.code → geo.customer_region` (2 hops via mapping table). Confidence: A=0.98, B=0.72. Recommend Path A." |
| **Aggregation Disambiguation**  | Ambiguous aggregation         | "Option 1: GROUP BY region, month. Option 2: Moving average OVER (PARTITION BY region ORDER BY month ROWS 2 PRECEDING). Context: user requested 'monthly trend' → Recommend Option 2."                        |
| **Business Logic Confirmation** | Inferred formula              | "Formula 'net_revenue = gross_sales - returns - discounts' matches glossary entry 'Net Revenue (ASC 606)' with confidence 0.85. Please confirm or edit."                                                      |
| **Manual Override**             | No high-confidence suggestion | "Cannot resolve. Please specify manually: [free-text input + schema browser]"                                                                                                                                 |

**Conflict Resolution Rule**: When user explicitly defines a mapping that conflicts with KB → user definition wins (recorded as KB override). When two fuzzy nodes suggest conflicting resolutions → both surfaced to user with impact comparison.

### Shared runtime sequence

The complete freeze-side flow — from USER clicking "Freeze", through SRA scanning fuzzy nodes, Validation, Test Runner, Impact Report, PR creation, Review, and the full Canary 1% → 10% → 50% → 100% rollout with auto-rollback — is documented end-to-end in [`../_shared/sequence-diagrams.md`](../_shared/sequence-diagrams.md) **§21.1 Freeze Flow: Full End-to-End**. That sequence is the canonical reference for this module's Key Flows and is co-owned with [`agent-platform`](../agent-platform/) (Spec Refinement Assistant uses LLM), [`knowledge-services`](../knowledge-services/) (Code Graph for impact), and [`platform-core`](../platform-core/) (Notification, Audit Trail, Release Manager, Incident Manager).

## Design References

- **Original sections**: §4 (Freeze Pipeline), §4.1 (Spec Refinement Assistant), §4.1b (`llm_reasoning` Job Resolution During Freeze), §4.2 (Canary Gating & Auto-Rollback), §4.3 (Fuzzy Node Detection & Resolution Algorithm), §4.3.1 (Fuzzy Node Types), §4.3.2 (Detection Algorithm — Pseudocode), §4.3.3 (Resolution Strategy Catalog) of [`docs/03-architecture.md`](../../03-architecture.md).
- **Related workflow-engine docs**: [`compute-spec.md`](compute-spec.md) (§6 — Job Types and trigger rules validated during freeze), [`execution-sandbox.md`](execution-sandbox.md) (§7 — Sandbox used by the Test Runner), [`design-artifact.md`](design-artifact.md) (§3.3 — the Design Artifact whose `fuzzy_nodes` are scanned).
- **Shared sequence diagram**: [`../_shared/sequence-diagrams.md`](../_shared/sequence-diagrams.md) §21.1 Freeze Flow: Full End-to-End (primary sub-project).
- **ADRs** ([index](../../adr-index.md)): [ADR-0025 Unified Workflow Engine](../../../adr/0025-unified-workflow-engine.md) (freeze is a built-in engine op, not a separate plane), [ADR-0006 Freeze Bridge Independence](../../../adr/0006-freeze-bridge-independence.md) (the freeze stage's independence guarantees), [ADR-0005 Four-Layer Architecture](../../../adr/0005-four-layer-architecture.md) (Zero AI Side Effects — enforced by mandatory human sign-off).
- **Glossary** ([../../glossary.md](../../glossary.md)): Freeze Pipeline, Spec Refinement Assistant, Fuzzy Node, Canary Gating, Auto-Rollback, Validation Engine, Test Runner, Impact Report.
- **Cross-references retained from source**: §3.3 (Design Artifact schema carrying `fuzzy_nodes`); §6.1 (engine-compatibility check run by the Validation Engine); §7.2 / §7.3 (Python AST + SQL AST scans run at step 14 of §21.1); §9.2 (Post-Change Summary generated at step 42 of §21.1).
