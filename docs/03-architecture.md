# 03 - Architecture

> The New Model for Reporting + ETL Workflow + Adjustment in the LLM Era — Architecture Design Master Document
>
> This document integrates three major design domains: Architecture Overview, Core Engine, and Knowledge Base.
> For detailed requirements see `docs/02-requirement.md`, for background and decision records see `docs/01-facts.md`.

---

## 1. Core Design Philosophy

| Principle | Description |
| --------------------------------------- | ------------------------------------------------------------------ |
| **Explore with AI, Execute without AI Side Effects** | Design Plane uses LLM to assist exploration; Runtime Plane executes deterministically with zero AI side effects. Intelligence Plane provides read-only AI analysis (ad-hoc Q&A, attribution analysis), but answers do not cross the bridge — they are not written into Runtime state |
| **Freeze is an Explicit Operation** | After user validation, one-click solidification: AI artifacts → deterministic scripts; reversible and requires approval |
| **Knowledge-Driven > Data-Driven** | AI reasons on the user-provided Knowledge Base and does not guess data semantics from thin air |
| **Compliance is Foundation, not Feature** | SDLC / permissions / audit are built in from day one |
| **User Modifications Matter More than AI Generation** | AI output is a suggestion; users can manually correct at any time |

---

## 2. Panoramic Architecture

> **Note**: Per ADR-0025, the architecture is reframed as **one Workflow Engine running in three environments + one cross-environment read-only mode**, not four independent planes. The same Compute Spec executes in any environment; environment configuration determines which capabilities are enabled.

```
                            ┌──────────────────────────────────────────┐
                            │            Auth Gateway                   │
                            │   OAuth 2.0 │ Kerberos │ SAML/SSO │ LDAP │
                            └────────────┬─────────────────────────────┘
                                         │
                    ┌────────────────────┴────────────────────┐
                    │              API Gateway                  │
                    │    Rate Limit │ Auth │ Route │ Tenant    │
                    └────────────────────┬────────────────────┘
                                         │
         ┌───────────────────────────────┼───────────────────────────────┐
         │                     WORKFLOW ENGINE                            │
         │                                                                │
         │  ┌───────────────────────┐         ┌───────────────────────┐  │
         │  │ EXPLORATION ENVIRONMENT│  freeze() │ PRODUCTION ENVIRONMENT │  │
         │  │ (LLM APIs Reachable)  │─────────▶│ (LLM API Egress        │  │
         │  │ Mutability: High       │  pipeline │  Blocked by NetPolicy) │  │
         │  │                       │◀─────────│ Mutability: Zero        │  │
         │  ├───────────────────────┤ rollback ├───────────────────────┤  │
         │  │ • Conversation UI     │         │ • Workflow Executor     │  │
         │  │ • Visual Designer     │         │ • Data Connectors       │  │
         │  │ • Workbench           │         │ • Output Renderer       │  │
         │  │ • AI Copilot Engine   │         │ • Scheduler             │  │
         │  │ • Light Engine        │         │ • Incident Manager      │  │
         │  │   (DuckDB/Polars)     │         │ • Query Rewriter        │  │
         │  │                       │         │ • Heavy Engine (Spark)  │  │
         │  └───────────┬───────────┘         └───────────┬───────────┘  │
         │              │                                 │              │
         │              │  ┌───────────────────────────┐  │              │
         │              │  │   FREEZE PIPELINE          │  │              │
         │              │  │   (built-in engine op)     │  │              │
         │              │  ├───────────────────────────┤  │              │
         │              │  │ • Spec Refinement Asst    │  │              │
         │              │  │ • Validation Engine       │  │              │
         │              │  │ • Test Runner (Sandbox)   │  │              │
         │              │  │ • Release Manager         │  │              │
         │              │  │ • CI/CD Pipeline          │  │              │
         │              │  │ • Pre-Change Doc Gen      │  │              │
         │              │  └───────────────────────────┘  │              │
         │              │                                 │              │
         │  ┌───────────┴─────────────────────────────────┴───────────┐  │
         │  │        CROSS-ENVIRONMENT READ-ONLY MODE                  │  │
         │  │  (Same Engine, Write Operations Intercepted at Engine Level) │
         │  ├──────────────────────────────────────────────────────────┤  │
         │  │ • AI Knowledge Agent (NL→Answers, Attribution Analysis) │  │
         │  │ • Pre/Post-Change Impact Report                         │  │
         │  │ • Observability & Log Analysis                          │  │
         │  │ • Queries Read-Replicas of Both Environments             │  │
         │  └──────────────────────────┬──────────────────────────────┘  │
         │                             │                                 │
         └─────────────────────────────┼─────────────────────────────────┘
                                       │
               ┌───────────────────────┴───────────────────────┐
               │      KNOWLEDGE BASE (Cross-Environment)        │
               ├───────────────────────────────────────────────┤
               │  Business Glossary │ Data Catalog             │
               │  Mapping Registry  │ Workflow Templates       │
               │  Adjustment History│ Behavior Patterns        │
               │  Report/Metric Catalog │ Diagnostic Playbooks│
               │  Code Knowledge                               │
               │  ──────────────────────────────────────────── │
               │  PostgreSQL + pgvector (Vector/Graph/Relational)   │
               │  + S3/MinIO (Object Store)                     │
               └──────────────┬────────────────────────────────┘
                              │
               ┌──────────────┴──────────────┐
               │        CODE GRAPH            │
               │   (System Knowledge Graph)   │
               │   Nodes: Workflow/Job/DS/... │
               │   Edges: DEPENDS_ON/READS... │
               └──────────────────────────────┘

          ┌─────────────────────────────────────────────────────────┐
          │               CROSS-CUTTING LAYER                        │
          │  Audit Trail │ Version Control │ Entitlement │ Tenant   │
          │  Data Masking│ File Export     │ Notification│ Config   │
          │  Observability│ Log System     │ Support/Ticket│        │
          └─────────────────────────────────────────────────────────┘
```

### 2.1 Code Graph API

The Code Graph serves as the system's structural knowledge graph — a unified, queryable model of all artifacts (Workflows, Jobs, DataSources, Formats, KB entries) and their relationships. It is the backbone for impact analysis, lineage tracing, and AI context retrieval.

| Aspect             | Specification                                                                                                                                                                                                              |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Query Protocol** | GraphQL read interface; Cypher/Gremlin for deep graph traversals. All queries are parameterized and logged.                                                                                                                |
| **Write Triggers** | Event-sourced: Freeze Bridge `merge` → node/edge upsert; Runtime `execute` → status edges; KB `confirm` → cross-graph bridge edges. No direct user writes — all mutations flow through domain events.                      |
| **RBAC Filtering** | Queries are transparently filtered by caller's entitlement context: row-level (tenant), column-level (PII fields), and edge-level (cross-tenant relationships denied). The graph never returns data the caller cannot see. |
| **Cache Strategy** | Hot subgraph (active Workflows, recent KB) in Redis; full graph in Graph DB; read replicas for analytical queries.                                                                                                         |
| **Consistency**    | Eventually consistent with the Relational DB (source of truth). Max staleness: 5 seconds for status edges, 30 seconds for structural edges.                                                                                |

> **Note**: Detailed Code Graph design (query protocol, write triggers, RBAC filtering, cache strategy, failure modes) is in [`docs/sub-projects/knowledge-services/code-graph.md`](sub-projects/knowledge-services/code-graph.md).

---

## 3. Unified Workflow Engine — Environments & Design

> **Migrated** to [`docs/sub-projects/workflow-engine/`](sub-projects/workflow-engine/) (§3.1–§3.5). This stub preserves the `§3` anchor required by ADRs and `docs/01-facts.md`.

### 3.1 Exploration Environment in Detail

> **Migrated** to [`docs/sub-projects/agent-platform/exploration-runtime.md`](sub-projects/agent-platform/exploration-runtime.md) (§3.1). This stub preserves the `§3.1` anchor required by ADRs and `docs/01-facts.md`.

### 3.2 Conversation Interface — Prompt Injection Defense

> **Migrated** to [`docs/sub-projects/agent-platform/exploration-runtime.md`](sub-projects/agent-platform/exploration-runtime.md) (§3.2). This stub preserves the `§3.2` anchor required by ADRs and `docs/01-facts.md`.

### 3.3 Design Artifact Schema (Handoff Contract)

> **Migrated** to [`docs/sub-projects/workflow-engine/design-artifact.md`](sub-projects/workflow-engine/design-artifact.md) (§3.3). This stub preserves the `§3.3` anchor required by ADRs and `docs/01-facts.md`.

### 3.4 Workbench — VCS Integration

> **Migrated** to [`docs/sub-projects/agent-platform/exploration-runtime.md`](sub-projects/agent-platform/exploration-runtime.md) (§3.4). This stub preserves the `§3.4` anchor required by ADRs and `docs/01-facts.md`.

### 3.5 Exploration Environment — Detailed Component Architecture

> **Migrated** to [`docs/sub-projects/agent-platform/exploration-runtime.md`](sub-projects/agent-platform/exploration-runtime.md) (§3.5). This stub preserves the `§3.5` anchor required by ADRs and `docs/01-facts.md`.

## 4. Freeze Pipeline

> **Migrated** to [`docs/sub-projects/workflow-engine/freeze-pipeline.md`](sub-projects/workflow-engine/freeze-pipeline.md) (§4). This stub preserves the `§4` anchor required by ADRs and `docs/01-facts.md`.

### 4.1 Spec Refinement Assistant

> **Migrated** to [`docs/sub-projects/workflow-engine/freeze-pipeline.md`](sub-projects/workflow-engine/freeze-pipeline.md) (§4.1). This stub preserves the `§4.1` anchor required by ADRs and `docs/01-facts.md`.

### 4.1b `llm_reasoning` Job Resolution During Freeze

> **Migrated** to [`docs/sub-projects/workflow-engine/freeze-pipeline.md`](sub-projects/workflow-engine/freeze-pipeline.md) (§4). This stub preserves the `§4` anchor required by ADRs and `docs/01-facts.md`.

### 4.2 Canary Gating & Auto-Rollback

> **Migrated** to [`docs/sub-projects/workflow-engine/freeze-pipeline.md`](sub-projects/workflow-engine/freeze-pipeline.md) (§4.2). This stub preserves the `§4.2` anchor required by ADRs and `docs/01-facts.md`.

### 4.3 Fuzzy Node Detection & Resolution Algorithm

> **Migrated** to [`docs/sub-projects/workflow-engine/freeze-pipeline.md`](sub-projects/workflow-engine/freeze-pipeline.md) (§4.3). This stub preserves the `§4.3` anchor required by ADRs and `docs/01-facts.md`.

#### 4.3.1 Fuzzy Node Types (Fuzzy Node Classification)

> **Migrated** to [`docs/sub-projects/workflow-engine/freeze-pipeline.md`](sub-projects/workflow-engine/freeze-pipeline.md) (§4.3.1). This stub preserves the `§4.3.1` anchor required by ADRs and `docs/01-facts.md`.

#### 4.3.2 Detection Algorithm (Pseudocode)

> **Migrated** to [`docs/sub-projects/workflow-engine/freeze-pipeline.md`](sub-projects/workflow-engine/freeze-pipeline.md) (§4.3.2). This stub preserves the `§4.3.2` anchor required by ADRs and `docs/01-facts.md`.

#### 4.3.3 Resolution Strategy Catalog

