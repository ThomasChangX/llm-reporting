# workflow-engine — Unified Workflow Engine

> **Origin**: §3, §4, §6, §7 of `docs/03-architecture.md`
> **Key ADRs**: [ADR-0025](../../adr/0025-unified-workflow-engine.md) (Unified Engine), [ADR-0011](../../adr/0011-materialize-job-type.md) (Materialize Job Type)

## Positioning

The **Unified Workflow Engine** is the system's beating heart. Per ADR-0025, it is *one* engine operating across three environments (Exploration, Freeze Pipeline, Production) plus a cross-environment read-only mode — not four separate planes. The same Compute Spec YAML executes in any environment; only the environment's configuration determines which capabilities are active.

This sub-project owns: the engine itself, its Compute Spec language, its execution sandbox, and the Freeze Pipeline (a built-in engine operation, not a separate service).

## Boundaries

**In-scope:**
- Compute Spec definition, parsing, validation (10 Job Types)
- DAG construction and dependency-trigger evaluation
- Execution Sandbox (per-Job isolation: CPU/memory/disk/network + seccomp)
- Freeze Pipeline (`freeze()` — built-in engine operation)
- Design Artifact schema (the handoff contract between environments)
- Light Engine (DuckDB + Polars) and Heavy Engine (Spark) abstractions

**Delegated to other sub-projects:**
- LLM invocation within `llm_reasoning` Jobs → routed through MCP servers owned by [`agent-platform`](../agent-platform/)
- KB retrieval during execution → [`knowledge-services`](../knowledge-services/)
- Query optimization for `output` Jobs → [`query-serving`](../query-serving/)
- Auth, audit, tenant isolation → [`platform-core`](../platform-core/)

## Module List

| Module | Origin | Document |
|--------|--------|----------|
| Compute Spec (10 Job Types, Dependency Rules, Format System, Common Subset) | §6 | [`compute-spec.md`](compute-spec.md) |
| Execution Sandbox (State-Passing, Python Constraints, SQL Injection Defense) | §7 | [`execution-sandbox.md`](execution-sandbox.md) |
| Freeze Pipeline (Spec Refinement, llm_reasoning Resolution, Canary Gating, Fuzzy Node Detection) | §4 | [`freeze-pipeline.md`](freeze-pipeline.md) |
| Design Artifact Schema (Handoff Contract) | §3.3 | [`design-artifact.md`](design-artifact.md) |

## External Interface Contract

| Interface | Consumer | Contract |
|-----------|----------|----------|
| `submit(compute_spec_yaml) → workflow_id` | All sub-projects | Accepts validated Compute Spec, returns workflow ID |
| `execute(workflow_id, environment_config) → execution_log` | Exploration, Production | Executes frozen Spec in target environment |
| `freeze(workflow_def) → frozen_spec` | Exploration → Production transition | Built-in op: scans llm_reasoning/fuzzy_nodes, human resolution, sandbox dry-run, marks frozen |
| `get_status(workflow_id) → status` | Agent Platform, Query Serving | DAG node status, execution progress |

## Related ADRs

- [ADR-0025](../../adr/0025-unified-workflow-engine.md) — Unified Workflow Engine (one engine, three environments)
- [ADR-0011](../../adr/0011-materialize-job-type.md) — Materialize Job Type
- [ADR-0005](../../adr/0005-four-layer-architecture.md) — Four-Layer Architecture (Zero AI Side Effects)
- [ADR-0006](../../adr/0006-freeze-bridge-independence.md) — Freeze Bridge Independence
