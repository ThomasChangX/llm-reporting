# brd-adr-lifecycle — BRD & ADR as First-Class Entities

> **Origin**: §23 of `docs/03-architecture.md` (1488 lines)
> **Key ADRs**: [ADR-0010](../../adr/0010-brd-adr-first-class.md) (BRD/ADR First-Class), [ADR-0022](../../adr/0022-brd-generation-agent-pipeline.md) (Generation Pipeline Redesign)

## Positioning

The **BRD & ADR Lifecycle** sub-project treats Business Requirements Documents and Architecture Decision Records as first-class entities — structured, versioned, bidirectionally linked to Workflows, and generatable through an AI-assisted 8-agent pipeline. This is the system's meta-layer: it manages "requirements about requirements."

§23 is the largest single chapter in the architecture (1488 lines), reflecting the depth of the BRD generation pipeline (6-stage agent workflow), the lifecycle state machines (16-state BRD, 12-state ADR), and the traceability web (relationship model with typed edges).

## Boundaries

**In-scope:**
- BRD Entity Model (YAML schema, as Code Graph node)
- ADR Entity Model (YAML schema, MADR mapping)
- BRD/ADR Lifecycle State Machines (extended state machines)
- AI-Assisted Generation Pipeline (8 sub-agents: IntentDeepener, ContextGatherer, VaguenessResolver, DraftWriter, Verifier, Assembler, Multi-BRD Conflict Detection, ADR Generation)
- Traceability Web (relationship model, edge type catalog, NL query examples)
- BRD/ADR as Compute Spec Types (capability inheritance, CI/CD validation pipeline)
- External Tool Integration (Jira/Confluence/Compliance via MCP-20/21/22)
- Experience Typology Tree (three-layer progressive construction)
- BRD Product Quality Assessment (four-dimension human reviewer scoring)

**Delegated to other sub-projects:**
- Agent execution of generation pipeline → [`agent-platform`](../agent-platform/)
- Compute Spec validation → [`workflow-engine`](../workflow-engine/)
- Code Graph node/edge storage → [`knowledge-services`](../knowledge-services/)

## Module List

| Module | Origin | Document |
|--------|--------|----------|
| BRD Entity Model | §23.2 | [`brd-entity-model.md`](brd-entity-model.md) |
| ADR Entity Model | §23.3 | [`adr-entity-model.md`](adr-entity-model.md) |
| Lifecycle State Machine | §23.4 | [`lifecycle-state-machine.md`](lifecycle-state-machine.md) |
| AI-Assisted Generation Pipeline (8 sub-agents) | §23.5 | [`generation-pipeline.md`](generation-pipeline.md) |
| Traceability Web | §23.6 | [`traceability-web.md`](traceability-web.md) |
| BRD/ADR as Compute Spec Types | §23.7 | [`compute-spec-integration.md`](compute-spec-integration.md) |
| External Tool Integration (Jira/Confluence/Compliance) | §23.8 | [`external-integration.md`](external-integration.md) |
| Experience Typology Tree + Product Quality Assessment | §23.11, §23.12 | [`quality-and-typology.md`](quality-and-typology.md) |

## External Interface Contract

| Interface | Consumer | Contract |
|-----------|----------|----------|
| `brd.generate(intent, context) → brd_draft` | Exploration Environment | 8-agent pipeline → structured BRD YAML |
| `adr.generate(decision_context) → adr_draft` | Exploration Environment | ADR generation flow → MADR-compliant ADR |
| `brd.validate(brd_yaml) → validation_report` | CI/CD Pipeline (§23.7.2) | Structural + cross-reference + conflict validation |
| `traceability.query(entity_id) → relationship_graph` | Agent Platform, Change Intelligence | Bidirectional links across BRD↔ADR↔Workflow↔Code |

## Related ADRs

- [ADR-0010](../../adr/0010-brd-adr-first-class.md) — BRD/ADR as First-Class Entities
- [ADR-0022](../../adr/0022-brd-generation-agent-pipeline.md) — BRD Generation Agent Pipeline Redesign