> **Migrated** to [`docs/sub-projects/workflow-engine/freeze-pipeline.md`](sub-projects/workflow-engine/freeze-pipeline.md) (§4.3.3). This stub preserves the `§4.3.3` anchor required by ADRs and `docs/01-facts.md`.

## 5. Production Environment

> **Migrated** to [`docs/sub-projects/query-serving/`](sub-projects/query-serving/) (§5.1–§5.4). This stub preserves the `§5` anchor required by ADRs and `docs/01-facts.md`.

### 5.1 Resilience Patterns

> **Migrated** to [`docs/sub-projects/query-serving/query-service.md`](sub-projects/query-serving/query-service.md) (§5.1). This stub preserves the `§5.1` anchor required by ADRs and `docs/01-facts.md`.

### 5.2 Data Classification Tiers

> **Migrated** to [`docs/sub-projects/query-serving/query-service.md`](sub-projects/query-serving/query-service.md) (§5.2). This stub preserves the `§5.2` anchor required by ADRs and `docs/01-facts.md`.

### 5.3 Query Service

> **Migrated** to [`docs/sub-projects/query-serving/query-service.md`](sub-projects/query-serving/query-service.md) (§5.3). This stub preserves the `§5.3` anchor required by ADRs and `docs/01-facts.md`.

#### 5.3.1 Metadata Manager

> **Migrated** to [`docs/sub-projects/query-serving/query-service.md`](sub-projects/query-serving/query-service.md) (§5.3.1). This stub preserves the `§5.3.1` anchor required by ADRs and `docs/01-facts.md`.

#### 5.3.2 Query Generator

> **Migrated** to [`docs/sub-projects/query-serving/query-service.md`](sub-projects/query-serving/query-service.md) (§5.3.2). This stub preserves the `§5.3.2` anchor required by ADRs and `docs/01-facts.md`.

#### 5.3.3 Pushdown Optimizer

> **Migrated** to [`docs/sub-projects/query-serving/query-service.md`](sub-projects/query-serving/query-service.md) (§5.3.3). This stub preserves the `§5.3.3` anchor required by ADRs and `docs/01-facts.md`.

#### 5.3.4 Collaboration with Existing Components

> **Migrated** to [`docs/sub-projects/query-serving/query-service.md`](sub-projects/query-serving/query-service.md) (§5.3.4). This stub preserves the `§5.3.4` anchor required by ADRs and `docs/01-facts.md`.

#### 5.3.5 Query Cache

> **Migrated** to [`docs/sub-projects/query-serving/query-service.md`](sub-projects/query-serving/query-service.md) (§5.3.5). This stub preserves the `§5.3.5` anchor required by ADRs and `docs/01-facts.md`.

### 5.4 Large-Scale Data Architecture

> **Migrated** to [`docs/sub-projects/query-serving/large-scale-data.md`](sub-projects/query-serving/large-scale-data.md) (§5.4). This stub preserves the `§5.4` anchor required by ADRs and `docs/01-facts.md`.

#### 5.4.1 Industry Best Practice Comparison

> **Migrated** to [`docs/sub-projects/query-serving/large-scale-data.md`](sub-projects/query-serving/large-scale-data.md) (§5.4.1). This stub preserves the `§5.4.1` anchor required by ADRs and `docs/01-facts.md`.

#### 5.4.2 Partitioning & Pruning

> **Migrated** to [`docs/sub-projects/query-serving/large-scale-data.md`](sub-projects/query-serving/large-scale-data.md) (§5.4.2). This stub preserves the `§5.4.2` anchor required by ADRs and `docs/01-facts.md`.

#### 5.4.3 Incremental Processing

> **Migrated** to [`docs/sub-projects/query-serving/large-scale-data.md`](sub-projects/query-serving/large-scale-data.md) (§5.4.3). This stub preserves the `§5.4.3` anchor required by ADRs and `docs/01-facts.md`.

#### 5.4.4 Pre-Aggregation & Materialization

> **Migrated** to [`docs/sub-projects/query-serving/large-scale-data.md`](sub-projects/query-serving/large-scale-data.md) (§5.4.4). This stub preserves the `§5.4.4` anchor required by ADRs and `docs/01-facts.md`.

#### 5.4.5 Cost-Based Optimization

> **Migrated** to [`docs/sub-projects/query-serving/large-scale-data.md`](sub-projects/query-serving/large-scale-data.md) (§5.4.5). This stub preserves the `§5.4.5` anchor required by ADRs and `docs/01-facts.md`.

#### 5.4.6 Federated Heterogeneous Data Source Strategy

> **Migrated** to [`docs/sub-projects/query-serving/large-scale-data.md`](sub-projects/query-serving/large-scale-data.md) (§5.4.6). This stub preserves the `§5.4.6` anchor required by ADRs and `docs/01-facts.md`.

## 6. Compute Spec (Unified Compute Definition)

> **Migrated** to [`docs/sub-projects/workflow-engine/compute-spec.md`](sub-projects/workflow-engine/compute-spec.md) (§6). This stub preserves the `§6` anchor required by ADRs and `docs/01-facts.md`.

### 6.1 Dependency Trigger Rules

> **Migrated** to [`docs/sub-projects/workflow-engine/compute-spec.md`](sub-projects/workflow-engine/compute-spec.md) (§6.1). This stub preserves the `§6.1` anchor required by ADRs and `docs/01-facts.md`.

### 6.2 Common Compute Subset (Portability Guarantee)

> **Migrated** to [`docs/sub-projects/workflow-engine/compute-spec.md`](sub-projects/workflow-engine/compute-spec.md) (§6.2). This stub preserves the `§6.2` anchor required by ADRs and `docs/01-facts.md`.

## 7. Execution Sandbox

> **Migrated** to [`docs/sub-projects/workflow-engine/execution-sandbox.md`](sub-projects/workflow-engine/execution-sandbox.md) (§7). This stub preserves the `§7` anchor required by ADRs and `docs/01-facts.md`.

### 7.1 State-Passing Mechanism

> **Migrated** to [`docs/sub-projects/workflow-engine/execution-sandbox.md`](sub-projects/workflow-engine/execution-sandbox.md) (§7.1). This stub preserves the `§7.1` anchor required by ADRs and `docs/01-facts.md`.

### 7.2 Python Execution Constraints

> **Migrated** to [`docs/sub-projects/workflow-engine/execution-sandbox.md`](sub-projects/workflow-engine/execution-sandbox.md) (§7.2). This stub preserves the `§7.2` anchor required by ADRs and `docs/01-facts.md`.

### 7.3 SQL Injection Defense

> **Migrated** to [`docs/sub-projects/workflow-engine/execution-sandbox.md`](sub-projects/workflow-engine/execution-sandbox.md) (§7.3). This stub preserves the `§7.3` anchor required by ADRs and `docs/01-facts.md`.

## 8. Log System

> **Migrated** to [`docs/sub-projects/platform-core/observability.md`](sub-projects/platform-core/observability.md) (§8). This stub preserves the `§8` anchor required by ADRs and `docs/01-facts.md`.

### 8.1 OpenTelemetry Alignment (Observability Standard Alignment)

> **Migrated** to [`docs/sub-projects/platform-core/observability.md`](sub-projects/platform-core/observability.md) (§8.1). This stub preserves the `§8.1` anchor required by ADRs and `docs/01-facts.md`.

## 9. Change Intelligence & Agent Triage

> **Migrated** to [`docs/sub-projects/knowledge-services/change-intelligence.md`](sub-projects/knowledge-services/change-intelligence.md) (§9). This stub preserves the `§9` anchor required by ADRs and `docs/01-facts.md`.

### 9.0 Agent Triage Layer (Alert Triage & Proactive Push)

> **Migrated** to [`docs/sub-projects/knowledge-services/change-intelligence.md`](sub-projects/knowledge-services/change-intelligence.md) (§9.0). This stub preserves the `§9.0` anchor required by ADRs and `docs/01-facts.md`.

### 9.1 Pre-Change Impact Report (Before Change)

> **Migrated** to [`docs/sub-projects/knowledge-services/change-intelligence.md`](sub-projects/knowledge-services/change-intelligence.md) (§9.1). This stub preserves the `§9.1` anchor required by ADRs and `docs/01-facts.md`.

### 9.2 Post-Change Verification (After Change)

> **Migrated** to [`docs/sub-projects/knowledge-services/change-intelligence.md`](sub-projects/knowledge-services/change-intelligence.md) (§9.2). This stub preserves the `§9.2` anchor required by ADRs and `docs/01-facts.md`.

### 9.3 AI Knowledge Agent (The Omniscient) — Cross-Environment Read-Only Mode

> **Migrated** to [`docs/sub-projects/knowledge-services/change-intelligence.md`](sub-projects/knowledge-services/change-intelligence.md) (§9.3). This stub preserves the `§9.3` anchor required by ADRs and `docs/01-facts.md`.

## 10. Knowledge Base

> **Migrated** to [`docs/sub-projects/knowledge-services/knowledge-base.md`](sub-projects/knowledge-services/knowledge-base.md) (§10). This stub preserves the `§10` anchor required by ADRs and `docs/01-facts.md`.

### 10.1 Consistency Model

> **Migrated** to [`docs/sub-projects/knowledge-services/knowledge-base.md`](sub-projects/knowledge-services/knowledge-base.md) (§10.1). This stub preserves the `§10.1` anchor required by ADRs and `docs/01-facts.md`.

### 10.2 Content Processing Pipeline → adr/0023

> **Migrated** to [`docs/sub-projects/knowledge-services/knowledge-base.md`](sub-projects/knowledge-services/knowledge-base.md) (§10.2). This stub preserves the `§10.2` anchor required by ADRs and `docs/01-facts.md`.

### 10.3 Linkage Weaving Layer → adr/0023

> **Migrated** to [`docs/sub-projects/knowledge-services/knowledge-base.md`](sub-projects/knowledge-services/knowledge-base.md) (§10.3). This stub preserves the `§10.3` anchor required by ADRs and `docs/01-facts.md`.

### 10.4 Quality Flywheel → adr/0023

> **Migrated** to [`docs/sub-projects/knowledge-services/knowledge-base.md`](sub-projects/knowledge-services/knowledge-base.md) (§10.4). This stub preserves the `§10.4` anchor required by ADRs and `docs/01-facts.md`.

## 11. Cross-Cutting Layer

> **Migrated** to [`docs/sub-projects/platform-core/cross-cutting-layer.md`](sub-projects/platform-core/cross-cutting-layer.md) (§11). This stub preserves the `§11` anchor required by ADRs and `docs/01-facts.md`.

### 11.1 Security & Encryption

> **Migrated** to [`docs/sub-projects/platform-core/cross-cutting-layer.md`](sub-projects/platform-core/cross-cutting-layer.md) (§11.1). This stub preserves the `§11.1` anchor required by ADRs and `docs/01-facts.md`.

### 11.2 Entitlement (RBAC + ABAC)

> **Migrated** to [`docs/sub-projects/platform-core/cross-cutting-layer.md`](sub-projects/platform-core/cross-cutting-layer.md) (§11.2). This stub preserves the `§11.2` anchor required by ADRs and `docs/01-facts.md`.

### 11.3 Version Control

> **Migrated** to [`docs/sub-projects/platform-core/cross-cutting-layer.md`](sub-projects/platform-core/cross-cutting-layer.md) (§11.3). This stub preserves the `§11.3` anchor required by ADRs and `docs/01-facts.md`.

### 11.4 Observability

