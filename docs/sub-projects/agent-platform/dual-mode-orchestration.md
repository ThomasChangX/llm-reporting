# Dual-Mode Orchestration

> **Origin**: §22A of [`docs/03-architecture.md`](../../03-architecture.md) | **Sub-project**: [agent-platform](README.md)

## Purpose

This module covers the **Agent SDK Architecture — Dual-Mode Orchestration** (§22A). Agent orchestration uses a **dual-mode architecture**, routing by operational risk. Core principle: **Explore with AI (Exploration), Execute without AI Side Effects (Verified Path)**. See [ADR-0016](../../../adr/0016-dual-mode-agent-orchestration.md) for the decision rationale.

This module owns:
- **§22A overview + mode-switching table** — Exploration vs Verified Path routing, and the `S01 IntentParser`-driven mode switch.
- **§22A.1 Agent Runtime Overall Architecture (Exploration Mode)** — the Planner-Executor-Responder three-phase pipeline (7 runtime steps from Intent Classifier through Response Guard).
- **§22A.2 Tool-Call Flow — Detailed Steps** — the 7-step component responsibility table (Intent Classifier → Skill Planner → Permission Gate → Parallel Executor → Output Sanitizer → Response Synthesizer → Response Guard).
- **§22A.3 ReAct Loop (Multi-Round Reasoning)** — the max-5-rounds loop with per-tenant configurable control parameters.
- **§22A.4 Durable Execution & Idempotency → ADR-0017** — Saga semantics, three-layer idempotency, persistent state tables, the Evidence Packet (decision evidence package), and DLQ handling.
- **§22A.5 Multi-Model Support** — Model Registry architecture, the `ModelInterface` abstract interface, Model Selection Logic (Task Type / Data Sensitivity / Cost Budget / Latency / Failover), and Tenant-Level Model Preference.
- **§22A.6 Hierarchical Multi-Agent Architecture (Phase 7+)** — the evolution direction from the flat 18-Skill MVP catalog to a Central Reasoner + Sub-Agent layered architecture, with three-gate introduction criteria.

## Boundaries

**In-scope:**
- §22A — the dual-mode concept (Exploration vs Verified Path), the mode-switching rules, and the rejection rule for un-pathed modifications.
- §22A.1 — the 7-step Exploration-Mode runtime pipeline (Intent Classifier, Skill Planner, Permission Gate, Parallel Tool Executor, Tool Output Sanitizer, Response Synthesizer, Response Guard) and the immutable Session Context.
- §22A.2 — the detailed per-step responsibility table with inputs/outputs/key constraints.
- §22A.3 — the ReAct loop (max 5 rounds) and the per-tenant loop-control parameters (`max_rounds`, `loop_timeout_seconds`, `tool_call_budget`, `parallelism`, `confidence_threshold`).
- §22A.4 — Saga semantics for Verified Path execution, the three-layer idempotency key, `verified_path_executions` / `verified_path_step_events` / `dlq_entries` tables, the Evidence Packet JSON structure, and DLQ escalation.
- §22A.5 — the Model Registry, `ModelInterface`, selection dimensions, and tenant/group/user model-preference overrides.
- §22A.6 — the Phase 7+ Central Reasoner + Sub-Agent architecture, its relationship to the MVP flat Skill catalog, and the three-gate introduction criteria.

**Delegated / out-of-scope:**
- The Skill catalog itself (S01–S18) → [`skill-catalog.md`](skill-catalog.md) (§22B).
- The MCP server catalog → [`mcp-catalog.md`](mcp-catalog.md) (§22C).
- The full 7-layer security defense (Permission Gate here is one boundary within Layer 2) → [`agent-security.md`](agent-security.md) (§22D).
- Verified Path catalog entries, capability discovery, and governance → `verified-path-and-governance.md` (§22F–§22H, §22K–§22M).
- Agent memory (L1–L4) and the evaluation framework → `memory-and-evaluation.md` (§22I, §22J).
- Cost governance & model-degradation detection → [`README.md`](README.md) ADR-0020 (§22K cost governance).
- Workflow execution (the Jobs the Agent invokes) → [`workflow-engine`](../workflow-engine/).

**Upstream/downstream neighbors:**
- *Input*: user natural-language query + immutable Session Context (`tenant_id`, `user_id`, `role`, `permissions`, `caps`); for Verified Path, a `verified_path_id` + params.
- *Output*: a guarded user response with citations + per-claim confidence + guard warnings; for Verified Path, durable execution with resumable state and an Evidence Packet per step.

