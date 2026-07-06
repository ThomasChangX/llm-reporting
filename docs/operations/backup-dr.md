# Backup & Disaster Recovery Strategy

> Extracted from [docs/03-architecture.md §24.1-§24.2](../03-architecture.md) | Sync Date: 2026-07-04
>
> Defined based on industry standards (NIST SP 800-34, AWS Well-Architected Framework — Reliability Pillar, Google SRE Workbook).

## 1. RPO / RTO Matrix

| Data Tier | Service | RPO (Recovery Point Objective) | RTO (Recovery Time Objective) | Backup Method | Validation |
|-----------|---------|-------------------------------|------------------------------|---------------|------------|
| **T0 (Public)** | Config, Templates | 24h | 4h | pg_dump → S3 (daily) | Restore to staging, integration test |
| **T1 (Internal)** | Workflow Specs, KB Metadata, Code Graph | 1h | 1h | WAL-G continuous archiving + PITR | Weekly restore drill to staging |
| **T2 (Confidential)** | Financial Data, Customer Lists, Payroll | 15min | 30min | WAL-G + Streaming Replication (sync to Standby) | Bi-weekly restore drill; DQ validation after restore |
| **T3 (Restricted)** | PII, Passwords, Tokens, Medical | 5min | 15min | WAL-G + Sync Replication + Cross-Region Async Replica | Weekly restore drill; encryption verification; access audit |

### RPO/RTO Rationale

- **T0**: Non-sensitive, can be regenerated from code. Minimal cost acceptable.
- **T1**: Business operations depend on workflow specs. 1h RPO balances cost vs. data loss risk.
- **T2**: Financial data subject to SOX compliance. 15min RPO meets audit requirements (FISCAM (Federal Information System Controls Audit Manual) §3.2).
- **T3**: PII subject to GDPR 72h breach notification. 5min RPO ensures minimal exposure. Cross-region replica for geographic redundancy.

## 2. Backup Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   BACKUP ARCHITECTURE                         │
│                                                              │
│  ┌──────────┐   WAL-G Continuous    ┌──────────────┐        │
│  │ PostgreSQL│──────────────────────►│  S3 (Primary │        │
│  │ Primary  │   (PITR base + WAL)   │   Region)    │        │
│  └────┬─────┘                       └──────┬───────┘        │
│       │                                    │                │
│       │ Streaming Replication              │ S3 Cross-Region│
│       │ (sync for T2/T3)                   │ Replication    │
│       ▼                                    ▼                │
│  ┌──────────┐                       ┌──────────────┐        │
│  │ PostgreSQL│                       │  S3 (DR       │        │
│  │ Standby  │                       │   Region)     │        │
│  │ (Same AZ)│                       └──────────────┘        │
│  └──────────┘                                               │
│                                                              │
│  │  ┌──────────┐   neo4j-admin      ┌──────────────┐           │
│  │  │  Neo4j   │───────────────────►│  S3 Backup    │           │
│  │  │ Cluster  │   (daily full)     │              │           │
│  │  │(Post-MVP)│                    │              │           │
│  │  └──────────┘                    └──────────────┘           │
│                                                              │
│  ┌──────────┐   S3 Sync          ┌──────────────┐           │
│  │ Milvus   │───────────────────►│  S3 (Vector   │           │
│  │ (Vector) │   (daily snapshot) │   Backups)    │           │
│  └──────────┘                    └──────────────┘           │
│                                                              │
│  ┌──────────┐   Elasticsearch    ┌──────────────┐           │
│  │   ES     │───────────────────►│  S3 (Snapshot │           │
│  │ (Hot 7d) │   (daily snapshot) │   Repository) │           │
│  └──────────┘                    └──────────────┘           │
│                                                              │
│  ┌──────────┐   BGSAVE           ┌──────────────┐           │
│  │  Redis   │───────────────────►│  S3 (RDB      │           │
│  │ Sentinel │   (hourly)         │   Dump)       │           │
│  └──────────┘                    └──────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

## 3. Backup Schedule

| Component | Method | Frequency | Retention | Encryption |
|-----------|--------|-----------|-----------|------------|
| PostgreSQL | WAL-G (PITR) | Continuous WAL + Daily Full | 30 days rolling | AES-256 (S3 SSE-KMS) |
| Neo4j (Post-MVP; MVP uses PG-only per ADR-0013) | neo4j-admin backup | Daily (off-peak) | 30 days | AES-256 |
| Milvus | Snapshot to S3 | Daily | 14 days | AES-256 |
| Elasticsearch | Snapshot Repository (S3) | Daily | 7 days (hot data only) | AES-256 |
| Redis | BGSAVE → S3 | Hourly | 7 days | AES-256 |
| S3 (Object Store) | Cross-Region Replication | Continuous | Per retention policy | AES-256 |

## 4. Disaster Recovery

### 4.1 Multi-Region Architecture

```
Primary Region (us-east-1 / cn-north-1)     DR Region (us-west-2 / cn-east-2)
┌──────────────────────────┐          ┌──────────────────────────┐
│  K8s Cluster (Active)    │  Async   │  K8s Cluster (Passive)   │
│  ┌────────────────────┐  │  Repl.   │  ┌────────────────────┐  │
│  │ All Services       │  │─────────►│  │ Minimal Pods (1×)   │  │
│  │ (N× replicas)      │  │          │  │ Scaled on failover  │  │
│  └────────────────────┘  │          │  └────────────────────┘  │
│                          │          │                          │
│  PostgreSQL (Primary)    │  Async   │  PostgreSQL (Standby)    │
│  Neo4j (Cluster, Post-MVP)│ Stream  │  Neo4j (Read Replica)   │
│  Redis (Sentinel)        │          │  Redis (Standalone)     │
│                          │          │                          │
│  S3 (Primary Bucket)     │  CRR     │  S3 (DR Bucket)         │
└──────────────────────────┘          └──────────────────────────┘
```

### 4.2 Failover Procedure

| Phase | Action | Target Duration | Owner |
|-------|--------|-----------------|-------|
| **Detection** | Prometheus AlertManager detects primary region unavailability (>5min) | Auto | Monitoring |
| **Decision** | Incident Commander declares DR event | Manual (<15min) | SRE Lead |
| **DNS Cutover** | Route53 / DNS update: `*.app.system.com` → DR Region LB | <5min (TTL 60s) | DevOps |
| **DB Promotion** | Promote PostgreSQL Standby to Primary in DR Region | <5min | DBA |
| **Service Scale-Up** | Scale DR K8s Deployments to production replica count | <10min | DevOps |
| **Validation** | Smoke tests: NL→Preview, Workflow Execute, Agent Query | <15min | QA |
| **Communication** | StatusPage update + notify tenants via email/in-app | <5min | Support |

**Total RTO Target**: <60 minutes from detection to validated service restoration.

### 4.3 Recovery Testing

| Test Type | Frequency | Scope |
|-----------|----------|-------|
| Backup Restore Drill | Weekly (T2/T3), Monthly (T0/T1) | Restore to staging, run DQ validation |
| DR Failover Drill | Quarterly | Full production-like failover to DR region |
| Chaos Engineering | Post-MVP (Phase 7+) | Controlled fault injection |

## 5. References

- **NIST SP 800-34 Rev 1**: Contingency Planning Guide for Federal Information Systems
- **AWS Well-Architected Framework**: Reliability Pillar (REL-9: Back up data; REL-10: Use fault isolation)
- **Google SRE Workbook**: Chapter 8 — Disaster Recovery
- **ISO 22301**: Business Continuity Management Systems

---

> 📄 Source Location: [../03-architecture.md §24](../03-architecture.md)
