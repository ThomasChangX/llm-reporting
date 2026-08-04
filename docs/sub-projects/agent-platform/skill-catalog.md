# Skill Catalog

> **Origin**: §22B of [`docs/03-architecture.md`](../../03-architecture.md) | **Sub-project**: [agent-platform](README.md)

## Purpose

This module covers the **Complete Skill Catalog** (§22B). A **Skill** is a reusable, composable Agent capability module. Each Skill contains: name, description, tools (MCP endpoints), permissions, input/output Schema, reasoning model preference — and **orchestration metadata** (`prerequisites`, `compatible_with`, `side_effects`, `fallback`), used by the LLM for correct orchestration in Exploration Mode and as reference for Verified Path definition.

This module owns:
- **Skill Orchestration Metadata** — the metadata fields carried by every Skill, consumed by the Agent runtime for orchestration decisions.
- **P0 Skills (Core Required, MVP Delivery)** — S01 IntentParser, S02 KBRetriever, S03 CodeGraphQuery, S04 ImpactAnalyzer, S05 SpecGenerator, S06 DocGenerator, S07 IncidentDiagnostician, S08 DataQualityAdvisor (with closed-loop learning), S09 ReconBreakAnalyzer, S10 EmailFactExtractor, and S18 PlaybookRouter.
- **P1–P2 Skills (Advanced Capabilities, Later Delivery)** — S11 BehaviorObserver, S12 CodeReviewer, S13 OnboardingWizard, S14 MigrationAdvisor.

## Boundaries

**In-scope:**
- §22B — the Skill concept, the orchestration metadata fields (`prerequisites`, `compatible_with`, `incompatible_with`, `side_effects`, `produces`, `fallback`, `verified_paths`), and their role in Exploration-Mode and Verified Path execution.
- All P0 Skill definitions: S01–S10 and S18 (description, tools, permissions, reasoning model, input, output, plus Skill-specific catalogs/triggers such as S01 Intent Catalog, S02 Retrieval Flow, S08 Closed-Loop Learning trigger table, S18 Playbook Sources + Closed Loop).
- All P1–P2 Skill definitions: S11–S14.

**Delegated / out-of-scope:**
- How Skills are invoked by the runtime (Planner, Permission Gate, Executor) → [`dual-mode-orchestration.md`](dual-mode-orchestration.md) (§22A.1/§22A.2).
- The MCP endpoints each Skill lists under `Tools` → [`mcp-catalog.md`](mcp-catalog.md) (§22C).
- The Verified Path definitions that reference Skills via `verified_paths` → `verified-path-and-governance.md` (§22F–§22H).
- The 7-layer security that enforces each Skill's `permissions` → [`agent-security.md`](agent-security.md) (§22D).
- Agent memory tiers (L1–L4) referenced by S18's Closed Loop (L2 Episodic Memory) → `memory-and-evaluation.md` (§22I), [ADR-0019](../../../adr/0019-agent-memory-architecture.md).
- KB domains retrieved by S02/S05/etc. → [`knowledge-services`](../knowledge-services/).

**Upstream/downstream neighbors:**
- *Input*: caller (Agent runtime or another Skill) supplies the documented input schema; S01 IntentParser consumes raw user NL text.
- *Output*: the documented output schema (entities, retrieved KB entries, impact reports, Design Artifacts, generated docs, diagnoses, DQ rule drafts, recon break classifications, extracted facts, playbooks, etc.).

## Interfaces

> Skill = reusable, composable Agent capability modules. Each Skill contains: name, description, tools (MCP endpoints), permissions, input/output Schema, reasoning model preference — and **orchestration metadata** (prerequisites, compatible_with, side_effects, fallback), used by the LLM for correct orchestration in Exploration Mode and as reference for Verified Path definition.

### Skill Orchestration Metadata (Carried by Each Skill)

| Field | Description | Purpose |
|---|---|---|
| `prerequisites` | Skills that must be executed first | Mandatory prerequisite during LLM orchestration; execution rejected if missing |
| `compatible_with` | Skills that can execute in parallel | LLM can place in the same parallel batch during orchestration |
| `incompatible_with` | Skills that cannot run in parallel (competing locks/resources) | LLM avoids parallelism during orchestration |
| `side_effects` | State changes produced | In Exploration Mode, Skills with side_effect ≠ [] are restricted; in Verified Path, marks Gate requirements |
| `produces` | Output entity type | Downstream Skill matches input type |
| `fallback` | Degradation strategy on failure | Auto-switch on LLM or Verified Path step failure |
| `verified_paths` | List of Verified Paths participated in | Reverse index — which compliance paths depend on this Skill |

