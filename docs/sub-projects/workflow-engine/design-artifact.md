# Design Artifact Schema

> **Origin**: §3.3 of [`docs/03-architecture.md`](../../03-architecture.md) | **Sub-project**: [workflow-engine](README.md)

## Purpose

This module covers the **Design Artifact Schema** — the formal handoff contract between the Design Plane and the Freeze Bridge. Per §3.3, the Design Plane produces a **Design Artifact** (YAML) that captures both the intended specification and the AI's uncertainty about each element. It is the structure the Freeze Pipeline (§4) scans for `fuzzy_nodes` and `llm_reasoning` Jobs, and the structure the Freeze Bridge rejects if any fuzzy node remains unresolved.

The Design Artifact is the boundary object that makes "the Assistant flags and proposes; the human decides" enforceable: every AI-generated uncertainty is materialized as a typed `fuzzy_node` with a marker, a confidence score, and an optional `proposed_resolution`, and every human confirmation is materialized as a `confirmed_field`.

## Boundaries

**In-scope:**
- §3.3 Design Artifact Schema (Handoff Contract) — the YAML structure produced by the Design Plane and consumed by the Freeze Bridge.
- The `artifact` block (`id`, `workflow_ref`, `created_by`, `status`: `draft` | `user_reviewed` | `frozen`).
- The `spec` block (the full Compute Spec of §6, embedded by reference).
- The `fuzzy_nodes` list — each entry carries `path`, `marker`, `description`, `confidence`, `proposed_resolution`, `user_confirmed`.
- The `confirmed_fields` list — nodes explicitly confirmed by a human user.
- The `confidence_summary` block — `overall`, `fully_confirmed_nodes`, `fuzzy_nodes`, `unresolved_nodes`.
- The field-purpose semantics: `fuzzy_nodes` (rejected if unresolved), `confirmed_fields` (authoritative, skip AI re-evaluation), `confidence_summary` (`overall < 0.8` mandates full peer review).

**Delegated / out-of-scope:**
- The Compute Spec embedded under `spec.workflow` → [`compute-spec.md`](compute-spec.md) (§6).
- The `freeze()` operation that consumes the artifact and resolves its fuzzy nodes → [`freeze-pipeline.md`](freeze-pipeline.md) (§4).
- The Sandbox and validation scans applied to the artifact's Python/SQL → [`execution-sandbox.md`](execution-sandbox.md) (§7).
- The Design Plane NL→Spec authoring UX that produces the artifact → not owned by `workflow-engine`.

**Upstream/downstream neighbors:**
- *Producer*: Design Plane (user + copilot) emits the artifact in `draft` status.
- *Consumer*: Freeze Bridge — scans `fuzzy_nodes` + `llm_reasoning` Jobs, requires all `user_confirmed == true`, advances status to `frozen`.

## Interfaces

### §3.3 Design Artifact — YAML contract

The Design Plane produces a **Design Artifact** (YAML) that serves as the formal contract between Design Plane and Freeze Bridge. It captures both the intended specification and the AI's uncertainty about each element.

```yaml
# Design Artifact — Handoff Contract
artifact:
  id: "da_20260704_001"
  workflow_ref: "monthly_revenue_report"
  created_by: "user:alice / copilot:v3.2"
  status: draft  # draft | user_reviewed | frozen

spec:
  workflow:
    name: "Monthly Revenue Report"
    # ... full Compute Spec (Section 6) ...

fuzzy_nodes:
  - path: "jobs.transform_revenue.op[2]"
    marker: "AMBIGUOUS_FILTER"
    description: "Filter condition 'large accounts' needs definition"
    confidence: 0.45
    proposed_resolution: "WHERE account.balance > 1000000"
    user_confirmed: false

  - path: "jobs.join_crm.source.table"
    marker: "UNRESOLVED_REFERENCE"
    description: "Table 'crm_prod.accounts' not found in Data Catalog"
    confidence: 0.0
    proposed_resolution: null
    user_confirmed: false

confirmed_fields:
  - path: "jobs.source_revenue"
    confirmed_by: "user:alice"
    confirmed_at: "2026-07-04T10:30:00Z"

confidence_summary:
  overall: 0.72
  fully_confirmed_nodes: 8
  fuzzy_nodes: 2
  unresolved_nodes: 1
```

### §3.3 Field purpose

| Field                | Purpose                                                                                                                                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `fuzzy_nodes`        | Nodes the AI could not deterministically resolve. Each carries a `marker` type, `confidence` score, and optional `proposed_resolution`. Freeze Bridge rejects any artifact with unresolved fuzzy nodes. |
| `confirmed_fields`   | Nodes explicitly confirmed by a human user. Freeze Bridge treats these as authoritative, skipping AI re-evaluation.                                                                                     |
| `confidence_summary` | Aggregate scores used by Freeze Bridge to decide required review depth. Artifacts with `overall < 0.8` mandate full peer review.                                                                        |

