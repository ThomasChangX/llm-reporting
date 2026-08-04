# BRD Entity Model

> **Origin**: §23.2 of [`docs/03-architecture.md`](../../03-architecture.md) | **Sub-project**: [brd-adr-lifecycle](README.md)

## Purpose

The Business Requirements Document (BRD) is a structured YAML entity within the system (a Compute Spec subtype declared by `spec_type: brd`), stored in Git repositories, and establishing **bidirectional relationship edges with all other entities** through the Code Graph. This module defines the canonical shape of a BRD: the YAML schema that makes a BRD fully machine-readable and queryable, and the Code Graph node model that links a BRD to the regulations, ADRs, Jira epics, workflows, data sources, and knowledge-base entries it must stay consistent with.

By treating the BRD as structured data rather than a free-text document, the system can: (1) automatically trace every requirement to the workflows that implement it and the KB entries that define it; (2) drive CI/CD validation against the BRD's acceptance criteria; (3) detect, via the Code Graph, when a downstream entity changes in a way that makes the BRD stale (the `needs_update` lifecycle state — see [Lifecycle State Machine](lifecycle-state-machine.md)); and (4) generate BRDs through the AI-assisted pipeline (see [Generation Pipeline](generation-pipeline.md)).

This module covers §23.2 in full: the §23.2.1 BRD YAML Schema and the §23.2.2 BRD-as-Code-Graph-Node model.

## Boundaries

**In scope**

- The complete BRD YAML schema (§23.2.1): identity, stakeholders, business context, requirements (with acceptance criteria and linked entities), data flows, traceability, and the Jira/Rally multi-level structure mapping.
- The BRD as a Code Graph node (§23.2.2): the `BRD` node type and its typed relationship edges to ADR, Regulation, Jira Epic, Workflow, Data Source, and KB Entry.

**Out of scope**

- The BRD **lifecycle** state machine (draft → in_review → approved …, 16 states) — see [Lifecycle State Machine](lifecycle-state-machine.md).
- The **AI-assisted generation** of BRDs (the 8-agent pipeline) — see [Generation Pipeline](generation-pipeline.md).
- The **ADR entity model** — see [ADR Entity Model](adr-entity-model.md).
- The full **traceability web** relationship matrix (BRD ↔ all entities across the system) — covered by the parent architecture's §23.6.
- BRD/ADR as **Compute Spec types** (capability inheritance, CI/CD validation pipeline) — covered by the parent architecture's §23.7.
- The underlying **Code Graph storage** (Neo4j node/edge persistence) — owned by the [`knowledge-services`](../knowledge-services/) sub-project.

## Interfaces

- **Storage interface** — a BRD is a YAML file in Git (e.g. `BRD-2026-001.yaml`) with the top-level keys `spec_type: brd` and a `brd:` object containing the schema below. The YAML is the single source of truth; the Code Graph node is derived from it.
- **Code Graph interface** — a BRD is materialised as a node of type `BRD` in the Code Graph. The graph stores the typed edges defined in §23.2.2 (`JUSTIFIES`, `TRACKS_BY`, `REQUIRES`, `READS_FROM`, `DEFINED_BY`, `COMPLIES_WITH`). Graph queries return the BRD's bidirectional neighbours.
- **Compute Spec interface** — because `spec_type: brd`, a BRD inherits Compute Spec capabilities (validation, CI/CD integration) — see §23.7 of the parent architecture.
- **External tracking interface** — the `external_tracking` block (Jira `epic_key` / Rally `feature_id`, `requirement_mappings`) is the contract consumed by the bidirectional Jira/Rally synchronisation (Pre-Sync Gate — see [Generation Pipeline](generation-pipeline.md) §23.5.7, and §23.8 External Tool Integration).

## Dependencies