## Interfaces

### §22A Dual-mode routing + mode switching

Agent orchestration uses a **dual-mode architecture**, routing by operational risk. Core principle: **Explore with AI (Exploration), Execute without AI Side Effects (Verified Path)**. See [ADR-0016](../../../adr/0016-dual-mode-agent-orchestration.md) for details.

| Mode | Scenario | Orchestration Method | Guardrails |
|---|---|---|---|
| **Exploration** | Ad-hoc Q&A, attribution analysis, data exploration, KB queries | LLM dynamically selects Skills and ordering | tool_budget=20, max_rounds=5, Permission Gate |
| **Verified Path** | Adjustment, Workflow changes, DQ Rule modifications, KB definition changes | Predefined fixed step sequence — LLM reasons within each step but cannot skip/reorder | The path itself is the guardrail; missing steps → execution rejected |

**Mode Switching**:
```
User Request → S01 IntentParser
    ├── Matches Verified Path → Force Verified Path Mode
    ├── Involves modifications (spec:write, kb:write, adjustment:create) but no matching Path → Reject execution
    └── Other → Exploration Mode (LLM free orchestration + Skill metadata hints)
```

### §22A.1 Agent Runtime Overall Architecture (Exploration Mode)

The Agent runtime uses a **Planner-Executor-Responder** three-phase pipeline, based on the ReAct (Reasoning + Acting) pattern but with security boundaries strengthened for enterprise scenarios:

```
                              ┌──────────────────────────────────────────────────────────┐
                              │                   AGENT RUNTIME                            │
                              │                                                           │
  User Query ────────────────►│  ┌──────────────────────────────────────────────────┐    │
  (NL text)                   │  │              SESSION CONTEXT (immutable)            │    │
                              │  │  tenant_id │ user_id │ role │ permissions │ caps  │    │
                              │  └──────────────────────────────────────────────────┘    │
                              │                         │                                 │
                              │                         ▼                                 │
                              │  ┌──────────────────────────────────────────────────┐    │
                              │  │              STEP 1: INTENT CLASSIFIER             │    │
                              │  │  • Fast model (Haiku/DeepSeek-Lite)                │    │
                              │  │  • Classify → route to best-matching Skill         │    │
                              │  │  • Output: { intent, entities, confidence,         │    │
                              │  │              routed_skill, fallback_skills }       │    │
                              │  └──────────────────────┬───────────────────────────┘    │
                              │                         │                                 │
                              │                         ▼                                 │
                              │  ┌──────────────────────────────────────────────────┐    │
                              │  │              STEP 2: SKILL PLANNER                 │    │
                              │  │  • Load Skill definition (tools, system prompt)    │    │
                              │  │  • Decompose intent → tool-call sequence           │    │
                              │  │  • Identify parallelizable sub-calls               │    │
                              │  │  • Output: ExecutionPlan { steps[] }               │    │
                              │  └──────────────────────┬───────────────────────────┘    │
                              │                         │                                 │
                              │                         ▼                                 │
                              │  ┌──────────────────────────────────────────────────┐    │
                              │  │         STEP 3: PERMISSION GATE (per tool-call)   │    │
                              │  │  • Role check: Is this user role authorized to call this tool?      │    │
                              │  │  • Tenant check: Do the resources the tool accesses belong within the tenant boundary?  │    │
                              │  │  • Resource check: Does column-level/row-level ACL permit access?    │    │
                              │  │  • Parameter check: Are parameters anomalous (injection/escalation)?     │    │
                              │  │  • FAIL → tool-call rejected + audit log + alert   │    │
                              │  └──────────────────────┬───────────────────────────┘    │
                              │                         │                                 │
                              │                         ▼                                 │
                              │  ┌──────────────────────────────────────────────────┐    │
                              │  │         STEP 4: PARALLEL TOOL EXECUTOR            │    │
                              │  │  • Independent tool calls → concurrent goroutines  │    │
                              │  │  • Each call → MCP server (gRPC/REST)             │    │
                              │  │  • Timeout per call: 30s (configurable)           │    │
                              │  │  • Retry: max 2 for transient errors (5xx)        │    │
                              │  └──────────────────────┬───────────────────────────┘    │
                              │                         │                                 │
                              │                         ▼                                 │
                              │  ┌──────────────────────────────────────────────────┐    │
                              │  │         STEP 5: TOOL OUTPUT SANITIZER             │    │
                              │  │  • Strip PII (if user lacks permission)           │    │
                              │  │  • Truncate >100KB outputs → summarize/paginate   │    │
                              │  │  • Validate output schema matches expected format  │    │
                              │  │  • Detect reflective injection (tool output        │    │
                              │  │    containing malicious instructions)              │    │
                              │  └──────────────────────┬───────────────────────────┘    │
                              │                         │                                 │
                              │                         ▼                                 │
                              │  ┌──────────────────────────────────────────────────┐    │
                              │  │         STEP 6: RESPONSE SYNTHESIZER              │    │
                              │  │  • Reasoning LLM (Sonnet/DeepSeek-R1)             │    │
                              │  │  • Fuse tool results → coherent answer            │    │
                              │  │  • Generate citations: [Source: KB Entry #1234]      │    │
                              │  │  • Confidence scoring per claim                   │    │
                              │  └──────────────────────┬───────────────────────────┘    │
                              │                         │                                 │
                              │                         ▼                                 │
                              │  ┌──────────────────────────────────────────────────┐    │
                              │  │         STEP 7: RESPONSE GUARD                    │    │
                              │  │  • Data leakage scan: response contains restricted │    │
                              │  │    data from tools user shouldn't access?          │    │
                              │  │  • Prompt leakage scan: system prompt fragments?   │    │
                              │  │  • Instruction injection scan: malicious guidance? │    │
                              │  │  • Confidence < 0.7 → flag with [LOW CONFIDENCE]   │    │
                              │  │  • Log to LLM Interaction Log (prompt_hash,        │    │
                              │  │    tools_called, tokens, cost, guard_results)      │    │
                              │  └──────────────────────┬───────────────────────────┘    │
                              │                         │                                 │
                              └─────────────────────────┼─────────────────────────────────┘
                                                        │
                              User Response ◄───────────┘
                              (with citations + confidence + guard warnings)
```

