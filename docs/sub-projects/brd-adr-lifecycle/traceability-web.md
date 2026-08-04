# Traceability Web

> **Origin**: §23.6 of [`docs/03-architecture.md`](../../03-architecture.md) | **Sub-project**: [brd-adr-lifecycle](README.md)

## Purpose

The Traceability Web establishes bidirectional relationship edges between BRDs/ADRs and every other system entity (Workflows, Code Graph components, Jira Epics/Stories, Incidents, KB entries, Regulations, Compute Specs, PRs, Deployments) through the Code Graph. Its purpose is to make "requirements → implementation" a native, real-time, queryable relationship rather than a static Excel traceability matrix.

This module defines the **complete relationship model** (§23.6.1), the **Code Graph relation edge catalog** (§23.6.2), and the **natural language query patterns** (§23.6.3) that the system supports.

## Boundaries

**In-scope:**
- The full entity relationship topology anchored on BRD/ADR nodes (§23.6.1).
- The typed edge catalog consumed by the Code Graph (§23.6.2): `REQUIRES`, `JUSTIFIES`, `TRACKS_BY`, `COMPLIES_WITH`, `DEFINED_BY`, `READS_FROM`, `IMPLEMENTED_BY`, `TRIGGERED_BY`, `SUPERSEDES`, `CONSTRAINS`, `RELATED_TO`, `REALIZES`, `CONSTRAINED_BY`, `IMPACTS`, `MAY_SUPERSEDE`.
- Natural-language-to-Cypher query patterns over the traceability graph (§23.6.3).

**Out of scope (delegated):**
- Physical storage of graph nodes/edges → [`knowledge-services`](../knowledge-services/) (Code Graph).
- Broken/stale link detection and visualization → [TraceabilityAnalyzer (S17)](external-integration.md) and the [`generation-pipeline.md`](generation-pipeline.md).
- BRD/ADR YAML schemas themselves → [`brd-entity-model.md`](brd-entity-model.md), [`adr-entity-model.md`](adr-entity-model.md).

## Interfaces

| Interface | Consumer | Contract |
|-----------|----------|----------|
| `traceability.query(entity_id) → relationship_graph` | Agent Platform, Change Intelligence (FR28) | Bidirectional links across BRD↔ADR↔Workflow↔Code, returned as nodes + edges |
| NL query → Cypher (via S01 → S03 CodeGraphQuery) | Workbench users, non-technical stakeholders | Natural-language question translated to graph traversal |
| `IMPACTS` / `MAY_SUPERSEDE` edge events | Change Intelligence (FR28) | A `Change` node emitting `IMPACTS` on a BRD triggers `needs_update`; `MAY_SUPERSEDE` on an ADR flags obsolescence |

## Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| **Code Graph** (Neo4j) | Hard | Single source of truth for all traceability edges (per ADR-012, see [Design References](#design-references)). Requires BRD/ADR node types and 12+ typed edge types. |
| **S01** AI Knowledge Agent | Hard | Front-door for natural-language traceability queries. |
| **S03** CodeGraphQuery | Hard | Executes Cypher traversals produced from NL queries. |
| **S17** TraceabilityAnalyzer | Soft | Consumes the edge catalog to detect broken/stale links and produce coverage reports. |
| BRD/ADR Compute Spec persistence (Git) | Hard | Edges reference BRD/ADR IDs that must exist as versioned Compute Specs. |

## Data Model

### §23.6.1 Complete Relationship Model

BRD and ADR establish bidirectional relationship edges with all system entities through the Code Graph. Below is the complete relationship matrix:

```
                         ┌──────────────────┐
                         │    REGULATION    │
                         │ SOX / HIPAA /    │
                         │ GDPR / ASC606    │
                         └────────┬─────────┘
                                  │ COMPLIES_WITH
                    ┌─────────────┼─────────────┐
                    │             │             │
                    ▼             ▼             ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │   BRD    │ │   ADR    │ │ WORKFLOW │
              └────┬─────┘ └────┬─────┘ └────┬─────┘
                   │            │            │
    ┌──────────────┼──┐    ┌────┼────────┐   │
    │              │  │    │    │        │   │
    ▼              ▼  │    ▼    ▼        ▼   │
┌────────┐  ┌────────┐│ ┌────────┐ ┌────────┐│
│  JIRA  │  │KB ENTRY││ │ CODE   │ │INCIDENT││
│  EPIC  │  └────────┘│ │ GRAPH  │ └────────┘│
└───┬────┘            │ │COMPONENT│           │
    │                 │ └────────┘           │
    ▼                 │                      │
┌────────┐            │                      │
│  JIRA  │            │                      │
│ STORY  │            │                      │
└───┬────┘            │                      │
    │                 │                      │
    ▼                 │                      │
┌────────┐◄───────────┘                      │
│COMPUTE │                                   │
│ SPEC   │                                   │
└───┬────┘                                   │
    │                                        │
    ▼                                        │
┌────────┐                                   │
│   PR   │                                   │
└───┬────┘                                   │
    │                                        │
    ▼                                        │
┌────────┐                                   │
│DEPLOY  │                                   │
└────────┘                                   │
```

