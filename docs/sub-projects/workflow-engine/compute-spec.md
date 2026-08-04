# Compute Spec

> **Origin**: §6 of [`docs/03-architecture.md`](../../03-architecture.md) | **Sub-project**: [workflow-engine](README.md)

## Purpose

This module covers the **Compute Spec** — the Unified Compute Definition that Reporting, ETL, Adjustment, and Recon all share. Reporting, ETL, Adjustment, and Recon share the same set of YAML definitions; a single Spec language describes every Workflow that the Unified Workflow Engine (ADR-0025) can execute across the Exploration, Freeze, and Production environments.

The Compute Spec defines the concept hierarchy (Workflow → Variables/Parameters/Formats/Job Groups → Jobs), the complete enumeration of 10 Job Types, the dependency-trigger rules (`depends_on` + `trigger_rule`), the Format System (decoupled rendering templates), and the **Common Compute Subset** — the minimum set of operations guaranteed to be portable between the Light Engine (DuckDB/Polars) and the Heavy Engine (Spark/Trino/Ray).

## Boundaries

**In-scope:**
- §6 Concept Hierarchy — Workflow → Variables / Parameters / Formats / Job Groups → Jobs.
- §6 Execution Rules — `depends_on` is the sole ordering declaration; YAML ordering is irrelevant; groups support stage-level dependency; nested `workflow_ref` exposes a summary DAG.
- §6 Job Type Complete Enumeration (all 10 types: `source`, `transform`, `output`, `quality`, `workflow_ref`, `data_writer`, `decision`, `wait`, `materialize`, `llm_reasoning`).
- §6.1 Dependency Trigger Rules (`all_success`, `all_failed`, `all_done`, `one_success`, `none_failed`) and the `trigger_rule` YAML field.
- §6 Format System — global Format definitions decoupled from Jobs (report/excel/dashboard/data_export), including Dashboard interactivity blocks.
- §6.2 Common Compute Subset — the portability-guarantee table mapping each operation to Light/Heavy Engine support, plus the Portability Rules (`engine: light_only`, Freeze Pipeline incompatibility blocking).

**Delegated / out-of-scope:**
- Execution isolation, state-passing, Python constraints, and SQL-injection defense → [`execution-sandbox.md`](execution-sandbox.md) (§7).
- `freeze()` operation, Spec Refinement, canary gating, fuzzy-node detection → [`freeze-pipeline.md`](freeze-pipeline.md) (§4).
- Design Artifact (the handoff YAML carrying fuzzy nodes + confidence) → [`design-artifact.md`](design-artifact.md) (§3.3).
- MCP servers and Tools that actually serve `llm_reasoning` invocations → [`agent-platform`](../agent-platform/) (the Compute Spec only declares the Job; the call is routed through MCP).
- KB retrieval used inside transforms, and Query pushdown for `output` Jobs → [`knowledge-services`](../knowledge-services/) and [`query-serving`](../query-serving/).

**Upstream/downstream neighbors:**
- *Authoring path*: Exploration Environment emits a Design Artifact (§3.3) → Freeze Pipeline resolves fuzzy nodes (§4.3) → frozen Compute Spec is submitted to the Engine.
- *Runtime path*: Scheduler → Executor builds the DAG from `depends_on` → per-Job Sandbox (§7) → Light/Heavy Engine execution → `output`/`data_writer` delivery.

## Interfaces

### §6 Concept Hierarchy

```
Workflow
  ├── Variables (global variables)
  ├── Parameters (runtime inputs)
  ├── Formats (output format templates)
  └── Job Groups (logical grouping)
  └── Jobs (smallest execution unit)
       ├── type: source | transform | output | quality | workflow_ref | data_writer | decision | wait | materialize | llm_reasoning
       └── depends_on: [job_id, ...]  ← sole ordering declaration
```

### §6 Execution Rules

- `depends_on` determines serial/parallel execution; YAML ordering is irrelevant.
- Jobs without mutual dependencies → auto-parallelized.
- Groups support `depends_on` on another Group (stage-level dependency).
- Nested Workflows (`workflow_ref`) expose a summary DAG (Job list and execution status) to the parent Workflow for debugging and monitoring, while keeping execution context isolated.

### §6 Job Type Complete Enumeration

