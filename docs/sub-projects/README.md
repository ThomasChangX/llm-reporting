# Sub-Projects — Detailed Module Design

> **Parent**: [`docs/03-architecture.md`](../03-architecture.md) (slimmed overview + §N anchor stubs)
> **Scope**: Per-module deep-dive design, migrated from the original monolithic `03-architecture.md` (6412 lines) into focused, maintainable files.

This directory decomposes the llm-reporting platform into **seven sub-projects**, each a cohesive domain with its own deployment surface, team boundary, and module set. The decomposition follows three signals from the design itself:

1. **ADR-0025** — the Workflow Engine is *one* engine across three environments; sub-projects split by domain, not by environment.
2. **§2 Panoramic Architecture** — four coarse zones (Engine / KB / Code Graph / Cross-Cutting) define the natural domain boundaries.
3. **§17.2 Workload Placement Table** — deployable, independently-scalable service units define the deployment boundaries.

---

## Sub-Project Map

| # | Sub-Project | Purpose | Key ADRs | Origin Sections |
|---|-------------|---------|----------|-----------------|
| 1 | [`workflow-engine/`](workflow-engine/) | Unified engine: Compute Spec, DAG execution, Sandbox, Freeze Pipeline | ADR-0025, ADR-0011 | §3, §4, §6, §7 |
| 2 | [`agent-platform/`](agent-platform/) | Agent SDK, Skills, MCP servers, memory, governance, evaluation | ADR-0016–0021, ADR-0024 | §22A–§22M, §3.1–§3.5 |
| 3 | [`knowledge-services/`](knowledge-services/) | Knowledge Base (9 domains), Code Graph, CDC pipeline, Change Intelligence | ADR-0013, ADR-0023, ADR-0024 | §2.1, §9, §10, §20 |
| 4 | [`query-serving/`](query-serving/) | Query Service, large-scale data architecture, resilience | ADR-0007, ADR-0008 | §5.1–§5.4 |
| 5 | [`data-health/`](data-health/) | Data quality, reconciliation, anomaly detection, remediation gateway | ADR-0014, ADR-0015 | §12.2 |
| 6 | [`brd-adr-lifecycle/`](brd-adr-lifecycle/) | BRD/ADR as first-class entities, AI generation pipeline, traceability | ADR-0010, ADR-0022 | §23 |
| 7 | [`platform-core/`](platform-core/) | Auth, entitlement, tenant isolation, audit, observability, ops, compliance | — | §8, §11, §12.1, §12.3–§12.7, §24, §25 |

---

## Dependency Graph

```
                    ┌─────────────────────────┐
                    │      platform-core       │  ← every sub-project depends on this
                    │  (auth · RBAC · audit ·  │
                    │   tenant · obs · ops)    │
                    └───────────┬─────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌───────▼──────┐       ┌────────▼────────┐      ┌──────▼───────┐
│  workflow-   │       │  knowledge-     │      │   query-     │
│  engine      │◀─────▶│  services       │◀────▶│   serving    │
│ (engine core)│       │ (KB · graph ·   │      │ (query svc)  │
└───────┬──────┘       │  CDC)           │      └──────────────┘
        │              └────────┬────────┘
        │                       │
┌───────▼──────┐       ┌────────▼────────┐
│   agent-     │       │   data-health   │
│   platform   │──────▶│   (DQ · recon)  │
│ (SDK · MCP)  │       └─────────────────┘
└───────┬──────┘
        │
┌───────▼──────┐
│  brd-adr-    │
│  lifecycle   │  (uses agent-platform for generation pipeline)
└──────────────┘
```

**Key dependency rules:**
- `platform-core` is the foundation — all others depend on it (never the reverse).
- `workflow-engine` and `knowledge-services` are peers; both are consumed by `agent-platform` and `query-serving`.
- `agent-platform` depends on `workflow-engine` (executes Compute Specs) and `knowledge-services` (retrieves KB context).
- `brd-adr-lifecycle` depends on `agent-platform` (its 8-agent generation pipeline) and `workflow-engine` (BRD/ADR as Compute Spec types).
- `data-health` depends on `knowledge-services` (writes results to KB) and `agent-platform` (Agent Triage).

---

## How to Read

**First-time readers**: Start with [`../01-facts.md`](../01-facts.md) → [`../02-requirement.md`](../02-requirement.md) → [`../03-architecture.md`](../03-architecture.md) §1–§2 (philosophy + panoramic overview), then dive into the sub-project README that matches your interest.

**Each sub-project README** provides:
- **Positioning** — what this sub-project is and why it exists as a separate unit
- **Boundaries** — what's in-scope vs. delegated to other sub-projects
- **Module list** — table of all modules with their origin §N anchors
- **External interface contract** — what this sub-project exposes to others
- **Related ADRs** — decisions that shaped this sub-project

**Each module doc** follows a consistent 9-section template: Purpose → Boundaries → Interfaces → Dependencies → Data Model → Failure Modes & Recovery → Non-Functional Requirements → Key Flows → Design References.

---

## Relationship to `03-architecture.md`

The original `03-architecture.md` is **not deleted** — it is slimmed to an overview document retaining:
- §1 (Core Design Philosophy), §2 (Panoramic Architecture)
- §13 (Technology Selection), §14 (Design Principles Checklist), §17 (Deployment Architecture)
- **Stub headings** for every migrated section (e.g., `## 22A. Agent SDK Architecture → migrated to agent-platform/`)

These stubs preserve the `§N` anchor contract: ADRs and `01-facts.md` cite sections like `§22A`; the checker (`scripts/check_adr_semantics.py`) validates these against `03-architecture.md` headings. The stubs keep all citations resolving correctly while the detailed content lives in these sub-project files.

---

## Migration Provenance

| Migrated from | Lines (original) | To sub-project |
|---------------|------------------|----------------|
| §3 (Exploration Environment) | 121–258 | agent-platform (`exploration-runtime.md`) + workflow-engine (`design-artifact.md`) |
| §4 (Freeze Pipeline) | 259–403 | workflow-engine (`freeze-pipeline.md`) |
| §5.1–§5.4 (Production: Query + Large-Scale) | 404–942 | query-serving |
| §6 (Compute Spec) | 943–1025 | workflow-engine (`compute-spec.md`) |
| §7 (Execution Sandbox) | 1026–1086 | workflow-engine (`execution-sandbox.md`) |
| §8 (Log System) | 1087–1113 | platform-core (`observability.md`) |
| §9 (Change Intelligence) | 1114–1165 | knowledge-services (`change-intelligence.md`) |
| §10 (Knowledge Base) | 1166–1334 | knowledge-services (`knowledge-base.md`) |
| §11 (Cross-Cutting Layer) | 1335–1391 | platform-core (`cross-cutting-layer.md`) |
| §12 (Domain Components) | 1392–1823 | data-health + platform-core (`domain-services.md`) |
| §20 (CDC Pipeline) | 2208–2413 | knowledge-services (`cdc-pipeline.md`) |
| §21 (Sequence Diagrams) | 2414–2773 | distributed (cross-referenced by relevant modules) |
| §22A–§22M (Agent Deep Design) | 2806–4769 | agent-platform (8 files) |
| §23 (BRD & ADR) | 4770–6257 | brd-adr-lifecycle (8 files) |
| §24 (Operational Architecture) | 6258–6344 | platform-core (`operational-architecture.md`) |
| §25 (Compliance Architecture) | 6345–6412 | platform-core (`compliance-architecture.md`) |