> **Migrated** to [`docs/sub-projects/platform-core/cross-cutting-layer.md`](sub-projects/platform-core/cross-cutting-layer.md) (§11.4). This stub preserves the `§11.4` anchor required by ADRs and `docs/01-facts.md`.

### 11.5 Additional Cross-Cutting Components

> **Migrated** to [`docs/sub-projects/platform-core/cross-cutting-layer.md`](sub-projects/platform-core/cross-cutting-layer.md) (§11.5). This stub preserves the `§11.5` anchor required by ADRs and `docs/01-facts.md`.

## 12. Domain-Specific Architecture Components

> **Migrated** to [`docs/sub-projects/platform-core/domain-services.md`](sub-projects/platform-core/domain-services.md) (§12). This stub preserves the `§12` anchor required by ADRs and `docs/01-facts.md`.

### 12.1 Email Ingestion Pipeline → FR17

> **Migrated** to [`docs/sub-projects/platform-core/domain-services.md`](sub-projects/platform-core/domain-services.md) (§12.1). This stub preserves the `§12.1` anchor required by ADRs and `docs/01-facts.md`.

### 12.2 Data Health Check Framework → FR18, FR19

> **Migrated** to [`docs/sub-projects/data-health/health-check-framework.md`](sub-projects/data-health/health-check-framework.md) (§12.2). This stub preserves the `§12.2` anchor required by ADRs and `docs/01-facts.md`.

### 12.3 Backup & Disaster Recovery Architecture → FR41

> **Migrated** to [`docs/sub-projects/platform-core/domain-services.md`](sub-projects/platform-core/domain-services.md) (§12.3). This stub preserves the `§12.3` anchor required by ADRs and `docs/01-facts.md`.

### 12.4 Notification Service Architecture → FR37

> **Migrated** to [`docs/sub-projects/platform-core/domain-services.md`](sub-projects/platform-core/domain-services.md) (§12.4). This stub preserves the `§12.4` anchor required by ADRs and `docs/01-facts.md`.

### 12.5 Runtime Dependency Manager → FR40

> **Migrated** to [`docs/sub-projects/platform-core/domain-services.md`](sub-projects/platform-core/domain-services.md) (§12.5). This stub preserves the `§12.5` anchor required by ADRs and `docs/01-facts.md`.

### 12.6 Observation Engine → FR3

> **Migrated** to [`docs/sub-projects/platform-core/observability.md`](sub-projects/platform-core/observability.md) (§12.6). This stub preserves the `§12.6` anchor required by ADRs and `docs/01-facts.md`.

## 12.7 Data Flow Panorama

> **Migrated** to [`docs/sub-projects/platform-core/domain-services.md`](sub-projects/platform-core/domain-services.md) (§12.7). This stub preserves the `§12.7` anchor required by ADRs and `docs/01-facts.md`.

## 13. Technology Selection Summary

| Layer         | Selection                                        |
| ------------- | ------------------------------------------------ |
| Logic Script  | Python (Polars/pandas) + **SQL (ANSI SQL:2003)** |
| Spec Format   | YAML                                             |
| Design Compute| DuckDB + Polars (Light Engine)                   |
| Runtime Compute| Spark (Heavy Engine, Post-MVP) [Trino/Ray deferred] |
| Vector DB     | Milvus / pgvector                                |
| Graph DB      | Neo4j                                            |
| Metadata DB   | PostgreSQL                                       |
| Object Store  | S3 / MinIO                                       |
| Log Hot Store | Elasticsearch                                    |
| Version Control| Git                                              |
| AI Agent Arch | LLM SDK + Skill + MCP                            |
| AI Model      | Pluggable (OpenAI/Anthropic/Open-source/Private)  |

### 13.1 Operational Complexity Assessment

This architecture is designed for enterprise-scale reporting and ETL orchestration. Below is an honest assessment of operational complexity and the recommended adoption path.

| Dimension           | Complexity | Rationale                                                                                                                                                                                 |
| ------------------- | ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Infrastructure**  | **High**   | 10+ distinct services (PostgreSQL, Vector DB, Graph DB, Elasticsearch, S3, Redis, Vault, Spark/Trino/Ray cluster, Sandbox runtime, KMS). Requires Kubernetes or equivalent orchestration. |
| **Security**        | **High**   | mTLS, KMS key hierarchy, Row-Level Security via Query Rewriter, multi-layer prompt injection defense, Sandbox seccomp profiles. All mandatory from Day 1.                                 |
| **Data Governance** | **High**   | KB consistency model (Relational source-of-truth + eventually-consistent projections), CDC pipelines, versioned everything, cross-store sync monitoring.                                  |
| **AI Safety**       | **Medium** | Prompt injection defense, confidence scoring, mandatory human sign-off, LLM interaction audit logging. Manageable with the guard pipeline defined in Section 3.2.                         |
| **Multi-Tenancy**   | **Medium** | Three-tier isolation model gives flexibility; L1 (process) is straightforward, L3 (cluster) is complex but only required for regulated industries.                                        |

### 13.2 Minimum Viable Stack (MVP)

For teams that want to start small and grow into the full architecture, the following is the recommended **Minimum Viable Stack**:

| Component                | Full Stack                   | MVP Alternative                               | When to Upgrade                                 |
| ------------------------ | ---------------------------- | --------------------------------------------- | ----------------------------------------------- |
| **Compute Engine**       | Spark / Trino / Ray          | DuckDB + Polars (Light Engine only)           | Data volume exceeds 500GB or single query >5min |
| **Vector DB**            | Milvus (dedicated)           | pgvector (PostgreSQL extension)               | >1M embeddings or latency >200ms                |
| **Graph DB**             | Neo4j                        | PostgreSQL recursive CTEs + adjacency lists   | >10K nodes or traversal depth >3                |
| **Heavy Compute**        | Spark cluster                | DuckDB on single-node with Polars             | Distributed processing needed                   |
| **Sandbox Orchestrator** | Kubernetes                   | Docker Compose (single-node)                  | Multi-node / HA required                        |
| **KMS**                  | AWS KMS / Vault              | Vault in dev mode (single instance)           | Production deployment                           |
| **Observability**        | Prometheus + Grafana + Tempo | Prometheus + Grafana (no distributed tracing) | >10 workflows in production                     |
| **Cache**                | Redis Cluster                | Redis (single instance)                       | HA required                                     |

**MVP Scope**: Start with Design Plane + Light Engine + PostgreSQL (with pgvector) + Git + basic RBAC. Add Freeze Bridge with manual review (no canary). Add Heavy Engine and canary gating post-MVP.

**MVP Deployment**: Single `docker-compose up` with all core services. Estimated resource footprint: 4 vCPU, 16GB RAM, 50GB disk. Suitable for teams of 2–5 data professionals.

---

## 14. Design Principles Checklist

- [x] AI is on the exploration side, not the execution side
- [x] Freeze is explicit, reversible, and requires approval
- [x] User modifications are more important than AI generation
- [x] Knowledge Base is the foundation of AI capabilities, requires human confirmation before entering KB
- [x] The system observes but does not disturb, suggests but does not enforce
- [x] Enterprise-grade SDLC + permissions + audit built-in from day one
- [x] All core artifacts can be exported to standard file formats
- [x] Coexist with legacy systems through a multi-layer integration framework
- [x] Auto-generate human-readable documentation before and after changes
- [x] AI Agent permissions are consistent with user roles, cannot exceed authority
- [x] Logs support AI-driven diagnosis and cost tracking

---

*Last updated: 2026-07-04*

---

## 15. C4 Model Diagrams

> 📄 Complete C4 Model content (System Context and Container two-level architecture diagrams + external relationship descriptions + inter-container communication protocol matrix) has been moved to **[docs/architecture/c4-model.md](architecture/c4-model.md)**.
>
> This section retains the architecture summary. For detailed diagrams, external system interface definitions, and inter-container communication protocols (12 Producer→Consumer mappings), please refer to the standalone file.

### 15.1 Architecture Overview

Six user roles (Viewer/Analyst/Developer/Admin/Data Owner/External Auditor) connect via HTTPS/WSS to API Gateway. Core environments of the unified Workflow Engine: Exploration Environment Svc (Python/FastAPI, AI-assisted exploration), Freeze Pipeline (built-in engine operation, AI→deterministic conversion), Production Executor Svc (Go/Rust, zero AI side effects with NetworkPolicy enforcement), Cross-Environment Read-Only Mode Svc (Python/FastAPI, AI read-only analysis, write operations intercepted at Engine level). Cross-Environment Read-Only Mode queries across environments but does not write to any environment state.

Knowledge Base data layer: PostgreSQL (Source of Truth), Milvus/pgvector (Vector Embeddings), Neo4j Cluster (Graph Relations), Elasticsearch (Hot Logs 7d), Redis Sentinel (Cache+Session), S3/MinIO (Object Store) (MVP: pgvector + PG only; Neo4j/Milvus post-MVP per ADR-0013). Code Graph Svc provides impact analysis and lineage tracking based on Neo4j. Kafka/Redpanda serves as the unified message bus.

External systems: Enterprise ERP, Data Warehouse, Email Server, Identity Provider, Git Platform, Jira/ServiceNow, Cloud KMS, Object Store, Slack/Teams.

### 15.2 Inter-Container Communication

The communication matrix covers 12 Producer→Consumer paths: Web SPA→API Gateway (HTTPS JWT), internal service-to-service (gRPC mTLS), KB access (Milvus SDK / PostgreSQL wire / Bolt protocol), Kafka message bus (Avro Schema Registry), notification distribution (SMTP/Webhook). See standalone file for complete matrix.

---

## 16. STRIDE Threat Model

> The complete STRIDE threat matrix (10 components × 6 dimensions, 38 threat entries) + OWASP Top 10 for LLM Applications (v1.0, 2023) item-by-item assessment has been moved to **[docs/security/threat-model.md](security/threat-model.md)**.
>
> Bare `§N` references in the standalone file point to this document; consult here for full context.

### 16.1 Threat Matrix Summary

STRIDE covers 10 core components: Conversation Interface, AI Copilot Engine, Spec Refinement Assistant, Workflow Executor, Query Rewriter, Code Graph, KB Write Pipeline, Email Ingest Gateway, Notification Service, API Gateway.

Key residual risks (P0): AI Copilot Engine provider-side log leakage of sensitive data (H), KB Write Pipeline email PII leakage to LLM (H). See standalone file for complete threat matrix and mitigation measures.

### 16.2 OWASP LLM Assessment Summary

Item-by-item assessment per OWASP Top 10 for LLM Applications (v1.0, 2023):

| Threat | Risk | Defense Status |
| --------------------------------- | ------------ | ---------------------------------------- |
| LLM01 Prompt Injection | [CRITICAL] | Five-layer defense, residual risk: Medium |
| LLM02 Insecure Output Handling | [HIGH] | Adequately defended |
| LLM03 Training Data Poisoning | [HIGH] | Three-path write + human confirmation, residual risk: Medium |
| LLM04 Model DoS | [HIGH] | Adequately defended |
| LLM05 Supply Chain | [HIGH] | [WARN] Needs enhancement: signature verification, SBOM, CVE scanning |
| LLM06 Sensitive Info Disclosure   | [CRITICAL]   | Data classification T0-T3 + encryption + masking, residual risk: Low-Medium |
| LLM07 Insecure Plugin Design      | [HIGH]       | [WARN] Needs enhancement: parameter Schema validation, inter-Skill sanitization    |
| LLM08 Excessive Agency | [HIGH] | Adequately defended (five-level operation classification) |
| LLM09 Overreliance | [MEDIUM] | [WARN] Needs enhancement: AI watermark, quarterly Accuracy Audit |
| LLM10 Model Theft | [MEDIUM] | [WARN] Needs enhancement: access anomaly detection, weight encryption |

