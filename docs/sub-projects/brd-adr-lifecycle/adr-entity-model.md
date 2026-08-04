# ADR Entity Model

> **Origin**: §23.3 of [`docs/03-architecture.md`](../../03-architecture.md) | **Sub-project**: [brd-adr-lifecycle](README.md)

## Purpose

The Architecture Decision Record (ADR) follows the MADR (Markdown Architectural Decision Records) pattern, but is stored as a **structured YAML entity** within the system (a Compute Spec subtype declared by `spec_type: adr`), making ADRs fully machine-readable, queryable, and linkable. This module defines the canonical shape of an ADR: the YAML schema that captures context, decision drivers, considered options, the decision outcome, consequences, and full traceability; and the explicit mapping from each MADR section to its YAML field.

Treating the ADR as structured data (rather than a free-form Markdown narrative) is what enables: (1) automatic detection of "architecturally significant changes" in code that should trigger an ADR (see [Generation Pipeline](generation-pipeline.md) §23.5.9); (2) compliance verification of accepted decisions through CI/CD fitness functions (the MADR *Confirmation* section — see §23.8 of the parent architecture); (3) bidirectional traceability between an ADR and the BRDs, components, incidents, and KB entries it relates to; and (4) the immutable decision chain formed by the `supersedes` / `superseded_by` fields.

This module covers §23.3 in full: the §23.3.1 ADR YAML Schema and the §23.3.2 ADR-to-MADR Mapping.

## Boundaries

**In scope**

- The complete ADR YAML schema (§23.3.1): identity/status, decision participants (decision makers / consulted / informed), `context`, `decision_drivers`, the `options[]` array (each with pros/cons), the `decision` outcome, the `consequences` block (positive / negative / risks with mitigations and residuals), and the `traceability` block.
- The explicit ADR-to-MADR field mapping (§23.3.2), including how the MADR *Confirmation* section is implemented via the CI/CD Fitness Function / Compliance Mapper.

**Out of scope**

- The ADR **lifecycle** state machine (proposed → in_discussion → accepted …, 12 states, immutability after `accepted`) — see [Lifecycle State Machine](lifecycle-state-machine.md).
- The **AI-assisted generation flow** for ADRs (the 5-step architectural-significance → context → draft → review → acceptance flow) — see [Generation Pipeline](generation-pipeline.md) §23.5.9.
- The **BRD entity model** — see [BRD Entity Model](brd-entity-model.md).
- The full **traceability web** relationship matrix — covered by the parent architecture's §23.6.
- The **Compliance Mapper / CI/CD Fitness Function** internals — covered by the parent architecture's §23.8.

## Interfaces

- **Storage interface** — an ADR is a YAML file at the repo root (`adr/NNNN-slug.md`, e.g. `adr/0042-debezium-kafka-cdc.md`); ADRs live peer to `docs/`. From this document, the relative path to an ADR is `../../../adr/NNNN-slug.md`. The YAML has the top-level keys `spec_type: adr` and an `adr:` object containing the schema below.
- **Code Graph interface** — an ADR is materialised as a node of type `ADR` in the Code Graph, with the bidirectional `JUSTIFIES` edge to BRD(s) and traceability edges to components, incidents, and KB entries (see [`brd-entity-model.md`](brd-entity-model.md) §23.2.2 for the BRD-centred edge diagram).
- **Compute Spec interface** — because `spec_type: adr`, an ADR inherits Compute Spec capabilities (validation, CI/CD integration) — see §23.7 of the parent architecture. The MADR *Confirmation* is realised as a CI/CD Fitness Function verified by the Compliance Mapper (§23.8).
- **Immutability interface** — once `status: accepted`, the ADR's decision **content** is immutable; only status markers may change (`accepted → monitoring → partially_superseded → superseded / deprecated`). See [Lifecycle State Machine](lifecycle-state-machine.md) §23.4.2.

## Dependencies

