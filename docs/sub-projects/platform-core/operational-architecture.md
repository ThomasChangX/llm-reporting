# Operational Architecture

> **Origin**: §24 of [`docs/03-architecture.md`](../../03-architecture.md) | **Sub-project**: [platform-core](README.md)

## Purpose

The Operational Architecture defines how the platform is run: backup and recovery (§24.1), disaster recovery (§24.2), schema migration strategy (§24.3), data retention policies (§24.4), secrets rotation (§24.5), platform deployment strategy (§24.6), and the capacity planning model (§24.7). It is grounded in NIST SP 800-34, the AWS Well-Architected Framework (Reliability Pillar), and the Google SRE Workbook, and it operationalizes the per-store backup matrix defined in [domain-services.md](domain-services.md) §12.3 into platform-level RPO/RTO tiers, failover procedures, and runbooks. This module is the platform-level complement to the per-store DR matrix and to the cross-cutting DevOps component (§11.5).

## Boundaries

**In-scope:**
- RPO/RTO matrix and backup schedule by data tier T0–T3 (§24.1).
- Multi-region active-passive DR architecture and failover procedure (§24.2).
- Schema migration tooling policy (Flyway / Alembic), rollback, backward compatibility, and breaking-change handling (§24.3).
- Data retention policies across hot/warm/cold tiers per entity (§24.4).
- Secrets rotation periods, methods, and mid-execution handling (§24.5).
- Platform deployment strategies (Blue-Green, Rolling, Canary, Recreate) with rollback triggers (§24.6).
- Capacity planning model and scaling triggers (§24.7).

**Delegated / out-of-scope:**
- **Per-store backup methods and component-level RPO/RTO** → [domain-services.md](domain-services.md) §12.3 (this document holds the data-tier-level RPO/RTO matrix).
- **Workflow-specific canary gating** → §4.2 of the architecture (referenced by §24.6).
- **Compliance obligations** (DSAR, erasure, residency) → [compliance-architecture.md](compliance-architecture.md) §25.
- **Observability/alerting details** → [observability.md](observability.md).

**Upstream/downstream neighbors:**
- All data stores (PostgreSQL, Neo4j, Milvus, Elasticsearch, Redis, S3) and infra (Vault, K8s, Route53, cert-manager) are subjects of these procedures.
- Downstream consumers: Incident Commander (failover decisions), StatusPage (comms), CI/CD pipeline (deployment gates), and capacity planners.

## Interfaces

### §24.1 Backup & Recovery — RPO/RTO Matrix (by data tier)

| Data Tier | RPO | RTO | Method |
| --- | --- | --- | --- |
| T0 (Public) | 24h | 4h | pg_dump → S3 daily |
| T1 (Internal) | 1h | 1h | WAL-G continuous + PITR |
| T2 (Confidential) | 15min | 30min | WAL-G + Streaming Replication (sync) |
| T3 (Restricted) | 5min | 15min | WAL-G + Sync Replication + Cross-Region Async Replica |

**Backup Schedule**: PostgreSQL (WAL-G PITR, daily full, 30d retention), Neo4j (neo4j-admin daily, 30d), Milvus (daily snapshot, 14d), Elasticsearch (daily snapshot, 7d), Redis (BGSAVE hourly, 7d), S3 (Cross-Region Replication, continuous). All backups encrypted AES-256 (SSE-KMS).

### §24.3 Schema Migration Strategy — policy

| Aspect | Policy |
| --- | --- |
| **Migration Format** | Versioned SQL (`V{YYYYMMDDHHMM}__description.sql`) or Python (Alembic) |
| **Naming** | Timestamp-based (not sequential) to avoid merge conflicts |
| **Rollback** | Each `V` migration has corresponding `U` (undo) migration; tested in CI |
| **Backward Compatibility** | 3-version policy: migration must be compatible with N-1 and N-2 app versions |
| **CI/CD Gate** | Migration dry-run in CI (temp DB); failure blocks deploy |
| **Production Execution** | Blue-Green: migrate standby first, verify, then switchover |
| **Breaking Changes** | Require ADR + multi-step migration (add column → dual-write → migrate data → remove old column over 3 releases) |

### §24.4 Data Retention Policies

| Entity | Hot (PG/ES) | Warm (S3 Parquet) | Cold (Glacier) | Deletion Trigger |
| --- | --- | --- | --- | --- |
| `audit_log` | Current + 12 months | 12–84 months (7yr total) | 84+ months (optional) | 7yr + 90d grace → permanent delete |
| `workflow` | Active + 6 months deprecated | — | — | Tenant-initiated + 30d grace |
| `workflow_version` | All versions (co-located) | — | — | On parent workflow deletion |
| `kb_entry` | All confirmed + superseded | — | — | Superseded entries: 12 months; expired entries: on `expires_at` |
| `user_session` | Active only | — | — | On deactivation + 90d grace |
| `incident` | Open + 3 months resolved | 3–24 months | — | 24 months post-resolution |
| `LLM Interaction Log` | — | 90 days (S3 Parquet) | 7 years (compliance) | Per Cold retention policy |

