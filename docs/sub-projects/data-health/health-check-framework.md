# Data Health Check Framework

> **Origin**: §12.2 of [`docs/03-architecture.md`](../../03-architecture.md) | **Sub-project**: [data-health](README.md)

## Purpose

The Data Health Check Framework is a unified, configuration-driven framework (mapped to **FR18** and **FR19**) in which three check types — `rule`, `anomaly`, and `recon` — share a single scheduling → execution → output → alerting pipeline.

The driving philosophy: **users do not care whether an anomaly was found by rules or by ML** — they only care about "what's wrong with my data?". The framework therefore abstracts away the detection mechanism behind a single declarative YAML schema, a unified output pipeline, and a single Agent Triage Layer that classifies and summarizes findings regardless of how they were produced.

The framework is responsible for:

- Declaring data-quality, anomaly, and reconciliation checks via one common configuration schema.
- Executing those checks on a shared scheduling substrate (`auto` / `cron` / `manual` / `on_recon_complete`).
- Producing a unified output: annotated reports, alert routing, and incident creation.
- Powering an Intelligence-Plane Agent Triage Layer that performs read-only diagnosis, dedup/merge, confidence prediction, and remediation guidance.
- Routing any user- or agent-initiated *modification* operation through a tiered (L0–L3) Remediation Gateway so that financial and production-affecting changes always require human approval.
- Providing a cold-start path (Agent Onboarding) that bootstraps a tenant's DQ rules and anomaly checks from its own schema — strictly tenant-isolated.

## Boundaries

**In scope**

- Definition, scheduling, execution, and output of `rule`, `anomaly`, and `recon` checks.
- The unified configuration schema (`data_health` YAML profile) and its shared/common config items.
- The Recon Execution Engine (LOAD → HASH → JOIN → COMPARE → CLASSIFY) for `type: recon`.
- AI-assisted Break Analysis for unmatched/partial recon results (Intelligence Plane, read-only suggestions).
- The Agent Triage Layer that post-processes execution results by severity (`error` / `warning` / `info`).
- The Layered Remediation Gateway (L0–L3) that gates any modification operation on health-check outputs.
- The DQ Gate blocking points for `rule`/`anomaly` types across the pipeline lifecycle.
- The Consistency Bridge that promotes a `rule` consistency failure into a `recon` workflow.
- Anomaly detection learning-period lifecycle (`learning` → `active` → `stable` → `degraded`).
- Agent Onboarding cold-start for new tenants.

**Out of scope**

- The underlying Report publication pipeline itself (health checks *annotate* published reports but do not own publication).
- The Compute Spec / Freeze Bridge change-management process (referenced as a downstream consumer for L3 operations — see §9).
- Tenant identity, auth, and RBAC (consumed; not redefined here).
- Cross-tenant model learning or any global baseline — **explicitly forbidden** by the isolation constraint.

## Interfaces

### Configuration Interface (Inbound)

Checks are declared via a single `data_health` YAML block. The schema is unified across all three check types; per-type fields are gated by `type`.

