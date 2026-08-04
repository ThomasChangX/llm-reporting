# External Tool Integration & Supporting Skills

> **Origin**: §23.8, §23.9, §23.10 of [`docs/03-architecture.md`](../../03-architecture.md) | **Sub-project**: [brd-adr-lifecycle](README.md)

## Purpose

This module covers everything that bridges the BRD/ADR hub to the world outside it: the **integration architecture** connecting BRDs/ADRs to Jira, Confluence/Notion, and compliance frameworks via three new MCP servers (§23.8); the **import capability** that migrates legacy BRDs from Word/Excel/PDF into structured YAML (§23.8.3); the **new Skills** S15/S16/S17 that generate and analyze BRDs/ADRs (§23.9); and the **summary of BRD/ADR architecture decisions** ADR-010/011/012 (§23.10).

The unifying principle, enforced by MCP-20 (jira-sync), is that **the BRD is the sole Source of Truth** — external systems receive a projection of it but never write back to it.

## Boundaries

**In-scope:**
- The System BRD/ADR Hub integration topology (§23.8.1) — internal representation (YAML Compute Spec + Code Graph nodes/edges + KB references) fanning out to external systems.
- Three new MCP servers (§23.8.2):
  - **MCP-20 jira-sync** — one-way System → Jira sync (create Epic, link, push status, create Story from requirement); Jira webhook → System read-only.
  - **MCP-21 confluence-export** — export BRD/ADR to Confluence pages or Notion databases (single + batch).
  - **MCP-22 compliance-mapper** — map BRD requirements to compliance framework controls and validate coverage.
- Import / legacy migration (§23.8.3) via S14 MigrationAdvisor (OCR + excel-parser + LLM structuring).
- New Skills (§23.9): **S15 BRDGenerator**, **S16 ADRGenerator**, **S17 TraceabilityAnalyzer**.
- Summary decisions (§23.10): **ADR-010** (Compute Spec subtypes), **ADR-011** (AI-assisted generation with human review gate), **ADR-012** (Code Graph as single source of traceability truth).