- **Code Graph** (Neo4j) — stores the `BRD` node and its relationship edges; the graph is what makes "bidirectional links" queryable. Owned by [`knowledge-services`](../knowledge-services/).
- **Knowledge Base** — the `linked_kb_entries` references (e.g. `kb:glossary/revenue_accounts`) resolve against the KB Glossary, Catalog, and Mapping Registry.
- **Workflow Engine** — `linked_workflows` references (e.g. `wf:revenue_extract_v2`) resolve against Compute Specs owned by [`workflow-engine`](../workflow-engine/).
- **ADR store** — `linked_ADRs` references resolve against ADRs at the repo root (`adr/NNNN-slug.md`); from this document the relative path is `../../../adr/NNNN-slug.md`.
- **External trackers** — Jira and Rally APIs (consumed via MCP-20/MCP-21 — see §23.8) for the `external_tracking` block.
- **Git** — the YAML files are versioned in Git, giving the BRD full audit history.

## Data Model

### §23.2 BRD Entity Model

A BRD is a structured YAML entity within the system (Compute Spec subtype `spec_type: brd`), stored in Git repositories, establishing bidirectional relationship edges with all other entities through the Code Graph.

### §23.2.1 BRD YAML Schema

> **Note**: The lines beginning `# BRD-2026-001.yaml — Full BRD Schema` inside the block below are the YAML file's own title comment, not document headings.

