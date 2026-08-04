# Change Intelligence & Agent Triage

> **Origin**: §9 of [`docs/03-architecture.md`](../../03-architecture.md) (lines 1114–1165) | **Sub-project**: [knowledge-services](README.md)

## Purpose

Change Intelligence & Agent Triage is the system's reasoning layer over **change** and **alert volume**. It solves two problems stated in §9: *"changes happen too fast for anyone to understand the system"* and *"too many alerts for anyone to review one by one"*.

It comprises three core capabilities plus an Agent Triage Layer:
- **§9.0 Agent Triage Layer** — automatic alert triage, false-positive prediction, dedup/merge, and proactive push (read-only).
- **§9.1 Pre-Change Impact Report** — auto-generated before each Freeze/PR.
- **§9.2 Post-Change Verification** — auto-generated after merge.
- **§9.3 AI Knowledge Agent ("The Omniscient")** — cross-environment read-only analysis surface.

The layer reasons over the Code Graph (impact/lineage) and the Knowledge Base (provenance, definitions, playbooks), so it depends heavily on [`code-graph.md`](code-graph.md) and [`knowledge-base.md`](knowledge-base.md).

## Boundaries

**In-scope:**
- Agent Triage Layer: automatic triage, false-positive prediction, dedup & merge, proactive summary push — **all read-only**.
- Pre-Change Impact Report content: What & Why (Diff + KB provenance + BRD linkage), Impact Graph, Data Impact Preview, Test Results + Approval Requirements.
- Post-Change Verification content: Design vs Actual consistency check, updated DAG, Change Log + Related Resources, Cost & Performance Profile.
- AI Knowledge Agent positioning, technical architecture, knowledge sources, capabilities, permission trimming, customization, operational boundary, and temporality constraint.

**Out of scope (delegated):**
- Configuration changes / remediation actions → must go through the **Remediation Gateway** (L0–L3 tiered approval, see §12.2 of [`docs/03-architecture.md`](../../03-architecture.md)). The Agent Triage Layer never writes configuration.
- Persisting AI answers as KB entries → only happens via explicit user confirmation through the Exploration Environment → Freeze Pipeline → Production path (the "solidify" flow).
- The Agent SDK, Skill registry, and MCP plumbing internals → [`agent-platform`](../agent-platform/).

## Interfaces

| Interface | Consumer | Contract |
| --- | --- | --- |
| `change_intelligence.pre_change_report(freeze_or_pr) → report` | Freeze Pipeline, Reviewers | Auto-generated impact report (What & Why, Impact Graph, Data Impact Preview, Test Results + Approval Requirements) |
| `change_intelligence.post_change_verification(merge) → report` | CI/CD, Reviewers | Auto-generated verification (Design vs Actual, updated DAG, Change Log + Related Resources, Cost & Performance Profile) |
| `triage.run(health_check_results) → triaged_summary` | Intelligence Plane (automatic) | Read-only: dedup, merge, false-positive prediction, severity-routed proactive push |
| `agent.query(nl_question, session_context) → answer` | Conversation Interface (Design Plane) | Read-only cross-environment query; RBAC-filtered; output is a "disposable consumable" |

## Dependencies

- **Code Graph** ([`code-graph.md`](code-graph.md)) — the Impact Graph (upstream/downstream/indirect scope) is computed via graph traversal; the updated DAG in Post-Change Verification marks changed nodes.
- **Knowledge Base** ([`knowledge-base.md`](knowledge-base.md)) — KB provenance, BRD/ADR/KB linkages, and Diagnostic Playbooks (domain 8, [ADR-0024](../../../adr/0024-kb-reasoning-support-playbooks-code.md)) feed the "What & Why" and the Agent's reasoning.
- **Log Store** — execution logs (read-only replicas) are a knowledge source for the AI Knowledge Agent.
- **Auth Service** — every Agent query passes through RBAC filters; Dev cannot query Business Data, Business User cannot modify code.
- **Remediation Gateway** (§12.2) — the only path through which triage findings become configuration changes (L0–L3 approval).
- **Data Health Check** — its results are the input to the Agent Triage Layer.
- **Exploration Environment / Freeze Pipeline** — the "solidify" path that turns a disposable Agent answer into a frozen, deterministic Compute Spec.