**Out of scope (delegated):**
- MCP server runtime / registry → platform MCP infrastructure.
- The 6-agent BRD generation pipeline internals (S15's refined internal flow) → [`generation-pipeline.md`](generation-pipeline.md).
- Code Graph storage of edges that MCP-20 creates → [`knowledge-services`](../knowledge-services/).
- BRD/ADR YAML schemas → [`brd-entity-model.md`](brd-entity-model.md), [`adr-entity-model.md`](adr-entity-model.md).
- Agent trajectory scoring (ADR-0018) → [`quality-and-typology.md`](quality-and-typology.md) §Distinction.

## Interfaces

| Interface | Consumer | Contract |
|-----------|----------|----------|
| MCP-20 `create_epic(brd_yaml) → JiraEpic` | Workbench / automation | Create Jira Epic from a BRD; returns the created Epic. |
| MCP-20 `link_to_epic(brd_id, epic_key) → LinkResult` | Workbench | Establish BRD↔Epic bidirectional link (writes `TRACKS_BY` edge). |
| MCP-20 `push_status(brd_id) → SyncStatus` | Lifecycle state machine | Push BRD status to Jira (`approved` → "Ready for Dev", `implemented` → "Done"). |
| MCP-20 `create_story_from_req(brd_id, req_id) → JiraStory` | Workbench | Create a Jira User Story from a single BRD requirement. |
| MCP-20 `get_story_status(story_key) → StoryStatus` | (Webhook, read-only) | Query Jira Story progress; does not write back to BRD. |
| MCP-20 `get_trace(epic_key) → TraceChain` | Workbench / S17 | Jara → Spec → PR → Deploy traceability chain. |
| MCP-21 `export_to_page(spec_id, space_key, parent_page_id?) → PageResult` | Workbench, CI export | Export a BRD/ADR as a Confluence page. |
| MCP-21 `update_page(spec_id, confluence_page_id) → PageResult` | Workbench | Update an already-exported Confluence page. |
| MCP-21 `export_to_notion(spec_id, database_id) → NotionResult` | Workbench | Export to a Notion database. |
| MCP-21 `batch_export(spec_ids, target) → BatchResult` | Workbench | Batch export to `confluence` or `notion`. |
| MCP-22 `map_brd_to_framework(brd_id, framework) → MappingResult` | CI compliance stage, Workbench | Map BRD requirements to framework controls (SOX/HIPAA/GDPR/ASC606/BASEL/…). |
| MCP-22 `validate_coverage(brd_id) → CoverageReport` | CI compliance stage (§23.7.2 stage 4) | Check the BRD covers all necessary compliance items. |
| MCP-22 `get_control_detail(control_id) → ControlDetail` | Workbench | Get a control's detail description. |
| MCP-22 `suggest_missing_controls(brd_id) → SuggestionList` | Workbench | AI-suggest potentially missing compliance controls. |
| S14 MigrationAdvisor (import) | Onboarding / migration | Legacy BRD (Word/Excel/PDF) → Draft BRD YAML + `migration_notes`. |

## Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| **Jira Cloud / Server** | External (MCP-20) | OAuth 2.0 (Cloud) / PAT (Server); rate-limited by Jira API. |
| **Confluence Cloud/Server / Notion** | External (MCP-21) | OAuth 2.0 (Confluence Cloud) / API Token (Confluence Server/Notion). |
| **Compliance Framework Registry** | External (MCP-22) | Pre-loaded SOX (302/404), HIPAA (Security/Privacy Rules), GDPR (Art.5/25/32), ASC606 (5-step), Basel III; supports tenant custom framework extensions. |
| **MCP-12 (OCR)** | Hard (import) | Scans text in legacy PDF/images for S14. |
| **MCP-16 (excel-parser)** | Hard (import) | Parses legacy Excel BRDs for S14. |
| **MCP-06 (git-diff), MCP-05 (log-search)** | Hard (S16) | Source the architecture-change signal for ADR generation. |
| **MCP-07 (template-render)** | Hard (S17) | Renders traceability visualizations. |
| **S02 KBRetriever, S03 CodeGraphQuery, S04 ImpactAnalyzer, S06 DocGenerator** | Hard (S15/S16/S17) | Shared skill dependencies for retrieval, graph query, impact analysis, and document generation. |
| **Code Graph** | Hard | Persistence for all `TRACKS_BY` / traceability edges that MCP-20 establishes. |
| **CI/CD Validation pipeline** | Soft | MCP-22 feeds compliance stage 4; see [compute-spec-integration.md](compute-spec-integration.md). |

## Data Model

### §23.8.1 Integration Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                    SYSTEM BRD/ADR HUB                                 │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                   INTERNAL REPRESENTATION                      │   │
│  │  • YAML Compute Spec (Git versioned)                           │   │
│  │  • Code Graph nodes + edges                                    │   │
│  │  • KB references                                               │   │
│  └──────────────────────┬───────────────────────────────────────┘   │
│                         │                                           │
│         ┌───────────────┼───────────────┬───────────────┐          │
│         ▼               ▼               ▼               ▼          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  │
│  │ MCP-20     │  │ MCP-21     │  │ MCP-22     │  │ BRD/ADR    │  │
│  │ jira-sync  │  │ confluence │  │ compliance │  │ Export     │  │
│  │            │  │ -export    │  │ -mapper    │  │ Service    │  │
│  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘  │
│         │               │               │               │          │
└─────────┼───────────────┼───────────────┼───────────────┼──────────┘
          ▼               ▼               ▼               ▼
    ┌──────────┐   ┌────────────┐  ┌───────────┐  ┌──────────────┐
    │   Jira   │   │ Confluence │  │Compliance │  │  PDF/Markdown│
    │  Cloud/  │   │ / Notion   │  │ Framework │  │  / Confluence│
    │  Server  │   │            │  │ Registry  │  │  Pages       │
    └──────────┘   └────────────┘  └───────────┘  └──────────────┘
```

The internal representation (YAML Compute Spec + Code Graph nodes/edges + KB references) is the single source of truth. All four outbound channels (MCP-20, MCP-21, MCP-22, BRD/ADR Export Service) are *projections* of that internal state — none of them write back into the BRD/ADR.

### §23.8.2 New MCP Servers

#### MCP-20: jira-sync (Jira One-Way Sync)

| Attribute         | Description                                                                                                                                                                                                                                                                                                                                                                                                      |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Tools**    | `create_epic(brd_yaml) → JiraEpic` — Create Jira Epic from BRD; `link_to_epic(brd_id, epic_key) → LinkResult` — Establish BRD↔Epic bidirectional link; `push_status(brd_id) → SyncStatus` — Push BRD status to Jira (approved → "Ready for Dev", implemented → "Done"); `create_story_from_req(brd_id, req_id) → JiraStory` — Create User Story from BRD requirement; `get_story_status(story_key) → StoryStatus` — Webhook read-only query Jira Story progress (does not write back to BRD); `get_trace(epic_key) → TraceChain` — Get Jira→Spec→PR→Deploy traceability chain |
| **Protocol** | REST (JSON) over TLS 1.3                                                                                                                                                                                                                                                                                                                                                                                  |
| **Auth**     | OAuth 2.0 (Jira Cloud) / Personal Access Token (Jira Server) + `X-Tenant-ID` Header                                                                                                                                                                                                                                                                                                                       |
| **Rate Limit** | 30 req/min per tenant (limited by Jira API)                                                                                                                                                                                                                                                                                                                                                                 |
| **Sync Direction** | One-way: System → Jira (create/link/push_status); Jira Webhook → System (read-only query Story status, update BRD implementation_progress). BRD is the sole Source of Truth —Jira content does not write back to BRD                                                                                                                                                                                                                              |
| **Timeout**  | 15s                                                                                                                                                                                                                                                                                                                                                                                                       |

#### MCP-21: confluence-export (Confluence/Notion Export)

| Attribute         | Description                                                                                                                                                                                                                                                                                                                               |
| ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Tools**    | `export_to_page(spec_id, space_key, parent_page_id?) → PageResult` — Export BRD/ADR as Confluence page; `update_page(spec_id, confluence_page_id) → PageResult` — Update already exported Confluence page; `export_to_notion(spec_id, database_id) → NotionResult` — Export to Notion Database; `batch_export(spec_ids: list, target: "confluence" | "notion") → BatchResult` — Batch export |
| **Protocol** | REST (JSON)                                                                                                                                                                                                                                                                                                                        |
| **Auth**     | OAuth 2.0 (Confluence Cloud) / API Token (Confluence Server/Notion)                                                                                                                                                                                                                                                                |
| **Render Format** | BRD/ADR YAML → Confluence Storage Format (XHTML) / Notion Blocks; includes all traceability links → auto-converted to Confluence/Notion hyperlinks                                                                                                                                                                                                 |
| **Rate Limit** | 10 req/min per tenant                                                                                                                                                                                                                                                                                                              |
| **Timeout**  | 30s                                                                                                                                                                                                                                                                                                                                |

#### MCP-22: compliance-mapper (Compliance Mapper)

| Attribute           | Description                                                                                                                            |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| **Tools**       | `map_brd_to_framework(brd_id, framework: "SOX" / "HIPAA" / "GDPR" / "ASC606" / "BASEL" / …) → MappingResult` — Map BRD requirements to compliance framework controls; `validate_coverage(brd_id) → CoverageReport` — Check if BRD requirements cover all necessary compliance items; `get_control_detail(control_id) → ControlDetail` — Get compliance control detail description; `suggest_missing_controls(brd_id) → SuggestionList` — AI suggest potentially missing compliance controls |
| **Protocol**    | gRPC                                                                                                                            |
| **Auth**        | API Key + `X-Tenant-ID` + mTLS                                                                                                  |
| **Compliance Framework Library** | Pre-loaded with SOX (302/404), HIPAA (Security/Privacy Rules), GDPR (Art.5/25/32), ASC606 (5-step), Basel III, etc. Supports tenant custom framework extensions |
| **Rate Limit** | 20 req/min per tenant |
| **Timeout** | 10s |

### §23.8.3 Import Capability (Legacy Migration)

Supports importing from legacy systems via S14 MigrationAdvisor:

```
Legacy BRD (Word/Excel/PDF)
    │
    ▼
┌──────────────────────────────────────────────┐
│ S14: MigrationAdvisor                        │
│                                              │
│ • MCP-12 (OCR) → Scan text in PDF/images     │
│ • MCP-16 (excel-parser) → Parse Excel BRD    │
│ • LLM → Structure into BRD YAML Schema       │
│ • LLM → Extract requirements + stakeholders  │
│ • LLM → Suggest associated KB entries + Workflows │
│                                              │
│ Output: Draft BRD YAML +                    │
│         migration_notes (manual review item) │
└──────────────────────────────────────────────┘
```

The pipeline is non-destructive: its output is a **Draft BRD YAML** plus `migration_notes` that flag items requiring manual review. The migrated BRD enters the normal lifecycle as a draft and must pass the same CI/CD validation and human review gates as any other BRD.

### §23.9 New Skills (New Skill Definitions)

> Note: S15's *internal* 6-agent pipeline (IntentDeepener / ContextGatherer / VaguenessResolver / DraftWriter / Verifier / Assembler) is specified in detail in [`generation-pipeline.md`](generation-pipeline.md) and [`../../../adr/0022-brd-generation-agent-pipeline.md`](../../../adr/0022-brd-generation-agent-pipeline.md). This section preserves the skill-level contracts from §23.9.

#### S15 — BRDGenerator (BRD Generator) [P1]

| Attribute         | Description                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Description** | Automatically generates structured BRD YAML drafts from natural language descriptions + KB context. **The internal pipeline has been refined by ADR-0022 into 6 Agents** (BRD-IntentDeepener / ContextGatherer / VaguenessResolver / DraftWriter / Verifier / Assembler) executing serially; see §23.5.1 for details |
| **Tools** | S02 (KBRetriever), S03 (CodeGraphQuery), S04 (ImpactAnalyzer), S06 (DocGenerator) |
| **Permissions** | `kb:read`, `code_graph:read`, `spec:write` (draft status only) |
| **Reasoning Model** | Large model (requires understanding of complex business logic and compliance requirements) |
| **Input** | `{ intent: "create_brd", entities: { report_type, compliance, frequency, data_domain, ... }, session_context }` |
| **Output** | `{ brd_draft: { brd YAML object }, fuzzy_nodes: [...], confidence_summary, impact_preview: { affected_workflows, suggested_approvers }, followup_questions: [...] }` |
| **Generation Strategy** | **Phase 1 - Elicitation**: BRD-IntentDeepener (Five Whys) → BRD-ContextGatherer (Three-source RAG + Schema Bootstrap fallback) → BRD-VaguenessResolver (Typology Tree + Gating/Pruning). **Phase 2 - Generation**: BRD-DraftWriter (Chapter-by-chapter generation + Soft Locking + Bounded Rollback + Inline AssumptionCheck). **Phase 3 - Verify (6 Rounds)**: BRD-Verifier (Structural completeness → KB cross-validation → Impact analysis → Gap analysis → Approval chain → Testability). **Phase 4 - Assembly**: BRD-Assembler (Three-format output + Pre-Sync Gate). See [`../../../adr/0022-brd-generation-agent-pipeline.md`](../../../adr/0022-brd-generation-agent-pipeline.md) for details |

#### S16 — ADRGenerator (ADR Generator) [P1]

| Attribute         | Description                                                                                                                                                                                                                                                            |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Description** | Auto-draft ADR from architecture change events (PR merge/Diff)                                                                                                                                                                                                                     |
| **Tools**    | S02 (KBRetriever), S03 (CodeGraphQuery), S04 (ImpactAnalyzer), S06 (DocGenerator), MCP-06 (git-diff), MCP-05 (log-search)                                                                                                                                       |
| **Permissions** | `code_graph:read`, `kb:read`, `log:read`, `spec:write` (draft status only)                                                                                                                                                                                         |
| **Reasoning Model** | Large model (needs multi-source correlation reasoning and architectural judgment)                                                                                                                                                                                                                            |
| **Input**    | `{ trigger: "change_detected" / "manual", change_source: { type: "pr_merge" / "spec_diff" / "incident", payload: { pr_id?, diff?, incident_id? } } }` |
| **Output**   | `{ adr_draft: { adr YAML object }, suggested_options: [...], supersedes_candidates: [adr_id], fuzzy_decisions: [...], review_checklist: [...] }`                                                                                                                |
| **Generation Strategy** | 1) Code Graph diff identifies architecture change type → 2) Extract rationale from PR description + commit → 3) Search similar ADRs for options templates → 4) ImpactAnalyzer generates consequences → 5) Auto-link affected components + related ADRs + trigger incidents → 6) Mark content requiring developer supplementation |

#### S17 — TraceabilityAnalyzer (Traceability Chain Analyzer) [P2]

| Attribute         | Description                                                                                                                                                                                                                                                                                                                                  |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Description** | Analyze and visualize BRD→ADR→Workflow→Code→Test→Deploy full-chain traceability relationships, detect broken chains and stale links                                                                                                                                                                                                                                                   |
| **Tools**    | S03 (CodeGraphQuery), S02 (KBRetriever), MCP-07 (template-render)                                                                                                                                                                                                                                                                     |
| **Permissions** | `code_graph:read`, `kb:read`                                                                                                                                                                                                                                                                                                          |
| **Reasoning Model** | Small model (graph traversal + rule detection)                                                                                                                                                                                                                                                                                                           |
| **Input**    | `{ root_entity: { type: "brd" / "adr" / "workflow", id: string }, direction: "downstream" / "upstream" / "both", depth?: int }` |
| **Output**   | `{ trace_chain: { nodes: [...], edges: [...], visualization: { mermaid_diagram }, broken_links: [{ from, to, expected_relation, missing }], stale_links: [{ from, to, last_updated, threshold_exceeded }], coverage_report: { requirements_with_implementation, requirements_without_implementation, adrs_without_implementation } }` |

S17 is the analytic engine behind the [Traceability Web](traceability-web.md) failure modes: `broken_links`, `stale_links`, and `coverage_report` all originate from this skill's output contract.

## Failure Modes & Recovery

| Failure Mode | Detection | Recovery |
|--------------|-----------|----------|
| **External API rate-limit** — Jira (30/min), Confluence/Notion (10/min), Compliance (20/min). | MCP server returns 429 / rate-limit response. | MCP server backs off and retries with exponential backoff within the timeout window; sustained limits surface to the Workbench as a throttled task. |
| **External API timeout** — Jira 15s, Confluence 30s, Compliance 10s. | Tool call exceeds configured timeout. | Fail the individual tool call; for sync/export, mark the operation retryable; for CI compliance checks, fall back to cached framework library. |
| **OAuth/PAT credential expiry. | Auth challenge from external system. | Surface a re-auth required state in the tenant's integration settings; pause scheduled syncs until re-auth. |
| **One-way sync invariant violation** — something attempts to write Jira content back into a BRD. | `get_story_status` is the only Jira→System path and is read-only by design; any write attempt is rejected. | Reject the write; BRD remains the sole Source of Truth. |
| **Compliance framework mapping drift** — a control id in the BRD no longer exists in the (updated) framework library. | MCP-22 `validate_coverage` / `get_control_detail` returns "unknown control". | Re-run `map_brd_to_framework` to re-map against the current library; review `migration_notes`-style output. |
| **Legacy import produces ambiguous YAML** — OCR/excel-parse ambiguity or missing stakeholders. | S14 emits `migration_notes` flagging manual-review items. | Draft BRD stays in draft status; human reviewer resolves notes before promotion. |
| **S15/S16 hallucination / unsupported assumptions. | Inline AssumptionCheck (ADR-0022) marks `fuzzy_nodes` / `fuzzy_decisions`; Verifier 6-round check fails on KB cross-validation. | Human reviewer confirms or rejects each fuzzy node in the Workbench before the spec leaves draft. |
| **S17 broken/stale link flood** after a large refactor. | S17 `broken_links[]` / `stale_links[]` exceed threshold. | Batch remediation in the Workbench; edges are durable so this is a curation task, not data loss. |

## Non-Functional Requirements

| NFR | Target | Rationale |
|-----|--------|-----------|
| External call isolation | Each MCP server is independently rate-limited and timeout-bounded | One slow external system must not stall the others or the BRD/ADR hub. |
| Sync determinism | Re-running `push_status` for an unchanged BRD is idempotent | Avoids flapping Jira statuses on retries. |
| Tenant isolation on egress | Every external call carries `X-Tenant-ID` and uses tenant-scoped credentials | No cross-tenant data leakage to Jira/Confluence/Compliance. |
| Export fidelity | All traceability links rendered as Confluence/Notion hyperlinks | Readers in Confluence/Notion must be able to navigate the traceability web. |
| Compliance library freshness | Tenant can extend the framework library with custom controls | Pre-loaded SOX/HIPAA/GDPR/ASC606/Basel III plus tenant custom extensions. |
| Import non-destructiveness | Legacy import only ever produces Draft YAML + `migration_notes` | No legacy content enters the source of truth without human review. |
| Skill safety | S15/S16 may only write specs in `draft` status (`spec:write` draft-only) | Per ADR-011: all AI-generated content requires human review and confirmation. |

## Key Flows

### Jira sync flow (MCP-20)

1. A BRD reaches `approved` → MCP-20 `push_status` maps it to Jira "Ready for Dev".
2. Optionally `create_epic` / `create_story_from_req` project the BRD into Jira Epic + Stories; `link_to_epic` writes the `TRACKS_BY` edge into the Code Graph (see [traceability-web.md](traceability-web.md)).
3. As work progresses, Jira webhooks feed `get_story_status` (read-only) which updates the BRD's `implementation_progress` field — without ever mutating BRD content.
4. On BRD `implemented`, `push_status` maps to Jira "Done".

### Compliance mapping flow (MCP-22)

1. BRD is drafted with `linked_compliance` references.
2. CI compliance stage (§23.7.2 stage 4) calls `validate_coverage` to ensure all necessary controls are mapped.
3. `suggest_missing_controls` offers AI-suggested additions; `get_control_detail` provides control text for the reviewer.
4. `map_brd_to_framework` is re-runnable against any supported framework (SOX/HIPAA/GDPR/ASC606/BASEL/…).

### Legacy migration flow (§23.8.3, S14)

1. Legacy artifact (Word/Excel/PDF) ingested → MCP-12 (OCR) or MCP-16 (excel-parser) extracts raw text/structure.
2. LLM structures it into BRD YAML, extracts requirements + stakeholders, and suggests associated KB entries + Workflows.
3. Output is a Draft BRD YAML + `migration_notes` (manual review items) — never a directly-active BRD.

### Generation & analysis flows (S15/S16/S17)

- **S15 BRDGenerator** — NL intent → 6-agent serial pipeline → Draft BRD YAML + `fuzzy_nodes` + `confidence_summary` + `impact_preview` + `followup_questions`. Detailed phasing (Elicitation / Generation / Verify / Assembly) lives in [`generation-pipeline.md`](generation-pipeline.md) and ADR-0022.
- **S16 ADRGenerator** — change event (`pr_merge` / `spec_diff` / `incident`) → Code Graph diff → rationale extraction → options templating → ImpactAnalyzer consequences → auto-linked components/ADRs/incidents → Draft ADR YAML + `supersedes_candidates` + `review_checklist`.
- **S17 TraceabilityAnalyzer** — root entity + direction + depth → `trace_chain` (nodes, edges, mermaid visualization) + `broken_links` + `stale_links` + `coverage_report`. This is the analytic counterpart to the [Traceability Web](traceability-web.md).

## Design References

- **§23.8, §23.9, §23.10** of [`docs/03-architecture.md`](../../03-architecture.md) — source sections for this module.
- [`../../../adr/0010-brd-adr-first-class.md`](../../../adr/0010-brd-adr-first-class.md) — ADR-0010 (referenced via §23.10 below).
- [`../../../adr/0022-brd-generation-agent-pipeline.md`](../../../adr/0022-brd-generation-agent-pipeline.md) — ADR-0022, refines S15 into the 6-agent pipeline and introduces Inline AssumptionCheck.

### §23.10 Summary: BRD/ADR Architecture Decisions

#### ADR-010: BRD and ADR as Compute Spec Subtypes

| Attribute | Description |
| ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Context** | Traditional BRD/ADR management systems treat requirements and decisions as document entities separated from implementation. The system needs a way for BRDs and ADRs to form a cohesive, traceable whole with Workflow/Code/Test/Deploy. |
| **Decision** | Model BRDs and ADRs as Compute Spec subtypes (`spec_type: brd` / `spec_type: adr`), stored in Git, with complete relationship edges to other entities in Code Graph, enjoying the same infrastructure capabilities as Workflows (version control, CI/CD validation, RBAC, audit). |
| **Rationale** | Unified abstraction eliminates the "requirements→implementation" gap — BRD creation and Workflow implementation happen in the same system; links are native, not integrated. Inheriting Compute Spec infrastructure means zero additional cost for version control, CI/CD, permissions, and audit. |
| **Consequences** | BRD/ADR YAML Schema becomes part of the system contract; CI/CD pipeline needs BRD/ADR-specific lint rules; Code Graph needs to support BRD/ADR node types and related edge types. |

Full realization: [`../../../adr/0010-brd-adr-first-class.md`](../../../adr/0010-brd-adr-first-class.md) and [compute-spec-integration.md](compute-spec-integration.md).

#### ADR-011: AI-Assisted BRD/ADR Generation with Human Review Gate

| Attribute | Description |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Context** | AI can dramatically accelerate BRD/ADR creation, but requirements and architecture decisions have legal and compliance implications and cannot be fully automated. |
| **Decision** | AI Agent auto-drafts BRDs/ADRs (S15/S16), generating complete structured YAML + fuzzy_nodes markers. S15 has been internally refined by ADR-0022 into a 6-Agent serial pipeline (IntentDeepener/ContextGatherer/VaguenessResolver/DraftWriter/Verifier/Assembler), introducing Inline AssumptionCheck to prevent hallucination snowballing. All AI-generated content requires Workbench human review and confirmation. BRDs require stakeholder approval; ADRs require architecture review (in_discussion → accepted). ADRs are immutable once accepted. |
| **Rationale** | Combines AI speed with human judgment. Atomic Claim Decomposition + NLI verification ensures AI uncertainty is transparently visible; it not only marks LLM-self-known fuzzy_nodes, but also detects LLM-confident business assumptions lacking KB support. Immutable accepted ADRs guarantee historical decision traceability. |
| **Consequences** | Requires development of S15 (6-Agent internal pipeline) and S16 (ADRGenerator); Workbench needs BRD/ADR editing, Inline AssumptionCheck interaction, per-Section progressive rendering UI; requires implementation of BRD/ADR approval workflow engine. |

Full realization: [`../../../adr/0022-brd-generation-agent-pipeline.md`](../../../adr/0022-brd-generation-agent-pipeline.md), [generation-pipeline.md](generation-pipeline.md), and [lifecycle-state-machine.md](lifecycle-state-machine.md).

#### ADR-012: Code Graph as Single Source of Traceability Truth

| Attribute             | Description                                                                                                                                                      |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Context** | Requirements traceability matrices are traditionally static Excel spreadsheets, disconnected from real-time system state. |
| **Decision** | Use Code Graph as the single source of truth for all traceability relationships. All BRD→ADR→Workflow→Code→Test→Deploy relationships are stored as graph edges, updated in real time, and queryable via Cypher and natural language. |
| **Rationale** | Graph databases are naturally suited for modeling many-to-many traceability relationships; real-time updates mean "impact analysis" is always based on the latest state; natural language queries (via S03) enable non-technical users to explore traceability relationships. |
| **Consequences** | Code Graph needs new BRD/ADR node types and 12+ relationship edge types; query performance needs optimization (multi-level traversal may require index optimization); S17 (TraceabilityAnalyzer) needs to be developed for broken link detection. |

Full realization: [traceability-web.md](traceability-web.md).

### Cross-references

- [`README.md`](README.md) — sub-project overview and module list.
- [`traceability-web.md`](traceability-web.md) — the edge catalog that MCP-20 `link_to_epic` and S17 operate over.
- [`compute-spec-integration.md`](compute-spec-integration.md) — CI compliance stage consumes MCP-22; Export Capability row references MCP-21.
- [`generation-pipeline.md`](generation-pipeline.md) — S15/S16 internal agent pipelines.
- [`lifecycle-state-machine.md`](lifecycle-state-machine.md) — the `approved`/`implemented`/`accepted` states that MCP-20 `push_status` projects to Jira.
