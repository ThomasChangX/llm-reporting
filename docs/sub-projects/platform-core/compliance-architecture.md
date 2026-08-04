# Compliance Architecture

> **Origin**: §25 of [`docs/03-architecture.md`](../../03-architecture.md) | **Sub-project**: [platform-core](README.md)

## Purpose

The Compliance Architecture encodes the platform's obligations under GDPR (EU 2016/679), CCPA (AB-375/CPRA), HIPAA (45 CFR §164), and CSL/DSL/PIPL (PRC). It defines the Data Subject Access Request (DSAR) pipeline (§25.1), the Right-to-Erasure cascade deletion strategy (§25.2), data residency rules (§25.3), consent management (§25.4), breach notification (§25.5), and the API versioning strategy (§25.6). This module operationalizes the platform's security and tenant-isolation foundations (§11) into concrete privacy and regulatory procedures, and it consumes the retention/backup infrastructure defined in [operational-architecture.md](operational-architecture.md).

## Boundaries

**In-scope:**
- Four-stage DSAR processing pipeline and SLA (§25.1).
- Right-to-Erasure cascade deletion with exceptions (§25.2).
- Data residency rules by market (China/US/EU) and cross-border safeguards (§25.3).
- Consent management granularity and withdrawal behavior (§25.4).
- Breach notification timelines to authorities and data subjects (§25.5).
- API versioning scheme (URL/gRPC/MCP), deprecation, sunset, and breaking-change policy (§25.6).

**Delegated / out-of-scope:**
- **Retention schedules and backup/DR mechanics** → [operational-architecture.md](operational-architecture.md) §24.1, §24.4 (this document references them for erasure/backup handling).
- **Encryption, secrets, and tenant isolation primitives** → [cross-cutting-layer.md](cross-cutting-layer.md) §11.1, §11.2.
- **Security incident response / threat analysis** → [docs/security/threat-model.md](../../security/threat-model.md) (this document defines the *notification* obligations once a breach is confirmed).

**Upstream/downstream neighbors:**
- *Producers*: data subjects (DSAR/erasure/consent requests), the incident system (breach flags), API consumers (versioning).
- *Consumers*: all data stores (PG/Vector/Graph/S3) for discovery and erasure; the Audit Trail (breach logging); API Gateway and all sub-projects (versioning policy).

## Interfaces

### §25.1 Data Subject Access Request (DSAR) — four-stage pipeline

| Stage | Function |
| --- | --- |
| 1. Identity Verification | Government ID + 2FA; Confirm jurisdiction (GDPR/CCPA) |
| 2. Data Discovery | Query all stores by subject_id/tenant_id (PG + Vector + Graph + S3) |
| 3. Data Compilation | Machine-readable JSON/CSV; Categories, purposes, recipients, retention periods included |
| 4. Secure Delivery | AES-256 encrypted download (7d expiry) or physical media |

**SLA**: 30 calendar days (GDPR Art.12.3); +60d extension for complex requests (notify within 30d).

### §25.2 Right to Erasure — cascade deletion

| Entity | Method | Exceptions |
| --- | --- | --- |
| `user_session` | Soft-delete → PII nullified after 30d grace | — |
| `tenant` | Soft-delete → 90d grace → full PII purge | Legal hold flag |
| `kb_entry` | Anonymize source_reference, confirmed_by | — |
| `audit_log` | **No deletion** (7yr regulatory retention) | SOX/HIPAA mandate |
| Backups | Delete on next rotation cycle (max 30d) | Restore verification required |

### §25.3 Data Residency

| Market | Primary Region | Rule |
| --- | --- | --- |
| China | cn-north-1 (Beijing) | T2/T3 data within PRC (CSL/DSL) |
| US | us-east-1 (Virginia) | T2/T3 data within US |
| EU | eu-central-1 (Frankfurt) | T2/T3 data within EU/EEA (GDPR Art.44-49) |

**Cross-Border Safeguards**: SCC (EU→Third Country), BCR (intra-group), DPA with all sub-processors.

### §25.4 Consent Management