### P0 Skills (Core Required, MVP Delivery)

#### S01 — IntentParser (Intent Parser)

| Attribute                         | Description                                                                                                                                                                                                                                                                                              |
| --------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Description**                   | Classify user natural language into system predefined intents, extract structured entities, route to the best Skill                                                                                                                                                                                       |
| **Tools**                         | None (pure LLM reasoning, no external tool calls)                                                                                                                                                                                                                                                        |
| **Permissions**                   | None (only consumes user input text, does not access any data)                                                                                                                                                                                                                                           |
| **Reasoning Model**               | Small model: Claude Haiku / GPT-4o-mini / DeepSeek-Lite                                                                                                                                                                                                                                                  |
| **Input**                         | `{ query: string, session_context: { role, capabilities } }`                                                                                                                                                                                                                                             |
| **Output**                        | `{ intent: string, entities: { key: value }, confidence: float, routed_skill: string, fallback_skills: [string], reasoning: string }`                                                                                                                                                                    |
| **Intent Catalog** (50+ predefined intents) | `create_report`, `modify_report`, `query_kb`, `analyze_impact`, `diagnose_incident`, `explain_lineage`, `suggest_dq_rules`, `classify_recon_break`, `extract_email_facts`, `review_code`, `onboarding_help`, `migration_advice`, `schedule_workflow`, `audit_query`, `compare_versions`, `generate_doc`… |
| **Entity Types**                  | `workflow_name`, `data_source`, `time_range`, `metric`, `dimension`, `incident_id`, `person`, `branch`, `file_path`…                                                                                                                                                                                     |

#### S02 — KBRetriever (Knowledge Base Retriever)

| Attribute | Description |
| --------- | ----------- |
| **Description** | Hybrid retrieval (semantic + keyword + graph traversal) from the nine domains of the Knowledge Base, retrieving the most relevant knowledge entries |
| **Tools** | MCP-01 (vector-search), MCP-02 (graph-traverse), MCP-04 (pg-query) |
| **Permissions** | `kb:read` (role-filtered — Dev cannot query business data definitions in Business Glossary, only technical metadata) |
| **Reasoning Model** | Small model (Embedding matching + result re-ranking); Embedding model: `text-embedding-3-large` or tenant-configured private model |
| **Input** | `{ query: string, domains?: [glossary                                                                                                                                                                 | catalog | mapping | template | adjustment | behavior], filters?: { tenant, date_range, owner }, top_k?: int, expand_graph?: bool }` |
| **Output** | `{ results: [{ kb_id, domain, title, snippet, score, source_confidence, graph_related: [{kb_id, relation}] }], total_found: int, search_latency_ms: int }`                                            |
| **Retrieval Flow** | Step 1: Embedding semantic search (Vector DB, top_k=60) → Step 2: Keyword/metadata filtering → Step 3: Relationship expansion (Graph DB, 1-hop) → Step 4: Fusion ranking (Semantic score × 0.5 + Keyword score × 0.25 + Relationship score × 0.15 + Freshness × 0.10) |

#### S03 — CodeGraphQuery (Code Graph Query)

| Attribute | Description |
| --------- | ----------- |
| **Description** | Translates natural language questions into Cypher/Gremlin graph queries, executes them, and traverses + formats results in the Code Graph |
| **Tools** | MCP-03 (graph-query), the `nl_to_cypher` endpoint within MCP-03 |
| **Permissions** | `code_graph:read` (role-filtered — Dev can query full structure; Business User can only query Workflows/DataSources they own) |
| **Reasoning Model** | Small model (NL→Cypher translation); Large model (complex traversal result explanation) |
| **Input** | `{ question: string, entity_filters?: { type: "DataSource" or "Workflow" or "Job" or ..., name?: string, owner?: string }, traversal_depth?: int }` |
| **Output**         | `{ cypher_query: string, results: { nodes: [...], edges: [...] }, natural_language_summary: string, visualization_data?: { dag_json } }`                |
| **Typical Query Example** | "Which Workflows consume sales_orders from ERP?" → `MATCH (ds:DataSource {name:'sales_orders'})-[r:READS_FROM]-(j:Job)-[:BELONGS_TO]-(w:Workflow) RETURN w` |