> Comprehensive conclusion: This architecture provides adequate defense on LLM01/02/04/08. LLM05/07/09/10 have residual risks requiring enhancement in Phase 6-7. See standalone file for complete assessment, detailed threat entries, and risk remediation priorities.

---

## 17. Deployment Architecture / Infrastructure Topology

### 17.1 Physical Topology Diagram

```
                            INTERNET
                               │
                    ┌──────────┴──────────┐
                    │   CDN (CloudFront / │
                    │   Cloudflare)       │
                    │   Static Assets +   │
                    │   DDoS Protection   │
                    └──────────┬──────────┘
                               │ HTTPS
                    ┌──────────┴──────────┐
                    │   WAF (AWS WAF /    │
                    │   ModSecurity)      │
                    │   OWASP Top 10      │
                    │   Rate Limiting     │
                    └──────────┬──────────┘
                               │
         ┌─────────────────────┴─────────────────────┐
         │          REGION: us-east-1 / cn-north-1    │
         │                                             │
         │  ┌──────────────────────────────────────┐  │
         │  │         PUBLIC DMZ (VPC: 10.0.0.0/24) │  │
         │  │                                        │  │
         │  │  ┌──────────────────────────────────┐ │  │
         │  │  │  ALB (Application Load Balancer) │ │  │
         │  │  │  TLS Termination │ Health Check  │ │  │
         │  │  └────────────┬─────────────────────┘ │  │
         │  └───────────────┼────────────────────────┘  │
         │                  │                            │
         │  ┌───────────────┼────────────────────────┐  │
         │  │  APP SUBNET   │  (VPC: 10.0.1.0/24)   │  │
         │  │               │                         │  │
         │  │  ┌────────────┴──────────────────────┐ │  │
         │  │  │  API Gateway (Kong/Envoy) ×3      │ │  │
         │  │  │  (per-AZ)                          │ │  │
         │  │  └────────────┬──────────────────────┘ │  │
         │  │               │                         │  │
         │  │  ┌────────────┴──────────────────────┐ │  │
         │  │  │  ISTIO/LINKERD SERVICE MESH       │ │  │
         │  │  │  mTLS │ Telemetry │ Circuit Break │ │  │
         │  │  └──┬────┬────┬────┬────┬────┬───────┘ │  │
         │  │     │    │    │    │    │    │          │  │
         │  └─────┼────┼────┼────┼────┼────┼──────────┘  │
         │        │    │    │    │    │    │              │
         │  ┌─────┼────┼────┼────┼────┼────┼──────────┐  │
         │  │     ▼    ▼    ▼    ▼    ▼    ▼           │  │
         │  │  Design │Freeze│Runtime│ Code │ Notif   │  │
         │  │  Plane  │Bridge│ Exec. │Graph │ Service  │  │
         │  │  ×2     │ ×2   │ ×3    │ ×2   │ ×2      │  │
         │  │  (Pod Anti-Affinity across AZs)         │  │
         │  └─────────────────┬────────────────────────┘  │
         │                    │                            │
         │  ┌─────────────────┴────────────────────────┐  │
         │  │  DATA SUBNET (VPC: 10.0.2.0/24)          │  │
         │  │  No public IP │ Security Group: app-only │  │
         │  │                                            │  │
         │  │  ┌──────────────────┐ ┌──────────────────┐│  │
         │  │  │ PG Patroni HA    │ │ Neo4j Cluster    ││  │
         │  │  │ (3 nodes, 1AZ ea)│ │ (3 Core + 2 RR)  ││  │
         │  │  │ ● Primary (AZ-a) │ │ ● Leader (AZ-a)  ││  │
         │  │  │ ○ Replica (AZ-b) │ │ ○ Follower (AZ-b)││  │
         │  │  │ ○ Replica (AZ-c) │ │ ○ Follower (AZ-c)││  │
         │  │  │ etcd for leader  │ │ ○ Read Replica×2 ││  │
         │  │  │ election         │ │                  ││  │
         │  │  └──────────────────┘ └──────────────────┘│  │
         │  │                                            │  │
         │  │  ┌──────────────────┐ ┌──────────────────┐│  │
         │  │  │ Milvus Cluster   │ │ Elasticsearch    ││  │
         │  │  │ (3 Query + 2     │ │ (3 Master + 3    ││  │
         │  │  │  Data + 1 Index) │ │  Data + 2 Coord) ││  │
         │  │  │ etcd + MinIO     │ │ 7-day hot window ││  │
         │  │  └──────────────────┘ └──────────────────┘│  │
         │  │                                            │  │
         │  │  ┌──────────────────┐ ┌──────────────────┐│  │
         │  │  │ Redis Sentinel   │ │ Kafka/Redpanda   ││  │
         │  │  │ (3 Sentinel +    │ │ (3 Brokers,      ││  │
         │  │  │  2 Redis)        │ │  1 per AZ)       ││  │
         │  │  │ Cache+Session    │ │ RF=3, minISR=2   ││  │
         │  │  └──────────────────┘ └──────────────────┘│  │
         │  └────────────────────────────────────────────┘  │
         │                                                  │
         │  ┌────────────────────────────────────────────┐  │
         │  │  CROSS-CUTTING (per node)                  │  │
         │  │  ┌──────────┐ ┌───────────┐ ┌───────────┐ │  │
         │  │  │Prometheus│ │Fluentd/   │ │Vault Agent│ │  │
         │  │  │ Exporter │ │Fluent Bit │ │(sidecar)  │ │  │
         │  │  │(metrics) │ │(log ship) │ │(secrets)  │ │  │
         │  │  └──────────┘ └───────────┘ └───────────┘ │  │
         │  └────────────────────────────────────────────┘  │
         │                                                  │
         │  ┌────────────────────────────────────────────┐  │
         │  │  BACKUP FLOWS                              │  │
         │  │  PG WAL → S3 cross-region (continuous)     │  │
         │  │  Neo4j Dump → S3 (daily, 02:00 UTC)       │  │
         │  │  ES Snapshot → S3 (daily, 03:00 UTC)       │  │
         │  │  S3 Cross-region Replication (async)       │  │
         │  │  Vault Snapshot → encrypted export         │  │
         │  └────────────────────────────────────────────┘  │
         └──────────────────────────────────────────────────┘

   AZ-a (us-east-1a)        AZ-b (us-east-1b)        AZ-c (us-east-1c)
   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
   │ Worker Node ×2  │    │ Worker Node ×2  │    │ Worker Node ×2  │
   │ (app workloads) │    │ (app workloads) │    │ (app workloads) │
   │                 │    │                 │    │                 │
   │ PG Primary      │    │ PG Replica      │    │ PG Replica      │
   │ Neo4j Leader    │    │ Neo4j Follower  │    │ Neo4j Follower  │
   │ Kafka Broker 1  │    │ Kafka Broker 2  │    │ Kafka Broker 3  │
   │ Redis Primary   │    │ Redis Replica   │    │ Redis Sentinel  │
   └─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 17.2 Workload Placement Table

| Service              | Replicas     | Node Selector   | Resource Request | Resource Limit | Anti-Affinity                                                        |
| -------------------- | ------------ | --------------- | ---------------- | -------------- | -------------------------------------------------------------------- |
| Kong Ingress         | 3 (1 per AZ) | `role: gateway` | 1 CPU, 512Mi     | 2 CPU, 1Gi     | `podAntiAffinity: requiredDuringScheduling` by AZ                    |
| Design Plane Svc     | 2            | `role: app`     | 1 CPU, 1Gi       | 4 CPU, 4Gi     | `preferredDuringScheduling` by AZ                                    |
| Freeze Bridge Svc    | 2            | `role: app`     | 0.5 CPU, 512Mi   | 2 CPU, 2Gi     | `preferredDuringScheduling` by AZ                                    |
| Runtime Executor Svc | 3            | `role: app`     | 2 CPU, 2Gi       | 8 CPU, 16Gi    | `preferredDuringScheduling` by AZ                                    |
| Code Graph Svc       | 2            | `role: app`     | 1 CPU, 2Gi       | 4 CPU, 8Gi     | `preferredDuringScheduling` by AZ                                    |
| Notification Svc     | 2            | `role: app`     | 0.5 CPU, 256Mi   | 1 CPU, 512Mi   | `preferredDuringScheduling` by AZ                                    |
| PostgreSQL (Patroni) | 3 (1+2)      | `role: data`    | 4 CPU, 16Gi      | 16 CPU, 64Gi   | `requiredDuringScheduling` by AZ (each node must be in different AZ) |
| Neo4j Cluster        | 5 (3+2)      | `role: data`    | 4 CPU, 16Gi      | 16 CPU, 64Gi   | `requiredDuringScheduling` by AZ for Core nodes                      |
| Milvus Query Node    | 3            | `role: data`    | 4 CPU, 16Gi      | 16 CPU, 64Gi   | `preferredDuringScheduling` by AZ                                    |
| Milvus Data Node     | 2            | `role: data`    | 8 CPU, 32Gi      | 32 CPU, 128Gi  | `preferredDuringScheduling` by AZ                                    |
| Elasticsearch Master | 3            | `role: data`    | 2 CPU, 4Gi       | 4 CPU, 8Gi     | `requiredDuringScheduling` by AZ                                     |
| Elasticsearch Data   | 3            | `role: data`    | 8 CPU, 32Gi      | 16 CPU, 64Gi   | `preferredDuringScheduling` by AZ                                    |
| Redis (Sentinel)     | 5 (3+2)      | `role: data`    | 1 CPU, 2Gi       | 2 CPU, 4Gi     | `preferredDuringScheduling` by AZ                                    |
| Kafka Broker         | 3            | `role: data`    | 4 CPU, 8Gi       | 8 CPU, 16Gi    | `requiredDuringScheduling` by AZ                                     |
| Prometheus           | 1            | `role: monitor` | 2 CPU, 8Gi       | 4 CPU, 16Gi    | N/A (StatefulSet)                                                    |
| Grafana              | 1            | `role: monitor` | 0.5 CPU, 512Mi   | 1 CPU, 1Gi     | N/A                                                                  |

### 17.3 Network Security Group Rules

| Source                   | Destination               | Protocol  | Port           | Purpose                                         |
| ------------------------ | ------------------------- | --------- | -------------- | ----------------------------------------------- |
| Internet (0.0.0.0/0)     | ALB (Public DMZ)          | TCP/TLS   | 443            | User HTTPS traffic                              |
| ALB                      | API Gateway (App Subnet)  | TCP/HTTPS | 8443           | Proxied requests                                |
| API Gateway              | App Services (Mesh)       | TCP/mTLS  | 9080           | Service mesh routing                            |
| App Services             | Data Subnet (PG)          | TCP/TLS   | 5432           | PostgreSQL queries                              |
| App Services             | Data Subnet (Neo4j)       | TCP/TLS   | 7687           | Bolt protocol                                   |
| App Services             | Data Subnet (Milvus)      | TCP/gRPC  | 19530          | Vector operations                               |
| App Services             | Data Subnet (ES)          | TCP/HTTPS | 9200           | Log queries                                     |
| App Services             | Data Subnet (Redis)       | TCP/TLS   | 6379           | Cache access                                    |
| App Services             | Data Subnet (Kafka)       | TCP/mTLS  | 9093           | Message produce/consume                         |
| Data Subnet (PG Primary) | Data Subnet (PG Replicas) | TCP/TLS   | 5432           | Streaming replication                           |
| App Services (`role: exploration`)  | MCP Gateway / LLM API Endpoint | TCP/TLS   | 443            | LLM invocation for all `llm_reasoning` capabilities                                                                                                              |
| App Services (`role: production`)   | MCP Gateway / LLM API Endpoint | TCP/TLS   | 443            | LLM invocation for `read_analyze` and `suggest_plan` only (Engine-level enforcement as primary gate; NetworkPolicy provides defense-in-depth)                   |
| App Services (`role: production`)   | 0.0.0.0/0 (Internet)         | TCP/TLS   | 443            | **DENY** (default-deny for Production egress to internet; explicit allow only to MCP Gateway and approved endpoints)                                           |
| App Services (`role: cross-env-read`)| Data Subnet (PG Read Replicas)| TCP/TLS   | 5432           | Read-only queries against Exploration and Production read replicas                                                                                              |
| App Subnet               | S3 Gateway Endpoint       | HTTPS     | 443            | Object store access (VPC endpoint, no internet) |
| App Subnet               | KMS Endpoint              | HTTPS     | 443            | Key operations (VPC endpoint)                   |
| Monitor Subnet           | All Subnets               | TCP       | 9100/9113/9150 | Prometheus scraping                             |

### 17.3.1 Environment-Level NetworkPolicy (Kubernetes)

Per ADR-0025, Production Environment Pods require Kubernetes NetworkPolicy resources that complement the cloud-level Security Group rules. These provide defense-in-depth for the "zero AI side effects" guarantee:

```yaml
# Production Environment — default-deny all egress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: production-deny-all-egress
  namespace: production
