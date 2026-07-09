# C4 Model Diagrams

> Extracted from [docs/03-architecture.md §15](../03-architecture.md) | Sync Date: 2026-07-04
>
> C4 Model is a layered approach to software architecture visualization. This section contains System Context, Container, and Component three-level architecture diagrams.

## 15.1 System Context Diagram (System Context View)

```
                                          ┌─────────────────────────────┐
                                          │     Identity Provider        │
                                          │   (SSO/OAuth 2.0/OIDC)       │
                                          │   Keycloak / Okta / Entra ID │
                                          └──────────────┬──────────────┘
                                                         │ SAML/OIDC
                                                         │ (TLS 1.3)
  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐│  ┌──────────┐  ┌──────────────┐
  │  Viewer  │  │ Analyst  │  │Developer │  │  Admin   ││  │  Data    │  │   External   │
  │ (Read-only)│  │ (Design)  │  │ (Develop) │  │ (Ops)     ││  │  Owner   │  │   Auditor    │
  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘│  └────┬─────┘  └──────┬───────┘
       │             │             │             │       │       │               │
       └─────────────┼─────────────┼─────────────┼───────┼───────┼───────────────┘
                     │             │             │       │       │
                     │   HTTPS/TLS 1.3 (WebSockets for real-time)  │
                     │             │             │       │       │
                     └─────────────┼─────────────┼───────┼───────┘
                                   │             │       │
                                   ▼             ▼       ▼
                          ┌────────────────────────────────────────┐
                          │                                        │
                          │      LLM Reporting BI Platform         │
                          │      [Software System]                 │
                          │                                        │
                          │   AI-assisted reporting, ETL,          │
                          │   adjustment & reconciliation          │
                          │   with enterprise SDLC integration     │
                          │                                        │
                          └───────┬──────┬──────┬──────┬───────────┘
                                  │      │      │      │
              ┌───────────────────┼──────┼──────┼──────┼───────────────────┐
              │                   │      │      │      │                   │
              ▼                   ▼      ▼      ▼      ▼                   ▼
    ┌─────────────────┐  ┌──────────┐ ┌──────┐ ┌──────────┐  ┌─────────────────────┐
    │ Enterprise ERP   │  │  Data    │ │Email │ │   Git    │  │  Jira / ServiceNow  │
    │ (SAP/Oracle)     │  │Warehouse │ │Server│ │ Platform │  │  (REST API/Webhook) │
    │                  │  │(Snowflake│ │(SMTP)│ │(GitHub/  │  │                     │
    │ JDBC/ODBC/REST   │  │ BigQuery │ │      │ │ GitLab)  │  │ BRD→Epic→Story→PR  │
    │ over TLS         │  │ Redshift)│ │ TLS  │ │ SSH/HTTPS│  │ traceability chain  │
    └─────────────────┘  └──────────┘ └──────┘ └──────────┘  └─────────────────────┘
              │                   │
              ▼                   ▼
    ┌─────────────────┐  ┌──────────────────────────────────────────────┐
    │  Cloud KMS      │  │         Object Store (S3 / MinIO)             │
    │  (AWS KMS /     │  │  Warm/Cold Logs, Attachments, LLM Transcripts│
    │   Vault Transit) │  │  S3 API over TLS / IAM Role                  │
    │  Key management │  └──────────────────────────────────────────────┘
    │  + cert rotation │
    └─────────────────┘  ┌──────────────────────────────────────────────┐
                         │      Slack / Teams (Notification Sink)       │
                         │      Incoming Webhook / Bot API over TLS     │
                         └──────────────────────────────────────────────┘
```

**Relationship Description**:

