# Exploration Environment

> **Origin**: §3.1, §3.2, §3.4, §3.5 of [`docs/03-architecture.md`](../../03-architecture.md) | **Sub-project**: [agent-platform](README.md)

## Purpose

This module covers the **Exploration Environment** — the interactive UI and reasoning layer where users explore, design, and test. Per §3.1, all artifacts produced here are "design drafts" and produce **no production side effects**. It is the front door for natural-language interaction with the Agent Platform, the visual authoring surface for Specs/Formats, and the primary attack surface for prompt injection (hence the dedicated guard pipeline in §3.2).

This module owns:
- **§3.1 Exploration Environment in Detail** — the five-component overview table (Conversation Interface, Visual Designer, Workbench, AI Copilot Engine, Light Compute Engine).
- **§3.2 Conversation Interface — Prompt Injection Defense** — the six-layer defense pipeline (Input Sanitization, Instruction Boundary, KB Content Sanitization, RBAC Context Injection, Output Guard, Audit) that every user input must pass before reaching any LLM.
- **§3.4 Workbench — VCS Integration** — the Git-worktree-backed authoring surface (Session = Branch, Diff Preview, PR Workflow, Conflict Resolution, History).
- **§3.5 Exploration Environment — Detailed Component Architecture** — the detailed sub-components of Conversation Interface (Intent Parser, Context Resolver, Plan Generator, Artifact Builder), Visual Designer (Report Designer, ETL Designer, Adjustment Form Builder), and AI Copilot Engine (Provider Plugin, KB Retriever, Reasoning Engine, Feedback Loop).

## Boundaries

**In-scope:**
- §3.1 — the Exploration Environment component roster and the principle that all outputs are non-productive design drafts.
- §3.2 — the six-layer Prompt Injection Defense pipeline that wraps every LLM call originating from the Conversation Interface (Input Sanitization, Instruction Boundary, KB Content Sanitization, RBAC Context Injection, Output Guard, Audit).
- §3.4 — the Workbench as a VCS-integrated workspace: Session = Branch, structured auto-commits, rich Diff Preview, Freeze-triggered PR workflow, Git merge-conflict resolution, and `git log` timeline view.
- §3.5 Conversation Interface sub-components — Intent Parser, Context Resolver (hybrid KB search), Plan Generator, Artifact Builder.
- §3.5 Visual Designer sub-components — Report Designer, ETL Designer, Adjustment Form Builder (including the Adjustment Submission Pipeline and its core principles).
- §3.5 AI Copilot Engine sub-components — Provider Plugin, KB Retriever (hybrid search + future pluggable VectorStore/GraphStore), Reasoning Engine, Feedback Loop.

