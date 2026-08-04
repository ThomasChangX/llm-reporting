# platform-core — Platform Foundation & Cross-Cutting Concerns

> **Origin**: §8, §11, §12.1, §12.3–§12.7, §24, §25 of `docs/03-architecture.md`
> **Related**: [`docs/security/threat-model.md`](../security/threat-model.md), [`docs/operations/`](../operations/)

## Positioning

The **Platform Core** sub-project is the foundation every other sub-project builds upon. It owns all cross-cutting infrastructure: authentication, authorization, tenant isolation, audit trails, observability, logging, notification, file export, integration framework, support/ticket, DevOps, operational architecture, and compliance.

This is intentionally the largest "bucket" — cross-cutting concerns are, by definition, shared. The natural split point if future scale demands it is **security-compliance** (§11.1/§11.2/§16/§25) as a separate sub-project, but premature decomposition of cross-cutting layers is avoided per the design's "one platform" philosophy.

## Boundaries

**In-scope:**
- Auth Gateway (OAuth 2.0, Kerberos, SAML/SSO, LDAP) + API Gateway (Rate Limit, Auth, Route, Tenant)
- Entitlement (RBAC + ABAC) and Tenant Isolation (three-level, Data Masking, Row-Level Security)
- Audit Trail (immutable, exportable)
- Version Control (Git-based VCS integration)
- Observability (OpenTelemetry-aligned) and Log System
- Cross-Cutting Components: File Export, Integration Framework, Support & Ticket, Jira/Rally Integration, DevOps
- Domain Services: Email Ingestion Pipeline (FR17), Backup & DR (FR41), Notification Service (FR37), Runtime Dependency Manager (FR40), Observation Engine (FR3), Data Flow Panorama
- Operational Architecture: Backup & Recovery, DR, Schema Migration, Data Retention, Secrets Rotation, Platform Deployment, Capacity Planning
- Compliance Architecture: DSAR, Right to Erasure, Data Residency, Consent Management, Breach Notification, API Versioning

**Consumed by (all sub-projects):**
- Every sub-project relies on platform-core for auth context, RBAC enforcement, audit logging, tenant isolation, and observability instrumentation.

## Module List

| Module | Origin | Document |
|--------|--------|----------|
| Cross-Cutting Layer (Security, Entitlement, VC, Observability, Audit, Tenant, Integration, File Export, Support, DevOps) | §11 | [`cross-cutting-layer.md`](cross-cutting-layer.md) |
| Observability & Log System + Observation Engine | §8, §12.6 | [`observability.md`](observability.md) |
| Domain Services (Email Ingestion, Backup & DR, Notification, Runtime Dependency, Data Flow) | §12.1, §12.3–§12.5, §12.7 | [`domain-services.md`](domain-services.md) |
| Operational Architecture (Backup, DR, Schema Migration, Retention, Secrets, Deployment, Capacity) | §24 | [`operational-architecture.md`](operational-architecture.md) |
| Compliance Architecture (GDPR, CCPA, HIPAA, CSL) | §25 | [`compliance-architecture.md`](compliance-architecture.md) |

## External Interface Contract

| Interface | Consumer | Contract |
|-----------|----------|----------|
| `auth.authenticate(token) → principal` | All sub-projects | Validates OAuth/Kerberos/SAML → returns tenant + role context |
| `entitlement.check(principal, resource, action) → bool` | All sub-projects | RBAC + ABAC evaluation |
| `audit.log(principal, action, resource, result)` | All sub-projects | Immutable append to audit trail |
| `observability.trace(span_data)` | All sub-projects | OpenTelemetry-compatible span emission |
| `notify.recipient(channel, message)` | Workflow Engine, Data Health, Agent Platform | Multi-channel notification (Email/Slack/Webhook) |

## Related Views

- [Threat Model (STRIDE + OWASP LLM)](../security/threat-model.md) — cross-sub-project security analysis
- [SLO/SLI Definitions](../operations/slo-sli.md) — error budget allocation
- [Backup & DR](../operations/backup-dr.md) — operational procedures
- [GDPR Compliance](../operations/gdpr-compliance.md) — compliance procedures