### §22A.2 Tool-Call Flow — Detailed Steps

| Step  | Component             | Responsibility                                                       | Input                               | Output                                                                                                  | Key Constraint                                                                                          |
| ----- | --------------------- | -------------------------------------------------------------------- | ----------------------------------- | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| **1** | Intent Classifier     | Classify user NL text into system intent, route to best Skill        | NL text                             | `{ intent: "create_report", entities: {...}, confidence: 0.92, routed_skill: "S05", fallback: ["S02"] }` | Small model (<1s); must not modify Session Context                                                      |
| **2** | Skill Planner         | Load Skill definition, decompose intent into tool-call sequence, identify parallelism opportunities | Intent + Skill Definition           | `ExecutionPlan { steps: [{tool, params, depends_on}, ...] }`                                             | Skill definition loaded from immutable registry; Plan must not contain unregistered tools                |
| **3** | Permission Gate       | Perform four-dimensional check (role/tenant/resource/params) on each tool-call | (Tool, Params, SessionContext)      | `PERMIT` or `DENY { reason, evidence }`                                                                  | **Block-before-execute** — prevent before execution; failure logged as SECURITY-level event              |
| **4** | Parallel Executor     | Execute independent tool calls concurrently                         | ExecutionPlan (filtered)            | `[{tool, result, latency, error?}, ...]`                                                                 | 30s timeout per call; max 3 retries (transient errors only); concurrency limit 8                         |
| **5** | Output Sanitizer      | Clean tool output before feeding into reasoning LLM                  | Raw tool results                    | Sanitized results (PII redaction/truncation/format validation)                                           | Redaction is irreversible; reflection injection detection is a hard block                                |
| **6** | Response Synthesizer  | Fuse tool results, reason to generate final answer with citations and confidence | Sanitized results + Session Context | `{ answer, citations[], confidence_per_claim[] }`                                                        | Reasoning model (strong model); temperature=0.3 (low creativity)                                        |
| **7** | Response Guard        | Final output security check — data leakage/prompt leakage/instruction injection/low confidence | Synthesized response                | Guarded response (may carry markers)                                                                     | Leakage detection is a hard block; low-confidence marking is a soft warning                              |

### §22A.3 ReAct Loop (Multi-Round Reasoning)

For complex queries requiring multi-round reasoning (e.g., "Why did this workflow fail? What is the impact? How to fix it?"), the Agent employs a ReAct loop:

```
┌─────────────────────────────────────────────────────────────┐
│                    ReAct LOOP (max 5 rounds)                 │
│                                                              │
│  Round 1: Thought → Act (S01 IntentParser) → Observe         │
│  Round 2: Thought → Act (S07+MCP-05) → Observe (logs/trace) │
│  Round 3: Thought → Act (S03+MCP-03) → Observe (code graph)  │
│  Round 4: Thought → Act (S04 impact analysis) → Observe      │
│  Round 5: Thought → Final Answer (synthesize)                │
│                                                              │
│  Guard: max_rounds=5, loop_timeout=300s,                    │
│         tool_call_budget=20 (hard limit to prevent runaway)  │
└─────────────────────────────────────────────────────────────┘
```

**Loop Control Parameters** (per-tenant configurable):

| Parameter              | Default | Description                                            |
| ---------------------- | ------- | ------------------------------------------------------ |
| `max_rounds`           | 5       | Maximum ReAct rounds, prevents infinite loop           |
| `loop_timeout_seconds` | 300     | Total timeout for a single query                       |
| `tool_call_budget`     | 20      | Maximum tool calls per query (hard limit)              |
| `parallelism`          | 8       | Maximum parallel tool calls in same round              |
| `confidence_threshold` | 0.6    | Claims below this confidence must be marked            |

### §22A.4 Durable Execution & Idempotency → ADR-0017

Verified Path execution follows Saga semantics. Built on existing PG + Redis — no heavyweight workflow engine needed.

**Idempotency Key**: `{path_id}_{date}_{entity_id}` — deterministically generated. Three-layer protection: Path-level (Redis `SET NX`), Step-level (Redis + PG dual-write), Skill-level (PG `ON CONFLICT DO NOTHING`).

**Persistent State**: `verified_path_executions` table records each Path instance's status / current_step / idempotency_key. `verified_path_step_events` table records forward/compensation events per step with an `evidence_packet JSONB` field (see below). After Agent Runtime crash restart, resumes from `current_step` — before each step, checks idempotency key and skips if already completed.

**Evidence Packet (Decision Evidence Package)**: After each Step involving LLM reasoning completes, the Agent writes a structured decision record in `verified_path_step_events.evidence_packet`:

```json
{
  "query": "What type does this Recon break belong to?",
  "context_snapshot": {
    "citations": ["source_a", "source_b"],
    "historical_patterns": ["pat_1"],
    "retrieved_kb_entries": ["kb_entry_42"]
  },
  "decision": "TIMING",
  "confidence": 0.87,
  "alternatives_considered": [
    {"option": "MISSING", "reason_rejected": "Date difference between both systems <3 days"}
  ],
  "human_reviewed": true,
  "reviewer_id": "usr_123"
}
```

The Evidence Packet is an evidence snapshot at the moment of decision — even if the KB is subsequently modified, audit retrospectives see the evidence state at decision time. This aligns with SOX audit requirements: proving that decisions were made on reasonable evidence at the time, not proving that decisions were forever correct.

**DLQ (Dead Letter Queue)**: After 3 compensation retries (exponential backoff 1s→2s→4s) still fail → write to `dlq_entries` table → create Incident → escalate to Data Owner. Manual cleanup of residuals then manual resolve.

### §22A.5 Multi-Model Support

#### Model Registry Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     MODEL REGISTRY                            │
│                                                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ ModelInterface   │  │ ModelInterface   │  │ModelInterface│ │
│  │ (OpenAI)         │  │ (Anthropic)      │  │ (DeepSeek)   │ │
│  │ • GPT-4o         │  │ • Claude Sonnet  │  │ • DeepSeek-V3│ │
│  │ • GPT-4o-mini    │  │ • Claude Haiku   │  │ • DeepSeek-R1│ │
│  └────────┬─────────┘  └────────┬─────────┘  └──────┬───────┘ │
│           │                     │                    │         │
│           └─────────────────────┼────────────────────┘         │
│                                 │                              │
│  ┌─────────────────┐           │           ┌──────────────┐   │
│  │ ModelInterface   │           │           │ModelInterface│   │
│  │ (Local/vLLM)     │           │           │ (Custom)     │   │
│  │ • Llama-3.1-70B  │           │           │ • BYO Model  │   │
│  │ • Qwen-2.5-72B   │           │           │ • gRPC adapt │   │
│  └────────┬─────────┘           │           └──────┬───────┘   │
│           └─────────────────────┼──────────────────┘           │
│                                 ▼                              │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │              MODEL ROUTER (selection logic)               │ │
│  │  • Task Type: classification→Haiku/Lite, reasoning→Sonnet│ │
│  │  • Data Sensitivity: T3→local only, T2→private SaaS      │ │
│  │  • Cost Budget: tenant monthly cap → downgrade if near   │ │
│  │  • Failover: primary→secondary→tertiary chain            │ │
│  └──────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