spec:
  podSelector:
    matchLabels:
      environment: production
  policyTypes:
  - Egress
  egress:
  # Allow only: MCP Gateway, Data Subnet, S3 Gateway, KMS, DNS
  - to:
    - namespaceSelector:
        matchLabels:
          name: mcp-gateway
    ports:
    - protocol: TCP
      port: 443
  - to:
    - podSelector:
        matchLabels:
          role: data
    ports:
    - protocol: TCP
      port: 5432
  - to:  # S3 VPC Endpoint
    - ipBlock:
        cidr: 10.0.3.0/24
    ports:
    - protocol: TCP
      port: 443
  - to:  # DNS (required for service discovery)
    - namespaceSelector: {}
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53
```

**Enforcement model** (defense-in-depth for zero AI side effects):
1. **Engine level** (primary): Workflow Engine rejects Jobs whose `llm.capability` is not in the environment's `allowed_capabilities` list. Rejection occurs at Job submission time.
2. **NetworkPolicy level**: Production Pods cannot egress to the internet. MCP Gateway is the sole allowed external endpoint. Direct LLM provider API calls are impossible — all LLM traffic routes through MCP Gateway.
3. **Sandbox level**: Existing seccomp profiles (§7.2) block network egress at the Job sandbox level.

This layered enforcement means that even if the Engine-level check is misconfigured, the NetworkPolicy still blocks LLM API egress, and even if NetworkPolicy is misconfigured, the Sandbox seccomp still blocks network calls. Auditors can independently verify each layer.

---

## 18. Core Entity ERD

> The complete core entity model (DDL-level definitions of 7 entities, ERD relationship diagram, partitioning strategy, index design) has been moved to **[docs/architecture/entity-erd.md](architecture/entity-erd.md)**.
>
> This section retains the entity list summary. For detailed DDL definitions, index strategies, partitioning schemes, and ERD relationship diagrams, please refer to the standalone file.

### 18.1 Core Entity List

| Entity | Purpose | Key Design |
| ---------------- | ---------------- | ------------------------------------------------------------------ |
| **tenant** | Multi-tenant anchor | UUID PK, isolation_level (L1/L2/L3), JSONB config |
| **workflow** | Top-level unit of work | spec_yaml immutable after freeze, workflow_version as version chain |
| **job** | Smallest DAG execution unit | 10 types, UUID[] dependencies, engine overridable |
| **data_source** | Registered external data source | connector_config encrypted, schema_catalog periodically refreshed, T0-T3 classification |
| **kb_entry** | KB entry (9 domains) | content_vector (1536-dim), partitioned by domain LIST, superseded_by version chain |
| **audit_log** | Immutable audit log | BIGSERIAL PK, monthly RANGE partitioning, no FK constraints, 7-year hot storage |
| **user_session** | User identity and session | idp_subject immutable, extra_permissions time-limited authorization |
| **incident** | Operations event | severity P0-P4, SLA auto-calculated, context JSONB with full context |

### 18.2 ERD Relationships
All entities are tenant-scoped (tenant_id FK). workflow 1:N job, dependencies self-referencing. kb_entry self-referencing version chain via parent_id + superseded_by. incident associates with workflow/job/user. audit_log references all entity UUIDs but does not set FK (immutable log independence). See standalone file for complete ERD diagram.

---

## 19. SLO / SLI Definitions with Error Budgets

> 📄 Complete SLO/SLI definitions (detailed SLI metrics, SLO targets, error budget strategies for 5 critical user journeys) have been moved to **[docs/operations/slo-sli.md](operations/slo-sli.md)**.
>
> This section retains the SLO summary table. For complete definitions, SLI measurement methods, exclusion conditions, and error budget exhaustion gating strategies, please refer to the standalone file.

### 19.1 Critical User Journey SLOs Summary

| Journey             | SLI                    | SLO            | Monthly Error Budget |
| ------------------- | ---------------------- | -------------- | ------------- |
| NL → Preview        | p95 latency            | ≤15s           | 5% (~33.6h)   |
| Freeze → Deploy     | p95 TTP                | ≤4h (standard) | 10% (~67.2h)  |
| Scheduled Execution | Success rate           | ≥99.5%         | 0.5% (~3.36h) |
| AI Agent QA         | p95 latency + accuracy | ≤20s + ≥85%    | 5% latency (~33.6h) / 15% accuracy |
| Recon Run (1M rows) | p95 duration           | ≤5min          | 5% (~3.36h)   |

For error budget exhaustion gating strategy details, see the standalone file.

---

## 20. CDC Pipeline Architecture Detail

> **Migrated** to [`docs/sub-projects/knowledge-services/cdc-pipeline.md`](sub-projects/knowledge-services/cdc-pipeline.md) (§20). This stub preserves the `§20` anchor required by ADRs and `docs/01-facts.md`.

### 20.1 Architecture Overview

> **Migrated** to [`docs/sub-projects/knowledge-services/cdc-pipeline.md`](sub-projects/knowledge-services/cdc-pipeline.md) (§20.1). This stub preserves the `§20.1` anchor required by ADRs and `docs/01-facts.md`.

### 20.2 Technology Justification: Debezium + Kafka Connect vs. PG Logical Replication Directly

> **Migrated** to [`docs/sub-projects/knowledge-services/cdc-pipeline.md`](sub-projects/knowledge-services/cdc-pipeline.md) (§20.2). This stub preserves the `§20.2` anchor required by ADRs and `docs/01-facts.md`.

### 20.3 Per-Target Transformation Logic

> **Migrated** to [`docs/sub-projects/knowledge-services/cdc-pipeline.md`](sub-projects/knowledge-services/cdc-pipeline.md) (§20.3). This stub preserves the `§20.3` anchor required by ADRs and `docs/01-facts.md`.

#### 20.3.1 Vector DB Sink (kb_entry → Milvus)

> **Migrated** to [`docs/sub-projects/knowledge-services/cdc-pipeline.md`](sub-projects/knowledge-services/cdc-pipeline.md) (§20.3.1). This stub preserves the `§20.3.1` anchor required by ADRs and `docs/01-facts.md`.

#### 20.3.2 Graph DB Sink (workflow, kb_entry → Neo4j)

> **Migrated** to [`docs/sub-projects/knowledge-services/cdc-pipeline.md`](sub-projects/knowledge-services/cdc-pipeline.md) (§20.3.2). This stub preserves the `§20.3.2` anchor required by ADRs and `docs/01-facts.md`.

### 20.4 Failure Modes and Recovery Procedures

> **Migrated** to [`docs/sub-projects/knowledge-services/cdc-pipeline.md`](sub-projects/knowledge-services/cdc-pipeline.md) (§20.4). This stub preserves the `§20.4` anchor required by ADRs and `docs/01-facts.md`.

### 20.5 Backfill Strategy: Initial Population from Relational DB to Vector/Graph

> **Migrated** to [`docs/sub-projects/knowledge-services/cdc-pipeline.md`](sub-projects/knowledge-services/cdc-pipeline.md) (§20.5). This stub preserves the `§20.5` anchor required by ADRs and `docs/01-facts.md`.

## 21. Key Sequence Diagrams

> **Migrated** to [`docs/sub-projects/_shared/sequence-diagrams.md`](sub-projects/_shared/sequence-diagrams.md) (§21). This stub preserves the `§21` anchor required by ADRs and `docs/01-facts.md`.

### 21.1 Freeze Flow: Full End-to-End

> **Migrated** to [`docs/sub-projects/_shared/sequence-diagrams.md`](sub-projects/_shared/sequence-diagrams.md) (§21.1). This stub preserves the `§21.1` anchor required by ADRs and `docs/01-facts.md`.

### 21.2 Runtime Execution with Failure

> **Migrated** to [`docs/sub-projects/_shared/sequence-diagrams.md`](sub-projects/_shared/sequence-diagrams.md) (§21.2). This stub preserves the `§21.2` anchor required by ADRs and `docs/01-facts.md`.

### 21.3 AI Agent Query with Permission Gating

> **Migrated** to [`docs/sub-projects/_shared/sequence-diagrams.md`](sub-projects/_shared/sequence-diagrams.md) (§21.3). This stub preserves the `§21.3` anchor required by ADRs and `docs/01-facts.md`.

## Appendix: Section Index

| Section | Title                                    | Content Type                                                                                                                   |
| ------- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| §1–§2   | Core Philosophy & Panoramic Architecture | Architecture Overview                                                                                                          |
| **§3**  | **Unified Workflow Engine**              | **→ [docs/sub-projects/workflow-engine/](sub-projects/workflow-engine/) (§3.1–§3.5)**                                           |
| **§4**  | **Freeze Pipeline**                      | **→ [docs/sub-projects/workflow-engine/freeze-pipeline.md](sub-projects/workflow-engine/freeze-pipeline.md)**                   |
| **§5**  | **Production Environment**               | **→ [docs/sub-projects/query-serving/](sub-projects/query-serving/) (§5.1–§5.4)**                                              |
| **§6**  | **Compute Spec**                         | **→ [docs/sub-projects/workflow-engine/compute-spec.md](sub-projects/workflow-engine/compute-spec.md)**                         |
| **§7**  | **Execution Sandbox**                    | **→ [docs/sub-projects/workflow-engine/execution-sandbox.md](sub-projects/workflow-engine/execution-sandbox.md)**               |
| **§8**  | **Log System**                           | **→ [docs/sub-projects/platform-core/observability.md](sub-projects/platform-core/observability.md)**                           |
| **§9**  | **Change Intelligence & Agent Triage**   | **→ [docs/sub-projects/knowledge-services/change-intelligence.md](sub-projects/knowledge-services/change-intelligence.md)**     |
| **§10** | **Knowledge Base**                       | **→ [docs/sub-projects/knowledge-services/knowledge-base.md](sub-projects/knowledge-services/knowledge-base.md)**               |
| **§11** | **Cross-Cutting Layer**                  | **→ [docs/sub-projects/platform-core/cross-cutting-layer.md](sub-projects/platform-core/cross-cutting-layer.md)**               |
| **§12** | **Domain-Specific Components**           | **→ [docs/sub-projects/data-health/](sub-projects/data-health/) (§12.2) + [platform-core/domain-services.md](sub-projects/platform-core/domain-services.md) (§12.1, §12.3–§12.7)** |
| §13     | Technology Selection                     | Stack & MVP                                                                                                                    |
| §14     | Design Principles Checklist              | Requirements Coverage                                                                                                          |
| **§15** | **C4 Model Diagrams**                    | **→ [docs/architecture/c4-model.md](architecture/c4-model.md)**                                                                |
| **§16** | **STRIDE Threat Model**                  | **→ [docs/security/threat-model.md](security/threat-model.md)**                                                                |
| **§17** | **Deployment Architecture**              | **Multi-AZ K8s Topology**                                                                                                      |
| **§18** | **Core Entity ERD**                      | **→ [docs/architecture/entity-erd.md](architecture/entity-erd.md)**                                                            |
| **§19** | **SLO/SLI Definitions**                  | **→ [docs/operations/slo-sli.md](operations/slo-sli.md)**                                                                      |
| **§20** | **CDC Pipeline Architecture**            | **→ [docs/sub-projects/knowledge-services/cdc-pipeline.md](sub-projects/knowledge-services/cdc-pipeline.md)**                   |
| **§21** | **Key Sequence Diagrams**                | **→ [docs/sub-projects/_shared/sequence-diagrams.md](sub-projects/_shared/sequence-diagrams.md)**                               |
| **§22** | **AI Agent Deep Design**                 | **→ [docs/sub-projects/agent-platform/](sub-projects/agent-platform/) (§22A–§22M)**                                             |
| **§23** | **BRD & ADR as First-Class Entities**    | **→ [docs/sub-projects/brd-adr-lifecycle/](sub-projects/brd-adr-lifecycle/) (§23.1–§23.12)**                                    |
| **§24** | **Operational Architecture**             | **→ [docs/sub-projects/platform-core/operational-architecture.md](sub-projects/platform-core/operational-architecture.md)**     |
| **§25** | **Compliance Architecture**              | **→ [docs/sub-projects/platform-core/compliance-architecture.md](sub-projects/platform-core/compliance-architecture.md)**       |

---

## 22. AI Agent Deep Design

> **Migrated** to [`docs/sub-projects/agent-platform/`](sub-projects/agent-platform/) (§22A–§22M). This stub preserves the `§22` anchor required by ADRs and `docs/01-facts.md`.

## 22A. Agent SDK Architecture — Dual-Mode Orchestration

> **Migrated** to [`docs/sub-projects/agent-platform/dual-mode-orchestration.md`](sub-projects/agent-platform/dual-mode-orchestration.md) (§22A). This stub preserves the `§22A` anchor required by ADRs and `docs/01-facts.md`.

### 22A.1 Agent Runtime Overall Architecture (Exploration Mode)

> **Migrated** to [`docs/sub-projects/agent-platform/dual-mode-orchestration.md`](sub-projects/agent-platform/dual-mode-orchestration.md) (§22A.1). This stub preserves the `§22A.1` anchor required by ADRs and `docs/01-facts.md`.

### 22A.2 Tool-Call Flow — Detailed Steps

> **Migrated** to [`docs/sub-projects/agent-platform/dual-mode-orchestration.md`](sub-projects/agent-platform/dual-mode-orchestration.md) (§22A.2). This stub preserves the `§22A.2` anchor required by ADRs and `docs/01-facts.md`.

### 22A.3 ReAct Loop (Multi-Round Reasoning)

> **Migrated** to [`docs/sub-projects/agent-platform/dual-mode-orchestration.md`](sub-projects/agent-platform/dual-mode-orchestration.md) (§22A.3). This stub preserves the `§22A.3` anchor required by ADRs and `docs/01-facts.md`.

### 22A.4 Durable Execution & Idempotency → adr/0017

> **Migrated** to [`docs/sub-projects/agent-platform/dual-mode-orchestration.md`](sub-projects/agent-platform/dual-mode-orchestration.md) (§22A.4). This stub preserves the `§22A.4` anchor required by ADRs and `docs/01-facts.md`.

### 22A.5 Multi-Model Support

> **Migrated** to [`docs/sub-projects/agent-platform/dual-mode-orchestration.md`](sub-projects/agent-platform/dual-mode-orchestration.md) (§22A.5). This stub preserves the `§22A.5` anchor required by ADRs and `docs/01-facts.md`.

### 22A.6 Hierarchical Multi-Agent Architecture (Evolution Direction, Phase 7+)

> **Migrated** to [`docs/sub-projects/agent-platform/dual-mode-orchestration.md`](sub-projects/agent-platform/dual-mode-orchestration.md) (§22A.6). This stub preserves the `§22A.6` anchor required by ADRs and `docs/01-facts.md`.

## 22B. Complete Skill Catalog

> **Migrated** to [`docs/sub-projects/agent-platform/skill-catalog.md`](sub-projects/agent-platform/skill-catalog.md) (§22B). This stub preserves the `§22B` anchor required by ADRs and `docs/01-facts.md`.

## 22C. MCP Server Catalog

> **Migrated** to [`docs/sub-projects/agent-platform/mcp-catalog.md`](sub-projects/agent-platform/mcp-catalog.md) (§22C). This stub preserves the `§22C` anchor required by ADRs and `docs/01-facts.md`.

## 22D. Agent Security Architecture — 7-Layer Anti-Exploitation Defense

> **Migrated** to [`docs/sub-projects/agent-platform/agent-security.md`](sub-projects/agent-platform/agent-security.md) (§22D). This stub preserves the `§22D` anchor required by ADRs and `docs/01-facts.md`.

## 22E. Agent Workflow Composition — Skill Chaining

> **Migrated** to [`docs/sub-projects/agent-platform/workflow-composition.md`](sub-projects/agent-platform/workflow-composition.md) (§22E). This stub preserves the `§22E` anchor required by ADRs and `docs/01-facts.md`.

## 22F. Agent Multi-Tenant Isolation

> **Migrated** to [`docs/sub-projects/agent-platform/verified-path-and-governance.md`](sub-projects/agent-platform/verified-path-and-governance.md) (§22F). This stub preserves the `§22F` anchor required by ADRs and `docs/01-facts.md`.

### 22F.1 Tenant Context Injection (Session Context)

> **Migrated** to [`docs/sub-projects/agent-platform/verified-path-and-governance.md`](sub-projects/agent-platform/verified-path-and-governance.md) (§22F.1). This stub preserves the `§22F.1` anchor required by ADRs and `docs/01-facts.md`.

### 22F.2 MCP-Level Tenant Filtering

> **Migrated** to [`docs/sub-projects/agent-platform/verified-path-and-governance.md`](sub-projects/agent-platform/verified-path-and-governance.md) (§22F.2). This stub preserves the `§22F.2` anchor required by ADRs and `docs/01-facts.md`.

### 22F.3 Model Isolation (Optional — Regulated Tenants)

> **Migrated** to [`docs/sub-projects/agent-platform/verified-path-and-governance.md`](sub-projects/agent-platform/verified-path-and-governance.md) (§22F.3). This stub preserves the `§22F.3` anchor required by ADRs and `docs/01-facts.md`.

### 22F.4 Log & Audit Isolation

> **Migrated** to [`docs/sub-projects/agent-platform/verified-path-and-governance.md`](sub-projects/agent-platform/verified-path-and-governance.md) (§22F.4). This stub preserves the `§22F.4` anchor required by ADRs and `docs/01-facts.md`.

### 22F.5 Cross-Tenant Isolation Verification

> **Migrated** to [`docs/sub-projects/agent-platform/verified-path-and-governance.md`](sub-projects/agent-platform/verified-path-and-governance.md) (§22F.5). This stub preserves the `§22F.5` anchor required by ADRs and `docs/01-facts.md`.

## 22G. Summary: Agent Architecture Decision Records

> **Migrated** to [`docs/sub-projects/agent-platform/verified-path-and-governance.md`](sub-projects/agent-platform/verified-path-and-governance.md) (§22G). This stub preserves the `§22G` anchor required by ADRs and `docs/01-facts.md`.

## 22H. Verified Path Catalog

> **Migrated** to [`docs/sub-projects/agent-platform/verified-path-and-governance.md`](sub-projects/agent-platform/verified-path-and-governance.md) (§22H). This stub preserves the `§22H` anchor required by ADRs and `docs/01-facts.md`.

## 22I. Agent Evaluation Framework → adr/0018

> **Migrated** to [`docs/sub-projects/agent-platform/memory-and-evaluation.md`](sub-projects/agent-platform/memory-and-evaluation.md) (§22I). This stub preserves the `§22I` anchor required by ADRs and `docs/01-facts.md`.

### 22I.1 Six-Dimension Trajectory Scoring

> **Migrated** to [`docs/sub-projects/agent-platform/memory-and-evaluation.md`](sub-projects/agent-platform/memory-and-evaluation.md) (§22I.1). This stub preserves the `§22I.1` anchor required by ADRs and `docs/01-facts.md`.

### 22I.2 Compound Error Tracking

> **Migrated** to [`docs/sub-projects/agent-platform/memory-and-evaluation.md`](sub-projects/agent-platform/memory-and-evaluation.md) (§22I.2). This stub preserves the `§22I.2` anchor required by ADRs and `docs/01-facts.md`.

### 22I.3 Evaluation Flywheel

> **Migrated** to [`docs/sub-projects/agent-platform/memory-and-evaluation.md`](sub-projects/agent-platform/memory-and-evaluation.md) (§22I.3). This stub preserves the `§22I.3` anchor required by ADRs and `docs/01-facts.md`.

### 22I.4 Golden Dataset

> **Migrated** to [`docs/sub-projects/agent-platform/memory-and-evaluation.md`](sub-projects/agent-platform/memory-and-evaluation.md) (§22I.4). This stub preserves the `§22I.4` anchor required by ADRs and `docs/01-facts.md`.

### 22I.5 Three-Layer Monitoring Dashboard

> **Migrated** to [`docs/sub-projects/agent-platform/memory-and-evaluation.md`](sub-projects/agent-platform/memory-and-evaluation.md) (§22I.5). This stub preserves the `§22I.5` anchor required by ADRs and `docs/01-facts.md`.

### 22I.6 Evaluation Frequency

> **Migrated** to [`docs/sub-projects/agent-platform/memory-and-evaluation.md`](sub-projects/agent-platform/memory-and-evaluation.md) (§22I.6). This stub preserves the `§22I.6` anchor required by ADRs and `docs/01-facts.md`.

## 22J. Agent Memory Architecture (Agent Four-Layer Memory Architecture) → adr/0019

> **Migrated** to [`docs/sub-projects/agent-platform/memory-and-evaluation.md`](sub-projects/agent-platform/memory-and-evaluation.md) (§22J). This stub preserves the `§22J` anchor required by ADRs and `docs/01-facts.md`.

### 22J.1 Four-Layer Model

> **Migrated** to [`docs/sub-projects/agent-platform/memory-and-evaluation.md`](sub-projects/agent-platform/memory-and-evaluation.md) (§22J.1). This stub preserves the `§22J.1` anchor required by ADRs and `docs/01-facts.md`.

### 22J.2 L1 Working Memory

> **Migrated** to [`docs/sub-projects/agent-platform/memory-and-evaluation.md`](sub-projects/agent-platform/memory-and-evaluation.md) (§22J.2). This stub preserves the `§22J.2` anchor required by ADRs and `docs/01-facts.md`.

### 22J.3 L2 Episodic Memory (New)

> **Migrated** to [`docs/sub-projects/agent-platform/memory-and-evaluation.md`](sub-projects/agent-platform/memory-and-evaluation.md) (§22J.3). This stub preserves the `§22J.3` anchor required by ADRs and `docs/01-facts.md`.

### 22J.4 L3 Semantic Memory (New)

> **Migrated** to [`docs/sub-projects/agent-platform/memory-and-evaluation.md`](sub-projects/agent-platform/memory-and-evaluation.md) (§22J.4). This stub preserves the `§22J.4` anchor required by ADRs and `docs/01-facts.md`.

### 22J.5 Provenance Marking

> **Migrated** to [`docs/sub-projects/agent-platform/memory-and-evaluation.md`](sub-projects/agent-platform/memory-and-evaluation.md) (§22J.5). This stub preserves the `§22J.5` anchor required by ADRs and `docs/01-facts.md`.

### 22J.6 Graduation Rules

> **Migrated** to [`docs/sub-projects/agent-platform/memory-and-evaluation.md`](sub-projects/agent-platform/memory-and-evaluation.md) (§22J.6). This stub preserves the `§22J.6` anchor required by ADRs and `docs/01-facts.md`.

### 22J.7 Bitemporal Validity

> **Migrated** to [`docs/sub-projects/agent-platform/memory-and-evaluation.md`](sub-projects/agent-platform/memory-and-evaluation.md) (§22J.7). This stub preserves the `§22J.7` anchor required by ADRs and `docs/01-facts.md`.

## 22K. Agent Cost Governance & Model Degradation Detection → adr/0020

> **Migrated** to [`docs/sub-projects/agent-platform/verified-path-and-governance.md`](sub-projects/agent-platform/verified-path-and-governance.md) (§22K). This stub preserves the `§22K` anchor required by ADRs and `docs/01-facts.md`.

### 22K.1 Tiered Token Budget System

> **Migrated** to [`docs/sub-projects/agent-platform/verified-path-and-governance.md`](sub-projects/agent-platform/verified-path-and-governance.md) (§22K.1). This stub preserves the `§22K.1` anchor required by ADRs and `docs/01-facts.md`.

### 22K.2 Graduated Execution (Non-Binary Blocking)

> **Migrated** to [`docs/sub-projects/agent-platform/verified-path-and-governance.md`](sub-projects/agent-platform/verified-path-and-governance.md) (§22K.2). This stub preserves the `§22K.2` anchor required by ADRs and `docs/01-facts.md`.

### 22K.3 Loop Detection (Runaway Exploration Prevention)

> **Migrated** to [`docs/sub-projects/agent-platform/verified-path-and-governance.md`](sub-projects/agent-platform/verified-path-and-governance.md) (§22K.3). This stub preserves the `§22K.3` anchor required by ADRs and `docs/01-facts.md`.

### 22K.4 Model Degradation Detection: Four-Stage Funnel

> **Migrated** to [`docs/sub-projects/agent-platform/verified-path-and-governance.md`](sub-projects/agent-platform/verified-path-and-governance.md) (§22K.4). This stub preserves the `§22K.4` anchor required by ADRs and `docs/01-facts.md`.

### 22K.5 Auto-Rollback Triggers

> **Migrated** to [`docs/sub-projects/agent-platform/verified-path-and-governance.md`](sub-projects/agent-platform/verified-path-and-governance.md) (§22K.5). This stub preserves the `§22K.5` anchor required by ADRs and `docs/01-facts.md`.

### 22K.6 CI Regression Gate

> **Migrated** to [`docs/sub-projects/agent-platform/verified-path-and-governance.md`](sub-projects/agent-platform/verified-path-and-governance.md) (§22K.6). This stub preserves the `§22K.6` anchor required by ADRs and `docs/01-facts.md`.

## 22L. VP Promotion & Multi-Agent Concurrency → adr/0021

> **Migrated** to [`docs/sub-projects/agent-platform/verified-path-and-governance.md`](sub-projects/agent-platform/verified-path-and-governance.md) (§22L). This stub preserves the `§22L` anchor required by ADRs and `docs/01-facts.md`.

### 22L.1 VP Risk-Level Promotion

> **Migrated** to [`docs/sub-projects/agent-platform/verified-path-and-governance.md`](sub-projects/agent-platform/verified-path-and-governance.md) (§22L.1). This stub preserves the `§22L.1` anchor required by ADRs and `docs/01-facts.md`.

### 22L.2 Multi-Layer Concurrency Control

> **Migrated** to [`docs/sub-projects/agent-platform/verified-path-and-governance.md`](sub-projects/agent-platform/verified-path-and-governance.md) (§22L.2). This stub preserves the `§22L.2` anchor required by ADRs and `docs/01-facts.md`.

### 22L.3 Priority Preemption

> **Migrated** to [`docs/sub-projects/agent-platform/verified-path-and-governance.md`](sub-projects/agent-platform/verified-path-and-governance.md) (§22L.3). This stub preserves the `§22L.3` anchor required by ADRs and `docs/01-facts.md`.

## 22M. Agent Capability Discovery → adr/0021

> **Migrated** to [`docs/sub-projects/agent-platform/verified-path-and-governance.md`](sub-projects/agent-platform/verified-path-and-governance.md) (§22M). This stub preserves the `§22M` anchor required by ADRs and `docs/01-facts.md`.

### 22M.1 Three-Layer Progressive Capability Reveal

> **Migrated** to [`docs/sub-projects/agent-platform/verified-path-and-governance.md`](sub-projects/agent-platform/verified-path-and-governance.md) (§22M.1). This stub preserves the `§22M.1` anchor required by ADRs and `docs/01-facts.md`.

### 22M.2 Starter Prompt Cards

> **Migrated** to [`docs/sub-projects/agent-platform/verified-path-and-governance.md`](sub-projects/agent-platform/verified-path-and-governance.md) (§22M.2). This stub preserves the `§22M.2` anchor required by ADRs and `docs/01-facts.md`.

### 22M.3 Context-Aware Suggestions

> **Migrated** to [`docs/sub-projects/agent-platform/verified-path-and-governance.md`](sub-projects/agent-platform/verified-path-and-governance.md) (§22M.3). This stub preserves the `§22M.3` anchor required by ADRs and `docs/01-facts.md`.

### 22M.4 Clarification Instead of Guessing When Intent is Ambiguous

> **Migrated** to [`docs/sub-projects/agent-platform/verified-path-and-governance.md`](sub-projects/agent-platform/verified-path-and-governance.md) (§22M.4). This stub preserves the `§22M.4` anchor required by ADRs and `docs/01-facts.md`.

## 23. BRD & ADR as First-Class Entities

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/`](sub-projects/brd-adr-lifecycle/) (§23.1–§23.12). This stub preserves the `§23` anchor required by ADRs and `docs/01-facts.md`.