| External System | Protocol | Direction | Description |
|----------|----------|----------|------|
| **Enterprise ERP** (SAP/Oracle EBS) | JDBC/ODBC over TLS 1.3, REST API | Bi-directional | Runtime Executor pulls source data; `data_writer` Job writes back adjustment vouchers |
| **Data Warehouse** (Snowflake/BigQuery/Redshift) | Native Driver over TLS 1.3 | Read-heavy | Runtime Executor pulls analytics data; Query Rewriter injects row-level security predicates |
| **Email Server** (SMTP) | SMTP over TLS (port 587), IMAP (port 993) | Inbound + Outbound | Inbound: KB email ingestion (`kb@tenant.system.com`); Outbound: Notification Service sends reports/alerts |
| **Identity Provider** (Keycloak/Okta/Entra ID) | SAML 2.0 / OIDC over TLS 1.3 | Read | Auth Gateway validates identity, refreshes tokens, syncs roles |
| **Git Platform** (GitHub/GitLab) | SSH (git transport), HTTPS REST API | Bi-directional | Workbench branch management, Freeze PR, Spec/KB version control |
| **Jira/ServiceNow** | REST API over TLS 1.3 | Bi-directional | BRD→Epic→Story→Spec→PR traceability; Incident auto-creation/sync |
| **Cloud KMS** (AWS KMS/Vault Transit) | gRPC / REST over mTLS | Read | Key encryption/decryption/rotation; envelope encryption DEK management |
| **Object Store** (S3/MinIO) | S3 API over TLS / IAM Role | Write + Read | Log archiving, attachment storage, sandbox intermediate data transfer |
| **Slack/Teams** | Incoming Webhook / Bot API over TLS | Outbound | Notification delivery, approval reminders, incident alerts |

### 15.2 Container Diagram (Container View)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              LLM Reporting BI Platform                                │
│                                                                                       │
│  ┌──────────────┐     ┌───────────────────┐     ┌───────────────────────────────┐    │
│  │  Web SPA     │────▶│  API Gateway      │────▶│  Auth Service                 │    │
│  │  (React)     │     │  (Kong/Envoy)     │     │  (OAuth2/OIDC Gateway)        │    │
│  │              │     │  Rate Limit       │     │  Token Validation │ Role Sync │    │
│  │ HTTPS/WSS   │     │  Auth Filter      │     │  [PostgreSQL: sessions]       │    │
│  │              │     │  Tenant Router    │     └───────────────────────────────┘    │
│  └──────────────┘     │  Circuit Breaker  │                                           │
│                        └──────┬────┬──────┘                                           │
│                               │    │                                                  │
│              ┌────────────────┼────┼────────────────────────────────┐                 │
│              │                │    │                                │                 │
│              ▼                ▼    ▼                                ▼                 │
│  ┌────────────────────┐ ┌──────────────────────┐ ┌──────────────────────────────┐   │
│  │ Design Plane Svc   │ │ Freeze Bridge Svc    │ │ Runtime Executor Svc         │   │
│  │ (Python/FastAPI)   │ │ (Python/FastAPI)     │ │ (Go/Rust — Zero AI Side-Effects)       │   │
│  │ ┌────────────────┐ │ │ ┌──────────────────┐ │ │ ┌──────────────────────────┐ │   │
│  │ │Conversation UI │ │ │ │Spec Refinement   │ │ │ │Scheduler (cron/event/    │ │   │
│  │ │Intent Parser   │ │ │ │Validation Engine │ │ │ │ webhook/manual)          │ │   │
│  │ │Plan Generator  │ │ │ │Test Runner       │ │ │ │Workflow Executor         │ │   │
│  │ │Artifact Builder│ │ │ │Release Manager   │ │ │ │Query Rewriter (RLS/DM)   │ │   │
│  │ │AI Copilot      │ │ │ │CI/CD Integration │ │ │ │Data Connector Adapter    │ │   │
│  │ └────────────────┘ │ │ └──────────────────┘ │ │ │Output Renderer           │ │   │
│  │ REST/gRPC         │ │ REST/gRPC            │ │ │Incident Manager          │ │   │
│  └────────┬───────────┘ └──────────┬───────────┘ │ └──────────────────────────┘ │   │
│           │                        │              │ gRPC                         │   │
│           └────────────┬───────────┘              └──────────┬───────────────────┘   │
│                        │                                     │                       │
│                        ▼                                     ▼                       │
│              ┌──────────────────────────────────────────────────────────────┐        │
│              │              KNOWLEDGE BASE (Data Tier)                       │        │
│              │                                                               │        │
│              │  [PostgreSQL]        [Milvus/pgvector]     [Neo4j (Post-MVP)]│        │
│              │  Source of Truth     Vector Embeddings      Graph Relations   │        │
│              │  ACID, Versioned     ▶ CDC sync (30s lag)   ▶ CDC sync (30s)  │        │
│              │                                                               │        │
│              │  [Elasticsearch]     [Redis Sentinel]       [S3/MinIO]        │        │
│              │  Hot Logs (7d)       Cache + Session        Object Store      │        │
│              │                      Code Graph Hot Subg.   Warm/Cold/Attach. │        │
│              └──────────────────────────────────────────────────────────────┘        │
│                        │                                                              │
│              ┌─────────┴──────────┐                                                   │
│              ▼                    ▼                                                   │
│  ┌────────────────────┐  ┌──────────────────────────────┐                            │
│  │ Code Graph Svc     │  │ Notification Svc              │                            │
│  │ (GraphQL/gRPC)     │  │ (Kafka Consumer + Dispatch)   │                            │
│  │ ┌────────────────┐ │  │ ┌──────────────────────────┐ │                            │
│  │ │Impact Analysis │ │  │ │Priority Router           │ │                            │
│  │ │Lineage Tracing │ │  │ │Template Engine (Jinja2)  │ │                            │
│  │ │RBAC Filter     │ │  │ │Suppression Engine        │ │                            │
│  │ │Cross-graph Link│ │  │ │Channel Dispatcher        │ │                            │
│  │ └────────────────┘ │  │ │(Email/Slack/Teams/SMS)   │ │                            │
│  │ [Neo4j (Post-MVP)] │  │ └──────────────────────────┘ │                            │
│  └────────────────────┘  └──────────────────────────────┘                            │
│                                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐                   │
│  │               Log Ingestion Svc (Kafka → Fluentd → ES + S3)    │                   │
│  │   Structured Event Log │ Execution Trace │ LLM Interaction Log │                   │
│  └────────────────────────────────────────────────────────────────┘                   │
│                                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐                   │
│  │               Message Bus (Apache Kafka / Redpanda)             │                   │
│  │   Topics: events.workflow.* │ events.freeze.* │ events.kb.*    │                   │
│  │           events.incident.* │ notifications.* │ audit.*        │                   │
│  └────────────────────────────────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