#### S04 — ImpactAnalyzer (Impact Analyzer)

| Attribute         | Description                                                                                                                                                                                                                                                                                 |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Description** | Given a change (Spec diff / data source change / KB entry change), compute upstream sources and downstream impact scope, generate impact DAG report                                                                                                                                                                                  |
| **Tools**    | S02 (KBRetriever), S03 (CodeGraphQuery), MCP-06 (git-diff)                                                                                                                                                                                                                           |
| **Permissions** | `code_graph:read`, `kb:read` (same role filtering as S02, S03)                                                                                                                                                                                                                             |
| **Reasoning Model** | Large model (Sonnet/DeepSeek-R1) — needs to reason about indirect impact chains                                                                                                                                                                                                                                     |
| **Input**    | `{ change_source: { type: "spec_diff" or "datasource_change" or "kb_change", payload: { branch_a, branch_b, path? } or { source_id, change_desc } or { kb_id, change_desc } } }` |
| **Output**   | `{ impact_report: { summary: string, upstream_impact: [{ entity, impact_type, severity, detail }], downstream_impact: [{ entity, impact_type, severity, detail }], indirect_impact: [{ entity, path: [intermediaries], impact_type }], affected_owners: [user_id], risk_level: "LOW" or "MEDIUM" or "HIGH" or "CRITICAL", suggested_reviewers: [user_id] }, dag_json: {...}, confidence: float }` |

#### S05 — SpecGenerator (Compute Spec Generator)

| Attribute | Description |
| --------- | ----------- |
| **Description** | Generate or modify Compute Spec YAML (Reporting/ETL/Adjustment/Recon) from natural language intent, producing a Design Artifact rather than a production Spec |
| **Tools** | S02 (KBRetriever), MCP-07 (template-search) |
| **Permissions** | `kb:read`, `spec:write` (Note: `spec:write` only allows writing to **draft** status, cannot write directly to production) |
| **Reasoning Model** | Large model (requires understanding of complex computation logic and business rules) |
| **Input** | `{ intent: string, entities: {...}, existing_spec_id?: string, modification_type?: "create" or "modify" or "extend" }` |
| **Output**     | `{ design_artifact: { artifact_id, spec: {...}, fuzzy_nodes: [...], confirmed_fields: [...], confidence_summary: { overall, fully_confirmed, fuzzy, unresolved } }, explanation: string, followup_questions?: [string] }` |
| **Constraints**     | The output `fuzzy_nodes` must mark all areas where the AI is uncertain; when `confidence_summary.overall < 0.8`, automatically prompts for deep review |

#### S06 — DocGenerator (Document Generator)

| Attribute    | Description                                                                                                                |
| ------------ | --------------------------------------------------------------------------------------------------------------------------- |
| **Description** | Generate Human-Readable documents from structured data: Impact Report, Post-Change Summary, ADR, BRD, Recon Report, etc.                         |
| **Tools**    | S02 (KBRetriever), S03 (CodeGraphQuery), S04 (ImpactAnalyzer), MCP-07 (template-render)                                     |
| **Permissions** | `kb:read`, `code_graph:read`                                                                                                |
| **Reasoning Model** | Large model (long document structuring and professional writing)                                                                                            |
| **Input**    | `{ doc_type: "impact_report" or "post_change_summary" or "adr" or "brd" or "recon_report" or "incident_postmortem", data: {...}, format: "md" or "pdf", template_id?: string }` |
| **Output**   | `{ document: string (MD/PDF), sections: [{ title, content, citations }], toc: [...], estimated_reading_time_minutes: int }` |

#### S07 — IncidentDiagnostician (Incident Diagnostician)

