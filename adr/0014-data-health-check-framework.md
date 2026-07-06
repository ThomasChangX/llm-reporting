# ADR-0014: Unified Data Health Check Framework

- **Status**: Accepted
- **Date**: 2026-07-04
- **Deciders**: Project Sponsor

## Context

The system requires three data health check capabilities:

1. **DQ Rule (Rule-Driven)**: The user knows what to check — "amount cannot be NULL", "Line 3 and Line 12 must be consistent"
2. **Recon (Cross-Source Reconciliation)**: Two independent data sources matched by key to identify discrepancies — "ERP General Ledger vs. Bank Statements"
3. **Anomaly Detection (ML-Driven)**: The user doesn't know what to check — "whether this P&L date's data deviates abnormally from historical patterns", "ratio jumps across time dimensions"

The current design models the three as independent engines, with the following issues:
- Users don't care whether an anomaly was discovered by rules or ML — they only care about "What problems does my Report have today?"
- All three share output pipelines (Annotated Report, Alerts, Incidents), but are currently independent of each other
- Recon's Break Analysis uses AI (Design Plane), but the AI-assisted paths for DQ and Anomaly are not unified
- Industry trends (Monte Carlo, Soda, Great Expectations 2024-2026) are moving toward unification

## Options Considered

### Option A: Keep Three Separate Engines (Rejected)
Maintain the current design: DQ Framework + Recon Engine + new Anomaly Detection Engine.
- **Pro**: Each engine focuses on its own domain with independent optimization paths
- **Con**: Fragmented user mental model; three configuration schemas increase learning cost; the industry has already moved toward unification

### Option B: Unify Under Data Health Check Framework (Chosen)
A unified YAML configuration-driven framework, three check types, unified execution scheduling, unified output pipeline (Annotated Report), unified alerting.

### Option C: ML-Only (Rejected)
Rely solely on ML anomaly detection without providing explicit rule definitions.
- **Pro**: Zero configuration for users
- **Con**: Not explainable — financial/audit scenarios require precise reproducibility; users cannot express known business rules; no industry precedent

## Decision

Adopt **Option B** (Unified Data Health Check Framework):

### Unified Configuration Schema

```yaml
data_health:
  profile: "monthly_close_check"        # User-nameable, reusable
  scope:                                 # Detection scope
    reports: ["pnl_daily", "balance_sheet"]
    metrics: ["gross_margin", "revenue_growth"]
    datasources: ["erp_gl"]
  
  checks:
    - name: "Line 3 must not be empty"
      type: rule
      dimension: completeness
      scope: { line: 3, column: "amount" }
      condition: "value IS NOT NULL"
      severity: error

    - name: "Line 3 period-over-period anomalous jump"
      type: anomaly
      scope: { line: 3, column: "amount" }
      method: ratio_change
      params:
        window: 1
        direction: both
        threshold_pct: 15
      sensitivity: medium
      severity: warning

    - name: "ERP vs Bank monthly reconciliation"
      type: recon
      source_a: { connector: erp_gl, table: transactions }
      source_b: { connector: bank, table: statements }
      match_keys: [{ a: txn_id, b: ref_id }]
      compare_fields: [{ a: amount, b: amount, tolerance_pct: 0.01 }]
      schedule: monthly
      severity: error

    - name: "ERP vs Bank match rate anomalous decline"
      type: anomaly
      scope: { recon_check: "ERP vs Bank monthly reconciliation" }
      method: trend_change
      params:
        metric: match_rate
        window: 3
        threshold_pct: 5
      sensitivity: high
      severity: warning
```

### Three Check Types

| Type | Driver | Defined By | Purpose |
|---|---|---|---|
| `rule` | Explicit condition | Dev / Power User | Known business rules, compliance constraints |
| `anomaly` | ML statistical model | Regular User (one-click creation) | Unknown pattern deviations, trend anomalies |
| `recon` | Cross-source matching | Dev / Admin | Dual-party data consistency verification |