```yaml
data_health:
  profile: "monthly_close_check"        # User-nameable, reusable
  scope:                                 # Detection scope
    reports: ["pnl_daily", "balance_sheet"]
    metrics: ["gross_margin"]
    datasources: ["erp_gl"]

  checks:
    # ─── type: rule (Rule-driven) ───
    - name: "Line 3 must not be empty"
      type: rule
      dimension: completeness
      condition: "value IS NOT NULL"
      severity: error
      schedule: auto                    # Auto-execute after Report output

    - name: "Line 3 and Line 12 must be consistent"
      type: rule
      dimension: consistency
      condition: "line_3_total == line_12_total"
      severity: error
      schedule: auto

    # ─── type: anomaly (ML-driven, no explicit rules needed) ───
    - name: "Line 3 abnormal period-over-period jump"
      type: anomaly
      method: ratio_change              # ratio_change | z_score | seasonal_decomp | distribution_shift | trend_change
      params:
        window: 1
        direction: both
        threshold_pct: 15
      sensitivity: medium
      severity: warning
      schedule: auto                    # Can also be set to cron or manual

    # ─── type: recon (Cross-source Reconciliation) ───
    - name: "ERP vs Bank Monthly Reconciliation"
      type: recon
      source_a: { connector: erp_gl, table: transactions }
      source_b: { connector: bank, table: statements }
      match_keys: [{ a: txn_id, b: ref_id, match_type: exact }]
      compare_fields: [{ a: amount, b: amount, tolerance_pct: 0.01 }]
      tolerance_tiers:
        strict: 0.00
        normal: "±0.01%"
        relaxed: "±1%"
      group_by: ["region", "currency"]
      schedule: monthly                 # Independent scheduling (run monthly)

    # ─── type: anomaly (ML-driven Recon Trend Detection) ───
    - name: "ERP vs Bank Match Rate Abnormal Trend Decline"
      type: anomaly
      scope: { recon_check: "ERP vs Bank Monthly Reconciliation" }
      method: trend_change
      params:
        metric: match_rate
        window: 3
        threshold_pct: 5
      sensitivity: high
      severity: warning
      schedule: on_recon_complete       # Auto after Recon execution
```

### Output Interface (Outbound)

All check types emit through the **Unified Output Pipeline** (see Key Flows), which fans out to:

- **Annotated Report** — anomaly values and alerts are appended to the normal Report output (row-level / cell-level marking). Each alert carries `check_name`, `severity`, deviation magnitude, and confidence. Annotations never block Report publication.
- **Alert Manager** — routes by severity (`error` → PagerDuty / Slack / Email; `warning` → Dashboard notification badge; `info` → Log only).
- **Incident Manager** — `error`-level findings auto-create an Incident, associated with the affected Report / Datasource, and include Agent Triage diagnostic results.

### Control / Blocking Interfaces

- **DQ Gate** — `rule` and `anomaly` checks can be inserted at multiple pipeline execution points (see Failure Modes & Recovery → DQ Gate) and may block deployment or execution at `severity=error`.
- **Remediation Gateway** — any modification operation against health-check results is routed by risk level (L0–L3).
- **Consistency Bridge** — a `rule` consistency failure can auto-trigger a downstream `recon` workflow.

## Dependencies

- **Connectors / Data Engines** — `recon` checks depend on the Light/Heavy Engine to LOAD Source A and Source B (see §3.4).
- **Compute Spec & Freeze Bridge** — L3 remediation operations that change Workflows/Specs enter the Freeze Bridge (see §9). L0–L2 operations do not.
- **Incident Manager & Alert Manager** — consumers of the unified output.
- **Intelligence Plane / Agents** — S07 IncidentDiagnostician is auto-triggered on `severity=error`. The Agent Triage Layer depends on the agent runtime described in §22A / §22B.
- **Business Glossary / KB** — Break Analysis may surface KB / Mapping Registry update requests.
- **Permission → Validation → Approval pipeline** — required for any Break Analysis follow-up that modifies financial data (Adjustment Form path).
- **Tenant Schema & Data Dictionary** — input to Agent Onboarding inference and to Day-0 rule auto-inference.

## Data Model

### Three Check Types

| Type | Driver | Defined By | Purpose |
|---|---|---|---|
| `rule` | Explicit conditional expressions | Dev / Power User | Known business rules, compliance constraints. 7 dimensions: completeness / accuracy / consistency / timeliness / uniqueness / validity / **temporal_consistency** |
| `anomaly` | ML statistical models | Regular User (one-click creation); **Agent Onboarding can auto-infer from tenant Schema** | Unknown pattern deviations, ratio jumps, distribution drift. Users only need to specify scope + sensitivity |
| `recon` | Cross-source matching via Hash Join | Dev / Admin | Two-source data matched by key, differences classified |

### Common Configuration Items (Shared by all three types)