The diagram captures the full topology: a `REGULATION` (SOX/HIPAA/GDPR/ASC606) sits at the top and `COMPLIES_WITH` flows down into BRD, ADR, and Workflow. BRD connects out to Jira Epic → Jira Story → Compute Spec, KB Entry, Data Source (via `READS_FROM`), and `JUSTIFIES` the ADR. ADR connects to Code Graph Component (`IMPLEMENTED_BY`), Incident (`TRIGGERED_BY`), and back to Compute Spec. Workflow ties into the same Compute Spec → PR → Deploy chain.

### §23.6.2 Code Graph Relation Edge Catalog

| Source Node Type | Edge Type        | Target Node Type     | Meaning                                                          | Example Query                                                            |
| ---------------- | ---------------- | -------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------ |
| BRD              | `REQUIRES`       | Workflow             | BRD requirements are implemented via Workflow                    | "Which Workflows implement BRD-2026-001?"                                |
| BRD              | `JUSTIFIES`      | ADR                  | BRD business requirements justify the architecture decision      | "Which BRD does this ADR satisfy?"                                        |
| BRD              | `TRACKS_BY`      | Jira Epic            | BRD is tracked by Jira Epic                                      | "Which Jira Epic corresponds to BRD-2026-001?"                            |
| BRD              | `COMPLIES_WITH`  | Regulation           | Compliance requirements the BRD must satisfy                     | "Which SOX provisions does this BRD satisfy?"                             |
| BRD              | `DEFINED_BY`     | KB Entry             | Definition/calculation logic used in the BRD                     | "Which KB entry defines the revenue calculation logic?"                   |
| BRD              | `READS_FROM`     | Data Source          | Data sources the BRD depends on                                  | "Which BRDs would be affected by changing this data source?"              |
| ADR              | `IMPLEMENTED_BY` | Code Graph Component | Which components implement the ADR decision                      | "Which components are affected by the Kafka CDC decision?"                |
| ADR              | `TRIGGERED_BY`   | Incident             | The incident that triggered this decision                        | "Which incidents led to this architecture decision?"                      |
| ADR              | `SUPERSEDES`     | ADR                  | This ADR supersedes a prior decision                             | "What is the historical evolution chain of this decision?"                |
| ADR              | `CONSTRAINS`     | Workflow             | Architecture decision imposes constraints on Workflow            | "Which Workflows are constrained by the CDC decision?"                    |
| ADR              | `RELATED_TO`     | KB Entry             | ADR references this knowledge entry                              |                                                                          |
| Workflow         | `REALIZES`       | BRD                  | Workflow realizes BRD requirements                               |                                                                          |
| Workflow         | `CONSTRAINED_BY` | ADR                  | Workflow is constrained by ADR decision                          |                                                                          |
| Change           | `IMPACTS`        | BRD                  | Change impacts BRD → triggers needs_update                       |                                                                          |
| Change           | `MAY_SUPERSEDE`  | ADR                  | Change may render ADR obsolete                                   |                                                                          |

Notes on the catalog:
- BRD-centric edges (`REQUIRES`, `JUSTIFIES`, `TRACKS_BY`, `COMPLIES_WITH`, `DEFINED_BY`, `READS_FROM`) model the demand side: what the business requires and what it must comply with.
- ADR-centric edges (`IMPLEMENTED_BY`, `TRIGGERED_BY`, `SUPERSEDES`, `CONSTRAINS`, `RELATED_TO`) model the decision side: how decisions are realized, what prompted them, and how they constrain downstream work.
- `Change`-originated edges (`IMPACTS`, `MAY_SUPERSEDE`) are the integration point with **Change Intelligence (FR28)** — a detected change emits these edges, which the lifecycle state machines consume to flip BRDs into `needs_update` and flag ADRs for review.

## Failure Modes & Recovery

| Failure Mode | Detection | Recovery |
|--------------|-----------|----------|
| **Broken traceability link** — e.g., a BRD `REQUIRES` a Workflow that no longer exists, or an ADR `IMPLEMENTED_BY` a deleted component. | S17 TraceabilityAnalyzer periodic scan returns entries in `broken_links[]` (expected relation present but target missing). | Surface in Workbench for human remediation; re-link or archive the orphaned spec. |
| **Stale link** — relationship still nominally exists but the target entity has not been updated within a threshold (e.g., ADR `accepted_at` older than 12 months). | S17 returns entries in `stale_links[]` (last_updated threshold exceeded). | Trigger ADR review (flip to `in_review`) or BRD `needs_update`. |
| **Incomplete coverage** — BRD requirements without any linked Workflow/ADR, or accepted ADRs without `IMPLEMENTED_BY` components. | CI/CD Traceability Lint stage (see [compute-spec-integration.md](compute-spec-integration.md) §CI/CD stage 3) fails the build; S17 reports via `coverage_report`. | Block merge until traceability edges are added. |
| **Code Graph unavailable** during a query. | S03 CodeGraphQuery returns connection error. | Degrade NL query with a retry; edges are durable in Neo4j (WAL-G backups) so no data loss. |
| **Orphaned edge on import/migration** — legacy BRD imported (S14) references entities not yet in the graph. | MigrationAdvisor emits `migration_notes`; reference integrity CI stage (stage 2) flags unresolved links. | Manual review item; link once the target entity is created. |

