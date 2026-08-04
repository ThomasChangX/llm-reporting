# Cross-Cutting Layer

> **Origin**: §11 of [`docs/03-architecture.md`](../../03-architecture.md) | **Sub-project**: [platform-core](README.md)

## Purpose

The Cross-Cutting Layer is the set of platform-wide concerns that every plane and sub-project depends upon but that no single plane owns. It encompasses security and encryption (§11.1), entitlement enforcement combining RBAC and ABAC (§11.2), version control of artifacts (§11.3), observability (§11.4), and the additional cross-cutting components catalogued in §11.5 — Audit Trail, Tenant Isolation, Integration Framework, File Export, Support & Ticket, Jira/Rally Integration, BRD & ADR, and DevOps. These capabilities are exposed as shared services so that the Design, Freeze, and Runtime planes (and all sub-projects) can invoke them uniformly rather than re-implementing them.

## Boundaries

**In-scope:**
- Encryption in transit and at rest, key hierarchy, secrets management, and dynamic data masking.
- RBAC + ABAC permission evaluation, delegation, and cross-tenant access mediation.
- Version control of Compute Specs, KB entries, Formats, and Design Artifacts (branching, commit, PR, immutable history).
- Observability pillars: metrics, traces, logs, alerting, dashboards (detailed in [observability.md](observability.md)).
- Additional components: Audit Trail, Tenant Isolation, Integration Framework, File Export, Support & Ticket, Jira/Rally Integration, BRD & ADR, DevOps.

**Delegated (not re-specified here):**
- **Observability implementation detail** → [observability.md](observability.md) (§8 Log System + §12.6 Observation Engine).
- **Tenant isolation enforcement mechanics** (Data Masking, Row-Level Security) are applied at query time by the Query Rewriter — see [docs/sub-projects/query-serving/](../query-serving/) and §5 of the architecture.
- **Auth Gateway / API Gateway identity plumbing** → covered by the platform-core [README.md](README.md) interface contract and §2.1 Code Graph RBAC filter.
- **Compliance obligations** (DSAR, erasure, residency, consent) → [compliance-architecture.md](compliance-architecture.md).

**Upstream/downstream neighbors:**
- Every sub-project is a *consumer* of this layer (auth context, RBAC, audit, tenant isolation, observability instrumentation).
- Upstream feeders: API Gateway supplies principal/tenant context; Workbench and Workflow Executor emit audit events and metrics; Git (GitHub/GitLab) is the backing store for version-controlled artifacts.

## Interfaces

### §11.1 Security & Encryption

| Control | Specification |
| --- | --- |
| **Encryption in Transit** | TLS 1.3 mandatory for all network communication (API Gateway ↔ Services, Service ↔ DB, Service ↔ Object Store). mTLS for inter-service communication within the cluster. Certificate rotation via automated PKI (Vault or cert-manager). |
| **Encryption at Rest** | AES-256-GCM for all persistent storage. KMS (AWS KMS / HashiCorp Vault / cloud-agnostic) manages keys with automatic annual rotation. Per-tenant customer-managed key (CMK) option for regulated industries. |
| **Key Hierarchy** | Master Key (KMS) → Data Encryption Keys (DEK, per-store) → Row-Level Keys (optional, per-tenant). DEKs are encrypted by the Master Key and stored alongside data; never plaintext on disk. |
| **Secrets Management** | All credentials, API keys, and connection strings stored in HashiCorp Vault (or cloud-native equivalent). Sandbox accesses secrets via `/secrets/` tmpfs volume — never in environment variables or source code. |
| **Data Masking** | Dynamic masking at query time (Query Rewriter, Section 5). PII/Sensitive columns tagged in Data Catalog; masking policy (redact/hash/tokenize/partial) applied based on caller role. |

### §11.2 Entitlement (RBAC + ABAC)

| Dimension | Mechanism |
| --- | --- |
| **Role-Based (RBAC)** | Predefined roles: Viewer, Analyst, Developer, DataOwner, Admin. Each role maps to a set of permitted operations on scoped resources. |
| **Attribute-Based (ABAC)** | Row-level security: tenant_id, department, region. Column-level security: PII flag, sensitivity tier. Policy evaluated at query time by Query Rewriter. |
| **Permission Model** | `(subject, action, resource, conditions)` tuples. Evaluated per-request. Cached in Redis with 60s TTL; invalidation on role change. |
| **Delegation** | Data Owners can delegate temporary access (time-bound, scope-limited) to specific users. All delegations logged to Audit Trail. |
| **Cross-Tenant** | Cross-tenant access requires explicit opt-in from both tenant Data Owners. Mediated through the Code Graph's RBAC filter (Section 2.1). |