| Config Item | Description |
|---|---|
| `name` | Human-readable name |
| `severity` | error / warning / info. error blocks downstream consumption and creates an Incident |
| `schedule` | **auto** (auto after Report output) / **cron** (scheduled) / **manual** (manual trigger) / **on_recon_complete** (auto after Recon execution) |
| `scope` | Binding targets: reports / metrics / datasources / recon_check — all three types can be defined on any user-configured scope |
| `profile` | User-named rule group, reusable across Reports (e.g., "monthly_close_check" contains 12 rules bound to 3 Reports) |
| `status` | **anomaly type only**: `learning` (establish baseline, no alerts) → `active` (normal alerting) → `stable` (long-term stable) → `degraded` (excessive anomaly rate, needs manual review). Day 0 auto-set to learning |

### Anomaly Detection Lifecycle (`status`)

The `status` field applies only to `type: anomaly` and tracks baseline maturity:

- `learning` — establishing baseline; **no alerts generated, no Triage push**.
- `active` — normal alerting after baseline is established.
- `stable` — long-term stable.
- `degraded` — anomaly rate >30% or consecutive user false-positive marks → requires manual review before restarting learning or converting to `type: rule`.

Day 0 auto-set to `learning`. See *Anomaly Detection Learning Period* in Key Flows for the day-by-day progression.

## Failure Modes & Recovery

### Recon Classification Triage

The Recon Execution Engine's CLASSIFY phase produces a three-way triage of every joined row. MATCHED rows auto-pass; UNMATCHED and PARTIAL rows are routed to Break Analysis.

```
Phase 1: LOAD   — Light/Heavy Engine loads Source A and Source B
Phase 2: HASH   — Compute match key hash (both sides)
Phase 3: JOIN   — Full outer join on match key hash
Phase 4: COMPARE — Compare matched rows by compare_fields and tolerance
Phase 5: CLASSIFY → Three-way triage:
  ┌──────────────┐  ┌──────────────────┐  ┌──────────────────────┐
  │   MATCHED     │  │    UNMATCHED      │  │      PARTIAL          │
  │ (exact+tol)   │  │ (no counterpart)  │  │ (match key OK,         │
  │ → Auto-pass   │  │ → Break Analysis  │  │  compare fields diff)  │
  └──────────────┘  └──────────────────┘  │ → Break Analysis      │
                                          └──────────────────────┘
```

### Break Analysis (AI-Assisted, Intelligence Plane)

For UNMATCHED / PARTIAL classification discrepancies, the Intelligence Plane infers causes and suggests resolution paths.

**Core Principle**: Any operation modifying financial data, regardless of amount, must go through the Permission → Validation → Approval process. **There is no Auto-write-off.**

| Classification | Meaning | AI Suggestion | Follow-up Action |
|---|---|---|---|
| TIMING | Both sides have data, different periods | "Verify next cycle" | Auto-create reminder (zero financial impact) |
| ROUNDING | Amount difference ≤ tolerance | "Suggest write-off" | → Adjustment Form (Permission→Validation→Approval→Trigger ETL) |
| MISSING | Only one side has data | "Suggest creating Adjustment entry" | → Adjustment Form (same as above) |
| MAPPING | Key mismatch | "Suggest updating Mapping Registry" | → KB Update Request (follow KB confirmation process) |
| UNKNOWN | Cannot classify | "Manual review" | → Escalate to Data Owner |

### DQ Gate (Blocking Point for `rule` / `anomaly` type)

Checks of `type: rule` and `type: anomaly` can be inserted at multiple execution points along the pipeline:

```
Source Register → Transform Step → Freeze Bridge Validation →
Runtime Pre-Exec → Runtime Post-Exec → Periodic Patrol
```

| Execution Point | Trigger | Behavior when severity=error |
|---|---|---|
| Freeze Bridge Validation | Every Freeze PR | Block deployment (must fix and resubmit) |
| Runtime Pre-Exec | Before Workflow execution | Block execution (prevent bad data entering downstream) |
| Runtime Post-Exec | After Workflow execution / Report output | Do not block publishing, but create Incident + annotate Report |
| Periodic Patrol | Cron scheduled | Create Incident (does not affect published Reports) |