## Data Model

Change Intelligence is largely stateless and read-mostly; it does not own a primary store. The data it reasons over:

- **Code Graph subgraphs** — impact scope, lineage, changed-node markers (schema in [`code-graph.md`](code-graph.md)).
- **KB entries** — definitions, provenance, playbooks, BRD/ADR/Incident linkages (schema in [`knowledge-base.md`](knowledge-base.md)).
- **Read-only execution logs/metrics** — queried via replicas, never written back.
- **Interaction logs** — tagged as *"AI-assisted exploration"*, distinct from the production decision audit trail (see Temporality Constraint). These are retained for analytics but are **not** audited as production decisions.

The severity routing table that drives the Agent Triage Layer (§9.0):

```
severity=error   → Auto-trigger S07 IncidentDiagnostician (parallel sub-agent diagnosis)
severity=warning → Proactively generate Health Summary push (dedup + pattern matching + confidence prediction)
severity=info    → Log only (no proactive push)
```

## Failure Modes & Recovery

- **Wrong Agent answer (worst case).** Per the §9.3 positioning statement: the AI gives a wrong answer — it **will not pollute data, will not affect Pipelines, and will not be audited as a "production decision."** Output is a disposable consumable returned directly to the user, never written to system state. Recovery is simply that the user discards the answer.
- **Triage false negative / over-merge.** Dedup & merge uses pattern matching + confidence prediction; low-confidence merges are surfaced for human review rather than silently dropped. Original alerts remain queryable.
- **Stale impact graph.** Pre/Post-Change reports depend on the Code Graph's eventual consistency (≤5 s status edges, ≤30 s structural edges per [`code-graph.md`](code-graph.md)); reports generated within the staleness window may slightly lag and are regenerated on merge.
- **RBAC gap.** If the entitlement context is missing, the Agent defaults to deny (no Business Data, no cross-tenant results).

## Non-Functional Requirements

- **Triage effectiveness** (industry data, §9.0): alert volume reduced by **30–40%**, MTTR reduced by **50–70%** (known patterns).
- **Read-only guarantee** — all triage operations are read-only; configuration changes must go through the Remediation Gateway (L0–L3).
- **Cross-environment read-only mode** — the AI Knowledge Agent queries Exploration artifacts (BRD/ADR/Spec), Production execution logs (read-only replicas), and the KB; write operations are intercepted and rejected at the Engine level.
- **Permission trimming** — every query passes through RBAC filters (Dev cannot query Business Data; Business User cannot modify code).
- **Temporality** — AI-generated answers are not persisted as KB entries unless the user explicitly confirms and goes through the Exploration Environment process.

## Key Flows

### §9.0 Agent Triage Layer (Alert Triage & Proactive Push)

Located in the Intelligence Plane; runs automatically **after** Data Health Check results are produced and **before** users see them.

**Core Responsibilities**: automatic triage, false-positive prediction, deduplication & merging, proactive summary push. All operations are read-only — configuration changes must go through the Remediation Gateway (L0–L3 tiered approval, see §12.2).

Severity routing drives downstream action (table in Data Model above). **Dedup & Merge Example** (§9.0): `"Line 3 MoM +15% / Line 5 MoM +12% / Line 12 MoM +18%"` merged into `"ERP batch backfill caused multi-line spikes, consistent with quarter-end pattern"`.

### §9.1 Pre-Change Impact Report (Before Change)

Auto-generated with each Freeze/PR, including:
- **What & Why** (Diff + KB provenance + BRD linkage)
- **Impact Graph** (visualized impact scope: upstream/downstream/indirect)
- **Data Impact Preview** (historical data simulation of old vs new logic differences)
- **Test Results + Approval Requirements**

### §9.2 Post-Change Verification (After Change)

Auto-generated after merge, including:
- **Design vs Actual** (consistency check, detecting deviation)
- **Updated DAG** (mark changed nodes)
- **Change Log + Related Resources** (BRD/ADR/KB/Incident)
- **Cost & Performance Profile**

### §9.3 AI Knowledge Agent — Cross-Environment Read-Only Mode