- **Code Graph** (Neo4j) — stores the `ADR` node and its relationship edges (components, BRDs, incidents, KB entries, superseded/superseding ADRs). Owned by [`knowledge-services`](../knowledge-services/).
- **Change Intelligence** — detects architecturally significant code changes that should trigger ADR auto-drafting (see [Generation Pipeline](generation-pipeline.md) §23.5.9 Step 1). Owned by [`knowledge-services`](../knowledge-services/).
- **Compliance Mapper / Fitness Functions** — verifies accepted decisions against compliance constraints (the MADR *Confirmation* section). See §23.8 of the parent architecture.
- **BRD store** — `linked_BRDs` references resolve against BRDs (see [BRD Entity Model](brd-entity-model.md)).
- **Knowledge Base** — `linked_kb_entries` references (e.g. `kb:catalog/vector_db`) resolve against the KB Catalog.
- **Git** — the YAML files are versioned in Git; the immutable-after-`accepted` invariant is enforced socially and via review, not by file permissions.

## Data Model

### §23.3 ADR Entity Model

The ADR follows the MADR (Markdown Architectural Decision Records) pattern, but is stored as a structured YAML entity within the system (Compute Spec subtype `spec_type: adr`), making ADRs fully machine-readable, queryable, and linkable.

### §23.3.1 ADR YAML Schema

> **Note**: The line beginning `# ADR-0042.yaml — Full ADR Schema` inside the block below is the YAML file's own title comment, not a document heading.