> **Model Validation Constraint**: Each Skill declares its validated model list. Tenants can only select from validated models — arbitrary model selection is not supported. The complete multi-model support matrix (per-Skill × per-Provider) is continuously validated through Prompt regression test suites; when behavioral differences are detected, the model is marked as 'degraded' for that Skill.

#### ModelInterface (Abstract Interface)

Each model adapter implements a unified interface:

```
ModelInterface {
    // Core
    ChatCompletion(messages, tools?, tool_choice?, temperature, max_tokens) → ChatResponse
    EmbedText(text) → Vector

    // Metadata
    Capabilities() → { max_context_window, supports_tools, supports_vision, supports_streaming }
    CostPerToken() → { input_per_1k, output_per_1k }

    // Health
    HealthCheck() → { status, latency_p50, error_rate_5m }
}
```

#### Model Selection Logic

| Selection Dimension | Rule                                                                                                     | Example                                                                                  |
| ------------------- | -------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| **Task Type**       | Simple tasks (intent classification, keyword extraction, format validation) → small model; complex reasoning (impact analysis, root cause diagnosis, code review) → large model | S01 IntentParser → Haiku/DeepSeek-Lite; S04 ImpactAnalyzer → Sonnet/DeepSeek-R1          |
| **Data Sensitivity**| T3 (Restricted: PII/financial details) → local model only; T2 (Confidential) → private SaaS or local; T0-T1 → any                | Dev debugging (access logs, T1) → SaaS model OK; Business User querying customer details (T3) → local model only |
| **Cost Budget**      | Tenant monthly LLM budget → real-time consumption tracking → auto-downgrade to smaller/cheaper model at ~80% → local model only at 100%          | Tenant A $500/month → auto-downgrade from Sonnet to Haiku at $400 → DeepSeek-Lite only at $500         |
| **Latency Requirements**| Real-time interaction (<3s) → small model preferred; background analysis (<60s) → large model acceptable                                                  | Conversation UI → Haiku; Nightly Impact Report generation → Sonnet                                |
| **Failover**         | Primary model unavailable → auto failover chain: same provider alternate → cross-provider alternate → local model fallback                               | Sonnet unavailable → GPT-4o → DeepSeek-R1 → Local Llama                                       |

#### Tenant-Level Model Preference

| Configuration Level | Description | Example |
| ------------------- | ----------- | ------- |
| **Tenant Level** | Tenant default model policy | `default: { primary: "claude-sonnet", pii_model: "local-llama", budget: 500 }` |
| **Group Level** | Override tenant default (optional) | Finance Group `{ primary: "gpt-4o" }`; Engineering Group `{ primary: "claude-sonnet" }` |
| **User Level** | Personal preference (optional, constrained by tenant) | `{ preference: "claude-haiku" }` (but cannot override tenant PII policy) |

### §22A.6 Hierarchical Multi-Agent Architecture (Evolution Direction, Phase 7+)

> During the MVP phase, maintain the current flat catalog of 18 Skills (S01-S18). Phase 7+ evolves into a Central Reasoner + Sub-Agent layered architecture, aligned with Monte Carlo's 2025-2026 production architecture.

```
                          ┌─────────────────────────────────────┐
                          │     Central "Brain" Reasoner         │
                          │  (Comprehensive Reasoning Model: Sonnet/DeepSeek-R1)  │
                          └──────────────┬──────────────────────┘
                                         │
              ┌──────────────────────────┼──────────────────────────┐
              │                          │                          │
              ▼                          ▼                          ▼
    ┌─────────────────┐    ┌─────────────────────┐    ┌─────────────────────────┐
    │ Sub-Agent 1     │    │ Sub-Agent 2          │    │ Sub-Agent 3             │
    │ Pipeline Change │    │ Data Anomaly         │    │ Infrastructure          │
    │ Investigator    │    │ Investigator         │    │ Investigator            │
    ├─────────────────┤    ├─────────────────────┤    ├─────────────────────────┤
    │ • PR diffs      │    │ • Volume anomalies   │    │ • Compute metrics       │
    │ • dbt changes   │    │ • Freshness issues   │    │ • Network health        │
    │ • Spec diffs    │    │ • Schema changes     │    │ • Credential validity   │
    │ • Commit history│    │ • Distribution shift │    │ • Sandbox status        │
    │ • Config changes│    │ • Field-level stats  │    │ • CDC pipeline lag      │
    └────────┬────────┘    └──────────┬──────────┘    └──────────┬──────────────┘
             │                       │                           │
             └───────────────────────┼───────────────────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    ▼                                 ▼
          ┌─────────────────────┐        ┌─────────────────────────┐
          │ Sub-Agent 4         │        │ Sub-Agent 5             │
          │ Upstream Dependency │        │ Historical Pattern      │
          │ Investigator        │        │ Matcher                 │
          ├─────────────────────┤        ├─────────────────────────┤
          │ • Source system     │        │ • Similar past incidents│
          │   availability      │        │ • Known false-positive  │
          │ • Ingestion lag     │        │   patterns              │
          │ • API rate limits   │        │ • Seasonal baselines    │
          │ • Schema drift      │        │ • Past resolution paths │
          └─────────────────────┘        └─────────────────────────┘

  All Sub-Agents run in parallel → Central Reasoner synthesizes → outputs unified diagnosis
```

