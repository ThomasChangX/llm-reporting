# AI-Assisted Generation Pipeline

> **Origin**: §23.5 of [`docs/03-architecture.md`](../../03-architecture.md) | **Sub-project**: [brd-adr-lifecycle](README.md)

## Purpose

This module defines the **AI-assisted generation pipelines** that produce BRDs and ADRs. Per ADR-0022, BRD generation is a **6-Agent serial pipeline** (with prefix naming) preceded by a Five Whys intent-deepening step; each agent has a single responsibility and emits a typed JSON artifact consumed by the next. The pipeline is the system's mechanism for turning a one-line business request ("Finance says month-end reconciliation takes too long, help me automate it") into a structured, verified, human-approved BRD YAML, plus the parallel flow that auto-drafts an ADR whenever a code change is detected as architecturally significant.

The pipeline is deliberately **serial, not parallel** (LLM Gateway concurrency constraints; modular > monolithic per ReqInOne, RE 2025). It performs **inline** AssumptionCheck after each chapter — not post-hoc — to prevent Hallucination Snowballing (SHARS, ICLR 2025). Conflicts are detected by the agent and flagged, never auto-adjudicated; adjudication is always human (C2).

This module covers §23.5 in full:
- §23.5.1 BRD Generation Agent Pipeline Overview — the full 6-agent pipeline diagram and the 8 key design decisions.
- §23.5.2 BRD-IntentDeepener — Five Whys requirements tracing.
- §23.5.3 BRD-ContextGatherer — three-source RAG + cold-start degradation.
- §23.5.4 BRD-VaguenessResolver — Experience Typology Tree-driven disambiguation.
- §23.5.5 BRD-DraftWriter — chapter-by-chapter generation + inline AssumptionCheck.
- §23.5.6 BRD-Verifier — 6-round deep verification.
- §23.5.7 BRD-Assembler — assembly + Pre-Sync Gate.
- §23.5.8 Multi-BRD Conflict Detection — event-driven Suspect Flag.
- §23.5.9 ADR Generation Flow — the 5-step architecturally-significant-change → acceptance flow.

## Boundaries

**In scope**

- The full BRD generation agent pipeline: all 6 serial agents (IntentDeepener, ContextGatherer, VaguenessResolver, DraftWriter, Verifier, Assembler), their inputs/outputs, stopping conditions, and the inline AssumptionCheck + soft-lock + bounded-rollback mechanics.
- The 8 key design decisions (table) and their research-paper rationale.
- Multi-BRD conflict detection (event-driven Suspect Flag, Requirement-level granularity, incremental-patch revision mode).
- The ADR Generation Flow (5 steps: architectural significance detection → context gathering → draft generation → developer review → review & acceptance).

**Out of scope**