```yaml
# BRD-2026-001.yaml — Full BRD Schema
spec_type: brd
brd:
  id: "BRD-2026-001"
  title: "Monthly Revenue Recognition Report — ASC606 Compliant"
  status: draft            # draft | in_review | approved | in_progress | implemented | deprecated | needs_update
  version: 3
  created_at: "2026-06-01T09:00:00Z"
  updated_at: "2026-07-03T14:30:00Z"
  created_by: "user:alice.chen"
  approvers: ["user:bob.wang", "user:cfo.sarah"]
  approved_at: null

  stakeholders:
    - role: "CFO"
      name: "Sarah Johnson"
      contact: "sarah.johnson@company.com"
      approval_status: pending
    - role: "Controller"
      name: "Mike Liu"
      contact: "mike.liu@company.com"
      approval_status: pending
    - role: "Revenue Operations Lead"
      name: "Alice Chen"
      contact: "alice.chen@company.com"
      approval_status: approved

  business_context:
    problem_statement: |
      Currently, the monthly revenue recognition report requires manual data export
      from ERP and currency conversion plus intercompany elimination in Excel,
      taking 3-5 business days and failing to meet SOX audit trail requirements.
    success_criteria:
      - "Monthly report generation time reduced from 5 days to 4 hours"
      - "100% audit trail coverage (from source data to every report cell)"
      - "ASC606 compliant: full coverage of the five-step revenue recognition model"
      - "Support 15 currencies with automatic conversion, exchange rate source traceable to ECB publication date"
    scope:
      in_scope:
        - "ERP General Ledger data source (Oracle EBS 12.2)"
        - "CRM contract data (Salesforce)"
        - "Monthly revenue recognition report (PDF + Excel)"
        - "Revenue analysis dashboard by region/product line/customer dimension"
      out_of_scope:
        - "Daily revenue forecasting (Phase 2)"
        - "Tax calculation (handled by separate system)"
    constraints:
      - "Must be completed by the 5th business day of each month"
      - "Data sources limited to production environment; development environment data not permitted"
      - "Exchange rate source must be ECB official rate as of publication date"

  requirements:
    - id: "REQ-001"
      type: functional
      description: "Automatically extract monthly revenue account balances from ERP General Ledger"
      acceptance_criteria:
        - "Given monthly close is complete, When revenue extraction is triggered, Then all revenue account balances are extracted within 30 minutes"
        - "Given extraction is complete, When compared against ERP trial balance, Then amount variance < $0.01"
      priority: P0
      linked_kb_entries:
        - "kb:glossary/revenue_accounts"        # Revenue account definitions
        - "kb:catalog/erp.gl_balances"          # ERP GL table structure
        - "kb:mapping/coa_revenue_mapping"      # Chart of accounts mapping rules
      linked_workflows: ["wf:revenue_extract_v2"]
      linked_ADRs: ["ADR-0012", "ADR-0034"]

    - id: "REQ-002"
      type: non_functional
      description: "Audit trail must cover the complete path from source document to report cell"
      acceptance_criteria:
        - "Given report generation is complete, When auditor clicks any cell, Then trace back to original ERP journal entry ID"
        - "Given any intermediate Transform step, When querying data lineage, Then display complete upstream/downstream DAG path"
      priority: P0
      linked_kb_entries:
        - "kb:glossary/audit_trail"
      linked_compliance: ["SOX-302", "SOX-404"]

    - id: "REQ-003"
      type: regulatory
      description: "Revenue recognition must satisfy ASC606 five-step model requirements"
      acceptance_criteria:
        - "Given revenue data with multi-year contracts, When recognition calculation executes, Then split by performance obligation and recognize over time/point in time"
        - "Given contracts with variable consideration (discounts/rebates), When calculating recognized amount, Then use most-likely-amount method"
      priority: P0
      linked_kb_entries:
        - "kb:glossary/asc606_five_step"
        - "kb:glossary/performance_obligation"
      linked_compliance: ["GAAP-ASC606"]

    - id: "REQ-004"
      type: data_quality
      description: "Revenue data quality checks: cross-system amount consistency, currency completeness, period correctness"
      acceptance_criteria:
        - "Given revenue extraction complete, When DQ check executes, Then ERP vs CRM contract amount variance < 1%"
        - "Given foreign currency transactions exist, When DQ check executes, Then all transactions have corresponding exchange rates (none missing)"
      priority: P1
      linked_kb_entries:
        - "kb:catalog/crm.contracts"
        - "kb:mapping/currency_mapping"

  data_flows:
    - name: "Revenue Data Pipeline"
      description: "Multi-source extraction → Merge → Currency conversion → Intercompany elimination → Report output"
      sources:
        - data_source: "ds:erp_prod.gl_balances"
          tables: ["gl_je_lines", "gl_balances"]
          filter: "account_type = 'REVENUE'"
        - data_source: "ds:crm_prod.contracts"
          tables: ["contract_header", "contract_lines"]
          filter: "status = 'ACTIVE'"
        - data_source: "ds:ecb_api.daily_rates"
          tables: []
          filter: "currency in (USD, EUR, CNY, JPY)"
      transforms:
        - step: 1
          name: "Currency Conversion"
          description: "Convert each currency's revenue to reporting currency (USD) at ECB daily midpoint rate"
          linked_spec: "xf:currency_conversion_v3"
        - step: 2
          name: "Intercompany Elimination"
          description: "Eliminate inter-entity transactions (based on IC flag field)"
          linked_spec: "xf:intercompany_elimination_v1"
        - step: 3
          name: "Revenue Allocation"
          description: "Split multi-year contract revenue by performance obligation"
          linked_spec: "xf:rev_allocation_asc606"
      outputs:
        - "Report: Monthly Revenue Recognition Report (PDF/Excel)"
        - "Dashboard: Revenue KPI Dashboard"
        - "Data Write-back: revenue_recognized_monthly → erp_reporting.revenue_monthly"

  traceability:
    linked_workflows: ["wf:monthly_revenue_v3", "wf:revenue_extract_v2"]
    linked_epics: ["JIRA:PROJ-123", "JIRA:PROJ-456"]
    linked_ADRs:
      - "ADR-0012: Select ECB as authoritative exchange rate source"
      - "ADR-0034: Use five-step method rather than percentage-of-completion for ASC606 performance obligation splitting"
      - "ADR-0018: Use DuckDB for Exploration Environment currency conversion, Spark for Runtime currency conversion"
    linked_compliance:
      - "SOX-302: Internal Control over Financial Reporting"
      - "SOX-404: Management Assessment of Internal Controls"
      - "GAAP-ASC606: Revenue from Contracts with Customers"
    linked_incidents: []   # No related incidents at this time

  # ─────────────────────────────────────────────────────────
  # Jira / Rally Multi-Level Structure Mapping
  # ─────────────────────────────────────────────────────────
  external_tracking:
    jira:
      epic_key: "PROJ-456"
      epic_summary: "Monthly Revenue Recognition Automation"
      epic_status: "In Progress"
      sync_status: synced  # synced | pending_push | pending_pull | conflict
      last_sync: "2026-07-04T08:00:00Z"
      
    rally:  # Optional, if using Rally instead of Jira
      feature_id: "F12345"
      feature_name: "Revenue Recognition Reports"
      feature_status: "In Progress"
      sync_status: synced
      last_sync: "2026-07-04T08:00:00Z"

    # Per-Requirement → Story → Sub-task/Task Mapping
    # Hierarchy: BRD → Epic/Feature → (per requirement) → Story/User Story → (per AC) → Sub-task/Task
    requirement_mappings:
      - req_id: "REQ-001"
        jira:
          story_key: "PROJ-457"
          story_summary: "Auto-identify contract performance obligations"
          story_status: "In Progress"
          sub_tasks:
            - key: "PROJ-460"
              summary: "Parse contract terms via NLP pipeline"
              status: "Done"
            - key: "PROJ-461"
              summary: "Flag performance obligation nodes in contract graph"
              status: "In Progress"
        rally:
          user_story_id: "US67890"
          user_story_status: "In Progress"
          tasks:
            - id: "TA111"
              description: "Parse contract terms via NLP pipeline"
              state: "Completed"
            - id: "TA112"
              description: "Flag performance obligation nodes in contract graph"
              state: "In Progress"
              
      - req_id: "REQ-002"
        jira:
          story_key: "PROJ-458"
          story_summary: "Ensure complete audit trail from source to report"
          story_status: "To Do"
          sub_tasks:
            - key: "PROJ-462"
              summary: "Design audit log schema for revenue pipeline"
              status: "To Do"
            - key: "PROJ-463"
              summary: "Implement immutable audit log writer"
              status: "To Do"
        rally:
          user_story_id: "US67891"
          user_story_status: "Defined"
          tasks:
            - id: "TA113"
              description: "Design audit log schema"
              state: "Defined"
            - id: "TA114"
              description: "Implement immutable audit log writer"
              state: "Defined"

      - req_id: "REQ-003"
        jira:
          story_key: "PROJ-459"
          story_summary: "ASC606 five-step revenue recognition"
          story_status: "In Progress"
          sub_tasks: []
        rally:
          user_story_id: "US67892"
          user_story_status: "In Progress"
          tasks: []

      - req_id: "REQ-004"
        jira:
          story_key: "PROJ-465"
          story_summary: "Revenue data quality checks"
          story_status: "To Do"
          sub_tasks: []
        rally:
          user_story_id: "US67893"
          user_story_status: "Defined"
          tasks: []
```