## Non-Functional Requirements

| NFR | Target | Rationale |
|-----|--------|-----------|
| Query latency (single-hop) | Sub-second | NL traceability queries via S01→S03 must feel interactive in the Workbench. |
| Multi-level traversal depth | Up to 6 hops supported | The "complete traceability chain" query (BRD → Deploy) spans up to 6 edges; deeper traversals may require index optimization per ADR-012 consequences. |
| Edge write consistency | Strong (within a Compute Spec freeze/commit) | Traceability edges are written atomically with the spec commit so the graph never references a half-applied change. |
| Tenant isolation | All edges scoped by `tenant_id` | Inherited from Code Graph tenancy; no cross-tenant traceability. |
| Auditability | Every edge creation/supersession audited (FR10.1) | `SUPERSEDES` chains and `Change.IMPACTS` events must be reconstructable for compliance. |

## Key Flows

### §23.6.3 Natural Language Query Examples

Natural language queries supported via AI Knowledge Agent (S01 → S03 CodeGraphQuery):

| Question                                                                                                | Cypher Query Logic                                                                                                                |
| ------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| "Which BRDs would be affected by switching the exchange rate source from ECB to Fed?"                   | `MATCH (brd:BRD)-[:READS_FROM]->(ds:DataSource {name:'ECB'}) RETURN brd`                                                         |
| "Which ADRs influenced the Reconciliation Engine design?" | `MATCH (adr:ADR)-[:IMPLEMENTED_BY]->(comp:Component)-[:BELONGS_TO*1..3]->(w:Workflow {name:'Reconciliation Engine'}) RETURN adr` |
| "Which compliance requirements does this Workflow satisfy?" | `MATCH (w:Workflow)<-[:REQUIRES]-(brd:BRD)-[:COMPLIES_WITH]->(r:Regulation) RETURN r` |
| "Show the complete traceability chain from BRD-2026-001 to final deployment" | `MATCH path = (brd:BRD {id:'BRD-2026-001'})-[*1..6]-(deploy:Deployment) RETURN path` |
| "Which ADRs may be outdated due to no review in 12+ months?" | `MATCH (adr:ADR {status:'accepted'}) WHERE adr.accepted_at < date() - duration('P12M') RETURN adr` |

### Key Traceability Flows

1. **Forward traceability (BRD → Deploy):** BRD `REQUIRES` Workflow → Workflow realizes a Compute Spec → Compute Spec yields a PR → PR deploys. The 6-hop variable-length query above captures the entire chain; this is the canonical "requirements coverage" view.
2. **Reverse impact analysis (Change → BRD/ADR):** A `Change` (code diff, data-source change, or incident) emits `IMPACTS` on affected BRDs and `MAY_SUPERSEDE` on potentially obsolete ADRs. Change Intelligence (FR28) consumes these edges to drive the lifecycle state machines (`needs_update` for BRDs, review for ADRs).
3. **Compliance traceability:** BRD `COMPLIES_WITH` Regulation, and BRD `REQUIRES` Workflow — composing the two yields the controls satisfied by a given Workflow. This is the join the third NL query performs and is the basis for the [compliance-mapper (MCP-22)](external-integration.md) coverage reports.
4. **ADR evolution chain:** `SUPERSEDES` edges form a linked list across ADR history, answering "what is the historical evolution chain of this decision?" ADRs are immutable once accepted, so evolution is captured purely through supersession.

## Design References

- **§23.6** of [`docs/03-architecture.md`](../../03-architecture.md) — source section for this module.
- **ADR-0012** "Code Graph as Single Source of Traceability Truth" ([`../../../adr/0012-document-structure-v2.md`](../../../adr/0012-document-structure-v2.md) family / §23.10 in source) — establishes that all traceability relationships live as Code Graph edges, queryable via Cypher and NL, replacing static Excel matrices. Consequence: Code Graph needs BRD/ADR node types and 12+ relationship edge types; multi-level traversal may require index optimization.
- **ADR-0010** "BRD and ADR as Compute Spec Subtypes" ([`../../../adr/0010-brd-adr-first-class.md`](../../../adr/0010-brd-adr-first-class.md)) — BRDs/ADRs are first-class graph nodes, enabling these edges.
- [`README.md`](README.md) — sub-project overview and module list.
- [`compute-spec-integration.md`](compute-spec-integration.md) — CI/CD Traceability Lint stage that enforces edge completeness.
- [`external-integration.md`](external-integration.md) — Jira `TRACKS_BY` linkage (MCP-20) and compliance mapping (MCP-22) that populate these edges.
- [`lifecycle-state-machine.md`](lifecycle-state-machine.md) — consumes `Change.IMPACTS` / `MAY_SUPERSEDE` events to drive state transitions.