| Attribute         | Description                                                                                                                                                                                                                                                                                             |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Description**   | Analyze Workflow execution failure: correlate logs, trace error chain, reason about root cause, suggest remediation                                                                                                                                                                                                                             |
| **Tools**         | MCP-05 (log-search), MCP-09 (incident-query), S03 (CodeGraphQuery)                                                                                                                                                                                                                               |
| **Permissions**   | `log:read` (within tenant), `code_graph:read` — log content filtered by role: Dev sees technical error stack; Business User only sees business error description                                                                                                                                                                                  |
| **Reasoning Model** | Large model (multi-source correlation reasoning — logs + code graph + historical Incidents)                                                                                                                                                                                                                                          |
| **Input**         | `{ incident_id?: string, workflow_id?: string, execution_id?: string, time_range?: { start, end } }`                                                                                                                                                                                             |
| **Output**   | `{ diagnosis: { root_cause: string, confidence: float, evidence_chain: [{ source, entry, relevance }], contributing_factors: [string], suggested_fix: { action, risk_level, requires_approval }, related_incidents: [{ incident_id, similarity }] }, timeline: [{ timestamp, event, source }] }` |

#### S08 — DataQualityAdvisor (Data Quality Advisor + Closed-Loop Learning)

| Property          | Description                                                                                                                                                                                                                                                        |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Description**       | **Bidirectional**: (a) Analyze data Profile statistics, suggest DQ rules; generate DQ Rule YAML draft (b) **Closed-loop learning** — receive user action signals (false positive flagging, repeated inquiries), automatically suggest rule optimization              |
| **Tools**             | MCP-08 (data-profile), S02 (KBRetriever)                                                                                                                                                                                                                           |
| **Permissions**       | `kb:read`, `source:read` (sampled data limited to first 10,000 rows; T3 columns auto-redacted)                                                                                                                                                                      |
| **Reasoning Model**   | Small model (statistical analysis + pattern matching)                                                                                                                                                                                                              |
| **Input**             | `{ source_id: string, sample_size?: int, focus_dimensions?: [...], feedback_signal?: { type: "false_positive" \| "repeated_inquiry" \| "coverage_gap", rule_id?: string, anomaly_id?: string, metadata: {...} } }` |
| **Output**            | `{ suggested_rules: [...], anomalies_detected: [...], dq_rule_yaml: string (draft), optimization_suggestions?: [{ target_rule_id, issue: "high_false_positive_rate" \| "needs_automation" \| "coverage_gap", current_state: {...}, suggestion: {...}, evidence: {...} }] }` |

**Closed-Loop Learning Trigger Signals**:

| Signal | Threshold | S08 Response |
|---|---|---|
| User flags "False Positive" | Same rule flagged 3 times within 7 days | Suggest downgrading severity or adjusting threshold / adding exclusion rule → L1 confirmation |
| User repeatedly inquires about same anomaly | Same anomaly check ≥5 times within 30 days | Suggest hardening as `type: rule` (auto-attribution + push summary) → L2 approval |
| Coverage Gap detection | Some metric within scope has zero checks | Suggest creating anomaly check (default config) → L0 auto-generate draft |
| Rule has zero triggers for long period | 90 days with zero triggers | Suggest evaluating whether outdated / invalidated by upstream changes → L1 confirmation |

#### S09 — ReconBreakAnalyzer (Reconciliation Break Analyzer)

| Property          | Description                                                                                                                                       |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Description**       | After reconciliation completes, classify break items (Unmatched/Partial), infer causes, suggest resolution paths                                   |
| **Tools**             | S02 (KBRetriever), MCP-04 (pg-query) — query historical Recon records                                                                             |
| **Permissions**       | `kb:read` (only Business Glossary + Mapping Registry + Adjustment History domains)                                                                |
| **Reasoning Model**   | Large model (needs to combine KB and historical patterns to infer break causes)                                                                   |
| **Input**             | `{ recon_result: { matched_count, unmatched_count, partial_count, unmatched_items: [...], partial_items: [...] }, recon_rule_id: string }` |
| **Output**            | `{ classified_breaks: [{ item, break_type: "TIMING" or "MISSING" or "ROUNDING" or "MAPPING" or "UNKNOWN", confidence, explanation, resolution_suggestion: { action, detail } }], summary: { by_type: {...}, suggested_adjustments: [...], items_for_human_review: [...] } }` |

#### S10 — EmailFactExtractor (Email Fact Extractor)