**Schema field summary**

| Top-level block | Purpose |
|-----------------|---------|
| `id`, `title`, `status`, `version`, `created_at`, `updated_at`, `created_by`, `approvers`, `approved_at` | Identity, version, and approval ownership. `status` drives the lifecycle state machine ([Lifecycle State Machine](lifecycle-state-machine.md)). |
| `stakeholders` | Roster of roles (CFO, Controller, RevOps Lead …) with per-stakeholder `approval_status`, consumed by approval-chain validation (Verifier Round 5). |
| `business_context` | `problem_statement`, `success_criteria`, `scope.in_scope` / `out_of_scope`, and `constraints`. This block is the anchor all other sections reference (see DraftWriter section dependency graph, §23.5.5). |
| `requirements[]` | Each requirement carries `id`, `type` (`functional` / `non_functional` / `regulatory` / `data_quality`), `description`, `acceptance_criteria` (Given/When/Then), `priority` (P0/P1), and links to `linked_kb_entries`, `linked_workflows`, `linked_ADRs`, `linked_compliance`. Acceptance criteria are the unit CI/CD validation runs against. |
| `data_flows[]` | Named pipeline definition: `sources` (data source + tables + filter), ordered `transforms` (each with a `linked_spec`), and `outputs`. |
| `traceability` | Aggregate links: `linked_workflows`, `linked_epics`, `linked_ADRs`, `linked_compliance`, `linked_incidents`. |
| `external_tracking` | Jira (`epic_key`, `epic_status`, `sync_status`) and/or Rally (`feature_id`) top-level, plus per-requirement `requirement_mappings` mapping each `req_id` to a Jira Story + Sub-tasks and/or Rally User Story + Tasks. `sync_status` ∈ `synced | pending_push | pending_pull | conflict`. |

### §23.2.2 BRD as Code Graph Node

The BRD is modelled as a node type `BRD` in the Code Graph, establishing relationship edges with the following node types:

```
                         ┌─────────────┐
                         │  Regulation │
                         │ (SOX/HIPAA/ │
                         │   GDPR)     │
                         └──────┬──────┘
                                │ COMPLIES_WITH
                                ▼
     ┌──────────┐    JUSTIFIES  ┌──────────┐  TRACKS_BY   ┌───────────┐
     │   ADR    │◄──────────────│   BRD   │──────────────►│ Jira Epic │
     └──────────┘               └────┬─────┘               └───────────┘
                                     │
                     ┌───────────────┼───────────────┐
                     │               │               │
                     ▼               ▼               ▼
              ┌──────────┐   ┌──────────────┐  ┌───────────┐
              │ Workflow │   │ Data Source  │  │  KB Entry │
              │ (REQUIRES)│   │ (READS_FROM) │  │ (DEFINED_ │
              │           │   │              │  │  BY)      │
              └──────────┘   └──────────────┘  └───────────┘
```

**Edge type catalog (BRD-centred)**

| Edge type | Direction | From → To | Meaning |
|-----------|-----------|-----------|---------|
| `JUSTIFIES` | BRD → ADR (reverse: ADR is justified by BRD) | `BRD` → `ADR` | The BRD's requirements are the reason an ADR was taken (the ADR is drawn `◄──` from BRD). |
| `TRACKS_BY` | BRD → Jira Epic | `BRD` → `Jira Epic` | The BRD is tracked by the Jira/Rally epic/feature (maps to `external_tracking.jira.epic_key`). |
| `COMPLIES_WITH` | BRD → Regulation | `BRD` → `Regulation` | The BRD must comply with the named regulation (SOX/HIPAA/GDPR); maps to `linked_compliance`. |
| `REQUIRES` | BRD → Workflow | `BRD` → `Workflow` | The BRD requires the named Workflow(s) for implementation; maps to `linked_workflows`. |
| `READS_FROM` | BRD → Data Source | `BRD` → `Data Source` | The BRD's `data_flows[].sources` read from these data sources. |
| `DEFINED_BY` | BRD → KB Entry | `BRD` → `KB Entry` | The BRD's terms/dimensions are defined by the linked KB glossary/catalog/mapping entries; maps to `linked_kb_entries`. |

These edges are **bidirectional** in the Code Graph: a traversal from any neighbour (e.g. a changed KB Entry, a superseded ADR, a modified Workflow) reaches the BRD, which is the mechanism that powers the auto-triggered `needs_update` Suspect Flag (see [Generation Pipeline](generation-pipeline.md) §23.5.8) and the impact-analysis queries in the parent architecture's §23.6.

## Failure Modes & Recovery

Because the BRD YAML in Git is the single source of truth and the Code Graph node is derived, the failure surface for this entity model is small. The notable failure modes relate to consistency between the YAML and the graph, and to external-tracking sync.

| Failure mode | Detection | Impact | Recovery |
|--------------|-----------|--------|----------|
| **Code Graph node stale vs. YAML** (YAML edited, graph not refreshed) | Code Graph consistency check (node fields vs. parsed YAML); also surfaced by CDC-driven refresh — see [`knowledge-services/cdc-pipeline.md`](../knowledge-services/cdc-pipeline.md) | Traceability/impact queries return outdated neighbours; `needs_update` Suspect Flags may mis-fire | Re-materialise the `BRD` node and its edges from the committed YAML; consistency report logged to Audit Trail |
| **Broken link reference** (e.g. `linked_ADRs: ["ADR-0099"]` but no such ADR exists) | Structural validation in the BRD Verifier (Round 1, structural completeness — §23.5.6) and CI/CD Compute Spec validation (§23.7) | Traceability holes; ADR/KB/Workflow edges cannot be created | Flag as P0/P1 issue (Verifier output); require author to correct the reference or add the missing entity before `in_review → approved` (guard condition, §23.4.4) |
| **Jira/Rally sync conflict** (`sync_status: conflict`) | External Tool Integration sync job (MCP-20/MCP-21, §23.8) | `external_tracking` diverges between BRD YAML and the tracker | Surface conflict in Workbench; **BRD is the sole Source of Truth** — Jira sync is unidirectional (BRD → Jira, per ADR-0022 decision 5), so the BRD YAML wins and the tracker is re-pushed |
| **Pre-Sync Gate blocks incomplete BRD** | BRD-Assembler Pre-Sync Gate (§23.5.7): unresolved fuzzy_nodes + unconfirmed Blocking assumptions + Verifier P0 issues | 🚫 Jira/Rally creation disabled (button disabled in Workbench) | Resolve blockers / confirm assumptions / fix P0 issues, then re-attempt sync. Markdown/PDF export is unaffected (fuzzy content annotated `[TBD: ...]`). |

