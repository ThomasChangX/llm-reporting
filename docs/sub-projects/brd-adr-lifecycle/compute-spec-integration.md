# BRD/ADR as Compute Spec Types

> **Origin**: §23.7 of [`docs/03-architecture.md`](../../03-architecture.md) | **Sub-project**: [brd-adr-lifecycle](README.md)

## Purpose

Both BRD and ADR are modeled as **specialized types of Compute Spec** (just as Agent Workflow is a meta-workflow type). By carrying `spec_type: brd` or `spec_type: adr`, they inherit the entire Compute Spec infrastructure stack — Git versioning, branch strategy, PR review, CI/CD validation, Code Graph integration, RBAC, audit trail, change intelligence, data lineage, export, notifications, and tenant isolation — at zero additional cost.

This module specifies the **inherited capability matrix** (§23.7.1) and the **CI/CD validation pipeline** (§23.7.2) that adapts the base Compute Spec pipeline to BRD/ADR-specific checks (compliance lint for BRDs, fitness functions for ADRs).

This is the realization of **ADR-0010** "BRD and ADR as Compute Spec Subtypes" (see [Design References](#design-references)).

## Boundaries

**In-scope:**
- The capability inheritance contract between Compute Spec (base) and BRD/ADR (subtypes) — §23.7.1.
- The 6-stage BRD/ADR CI/CD validation pipeline and its stage-specific rules — §23.7.2:
  1. Schema Validation
  2. Reference Integrity
  3. Traceability Lint
  4. Compliance Mapping (BRD only)
  5. Fitness Function (ADR only)
  6. Impact Report Generation (PR events only)

**Out of scope (delegated):**
- Compute Spec base infrastructure (Git storage, branch/freeze model, RBAC engine, audit logging) → [`workflow-engine`](../workflow-engine/) and platform services.
- BRD/ADR YAML schema definitions → [`brd-entity-model.md`](brd-entity-model.md), [`adr-entity-model.md`](adr-entity-model.md).
- BRD/ADR lifecycle state transitions driven by CI outcomes → [`lifecycle-state-machine.md`](lifecycle-state-machine.md).
- Code Graph node/edge storage backing reference integrity checks → [`knowledge-services`](../knowledge-services/).

## Interfaces

| Interface | Consumer | Contract |
|-----------|----------|----------|
| `brd.validate(brd_yaml) → validation_report` | CI/CD pipeline (§23.7.2), Workbench | Runs stages 1–4 (+6 on PR); returns structured report of schema/reference/traceability/compliance findings |
| `adr.validate(adr_yaml) → validation_report` | CI/CD pipeline (§23.7.2), Workbench | Runs stages 1–3, 5 (+6 on PR); returns schema/reference/traceability/fitness findings |
| `spec.commit(spec_yaml) → frozen_spec` (inherited) | Generation pipeline, human reviewers | Same freeze/branch/PR semantics as any Compute Spec |
| CI stage gates → lifecycle state machine | Lifecycle State Machine | A failing compliance/fitness stage blocks promotion to `approved`/`accepted` |

## Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| **Compute Spec base infrastructure** | Hard (inherited) | Git versioning (FR8.1), branch strategy (feature → freeze → main), PR review (FR8.2), RBAC (FR9), audit (FR10.1), notifications (FR37), tenant isolation. BRD/ADR get all of this by being Compute Spec subtypes. |
| **CI/CD Validation framework** (FR20.1) | Hard | The base pipeline runner that this module specializes with BRD/ADR stages. |
| **Code Graph** | Hard | Reference Integrity and Traceability Lint stages query the graph for linked Workflows/ADRs/components. |
| **compliance-mapper (MCP-22)** | Soft | Compliance Mapping stage (4) may consult MCP-22 framework libraries for cross-checks; see [external-integration.md](external-integration.md). |
| **Change Intelligence (FR28)** | Hard | Change-triggered change intelligence is inherited; the Impact Report stage (6) is its CI surface. |
| **S17 TraceabilityAnalyzer** | Soft | Provides the coverage data the Traceability Lint stage (3) enforces. |

## Data Model

### §23.7.1 Inherited Capability Matrix

Both BRD and ADR inherit all infrastructure capabilities of Compute Spec. The matrix below shows what each spec type receives:

| Capability                               | Compute Spec Base | BRD (`spec_type: brd`) | ADR (`spec_type: adr`) | Agent Workflow |
| ---------------------------------------- | :---------------: | :--------------------: | :--------------------: | :------------: |
| **Git Versioning** (FR8.1)               |         ✅         |           ✅            |           ✅            |       ✅        |
| **Branch Strategy** (feature → freeze → main) |         ✅         |           ✅            |           ✅            |       ✅        |
| **PR Review Workflow** (FR8.2)           |         ✅         | ✅ (stakeholder review) |    ✅ (arch. review)    |       ✅        |
| **CI/CD Validation** (FR20.1)            |         ✅         |  ✅ (compliance lint)   |  ✅ (fitness function)  |       ✅        |
| **Code Graph Nodes + Edges**             |         ✅         |           ✅            |           ✅            |       ✅        |
| **RBAC Access Control** (FR9)            |         ✅         |           ✅            |           ✅            |       ✅        |
| **Full Audit Trail** (FR10.1)            |         ✅         |           ✅            |           ✅            |       ✅        |
| **Change-Triggered Change Intelligence** |         ✅         |        ✅ (FR28)        |        ✅ (FR28)        |       ✅        |
| **Data Lineage Tracking**                | ✅ (Workflow DAG)  |  ✅ (BRD → WF → Code)   |  ✅ (ADR → Component)   |       ✅        |
| **Export Capability** (FR5.5)            |   ✅ (YAML/JSON)   |  ✅ (+ PDF/Confluence)  |  ✅ (+ PDF/Confluence)  |       ✅        |
| **Notification System Integration** (FR37) |         ✅         |           ✅            |           ✅            |       ✅        |
| **Tenant Isolation**                     |         ✅         |           ✅            |           ✅            |       ✅        |

Key specializations worth highlighting:
- **PR Review Workflow** differs by type: BRDs go through *stakeholder review*; ADRs go through *architecture review*.
- **CI/CD Validation** specializes into *compliance lint* for BRDs and *fitness functions* for ADRs (see pipeline below).
- **Data Lineage Tracking** follows each type's natural chain: BRD → Workflow → Code; ADR → Component.
- **Export Capability** extends the base YAML/JSON export with PDF and Confluence rendering (via [MCP-21 confluence-export](external-integration.md)).

## Failure Modes & Recovery

| Failure Mode | Detection | Recovery |
|--------------|-----------|----------|
| **Schema Validation failure** (stage 1) — missing required field, malformed YAML, duplicate ID. | CI build fails at stage 1 with field-level errors. | Author corrects YAML in the feature branch; re-push. |
| **Reference Integrity failure** (stage 2) — `linked_workflows`, `linked_ADRs`, or `linked_kb_entries` point at non-existent entities. | CI build fails at stage 2 listing each dangling reference. | Create the missing target entity first, or correct the ID; re-push. |
| **Traceability Lint failure** (stage 3) — BRD requirements lack a linked Workflow/ADR, or ADR options lack pros/cons analysis. | CI build fails at stage 3 with coverage gaps. | Complete the traceability edges / decision analysis; re-push. |
| **Compliance Mapping failure** (stage 4, BRD only) — `linked_compliance` inconsistent with requirements, or required compliance items missing. | CI build fails at stage 4. | Align compliance mapping (consult MCP-22); re-push. |
| **Fitness Function failure** (stage 5, ADR only) — new code violates an accepted ADR decision (ArchUnit-like check). | CI build fails at stage 5 identifying the violating code and the ADR it contradicts. | Either change the code to comply, or formally supersede the ADR (new ADR `SUPERSEDES` old); cannot silently violate. |
| **Impact Report generation failure** (stage 6, PR only) — underlying Code Graph / Change Intelligence temporarily unavailable. | Non-blocking (report-only); PR proceeds with a warning and a re-run trigger. | Re-trigger impact analysis once dependencies recover. |
| **Inherited infrastructure failure** (e.g., Git, RBAC, audit). | Surfaced by the Compute Spec base platform. | Delegated to platform recovery procedures (out of scope for this module). |

## Non-Functional Requirements

| NFR | Target | Rationale |
|-----|--------|-----------|
| CI pipeline total runtime | Fast feedback for authors | Stages run sequentially; schema/reference/traceability are lightweight, compliance/fitness may invoke external services (MCP-22). |
| Stage isolation | Each stage fails independently and reports its own diagnostics | Authors must know *which* check failed without re-running the whole pipeline mentally. |
| Idempotency | Re-pushing the same YAML yields the same verdict | Deterministic lint/fitness checks; no flaky compliance lookups (cache MCP-22 framework library). |
| Auditability | Every CI verdict (pass/fail) recorded (FR10.1) | Compliance evidence: which BRD passed which compliance check at which commit. |
| Tenant isolation | All checks scoped to the spec's `tenant_id` | Inherited from Compute Spec base; no cross-tenant reference resolution. |
| Immutability of accepted ADRs | Fitness functions (stage 5) enforce, never mutate, accepted ADRs | Per ADR-0011: accepted ADRs are immutable; only supersession can change the active decision. |

## Key Flows

### §23.7.2 CI/CD Validation Pipeline

```
                    ┌─────────────────────────────────┐
                    │   BRD/ADR CI/CD Pipeline         │
                    │                                  │
  Git Push ────────►│  ┌───────────────────────────┐  │
                    │  │ 1. Schema Validation       │  │
                    │  │    • YAML structure validation  │  │
                    │  │    • Required field completeness check │  │
                    │  │    • ID uniqueness verification │  │
                    │  └─────────────┬─────────────┘  │
                    │                ▼                 │
                    │  ┌───────────────────────────┐  │
                    │  │ 2. Reference Integrity     │  │
                    │  │    • linked_workflows exist? │  │
                    │  │    • linked_ADRs exist?      │  │
                    │  │    • linked_kb_entries valid?│  │
                    │  └─────────────┬─────────────┘  │
                    │                ▼                 │
                    │  ┌───────────────────────────┐  │
                    │  │ 3. Traceability Lint       │  │
                    │  │    • Do all BRD requirements │  │
                    │  │      have linked Workflow/ADR? │  │
                    │  │    • Do all ADR options      │  │
                    │  │      have pros/cons analysis? │  │
                    │  └─────────────┬─────────────┘  │
                    │                ▼                 │
                    │  ┌───────────────────────────┐  │
                    │  │ 4. Compliance Mapping      │  │
                    │  │    (BRD only)               │  │
                    │  │    • Are linked_compliance   │  │
                    │  │      consistent with requirements? │  │
                    │  │    • Are required compliance items missing? │  │
                    │  └─────────────┬─────────────┘  │
                    │                ▼                 │
                    │  ┌───────────────────────────┐  │
                    │  │ 5. Fitness Function        │  │
                    │  │    (ADR only)               │  │
                    │  │    • Verify decisions are still being adhered to │  │
                    │  │    • Check for new code that │  │
                    │  │      violates decisions (ArchUnit-like) │  │
                    │  └─────────────┬─────────────┘  │
                    │                ▼                 │
                    │  ┌───────────────────────────┐  │
                    │  │ 6. Impact Report Generation │  │
                    │  │    (PR events only)         │  │
                    │  │    • Pre-Change Impact      │  │
                    │  └───────────────────────────┘  │
                    │                                  │
                    └─────────────────────────────────┘
```

Stage semantics:

1. **Schema Validation** — structural correctness of the YAML itself (FR8.1 baseline). Confirms the BRD/ADR conforms to its schema, required fields are present, and IDs are unique within the tenant. Runs for every spec type.
2. **Reference Integrity** — every cross-reference resolves. `linked_workflows`, `linked_ADRs`, and `linked_kb_entries` must point at entities that actually exist in the Code Graph / KB store. This is the guard against orphaned traceability edges.
3. **Traceability Lint** — the completeness gate. For BRDs: every requirement must have a linked Workflow/ADR. For ADRs: every option must carry pros/cons analysis. This stage directly enforces the [Traceability Web](traceability-web.md) coverage contract.
4. **Compliance Mapping (BRD only)** — verifies `linked_compliance` is consistent with the requirements and that no mandatory compliance items are missing. The authoritative framework library lives in [compliance-mapper (MCP-22)](external-integration.md).
5. **Fitness Function (ADR only)** — ArchUnit-like enforcement: verifies accepted decisions are still being adhered to and flags new code that violates them. This is what keeps ADRs from rotting silently.
6. **Impact Report Generation (PR events only)** — produces a Pre-Change Impact report (Change Intelligence / FR28 surface). Report-only; does not block.

### Lifecycle coupling

CI outcomes feed the lifecycle state machines: a clean BRD pipeline is a prerequisite for the stakeholder-review gate that promotes a BRD to `approved`; a clean ADR pipeline (notably stage 5) is a prerequisite for architecture review promoting an ADR from `in_discussion` to `accepted`. See [`lifecycle-state-machine.md`](lifecycle-state-machine.md).

## Design References

- **§23.7** of [`docs/03-architecture.md`](../../03-architecture.md) — source section for this module.
- **ADR-0010** "BRD and ADR as Compute Spec Subtypes" ([`../../../adr/0010-brd-adr-first-class.md`](../../../adr/0010-brd-adr-first-class.md)) — the decision that BRDs/ADRs are Compute Spec subtypes stored in Git with full relationship edges, enjoying the same infrastructure as Workflows. Consequence: BRD/ADR YAML schema becomes part of the system contract; CI/CD needs BRD/ADR-specific lint rules; Code Graph needs BRD/ADR node + edge types.
- [`README.md`](README.md) — sub-project overview.
- [`brd-entity-model.md`](brd-entity-model.md) / [`adr-entity-model.md`](adr-entity-model.md) — the schemas that stages 1–2 validate.
- [`traceability-web.md`](traceability-web.md) — the edge catalog that stage 3 enforces.
- [`lifecycle-state-machine.md`](lifecycle-state-machine.md) — consumes CI verdicts as promotion gates.
- [`external-integration.md`](external-integration.md) — MCP-22 compliance framework library used by stage 4; MCP-21 export referenced by the Export Capability row.
