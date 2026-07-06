# GDPR & CCPA Compliance Architecture

> Extracted from [docs/03-architecture.md §25](../03-architecture.md) | Sync Date: 2026-07-04
>
> Designed based on GDPR (EU 2016/679), CCPA (AB-375), HIPAA (45 CFR §164) compliance requirements.

## 1. Data Subject Access Request (DSAR) Workflow

```
User/Data Subject
      │
      │  Submit DSAR via Privacy Portal or email dpo@system.com
      ▼
┌──────────────────────────────────────────────────────────────┐
│                    DSAR HANDLING PIPELINE                      │
│                                                               │
│  1. IDENTITY VERIFICATION                                     │
│     • Verify requester identity (government ID, 2FA)          │
│     • Confirm jurisdiction (GDPR EU citizen? CCPA CA resident?)│
│     • Log request with immutable request_id                    │
│                                                               │
│  2. DATA DISCOVERY                                            │
│     • Query all data stores by subject_id / tenant_id          │
│     • PostgreSQL: SELECT FROM audit_log, user_session,        │
│       workflow (created_by), kb_entry (confirmed_by)          │
│     • Vector DB: Embedding search for PII mentions            │
│     • Graph DB: Traverse all nodes linked to subject          │
│     • Object Store: Scan email attachments, LLM transcripts   │
│                                                               │
│  3. DATA COMPILATION                                          │
│     • Aggregate into machine-readable JSON/CSV                │
│     • Include: data categories, processing purposes,          │
│       recipients, retention periods, source                    │
│     • Redact third-party PII before delivery                  │
│                                                               │
│  4. SECURE DELIVERY                                           │
│     • Encrypted download link (AES-256, 7-day expiry)         │
│     • Or physical media (encrypted USB, registered mail)      │
│     • Delivery confirmation + audit log entry                 │
│                                                               │
│  SLA: 30 calendar days (GDPR Art.12.3)                        │
│  Extension: +60 days for complex requests (notify within 30d) │
└──────────────────────────────────────────────────────────────┘
```

## 2. Right to Erasure ("Right to be Forgotten")

### 2.1 Cascade Deletion Strategy

| Entity | Deletion Method | Cascade Effect |
|--------|----------------|----------------|
| `user_session` | Soft-delete → `status='deactivated'`; PII fields nullified after 30d grace | Anonymize `created_by`, `confirmed_by` references in workflow, kb_entry |
| `tenant` (full account deletion) | Soft-delete → `status='deleted'`; 90d grace period; Full PII purge after grace | Cascade to all tenant-scoped entities per retention policy |
| `kb_entry` (user-authored) | Anonymize `source_reference`, `confirmed_by`; retain content_vector for system integrity | Notify affected Workflow Owners if entry is referenced |
| `audit_log` (individual events) | **No deletion** (7-year regulatory retention required). PII redaction via masking at query time | N/A — audit trail immutability preserved |
| Email attachments | Delete from S3 after erasure request + grace period | PII scan to verify completeness |
| Backup archives | Delete from backup on next rotation cycle (max 30d) | Backup restoration includes erasure verification |

### 2.2 Erasure Exceptions (GDPR Art.17.3)

The system may refuse erasure when data is necessary for:
- **Legal obligation** (SOX/HIPAA retention mandates — audit_log excluded from erasure)
- **Legal claims** (active litigation hold — flag preserved via `legal_hold` metadata)
- **Public interest** (archiving purposes in public interest)
- **Freedom of expression** (exercising right to freedom of expression and information)

## 3. Data Residency & Cross-Border Transfer

### 3.1 Region Affinity

| Market | Primary Region | DR Region | Data Residency Rule |
|--------|---------------|-----------|---------------------|
| **China** | cn-north-1 (Beijing) | cn-east-2 (Shanghai) | All T2/T3 data stays within PRC borders (CSL + DSL compliance) |
| **US** | us-east-1 (Virginia) | us-west-2 (Oregon) | All T2/T3 data stays within US borders |
| **EU** | eu-central-1 (Frankfurt) | eu-west-1 (Ireland) | All T2/T3 data stays within EU/EEA (GDPR Art.44-49) |

### 3.2 Cross-Border Transfer Safeguards

When data MUST cross borders (e.g., US support team accessing EU tenant data):

| Mechanism | Applicable Regulation | Implementation |
|-----------|----------------------|----------------|
| **Standard Contractual Clauses (SCC)** | GDPR (EU→Third Country) | Incorporated into DPA; reviewed annually |
| **Binding Corporate Rules (BCR)** | GDPR (intra-group transfers) | Approved by lead supervisory authority |
| **Data Processing Agreement (DPA)** | GDPR Art.28 | Signed with all sub-processors (LLM Providers, Cloud Vendors) |
| **Adequacy Decision** | GDPR Art.45 | Rely on EU Commission adequacy decisions where applicable |
| **Privacy Shield 2.0** | EU-US Data Privacy Framework | Certified if adopted and recognized |

## 4. Consent Management

| Consent Type | When Collected | Granularity | Withdrawal |
|-------------|---------------|-------------|------------|
| **Data Processing** | Tenant onboarding | Per-purpose: Analytics, AI Training, Email Notifications | Self-service in Privacy Portal |
| **LLM Data Sharing** | Before first AI interaction | Per-LLM-Provider (opt-in, not bundled) | Immediate effect; fallback to local model or manual mode |
| **Email Ingestion** | Per-email-source configuration | Per-email-address | Remove email source from KB ingestion config |
| **Behavior Tracking** | First login | Opt-in (not pre-checked per GDPR) | Delete behavior pattern store entries |

## 5. Data Protection Officer (DPO)

Per GDPR Art.37, a DPO is required because:
1. Processing is carried out by a public authority (if serving government clients)
2. Core activities consist of **regular and systematic monitoring of data subjects on a large scale** (the Behavior Pattern Store)
3. Core activities consist of **processing on a large scale of special categories of data** (T3 Restricted data)

**DPO Responsibilities**:
- Monitor GDPR/CCPA/HIPAA compliance
- Advise on Data Protection Impact Assessments (DPIA)
- Cooperate with supervisory authorities
- Act as contact point for data subjects
- Maintain Records of Processing Activities (ROPA, GDPR Art.30)

**Estimated Cost**: $80,000–$120,000/year (full-time or fractional, see `docs/05-cost.md` (cost estimates section))

## 6. Breach Notification

Per GDPR Art.33-34:
- **To Supervisory Authority**: Within **72 hours** of becoming aware of breach (unless unlikely to result in risk)
- **To Data Subjects**: Without **undue delay** if high risk to rights and freedoms
- **Documentation**: All breaches documented in incident system with `compliance_breach` flag

## 7. References

- **GDPR**: Regulation (EU) 2016/679 of the European Parliament
- **CCPA**: California Consumer Privacy Act (AB-375), as amended by CPRA
- **HIPAA**: 45 CFR Part 160 and Subparts A, C, and E of Part 164
- **CSL**: Cybersecurity Law of the People's Republic of China (2017)
- **DSL**: Data Security Law of the People's Republic of China (2021)
- **PIPL**: Personal Information Protection Law of the People's Republic of China (2021)
- **ISO 27701**: Privacy Information Management System (PIMS)

---

> 📄 Original Location: [../03-architecture.md §25](../03-architecture.md)