## 23.1 Industry Best Practice Analysis

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/`](sub-projects/brd-adr-lifecycle/) (§23.1). This stub preserves the `§23.1` anchor required by ADRs and `docs/01-facts.md`.

## 23.2 BRD Entity Model

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/brd-entity-model.md`](sub-projects/brd-adr-lifecycle/brd-entity-model.md) (§23.2). This stub preserves the `§23.2` anchor required by ADRs and `docs/01-facts.md`.

### 23.2.1 BRD YAML Schema

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/brd-entity-model.md`](sub-projects/brd-adr-lifecycle/brd-entity-model.md) (§23.2.1). This stub preserves the `§23.2.1` anchor required by ADRs and `docs/01-facts.md`.

### 23.2.2 BRD as Code Graph Node

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/brd-entity-model.md`](sub-projects/brd-adr-lifecycle/brd-entity-model.md) (§23.2.2). This stub preserves the `§23.2.2` anchor required by ADRs and `docs/01-facts.md`.

## 23.3 ADR Entity Model

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/adr-entity-model.md`](sub-projects/brd-adr-lifecycle/adr-entity-model.md) (§23.3). This stub preserves the `§23.3` anchor required by ADRs and `docs/01-facts.md`.

### 23.3.1 ADR YAML Schema

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/adr-entity-model.md`](sub-projects/brd-adr-lifecycle/adr-entity-model.md) (§23.3.1). This stub preserves the `§23.3.1` anchor required by ADRs and `docs/01-facts.md`.