```yaml
# ADR-0042.yaml — Full ADR Schema
spec_type: adr
adr:
  id: "ADR-0042"
  title: "Use Debezium + Kafka Connect for CDC instead of PostgreSQL Logical Replication directly"
  status: accepted          # proposed | in_discussion | accepted | deprecated | superseded
  superseded_by: null       # If superseded → "ADR-0051"
  supersedes: ["ADR-0028"]  # If superseding a previous decision
  created_at: "2026-06-15T10:00:00Z"
  accepted_at: "2026-06-20T14:00:00Z"
  author: "user:bob.zhang"
  decision_makers: ["user:bob.zhang", "user:arch.team", "user:cto.lin"]
  consulted: ["user:db.team", "user:kafka.ops"]
  informed: ["user:dev.team", "user:qa.team"]

  context: |
    ## Background and Problem Statement

    Currently, the system uses PostgreSQL Logical Replication to push KB metadata
    changes directly to Vector DB and Graph DB. As downstream consumers increase
    (Vector DB writes, Graph DB edge updates, Search Index rebuilds, Audit Log
    triggers), two critical issues have emerged:

    1. **Replication Slot Exhaustion Risk**: A single PG publication supports a
       limited number of replication slots. Each additional downstream consumer
       consumes one slot. Currently 6/10 slots are in use, and planned Notification
       Service and Cost Tracker require 2 more slots.

    2. **Missing Backpressure**: When Vector DB delays due to batch writes, PG WAL
       logs accumulate with no buffering mechanism, causing primary database disk
       alerts.

    The architecture review confirmed this is an Architecturally Significant
    Requirement (ASR) — it directly impacts system scalability and reliability.

  decision_drivers:
    - "Scale to 15+ downstream consumers without increasing PG load"
    - "Backpressure handling: slow consumers do not block upstream"
    - "RPO (Recovery Point Objective) < 4 hours"
    - "Ops team already has Kafka operational experience (existing event bus)"
    - "Total incremental infrastructure cost < $500/month"

  options:
    - id: "opt-1"
      name: "Debezium + Kafka Connect + Schema Registry"
      description: "Debezium captures PG WAL → Kafka Topic → Kafka Connect Sink → downstream systems"
      pros:
        - "Kafka provides natural buffering (Topic Retention 7 days), consumers can freely replay/backfill"
        - "Debezium supports PG 10+ native logical replication, handles schema evolution automatically"
        - "Schema Registry ensures Avro Schema forward/backward compatibility"
        - "Single source, multiple consumers: PG needs only 1 replication slot for Debezium"
        - "Kafka ecosystem monitoring: Lag, Throughput, Consumer Health already observable"
      cons:
        - "New infrastructure: Kafka 3-broker + Connect 2-node cluster"
        - "Increased operational complexity (but team already has Kafka experience)"
        - "End-to-end latency increases ~500ms (PG→Kafka→Consumer) — acceptable for KB sync use case"

    - id: "opt-2"
      name: "PostgreSQL Logical Replication Direct Subscription (Status Quo + Optimization)"
      description: "Maintain PG logical replication direct connections, mitigate issues via replication slot management and batch write optimization"
      pros:
        - "Simple architecture: no middleware, PG→Consumer direct"
        - "No new infrastructure needed"
        - "Lower latency (< 50ms)"
      cons:
        - "Replication slot count hard-limited by PG version (max_replication_slots=10)"
        - "No buffering: WAL accumulation when consumers are slow, may cause primary database unavailability"
        - "Each new consumer requires PG config changes + restart or reload"
        - "Schema changes require manual coordination across all consumers"
        - "Does not meet 15+ consumer target"

    - id: "opt-3"
      name: "PgBouncer + Custom CDC Service (In-House CDC Forwarding Layer)"
      description: "Build a Go service connecting PG logical replication → forward to N consumers"
      pros:
        - "Fully controllable"
        - "No Kafka dependency"
      cons:
        - "Development cycle 6-8 weeks vs Kafka solution 2 weeks integration"
        - "Requires building buffering, retry, schema management in-house — reinventing the wheel"
        - "High long-term maintenance cost (Debezium has ongoing community updates)"

  decision: |
    ## Final Decision

    Selected **Option 1: Debezium + Kafka Connect**, for the following reasons:

    1. **Decisive Factor**: Single PG replication slot supports unlimited downstream
       consumers. This is the fundamental bottleneck of opt-2; opt-3 solves it but
       at excessive development cost.

    2. **Buffering Capability**: Kafka Topic Retention provides a 7-day replay window,
       solving the backpressure problem. Consumers can consume at their own pace
       without blocking upstream PG.

    3. **Operational Fit**: The team already has Kafka cluster operational experience
       (existing event bus 3-broker cluster), with a gentle learning curve. Kafka
       monitoring is already integrated into Prometheus/Grafana.

    4. **Incremental Cost Acceptable**: New 3-broker Kafka + 2-node Connect cluster,
       monthly cost $350, within the $500 budget.

    5. **Future Extensibility**: Kafka Topics natively support multiple consumer groups
       (Vector DB Sync, Graph DB Sync, Audit Logger, Search Index Rebuild, Cost
       Tracker — all can independently consume the same topic), without modifying
       upstream PG configuration.

  consequences:
    positive:
      - "Single PG replication slot supports unlimited downstream consumers (via Kafka Consumer Groups)"
      - "7-day Topic Retention provides failure recovery window, RPO can improve from 4 hours to < 1 hour"
      - "Schema Registry automates schema evolution management"
      - "Kafka Connect ecosystem: pre-built Elasticsearch, JDBC, S3 Sink Connectors"
    negative:
      - "New Kafka cluster monthly infrastructure cost $350"
      - "End-to-end latency increases 500ms — no practical impact on KB sync (target 30s latency)"
      - "Ops team must monitor Kafka + Connect cluster health"
    risks:
      - risk: "Kafka Broker failure causes CDC pipeline interruption"
        mitigation: "3-broker cluster + min.insync.replicas=2, single broker failure has no impact"
        residual: "LOW"
      - risk: "Schema Registry unavailability causes Avro serialization failures"
        mitigation: "Schema Registry dual-node + local schema caching"
        residual: "LOW"
      - risk: "Kafka Connect task failure"
        mitigation: "Connect REST API monitoring + auto-restart policy"
        residual: "MEDIUM"

  traceability:
    linked_components:
      - "code_graph:cdc_pipeline"            # CDC Pipeline component
      - "code_graph:kb_vector_db_sync"       # Vector DB Sync Job
      - "code_graph:kb_graph_db_sync"        # Graph DB Sync Job
      - "code_graph:audit_log_forwarder"     # Audit Log Forwarder
    linked_BRDs: ["BRD-2026-005"]            # KB Expansion Requirements BRD
    linked_incidents: ["INC-0042"]           # PG replication slot exhaustion incident that triggered this decision
    linked_ADRs:
      - "ADR-0028"   # superseded: Original "Use PG Logical Replication" decision
      - "ADR-0030"   # related: Vector DB selection decision
    linked_kb_entries:
      - "kb:catalog/vector_db"               # Vector DB data catalog
      - "kb:catalog/graph_db"                # Graph DB data catalog
```

**Schema field summary**