**Key Positioning Statement** (§9.3): the AI Knowledge Agent operates in **Cross-Environment Read-Only Mode** of the unified Workflow Engine. It queries Exploration artifacts (BRD/ADR/Spec), Production execution logs (read-only replicas), and the KB, but write operations are intercepted and rejected at the Engine level. This upholds the core principle of **"Zero AI Side Effects at Production"**:
- **Cross-environment mode output is a "disposable consumable"**, not a "persistent asset" — answers are returned directly to the user, not written to system state.
- **User wants to solidify analysis results** → go through Exploration Environment → Freeze Pipeline → Production Environment; analysis logic is frozen into a deterministic Compute Spec.
- **Worst case**: AI gives a wrong answer. It will not pollute data, will not affect Pipelines, and will not be audited as a "production decision".

**Typical ad-hoc scenario** (§9.3): User asks *"Why did East China gross margin drop 2 points last month?"* → Cross-Environment Read-Only Mode queries KB + Production logs (read-only replica) → generates attribution analysis → returns explanatory text + charts → user finds it useful → clicks *"Solidify as Weekly Report"* → enters Exploration Environment process.

| Attribute | Specification |
| --- | --- |
| **Belongs to** | Cross-Environment Read-Only Mode (read-only analysis surface), not part of Production execution path. Production Environment may invoke LLMs via `llm_reasoning` Jobs with `read_analyze` or `suggest_plan` capabilities (configurable), but these are governed by Engine-level capability enforcement, not cross-environment mode. |
| **Technical Architecture** | **LLM SDK + Skill + MCP** |
| **Knowledge Sources** | Code Graph + KB + Log Store + Docs (all read-only queries, no write-back) |
| **Capabilities** | Answer factual questions, interrelationships, historical changes, impact analysis, provide suggestions; ad-hoc NL Q&A (attribution analysis, anomaly explanation, definition lineage tracing) |
| **Permission Trimming** | Dev cannot query Business Data; Business User cannot modify code. Every query passes through RBAC filters. |
| **Customization** | Different Teams/Owners predefine multiple sets of Agent Workflows; different users can connect to different AI Models |
| **Operational Boundary** | Agent queries execution state (logs, metrics) via read-only replicas; Agent suggestions are presented through Exploration Environment, and after user confirmation go through Freeze Pipeline — Agent never directly modifies Production configuration or data. |
| **Temporality Constraint** | AI-generated answers are not persisted as KB entries (unless user explicitly confirms and goes through Exploration Environment process); interaction logs are tagged as "AI-assisted exploration" (distinct from production decision audit trail) |

### Shared Sequence Diagram

The end-to-end Agent query flow — including intent parsing, permission-boundary retrieval from the Auth Service, RBAC-filtered Code Graph and KB queries, output guarding, and citation building — is defined in the shared sequence diagram at [`../_shared/sequence-diagrams.md`](../_shared/sequence-diagrams.md), specifically **§21.3 AI Agent Query with Permission Gating**. That diagram is the canonical reference for the participant flow (`USER → CONV → AGENT → AUTH/CG/KB_VEC/KB_REL/LOG → GUARD → CITATION → USER`) and should be consulted for implementation rather than duplicating the sequence here.

## Design References

- **§9 Change Intelligence & Agent Triage** — [`docs/03-architecture.md`](../../03-architecture.md) (lines 1114–1165): the canonical source for §9.0 Agent Triage Layer, §9.1 Pre-Change Impact Report, §9.2 Post-Change Verification, and §9.3 AI Knowledge Agent.
- **§12.2 Remediation Gateway** — [`docs/03-architecture.md`](../../03-architecture.md): L0–L3 tiered approval, the only path from triage findings to configuration changes.
- **§3 Unified Workflow Engine** — [`docs/03-architecture.md`](../../03-architecture.md): Cross-Environment Read-Only Mode and Engine-level capability enforcement (`read_analyze`, `suggest_plan`).
- Shared sequence diagram **§21.3 AI Agent Query with Permission Gating** — [`../_shared/sequence-diagrams.md`](../_shared/sequence-diagrams.md).
- Cross-references: [`code-graph.md`](code-graph.md) (Impact Graph, updated DAG), [`knowledge-base.md`](knowledge-base.md) (provenance, BRD/ADR linkage, Diagnostic Playbooks).
- Glossary: [`../../glossary.md`](../../glossary.md).
