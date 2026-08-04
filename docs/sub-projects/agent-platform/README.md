# agent-platform — Agent Orchestration & AI Capabilities

> **Origin**: §22A–§22M, §3.1–§3.5 of `docs/03-architecture.md`
> **Key ADRs**: [ADR-0016](../../adr/0016-dual-mode-agent-orchestration.md) (Dual-Mode), [ADR-0017](../../adr/0017-verified-path-saga-semantics.md)–[ADR-0021](../../adr/0021-vp-promotion-concurrency.md), [ADR-0024](../../adr/0024-kb-reasoning-support-playbooks-code.md)

## Positioning

The **Agent Platform** is the system's AI orchestration layer — the largest and most detailed sub-project in the design (§22A–§22M, 1964 lines). It implements the **dual-mode architecture** (ADR-0016): *Explore with AI, Execute without AI side effects*. Agents reason freely in Exploration Mode but follow predefined fixed-step Verified Paths for any state-mutating operation.

This sub-project owns: the Agent SDK runtime, the Skill catalog (18 skills), the MCP server catalog (21 servers), the 7-layer security defense, memory architecture, cost governance, evaluation framework, and the Exploration Environment's UI components.

## Boundaries

**In-scope:**
- Agent SDK runtime (ReAct loop, durable execution, multi-model support, hierarchical multi-agent)
- Dual-mode orchestration (Exploration vs Verified Path switching)
- Skill catalog (S01–S18) and MCP server catalog (MCP-01..17+23, MCP-20/21/22)
- 7-layer agent security defense (input/tool-gate/output/response/action/audit/sandbox)
- Agent memory (Four-Layer: L1 Working, L2 Episodic, L3 Semantic, L4 Procedural)
- Cost governance & model degradation (Tiered Enforcement, Loop Detection, Four-Stage Rollout)
- Agent evaluation framework (Six-Dimension Scoring, Golden Dataset, Evaluation Flywheel)
- Multi-agent concurrency control (Three-Layer Locking, Priority Preemption, Shadow Promotion)
- Verified Path catalog and capability discovery
- Exploration Environment UI (Conversation Interface, Visual Designer, Workbench)
- Prompt Injection Defense guard pipeline
- Change Intelligence (Pre/Post-Change Impact, AI Knowledge Agent)

**Delegated to other sub-projects:**
- Workflow execution (Agent invokes Jobs via the engine) → [`workflow-engine`](../workflow-engine/)
- KB storage & retrieval (Vector/Graph/Relational) → [`knowledge-services`](../knowledge-services/)
- Query pushdown optimization → [`query-serving`](../query-serving/)
- Auth/RBAC enforcement at tool-call boundary → [`platform-core`](../platform-core/)

## Module List

| Module | Origin | Document |
|--------|--------|----------|
| Exploration Environment (Conversation UI, Visual Designer, Workbench, AI Copilot) | §3.1–§3.5 | [`exploration-runtime.md`](exploration-runtime.md) |
| Agent SDK — Dual-Mode Orchestration | §22A | [`dual-mode-orchestration.md`](dual-mode-orchestration.md) |
| Skill Catalog (S01–S18) | §22B | [`skill-catalog.md`](skill-catalog.md) |
| MCP Server Catalog | §22C | [`mcp-catalog.md`](mcp-catalog.md) |
| Agent Security — 7-Layer Defense | §22D | [`agent-security.md`](agent-security.md) |
| Agent Workflow Composition (7 Scenarios) | §22E | [`workflow-composition.md`](workflow-composition.md) |
| Verified Path Catalog + Multi-Tenant Isolation + Governance + Concurrency + Capability Discovery | §22F–§22H, §22K–§22M | [`verified-path-and-governance.md`](verified-path-and-governance.md) |
| Agent Memory + Evaluation Framework | §22I, §22J | [`memory-and-evaluation.md`](memory-and-evaluation.md) |

## External Interface Contract

| Interface | Consumer | Contract |
|-----------|----------|----------|
| `agent.query(natural_language, context) → response` | Exploration UI, Cross-Env Read-Only | NL query → structured answer with attribution |
| `agent.execute(verified_path_id, params) → result` | Freeze Pipeline, Production | Fixed-step execution; LLM reasons within steps but cannot skip/reorder |
| `skill.invoke(skill_id, args) → result` | Internal (Agent SDK) | Skill execution with orchestration metadata |
| `mcp.call(server_id, tool, args) → result` | Internal (Agent SDK, llm_reasoning Jobs) | MCP tool invocation through guard pipeline |

## Related ADRs

- [ADR-0016](../../adr/0016-dual-mode-agent-orchestration.md) — Dual-Mode Agent Orchestration
- [ADR-0017](../../adr/0017-verified-path-saga-semantics.md) — Verified Path Saga Semantics & Durable Execution
- [ADR-0018](../../adr/0018-agent-evaluation-framework.md) — Agent Evaluation Framework
- [ADR-0019](../../adr/0019-agent-memory-architecture.md) — Agent Memory Architecture
- [ADR-0020](../../adr/0020-agent-cost-governance.md) — Agent Cost Governance & Model Degradation Detection
- [ADR-0021](../../adr/0021-vp-promotion-concurrency.md) — Verified Path Promotion & Multi-Agent Concurrency Control
- [ADR-0024](../../adr/0024-kb-reasoning-support-playbooks-code.md) — KB Reasoning Support (Playbooks & Code Knowledge)