### Anomaly Lifecycle Degradation & Recovery

If an anomaly check's anomaly rate exceeds 30%, or it receives consecutive user false-positive marks, its `status` is downgraded to `degraded`. Recovery requires **manual review** before the check can either restart learning or be converted into an explicit `type: rule`.

### Tenant Isolation Guarantee

Anomaly baselines are built using **only the tenant's own data**. There is no cross-tenant learning and no Global Baseline. This is both a correctness and a compliance boundary — see Agent Onboarding constraints below.

## Non-Functional Requirements

- **Strict tenant isolation** — baselines, learning, and Agent Onboarding inference use only the tenant's own Schema and data dictionary. No learning from other tenants; no Global Baseline.
- **No Auto-write-off** — financial modifications, regardless of amount, must traverse Permission → Validation → Approval. This is an inviolable control.
- **Read-only Triage** — all Agent Triage operations are analysis only: push summaries, suggest actions, predict confidence. Any operation modifying configuration or data must pass through human confirmation via the Remediation Gateway.
- **Progressive activation** — capabilities activate on a known timeline (Day 0 / 7 / 30 / 90). The system must manage tenant expectations and never promise instant full capabilities.
- **Non-blocking annotations** — anomaly annotations are appended to published report output; they never block publication.
- **SOX/HIPAA-grade audit** — required for L3 remediation operations (dual approval + complete Impact Report + Canary gradual rollout).

## Key Flows

### 1. Unified Output Pipeline (with Agent Triage Layer)

Every check execution — regardless of type — feeds into a single pipeline that first passes through the Agent Triage Layer (Intelligence Plane, read-only), then fans out by severity.

```
Data Health Check Execution (any type)
    │
    ▼
Agent Triage Layer (Intelligence Plane — read-only analysis)
    │
    ├── severity=error
    │    └── Auto-trigger S07 IncidentDiagnostician
    │         • Parallel diagnosis: Pipeline Change + Data Anomaly + Infrastructure + Historical Pattern
    │         • Additional check: Is this rule a known high-false-positive? (historical false-positive rate)
    │         • Output: Root cause hypothesis + Evidence Chain + suggested action (Block / Override)
    │
    ├── severity=warning
    │    └── Agent proactively generates Health Summary push (Slack/Email/In-App)
    │         • Dedup/Merge: Multiple alerts from the same root cause → one summary
    │         • Pattern matching: Search for similar anomalies in the past 30 days
    │         • Predicted confidence: Likely ignorable / Recommend investigation / Highly suspicious
    │         • User options: Ignore / Ask for details / Create BRD
    │
    └── severity=info → Log only (no proactive push)

    │
    ▼
Output (all severities)
    │
    ├──→ Annotated Report
    │    • Annotate anomaly values and alerts in normal Report output (row-level/cell-level marking)
    │    • Each alert carries: check_name / severity / deviation magnitude / confidence
    │    • Does not block Report publication — anomaly annotations are appended to the published output
    │
    ├──→ Alert Manager
    │    • error → PagerDuty / Slack / Email
    │    • warning → Dashboard notification badge
    │    • info → Log only
    │
    └──→ Incident Manager (error level)
         • Auto-create Incident → associate affected Report/Datasource
         • Includes Agent Triage diagnostic results
```

### 2. Layered Remediation Gateway (L0–L3 Tiered Approval)

Any modification operations by users (or proposed by the Agent) on Health Check results are routed by risk level:

| Level | Risk | Example Operations | Approval Requirement | Audit |
|---|---|---|---|---|
| **L0 — Zero Risk** | No production impact | Mark false positive, adjust personal Dashboard layout, add notes | Zero approval, auto-execute | Log only |
| **L1 — Low Risk** | Affects alerting behavior only | Adjust anomaly sensitivity, add exclusion rule, mute known false-positive patterns | Agent suggestion → user one-click confirm | Record operator + timestamp |
| **L2 — Medium Risk** | Affects detection logic | Modify DQ Rule threshold, KB entry update, materialization strategy adjustment | Single Approver + DQ Gate auto-validation | Full audit trail |
| **L3 — High Risk** | Affects data/financials | Adjustment (modify financial data), production Workflow changes, KB definition changes | Dual approval + complete Impact Report + Canary gradual rollout | SOX/HIPAA-grade audit |