| Property          | Description                                                                                                                                                                                                           |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Description**       | Extract objective facts (numbers, dates, definitions, decisions) from email content, with source citations; write to KB (draft status, requires human confirmation)                                                    |
| **Tools**             | MCP-12 (ocr), MCP-11 (email-parser), LLM inference                                                                                                                                                                    |
| **Permissions**       | `kb:write` (draft only, takes effect after confirm)                                                                                                                                                                   |
| **Reasoning Model**   | Large model (requires fine-grained semantic understanding to distinguish fact from opinion)                                                                                                                           |
| **Input**             | `{ email_id: string, email_record: { from, to, date, subject, body, attachments: [...] } }`                                                                                                                    |
| **Output**            | `{ extracted_facts: [{ fact_type, content, confidence, source_citation: { sentence, position }, suggested_kb_domain, requires_human_review }], conflicts_with_existing_kb: [{ fact, conflicting_kb_entry }] }` |

### P1-P2 Skills (Advanced Capabilities, Later Delivery)

#### S11 — BehaviorObserver (Behavior Observer) [P1]

| Property          | Description                                                                                                                             |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| **Description**       | Detect repetitive operation patterns from user activity stream, suggest Workflow automation                                              |
| **Tools**             | MCP-10 (user-activity-stream)                                                                                                           |
| **Permissions**       | `user_behavior:read` (same tenant only; cross-tenant learning prohibited)                                                               |
| **Reasoning Model**   | Small model (sequential pattern mining + rule matching)                                                                                |
| **Input**             | `{ user_id: string, time_window_days?: int }`                                                                                    |
| **Output**            | `{ detected_patterns: [{ pattern_id, action_sequence, frequency, temporal_pattern, suggested_workflow_template, confidence }] }` |

#### S12 — CodeReviewer (Code Reviewer) [P1]

| Property          | Description                                                                                                                                              |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Description**       | Review Spec changes: detect anti-patterns, security issues (SQL injection, Python sandbox escape), performance risks, best practice deviations            |
| **Tools**             | S03 (CodeGraphQuery), MCP-06 (git-diff), MCP-13 (static-analysis)                                                                                        |
| **Permissions**       | `code_graph:read`                                                                                                                                        |
| **Reasoning Model**   | Large model (requires deep understanding of code semantics and system context)                                                                           |
| **Input**             | `{ pr_id: string, diff: string, static_analysis_results: {...} }`                                                                                 |
| **Output**            | `{ review: { summary, issues: [{ severity, category, file, line, description, suggestion, autofix_possible }], approval_recommendation: "APPROVE" or "COMMENT" or "REQUEST_CHANGES", risk_level } }` |

#### S13 — OnboardingWizard (Onboarding Wizard) [P2]

| Property          | Description                                                                                      |
| ----------------- | ------------------------------------------------------------------------------------------------ |
| **Description**       | Guide new users through: Data source connection → Schema discovery → KB seeding → First report creation |
| **Tools**             | S02 (KBRetriever), S05 (SpecGenerator), MCP-15 (data-source-test)                                |
| **Permissions**       | `kb:write`, `spec:write`, `source:read`                                                          |
| **Reasoning Model**   | Small model (wizard-style dialogue, fixed steps)                                                 |
| **Input**             | `{ user_id, tenant_id, industry?: string, role?: string }`                                |
| **Output**            | `{ onboarding_plan: [{ step, status, required_actions, ai_guidance }], progress: float }` |

#### S14 — MigrationAdvisor (Migration Advisor) [P2]

| Property          | Description                                                                                                                                                                         |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Description**       | Analyze legacy Excel/PowerBI artifacts, suggest corresponding Compute Spec structure and KB mappings                                                                                 |
| **Tools**             | MCP-16 (excel-parser), MCP-16 PowerBI API adapter, S02 (KBRetriever)                                                                                                                |
| **Permissions**       | `kb:read`                                                                                                                                                                           |
| **Reasoning Model**   | Large model (needs to understand unstructured computation logic)                                                                                                                    |
| **Input**             | `{ artifact_type: "excel" or "powerbi", file_bytes?: bytes, connector_config?: {...} }` |
| **Output**            | `{ proposed_spec: { workflow, jobs, formats }, migration_notes: [{ original_element, proposed_equivalent, confidence, manual_review_needed }], unmappable_elements: [...] }` |

#### S18 — PlaybookRouter (Diagnostic Playbook Router) [P1] → ADR-0024