### §24.5 Secrets Rotation

| Secret Type | Rotation Period | Method | Mid-Execution Handling |
| --- | --- | --- | --- |
| **DB Credentials** | 30 days | Vault Dynamic Secrets (lease: 7d, renewable) | Existing connections not terminated; new connections use new credentials |
| **LLM API Keys** | 90 days | Vault KV v2 + manual rotation (Provider portal) | Grace period: 24h overlap between old and new key |
| **TLS Certificates** | 90 days (Let's Encrypt) / 365 days (CA) | cert-manager (K8s) auto-renewal | N/A (certificate reload on change, no downtime) |
| **Encryption Keys (KMS)** | 365 days (automatic) | AWS KMS / Vault Transit auto-rotation | Old key version retained for decryption; new data encrypted with new key |
| **JWT Signing Keys** | 30 days | Vault PKI backend | Old keys retained for token validation (token max age: 7d) |

### §24.6 Platform Deployment Strategy

| Strategy | Scope | Rollback Trigger |
| --- | --- | --- |
| **Blue-Green Deployment** | Stateless services (Design Plane, Freeze Bridge, Query Service) | Error rate > baseline + 5% OR p95 latency > baseline × 2 |
| **Rolling Update** | Stateful services (KB API, Code Graph API) | Health check failure on >10% of new pods |
| **Canary (10%→50%→100%)** | Runtime Plane Executor, Query Rewriter (critical path) | DQ score decrease >1% OR workflow failure rate increase >0.1% |
| **Recreate** | Database schema changes, Kafka topic changes | Migration dry-run passed in CI (precondition) |

### §24.7 Capacity Planning Model

| Metric | Unit | Forecasting Method |
| --- | --- | --- |
| **Tenant Growth** | Tenants/month | Linear regression on pipeline + step-function for enterprise deals |
| **Data Volume Growth** | GB/month | Per-tenant avg × tenant count + per-enterprise-tenant bump (50GB) |
| **Query Throughput** | Queries/sec | NL queries ∝ active users; scheduled workflows ∝ tenant count |
| **LLM Token Consumption** | Tokens/month | Design Plane active hours × tokens/hr + Agent queries × tokens/query |
| **Storage Growth** | TB/month | Data Volume + Backup retention (30d × daily snapshots) + Log retention |

**Scaling Triggers**: Compute >70% node utilization → add 1 node; Storage >80% → add 1TB; LLM quota >80% → alert + budget review.

## Dependencies

- **PostgreSQL** (WAL-G PITR, streaming replication, sync replication, cross-region async replica).
- **Neo4j** (neo4j-admin daily dump), **Milvus** (daily snapshot), **Elasticsearch** (daily snapshot), **Redis** (BGSAVE), **S3** (Cross-Region Replication).
- **HashiCorp Vault** (Dynamic Secrets, KV v2, Transit, PKI backend) and **AWS KMS**.
- **Kubernetes** (cert-manager, Blue-Green/Rolling/Canary controllers, Health checks).
- **DNS / Route53** (failover cutover), **StatusPage** (comms).
- **Flyway** (Java/Spring stack) or **Alembic** (Python stack) for schema migration.
- **CI/CD pipeline** (migration dry-run gate; deployment gates).
- Frameworks: NIST SP 800-34, AWS Well-Architected (Reliability Pillar), Google SRE Workbook.

## Data Model

This module is procedural rather than entity-owning, but it governs the lifecycle of these entities (retention/deletion rules in §24.4):

- `audit_log` — 7-year total retention (Hot 12mo → Warm 12–84mo → Cold 84+mo optional) then 90d grace → permanent delete.
- `workflow` / `workflow_version` — active + 6 months deprecated; tenant-initiated deletion + 30d grace.
- `kb_entry` — superseded entries retained 12 months; expired entries deleted on `expires_at`.
- `user_session` — active only; deleted on deactivation + 90d grace.
- `incident` — 24 months post-resolution.
- **LLM Interaction Log** — Warm 90 days (S3 Parquet) → Cold 7 years (compliance).
- **Schema migrations** — versioned `V{YYYYMMDDHHMM}__description.sql` / Alembic, each with a paired `U` undo migration.
- **Backup artifacts** — encrypted AES-256 (SSE-KMS); retention per store (PG 30d, Neo4j 30d, Milvus 14d, ES 7d, Redis 7d).

## Failure Modes & Recovery

### §24.2 Disaster Recovery — Failover Procedure (Target RTO <60min)

**Multi-Region Active-Passive**: Primary Region (Active K8s Cluster, N× replicas) → DR Region (Passive, 1× minimal pods, scaled on failover). PostgreSQL Async Streaming to DR Standby. S3 Cross-Region Replication.

Failover steps:

1. **Detection** (Prometheus AlertManager, auto 5min)
2. **Decision** (Incident Commander, manual <15min)
3. **DNS Cutover** (Route53, <5min)
4. **DB Promotion** (<5min)
5. **Service Scale-Up** (<10min)
6. **Validation** (smoke tests, <15min)
7. **Communication** (StatusPage, <5min)

### Recovery Testing

| Failure / drill | Cadence |
| --- | --- |
| Backup Restore Drill (T2/T3) | Weekly |
| Backup Restore Drill (T0/T1) | Monthly |
| DR Failover Drill | Quarterly |
| Chaos Engineering | Post-MVP Phase 7+ |

### Operational failure handling summary

| Failure | Impact | Recovery |
| --- | --- | --- |
| Primary region outage | Platform unavailable in primary | DR failover procedure above (target RTO <60min); async PG streaming + S3 CRR bound data loss to RPO. |
| Bad schema migration | Schema incompatibility, app errors | Each `V` migration has `U` undo; CI dry-run gate blocks deploy; Blue-Green switchover after standby verification; breaking changes require ADR + multi-step migration over 3 releases. |
| Secret compromise | Credential/key exposure | Rotation per §24.5 (DB 30d, LLM 90d, TLS 90/365d, KMS 365d, JWT 30d); mid-execution handling preserves running connections. |
| Canary regression | DQ/latency/failure-rate regression | Rollback trigger fires (e.g., DQ score decrease >1%); canary halted before 100%. |
| Storage/compute exhaustion | Service degradation | Scaling triggers add nodes/storage; LLM quota >80% → alert + budget review. |

For per-store recovery procedure (PG WAL replay, ES snapshot restore, Neo4j dump + CDC replay, Vector re-index), see [domain-services.md](domain-services.md) §12.3.

## Non-Functional Requirements

- **RPO/RTO by tier** (§24.1): T0 24h/4h, T1 1h/1h, T2 15min/30min, T3 5min/15min.
- **DR target RTO** <60min (§24.2 failover procedure).
- **Backup encryption**: AES-256 (SSE-KMS) for all backups.
- **Schema compatibility**: 3-version backward compatibility (N-1, N-2).
- **Secrets rotation**: periods per §24.5 with documented mid-execution handling.
- **Deployment safety**: Blue-Green for stateless; Rolling for stateful; Canary for critical path; Recreate only for schema/topic changes with CI dry-run precondition.
- **Retention compliance**: audit_log 7yr; LLM Interaction Log Cold 7yr — see [compliance-architecture.md](compliance-architecture.md) for the governing regulations.
- **SLOs**: error budgets and SLO definitions in [docs/operations/slo-sli.md](../../operations/slo-sli.md); full backup/DR procedures in [docs/operations/backup-dr.md](../../operations/backup-dr.md).
- **Security**: threat model in [docs/security/threat-model.md](../../security/threat-model.md).

## Key Flows

### §24.2 DR failover (Detection → Decision → DNS Cutover → DB Promotion → Scale-Up → Validation → Communication)

Prometheus AlertManager auto-detects (5min) → Incident Commander decides (manual, <15min) → Route53 DNS cutover (<5min) → DB promotion (<5min) → service scale-up (<10min) → smoke-test validation (<15min) → StatusPage communication (<5min). Aggregate target RTO <60min.

### §24.3 Schema migration (CI → Blue-Green → Switchover)

Developer authors `V{ts}__desc.sql` (+ paired `U` undo) → CI dry-run in temp DB (failure blocks deploy) → Blue-Green: migrate standby first, verify → switchover. Breaking changes require an ADR and the 4-step multi-release migration (add column → dual-write → migrate data → remove old column).

### §24.6 Deployment (strategy selection by service class)

Stateless → Blue-Green (rollback on error rate > baseline+5% or p95 > 2× baseline). Stateful → Rolling (rollback on >10% new-pod health-check failure). Critical path → Canary 10%→50%→100% (rollback on DQ decrease >1% or failure-rate increase >0.1%). Schema/Kafka topic changes → Recreate (precondition: CI dry-run passed).

## Design References

- **Original section**: §24 (§24.1–§24.7) of [`docs/03-architecture.md`](../../03-architecture.md).
- **Foundational frameworks**: NIST SP 800-34, AWS Well-Architected Framework (Reliability Pillar), Google SRE Workbook.
- **Related platform-core docs**: [domain-services.md](domain-services.md) §12.3 (per-store backup matrix + recovery procedure), [cross-cutting-layer.md](cross-cutting-layer.md) §11.5 (DevOps component), [compliance-architecture.md](compliance-architecture.md) §25.
- **ADRs** ([index](../../adr-index.md)): [ADR-0009 Dual-Model Pricing Strategy](../../../adr/0009-dual-model-pricing.md) (LLM cost), [ADR-0020 Agent Cost Governance](../../../adr/0020-agent-cost-governance.md), [ADR-0017 Verified Path — Saga Semantics & Durable Execution](../../../adr/0017-verified-path-saga-semantics.md).
- **Glossary** ([../../glossary.md](../../glossary.md)): Compute Spec, Production Environment.
- **External procedures**: [docs/operations/backup-dr.md](../../operations/backup-dr.md), [docs/operations/slo-sli.md](../../operations/slo-sli.md), [docs/security/threat-model.md](../../security/threat-model.md).
