# ADR-0015: Agent Triage & Layered Remediation Gateway

- **Status**: Accepted
- **Date**: 2026-07-04
- **Deciders**: Project Sponsor

## Context

The Data Health Check Framework (ADR-0014) produces unified detection results (three types: rule / anomaly / recon), but there is a gap between detection results and user action:

1. **Alert Volume Problem**: A mid-scale BI system may produce tens to hundreds of Health Check results per day. Users cannot review each one — industry reports show 30-40% of alerts are known false-positive patterns
2. **Asymmetric Agent Intervention**: Recon has S09 automatically analyzing discrepancies, but Agent analysis for `type: rule` and `type: anomaly` requires the user to proactively follow up — unsustainable as alert volume grows
3. **Single Approval Granularity**: Currently only one path: Permission → Validation → Approval, but the risk variance across operations is enormous — marking a false positive (zero risk) and modifying financial data (SOX compliance risk) should not go through the same approval chain
4. **Lack of Closed-Loop Learning**: Users repeatedly follow up on the same type of anomaly, repeatedly mark the same type of false positive — the system does not learn from these signals to optimize rules

The answer from industry best practices (Monte Carlo 2025-2026) is: **Layer an Agent Triage Layer on top of the detection layer**, enabling automatic classification, false-positive filtering, and severity re-evaluation. Production data shows MTTR reduction of 50-70%, alert volume reduction of 30-40%.

## Options Considered

### Option A: Keep Current — User-Driven Investigation (Rejected)
Maintain the existing design: Agent only responds when the user proactively follows up.
- **Pro**: Simple architecture, Agent behavior is fully controllable
- **Con**: Unsustainable as alert volume grows; excessive user cognitive burden; no learning feedback loop

### Option B: Fully Autonomous Remediation (Rejected)
AI Agent automatically handles all detection results, including auto-closing alerts, auto-adjusting rules, and auto-executing fixes.
- **Pro**: Minimizes manual intervention
- **Con**: Auto-closing false positives may mask real issues (industry-verified risk); unacceptable in financial/audit scenarios — SOX requires human approval records for all finance-related changes

### Option C: Agent Triage + Layered Remediation Gateway (Chosen)
Agent automatically classifies and pre-judges (read-only operations), humans approve based on risk level triage.

## Decision

Adopt **Option C** (Agent Triage + Layered Remediation Gateway):

### Agent Triage Layer (Intelligence Plane — new addition)

Data Health Check execution complete (any type, any severity) → Agent Triage Layer (Intelligence Plane — read-only analysis):

- **severity=error**: Auto-trigger S07 IncidentDiagnostician with parallel sub-agents (Pipeline Change Investigator + Data Anomaly Investigator + Infrastructure Investigator + Historical Pattern Matcher) → composite output: root cause hypothesis + Evidence Chain + confidence level → additional judgment: Is this rule known for high false positives? → suggested action: Block or Override with reasoning
- **severity=warning**: Agent proactively generates Health Summary push → dedup/merge (multiple alerts from same root cause → one summary) → pattern matching (search similar anomalies from past 30 days) → pre-judgment with confidence → push via Slack/Email/In-App → user options: Ignore / Follow up for details / Create BRD / Adjust rules
- **severity=info**: Log only (no proactive push)

**Key Constraint**: All operations in Agent Triage are **read-only analysis**. Any operation that modifies configuration or data must pass through human confirmation via the Remediation Gateway.

### Layered Remediation Gateway (L0-L3)

| Level | Risk | Example Operations | Approval Requirement | Audit |
|---|---|---|---|---|
| **L0 — Zero Risk** | No production impact | Mark false positive, adjust personal Dashboard layout, add notes | Zero approval, auto-execute | Log only |
| **L1 — Low Risk** | Impacts alert behavior only | Adjust anomaly sensitivity, add exclusion rule, silence known false-positive patterns | Agent suggestion → user one-click confirm | Record operator + timestamp |
| **L2 — Medium Risk** | Impacts detection logic | Modify DQ Rule threshold, update KB entry, adjust materialization strategy | Single Approver + DQ Gate auto-validation | Full audit trail |
| **L3 — High Risk** | Impacts data/financials | Adjustment (modify financial data), production Workflow changes, KB definition changes | Dual approval + complete Impact Report + Canary gradual rollout | SOX/HIPAA-level audit |

**Remediation Gateway & Freeze Bridge Relationship**: L3 operations after Remediation Gateway approval → enter Freeze Bridge (if Workflow/Spec change) or execute directly (if one-time data modification). L0-L2 operations do not pass through Freeze Bridge — they are not within the scope of Compute Spec changes.

### S08 Closed-Loop Learning Upgrade

S08 DataQualityAdvisor upgraded to **signal-driven closed-loop learning**:

User action signals → false positive marking → S08 records pattern → cumulative threshold reached (3 times within 7 days) → suggests rule adjustment → user confirms (L1) → rule auto-updated. User repeatedly follows up on same anomaly (≥5 times within 30 days) → S08 suggests solidifying as type: rule → user confirms (L1) → generate rule YAML draft → L2 approval. Coverage gap detected → S08 suggests creating anomaly check → user confirms (L0) → auto-generate default configuration.

**Operations NOT auto-executed**: Modify DQ Rule severity/threshold → L2 (must verify modification does not introduce new blind spots). Modify KB definition → L3 (definition changes impact all downstream Workflows).

### Layered Agent Reasoning Architecture (Phase 7+ Evolution Direction)

MVP maintains the existing flat directory of 14 Skills. Phase 7+ evolves to Hierarchical Multi-Agent: Central "Brain" Reasoner with 5 Sub-Agents (Pipeline Change / Data Anomaly / Infrastructure / Upstream Dependency / Historical Pattern Matcher) running in parallel with consolidated judgment. Aligned with Monte Carlo 2025-2026 production architecture.

## Rationale

1. **Alert volume reduction is the highest-ROI first step**: Industry data shows 30-40% — filtering noise before users see alerts takes priority over improving RCA
2. **Layered approval solves the granularity problem**: L0-L3 prevents low-risk operations from being blocked by excessive approval while preventing high-risk operations from slipping through simplified approval
3. **Closed-loop learning is the guarantee of sustainability**: DQ rules without feedback loops drift over time; closed-loop learning enables rules to evolve in sync with the business
4. **Layered Agent architecture is an evolution direction, not an MVP requirement**: The MVP flat Skill directory is sufficient; Central Reasoner is introduced when alert volume reaches critical scale

## Consequences

- **Positive**: Expected alert volume reduction of 30-40%; expected MTTR reduction of 50-70% (known patterns); L0-L1 operations no longer blocked by approval bottlenecks; closed-loop learning enables DQ rules to evolve with the business
- **Negative**: Agent Triage Layer increases Intelligence Plane complexity; L0 auto-execution requires additional audit logging
- **Neutral**: Agent Triage pre-judgments may be wrong — all pre-judgments are annotated with confidence; users can always override. Weekly manual sampling review of L0/L1 automated actions (industry best practice)

## Linked Modules

- `docs/03-architecture.md` → §9 (Intelligence Plane — Agent Triage Layer)
- `docs/03-architecture.md` → §12.2 (Data Health Check — output pipeline includes Triage + Remediation Gateway)
- `docs/03-architecture.md` → §22B (S08 DataQualityAdvisor closed-loop learning upgrade)
- `docs/03-architecture.md` → §22A (Layered Agent Reasoning Architecture evolution direction)
- `adr/0014-data-health-check-framework.md` → Decision #12 (Unified Data Health Framework)