| Attribute | Description |
| --------- | ----------- |
| **Description** | Match a user's diagnostic intent against the Diagnostic Playbooks KB domain; inject the matched playbook as a guided plan into the Skill Planner. Acts as the "soft skeleton" for Exploration-Mode diagnostics — the read-only counterpart to Verified Paths (ADR-0016). |
| **Tools** | S02 (KBRetriever — query the Diagnostic Playbooks domain), S01 (IntentParser — trigger matching) |
| **Permissions** | `kb:read` (role-filtered — playbooks are tenant-isolated; system-builtin playbooks are shared across tenants but contain no tenant data) |
| **Reasoning Model** | Small model (intent → playbook trigger matching); Large model (playbook step adaptation based on observations — the LLM reasons within the skeleton) |
| **Input** | `{ intent: string, entities: {...}, session_context: {...} }` (typically the output of S01 IntentParser) |
| **Output** | `{ matched_playbook: { id, name, steps: [...], confidence_thresholds: {...} }, routing_path: "explicit" or "implicit", fallback: "pure_react" }`. If no playbook matches, `matched_playbook: null` and `routing_path: "pure_react"` — the Agent falls back to unconstrained ReAct, preserving backward compatibility. |
| **Playbook Sources** | Three confidence-tagged sources (align ADR-0019): system-builtin (conf 1.0, shipped patterns), incident-distilled (model_inferred, conf 0.7-0.9, promoted after ≥3 recurrences + human confirm), user-defined (user_stated, conf 1.0, team SOP) |
| **Closed Loop** | Successful diagnostic trajectories stored in L2 Episodic Memory (ADR-0019); ≥3 recurrences → LLM proposes distillation into a new Playbook candidate → user confirms → promoted to domain (reuses S08 closed-loop pattern, ADR-0015) |

## Dependencies

- **MCP catalog** ([`mcp-catalog.md`](mcp-catalog.md), §22C) — every Skill's `Tools` field lists MCP endpoints (e.g., S02 → MCP-01/02/04; S07 → MCP-05/09; S08 → MCP-08; S10 → MCP-11/12; S12 → MCP-06/13; S13 → MCP-15; S14 → MCP-16).
- **Agent runtime** ([`dual-mode-orchestration.md`](dual-mode-orchestration.md), §22A) — loads Skill definitions from the immutable registry; uses orchestration metadata for parallelism, gating, and fallback.
- **Agent security** ([`agent-security.md`](agent-security.md), §22D) — enforces each Skill's `permissions` (e.g., `kb:read`, `spec:write`, `source:read`, `code_graph:read`, `user_behavior:read`) through the Permission Gate.
- **Knowledge services** ([`knowledge-services`](../knowledge-services/)) — KB nine-domain retrieval (S02), Code Graph (S03, S04, S06, S07, S12), Diagnostic Playbooks domain (S18).
- **Workflow engine** ([`workflow-engine`](../workflow-engine/)) — S05 writes Compute Spec drafts; S06 generates Impact/Post-Change/Recon docs; S04/S06 reason over Spec diffs and impact DAGs.
- **Agent memory** ([ADR-0019](../../../adr/0019-agent-memory-architecture.md)) — S18 stores successful trajectories in L2 Episodic Memory; S08 reuses the ADR-0015 closed-loop pattern.

## Data Model

- **Skill definition (immutable registry entry)** — `{ name, description, tools[], permissions[], input_schema, output_schema, reasoning_model_preference, orchestration_metadata }`.
- **Orchestration metadata** — `{ prerequisites[], compatible_with[], incompatible_with[], side_effects[], produces, fallback, verified_paths[] }`.
- **S01 Intent Catalog** — 50+ predefined intents (`create_report`, `modify_report`, `query_kb`, `analyze_impact`, `diagnose_incident`, `explain_lineage`, `suggest_dq_rules`, `classify_recon_break`, `extract_email_facts`, `review_code`, `onboarding_help`, `migration_advice`, `schedule_workflow`, `audit_query`, `compare_versions`, `generate_doc`, …).
- **S01 Entity Types** — `workflow_name`, `data_source`, `time_range`, `metric`, `dimension`, `incident_id`, `person`, `branch`, `file_path`, ….
- **S02 Retrieval ranking weights** — Semantic × 0.5 + Keyword × 0.25 + Relationship × 0.15 + Freshness × 0.10.
- **S08 Closed-Loop trigger thresholds** — 3 false-positives/7 days, 5 inquiries/30 days, zero-check coverage gap, 90 days zero triggers.
- **S18 Playbook source confidence** — system-builtin 1.0; incident-distilled 0.7–0.9 (≥3 recurrences + confirm); user-defined 1.0.
- **S05 confidence gating** — `confidence_summary.overall < 0.8` triggers a deep-review prompt.