### §11.5 Additional Cross-Cutting Components

| Component | Responsibility |
| --- | --- |
| **Audit Trail** | Immutable log of all operations, exportable |
| **Tenant Isolation** | Multi-tenant three-level isolation; Data Masking + Row-Level Security |
| **Integration Framework** | Five levels: File→DB→API→Message→Custom Plugin; unified DataSource Interface |
| **File Export** | PDF/Excel/CSV/JSON/Parquet; Local/S3/Email/API |
| **Support & Ticket** | L1 self-service → L2 ticket → L3 dev escalation; built-in + external JSM/ServiceNow |
| **Jira/Rally Integration** | BRD→Epic→Story→Spec→PR→Deploy full traceability chain |
| **BRD & ADR** | Structured requirements documents + architecture decision records, bidirectionally linked to Workflows |
| **DevOps** | CI/CD Pipeline, environment management (Dev/Staging/Prod), auto rollback, monitoring & alerting |

### Platform-facing contract (shared by all sub-projects)

| Interface | Consumer | Contract |
|-----------|----------|----------|
| `auth.authenticate(token) → principal` | All sub-projects | Validates OAuth/Kerberos/SAML → returns tenant + role context |
| `entitlement.check(principal, resource, action) → bool` | All sub-projects | RBAC + ABAC evaluation (cached in Redis, 60s TTL) |
| `audit.log(principal, action, resource, result)` | All sub-projects | Immutable append to Audit Trail |
| `secrets.get(path) → value` | Sandboxes, services | Reads from Vault via `/secrets/` tmpfs |

## Dependencies

- **HashiCorp Vault** (or cloud-native equivalent) — secrets, dynamic DB credentials, PKI, Transit encryption.
- **KMS** (AWS KMS / Vault Transit) — master key management and automatic rotation.
- **Redis** — entitlement decision cache (60s TTL, role-change invalidation).
- **cert-manager** (Kubernetes) — TLS certificate lifecycle; or cloud PKI.
- **Git** (GitHub/GitLab) — backing store for version-controlled artifacts.
- **Query Rewriter** (query-serving sub-project, §5) — enforces dynamic data masking and row/column-level ABAC at query time.
- **Code Graph** (§2.1) — mediates cross-tenant RBAC filtering.
- External integrations: JSM/ServiceNow (support), Jira/Rally (traceability).

## Data Model

The cross-cutting layer does not own a primary data store, but it writes to and reads from the following entities (canonical schemas live in the relevant sub-project documents):

- **Permission tuples** — `(subject, action, resource, conditions)`; cached projection in Redis.
- **Audit Trail records** — immutable; full schema and retention in [operational-architecture.md](operational-architecture.md) (§24.4) and §8 Log System. Exportable.
- **Version-controlled artifacts** — Compute Specs (YAML), KB entries (Business Glossary, Data Catalog, Mapping Registry, Workflow Templates), Formats, Design Artifacts. Stored in Git.
- **Delegation records** — time-bound, scope-limited grants; written to Audit Trail.
- **Data Catalog tags** — PII/Sensitivity flags that drive masking policy (consumed by Query Rewriter).

## Failure Modes & Recovery

| Failure | Impact | Recovery |
| --- | --- | --- |
| Vault outage | New secret leases and dynamic DB credentials fail to issue; existing leases continue until expiry (7d DB lease). | Vault HA failover; pre-fetched secrets in `/secrets/` tmpfs keep running sandboxes alive. See [operational-architecture.md](operational-architecture.md) §24.5 for secrets rotation mid-execution handling. |
| KMS unreachable | New DEKs cannot be unwrapped; existing data still readable (DEK cached encrypted). | KMS is regional HA; on key compromise, rotate via AWS KMS / Vault Transit (old key version retained for decryption). |
| Redis (entitlement cache) outage | Per-request evaluation falls through to source-of-truth (slower); no permission bypass. | Cache rebuild on restore; TTL 60s bounds staleness. |
| cert-manager / PKI failure | Certificate renewal stalls; existing certs valid until expiry. | cert-manager retry; alert fired on cert expiry <30d (§11.4 Alerting). |
| Git provider outage | Artifact commits/PRs blocked; reads via existing clones continue. | Git is inherently distributed — re-clone from remotes (RPO <5min, see §12.3 / [operational-architecture.md](operational-architecture.md) §24.1). |