**L3 & Freeze Bridge Relationship**: After L3 operations pass Remediation Gateway approval → enter Freeze Bridge (if Workflow/Spec change) or execute directly (if one-time data modification). L0–L2 operations do not pass through Freeze Bridge — they are not within Compute Spec change scope.

**Agent Triage Constraint**: All Triage operations are read-only analysis — push summaries, suggest actions, predict confidence. Any operation modifying configuration or data must pass through human confirmation via the Remediation Gateway.

### 3. Consistency Bridge to Recon

When a `type: rule` consistency check finds aggregate data inconsistent with detail data → auto-trigger a `type: recon` reconciliation Workflow. This bridges rule-based detection into deeper cross-source reconciliation when a consistency failure suggests the root cause spans two systems.

### 4. Anomaly Detection Learning Period

New tenants or newly created `type: anomaly` checks automatically enter the learning period. **Strict tenant isolation — baselines are built using only the tenant's own data.**

| Day | Capability | Description |
|---|---|---|
| 0 | Schema-based rules active | `type: rule` auto-inferred from column types/constraints takes effect immediately |
| 0–30 | Anomaly baseline building | `status: learning` — no alerts generated, no Triage push. Daily baseline statistics updated (mean, stddev, seasonal components) |
| 7 | ratio_change active | MoM spike detection (7 days of data sufficient for simple period-over-period comparison) |
| 30 | seasonal_decomp + z_score active | Monthly baseline established → seasonal patterns + statistical anomaly detection take effect |
| 90 | trend_change active | Quarterly baseline established → long-term trend deviation detection takes effect |

After the learning period ends, the Agent automatically pushes a summary; users can manually activate or extend. Anomaly check anomaly rate >30% or consecutive user false-positive marks → status downgraded to `degraded` → requires manual review before restarting learning or converting to `type: rule`.

### 5. Agent Onboarding (Cold Start Guide)

On a new tenant's first login → auto-trigger the Agent Onboarding Interview (see §22E Scenario 7):

1. Agent scans the tenant's connected Data Source Schema.
2. Auto-infers initial DQ Rules + Anomaly Checks from column types, DDL constraints, and naming conventions.
3. Infers Business Glossary draft from Chart of Accounts / Schema naming.
4. Conversational adjustment → generate Data Health Profile YAML.
5. Output progressive activation timeline — manage tenant expectations, no promise of instant full capabilities.

**Key Constraint**: All inference is based solely on the tenant's own Schema and data dictionary. No learning from other tenants, no Global Baseline usage. Strict tenant isolation.

## Design References

- **Source**: §12.2 of [`docs/03-architecture.md`](../../03-architecture.md) — Data Health Check Framework (FR18, FR19).
- [ADR-0014 — Unified Data Health Check Framework](../../../adr/0014-data-health-check-framework.md): establishes the unified `rule` / `anomaly` / `recon` configuration schema and shared scheduling → output → alerting pipeline.
- [ADR-0015 — Agent Triage & Layered Remediation Gateway](../../../adr/0015-agent-triage-remediation-gateway.md): establishes the Intelligence-Plane Agent Triage Layer (read-only) and the L0–L3 tiered approval gateway that gates all modification operations.
- **Cross-references in source**: §9 (Compute Spec / Freeze Bridge), §3.4 (Light/Heavy Engine), §22A / §22B (Intelligence Plane / Agents), §22E Scenario 7 (Agent Onboarding Interview).
- [`docs/glossary.md`](../../glossary.md): terminology for DQ dimensions, Incident, Profile, Recon, Break Analysis classifications.
- Sub-project entry point: [`data-health/README.md`](README.md).