## Failure Modes & Recovery

| Failure | Impact | Detection | Recovery |
| ------- | ------ | --------- | -------- |
| **Orchestration missing prerequisite** | Skill called before its prerequisite | `prerequisites` metadata checked by the runtime; execution rejected if missing (§22B metadata) | Reject execution; surface missing prerequisite to caller |
| **Skill `fallback` triggered** | Skill or model fails mid-step | `fallback` metadata declares degradation strategy | Auto-switch per the Skill's `fallback` policy |
| **S02 returns irrelevant KB context** | Low-quality suggestions | S02 `source_confidence` / `score` below threshold; S05 `confidence_summary.overall < 0.8` | Re-rank / re-query; prompt deep review (S05) |
| **S05 produces unresolved `fuzzy_nodes`** | Non-deterministic Spec | `confidence_summary.unresolved > 0` | Freeze Bridge rejects; mandatory human resolution before freeze (see `workflow-engine` `freeze-pipeline.md`) |
| **S07 root-cause confidence low** | Misdiagnosis | `diagnosis.confidence` below threshold; related-incidents similarity low | Mark low-confidence; surface contributing factors + suggested_fix.requires_approval |
| **S08 DQ rule high false-positive rate** | Noisy alerts | ≥3 false-positive flags / 7 days | Suggest severity downgrade / threshold adjust / exclusion rule → L1 confirmation |
| **S10 extracted fact conflicts with existing KB** | KB inconsistency | `conflicts_with_existing_kb` non-empty | Flag for human review; draft only (takes effect after confirm) |
| **S18 no playbook matches** | No guided skeleton | `matched_playbook: null` | `routing_path: "pure_react"` — fall back to unconstrained ReAct (backward compatible) |
| **Permission denied for a Skill's `permissions`** | Unauthorized access attempt | Permission Gate 4-dim check (§22D Layer 2) | `DENY` + SECURITY-level audit log + alert |

## Non-Functional Requirements

- **Reusable & composable** — each Skill is a self-contained capability module with declared tools, permissions, schemas, and orchestration metadata (§22B).
- **Side-effect-restricted in Exploration Mode** — Skills with `side_effect ≠ []` are restricted in Exploration Mode; in Verified Path they mark Gate requirements (§22B `side_effects`).
- **Validated reasoning models only** — each Skill declares its reasoning-model preference; tenants may only select validated models per the §22A.5 constraint (arbitrary selection unsupported; degraded models marked).
- **Role-filtered permissions** — every `permissions` field is enforced with role-aware filtering (e.g., S02 Dev vs Business User KB visibility; S07 Dev technical-stack vs Business business-description logs; S18 tenant-isolated vs shared system-builtin playbooks).
- **Sample/PII-bounded data access** — S08 limits sampled data to the first 10,000 rows with T3 columns auto-redacted; S09 restricts to specific KB domains; S11 same-tenant only (cross-tenant learning prohibited).
- **Draft-only writes** — S05 `spec:write` and S10 `kb:write` write only to draft status (production impact requires downstream confirmation/freeze).
- **Cited, confidence-scored outputs** — S06 docs carry per-section citations; S04/S07/S09/S10 outputs carry confidence scores; S05 auto-prompts deep review below 0.8.
- **Backward-compatible fallback** — S18 falls back to `pure_react` when no playbook matches; Skills declare `fallback` strategies for graceful degradation.

## Key Flows

### Skill invocation (runtime-driven, §22B metadata → §22A.1/§22A.2)

```
S01 IntentParser classifies → routes to routed_skill (with fallback_skills)
  → Skill Planner loads Skill definition (tools, system prompt, orchestration metadata)
    → checks prerequisites (reject if missing)
    → batches compatible_with Skills in parallel; avoids incompatible_with
    → Permission Gate per tool-call (permissions × Session Context)
    → Parallel Executor (MCP backends)
    → on failure → Skill fallback strategy
```

### S02 KBRetriever retrieval flow