| Type           | Purpose                                                                                                                                                                                                                                                                     |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `source`       | Fetch data from external sources (connector + query/path/endpoint)                                                                                                                                                                                                          |
| `transform`    | Data transformation (op sequence, SQL statement, or Python code block)                                                                                                                                                                                                      |
| `output`       | Output/distribution (format + destination)                                                                                                                                                                                                                                 |
| `quality`      | Data quality checks (rules)                                                                                                                                                                                                                                                 |
| `workflow_ref` | Reference another Workflow (black-box execution)                                                                                                                                                                                                                           |
| `data_writer`  | Write back to data source (upsert/append/merge + transaction). Must NOT be confused with `output`: `data_writer` specifically refers to writing back to a data source registered in Data Catalog; `output` specifically refers to rendered file/notification distribution. Decision rule: target is a data_source registered in Data Catalog → `writeback`; target is filesystem/messaging channel → `output`. |
| `decision`     | Conditional branching (conditions → branches). **Must declare `default` branch**; the default branch is taken when no condition matches. `default` cannot be omitted.                                                                                                       |
| `wait`         | Wait for external event (signal/webhook/time). **Must declare `timeout`** (max 72h); auto-transitions to `TIMED_OUT` status if exceeded, triggering an Incident.                                                                                                            |
| `materialize`  | Materialized aggregation (incremental/full refresh). Pre-computes and persists frequently-queried aggregation results to target tables for direct use by subsequent queries. Supports incremental watermark refresh + retention policy.                                     |
| `llm_reasoning` | Invoke LLM capabilities through registered MCP Servers and Tools (not direct provider API calls). Governed by the capability taxonomy: `read_analyze` (read-only analysis, attribution, anomaly explanation, NL summarization), `suggest_plan` (recommend next actions), `generate_draft` (generate Workflow Definition fragments from descriptions), `modify_spec` (propose modifications to existing Definitions), `kb_write` (extract knowledge and write to KB). Capabilities `generate_draft`, `modify_spec`, and `kb_write` are rejected at Engine level in Production Environment. Capabilities `read_analyze` and `suggest_plan` are configurable. All invocations preserve provider agnosticism via MCP. |

### §6 Format System

Global Format definitions, decoupled from Jobs. Supported types: `report` (PDF), `excel`, `dashboard`, `data_export` (Parquet/CSV). Note: `data_writer` is a Job type, not a Format type; Format is responsible for rendering/presentation, while `data_writer` handles database writebacks.

> Dashboard Format supports `interactivity` configuration blocks: `drill_down_paths` (drill-down paths), `cross_filter_dimensions` (cross-widget linked dimensions). The rendering engine generates interactive Dashboards based on this, not static images.

## Dependencies

- **Workflow/Job/YAML parsing**: depends on the Compute Spec schema validator (run by the Freeze Pipeline Validation Engine — see §4) before any Job is submitted.
- **`source` / `transform` (SQL)**: depend on the Data Connector Adapter (5 Levels) and the Dialect Adapter (ANSI SQL:2003 ↔ engine-specific dialects).
- **`transform` (Python)**: depends on the Light Engine Python UDF runtime (DuckDB/Polars); on the Heavy Engine it requires prior transpilation to Java/Scala UDF or SQL expressions (see §6.2 Portability Rules and §7.2 Python Execution Constraints).
- **`output`**: depends on the unified Format rendering engine (report/excel/dashboard/data_export).
- **`quality`**: depends on the unified Rule engine.
- **`decision`**: depends on the unified conditional evaluation engine.
- **`wait`**: depends on the unified event-waiting logic (signal/webhook/time, max 72h timeout).
- **`materialize`**: depends on the unified incremental/full-refresh interface; DuckDB handles <100GB materialization, Spark handles TB-scale (ADR-0011).
- **`llm_reasoning`**: invokes LLMs **via MCP infrastructure (§22)** — orthogonal to the Light/Heavy Engine distinction. Capability enforcement is at the Engine submission level and NetworkPolicy level, not the compute layer. Routes to [`agent-platform`](../agent-platform/) MCP servers/Tools.
- **Engine routing**: the Freeze Pipeline detects incompatibility between the `engine` tag and the target deployment environment during validation and blocks deployment.
- Cross-sub-project: [`knowledge-services`](../knowledge-services/) (Data Catalog, Business Glossary for transform formulas), [`query-serving`](../query-serving/) (pushdown for `output`), [`platform-core`](../platform-core/) (audit, tenant isolation, auth on every Job submission).

## Data Model

- **Workflow** — top-level YAML entity carrying `variables`, `parameters`, `formats`, `job_groups`, `jobs`, and an `engine` tag (`light` | `heavy` | `light_only`).
- **Job** — smallest execution unit. Fields: `type` (one of the 10 enumerated values), `depends_on: [job_id, ...]` (sole ordering declaration), and `trigger_rule` (defaults to `all_success`).
- **Job Group** — logical grouping of Jobs; itself carries a `depends_on` to express stage-level dependency on another Group.
- **Format** — global, decoupled from Jobs. Types: `report` (PDF), `excel`, `dashboard` (with optional `interactivity`: `drill_down_paths`, `cross_filter_dimensions`), `data_export` (Parquet/CSV).
- **`engine` tag** — emitted by the Freeze Pipeline based on Portability Rules:
  - Workflows using only the Common Compute Subset → freely switchable between Light/Heavy.
  - Workflows containing Python transforms → `engine: light_only`, unless all Python blocks have been transpiled.