**Delegated / out-of-scope:**
- The Design Artifact YAML schema (the handoff contract with `fuzzy_nodes`/`confirmed_fields`/`confidence_summary`) → `design-artifact.md` in [`workflow-engine`](../workflow-engine/) (§3.3).
- The Light Compute Engine internals (DuckDB + Polars) → [`query-serving`](../query-serving/).
- KB storage backends (PostgreSQL + pgvector, future Milvus/Neo4j) → [`knowledge-services`](../knowledge-services/).
- The deeper 7-layer Agent defense (this module's §3.2 is the input-side subset) → [`agent-security.md`](agent-security.md) (§22D).
- Production workflow execution and Freeze → [`workflow-engine`](../workflow-engine/).
- RBAC entitlement enforcement at the tool boundary → [`platform-core`](../platform-core/).

**Upstream/downstream neighbors:**
- *Input*: user natural language, drag-and-drop canvas edits, Adjustment Form submissions, and (via OCR/Email ingestion) unstructured documents.
- *Output*: Design Artifact (YAML) handed to the Freeze Pipeline; KB entry proposals and Feedback Loop signals captured back into the KB.

## Interfaces

### §3.1 Exploration Environment — component roster

Users explore, design, and test within the Exploration Environment; all artifacts are "design drafts" and produce no production side effects.

| Component | Responsibility |
| -------------------------- | ------------------------------------------------------------------------------------------- |
| **Conversation Interface** | Natural language interaction: Intent Parser → Context Resolver (KB retrieval) → Plan Generator → Artifact Builder |
| **Visual Designer** | Report Designer / ETL Designer / Adjustment Designer; produces Design Artifact (YAML) |
| **Workbench** | Core operation interface integrating conversation + visualization + data preview; Session = Project |
| **AI Copilot Engine** | Pluggable LLM Provider + KB Retriever + Reasoning Engine; all output is advisory with confidence scores |
| **Light Compute Engine** | DuckDB + Polars; sub-second startup, sampled data, real-time preview |

### §3.2 Conversation Interface — Prompt Injection Defense

The Conversation Interface is the primary attack surface for prompt injection. All user input passes through a multi-layer defense pipeline before reaching any LLM:

| Layer                       | Mechanism                                                                                                                                                                                                                             |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Input Sanitization**      | Strip control characters, normalize Unicode, reject inputs exceeding 32KB.                                                                                                                                                            |
| **Instruction Boundary**    | User input is wrapped in a delimited block (`<user_input>…</user_input>`); system instructions are in a separate, immutable block. The LLM is instructed to treat user content as data, never as commands.                            |
| **KB Content Sanitization** | When KB entries are created (especially via AI extraction and Email ingestion paths), scan content for instruction-following patterns ('ignore previous', 'you are now', 'instead you should', etc.) and mark for quarantine or stripping. OCR-extracted image text also undergoes injection detection before entering LLM context. |
| **RBAC Context Injection**  | The caller's role, tenant, and permission set are injected as non-overridable system context before every LLM call.                                                                                                                   |
| **Output Guard**            | LLM responses are scanned for: (a) attempts to emit system prompts, (b) instruction-following language directed at the system, (c) code that would execute outside the Sandbox. Suspicious outputs are flagged, stripped, and logged. |
| **Audit**                   | Every LLM interaction is logged to the LLM Interaction Log with prompt_hash, retrieved KB context, and guard trigger events.                                                                                                          |

### §3.4 Workbench — VCS Integration

The Workbench is the primary authoring surface — a Version Control System (VCS) integrated workspace. Every session is backed by a Git worktree:

| Integration Point       | Mechanism                                                                                                                                       |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| **Session = Branch**    | Each Workbench session creates a feature branch from `main`. All edits (Spec, KB, Format) are auto-committed with structured messages.          |
| **Diff Preview**        | Before Freeze, the Workbench renders a rich diff (Spec + Impact Graph + Data Preview) against the base branch.                                  |
| **PR Workflow**         | Freeze triggers PR creation. The Workbench embeds the PR conversation, CI status, and review checklist inline.                                  |
| **Conflict Resolution** | Concurrent edits to the same artifact are detected via Git merge conflicts. The Workbench provides a side-by-side merge editor with KB context. |
| **History**             | Full `git log` is exposed as a timeline view: who changed what, when, and why (linked to BRD/ADR/Incident).                                     |

### §3.5 Conversation Interface — detailed architecture

```
User Message → Intent Parser → Context Resolver → Plan Generator → Artifact Builder
                   │                │                  │
                   ▼                ▼                  ▼
              Intent Catalog   KB Retriever      Compute Spec
              (50+ intents)   (Vector+Graph)     Template Library
```
- **Intent Parser**: Classifies user intent (new_report, modify_filter, add_quality_check, explain_lineage, …) using a fine-tuned classifier backed by the Intent Catalog.
- **Context Resolver**: Retrieves relevant KB entries (Business Glossary terms, Data Catalog columns, Mapping Registry entries) via hybrid search (semantic + keyword + graph expansion).
- **Plan Generator**: Produces a structured plan (sequence of Spec edits) from intent + context, rendered for user confirmation before any artifact is touched.
- **Artifact Builder**: Executes the confirmed plan by mutating the Design Artifact YAML; each mutation is a discrete, undoable operation.

### §3.5 Visual Designer — sub-components

- **Report Designer**: Drag-and-drop canvas for layout (header, table, chart, KPI card, paragraph). Binds to DataSource columns via Data Catalog. Generates Format definitions in the Design Artifact.
- **ETL Designer**: Node-edge canvas mirroring the Code Graph. Drag a DataSource node → auto-generates `source` Job. Connect nodes → generates `depends_on`. Each node has a property panel for type-specific configuration.
- **Adjustment Form Builder**: Developer or Admin defines the Adjustment Form (column definitions, validation rules, approval chains) and produces the Form Definition YAML. Business Users submit via Web UI, download and fill an Excel file then upload/import, or submit via API — all three go through the same pipeline:

```
Adjustment Submission Pipeline:
  Permission → Validation → Approval → Trigger ETL (SDLC-defined Workflow)
```

Core Principles:
- **Validation before Approval** — an approver must never review a form that fails validation
- **Any operation that modifies financial data, regardless of amount, must go through this pipeline — there is no Auto-write-off**
- **Approval chain is configurable** (four-eyes principle / dual approval by amount threshold / no approval) to meet different team needs
- **Repeat Adjustment**: Scheduled preset Adjustments (amounts can be pre-filled), approval path can be simplified (auto-approve if amount stays within historical range)
- **Daily Manual Adjustment**: Event-driven blank form, full approval chain

### §3.5 AI Copilot Engine — sub-components

- **Provider Plugin**: OpenAI / Anthropic / open-source / private — configured per tenant. All calls go through the same guard pipeline (§3.2).
- **KB Retriever**: Hybrid search across PostgreSQL + pgvector (semantic vector search via HNSW), PG recursive CTE (graph expansion), and native SQL (exact metadata match). Results are fused and ranked before injection. Future: dedicated engines (Milvus/Neo4j) via same VectorStore/GraphStore interfaces — no query logic changes.
- **Reasoning Engine**: Chain-of-thought reasoning scoped to the retrieved KB context. Produces structured suggestions (Spec diffs, KB entry proposals, quality rule suggestions) with per-field confidence scores.
- **Feedback Loop**: User corrections are captured and used to fine-tune the Intent Parser and ranking model (within tenant boundary; no cross-tenant training).

## Dependencies

- **Knowledge services** ([`knowledge-services`](../knowledge-services/)) — KB Retriever and Context Resolver depend on the Business Glossary, Data Catalog, Mapping Registry, and the Code Graph; the hybrid search stack (pgvector / recursive CTE / SQL) and the future Milvus/Neo4j backends are owned there.
- **Query serving** ([`query-serving`](../query-serving/)) — the Light Compute Engine (DuckDB + Polars) and sampled-data previews.
- **Workflow engine** ([`workflow-engine`](../workflow-engine/)) — the Design Artifact schema (§3.3), the Compute Spec template library, and the Freeze Pipeline that consumes design drafts.
- **Platform core** ([`platform-core`](../platform-core/)) — RBAC/entitlement service that resolves the role/tenant/permission context injected before every LLM call, plus Audit Trail, Notification, and the LLM Interaction Log sink.
- **Agent security** ([`agent-security.md`](agent-security.md)) — §3.2 is the input-side subset of the §22D 7-layer defense; the Conversation Interface's guard pipeline is the "immune system first line of defense."

## Data Model

The Exploration Environment's primary data product is the **Design Artifact (YAML)** — the handoff contract between the Exploration Environment and Freeze Pipeline. It carries the intended specification plus the AI's uncertainty per element. The schema (including `fuzzy_nodes`, `confirmed_fields`, `confidence_summary`) is owned by [`workflow-engine` `design-artifact.md`](../workflow-engine/design-artifact.md) (§3.3); key fields recapitulated here for context:

| Field                | Purpose                                                                                                                                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `fuzzy_nodes`        | Nodes the AI could not deterministically resolve. Each carries a `marker` type, `confidence` score, and optional `proposed_resolution`. Freeze Pipeline rejects any artifact with unresolved fuzzy nodes. |
| `confirmed_fields`   | Nodes explicitly confirmed by a human user. Freeze Pipeline treats these as authoritative, skipping AI re-evaluation.                                                                                     |
| `confidence_summary` | Aggregate scores used by Freeze Pipeline to decide required review depth. Artifacts with `overall < 0.8` mandate full peer review.                                                                        |

Additional data structures owned or produced by this module:
- **Intent Catalog** — 50+ predefined intents (see Interfaces §3.5) backing the Intent Parser.
- **Form Definition YAML** — produced by the Adjustment Form Builder (column definitions, validation rules, approval chains).
- **LLM Interaction Log entries** — per §3.2 Audit, each entry carries `prompt_hash`, retrieved KB context, and guard trigger events.

## Failure Modes & Recovery

| Failure | Impact | Detection | Recovery |
| ------- | ------ | --------- | -------- |
| **Prompt injection breaks the instruction boundary** | LLM treats user content as commands | §3.2 guard pipeline — Instruction Boundary + Output Guard + injection-pattern scan | Suspicious output flagged, stripped, and logged; logged to LLM Interaction Log with guard events |
| **Malicious KB content injected into context** | Adversarial KB entry steers the LLM | §3.2 KB Content Sanitization (quarantine/strip on ingestion; OCR text also scanned) | Affected KB entry quarantined; Content re-reviewed before re-entering LLM context |
| **Input exceeds 32KB / control chars / homoglyphs** | DoS or encoding-based bypass | §3.2 Input Sanitization (32KB cap, Unicode NFC normalization, control-char strip) | Truncated with user notification; malformed input rejected |
| **Hybrid search returns irrelevant context** | Low-quality suggestions, low confidence scores | `confidence_summary.overall < 0.8` | Auto-prompt for deep review; user corrections captured via Feedback Loop to re-rank |
| **Concurrent Workbench edits collide** | Lost updates on the same artifact | Git merge conflicts (Session = Branch) | Side-by-side merge editor with KB context; structured re-commit |
| **LLM provider unavailable** | Copilot suggestions fail | Provider Plugin health check | Per-tenant failover chain (see `dual-mode-orchestration.md` §22A.5); advisory output degrades gracefully (non-blocking) |
| **Adjustment Form fails validation post-approval** | Bad data would reach production | "Validation before Approval" principle — approver never sees an invalid form | Form rejected at Validation stage; submitter must correct and resubmit |

## Non-Functional Requirements

- **Sub-second startup** — the Light Compute Engine (DuckDB + Polars) must come up in under one second for real-time preview on sampled data (§3.1).
- **Non-productive by construction** — all Exploration Environment artifacts are design drafts with zero production side effects (§3.1). Production writes only occur after Freeze + canary rollout (owned by [`workflow-engine`](../workflow-engine/)).
- **Tenant isolation for learning** — the Feedback Loop fine-tunes the Intent Parser and ranking model strictly within the tenant boundary; cross-tenant training is prohibited (§3.5).
- **Per-tenant LLM provider** — the Provider Plugin is configured per tenant; every call goes through the same §3.2 guard pipeline regardless of provider (§3.5).
- **Advisory-only AI output** — all Copilot output carries confidence scores and is advisory; nothing auto-publishes (§3.1, §3.5).
- **Pluggable retrieval backends** — the KB Retriever must allow swapping PostgreSQL+pgvector for dedicated Milvus/Neo4j engines via the same VectorStore/GraphStore interfaces with no query-logic changes (§3.5).
- **Input bound (32KB)** and **control-character / Unicode normalization** enforced on every user message (§3.2).
- **Immutable audit** — every LLM interaction logged with `prompt_hash`, retrieved KB context, and guard trigger events (§3.2).

## Key Flows

### Conversation Interface request flow (§3.5)

```
User Message → Intent Parser → Context Resolver → Plan Generator → Artifact Builder
```
1. **Intent Parser** classifies the message against the 50+-intent Intent Catalog.
2. **Context Resolver** retrieves relevant KB entries via hybrid search (semantic + keyword + graph expansion).
3. **Plan Generator** produces a structured plan (sequence of Spec edits), rendered for user confirmation.
4. **Artifact Builder** executes the confirmed plan by mutating the Design Artifact YAML, one discrete undoable operation per mutation.

Every step's LLM call is wrapped by the §3.2 six-layer guard pipeline (Input Sanitization → Instruction Boundary → KB Content Sanitization → RBAC Context Injection → Output Guard → Audit).

### Adjustment Submission flow (§3.5 Visual Designer)

```
Permission → Validation → Approval → Trigger ETL (SDLC-defined Workflow)
```
All three submission channels (Web UI, Excel upload/import, API) converge on the same pipeline. Core principle: Validation before Approval; no Auto-write-off for financial data regardless of amount.

### Workbench authoring flow (§3.4)

1. New session → feature branch off `main` (Session = Branch); all edits auto-committed with structured messages.
2. Author via Conversation Interface + Visual Designer; live preview via Light Compute Engine.
3. Before Freeze → rich Diff Preview (Spec + Impact Graph + Data Preview) against base branch.
4. Freeze → PR creation; Workbench embeds PR conversation, CI status, review checklist inline.
5. Conflicts → side-by-side merge editor with KB context.
6. History → `git log` timeline view (who/what/when/why, linked to BRD/ADR/Incident).

### Shared runtime sequence

The end-to-end Agent query flow — from USER submitting a natural-language question, through the Conversation Interface forwarding to the Agent, intent parsing, Permission-Gated tool calls against Code Graph / KB Vector / KB Relational / Log Store, the Output Guard, and Citation building — is documented in [`../_shared/sequence-diagrams.md`](../_shared/sequence-diagrams.md) **§21.3 AI Agent Query with Permission Gating**. That sequence is the canonical reference for the Conversation Interface → AI Copilot Engine interaction and is co-owned with [`knowledge-services`](../knowledge-services/) (Code Graph, KB Vector/Relational) and [`platform-core`](../platform-core/) (Auth, Log Store).

## Design References

- **Original sections**: §3.1 (Exploration Environment in Detail), §3.2 (Conversation Interface — Prompt Injection Defense), §3.4 (Workbench — VCS Integration), §3.5 (Exploration Environment — Detailed Component Architecture) of [`docs/03-architecture.md`](../../03-architecture.md).
- **Related agent-platform docs**: [`agent-security.md`](agent-security.md) (§22D — the full 7-layer defense of which §3.2 is the input-side subset), [`dual-mode-orchestration.md`](dual-mode-orchestration.md) (§22A — the Agent runtime invoked by the Conversation Interface), [`skill-catalog.md`](skill-catalog.md) (§22B — S01 IntentParser etc.), [`mcp-catalog.md`](mcp-catalog.md) (§22C — the MCP endpoints used by KB Retriever/Code Graph queries).
- **Related sub-project docs**: [`workflow-engine` `design-artifact.md`](../workflow-engine/design-artifact.md) (§3.3 — Design Artifact schema), [`workflow-engine` `freeze-pipeline.md`](../workflow-engine/freeze-pipeline.md) (§4 — consumer of design drafts), [`knowledge-services`](../knowledge-services/) (KB backends), [`query-serving`](../query-serving/) (Light Compute Engine), [`platform-core`](../platform-core/) (RBAC, Audit Trail, Notification).
- **Shared sequence diagram**: [`../_shared/sequence-diagrams.md`](../_shared/sequence-diagrams.md) §21.3 AI Agent Query with Permission Gating (primary sub-project).
- **ADRs** ([index](../../adr-index.md)): [ADR-0005 Four-Layer Architecture](../../../adr/0005-four-layer-architecture.md) (Zero AI Side Effects — why Exploration outputs are non-productive), [ADR-0016 Dual-Mode Agent Orchestration](../../../adr/0016-dual-mode-agent-orchestration.md) (the Conversation Interface triggers Exploration-Mode orchestration), [ADR-0024 KB Reasoning Support](../../../adr/0024-kb-reasoning-support-playbooks-code.md) (Playbooks/Code Knowledge surfaced through the Conversation Interface).
- **Glossary** ([../../glossary.md](../../glossary.md)): Exploration Environment, Conversation Interface, Visual Designer, Workbench, AI Copilot Engine, Light Compute Engine, Design Artifact, Prompt Injection Defense, Adjustment Submission Pipeline.
- **Cross-references retained from source**: §3.3 (Design Artifact handoff schema); §22A (Agent runtime that the Conversation Interface drives); §22D (the 7-layer superset of the §3.2 input-side defense).