```
Step 1: Embedding semantic search (Vector DB, top_k=60)
Step 2: Keyword/metadata filtering
Step 3: Relationship expansion (Graph DB, 1-hop)
Step 4: Fusion ranking (Semantic × 0.5 + Keyword × 0.25 + Relationship × 0.15 + Freshness × 0.10)
```

### S05 SpecGenerator → Design Artifact

```
intent + entities + existing_spec_id? + modification_type?
  → S02 (KBRetriever) + MCP-07 (template-search)
  → Large-model reasoning over computation logic + business rules
  → design_artifact { spec, fuzzy_nodes, confirmed_fields, confidence_summary }
  → if confidence_summary.overall < 0.8 → prompt deep review
```

### S08 DataQualityAdvisor closed loop

```
feedback_signal (false_positive | repeated_inquiry | coverage_gap)
  → threshold check (3/7d | 5/30d | zero-check | 90d zero-trigger)
  → optimization_suggestion (severity downgrade / harden to rule / create check / evaluate outdated)
  → approval tier (L0 auto-draft | L1 confirm | L2 approval)
```

### S18 PlaybookRouter routing

```
S01 IntentParser output (intent + entities + session_context)
  → match against Diagnostic Playbooks KB domain (system-builtin / incident-distilled / user-defined)
  → match? → inject matched_playbook as guided plan into Skill Planner (LLM reasons within skeleton)
       └─ success → store trajectory in L2 Episodic Memory (ADR-0019)
            └─ ≥3 recurrences → LLM proposes new Playbook candidate → user confirms → promote to domain
  → no match? → routing_path: "pure_react" (unconstrained ReAct, backward compatible)
```

### Shared runtime sequence

The end-to-end Agent query — including S01 IntentParser routing and the downstream Skill/MCP invocations gated by the Permission Gate — is documented in [`../_shared/sequence-diagrams.md`](../_shared/sequence-diagrams.md) **§21.3 AI Agent Query with Permission Gating**. That sequence is the canonical reference for how Skills from this catalog are dispatched at runtime and is co-owned with [`knowledge-services`](../knowledge-services/) (Code Graph, KB Vector/Relational) and [`platform-core`](../platform-core/) (Auth, Log Store).

## Design References

- **Original sections**: §22B (Complete Skill Catalog), including the Skill Orchestration Metadata table, the P0 Skills (S01–S10, S18), and the P1–P2 Skills (S11–S14) of [`docs/03-architecture.md`](../../03-architecture.md).
- **Related agent-platform docs**: [`dual-mode-orchestration.md`](dual-mode-orchestration.md) (§22A — how the runtime invokes these Skills), [`mcp-catalog.md`](mcp-catalog.md) (§22C — the MCP endpoints each Skill's `Tools` reference), [`agent-security.md`](agent-security.md) (§22D — enforcement of each Skill's `permissions`).
- **Shared sequence diagram**: [`../_shared/sequence-diagrams.md`](../_shared/sequence-diagrams.md) §21.3 AI Agent Query with Permission Gating (primary sub-project).
- **ADRs** ([index](../../adr-index.md)): [ADR-0015 Agent Triage/Remediation Gateway](../../../adr/0015-agent-triage-remediation-gateway.md) (S08 closed-loop pattern reused by S18), [ADR-0016 Dual-Mode Agent Orchestration](../../../adr/0016-dual-mode-agent-orchestration.md) (S18 is the read-only counterpart to Verified Paths), [ADR-0019 Agent Memory Architecture](../../../adr/0019-agent-memory-architecture.md) (S18 L2 Episodic Memory + playbook confidence tagging), [ADR-0024 KB Reasoning Support](../../../adr/0024-kb-reasoning-support-playbooks-code.md) (S18 PlaybookRouter + Diagnostic Playbooks/Code Knowledge).
- **Glossary** ([../../glossary.md](../../glossary.md)): Skill, Orchestration Metadata, Intent Catalog, Closed-Loop Learning, Design Artifact, Diagnostic Playbook, Playbook Sources.
- **Cross-references retained from source**: §22A (runtime that loads/invokes Skills), §22C (MCP endpoints listed under each Skill's Tools), §22D (permission enforcement), §22F–§22H (Verified Paths referencing Skills via `verified_paths`), ADR-0015/0016/0019/0024.