## Dependencies

- **`spec.workflow`**: embeds the full Compute Spec (§6) — Variables, Parameters, Formats, Job Groups, Jobs (10 Job Types), `depends_on`, `trigger_rule`. Validated by the Compute Spec schema.
- **`fuzzy_nodes[].marker`**: typed per the fuzzy-node classification in §4.3.1 — `AMBIGUOUS_FILTER`, `UNRESOLVED_REFERENCE`, `UNCERTAIN_FORMULA`, `MISSING_THRESHOLD`, `MISSING_OR_AMBIGUOUS_SOURCE`, `IMPLICIT_JOIN`, `AMBIGUOUS_AGGREGATION`, `INFERRED_BUSINESS_LOGIC`.
- **`fuzzy_nodes[].proposed_resolution`**: generated by the Spec Refinement Assistant (§4.1 Step 2) using KB Business Glossary + Code Graph + Data Catalog fuzzy-search.
- **`confirmed_fields[].confirmed_by`**: a human user identity (validated by [`platform-core`](../platform-core/) auth).
- **`confidence_summary.overall`**: drives Freeze Bridge review-depth gating (`< 0.8` → full peer review).
- **Freeze Bridge** ([`freeze-pipeline.md`](freeze-pipeline.md) §4): the consumer that enforces "all `fuzzy_nodes.user_confirmed == true`" before proceeding (step 4 of §21.1).
- Cross-sub-project: [`knowledge-services`](../knowledge-services/) (Data Catalog, Business Glossary, Code Graph feed the proposals), [`platform-core`](../platform-core/) (auth for `confirmed_by`, Audit Trail for the immutable record), [`agent-platform`](../agent-platform/) (LLM-assisted proposals via MCP).

## Data Model

- **`artifact`** — top-level envelope.
  - `id` — artifact identifier (e.g., `da_20260704_001`).
  - `workflow_ref` — reference to the target Workflow (e.g., `monthly_revenue_report`).
  - `created_by` — producer identity, format `user:<id> / copilot:<version>` (e.g., `user:alice / copilot:v3.2`).
  - `status` — lifecycle: `draft` | `user_reviewed` | `frozen`. Advanced to `frozen` only by the Freeze Bridge.
- **`spec.workflow`** — the embedded Compute Spec (§6); `name` plus the full Job/Group/Variable/Parameter/Format definition.
- **`fuzzy_nodes[]`** — one per AI-unresolvable node.
  - `path` — JSON-pointer-like path into the spec (e.g., `jobs.transform_revenue.op[2]`, `jobs.join_crm.source.table`).
  - `marker` — typed fuzzy-node marker (see §4.3.1 classification).
  - `description` — human-readable explanation of the uncertainty.
  - `confidence` — AI confidence in the node (`0.0`–`1.0`); `0.0` means fully unresolved.
  - `proposed_resolution` — optional deterministic proposal (`null` when none available).
  - `user_confirmed` — boolean; **must be `true` for Freeze Bridge to proceed**.
- **`confirmed_fields[]`** — one per human-confirmed node.
  - `path` — spec path.
  - `confirmed_by` — human user identity.
  - `confirmed_at` — ISO-8601 timestamp.
- **`confidence_summary`** — aggregate scoring.
  - `overall` — aggregate confidence (`< 0.8` mandates full peer review).
  - `fully_confirmed_nodes` — count of human-confirmed nodes.
  - `fuzzy_nodes` — count of fuzzy nodes.
  - `unresolved_nodes` — count of fuzzy nodes with no resolution.

## Failure Modes & Recovery

| Failure | Impact | Recovery |
| --- | --- | --- |
| Artifact submitted with any `fuzzy_nodes[].user_confirmed == false` | Freeze Bridge cannot proceed | Freeze Bridge rejects the artifact (step 4 of §21.1: requires `all fuzzy_nodes.user_confirmed == true`). User must resolve each via the Spec Refinement Assistant (§4.1 Step 4 — Mandatory). |
| `fuzzy_nodes[].proposed_resolution == null` (e.g., `UNRESOLVED_REFERENCE`, confidence `0.0`) | No AI proposal available | Spec Refinement Assistant generates 1–3 proposals via KB fuzzy-search; if none viable, user provides custom resolution or escalates to Data Owner (§4.3.3 Manual Override). |
| `confidence_summary.overall < 0.8` | Insufficient review depth | Mandates full peer review before the artifact can be frozen. |
| `confirmed_fields` conflicts with downstream `fuzzy_nodes` | Ambiguous authority | `confirmed_fields` are authoritative — Freeze Bridge skips AI re-evaluation for them. Conflicts surface via the §4.3.3 Conflict Resolution Rule. |
| `status` advanced prematurely (e.g., `frozen` without sign-off) | Invalid lifecycle transition | Status transitions are gated by the Freeze Bridge; only `freeze()` advances to `frozen`, and only after all gates pass. |
| Canary rollback after freeze | Frozen artifact invalidated | Per §4.2 Rollback Mechanism, the frozen artifact is returned to `draft` status with failed canary results attached. |