Security incident response and breach handling are cross-referenced in [docs/security/threat-model.md](../../security/threat-model.md) and [compliance-architecture.md](compliance-architecture.md) §25.5.

## Non-Functional Requirements

- **Security**: TLS 1.3 mandatory; AES-256-GCM at rest; annual KMS key rotation; 30d cert-expiry alert. See [docs/security/threat-model.md](../../security/threat-model.md) (STRIDE + OWASP LLM).
- **Performance**: Entitlement evaluation cached (Redis 60s TTL); per-request overhead bounded by cache hit. Masking applied inline at Query Rewriter.
- **SLO/SLI**: Audit write availability and audit query latency are tracked as part of platform SLOs — see [docs/operations/slo-sli.md](../../operations/slo-sli.md).
- **Scalability**: Cross-tenant RBAC and masking must scale to multi-tenant SaaS (see Tenant Isolation, three-level isolation model).
- **Auditability**: Git history append-only (no force-push to `main`); Audit Trail immutable, 7-year retention (§24.4).

## Key Flows

### §11.3 Version Control — Branch & PR Flow

| Aspect | Specification |
| --- | --- |
| **Artifacts Under VC** | Compute Specs (YAML), KB entries (Business Glossary, Data Catalog, Mapping Registry, Workflow Templates), Formats, Design Artifacts. All stored in Git (GitHub/GitLab). |
| **Branch Strategy** | `main` = production; feature branches per Workbench session; `freeze/<artifact-id>` for Freeze Pipeline reviews; `hotfix/` for emergency changes. |
| **Commit Convention** | Structured commits: `type(scope): description [BRD-123] [JIRA-456]`. Types: `spec`, `kb`, `format`, `freeze`, `rollback`. |
| **PR Workflow** | All changes via PR. Required: (a) CI passes (validation + test), (b) at least one peer review, (c) Business Approver for KB changes, (d) Data Owner for Data Catalog changes. |
| **Immutable History** | Git history is append-only (no force-push to `main`). All merges are squash-merge to maintain a linear, auditable history. |

### §11.4 Observability — Alerts and Dashboards

Alertmanager rules: (a) Workflow failure rate >1%, (b) p95 latency >2× baseline, (c) Sandbox starvation, (d) KB sync lag >60s, (e) encryption cert expiry <30d. Alerts route to Incident Manager. Dashboards: per-tenant operational dashboard (health, cost, usage), per-workflow performance dashboard, and executive summary dashboard (SLI/SLO compliance). Full observability pillar detail (Metrics/Traces/Logs) is in [observability.md](observability.md).

### End-to-end traceability chain (Jira/Rally)

`BRD → Epic → Story → Spec → PR → Deploy` — every artifact is bidirectionally linked, supporting the structured commits (`[BRD-123] [JIRA-456]`) and the BRD & ADR component.

## Design References

- **Original section**: §11 (§11.1–§11.5) of [`docs/03-architecture.md`](../../03-architecture.md).
- **Related observability**: [observability.md](observability.md) (§8, §12.6).
- **Related operations**: [operational-architecture.md](operational-architecture.md) (§24) — backup, retention, secrets rotation, deployment.
- **Related compliance**: [compliance-architecture.md](compliance-architecture.md) (§25) — DSAR, erasure, residency.
- **ADRs** ([index](../../adr-index.md)): [ADR-0005 Four-Layer Architecture](../../../adr/0005-four-layer-architecture.md), [ADR-0010 BRD/ADR as First-Class Entities](../../../adr/0010-brd-adr-first-class.md), [ADR-0013 KB Storage Strategy](../../../adr/0013-kb-storage-strategy.md).
- **Glossary** ([../../glossary.md](../../glossary.md)): Compute Spec, Cross-Environment Read-Only Mode, Freeze Pipeline, Production Environment.
- **External procedures**: [docs/security/threat-model.md](../../security/threat-model.md), [docs/operations/slo-sli.md](../../operations/slo-sli.md), [docs/operations/backup-dr.md](../../operations/backup-dr.md).