- **`llm_reasoning` capability field** — one of `read_analyze`, `suggest_plan`, `generate_draft`, `modify_spec`, `kb_write`. The Engine rejects `generate_draft`/`modify_spec`/`kb_write` in Production; `read_analyze`/`suggest_plan` are configurable.
- **`materialize` config** — refresh mode (`incremental` | `full`), watermark, retention policy, target table.

## Failure Modes & Recovery

| Failure | Impact | Recovery |
| --- | --- | --- |
| Job with `depends_on` cycle | DAG cannot be constructed | Validation Engine (§4) performs cycle detection pre-freeze; rejected with location evidence before submission. |
| `decision` Job missing `default` branch | Unhandled condition → execution stalls | Spec validation rejects the Job — `default` is mandatory and cannot be omitted. |
| `wait` Job exceeds 72h timeout | Hung Workflow | Auto-transitions to `TIMED_OUT`; triggers an Incident (see [`platform-core`](../platform-core/) Incident Manager). |
| `data_writer` vs `output` confusion (target misclassified) | Wrong delivery path (DB writeback vs file/notification) | Apply the decision rule: target is a Data-Catalog-registered `data_source` → `data_writer` (`writeback`); filesystem/messaging channel → `output`. Enforced at Spec validation. |
| Python transform on Heavy Engine (not transpiled) | Execution error | Non-transpiled Python transforms error on Heavy Engine and **fall back to Light Engine** (per §6.2 Portability Rules). |
| `engine` tag incompatible with target deployment | Blocked deployment | Freeze Pipeline detects incompatibility during the validation phase and blocks deployment. |
| `llm_reasoning` Job with forbidden capability in Production | Capability rejected at submission | `generate_draft`, `modify_spec`, `kb_write` are rejected at Engine level in Production; must be resolved during Freeze (§4.1b) to a deterministic replacement. |

## Non-Functional Requirements

### §6.2 Common Compute Subset (Portability Guarantee)

Engine independence is not absolute. The system defines a **Common Compute Subset** — the minimum set of operations guaranteed to be portable between Light Engine (DuckDB/Polars) and Heavy Engine (Spark/Trino/Ray):

| Operation            | Light Engine               | Heavy Engine            | Notes                                                                                                                                                                                                |
| -------------------- | -------------------------- | ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `source`             | ✅ Full                     | ✅ Full                  | Connector adaptation layer abstracts differences                                                                                                                                                     |
| `filter`             | ✅ Full                     | ✅ Full                  | WHERE / predicate pushdown                                                                                                                                                                           |
| `aggregate`          | ✅ Full                     | ✅ Full                  | GROUP BY, window functions (standard SQL:2003 subset)                                                                                                                                                |
| `join`               | ✅ Full                     | ✅ Full                  | Inner, Left, Right, Full Outer, Semi, Anti                                                                                                                                                           |
| `output`             | ✅ Full                     | ✅ Full                  | Unified Format rendering engine                                                                                                                                                                      |
| `quality`            | ✅ Full                     | ✅ Full                  | Unified Rule engine                                                                                                                                                                                  |
| `decision`           | ✅ Full                     | ✅ Full                  | Unified conditional evaluation engine                                                                                                                                                                |
| `wait`               | ✅ Full                     | ✅ Full                  | Unified event-waiting logic                                                                                                                                                                          |
| **materialize**      | ✅ Full (DuckDB)            | ✅ Full (Spark)          | Unified incremental refresh + full refresh interface; DuckDB handles <100GB materialization, Spark handles TB-scale materialization                                                                   |
| **llm_reasoning**     | — (routes through MCP)      | — (routes through MCP)   | `llm_reasoning` Jobs invoke LLMs via MCP infrastructure (§22); they are orthogonal to the Light/Heavy Engine distinction. Capability enforcement is at the Engine submission level and NetworkPolicy level, not the compute layer. |
| **Python transform** | ✅ DuckDB/Polars Python UDF | ⚠️ **Restricted**        | Python code blocks are only directly executed in Light Engine. Migration to Heavy Engine requires transpilation to Java/Scala UDF or SQL expressions. Non-transpiled Python transforms will error on Heavy Engine and fall back to Light Engine. |
| **SQL transform**    | ✅ Full                     | ✅ Full                  | ANSI SQL:2003 compatible subset; engine-specific dialects translated via Dialect Adapter                                                                                                          |
| **table_format**     | ✅ Iceberg/Delta/Parquet    | ✅ Iceberg/Delta/Parquet | Modern table formats (Iceberg/Delta Lake/Hudi) uniformly supported via Data Connector Adapter table format plugins                                                                                   |