| Top-level block | Purpose |
|-----------------|---------|
| `id`, `title`, `status`, `superseded_by`, `supersedes`, `created_at`, `accepted_at`, `author` | Identity, lifecycle status, and the supersession chain. `status` is one of `proposed`, `in_discussion`, `accepted`, `deprecated`, or `superseded`. `supersedes` / `superseded_by` form the immutable decision chain (see [Lifecycle State Machine](lifecycle-state-machine.md) §23.4.2). |
| `decision_makers`, `consulted`, `informed` | The decision's RACI-style participant roster (MADR *Decision Makers*, plus consulted and informed parties). |
| `context` | Markdown-format full background and problem statement. Establishes whether the decision addresses an Architecturally Significant Requirement (ASR). |
| `decision_drivers` | Structured list of drivers (e.g. scale targets, RPO, cost ceilings, existing operational experience). |
| `options[]` | The considered alternatives. Each option has `id`, `name`, `description`, `pros[]`, `cons[]`. The selected option is named in `decision`. |
| `decision` | Markdown-format final decision outcome, naming the selected option and the rationale. |
| `consequences` | Structured: `positive[]`, `negative[]`, and `risks[]` (each risk carries `risk`, `mitigation`, and `residual` severity `LOW | MEDIUM | HIGH`). |
| `traceability` | Structured links: `linked_components`, `linked_BRDs`, `linked_incidents`, `linked_ADRs` (superseded + related), `linked_kb_entries`. These become Code Graph edges. |

### §23.3.2 ADR-to-MADR Mapping

The ADR YAML is a structured-materialisation of the MADR format. Every MADR section maps to a YAML field:

| MADR Section                  | ADR YAML Field                     | Description                                                       |
| ----------------------------- | ---------------------------------- | ----------------------------------------------------------------- |
| Status (YAML front matter)    | `status`                           | proposed / in_discussion / accepted / deprecated / superseded     |
| Date                          | `created_at`, `accepted_at`        | ISO 8601 timestamps                                               |
| Decision Makers               | `decision_makers`                  | Decision participant list                                         |
| Context and Problem Statement | `context`                          | Markdown format full background description                       |
| Decision Drivers              | `decision_drivers`                 | Structured driver list                                            |
| Considered Options            | `options[]`                        | Structured options array with pros/cons                           |
| Decision Outcome              | `decision`                         | Markdown format decision statement                                |
| Consequences                  | `consequences`                     | Structured consequences: positive/negative/risks                  |
| Confirmation                  | Integrated into CI/CD Fitness Function | Verified via Compliance Mapper (see §23.8)                    |
| Pros and Cons                 | `options[].pros`, `options[].cons` | Embedded in options array                                    |
| More Information              | `traceability`                     | Structured traceability links                                |

**Key mapping notes**

- **Confirmation is not a static field** — MADR's *Confirmation* section (the human-readable checklist that the decision is actually being followed) is implemented as a **CI/CD Fitness Function** verified by the **Compliance Mapper** (§23.8 of the parent architecture). This is the structural difference between a narrative MADR and this system's machine-readable ADR: confirmation is executable, not declarative.
- **Pros and Cons are embedded** in each `options[]` entry (`options[].pros`, `options[].cons`), rather than as a separate top-level MADR section, so that each option is self-contained.
- **Supersession is first-class** — `supersedes` and `superseded_by` are top-level identity fields, not buried in prose. This is what lets the Code Graph maintain an immutable decision chain (old ADR → `superseded`, new ADR → `accepted`, edge between them).

## Failure Modes & Recovery

| Failure mode | Detection | Impact | Recovery |
|--------------|-----------|--------|----------|
| **Editing an accepted ADR's decision content** | Review process; the immutability invariant is enforced at `status: accepted` (see [Lifecycle State Machine](lifecycle-state-machine.md) §23.4.2) | Violates the immutable decision chain; compliance/audit trail compromised | Reject the edit. If the decision truly must change, create a **new** ADR that `supersedes` this one; the old ADR transitions `accepted → superseded` and its content remains as historical reference. |
| **Broken supersession link** (`supersedes: ["ADR-0028"]` but ADR-0028 missing, or `superseded_by` not set on the old ADR) | Structural validation (Compute Spec validation, §23.7); Code Graph consistency check | Decision chain broken; impact analysis cannot traverse old → new | Flag as P0 issue; require the supersession relationship to be consistent on both sides before the new ADR can reach `accepted`. |
| **Stale ADR vs. code reality** (accepted decision no longer matches what the code does, but no new ADR was raised) | Compliance Mapper / Fitness Function failure in CI/CD (the MADR *Confirmation*); Change Intelligence detecting an architecturally significant change without a corresponding ADR (see [Generation Pipeline](generation-pipeline.md) §23.5.9) | Compliance violations; decisions drift from implementation | Auto-draft a new ADR (§23.5.9 Step 1 → Step 3) for the divergent change; the original stays `accepted`/`monitoring` until a superseding ADR is accepted. |
| **Dangling traceability link** (e.g. `linked_components: ["code_graph:cdc_pipeline"]` but the component was removed) | Verifier / Code Graph consistency check | Traceability holes; impact queries incomplete | Flag for human adjudication; either correct the reference or open a revision. |