- The **entity models** the pipeline produces — see [BRD Entity Model](brd-entity-model.md) and [ADR Entity Model](adr-entity-model.md).
- The **lifecycle states** the produced drafts enter (`draft` / `proposed`) and their subsequent transitions — see [Lifecycle State Machine](lifecycle-state-machine.md).
- The **agent execution runtime** (LLM Gateway, concurrency, retry) — owned by the [`agent-platform`](../agent-platform/) sub-project.
- The **full 6-Round Verifier detail** — this pipeline retains the 6-Round pipeline unchanged from ADR-0010; the per-round detail lives in [ADR-0010](../../../adr/0010-brd-adr-first-class.md) and [ADR-0010's referenced `adr/0010`].
- The **Experience Typology Tree** storage and three-layer progressive construction internals beyond what VaguenessResolver needs — covered by the parent architecture's §23.11.

## Interfaces

- **Upstream input** — a natural-language business request (e.g., "Finance says month-end reconciliation takes too long, help me automate it") enters BRD-IntentDeepener. For ADR generation, the trigger is a merged PR detected by Change Intelligence as architecturally significant.
- **Inter-agent contract** — each agent emits a typed JSON artifact consumed by the next: `intent_profile.json` → `context_dossier.json` → `resolved_dimensions.json` → (user confirms) → streaming BRD YAML → `verification_report.json` → `brd_package.json`. These are the load-bearing contracts of the pipeline.
- **Downstream output** — `brd_package.json` (YAML + Markdown + Jira/Rally payload + export formats + confidence summary) for BRDs; an ADR draft for the ADR flow.
- **Web UI (Workbench)** — renders the streaming incremental BRD YAML per section, presents AssumptionCheck confirmations, the Pre-Sync Gate state, and the ADR draft review surface.
- **External trackers** — Jira/Rally sync is gated by the Pre-Sync Gate (§23.5.7); export (Markdown/PDF) is ungated.
- **Code Graph / Event Bus** — Multi-BRD Conflict Detection (§23.5.8) consumes `entity.changed` events and traverses the Code Graph dependency graph; ADR Generation (§23.5.9) consumes Change Intelligence's architectural-significance classification.

## Dependencies

- **LLM Gateway** — executes each agent's LLM call; its concurrency constraints are why the pipeline is serial (Decision 1). Owned by [`agent-platform`](../agent-platform/).
- **Knowledge Base (KB)** — Glossary + Data Catalog + Mapping Registry, consumed by ContextGatherer's three-source RAG and by DraftWriter's NLI verification. Owned by [`knowledge-services`](../knowledge-services/).
- **Code Graph** — consumed by ContextGatherer (existing code/repos), by Multi-BRD Conflict Detection (dependency traversal), and by ADR Generation (current architecture topology, similar past ADRs). Owned by [`knowledge-services`](../knowledge-services/).
- **Change Intelligence** — classifies merged PRs as architecturally significant (ADR Generation Step 1). Owned by [`knowledge-services`](../knowledge-services/).
- **ImpactAnalyzer (S04)** — provides downstream impact for ADR consequences. Owned by [`knowledge-services`](../knowledge-services/).
- **Jira/Rally history** — similar BRDs/Epics, reuse patterns, approval chains (ContextGatherer source 2).
- **GitHub code** — existing related Workflows and pipeline implementations (ContextGatherer source 3).
- **`agent_semantic_memory`** — stores the Experience Typology Tree, isolated by `tenant_id` (VaguenessResolver).
- **MCP plugins** — MCP-06 git-diff (PR Diff), MCP-05 log-search (recent errors) are used in ADR Generation Step 2; MCP-22 compliance mapping is used in Verifier Round 2.

### Research-paper foundations (cited in §23.5)

The pipeline's design is grounded in:
- **ReqInOne (RE 2025)** — modular agent > monolithic.
- **SHARS (ICLR 2025)** — post-hoc AssumptionCheck cannot prevent Hallucination Snowballing → inline check required.
- **FGL (2025)** — Atomic Claim Decomposition + NLI achieves 90–91.8% accuracy distinguishing supported / inferred / assumed.
- **ReAgent (ACL 2025) + CARE (2026)** — local bounded backtrack (not full restart).
- **TypoAgent / OntoAgent (RE 2026)** — Typology Tree three-layer progressive construction with strict tenant isolation.
- **O'Hara (IEEE 2025)** — Five Whys stopping conditions (semantic gating, diminishing returns, hard depth cap).
- **LLMs4OL (2025)** — GPT-4 structured extraction accuracy 84.76% (Schema-Driven Bootstrap).
- **AroTrace + ARTIAS (2025)** — Suspect Flag event-driven (detection automated ~99%, adjudication human).

## Data Model

### §23.5 AI-Assisted Generation Pipeline

#### §23.5.1 BRD Generation Agent Pipeline Overview

> **Design Change**: S15 BRDGenerator has been refined from a monolithic Skill into a 6-Agent serial pipeline with prefix naming per ADR-0022. The AI-assisted generation + 6-round verification + human approval direction established by this ADR remains unchanged, but the internal pipeline architecture has been substantially restructured. See [ADR-0022](../../../adr/0022-brd-generation-agent-pipeline.md) for details.

```
User: "Finance says month-end reconciliation takes too long, help me automate it"
      │
      ▼
┌──────────────────────────────────────────────────────────────────────┐
│ BRD-IntentDeepener (Requirements Tracing)                            │
│                                                                       │
│  Five Whys trace:                                                     │
│  L1: "Why does reconciliation take time?" → "Manual comparison of    │
│       US and China GL"                                                │
│  L2: "Why can't they be merged directly?" → "COA mapping             │
│       inconsistent"  → ✅ Actionable, stop                           │
│                                                                       │
│  Output → intent_profile.json:                                        │
│  { core_objective, success_criteria, scope {in_scope, out_of_scope} } │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│ BRD-ContextGatherer (Context Collection)                              │
│                                                                       │
│  Three-source RAG: KB (Glossary + Catalog + Mapping)                 │
│                  + Jira/Rally history (similar BRDs/Epics)            │
│                  + GitHub code (existing reconciliation Workflows)    │
│                                                                       │
│  Output → context_dossier.json:                                       │
│  { kb_entries, historical_artifacts, existing_code, gaps }            │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│ BRD-VaguenessResolver (Ambiguity Resolution)                          │
│                                                                       │
│  Experience Typology Tree:                                            │
│  Reconciliation BRD → [data sources, match keys, break categories,   │
│                         currency, frequency, approval chain]          │
│  auto_filled: data sources (NC+SAP), match key (COA code),           │
│               break categories (standard 3 types)                     │
│  needs_user: currency conversion rules →                             │
│              "Which exchange rate for US-China reconciliation?"       │
│  pruned: real-time alerts (scope explicitly month-end only)           │
│                                                                       │
│  Output → resolved_dimensions.json + targeted questions (≤3)          │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                          [User Confirms]
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│ BRD-DraftWriter (Section-by-Section + Inline AssumptionCheck)         │
│                                                                       │
│  Section order: business_context → requirements → data_flows         │
│               → stakeholders → traceability                          │
│                                                                       │
│  Per-section loop:                                                    │
│    1. Generate section draft                                          │
│    2. Atomic Claim Decomposition                                      │
│    3. NLI Verification (does KB source truly support this claim)      │
│    4. Assumption Inventory (extract claims without KB support)        │
│    5. Blocker? → present to user / Non-blocker → mark conditional,    │
│       continue                                                        │
│    6. Soft Lock → next section                                        │
│                                                                       │
│  Downstream discovers upstream flaw → bounded backtrack               │
│  (max 2, affected sections only)                                      │
│                                                                       │
│  Output → streaming incremental BRD YAML (Web UI renders per section) │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│ BRD-Verifier (6-Round Deep Verification)                              │
│                                                                       │
│  Round 1: Structural completeness  Round 2: KB cross-ref + compliance│
│                                          mapping (MCP-22)             │
│  Round 3: Impact analysis         Round 4: Gap analysis (historical  │
│                                          BRDs + Incidents)            │
│  Round 5: Approval chain validation Round 6: Testability & measurability │
│                                                                       │
│  Conflict detection → Agent detects, flags conflict, does not         │
│  adjudicate → hands off to human                                      │
│                                                                       │
│  Output → verification_report.json                                    │
│  { per-round scores, issues (P0/P1/P2), overall_confidence,           │
│    recommended_actions }                                              │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│ BRD-Assembler (Assembly + Pre-Sync Gate)                              │
│                                                                       │
│  Three-format output:                                                 │
│    YAML → Git storage (Compute Spec)                                 │
│    Markdown → text export                                             │
│    Jira Payload → Epic + Stories (Given/When/Then AC)                │
│                                                                       │
│  Pre-Sync Gate:                                                       │
│    Unresolved blocker present? → 🚫 Jira/Rally button disabled       │
│    No blocker? → ✅ sync allowed                                      │
│                                                                       │
│  Output → brd_package.json                                            │
│  { yaml, markdown, jira_payload, rally_payload,                       │
│    export_formats, confidence_summary }                               │
└──────────────────────────────────────────────────────────────────────┘
```

**Key Design Decisions** (details in [ADR-0022](../../../adr/0022-brd-generation-agent-pipeline.md)):

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | 6-Agent serial (not parallel) | LLM Gateway concurrency constraints; ReqInOne (RE 2025) modular > monolithic |
| 2 | Inline AssumptionCheck (not post-hoc) | SHARS (ICLR 2025): Post-hoc cannot prevent Hallucination Snowballing |
| 3 | Atomic Claim Decomposition + NLI | FGL (2025): 90-91.8% NLI accuracy, distinguishing supported/inferred/assumed |
| 4 | Soft Lock + bounded backtrack (max 2) | ReAgent (ACL 2025) + CARE (2026): local backtrack, not full restart |
| 5 | Jira unidirectional sync (BRD→Jira) | BRD is the sole Source of Truth; bidirectional sync with inconsistent state models inevitably causes conflicts |
| 6 | Typology Tree three-layer progressive construction | TypoAgent (RE 2026): Schema→BRD→Cross-BRD, strict tenant isolation |
| 7 | Suspect Flag event-driven | AroTrace + ARTIAS (2025): detection automated (99%), adjudication human |
| 8 | Pre-Sync Gate blocks incomplete sync | Prevents Jira/Rally creation when critical info is missing; export unaffected |

#### §23.5.2 BRD-IntentDeepener (Requirements Tracing)

**Purpose**: Five Whys trace to root cause of business need, extract core objective, success criteria, and scope.

**Stopping Conditions** (O'Hara, IEEE 2025):
- **Semantic Gating**: Answer maps to ≥1 Given/When/Then or success_criteria → stop
- **Diminishing Returns Zero**: Current round's answer adds no new information vs previous → stop
- **Hard Depth Cap**: 3 layers (99% of actionable requirements emerge within 3 layers)

**Output → `intent_profile.json`**:

```json
{
  "step": "intent_deepening",
  "original_input": "Finance says month-end reconciliation takes too long, help me automate it",
  "five_whys": [
    {"layer": 1, "question": "Why does reconciliation take time?", "answer": "Manual comparison of US and China GL"},
    {"layer": 2, "question": "Why can't they be merged directly?", "answer": "COA mapping inconsistent → actionable ✓"}
  ],
  "core_objective": "Automate US-China GL account-level reconciliation, reduce month-end close from T+5 to T+2",
  "success_criteria": ["Auto-match rate ≥ 80%", "Break classification accuracy ≥ 85%", "Total reconciliation time ≤ 2 business days"],
  "scope": {"in_scope": ["GL account-level reconciliation", "US and China GL"], "out_of_scope": ["AP/AR subledgers", "Tax reconciliation"]},
  "confidence": 0.82
}
```

#### §23.5.3 BRD-ContextGatherer (Context Collection)

**Purpose**: Three-source RAG + cold-start degradation.

**Three-Source Retrieval**:
- KB: Business Glossary + Data Catalog + Mapping Registry (existing S02)
- Jira/Rally History: Similar BRDs/Epics, reuse patterns and approval chains (new)
- GitHub Code: Existing related Workflows and data pipeline implementations (new)

**Cold-Start Degradation** (new tenant / new domain): All three sources empty → Schema-Driven Bootstrap — scan tenant Data Source schemas, infer business domain and requirement dimensions from table names / column names / DDL comments (LLMs4OL 2025: GPT-4 structured extraction accuracy 84.76%).

**Output → `context_dossier.json`**:

```json
{
  "step": "context_gathering",
  "kb_entries": [
    {"type": "glossary", "key": "US_GAAP_GL", "source": "kb_glossary"},
    {"type": "data_catalog", "key": "ds_nc_china", "source": "data_catalog"}
  ],
  "historical_artifacts": [
    {"type": "brd", "id": "BRD-0032", "similarity": 0.78, "reusable_patterns": ["Break three-tier routing"]}
  ],
  "existing_code": [
    {"repo": "etl-recon", "path": "src/recon/gl_matcher.py", "relevance": "Existing GL matching engine"}
  ],
  "gaps": [
    {"dimension": "US-China COA mapping coverage", "current": "73%", "required": "≥90%", "severity": "blocking"}
  ]
}
```

#### §23.5.4 BRD-VaguenessResolver (Vagueness Disambiguation)

**Purpose**: Detect missing dimensions based on the Experience Typology Tree and ask precise questions.

**Experience Typology Tree** (TypoAgent/OntoAgent, RE 2026):

Three-layer progressive construction (strict tenant isolation):

| Layer | Trigger Condition | Data Source | Coverage |
|-------|-------------------|-------------|----------|
| Layer 0 | Tenant onboarding (immediate) | Data Source Schema (table/column name inference) | 60-70% dimensions |
| Layer 1 | Each BRD closed | Dimensional structure extracted from that BRD YAML | +10-15% / BRD |
| Layer 2 | ≥3 BRDs of same type | Cross-BRD pattern induction | Standardized template |

The Tree is stored in `agent_semantic_memory`, isolated by `tenant_id`. The system provides a built-in "bare skeleton" (type names + generic dimension names only, no tenant data) that can be shared across tenants.

**Gating/Pruning Mechanism**: Dimensions already covered by the Typology Tree are auto-filled → remaining missing dimensions trigger precise questions (≤3 questions) → inapplicable dimensions are pruned and skipped.

**Output → `resolved_dimensions.json`**:

```json
{
  "step": "vagueness_resolution",
  "dimensions": [
    {"dimension": "data_sources", "status": "auto_filled", "value": ["NC_China_GL", "SAP_US_GL"], "source": "context_gathering"},
    {"dimension": "currency_conversion", "status": "needs_user", "question": "Which exchange rate should be used for US-China reconciliation?",
     "options": ["Month-end spot rate (Central Bank)", "Monthly average rate", "Fixed budget rate"], "default": "Month-end spot rate (Central Bank)"},
    {"dimension": "real_time_alert", "status": "pruned", "reason": "scope is explicitly month-end reconciliation only"}
  ],
  "questions_for_user": [{"id": "q1", "question": "...", "options": [...], "default": "..."}]
}
```

#### §23.5.5 BRD-DraftWriter (Chapter-by-Chapter Generation + Inline AssumptionCheck)

**Purpose**: Generate BRD YAML chapter by chapter, with each chapter soft-locked before serving as context for the next.

**Generation Order**: `business_context → requirements → data_flows → stakeholders → traceability`

**Soft-Lock + Bounded Rollback** (ReAgent, ACL 2025):

Section dependency graph:

```
business_context ─────────────────────────────┐
    ├──→ requirements ──┐                      │
    │                    ├──→ data_flows ──┐   │
    ├──→ stakeholders ───┼──────────────────┤   │
    └──→ traceability ───┴──────────────────┘   │
        All sections ultimately reference business_context ────┘
```

Rollback rules:
- Supplementary conflicts (e.g., new Stakeholder added) → write `pending_revision` marker, no rollback
- Blocking conflicts (e.g., core data source missing) → trigger local rollback (affected sections only)
- Same section max 2 attempts → escalate to P0 blocking issue for user resolution

**Inline AssumptionCheck** (SHARS, ICLR 2025 / FGL, 2025):

Executed immediately after each chapter is generated (not post-hoc):
1. Atomic Claim Decomposition: Break each sentence into independent claims
2. NLI Verification: Check whether KB sources genuinely support the claim (90-91.8% accuracy)
3. Labeling: `directly_supported` / `inferred_assumption` / `business_assumption`
4. Triage: Blocker (affects ≥2 Sections or ≥1 P0 Requirement) → halt / Non-blocker → mark conditional and continue

**Web UI Presentation**:

```
┌─────────────────────────────────────────────────────────┐
│  Step 4.5: Business Assumption Confirmation              │
│                                                          │
│  ⚠️ Critical Assumption #1                               │
│  "Revenue is recognized at a point in time (upon delivery)"│
│  Source: AI inferred based on IFRS 15                    │
│  Impact: Given/When/Then of FR-001, FR-002               │
│  ○ Correct  ● Incorrect, we use percentage-of-completion │
│                                                          │
│  ✅ Verified Claims (3)  ⚠️ Assumptions to Confirm (2)    │
└─────────────────────────────────────────────────────────┘
```

#### §23.5.6 BRD-Verifier (6-Round Deep Verification)

Retains the 6-Round verification pipeline (see [ADR-0010](../../../adr/0010-brd-adr-first-class.md) for details), with key changes:

- **Conflict Detection Strategy**: Agent detects conflicts, marks `conflict`, makes no ruling, throws back to human for resolution (C2)
- **Verification does not block generation**: Draft is presented first; verification results serve as supplementary decision support
- Each round's findings have independent priority (P0 blocking / P1 quality / P2 nice-to-have / Info)

Detailed 6-Round content refers to [ADR-0010](../../../adr/0010-brd-adr-first-class.md) (the original LLM Deep Verification Pipeline), remains unchanged.

**6-Round summary** (from the pipeline diagram):

| Round | Focus |
|-------|-------|
| Round 1 | Structural completeness |
| Round 2 | KB cross-ref + compliance mapping (MCP-22) |
| Round 3 | Impact analysis |
| Round 4 | Gap analysis (historical BRDs + Incidents) |
| Round 5 | Approval chain validation |
| Round 6 | Testability & measurability |

**Output → `verification_report.json`**: `{ per-round scores, issues (P0/P1/P2), overall_confidence, recommended_actions }`.

#### §23.5.7 BRD-Assembler (Assembly + Pre-Sync Gate)

**Purpose**: Aggregate the final artifacts and generate three output formats.

**Output → `brd_package.json`**:

```json
{
  "step": "assembly",
  "brd_id": "BRD-0047",
  "yaml": "brd:\n  id: BRD-0047\n  ...",
  "markdown": "# BRD-0047: US-China GL Auto-Reconciliation\n\n## 1. Business Context\n...",
  "jira_payload": {
    "epic": {"project_key": "FIN", "summary": "...", "labels": ["brd-generated"]},
    "stories": [{"summary": "[FR-001] ...", "acceptance_criteria": ["Given...When...Then..."]}]
  },
  "export_formats": {"markdown": "BRD-0047_v0.1-draft.md", "pdf": "BRD-0047_v0.1-draft.pdf"},
  "confidence_summary": {"overall": 0.83, "by_section": {...}}
}
```

**Pre-Sync Gate**: If unresolved blockers exist (fuzzy_nodes blocking + unconfirmed Blocking assumptions + Verifier P0 issues) → 🚫 Block Jira/Rally creation. Markdown/PDF export is unaffected (fuzzy content annotated with `[TBD: ...]`).

#### §23.5.8 Multi-BRD Conflict Detection

**Mechanism**: Event-driven Suspect Flag (AroTrace + ARTIAS, 2025)

```
Entity change (BRD approved / KB entry modified / Data Source Schema change)
    ↓
Publish entity.changed event
    ↓
Code Graph traverses dependency graph → finds all BRDs referencing that entity
    ↓
Auto-flag as needs_update (Suspect Flag)
    ↓
Notify BRD Owner → Human adjudication: Confirm Impact / Confirm No Impact / Create Revision BRD
```

**Granularity**: Precise to the Requirement level (Code Graph supports Requirement-level dependency edges from BRD→KB Entry).

**Revision Mode**: Incremental patch + cascade refresh — modify designated Section → auto-refresh affected downstream Sections via dependency graph, leaving unrelated sections untouched. Revision conflicts detected by Agent, marked conflict, returned to human adjudication.

#### §23.5.9 ADR Generation Flow

```
Trigger: Developer merges PR that introduces Kafka Connect dependency
         (Change Intelligence detects "architecturally significant change")
      │
      ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 1: ARCHITECTURAL SIGNIFICANCE DETECTION                         │
│                                                                      │
│  Change Intelligence auto-analyzes the merged Diff:                    │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ • Code Graph diff: new component "cdc_pipeline" introduces Kafka Connect │    │
│  │ • Dependency diff: new Maven/Gradle dependencies (Debezium, Avro)  │    │
│  │ • Pattern Analysis: new component type "Message Broker" appears for the first time │    │
│  │ → Classified as: ARCHITECTURALLY_SIGNIFICANT                  │    │
│  │ → Trigger: auto-draft ADR                                      │    │
│  └─────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 2: CONTEXT GATHERING (S02 + S03 + S04)                         │
│                                                                      │
│  Parallel gathering:                                                    │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ S03: Code Graph → "PG CDC" current architecture topology    │    │
│  │ S03: Code Graph → find similar technical decision patterns (past ADRs) │    │
│  │ S02: KB → retrieve relevant technical constraints (deployment constraints, SLAs) │    │
│  │ S04: ImpactAnalyzer → impact of this change on downstream components │    │
│  │ MCP-06: git-diff → PR #2347 full Diff                        │    │
│  │ MCP-05: log-search → recent "PG replication slot" related errors │    │
│  └─────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 3: ADR DRAFT GENERATION (S16 ADRGenerator + S06 DocGenerator)  │
│                                                                      │
│  AI auto-drafts based on gathered context:                             │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ context: auto-generated from Log + KB + PR description      │    │
│  │ decision_drivers: derived from KB deployment constraints + SLA │    │
│  │ options:                                                     │    │
│  │   - opt-1: extract current implementation approach from PR diff │    │
│  │   - opt-2: extract existing approach from Code Graph (the one being replaced) │    │
│  │   - opt-3: infer alternative approaches from similar ADR options │    │
│  │ decision: extract rationale from PR description + commit message │    │
│  │ consequences: extracted from S04 ImpactAnalyzer output       │    │
│  │ traceability: auto-populate linked components/BRDs/Incidents from Code Graph │    │
│  └─────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 4: DEVELOPER REVIEW IN WORKBENCH                                │
│                                                                      │
│  Developer receives notification: "PR #2347 triggered an ADR draft" │
│                                                                      │
│  Workbench presents ADR Draft:                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ ADR-0042 (Draft): Use Debezium + Kafka Connect for CDC      │    │
│  │                                                              │    │
│  │ ┌─ Auto-Generated ────────────────────────────────────────┐ │    │
│  │ │ Context ....... [✓ Generated from PR#2347 + INC-0042]   │ │    │
│  │ │ Options ....... [✓ opt-1 from diff, opt-2 from graph]   │ │    │
│  │ │ Decision ...... [⚠ Draft: please add your rationale]    │ │    │
│  │ │ Consequences .. [✓ From impact analysis]                │ │    │
│  │ │ Traceability .. [✓ auto-linked: COMPONENTS, INCIDENTS]  │ │    │
│  │ └────────────────────────────────────────────────────────┘ │    │
│  │                                                              │    │
│  │  [Edit & Submit]  [Request Team Review]  [Dismiss]           │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  Developer supplements rationale, adjusts options, adds team discussion notes │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 5: ADR REVIEW & ACCEPTANCE                                      │
│                                                                      │
│  • ADR status → in_discussion → team review (Code Graph suggests approvers) │
│  • Architecture review passed → status → accepted                     │
│  • ⚠️ ACCEPTED = IMMUTABLE — Cannot be edited thereafter             │
│  • If old ADR is superseded → old ADR status → superseded            │
│  • Code Graph: add ADR node + relationship edges                     │
│  • Notification → affected component Owners (FR37)                   │
└─────────────────────────────────────────────────────────────────────┘
```

## Failure Modes & Recovery

| Failure mode | Detection | Impact | Recovery |
|--------------|-----------|--------|----------|
| **LLM Gateway concurrency / rate-limit failure** (a single agent call fails) | LLM Gateway error response; agent-platform retry policy | That agent stalls; downstream agents blocked (serial pipeline) | Agent-platform retry with backoff. Because the pipeline is serial and each agent emits a persisted JSON artifact, recovery resumes from the last successful artifact — no full restart. |
| **Hallucination / unsupported claim in DraftWriter** | Inline AssumptionCheck NLI step labels the claim `inferred_assumption` / `business_assumption`; Blocker triage if it affects ≥2 Sections or ≥1 P0 Requirement | Draft cannot soft-lock the section | Present the assumption to the user (Web UI Step 4.5); on confirmation, mark conditional and continue; on rejection, the user corrects and the section regenerates. Same-section max 2 attempts → escalate to P0 blocking issue. |
| **Downstream section discovers upstream flaw** | DraftWriter detects a blocking conflict (e.g., core data source missing) when generating a later section | Cascading rework | Bounded local backtrack (max 2, affected sections only — ReAgent/CARE); not a full pipeline restart. Supplementary conflicts write a `pending_revision` marker with no rollback. |
| **Verifier finds P0 issue** | Verifier Round (1–6) emits a P0 issue | Draft is still presented (verification does not block generation), but Pre-Sync Gate blocks Jira/Rally sync | Verifier results are supplementary decision support. User resolves the P0 issue; Pre-Sync Gate re-evaluates. Export (Markdown/PDF) remains available with `[TBD: ...]` annotations. |
| **Pre-Sync Gate blocks sync** | Unresolved fuzzy_nodes + unconfirmed Blocking assumptions + Verifier P0 issues | 🚫 Jira/Rally creation disabled | Resolve blockers / confirm assumptions / fix P0 issues; Markdown/PDF export unaffected. |
| **Multi-BRD conflict (entity change affects existing BRDs)** | `entity.changed` event → Code Graph traversal → Suspect Flag | Affected BRD auto-flagged `needs_update`; possible revision conflicts | Human adjudication (Confirm Impact / Confirm No Impact / Create Revision BRD). Revision Mode = incremental patch + cascade refresh; conflicts detected and returned to human. |
| **Cold-start (all three ContextGatherer sources empty)** | ContextGatherer detects empty KB + no Jira/Rally history + no existing code | Pipeline cannot ground the BRD in real context | Schema-Driven Bootstrap: scan tenant Data Source schemas, infer domain/dimensions from table/column names + DDL comments (LLMs4OL 2025, 84.76% accuracy). Coverage is lower than warm-start but unblocks new tenants. |
| **ADR auto-draft dismissed / rejected** | Developer clicks "Dismiss", or architecture review rejects | No ADR created (or ADR → `rejected`, retained as historical reference) | The architecturally significant change remains flagged. If the decision is later needed, a new ADR draft can be regenerated; the rejected draft is cited as "why we didn't choose this approach." |

## Non-Functional Requirements

- **Serial execution** — the 6 BRD agents run strictly in sequence (Decision 1); there is no parallel branch. This respects LLM Gateway concurrency constraints and the modular > monolithic finding (ReqInOne, RE 2025).
- **Inline (not post-hoc) verification** — AssumptionCheck runs immediately after each chapter is generated (Decision 2) to prevent Hallucination Snowballing (SHARS, ICLR 2025).
- **Bounded rework** — backtrack is local (max 2, affected sections only) and never a full pipeline restart (Decision 4; ReAgent/CARE). Same-section max 2 attempts before P0 escalation.
- **Human-in-the-loop adjudication** — conflicts are detected by the agent and flagged, never auto-resolved (C2). VaguenessResolver asks ≤3 precise questions; AssumptionCheck halts on blockers; Multi-BRD Suspect Flags await human adjudication; ADR acceptance requires architecture review.
- **Tenant isolation** — the Experience Typology Tree is stored in `agent_semantic_memory` isolated by `tenant_id`; only the "bare skeleton" (generic type/dimension names, no tenant data) is shared across tenants (Decision 6).
- **Unidirectional external sync** — Jira/Rally sync is BRD → tracker only (Decision 5); the BRD is the sole Source of Truth. The Pre-Sync Gate (Decision 8) blocks incomplete syncs; export is always available.
- **Confidence transparency** — every agent emits a confidence signal (`intent_profile.confidence`, `brd_package.confidence_summary`); the Verifier emits per-round scores and an overall confidence. These surface in the Workbench.
- **Idempotent, artifact-persisted stages** — each agent's JSON output is persisted, so recovery resumes from the last successful artifact rather than re-running the whole pipeline.

## Key Flows

### BRD generation end-to-end (the 6-agent serial pipeline)

1. **IntentDeepener** (§23.5.2) — Five Whys trace with O'Hara stopping conditions (semantic gating / diminishing returns / hard depth cap 3). Emits `intent_profile.json` (`core_objective`, `success_criteria`, `scope`).
2. **ContextGatherer** (§23.5.3) — three-source RAG (KB + Jira/Rally history + GitHub code); cold-start degradation via Schema-Driven Bootstrap when all sources empty. Emits `context_dossier.json` (`kb_entries`, `historical_artifacts`, `existing_code`, `gaps`).
3. **VaguenessResolver** (§23.5.4) — Experience Typology Tree-driven gating/pruning: auto-fill covered dimensions, prune inapplicable ones, ask ≤3 precise questions on the rest. Emits `resolved_dimensions.json` + targeted questions. **[User Confirms]** is the gate to the next agent.
4. **DraftWriter** (§23.5.5) — chapter-by-chapter generation in order `business_context → requirements → data_flows → stakeholders → traceability`. Per section: generate → Atomic Claim Decomposition → NLI verify → assumption inventory → triage (blocker halts / non-blocker marks conditional) → soft-lock → next. Bounded backtrack (max 2) on blocking conflicts. Emits streaming incremental BRD YAML.
5. **Verifier** (§23.5.6) — 6-round deep verification (structural / KB+compliance / impact / gap / approval-chain / testability). Conflict detection flags, never adjudicates. Emits `verification_report.json`. **Does not block generation** — supplementary decision support.
6. **Assembler** (§23.5.7) — aggregate to three formats (YAML → Git, Markdown → export, Jira payload → Epic+Stories with Given/When/Then AC). Pre-Sync Gate blocks Jira/Rally creation on unresolved blockers; export always available. Emits `brd_package.json`.

### Multi-BRD conflict detection (event-driven, §23.5.8)

1. An entity changes (BRD approved / KB entry modified / Data Source schema change) → `entity.changed` event.
2. Code Graph traverses the dependency graph → finds all BRDs referencing that entity (Requirement-level precision).
3. Auto-flag the affected BRD `needs_update` (Suspect Flag) → notify BRD Owner.
4. Human adjudicates: Confirm Impact / Confirm No Impact / Create Revision BRD.
5. Revision Mode: incremental patch + cascade refresh of affected downstream sections via the dependency graph; conflicts detected and returned to human adjudication.

(See [Lifecycle State Machine](lifecycle-state-machine.md) for the `needs_update` state's subsequent transition back to `in_review`.)

### ADR generation flow (5 steps, §23.5.9)

1. **Architectural Significance Detection** — Change Intelligence analyses the merged Diff (Code Graph diff, dependency diff, pattern analysis). If classified `ARCHITECTURALLY_SIGNIFICANT` → trigger auto-draft.
2. **Context Gathering** (parallel, S02+S03+S04+MCPs) — Code Graph topology + similar past ADRs; KB technical constraints/SLAs; ImpactAnalyzer downstream impact; MCP-06 git-diff full PR Diff; MCP-05 log-search recent related errors.
3. **ADR Draft Generation** (S16 ADRGenerator + S06 DocGenerator) — auto-generate `context`, `decision_drivers`, `options` (opt-1 from diff, opt-2 from graph, opt-3 inferred from similar ADRs), `decision` (rationale from PR/commit), `consequences` (from ImpactAnalyzer), `traceability` (auto-linked from Code Graph).
4. **Developer Review in Workbench** — developer notified; reviews auto-generated sections, supplements rationale, adjusts options, adds team discussion notes. Actions: Edit & Submit / Request Team Review / Dismiss.
5. **ADR Review & Acceptance** — `in_discussion` → team review (Code Graph suggests approvers) → architecture review passed → `accepted` (**IMMUTABLE from here**). If superseding, old ADR → `superseded`. Code Graph adds the ADR node + edges; affected component Owners notified (FR37).

(See [Lifecycle State Machine](lifecycle-state-machine.md) §23.4.2 for the full ADR pre-acceptance intermediate states and the immutability invariant.)

## Design References

- **§23.5 AI-Assisted Generation Pipeline** — the source section in [`docs/03-architecture.md`](../../03-architecture.md).
- [ADR-0022](../../../adr/0022-brd-generation-agent-pipeline.md) — BRD Generation Agent Pipeline Redesign (the 8 key design decisions, in detail).
- [ADR-0010](../../../adr/0010-brd-adr-first-class.md) — BRD/ADR as First-Class Entities; the original LLM Deep Verification Pipeline (the 6 Round detail retained unchanged by §23.5.6).
- [BRD Entity Model](brd-entity-model.md) — the BRD YAML schema this pipeline produces.
- [ADR Entity Model](adr-entity-model.md) — the ADR YAML schema the ADR flow produces.
- [Lifecycle State Machine](lifecycle-state-machine.md) — the `draft` / `proposed` states the outputs enter, and the `needs_update` Suspect Flag transition.
- **§23.11 Experience Typology Tree** — the three-layer progressive construction consumed by VaguenessResolver, in [`docs/03-architecture.md`](../../03-architecture.md).
- **§23.8 External Tool Integration** — MCP-20/21/22 (Jira/Confluence/Compliance), including the MCP-22 compliance mapping used by Verifier Round 2, in [`docs/03-architecture.md`](../../03-architecture.md).
- [`docs/sub-projects/agent-platform/README.md`](../agent-platform/README.md) — the LLM Gateway and agent execution runtime.
- [`docs/sub-projects/knowledge-services/README.md`](../knowledge-services/README.md) — KB, Code Graph, Change Intelligence, ImpactAnalyzer.
- [`docs/glossary.md`](../../glossary.md) — definitions of Suspect Flag, Typology Tree, AssumptionCheck, NLI, and related terms.
- Sub-project README — [`docs/sub-projects/brd-adr-lifecycle/README.md`](README.md).