**Relationship with MVP Flat Skill Catalog**: In Phase 7+, the MVP's 18 Skills (S01-S18) become the underlying tool library for Sub-Agents. The Central Reasoner calls Sub-Agents, and Sub-Agents call existing Skills.

**Introduction Criteria** (Three-Gate Condition):
1. Alert volume reaches critical scale (daily average >50 warnings)
2. S07 single-Agent diagnostic accuracy <70% (requires division of labor to improve)
3. Flat orchestration ReAct loops exceed 5 rounds without locating root cause

## Dependencies

- **Skill catalog** ([`skill-catalog.md`](skill-catalog.md), §22B) — the runtime loads Skill definitions (tools, system prompt, orchestration metadata) from the immutable registry; Skills S01–S18 are the building blocks of both Exploration-Mode orchestration and Verified Path steps.
- **MCP catalog** ([`mcp-catalog.md`](mcp-catalog.md), §22C) — tool calls in Step 4 (Parallel Tool Executor) reach MCP backends through the MCP Gateway.
- **Agent security** ([`agent-security.md`](agent-security.md), §22D) — the Permission Gate (Step 3) is one boundary within Layer 2; the Tool Output Sanitizer (Step 5) is Layer 3; the Response Guard (Step 7) is Layer 4; the Sandbox (Layer 7) hosts the runtime.
- **Platform core** ([`platform-core`](../platform-core/)) — the Auth/Entitlement service resolves Session Context and the four Permission-Gate dimensions; Redis (Path/Step idempotency); PostgreSQL (`verified_path_executions`, `verified_path_step_events`, `dlq_entries`, `ON CONFLICT DO NOTHING`); Audit Trail and Incident Manager for DLQ escalation.
- **Knowledge services** ([`knowledge-services`](../knowledge-services/)) — KB retrieval and Code Graph queries issued by Skills during reasoning.
- **Workflow engine** ([`workflow-engine`](../workflow-engine/)) — the production Jobs the Agent ultimately invokes (especially in Verified Path steps).
- **Model providers** — OpenAI / Anthropic / DeepSeek / local-vLLM / custom adapters behind the ModelInterface.

## Data Model

- **Session Context (immutable)** — `{ tenant_id, user_id, role, permissions, caps }`, established once per query and read by every step; never mutated by the Intent Classifier or any downstream step (§22A.1/§22A.2 key constraint).
- **ExecutionPlan** — `{ steps: [{ tool, params, depends_on }, ...] }` produced by the Skill Planner; must not contain unregistered tools (§22A.2).
- **`verified_path_executions`** — one row per Verified Path instance: `status`, `current_step`, `idempotency_key`; the resumption point after crash restart (§22A.4).
- **`verified_path_step_events`** — forward/compensation events per step, including the `evidence_packet JSONB` field holding the decision evidence package shown above.
- **`dlq_entries`** — residuals after 3 failed compensation retries (exponential backoff 1s→2s→4s); triggers Incident creation and Data Owner escalation (§22A.4).
- **LLM Interaction Log entry** — `{ prompt_hash, tools_called, tokens, cost, guard_results }` written by Step 7 (Response Guard) for every query.

## Failure Modes & Recovery