## Non-Functional Requirements

- **Machine-readability** — the ADR is fully YAML-parseable; every MADR section maps to a structured field (§23.3.2). Context and decision remain Markdown (rich text) but are carried as string fields.
- **Immutability after acceptance** — the `decision`, `options`, `context`, and `decision_drivers` content of an `accepted` ADR must not change; only status markers evolve. This is the core ADR principle preserved by this model.
- **Decision-chain integrity** — `supersedes` / `superseded_by` must be consistent on both ends; the Code Graph maintains the chain as immutable edges.
- **Executable confirmation** — the MADR *Confirmation* is realised as a CI/CD Fitness Function (Compliance Mapper, §23.8), so "is this decision still being followed?" is answered by automated checks, not by re-reading prose.
- **Traceability coverage** — an accepted ADR SHOULD link to the components it governs, the BRD(s) that justified it, and (where relevant) the incident(s) that triggered it; the Compliance Mapper verifies this.
- **Tenant isolation** — all Code Graph edges are scoped by `tenant_id`.

## Key Flows

### ADR creation and acceptance

1. An ADR is created via the AI-assisted ADR Generation Flow (see [Generation Pipeline](generation-pipeline.md) §23.5.9), or manually. It starts at `status: proposed`.
2. It enters `in_discussion` for team review; intermediate states (`challenged`, `pending_validation`, `needs_revision`) may be exercised — see [Lifecycle State Machine](lifecycle-state-machine.md) §23.4.2.
3. On architecture-review approval (guard condition: quorum met, fitness functions pass — §23.4.4), the ADR transitions to `accepted`. **From this point the decision content is immutable.**
4. If it supersedes an earlier ADR, that earlier ADR transitions to `superseded` and the supersession edge is recorded on both.
5. The Code Graph adds the `ADR` node and its traceability edges (components, BRDs, incidents, KB entries). Affected component Owners are notified (FR37).

### ADR-to-code compliance (ongoing)

1. CI/CD runs the Fitness Function(s) corresponding to this ADR (the MADR *Confirmation*).
2. If a future code change violates the decision, the Fitness Function fails; Change Intelligence may auto-draft a new ADR (§23.5.9) if the change is architecturally significant.
3. The original ADR remains `accepted` (or moves to `monitoring`); only when a superseding ADR is accepted does it become `superseded`.

## Design References

- **§23.3 ADR Entity Model** — the source section in [`docs/03-architecture.md`](../../03-architecture.md).
- **§23.6 Traceability Web** — the complete relationship matrix across ADR ↔ all entities, in [`docs/03-architecture.md`](../../03-architecture.md).
- **§23.7 BRD/ADR as Compute Spec Types** — capability inheritance and the CI/CD validation pipeline, in [`docs/03-architecture.md`](../../03-architecture.md).
- **§23.8 External Tool Integration** — the Compliance Mapper that implements the MADR *Confirmation* as a Fitness Function, in [`docs/03-architecture.md`](../../03-architecture.md).
- [ADR-0010](../../../adr/0010-brd-adr-first-class.md) — BRD/ADR as First-Class Entities (the MADR-compliance direction).
- `ADR-0042` (`adr/0042-debezium-kafka-cdc.md` in the example) — the example ADR used throughout §23.3.1 (Debezium + Kafka Connect for CDC). This is an illustrative filename, not an actual file.
- [Lifecycle State Machine](lifecycle-state-machine.md) — the ADR's 12-state lifecycle and the immutability invariant at `accepted`.
- [Generation Pipeline](generation-pipeline.md) — §23.5.9 covers the ADR Generation Flow (architectural significance detection → context → draft → review → acceptance).
- [BRD Entity Model](brd-entity-model.md) — the entity an ADR is `JUSTIFIED` by.
- [`docs/glossary.md`](../../glossary.md) — definitions of ADR, MADR, ASR, Compute Spec, and related terms.
- Sub-project README — [`docs/sub-projects/brd-adr-lifecycle/README.md`](README.md).