## Non-Functional Requirements

### §3.3 Contract enforcement — quantitative gates

- **Fuzzy-node resolution**: `100%` of `fuzzy_nodes` must have `user_confirmed == true` before Freeze Bridge proceeds (hard gate).
- **Peer-review threshold**: `confidence_summary.overall < 0.8` mandates full peer review.
- **Immutability**: every resolution (who, when, which proposal, edits, final Spec fragment) is recorded immutably and linked to the Audit Trail (per §4.1 Step 5 / §4.1b Step 4).
- **`confirmed_fields` authority**: Freeze Bridge treats `confirmed_fields` as authoritative, skipping AI re-evaluation (zero re-check cost).
- **`unresolved_nodes` accounting**: every fuzzy node with no resolution is counted in `confidence_summary.unresolved_nodes` and surfaced for mandatory human resolution.

## Key Flows

### §3.3 Artifact lifecycle — draft → user_reviewed → frozen

```
Design Plane (user + copilot)
    │
    ▼
┌─────────────────────────────────────────────┐
│ 1. Emit Design Artifact (status: draft)       │
│    • spec.workflow = full Compute Spec (§6)   │
│    • fuzzy_nodes[] = AI uncertainties         │
│      (marker, confidence, proposed_resolution,│
│       user_confirmed: false)                  │
│    • confirmed_fields[] = human sign-offs     │
│    • confidence_summary                       │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│ 2. Spec Refinement Assistant (§4.1)           │
│    • Scan fuzzy_nodes + llm_reasoning Jobs    │
│    • Propose 1–3 deterministic options each   │
│    • User decides (accept / edit / custom /   │
│      escalate) — Mandatory                    │
│    • Record immutably → Audit Trail           │
│    • Set fuzzy_nodes[].user_confirmed = true  │
└──────────────────────┬──────────────────────┘
                       │ status → user_reviewed
                       ▼
┌─────────────────────────────────────────────┐
│ 3. Freeze Bridge (§4)                          │
│    Gate: all fuzzy_nodes.user_confirmed ==    │
│           true AND (overall >= 0.8 OR full    │
│           peer review completed)              │
│    • Validation Engine (schema/DQ/logic/AST)  │
│    • Test Runner (Sandbox, 5% sample)         │
│    • Impact Report → PR → Review              │
│    • Canary 1% → 10% → 50% → 100%             │
└──────────────────────┬──────────────────────┘
                       │ status → frozen
                       ▼
                 Frozen Workflow Definition
                 (deployed to Production)
```

### Shared runtime sequence

The Design Artifact is the input to the entire freeze-side sequence. Its `fuzzy_nodes` are scanned at step 5–7, resolved at step 9–12, validated at step 13–16, and dry-run at step 17–20 of [`../_shared/sequence-diagrams.md`](../_shared/sequence-diagrams.md) **§21.1 Freeze Flow: Full End-to-End**. The artifact's `confidence_summary.overall` drives the review-depth gating referenced throughout that sequence.

## Design References

- **Original section**: §3.3 (Design Artifact Schema — Handoff Contract) of [`docs/03-architecture.md`](../../03-architecture.md).
- **Related workflow-engine docs**: [`compute-spec.md`](compute-spec.md) (§6 — the `spec.workflow` embedded in the artifact), [`freeze-pipeline.md`](freeze-pipeline.md) (§4 — the consumer that resolves `fuzzy_nodes` and advances `status`), [`execution-sandbox.md`](execution-sandbox.md) (§7 — scans applied to the artifact's Python/SQL).
- **Shared sequence diagram**: [`../_shared/sequence-diagrams.md`](../_shared/sequence-diagrams.md) §21.1 Freeze Flow: Full End-to-End (the artifact is the input; fuzzy nodes scanned/resolved at steps 5–12).
- **ADRs** ([index](../../adr-index.md)): [ADR-0025 Unified Workflow Engine](../../../adr/0025-unified-workflow-engine.md) (the artifact is the handoff between engine environments), [ADR-0006 Freeze Bridge Independence](../../../adr/0006-freeze-bridge-independence.md) (the freeze gate that enforces artifact resolution), [ADR-0005 Four-Layer Architecture](../../../adr/0005-four-layer-architecture.md) (Zero AI Side Effects — the artifact materializes AI uncertainty for human sign-off).
- **Glossary** ([../../glossary.md](../../glossary.md)): Design Artifact, Handoff Contract, Fuzzy Node, `confirmed_fields`, `confidence_summary`, Freeze Bridge, Spec Refinement Assistant.
- **Cross-references retained from source**: §6 (the full Compute Spec embedded under `spec.workflow`); §4.3.1 (the `marker` classification used by `fuzzy_nodes`); §4.1 / §4.1b (the resolution loops that set `user_confirmed`).