## Non-Functional Requirements

- **Machine-readability** — the BRD is fully YAML-parseable; every field is structured (no free-text-only fields). Acceptance criteria are Given/When/Then so they can be executed as test cases.
- **Traceability coverage** — every requirement SHOULD link to ≥1 KB entry, and P0 requirements SHOULD link to ≥1 Workflow and ≥1 ADR. The Verifier (Round 2, KB cross-ref + compliance mapping — §23.5.6) checks this.
- **Versioning** — the YAML is Git-versioned; `version` is monotonically incremented on each accepted revision; full audit history is available via Git.
- **Tenant isolation** — all Code Graph edges and KB references are scoped by `tenant_id`; the BRD node and its neighbours are never leaked across tenants.
- **Bidirectional integrity** — the Code Graph guarantees that an edge materialised from a BRD's `linked_*` field is queryable in the reverse direction from the neighbour (this is what makes the `needs_update` auto-trigger work).

## Key Flows

### BRD creation and linking

1. A BRD YAML is authored (manually, or by the AI-assisted Generation Pipeline — see [Generation Pipeline](generation-pipeline.md) §23.5).
2. On commit, the Compute Spec validation (§23.7) runs: structural completeness, cross-reference validity (every `linked_*` resolves), and conflict validation.
3. The validated YAML is materialised as a `BRD` node in the Code Graph with the edges from §23.2.2 (`JUSTIFIES`, `TRACKS_BY`, `COMPLIES_WITH`, `REQUIRES`, `READS_FROM`, `DEFINED_BY`).
4. External tracking sync: if `external_tracking` is present and the Pre-Sync Gate passes, the epic/feature and per-requirement stories/tasks are pushed to Jira/Rally (unidirectional, BRD → tracker).

### Stale-BRD auto-detection ( Suspect Flag )

This flow is owned by the Generation Pipeline's Multi-BRD Conflict Detection (§23.5.8) but is enabled by this entity model's bidirectional edges:

1. An entity the BRD references changes (a KB entry is edited, an ADR is superseded, a Workflow is modified, a Data Source schema changes).
2. The Code Graph traverses the dependency graph from the changed entity and finds all BRDs referencing it (precise to the Requirement level, since the graph supports Requirement-level edges from BRD → KB Entry).
3. The affected BRD is auto-flagged `needs_update` (Suspect Flag) and the BRD Owner is notified for human adjudication.

See [Lifecycle State Machine](lifecycle-state-machine.md) for the full `needs_update` transition and [Generation Pipeline](generation-pipeline.md) §23.5.8 for the event-driven mechanism.

## Design References

- **§23.2 BRD Entity Model** — the source section in [`docs/03-architecture.md`](../../03-architecture.md).
- **§23.6 Traceability Web** — the complete relationship matrix across BRD ↔ all entities, in [`docs/03-architecture.md`](../../03-architecture.md).
- **§23.7 BRD/ADR as Compute Spec Types** — capability inheritance and the CI/CD validation pipeline, in [`docs/03-architecture.md`](../../03-architecture.md).
- **§23.8 External Tool Integration** — Jira/Confluence/Compliance via MCP-20/21/22, in [`docs/03-architecture.md`](../../03-architecture.md).
- [ADR-0010](../../../adr/0010-brd-adr-first-class.md) — BRD/ADR as First-Class Entities.
- [Lifecycle State Machine](lifecycle-state-machine.md) — the BRD's 16-state lifecycle driven by the `status` field.
- [Generation Pipeline](generation-pipeline.md) — the 8-agent pipeline that produces this YAML.
- [ADR Entity Model](adr-entity-model.md) — the entity this BRD `JUSTIFIES`.
- [`docs/glossary.md`](../../glossary.md) — definitions of BRD, Compute Spec, Code Graph, and related terms.
- Sub-project README — [`docs/sub-projects/brd-adr-lifecycle/README.md`](README.md).