### Common Configuration Items (shared across all three types)

| Config Item | Description |
|---|---|
| `name` | Human-readable name |
| `severity` | error / warning / info |
| `schedule` | auto (automatically after Report generation), cron (scheduled), manual (manual trigger), on_recon_complete (automatically after Recon execution) |
| `scope` | Binding target: Report/Metric/Datasource |
| `output` | Produces Annotated Report (annotated outliers) + Alert + Incident |

### Output Pipeline (Unified)

Data Health Check execution feeds into: Annotated Report (with root cause summary + confidence score, user can click to follow up with AI Agent) → Intelligence Plane (AI Agent auto-generates Health Summary, user can ask follow-up questions, Agent does KB + Code Graph + historical data attribution analysis, user can create BRD → push to Jira/Rally/ServiceNow) → Alert Manager (error → PagerDuty/Slack/Email, warning → Dashboard notification, info → Log only) → Incident Manager for error level (auto-create Incident, associate affected Report/Metric, trigger diagnostic Agent S07).

### Execution Scheduling Modes

| Mode | Trigger | Suitable Scenarios |
|---|---|---|
| `auto` | Automatically after Report generation | Standard Report publishing flow |
| `scheduled` | Cron timer | Cross-period trend monitoring |
| `manual` | User manually triggers | Ad-hoc investigation, debugging |
| `on_recon_complete` | Automatically after Recon execution | Anomaly trend detection on reconciliation results |

### Adjustment Trigger Path Correction

Recon Break Analysis no longer includes "Auto-write-off". Resolution suggestions output is corrected to:

| Classification | AI Suggestion | Subsequent Action |
|---|---|---|
| TIMING | "Verify next period" reminder | Auto-create reminder (zero financial impact) |
| ROUNDING | "Suggested write-off" (generate Adjustment Draft) | → Adjustment Form (Permission → Validation → Approval → Trigger ETL) |
| MISSING | "Suggest creating Adjustment entry" | → Adjustment Form (same as above) |
| MAPPING | "Suggest updating Mapping Registry" | → KB Update Request (follow KB confirmation process) |
| UNKNOWN | "Manual review" | → Escalate to Data Owner |

**Core Principle**: Any operation that modifies financial data, regardless of amount, must go through the Permission → Validation → Approval process. There is no Auto-write-off.

## Rationale

1. **Unified User Mental Model**: Users only need to ask "Is my data healthy?" — not caring whether the underlying method is rule-based, ML, or cross-source matching.
2. **Configuration Reuse**: Common configuration items such as scope, severity, schedule, and output only need to be defined once.
3. **Industry Alignment**: Monte Carlo, Soda, Great Expectations 2024-2026 are all trending toward unified frameworks.
4. **Unified AI Agent Orchestration**: Anomalies from all three check types can go through the same Agent pipeline for attribution analysis → BRD → Ticket.
5. **Extensible**: Adding new check types in the future does not affect the existing configuration structure.

## Consequences

- **Positive**: Unified configuration reduces learning cost; unified output pipeline eliminates alert fragmentation; AI Agent can orchestrate attribution flow uniformly.
- **Negative**: Unified framework requires additional abstraction layer maintenance; cross-source specificity of `type: recon` depends on Data Connector maturity.
- **Neutral**: Refactoring from three engines to a unified framework requires a one-time migration cost — recommended to design directly with the unified framework during the MVP phase to avoid later refactoring.

## Linked Modules

- `docs/03-architecture.md` → §12 (Data Health Check Framework detailed design)
- `docs/02-requirement.md` → FR18 (Reconciliation), FR19 (Data Quality), newly added FR19b (Anomaly Detection)
- `docs/03-architecture.md` → §22E (Agent Workflow Composition — Anomaly→BRD→Ticket scenario)
- `docs/03-architecture.md` → §7 (Adjustment Form Builder & Workflow)