**Portability Rules**:
- Workflows using only the Common Compute Subset can seamlessly switch between Light/Heavy Engines.
- Workflows containing Python transforms are marked `engine: light_only`, unless all Python blocks have been transpiled.
- The Freeze Pipeline detects incompatibility between the `engine` tag and the target deployment environment during the validation phase and blocks deployment.

## Key Flows

### §6 DAG construction flow

```
Compute Spec YAML (frozen)
    │
    ▼
┌─────────────────────────────────────────────┐
│ 1. Parse Workflow + Jobs + Job Groups        │
│    • type ∈ {10 enumerated Job Types}        │
│    • depends_on: [job_id, ...]               │
│    • trigger_rule: all_success (default)     │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│ 2. Build DAG                                 │
│    • Edge = depends_on (sole ordering decl)  │
│    • YAML order irrelevant                   │
│    • Jobs w/o mutual deps → auto-parallel    │
│    • Group→Group depends_on = stage dep      │
│    • workflow_ref exposes summary DAG to     │
│      parent (context isolated)               │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│ 3. Evaluate trigger_rule per downstream Job  │
│    • all_success (default)                   │
│    • all_failed | all_done | one_success |   │
│      none_failed                             │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│ 4. Dispatch each Job to Sandbox (§7)         │
│    • engine tag routing: light | heavy |     │
│      light_only                              │
│    • llm_reasoning → MCP (orthogonal)        │
└─────────────────────────────────────────────┘
```

### §6.1 Dependency Trigger Rules

`depends_on` default behavior is `all_success` (all upstream must succeed to trigger downstream). The following trigger rule overrides are supported:

| Rule                   | Behavior                                          | Applicable Scenario                          |
| ---------------------- | ------------------------------------------------- | -------------------------------------------- |
| `all_success` (default)| All upstream Jobs succeed → trigger downstream    | Normal data flow                             |
| `all_failed`           | All upstream Jobs fail → trigger downstream       | Cleanup/alert Jobs                           |
| `all_done`             | All upstream Jobs complete (regardless) → trigger | Data collection (partial results still valuable) |
| `one_success`          | At least one upstream Job succeeds → trigger      | Multi-source data (any source with data is sufficient) |
| `none_failed`          | No upstream Job fails (skipped allowed) → trigger | Optional dependency chain                    |

Specify via `trigger_rule` field in Job YAML: `depends_on: [job_a, job_b]` + `trigger_rule: all_success` (default, can be omitted).

### Shared runtime sequence

The Compute Spec's DAG is the artifact executed end-to-end by the Freeze Pipeline and the Runtime Executor. The full freeze-side sequence (Validation → Test Runner → Impact Report → Canary) is in [`../_shared/sequence-diagrams.md`](../_shared/sequence-diagrams.md) **§21.1 Freeze Flow: Full End-to-End**, and the runtime execution path (with failure handling) is in **§21.2 Runtime Execution with Failure**.

## Design References

- **Original sections**: §6 (Compute Spec), §6.1 (Dependency Trigger Rules), §6 Format System, §6.2 (Common Compute Subset / Portability Guarantee) of [`docs/03-architecture.md`](../../03-architecture.md).
- **Related workflow-engine docs**: [`execution-sandbox.md`](execution-sandbox.md) (§7 — Sandbox, Python constraints, SQL defense), [`freeze-pipeline.md`](freeze-pipeline.md) (§4 — `freeze()` and fuzzy-node resolution), [`design-artifact.md`](design-artifact.md) (§3.3 — handoff contract).
- **Shared sequence diagram**: [`../_shared/sequence-diagrams.md`](../_shared/sequence-diagrams.md) §21.1 Freeze Flow / §21.2 Runtime Execution with Failure.
- **ADRs** ([index](../../adr-index.md)): [ADR-0025 Unified Workflow Engine](../../../adr/0025-unified-workflow-engine.md) (one engine, three environments — the root decision behind the unified Compute Spec), [ADR-0011 Materialize Job Type](../../../adr/0011-materialize-job-type.md) (the `materialize` Job Type and Light/Heavy refresh split).
- **Glossary** ([../../glossary.md](../../glossary.md)): Compute Spec, Workflow, Job, Job Type, Format, Common Compute Subset, Light Engine, Heavy Engine, Materialize, `llm_reasoning`.
- **Cross-references retained from source**: §22 (MCP infrastructure invoked by `llm_reasoning`); §7.2 / §7.3 (Python AST + SQL AST scans referenced by the Validation Engine step 14 of §21.1).
