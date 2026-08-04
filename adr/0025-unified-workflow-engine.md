---
id: ADR-0025
title: "Unified Workflow Engine — One Engine, Three Environments"
status: accepted
date: 2026-07-30
deciders: "Project Sponsor"
domain: Architecture
---

# ADR-0025: Unified Workflow Engine — One Engine, Three Environments

- **Status**: Accepted
- **Date**: 2026-07-30
- **Deciders**: Project Sponsor
- **Domain**: Architecture

## Context

ADR-0005 established the four-layer architecture (Design Plane / Freeze Bridge / Runtime Plane / Intelligence Plane) based on the principle of separating AI-assisted exploration from deterministic production execution. ADR-0006 further established Freeze Bridge as an independent plane between Design and Runtime.

However, a closer analysis of the current design reveals that the four "planes" share a common computational core:

1. **A single Compute Spec (§6)**: Design Plane produces Design Artifacts whose `spec:` field is structurally identical to what Runtime Plane executes. The only difference is a temporary annotation layer (`fuzzy_nodes`, `confidence_summary`).
2. **A single computation engine**: Design Plane uses DuckDB/Polars (Light Engine), Runtime Plane uses Spark (Heavy Engine) — but §6.2 defines a Common Compute Subset guaranteeing portability between them. They are implementations of the same engine interface.
3. **A single deployment topology (§17)**: All four "planes" run as Pods in the same App Subnet (VPC: 10.0.1.0/24), same K8s cluster, same Istio Service Mesh. They are not physically separate systems.
4. **Shared infrastructure**: Git-based VCS (§3.4), unified Audit Trail (§11), OpenTelemetry tracing (§8.1), KB (§10) — all cross-plane.

In short, the architectural reality is **one Workflow Engine executing in different environments with different guarantees**, not four independent systems. However, the documentation consistently uses the language of "four independent planes" (ADR-0005: "Four independent planes with strict separation"). This framing obscures the underlying unity and creates three specific problems:

### Problem 1: Boundary ambiguity

The boundary between Intelligence Plane and Design Plane is unclear. Both invoke LLMs. Both are read-capable. The definition in §9.3 — "AI read-only analysis, temporary answers do not cross the bridge" — describes a capability restriction, not an architectural boundary. Users naturally ask: "Isn't Intelligence Plane just Design Plane without write permission?"

### Problem 2: LLM reasoning is treated as a plane concern, not a capability concern

Whether a step uses LLM reasoning is treated as defining *which plane it belongs to*, rather than as a *capability of that step*. This leads to:
- Intelligence Plane existing solely to provide a space for read-only LLM analysis
- No model for what happens when a Production user wants LLM-driven attribution analysis on live data
- The "zero AI side effects" guarantee relying on physical separation of services rather than on capability-level enforcement

### Problem 3: Missing infrastructure-level guarantees

The principle "Runtime Plane has zero AI side effects" is stated philosophically but its enforcement mechanism is scattered:
- Sandbox seccomp profiles (§7) block network egress at the Job level
- No plane-level NetworkPolicy blocks LLM API egress for Runtime Plane Pods (§17.3 lists 12 security group rules — none are plane-specific)
- The guarantee is component-level (Sandbox), not topology-level (NetworkPolicy)

## Options Considered

### Option A: Retain Four Independent Planes As-Is (Rejected)

Keep the current framing of four separate systems with separate services.

- **Pro**: No documentation changes needed. The "physical isolation" narrative is auditor-friendly.
- **Con**: The boundary ambiguity and missing infrastructure problems persist. The architecture-as-built (same cluster, same subnet, shared infrastructure) contradicts the architecture-as-documented (four independent planes). The Intelligence Plane / Design Plane distinction remains unconvincing at the technical level.
- **Assessment**: This option preserves the narrative but ignores the architectural reality. The current design already converges toward a unified engine — it just doesn't say so.

### Option B: Four Independent Services, Physically Isolated (Rejected)

Take "four independent planes" literally: deploy each plane in a separate VPC with strict network segmentation, independent databases, independent CI/CD, and explicit API contracts between them.

- **Pro**: True physical isolation. "Runtime Plane cannot call LLM" becomes provable at the VPC routing table level. Maximum auditability.
- **Con**: Massive operational complexity. Four sets of infrastructure, four monitoring stacks, four CI/CD pipelines. Cross-plane operations (e.g., Freeze Bridge reading Design Artifacts) require explicit API integrations with retry, circuit-breaking, and consistency guarantees. The shared KB becomes a distributed system problem. Cost multiplies by ~4×.
- **Assessment**: Technically pure but operationally prohibitive. The current deployment topology (§17) wisely avoids this, and we should not regress.

### Option C: Unified Workflow Engine + Environment-Level Isolation (Chosen)

Adopt a "one engine, three environments + one cross-environment mode" mental model while preserving physical isolation at the deployment level.

Core reframing:

| Current Concept | Reframed As |
|-----------------|-------------|
| **Design Plane** | **Exploration Environment** — same Workflow Engine, LLM APIs reachable, sampled data, no audit trail binding |
| **Freeze Bridge** | **Freeze Pipeline** — a built-in `freeze()` operation on the Workflow Engine, not an independent service. Scans llm_reasoning steps → proposes deterministic replacements → requires human sign-off → validates → marks frozen |
| **Runtime Plane** | **Production Environment** — same Workflow Engine, LLM API egress physically blocked at NetworkPolicy level, full data, full audit |
| **Intelligence Plane** | **Cross-Environment Read-Only Mode** — same Workflow Engine, can query read-replicas of both Exploration and Production environments. Write operations intercepted and rejected at the Engine level. Answers are temporary consumables, not persisted |

Key structural changes:

1. **`llm_reasoning` becomes the 10th Job Type** (alongside source/transform/output/quality/workflow_ref/data_writer/decision/wait/materialize). Whether LLM is used is a property of a Job, not a property of a "plane."

2. **Workflow Definition is environment-agnostic.** No `mode` field in the Workflow YAML. The same Workflow Definition can be executed in any environment — the environment's configuration determines which capabilities are enabled.

3. **Capability boundaries are enforced at the environment level via configuration + NetworkPolicy:**

```yaml
# Exploration Environment
engine:
  llm:
    enabled: true
    allowed_capabilities: [read_analyze, suggest_plan, generate_draft, modify_spec, kb_write]

# Production Environment  
engine:
  llm:
    enabled: true                    # Network is open for read-only LLM calls
    allowed_capabilities: [read_analyze, suggest_plan]  # Engine rejects others
  network:
    egress_policy:
      allow_llm_api: true            # LLM API reachable
      audit: full
```

1. **Freeze Bridge is demoted from a "plane" to a pipeline operation:** `freeze(workflow_def)` scans all `llm_reasoning` Jobs with `capability` other than `read_analyze` or `suggest_plan`, presents each for human resolution (replace with deterministic script OR keep with explicit justification), validates the result in a production-sandbox dry-run, and marks the Workflow as frozen. This is the Workflow Engine performing an operation on a Workflow Definition — not a cross-system migration.

2. **Plane-level NetworkPolicy is explicitly added** to the deployment architecture (§17.3) to complement the existing Sandbox-level seccomp enforcement (§7).

## Decision

Adopt **Option C**: Reframe the architecture as **one Workflow Engine running in three environments (Exploration / Freeze / Production) + one cross-environment read-only mode**, and introduce `llm_reasoning` as the 10th Job Type with capability-based access control.

### Decision #1: Reframe architectural narrative

The four "planes" remain as deployment concepts but are described as **environments of the same Workflow Engine**, not independent systems. The unified engine perspective is made explicit in:
- `docs/03-architecture.md` §2 (Panoramic Architecture) — add a note that all environments execute the same Compute Spec
- `docs/03-architecture.md` §3 (Four-Layer Model) — reframe the table to show "same engine, different guarantees"
- `docs/01-facts.md` Decision #2 — update to reflect the unification

ADR-0005 and ADR-0006 remain Accepted. This ADR refines their framing; it does not reverse the core architectural principle of separating exploration from production execution.

### Decision #2: `llm_reasoning` as 10th Job Type

Added to Compute Spec (§6) with the following capability taxonomy:

| capability | What LLM Can Do | Allowed in Production? | Rationale |
|------------|----------------|------------------------|-----------|
| `read_analyze` | Read-only analysis: attribution, anomaly explanation, trend analysis, NL summarization | ✅ Configurable | No state mutation; answers returned directly to user |
| `suggest_plan` | Recommend next actions: which Workflow to run, which investigation path to follow | ✅ Configurable | No state mutation; recommendations go through Design process |
| `generate_draft` | Generate Workflow Definition fragments from user descriptions | ❌ Prohibited | Generates Spec that could be directly consumed |
| `modify_spec` | Propose modifications to existing Workflow Definitions | ❌ Prohibited | Directly affects execution logic |
| `kb_write` | Extract knowledge and write to Knowledge Base | ❌ Prohibited | Writes persistent state |

The `llm_reasoning` Job integrates with the existing MCP infrastructure (§22): it invokes LLM capabilities through registered MCP Servers and Tools, not through direct provider API calls. This preserves provider agnosticism and reuses existing guard pipelines (§3.2).

### Decision #3: Environment-level capability enforcement

Capability enforcement is layered:
1. **Engine level**: The Workflow Engine rejects Jobs whose `llm.capability` is not in the environment's `allowed_capabilities` list. Rejection occurs at Job submission time, before any execution begins.
2. **Network level**: Production Environment Pods have NetworkPolicy rules explicitly restricting LLM API egress. Added to §17.3.
3. **Sandbox level**: Existing seccomp profiles (§7.2) remain as defense-in-depth.

### Decision #4: Workflow Definition v2 improvements

The following structural improvements to the Workflow Definition YAML are adopted:

| Improvement | Detail |
|-------------|--------|
| **UUID + display_name** | All entities (Workflow, Job, Group, Parameter) have both a stable `id` (UUID) and a human-readable `display_name` |
| **Parameter scope + inject_by** | Parameters declare `scope` (workflow/group/job) and `inject_by` (scheduler/user/upstream_workflow/api/environment/default_only) |
| **Parameter default value sources** | Default values support: static literal, built-in expression (`PREVIOUS_MONTH_START()`), config reference (`config://path`), environment variable (`from_env`), KB reference (`from_kb`) |
| **Output multi-file support** | `output` Jobs support multiple files with `concurrency` (parallel/sequential), `on_failure` (abort_all/continue/retry_failed_only), and per-file `condition` |
| **Generic JDBC/ODBC connectors** | `source` Jobs support generic `jdbc` and `odbc` connector protocols covering DB2, Sybase, Teradata, Oracle, SQL Server, and any JDBC/ODBC-compatible data source. Native connectors (PostgreSQL, MySQL, etc.) take priority when available |

## Rationale

1. **Architecture-as-documented should match architecture-as-built.** The current deployment topology (§17) already deploys all planes in the same cluster. The "one engine" framing is a documentation correction, not a redesign.

2. **LLM capability is orthogonal to execution environment.** Whether a step uses LLM reasoning should be a property of that step, not a reason to create a separate service. The `llm_reasoning` Job Type + capability taxonomy provides finer-grained control than the coarse "which plane?" question.

3. **Defense-in-depth for "zero AI side effects."** The current design relies on Sandbox seccomp alone. Adding plane-level NetworkPolicy provides topological enforcement that auditors can verify independently of application code.

4. **The four concepts survive.** Exploration, Freeze, Production, and Read-Only Analysis remain meaningful operational concepts. They just don't need to be four separate codebases or four separate services.

5. **The physical isolation guarantee is preserved.** The critical property — "Production cannot execute LLM steps that write state" — remains enforced. It is now enforced at two levels (Engine capability check + NetworkPolicy) rather than relying on the abstract notion of "separate planes."

6. **MCP integration avoids vendor lock-in.** By routing `llm_reasoning` through the existing MCP infrastructure rather than direct provider APIs, the Workflow Definition remains provider-agnostic. Switching from GPT-5 to Claude-4 is an MCP Server configuration change, not a Workflow Definition change.

## Consequences

### Positive

- **Architectural honesty**: Documentation accurately reflects the deployment reality.
- **Conceptual simplification**: Users and developers understand one Workflow Engine with different environment configurations, not four separate systems.
- **Finer-grained AI control**: The `llm_reasoning` capability taxonomy allows Production environments to enable read-only AI analysis while blocking speculative Spec generation — a middle ground the current all-or-nothing "plane" model cannot express.
- **Reduced duplication**: Workflow parsing, DAG scheduling, parameter binding, retry logic — implemented once, used across all environments.
- **Extensibility**: Adding a new "mode" (e.g., `staging` environment with Production data but Exploration capabilities) is a configuration change, not a new service.
- **Provider agnosticism**: `llm_reasoning` via MCP preserves the ability to switch LLM providers without modifying Workflow Definitions.

### Negative

- **Documentation refactoring cost**: Multiple sections of `docs/03-architecture.md` and `docs/01-facts.md` need updates to align with the reframed narrative. ADR-0005 and ADR-0006 need frontmatter updates linking to this ADR.
- **NetworkPolicy complexity**: Adding plane-specific egress rules increases operational surface area. Misconfiguration could accidentally block legitimate traffic or leave unintended LLM API paths open.
- **Auditor re-education**: Auditors familiar with the "four independent planes" narrative will need to understand the new model. The guarantee is equally strong (configuration + NetworkPolicy vs. separate service), but the explanation is different.
- **Workflow Definition migration**: Existing Workflow Definitions in the documentation examples need UUID and display_name fields added. Parameter definitions need `scope` and `inject_by` fields.

### Neutral

- **ADR-0005 and ADR-0006 remain Accepted.** This ADR refines their narrative framing but does not reverse the core decisions. Both should be updated with `refined_by: ADR-0025` in their frontmatter.
- **The 9 existing Job Types are unchanged.** `llm_reasoning` is additive. The existing taxonomy (source/transform/output/quality/workflow_ref/data_writer/decision/wait/materialize) is validated as correct per governance-semantic differentiation analysis.
- **MVP scope is unaffected.** The Freeze Pipeline and `llm_reasoning` Job Type are full-architecture features; MVP can start with Exploration Environment + manual freeze.

## Linked Modules

- `adr/0005-four-layer-architecture.md` → Refined by this ADR (narrative reframing; core decisions preserved)
- `adr/0006-freeze-bridge-independence.md` → Refined by this ADR (Freeze Bridge repositioned as engine operation)
- `adr/0011-materialize-job-type.md` → Precedent for adding Job Types with independent governance semantics
- `adr/0013-kb-storage-strategy.md` → KB remains cross-environment; no changes
- `adr/0016-dual-mode-agent-orchestration.md` → MCP-based `llm_reasoning` reuses the Skill/MCP infrastructure
- `docs/03-architecture.md` → §2 (Panoramic Architecture), §3 (Four-Layer Model), §4 (Freeze Bridge), §6 (Compute Spec), §7 (Execution Sandbox), §11 (Cross-Cutting), §17 (Deployment Architecture)
- `docs/01-facts.md` → Decision #1, Decision #2