### 23.3.2 ADR-to-MADR Mapping

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/adr-entity-model.md`](sub-projects/brd-adr-lifecycle/adr-entity-model.md) (§23.3.2). This stub preserves the `§23.3.2` anchor required by ADRs and `docs/01-facts.md`.

## 23.4 BRD/ADR Lifecycle State Machine

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/lifecycle-state-machine.md`](sub-projects/brd-adr-lifecycle/lifecycle-state-machine.md) (§23.4). This stub preserves the `§23.4` anchor required by ADRs and `docs/01-facts.md`.

### 23.4.1 BRD Lifecycle (Extended State Machine)

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/lifecycle-state-machine.md`](sub-projects/brd-adr-lifecycle/lifecycle-state-machine.md) (§23.4.1). This stub preserves the `§23.4.1` anchor required by ADRs and `docs/01-facts.md`.

### 23.4.2 ADR Lifecycle (Extended State Machine)

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/lifecycle-state-machine.md`](sub-projects/brd-adr-lifecycle/lifecycle-state-machine.md) (§23.4.2). This stub preserves the `§23.4.2` anchor required by ADRs and `docs/01-facts.md`.

#### 23.4.3 State Transition Diagrams

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/lifecycle-state-machine.md`](sub-projects/brd-adr-lifecycle/lifecycle-state-machine.md) (§23.4.3). This stub preserves the `§23.4.3` anchor required by ADRs and `docs/01-facts.md`.

#### 23.4.4 Guard Conditions (Selection)

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/lifecycle-state-machine.md`](sub-projects/brd-adr-lifecycle/lifecycle-state-machine.md) (§23.4.4). This stub preserves the `§23.4.4` anchor required by ADRs and `docs/01-facts.md`.

## 23.5 AI-Assisted Generation Pipeline

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/generation-pipeline.md`](sub-projects/brd-adr-lifecycle/generation-pipeline.md) (§23.5). This stub preserves the `§23.5` anchor required by ADRs and `docs/01-facts.md`.

### 23.5.1 BRD Generation Agent Pipeline Overview

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/generation-pipeline.md`](sub-projects/brd-adr-lifecycle/generation-pipeline.md) (§23.5.1). This stub preserves the `§23.5.1` anchor required by ADRs and `docs/01-facts.md`.

### 23.5.2 BRD-IntentDeepener (Requirements Tracing)

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/generation-pipeline.md`](sub-projects/brd-adr-lifecycle/generation-pipeline.md) (§23.5.2). This stub preserves the `§23.5.2` anchor required by ADRs and `docs/01-facts.md`.

### 23.5.3 BRD-ContextGatherer (Context Collection)

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/generation-pipeline.md`](sub-projects/brd-adr-lifecycle/generation-pipeline.md) (§23.5.3). This stub preserves the `§23.5.3` anchor required by ADRs and `docs/01-facts.md`.