**Inter-Container Communication Protocol Matrix**:

| Producer → Consumer | Protocol | Pattern | Notes |
|---------------------|----------|---------|-------|
| Web SPA → API Gateway | HTTPS (TLS 1.3), WSS | Request/Response | JWT Bearer Token in Authorization header |
| API Gateway → All Services | HTTPS (TLS 1.3) → Service (mTLS inside mesh) | Request/Response | Kong routes by path prefix; Envoy sidecar enforces mTLS |
| Design Plane ↔ Freeze Bridge | gRPC (mTLS) | Request/Response | Design Artifact handoff; Freeze status streaming |
| Design Plane → KB (Vector) | gRPC (mTLS) | Request/Response | Milvus SDK for semantic search |
| Freeze Bridge → KB (Relational) | PostgreSQL wire protocol (TLS) | Request/Response | SQL via parameterized queries |
| Runtime Executor → KB (Graph) | Bolt protocol (TLS) | Request/Response | Cypher queries via Neo4j driver (Post-MVP; MVP uses PG-only per ADR-0013) |
| All Services → Kafka | Kafka native protocol (mTLS) | Publish/Async | Schema Registry enforces Avro schemas |
| Kafka → Log Ingestion Svc | Kafka Consumer Group | Stream Processing | Fluentd/Fluent Bit consumers |
| Kafka → Notification Svc | Kafka Consumer Group | Stream Processing | At-least-once delivery; DLQ for failures |
| Notification Svc → External (Email/Slack) | SMTP/TLS, HTTPS Webhook | Async Dispatch | Channel-specific retry policies |
| Runtime Executor → Data Sources | JDBC/ODBC, REST, S3 API over TLS | Request/Response | Per-connector connection pooling |

---

> 📄 Source Location:[../03-architecture.md §15](../03-architecture.md)