| Failure | Impact | Detection | Recovery |
| ------- | ------ | --------- | -------- |
| **Runaway ReAct loop / DoW (Denial of Wallet)** | Infinite reasoning consumes LLM budget | Hard limits: `max_rounds=5`, `loop_timeout_seconds=300`, `tool_call_budget=20` (§22A.3) | Loop terminated at hard limit; partial results returned (if any) + timeout notification; FLAG + notify tenant Admin if single query > 50K tokens |
| **Un-pathed modification request** | Unauthorized state mutation | Mode Switching rule: modification intent (`spec:write`/`kb:write`/`adjustment:create`) with no matching Verified Path (§22A) | Execution rejected before any tool call |
| **Permission Gate denial** | Unauthorized tool call attempted | Four-dimensional check (role/tenant/resource/params) — **block-before-execute** (§22A.2 Step 3) | `DENY { reason, evidence }`; SECURITY-level audit log + alert; denial-storm (>5/min) throttles the session |
| **Agent Runtime crash mid-Verified-Path** | Partial execution, possible duplicate side effects | Crash; on restart, resume from `current_step` (§22A.4) | Three-layer idempotency key `{path_id}_{date}_{entity_id}` (Redis `SET NX`, Redis+PG dual-write, PG `ON CONFLICT DO NOTHING`); completed steps skipped |
| **Compensation failure** | Residual inconsistent state | 3 compensation retries fail (exponential backoff 1s→2s→4s) | Write to `dlq_entries` → create Incident → escalate to Data Owner → manual cleanup + manual resolve |
| **Primary model unavailable** | Reasoning/Tool selection stalls | ModelInterface `HealthCheck()` (§22A.5) | Auto failover chain: same-provider alternate → cross-provider alternate → local model fallback |
| **Tenant cost budget exhaustion** | Bill shock | Real-time consumption tracking (~80% downgrade, 100% local-only) | Auto-downgrade to smaller/cheaper model; at 100% force local model only |
| **Reflection injection via tool output** | Malicious tool data steers the LLM | Tool Output Sanitizer reflection-injection scan (§22A.2 Step 5) | Hard block — output fragment removed/replaced with `[FILTERED]`; SECURITY-level log |
| **Data leakage in synthesized response** | Restricted data exfiltrated to user | Response Guard data-leakage scan (§22A.2 Step 7) | Hard block — response withheld and replaced with filtering notice + security log |

## Non-Functional Requirements

- **Dual-mode by construction** — Exploration is bounded (`tool_budget=20`, `max_rounds=5`, Permission Gate); Verified Path is a fixed-step sequence the LLM cannot skip or reorder (the path itself is the guardrail) (§22A).
- **Block-before-execute** — every Permission Gate denial occurs *before* the tool runs, not as post-hoc audit (§22A.2 Step 3).
- **Sub-second intent classification** — the Intent Classifier uses a small model and must complete in < 1s without mutating Session Context (§22A.2 Step 1).
- **Concurrency limit 8** — the Parallel Tool Executor caps concurrent tool calls at 8, with 30s timeout per call and max 3 retries for transient (5xx) errors (§22A.2 Step 4).
- **Irreversible redaction** — Tool Output Sanitizer redaction is one-way before data enters the LLM context; reflection-injection detection is a hard block (§22A.2 Step 5).
- **Low-creativity synthesis** — the Response Synthesizer runs at `temperature=0.3` on a strong reasoning model (§22A.2 Step 6).
- **Durable / resumable Verified Path** — Saga semantics on PG + Redis (no heavyweight workflow engine); crash-restart resumes from `current_step` with three-layer idempotency (§22A.4).
- **Validated-models-only** — tenants may only select models each Skill has validated; the per-Skill × per-Provider matrix is continuously regression-tested and degraded models are marked (§22A.5).
- **Per-tenant loop control** — `max_rounds`, `loop_timeout_seconds`, `tool_call_budget`, `parallelism`, `confidence_threshold` are all per-tenant configurable (§22A.3).
- **Phase 7+ gated evolution** — the hierarchical Central Reasoner + Sub-Agent architecture is introduced only when the three-gate condition is met (>50 daily warnings, S07 accuracy <70%, ReAct >5 rounds without root cause) (§22A.6).

## Key Flows

### Exploration-Mode query (7-step pipeline, §22A.1 / §22A.2)

```
User Query + Session Context
  → Step 1 Intent Classifier (small model, route to Skill)
  → Step 2 Skill Planner (decompose → ExecutionPlan, identify parallelism)
  → Step 3 Permission Gate (4-dim check per tool-call, block-before-execute)
  → Step 4 Parallel Tool Executor (concurrency 8, 30s timeout, ≤3 retries)
  → Step 5 Tool Output Sanitizer (PII redaction, truncation, reflection-injection block)
  → Step 6 Response Synthesizer (strong model, temperature=0.3, citations + per-claim confidence)
  → Step 7 Response Guard (data/prompt leakage + instruction injection + confidence flag)
  → User Response (citations + confidence + guard warnings)
```

