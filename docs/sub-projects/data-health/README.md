# data-health — Data Quality, Reconciliation & Remediation

> **Origin**: §12.2 of `docs/03-architecture.md`
> **Key ADRs**: [ADR-0014](../../adr/0014-data-health-check-framework.md) (Unified Framework), [ADR-0015](../../adr/0015-agent-triage-remediation-gateway.md) (Agent Triage & Remediation Gateway)

## Positioning

The **Data Health** sub-project ensures financial data integrity through a unified YAML-configuration-driven framework covering three check types — rule-driven, ML-driven anomaly detection, and cross-source reconciliation. It integrates with the Agent Triage Layer (ADR-0015) for proactive issue surfacing and the Layered Remediation Gateway for tiered human approval of fixes.

This sub-project is business-critical: reconciliation breaks and data anomalies directly impact financial reporting accuracy (FR18, FR19).

## Boundaries

**In-scope:**
- Data Health Check Framework (unified YAML config, three check types: `rule`, `anomaly`, `recon`)
- Recon Execution Engine (cross-source reconciliation)
- Break Analysis (AI-assisted, Intelligence Plane)
- Anomaly Detection (ML-driven: ratio_change, z_score, seasonal_decomp, distribution_shift, trend_change; includes Temporal Consistency as 7th DQ dimension)
- Unified Output Pipeline (with Agent Triage Layer integration)
- Layered Remediation Gateway (L0–L3 tiered approval)
- DQ Gate (blocking point for rule/anomaly type)
- Consistency Bridge to Recon
- Agent Onboarding (Cold Start Guide)

**Delegated to other sub-projects:**
- AI-assisted break analysis reasoning → [`agent-platform`](../agent-platform/)
- Check results persistence → [`knowledge-services`](../knowledge-services/) (Adjustment History domain)
- Workflow execution of remediation → [`workflow-engine`](../workflow-engine/)

## Module List

| Module | Origin | Document |
|--------|--------|----------|
| Data Health Check Framework (all sub-components) | §12.2 | [`health-check-framework.md`](health-check-framework.md) |

## External Interface Contract

| Interface | Consumer | Contract |
|-----------|----------|----------|
| `health_check.run(config_yaml) → results` | Scheduler (cron), Workflow Engine (on_recon_complete) | Executes check, produces annotated results |
| `remediation.submit(break_id, fix_plan) → approval_chain` | Agent Platform, Business Users | Routes through L0–L3 gateway based on severity/amount |
| `anomaly.detect(scope, sensitivity) → anomalies` | Agent Platform (S08 DataQualityAdvisor) | ML-driven detection without explicit rules |

## Related ADRs

- [ADR-0014](../../adr/0014-data-health-check-framework.md) — Unified Data Health Check Framework
- [ADR-0015](../../adr/0015-agent-triage-remediation-gateway.md) — Agent Triage & Layered Remediation Gateway