| Type | Granularity | Withdrawal |
| --- | --- | --- |
| Data Processing | Per-purpose (Analytics, AI Training, Notifications) | Self-service Portal |
| LLM Data Sharing | Per-LLM-Provider (opt-in, not bundled) | Immediate; fallback to local model |
| Email Ingestion | Per-email-source | Remove from KB config |
| Behavior Tracking | Opt-in (not pre-checked per GDPR) | Delete behavior pattern store |

### §25.6 API Versioning Strategy

| Aspect | Policy |
| --- | --- |
| **Versioning Scheme** | URL path versioning: `/api/v1/`, `/api/v2/` |
| **gRPC** | Package-level versioning: `com.system.api.v1` |
| **MCP** | Protocol version in handshake; server capability negotiation |
| **Deprecation Timeline** | N-2 support: v1 deprecated when v3 released; v1 sunset after v4 release |
| **Sunset Policy** | 6-month notice before version removal; warning header `Sunset: Sat, 31 Dec 2026 23:59:59 GMT` |
| **Breaking Changes** | Require ADR; new API version; old version maintained for deprecation window |

> **Note** (from source): API versioning is an operational concern included here for completeness. See also §24 (Operational Architecture) — [operational-architecture.md](operational-architecture.md).

## Dependencies

- **Data stores** for DSAR discovery and erasure: PostgreSQL, Vector (Milvus/pgvector), Graph (Neo4j), S3 — all queried by `subject_id`/`tenant_id`.
- **Backup/retention infrastructure** (§24): backups are deleted on the next rotation cycle (max 30d) during erasure; `audit_log` retention (7yr) overrides erasure.
- **Audit Trail** — breaches flagged `compliance_breach` in the incident system (§25.5); all operations logged.
- **Identity verification** — Government ID + 2FA for DSAR.
- **API Gateway** and **all sub-projects** — consume the versioning policy.
- **Regulatory frameworks**: GDPR (EU 2016/679), CCPA (AB-375/CPRA), HIPAA (45 CFR §164), CSL/DSL/PIPL (PRC).

## Data Model

The compliance module does not introduce new primary entities; it governs the lifecycle and residency of existing ones:

- **DSAR record** — tracks identity verification, jurisdiction, discovery results, compiled export (JSON/CSV), and secure-delivery status with 7d expiry.
- **Erasure cascade targets** — `user_session` (PII nullified after 30d), `tenant` (90d grace → full PII purge; legal-hold exception), `kb_entry` (anonymize `source_reference`, `confirmed_by`), `audit_log` (no deletion — 7yr SOX/HIPAA retention), backups (next rotation cycle, max 30d).
- **Consent records** — per-purpose, per-LLM-provider, per-email-source, opt-in behavior-tracking; withdrawal triggers (self-service portal, immediate LLM fallback to local model, KB config removal, behavior-pattern-store deletion).
- **Breach record** — `compliance_breach` flag in the incident system; notification timestamps (authority ≤72h per GDPR Art.33; data subjects without undue delay if high risk per Art.34).
- **API version manifest** — active/deprecated/sunset versions; `Sunset` header; N-2 support window; ADR linkage for breaking changes.

## Failure Modes & Recovery

| Failure | Impact | Recovery / mitigation |
| --- | --- | --- |
| DSAR SLA breach (>30 days) | Regulatory non-compliance, fines | +60d extension for complex requests (notify within 30d, GDPR Art.12.3); track DSAR record stage. |
| Erasure conflicts with retention mandate | Cannot delete `audit_log` (7yr) or legal-hold tenants | Cascade exception table: `audit_log` no deletion (SOX/HIPAA); `tenant` legal-hold flag; backups deleted only on next rotation (restore verification required). |
| Cross-border data movement violation | Residency breach (CSL/DSL/GDPR Art.44-49) | T2/T3 pinned to market region; SCC/BCR/DPA safeguards with sub-processors. |
| Consent withdrawal failure | Unlawful continued processing | Immediate withdrawal paths: self-service portal, LLM fallback to local model, KB config removal, behavior-pattern-store deletion. |
| Breach notification missed (>72h to authority) | GDPR Art.33 violation | Breach auto-flagged `compliance_breach`; authority notification SLA tracked in incident system. |
| Breaking API change without ADR | Consumer breakage, contract violation | Policy requires ADR + new API version + old version maintained for deprecation window; 6-month sunset notice with `Sunset` header. |
| Erasure of backup containing PII | PII persists in backups | Backups deleted on next rotation cycle (max 30d); restore verification required before deletion. |