### ReAct loop (multi-round, §22A.3)

```
Round 1: Thought → Act (S01 IntentParser) → Observe
Round 2: Thought → Act (S07+MCP-05) → Observe (logs/trace)
Round 3: Thought → Act (S03+MCP-03) → Observe (code graph)
Round 4: Thought → Act (S04 impact analysis) → Observe
Round 5: Thought → Final Answer (synthesize)
```
Guarded by `max_rounds=5`, `loop_timeout=300s`, `tool_call_budget=20` (hard limit).

### Verified Path execution (Saga, §22A.4)

```
verified_path_id + params
  → Idempotency key {path_id}_{date}_{entity_id}
    (Path-level Redis SET NX → Step-level Redis+PG dual-write → Skill-level PG ON CONFLICT DO NOTHING)
  → Per step: execute → record event in verified_path_step_events (with evidence_packet JSONB)
  → On crash: resume from current_step (skip completed via idempotency key)
  → On compensation failure (3 retries, 1s→2s→4s): dlq_entries → Incident → Data Owner
```

### Shared runtime sequence

The full end-to-end Agent query — from USER submitting a natural-language question, through the Conversation Interface forwarding to the Agent, intent parsing, Permission-Gated tool calls against Code Graph / KB Vector / KB Relational / Log Store, the Output Guard, and Citation building — is documented in [`../_shared/sequence-diagrams.md`](../_shared/sequence-diagrams.md) **§21.3 AI Agent Query with Permission Gating**. That sequence is the canonical reference for the §22A.1 Exploration-Mode pipeline (Steps 1–7) and is co-owned with [`knowledge-services`](../knowledge-services/) (Code Graph, KB Vector/Relational) and [`platform-core`](../platform-core/) (Auth, Log Store).

## Design References

- **Original sections**: §22A (Agent SDK Architecture — Dual-Mode Orchestration), §22A.1 (Agent Runtime Overall Architecture — Exploration Mode), §22A.2 (Tool-Call Flow — Detailed Steps), §22A.3 (ReAct Loop — Multi-Round Reasoning), §22A.4 (Durable Execution & Idempotency), §22A.5 (Multi-Model Support: Model Registry, ModelInterface, Model Selection Logic, Tenant-Level Model Preference), §22A.6 (Hierarchical Multi-Agent Architecture — Phase 7+) of [`docs/03-architecture.md`](../../03-architecture.md).
- **Related agent-platform docs**: [`skill-catalog.md`](skill-catalog.md) (§22B — the Skills invoked by the runtime), [`mcp-catalog.md`](mcp-catalog.md) (§22C — tool backends), [`agent-security.md`](agent-security.md) (§22D — Permission Gate = Layer 2, Output Sanitizer = Layer 3, Response Guard = Layer 4, Sandbox = Layer 7), [`exploration-runtime.md`](exploration-runtime.md) (§3.1–§3.5 — the UI that drives Exploration Mode).
- **Shared sequence diagram**: [`../_shared/sequence-diagrams.md`](../_shared/sequence-diagrams.md) §21.3 AI Agent Query with Permission Gating (primary sub-project).
- **ADRs** ([index](../../adr-index.md)): [ADR-0016 Dual-Mode Agent Orchestration](../../../adr/0016-dual-mode-agent-orchestration.md) (Exploration vs Verified Path), [ADR-0017 Verified Path Saga Semantics](../../../adr/0017-verified-path-saga-semantics.md) (durable execution, three-layer idempotency, Evidence Packet, DLQ), [ADR-0020 Agent Cost Governance](../../../adr/0020-agent-cost-governance.md) (cost-budget-driven model downgrade), [ADR-0021 VP Promotion & Concurrency](../../../adr/0021-vp-promotion-concurrency.md) (Verified Path promotion and multi-agent concurrency), [ADR-0019 Agent Memory Architecture](../../../adr/0019-agent-memory-architecture.md) (memory feeding the ReAct loop).
- **Glossary** ([../../glossary.md](../../glossary.md)): Exploration Mode, Verified Path, ReAct Loop, Permission Gate, Session Context, ExecutionPlan, Idempotency Key, Evidence Packet, DLQ, Model Registry, ModelInterface, Sub-Agent.
- **Cross-references retained from source**: §22B (Skill catalog), §22C (MCP catalog), §22D (7-layer defense), §22I/§22J (memory + evaluation feeding the runtime), §22K (cost governance), ADR-0016/0017 (mode switching + Saga semantics).