### 23.5.4 BRD-VaguenessResolver (Vagueness Disambiguation)

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/generation-pipeline.md`](sub-projects/brd-adr-lifecycle/generation-pipeline.md) (§23.5.4). This stub preserves the `§23.5.4` anchor required by ADRs and `docs/01-facts.md`.

### 23.5.5 BRD-DraftWriter (Chapter-by-Chapter Generation + Inline AssumptionCheck)

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/generation-pipeline.md`](sub-projects/brd-adr-lifecycle/generation-pipeline.md) (§23.5.5). This stub preserves the `§23.5.5` anchor required by ADRs and `docs/01-facts.md`.

### 23.5.6 BRD-Verifier (6-Round Deep Verification)

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/generation-pipeline.md`](sub-projects/brd-adr-lifecycle/generation-pipeline.md) (§23.5.6). This stub preserves the `§23.5.6` anchor required by ADRs and `docs/01-facts.md`.

### 23.5.7 BRD-Assembler (Assembly + Pre-Sync Gate)

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/generation-pipeline.md`](sub-projects/brd-adr-lifecycle/generation-pipeline.md) (§23.5.7). This stub preserves the `§23.5.7` anchor required by ADRs and `docs/01-facts.md`.

### 23.5.8 Multi-BRD Conflict Detection

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/generation-pipeline.md`](sub-projects/brd-adr-lifecycle/generation-pipeline.md) (§23.5.8). This stub preserves the `§23.5.8` anchor required by ADRs and `docs/01-facts.md`.

### 23.5.9 ADR Generation Flow

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/generation-pipeline.md`](sub-projects/brd-adr-lifecycle/generation-pipeline.md) (§23.5.9). This stub preserves the `§23.5.9` anchor required by ADRs and `docs/01-facts.md`.

## 23.6 Traceability Web

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/traceability-web.md`](sub-projects/brd-adr-lifecycle/traceability-web.md) (§23.6). This stub preserves the `§23.6` anchor required by ADRs and `docs/01-facts.md`.

### 23.6.1 Complete Relationship Model

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/traceability-web.md`](sub-projects/brd-adr-lifecycle/traceability-web.md) (§23.6.1). This stub preserves the `§23.6.1` anchor required by ADRs and `docs/01-facts.md`.

### 23.6.2 Code Graph Relation Edge Catalog

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/traceability-web.md`](sub-projects/brd-adr-lifecycle/traceability-web.md) (§23.6.2). This stub preserves the `§23.6.2` anchor required by ADRs and `docs/01-facts.md`.

### 23.6.3 Natural Language Query Examples

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/traceability-web.md`](sub-projects/brd-adr-lifecycle/traceability-web.md) (§23.6.3). This stub preserves the `§23.6.3` anchor required by ADRs and `docs/01-facts.md`.

## 23.7 BRD/ADR as Compute Spec Types

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/compute-spec-integration.md`](sub-projects/brd-adr-lifecycle/compute-spec-integration.md) (§23.7). This stub preserves the `§23.7` anchor required by ADRs and `docs/01-facts.md`.

### 23.7.1 Inherited Capability Matrix

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/compute-spec-integration.md`](sub-projects/brd-adr-lifecycle/compute-spec-integration.md) (§23.7.1). This stub preserves the `§23.7.1` anchor required by ADRs and `docs/01-facts.md`.

### 23.7.2 CI/CD Validation Pipeline

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/compute-spec-integration.md`](sub-projects/brd-adr-lifecycle/compute-spec-integration.md) (§23.7.2). This stub preserves the `§23.7.2` anchor required by ADRs and `docs/01-facts.md`.

## 23.8 Integration with External Tools

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/external-integration.md`](sub-projects/brd-adr-lifecycle/external-integration.md) (§23.8). This stub preserves the `§23.8` anchor required by ADRs and `docs/01-facts.md`.

### 23.8.1 Integration Architecture Overview

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/external-integration.md`](sub-projects/brd-adr-lifecycle/external-integration.md) (§23.8.1). This stub preserves the `§23.8.1` anchor required by ADRs and `docs/01-facts.md`.

### 23.8.2 New MCP Servers

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/external-integration.md`](sub-projects/brd-adr-lifecycle/external-integration.md) (§23.8.2). This stub preserves the `§23.8.2` anchor required by ADRs and `docs/01-facts.md`.

### 23.8.3 Import Capability (Legacy Migration)

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/external-integration.md`](sub-projects/brd-adr-lifecycle/external-integration.md) (§23.8.3). This stub preserves the `§23.8.3` anchor required by ADRs and `docs/01-facts.md`.

## 23.9 New Skills (New Skill Definitions)

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/external-integration.md`](sub-projects/brd-adr-lifecycle/external-integration.md) (§23.9). This stub preserves the `§23.9` anchor required by ADRs and `docs/01-facts.md`.

## 23.10 Summary: BRD/ADR Architecture Decisions

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/external-integration.md`](sub-projects/brd-adr-lifecycle/external-integration.md) (§23.10). This stub preserves the `§23.10` anchor required by ADRs and `docs/01-facts.md`.

## 23.11 Experience Typology Tree

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/quality-and-typology.md`](sub-projects/brd-adr-lifecycle/quality-and-typology.md) (§23.11). This stub preserves the `§23.11` anchor required by ADRs and `docs/01-facts.md`.

### 23.11.1 Concept

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/quality-and-typology.md`](sub-projects/brd-adr-lifecycle/quality-and-typology.md) (§23.11.1). This stub preserves the `§23.11.1` anchor required by ADRs and `docs/01-facts.md`.

### 23.11.2 Three-Layer Progressive Construction

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/quality-and-typology.md`](sub-projects/brd-adr-lifecycle/quality-and-typology.md) (§23.11.2). This stub preserves the `§23.11.2` anchor required by ADRs and `docs/01-facts.md`.

### 23.11.3 Storage

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/quality-and-typology.md`](sub-projects/brd-adr-lifecycle/quality-and-typology.md) (§23.11.3). This stub preserves the `§23.11.3` anchor required by ADRs and `docs/01-facts.md`.

### 23.11.4 Degradation Mechanism

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/quality-and-typology.md`](sub-projects/brd-adr-lifecycle/quality-and-typology.md) (§23.11.4). This stub preserves the `§23.11.4` anchor required by ADRs and `docs/01-facts.md`.

## 23.12 BRD Product Quality Assessment

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/quality-and-typology.md`](sub-projects/brd-adr-lifecycle/quality-and-typology.md) (§23.12). This stub preserves the `§23.12` anchor required by ADRs and `docs/01-facts.md`.

### 23.12.1 Distinction from Agent Trajectory Scoring

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/quality-and-typology.md`](sub-projects/brd-adr-lifecycle/quality-and-typology.md) (§23.12.1). This stub preserves the `§23.12.1` anchor required by ADRs and `docs/01-facts.md`.

### 23.12.2 Four-Dimension Human Reviewer Scoring

> **Migrated** to [`docs/sub-projects/brd-adr-lifecycle/quality-and-typology.md`](sub-projects/brd-adr-lifecycle/quality-and-typology.md) (§23.12.2). This stub preserves the `§23.12.2` anchor required by ADRs and `docs/01-facts.md`.

## 24. Operational Architecture

> **Migrated** to [`docs/sub-projects/platform-core/operational-architecture.md`](sub-projects/platform-core/operational-architecture.md) (§24). This stub preserves the `§24` anchor required by ADRs and `docs/01-facts.md`.

### 24.1 Backup & Recovery

> **Migrated** to [`docs/sub-projects/platform-core/operational-architecture.md`](sub-projects/platform-core/operational-architecture.md) (§24.1). This stub preserves the `§24.1` anchor required by ADRs and `docs/01-facts.md`.

### 24.2 Disaster Recovery

> **Migrated** to [`docs/sub-projects/platform-core/operational-architecture.md`](sub-projects/platform-core/operational-architecture.md) (§24.2). This stub preserves the `§24.2` anchor required by ADRs and `docs/01-facts.md`.

### 24.3 Schema Migration Strategy

> **Migrated** to [`docs/sub-projects/platform-core/operational-architecture.md`](sub-projects/platform-core/operational-architecture.md) (§24.3). This stub preserves the `§24.3` anchor required by ADRs and `docs/01-facts.md`.

### 24.4 Data Retention Policies

> **Migrated** to [`docs/sub-projects/platform-core/operational-architecture.md`](sub-projects/platform-core/operational-architecture.md) (§24.4). This stub preserves the `§24.4` anchor required by ADRs and `docs/01-facts.md`.

### 24.5 Secrets Rotation

> **Migrated** to [`docs/sub-projects/platform-core/operational-architecture.md`](sub-projects/platform-core/operational-architecture.md) (§24.5). This stub preserves the `§24.5` anchor required by ADRs and `docs/01-facts.md`.

### 24.6 Platform Deployment Strategy

> **Migrated** to [`docs/sub-projects/platform-core/operational-architecture.md`](sub-projects/platform-core/operational-architecture.md) (§24.6). This stub preserves the `§24.6` anchor required by ADRs and `docs/01-facts.md`.

### 24.7 Capacity Planning Model

> **Migrated** to [`docs/sub-projects/platform-core/operational-architecture.md`](sub-projects/platform-core/operational-architecture.md) (§24.7). This stub preserves the `§24.7` anchor required by ADRs and `docs/01-facts.md`.

## 25. Compliance Architecture

> **Migrated** to [`docs/sub-projects/platform-core/compliance-architecture.md`](sub-projects/platform-core/compliance-architecture.md) (§25). This stub preserves the `§25` anchor required by ADRs and `docs/01-facts.md`.

### 25.1 Data Subject Access Request (DSAR)

> **Migrated** to [`docs/sub-projects/platform-core/compliance-architecture.md`](sub-projects/platform-core/compliance-architecture.md) (§25.1). This stub preserves the `§25.1` anchor required by ADRs and `docs/01-facts.md`.

### 25.2 Right to Erasure

> **Migrated** to [`docs/sub-projects/platform-core/compliance-architecture.md`](sub-projects/platform-core/compliance-architecture.md) (§25.2). This stub preserves the `§25.2` anchor required by ADRs and `docs/01-facts.md`.

### 25.3 Data Residency

> **Migrated** to [`docs/sub-projects/platform-core/compliance-architecture.md`](sub-projects/platform-core/compliance-architecture.md) (§25.3). This stub preserves the `§25.3` anchor required by ADRs and `docs/01-facts.md`.

### 25.4 Consent Management

> **Migrated** to [`docs/sub-projects/platform-core/compliance-architecture.md`](sub-projects/platform-core/compliance-architecture.md) (§25.4). This stub preserves the `§25.4` anchor required by ADRs and `docs/01-facts.md`.

### 25.5 Breach Notification

> **Migrated** to [`docs/sub-projects/platform-core/compliance-architecture.md`](sub-projects/platform-core/compliance-architecture.md) (§25.5). This stub preserves the `§25.5` anchor required by ADRs and `docs/01-facts.md`.

### 25.6 API Versioning Strategy

> **Migrated** to [`docs/sub-projects/platform-core/compliance-architecture.md`](sub-projects/platform-core/compliance-architecture.md) (§25.6). This stub preserves the `§25.6` anchor required by ADRs and `docs/01-facts.md`.

---

*Last updated: 2026-08-04 | Version: 2.0 | Detailed module design migrated to [`docs/sub-projects/`](sub-projects/) — this file retains §1, §2, §13, §14, §17 in full + §N anchor stubs for all migrated sections*