Recovery of the underlying stores (for DR, not erasure) is covered in [operational-architecture.md](operational-architecture.md) §24.1–§24.2 and [domain-services.md](domain-services.md) §12.3.

## Non-Functional Requirements

- **DSAR SLA**: 30 calendar days (GDPR Art.12.3); +60d extension with 30d notification.
- **Breach notification**: to authority within 72h (GDPR Art.33); to data subjects without undue delay if high risk (GDPR Art.34).
- **Residency**: T2/T3 data constrained to market region (China cn-north-1; US us-east-1; EU eu-central-1).
- **Consent**: opt-in not pre-checked (GDPR); per-LLM-provider granularity (not bundled); immediate withdrawal.
- **Erasure**: 30d grace (`user_session`), 90d grace (`tenant`); `audit_log` 7yr retention override.
- **API versioning**: N-2 support; 6-month sunset notice; breaking changes require ADR.
- **Security**: AES-256 encrypted DSAR delivery (7d expiry); threats analyzed in [docs/security/threat-model.md](../../security/threat-model.md).
- **Procedures**: detailed compliance procedures in [docs/operations/gdpr-compliance.md](../../operations/gdpr-compliance.md); SLOs in [docs/operations/slo-sli.md](../../operations/slo-sli.md).

## Key Flows

### §25.1 DSAR pipeline (Verify → Discover → Compile → Deliver)

Identity verification (Government ID + 2FA, confirm jurisdiction GDPR/CCPA) → data discovery across all stores by `subject_id`/`tenant_id` (PG + Vector + Graph + S3) → compilation to machine-readable JSON/CSV (categories, purposes, recipients, retention) → secure delivery via AES-256 encrypted download (7d expiry) or physical media. SLA: 30 days, extendable +60d for complex requests.

### §25.2 Right-to-Erasure cascade

Request received → cascade per entity table: `user_session` soft-delete + PII nullify (30d grace) → `tenant` soft-delete (90d grace → full PII purge; legal-hold exception) → `kb_entry` anonymize (`source_reference`, `confirmed_by`) → `audit_log` **no deletion** (7yr SOX/HIPAA) → backups deleted on next rotation cycle (max 30d, restore verification required).

### §25.5 Breach notification

Incident flagged `compliance_breach` in the incident system → authority notification within 72h (GDPR Art.33, unless unlikely to result in risk) → data-subject notification without undue delay if high risk (GDPR Art.34).

### §25.6 API version lifecycle

New version released (`/api/vN`) → previous versions maintained under N-2 support → on `vN+2` release, `vN` deprecated → sunset: 6-month notice with `Sunset` header → version removed. Breaking changes require an ADR and a new API version (old version retained through deprecation window).

## Design References

- **Original section**: §25 (§25.1–§25.6) of [`docs/03-architecture.md`](../../03-architecture.md).
- **Foundational regulations**: GDPR (EU 2016/679), CCPA (AB-375/CPRA), HIPAA (45 CFR §164), CSL/DSL/PIPL (PRC).
- **Related platform-core docs**: [operational-architecture.md](operational-architecture.md) §24 (retention/backup), [cross-cutting-layer.md](cross-cutting-layer.md) §11.1/§11.2 (encryption, tenant isolation, RBAC/ABAC), [domain-services.md](domain-services.md) §12.3 (per-store recovery).
- **ADRs** ([index](../../adr-index.md)): [ADR-0010 BRD/ADR as First-Class Entities](../../../adr/0010-brd-adr-first-class.md) (ADR requirement for breaking changes), [ADR-0013 KB Storage Strategy](../../../adr/0013-kb-storage-strategy.md).
- **Glossary** ([../../glossary.md](../../glossary.md)): Compute Spec, Cross-Environment Read-Only Mode.
- **External procedures**: [docs/operations/gdpr-compliance.md](../../operations/gdpr-compliance.md), [docs/security/threat-model.md](../../security/threat-model.md), [docs/operations/slo-sli.md](../../operations/slo-sli.md).
