# Core Entity ERD

> Extracted from [docs/03-architecture.md §18](../03-architecture.md) | Sync Date: 2026-07-04
>
> Core entity relationship model with complete DDL-level definitions for 9 entities (7 core entities: tenant/workflow/job/data_source/kb_entry/audit_log/user_session + workflow_version support entity + incident operations entity), relationship diagrams, and partitioning strategies.

## 18. Core Entity ERD

### 18.1 Entity Definitions

#### 18.1.1 `tenant`

| Property | Specification |
|----------|---------------|
| **Purpose** | Multi-tenancy anchor. Every other entity is tenant-scoped. |
| **PK** | `id UUID DEFAULT gen_random_uuid()` |
| **Critical Columns** | `name VARCHAR(128) NOT NULL UNIQUE`, `slug VARCHAR(64) NOT NULL UNIQUE`, `tier ENUM('free','pro','enterprise') NOT NULL DEFAULT 'pro'`, `config JSONB NOT NULL DEFAULT '{}'` (KMS key ARN, SSO metadata, feature flags, retention policies), `isolation_level ENUM('L1_process','L2_node','L3_cluster') NOT NULL DEFAULT 'L1_process'`, `status ENUM('active','suspended','deleted') NOT NULL DEFAULT 'active'`, `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`, `updated_at TIMESTAMPTZ NOT NULL DEFAULT now()` |
| **Indexes** | `UNIQUE(slug)`, `INDEX(status, tier)`, `GIN(config jsonb_path_ops)` |
| **Partition** | None (small table, <10K rows) |
| **Notes** | Soft-delete via `status='deleted'` + `deleted_at`. Per-tenant `config` drives SSO config, KMS key selection, and feature toggles. |

#### 18.1.2 `workflow`

| Property | Specification |
|----------|---------------|
| **Purpose** | Top-level unit of work: a reporting, ETL, adjustment, or reconciliation pipeline. |
| **PK** | `id UUID DEFAULT gen_random_uuid()` |
| **FK** | `tenant_id UUID NOT NULL REFERENCES tenant(id)` |
| **Critical Columns** | `name VARCHAR(256) NOT NULL`, `type ENUM('reporting','etl','adjustment','recon') NOT NULL`, `status ENUM('draft','user_reviewed','frozen','canary','active','paused','deprecated') NOT NULL DEFAULT 'draft'`, `spec_yaml TEXT NOT NULL` (full Compute Spec YAML, validated at write), `spec_hash CHAR(64) NOT NULL` (SHA-256 of spec_yaml, for integrity verification), `engine ENUM('light_only','heavy_only','portable') NOT NULL DEFAULT 'portable'`, `confidence_summary JSONB` (from Design Artifact), `git_commit_sha CHAR(40)`, `git_branch VARCHAR(256)`, `created_by UUID NOT NULL REFERENCES user_session(id)`, `updated_at TIMESTAMPTZ NOT NULL DEFAULT now()`, `frozen_at TIMESTAMPTZ`, `deprecated_at TIMESTAMPTZ` |
| **Indexes** | `INDEX(tenant_id, type)`, `INDEX(tenant_id, status)`, `INDEX(tenant_id, git_branch) WHERE status IN ('frozen','canary','active')`, `INDEX(created_at)` |
| **Partition** | **None** — rows per tenant expected <10K; no partitioning needed. |
| **Notes** | `spec_yaml` is immutable once `frozen_at` is set (enforced by application layer + trigger). Changes to a frozen workflow create a new version row in `workflow_version` (see below). |

#### 18.1.2b `workflow_version` (supporting entity for workflow versioning)

| Property | Specification |
|----------|---------------|
| **PK** | `id UUID DEFAULT gen_random_uuid()` |
| **FK** | `workflow_id UUID NOT NULL REFERENCES workflow(id)`, `frozen_by UUID NOT NULL REFERENCES user_session(id)` |
| **Critical Columns** | `version INT NOT NULL`, `spec_yaml TEXT NOT NULL`, `spec_hash CHAR(64) NOT NULL`, `change_summary TEXT NOT NULL`, `frozen_at TIMESTAMPTZ NOT NULL DEFAULT now()` |
| **Indexes** | `UNIQUE(workflow_id, version)`, `INDEX(workflow_id, frozen_at DESC)` |
| **Partition** | None |

#### 18.1.3 `job`

| Property | Specification |
|----------|---------------|
| **Purpose** | Smallest execution unit within a workflow. A DAG node. |
| **PK** | `id UUID DEFAULT gen_random_uuid()` |
| **FK** | `workflow_id UUID NOT NULL REFERENCES workflow(id) ON DELETE CASCADE`, `tenant_id UUID NOT NULL REFERENCES tenant(id)` |
| **Critical Columns** | `name VARCHAR(256) NOT NULL`, `type ENUM('source','transform','output','quality','workflow_ref','data_writer','decision','wait','materialize') NOT NULL`, `config JSONB NOT NULL` (type-specific config: connector, SQL, Python code, quality rules, etc.), `group_name VARCHAR(128)` (logical grouping), `position INT` (ordinal within group for display only — execution order determined by `depends_on`), `dependencies UUID[] NOT NULL DEFAULT '{}'` (array of job IDs this job depends on), `timeout_seconds INT NOT NULL DEFAULT 3600`, `retry_max INT NOT NULL DEFAULT 3`, `engine_override ENUM('light','heavy',NULL) DEFAULT NULL`, `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`, `updated_at TIMESTAMPTZ NOT NULL DEFAULT now()` |
| **Indexes** | `INDEX(workflow_id, group_name)`, `INDEX(tenant_id)`, `GIN(dependencies)` (for reverse-lookup: "what depends on this job?"), `INDEX(type)` |
| **Partition** | None (parent `workflow_id` provides natural sharding) |
| **Notes** | `dependencies` is a UUID array mapping to `depends_on` in Compute Spec. The DAG is validated on write: cycle detection runs via BFS; rejecting cycles before persist. `workflow_ref` type jobs store the referenced workflow's UUID in `config->>'ref_workflow_id'`. |

#### 18.1.4 `data_source`

| Property | Specification |
|----------|---------------|
| **Purpose** | Registered external data source available for Workflow `source` and `data_writer` jobs. |
| **PK** | `id UUID DEFAULT gen_random_uuid()` |
| **FK** | `tenant_id UUID NOT NULL REFERENCES tenant(id)`, `registered_by UUID NOT NULL REFERENCES user_session(id)` |
| **Critical Columns** | `name VARCHAR(256) NOT NULL`, `type ENUM('postgresql','snowflake','bigquery','redshift','mysql','mssql','oracle','s3','api_rest','kafka','custom') NOT NULL`, `connector_config JSONB NOT NULL` (encrypted at application layer: host, port, db, credentials reference to Vault path — never plaintext credentials), `schema_catalog JSONB` (cached schema snapshot: tables, columns, types — refreshed on schedule), `data_classification_tier ENUM('T0','T1','T2','T3') NOT NULL DEFAULT 'T2'`, `sensitivity_tags JSONB DEFAULT '{}'` (column-level PII flags), `dq_score DECIMAL(3,2) CHECK (dq_score >= 0 AND dq_score <= 1)`, `status ENUM('active','degraded','unavailable','deprecated') NOT NULL DEFAULT 'active'`, `last_validated_at TIMESTAMPTZ`, `created_at TIMESTAMPTZ NOT NULL DEFAULT now()` |
| **Indexes** | `INDEX(tenant_id, type)`, `INDEX(tenant_id, status)`, `GIN(connector_config jsonb_path_ops)`, `GIN(schema_catalog jsonb_path_ops)` |
| **Partition** | None |
| **Notes** | Credentials are stored in Vault at `secret/data_sources/{tenant_id}/{id}`. `connector_config` stores only the Vault path reference and non-secret fields (timeout, pool size, etc.). `schema_catalog` is refreshed by a background job that samples the source schema every 6h; drift alerts fire on change. |

#### 18.1.5 `kb_entry`

| Property | Specification |
|----------|---------------|
| **Purpose** | Single entry in any of the 9 KB domains (Business Glossary, Data Catalog, Mapping Registry, Workflow Templates, Adjustment History, Behavior Patterns, Report/Metric Catalog, Diagnostic Playbooks, Code Knowledge). |
| **PK** | `id UUID DEFAULT gen_random_uuid()` |
| **FK** | `tenant_id UUID NOT NULL REFERENCES tenant(id)`, `parent_id UUID REFERENCES kb_entry(id)` (for hierarchical entries), `confirmed_by UUID REFERENCES user_session(id)`, `superseded_by UUID REFERENCES kb_entry(id)` (version chain) |
| **Critical Columns** | `domain ENUM('business_glossary','data_catalog','mapping_registry','workflow_template','adjustment_history','behavior_pattern','report_catalog','diagnostic_playbook','code_knowledge') NOT NULL`, `title VARCHAR(512) NOT NULL`, `content TEXT NOT NULL` (Markdown body), `content_vector VECTOR(1536)` (embedding, generated by text-embedding-ada-002 or equivalent), `tags TEXT[] NOT NULL DEFAULT '{}'`, `metadata JSONB NOT NULL DEFAULT '{}'` (domain-specific structured fields), `version INT NOT NULL DEFAULT 1`, `status ENUM('draft','proposed','confirmed','deprecated','superseded') NOT NULL DEFAULT 'draft'`, `confidence DECIMAL(3,2)` (AI extraction confidence, NULL if human-authored), `source_type ENUM('human','ai_extraction','import') NOT NULL`, `source_reference TEXT` (e.g., email_id, import batch_id, original_url), `expires_at TIMESTAMPTZ` (for time-sensitive entries like quarterly definitions), `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`, `updated_at TIMESTAMPTZ NOT NULL DEFAULT now()` |
| **Indexes** | `INDEX(tenant_id, domain)`, `INDEX(tenant_id, status)`, `INDEX(tenant_id, tags) USING GIN`, `INDEX(tenant_id, parent_id)`, `INDEX(tenant_id, superseded_by)`, `INDEX(created_at)`, **Vector index**: `INDEX(content_vector) USING ivfflat (lists=1000)` or `INDEX(content_vector) USING hnsw` (for pgvector) |
| **Partition** | **Partition by LIST on `domain`** — each domain in its own partition for query isolation and backup granularity. |
| **Versioning Strategy** | On update to a `confirmed` entry: (1) increment version, (2) set old row's `status='superseded'` and `superseded_by=new_id`, (3) insert new row with `version=old.version+1` and `parent_id=old.id`. Full version history preserved. Immutable once `superseded`. |
| **Notes** | Embedding is regenerated on content change. Vector index is maintained on `confirmed` rows only. `expires_at` triggers a background job that sets `status='deprecated'` and notifies the owner. |

#### 18.1.6 `audit_log`

| Property | Specification |
|----------|---------------|
| **Purpose** | Immutable, append-only record of every state-changing operation in the system. |
| **PK** | `id BIGSERIAL` (monotonic, not UUID — for partition-range efficiency) |
| **FK** | `tenant_id UUID NOT NULL` (not a FK constraint — retained for partition pruning; the row may outlive the tenant row), `actor_id UUID` (may be NULL for system actions), `workflow_id UUID`, `job_id UUID` |
| **Critical Columns** | `event_type VARCHAR(64) NOT NULL` (e.g., `workflow.freeze`, `job.execute.start`, `kb.entry.confirm`, `user.login`), `event_ts TIMESTAMPTZ NOT NULL DEFAULT now()`, `resource_type VARCHAR(64) NOT NULL`, `resource_id UUID NOT NULL`, `diff JSONB` (before/after or change delta), `result JSONB` (outcome payload: success/error, duration, affected rows), `client_ip INET`, `user_agent TEXT`, `trace_id UUID` (OpenTelemetry trace correlation), `request_id UUID NOT NULL UNIQUE` (idempotency key) |
| **Indexes** | `INDEX(tenant_id, event_ts DESC)`, `INDEX(tenant_id, event_type, event_ts DESC)`, `INDEX(workflow_id, event_ts DESC)`, `INDEX(trace_id)`, `UNIQUE(request_id)` (idempotency) |
| **Partition** | **Partition by RANGE on `event_ts`**, one partition per calendar month. Auto-create future partitions via pg_partman or cron. Retention: 7 years hot (PG), then archived to S3 as Parquet and dropped. |
| **Notes** | **Strictly append-only**: no UPDATE or DELETE allowed (enforced by table-level trigger + restricted DB user). Reads are via dedicated `audit_reader` role. Immutability is the core compliance guarantee. |

#### 18.1.7 `user_session`

| Property | Specification |
|----------|---------------|
| **Purpose** | Authenticated user identity and session tracking. Links to IdP subject. |
| **PK** | `id UUID DEFAULT gen_random_uuid()` |
| **FK** | `tenant_id UUID NOT NULL REFERENCES tenant(id)` |
| **Critical Columns** | `idp_subject VARCHAR(256) NOT NULL` (immutable subject claim from IdP), `display_name VARCHAR(256) NOT NULL`, `email VARCHAR(256) NOT NULL`, `role ENUM('viewer','analyst','developer','data_owner','admin') NOT NULL`, `extra_permissions JSONB DEFAULT '[]'` (ABAC attribute grants: `[{"action":"approve_freeze","scope":"workflow:uuid-abc","expires_at":"..."}]`), `preferences JSONB DEFAULT '{}'` (UI preferences, notification settings, quiet hours), `last_login_at TIMESTAMPTZ`, `status ENUM('active','suspended','deactivated') NOT NULL DEFAULT 'active'`, `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`, `updated_at TIMESTAMPTZ NOT NULL DEFAULT now()` |
| **Indexes** | `UNIQUE(tenant_id, idp_subject)`, `UNIQUE(tenant_id, email)`, `INDEX(role)`, `INDEX(status)` |
| **Partition** | None |
| **Notes** | Role changes are logged to `audit_log`. `extra_permissions` are time-bound temporary grants that auto-expire. Session tokens (JWT) are not stored here — managed by Auth Service with Redis cache. |

#### 18.1.8 `incident`

| Property | Specification |
|----------|---------------|
| **Purpose** | Operational incident created automatically by Incident Manager or manually. |
| **PK** | `id UUID DEFAULT gen_random_uuid()` |
| **FK** | `tenant_id UUID NOT NULL REFERENCES tenant(id)`, `linked_workflow_id UUID REFERENCES workflow(id)`, `linked_job_id UUID REFERENCES job(id)`, `assigned_to UUID REFERENCES user_session(id)`, `resolved_by UUID REFERENCES user_session(id)` |
| **Critical Columns** | `title VARCHAR(512) NOT NULL`, `severity ENUM('P0_critical','P1_high','P2_medium','P3_low','P4_info') NOT NULL`, `status ENUM('open','acknowledged','investigating','mitigated','resolved','closed','duplicate') NOT NULL DEFAULT 'open'`, `source ENUM('workflow_failure','dq_failure','canary_gate','kb_sync_lag','system_health','manual') NOT NULL`, `context JSONB NOT NULL` (full execution context: trace_id, job config, input snapshot reference, error stack), `resolution_notes TEXT`, `escalation_path JSONB DEFAULT '[]'` (list of escalations with timestamps and assignees), `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`, `resolved_at TIMESTAMPTZ`, `closed_at TIMESTAMPTZ`, `sla_deadline TIMESTAMPTZ` (calculated from severity + business hours) |
| **Indexes** | `INDEX(tenant_id, status, severity)`, `INDEX(tenant_id, linked_workflow_id)`, `INDEX(assigned_to, status)`, `INDEX(sla_deadline) WHERE status NOT IN ('resolved','closed')`, `INDEX(created_at DESC)` |
| **Partition** | **Partition by RANGE on `created_at`**, monthly. Active partitions: current + previous 3 months. Older partitions archived to S3 after 3 months. |
| **Notes** | SLA deadlines: P0=1h, P1=4h, P2=24h, P3=72h, P4=1wk (business hours). Breach escalation: auto-notify manager at 50%/90%/100% of SLA window. `context` embeds enough information for the Incident Diagnosis Assistant (docs/03-architecture.md §8 AI-Powered consumption) to suggest root cause. |

### 18.2 ERD Relationship Summary

```
  ┌──────────┐
  │  tenant  │
  └────┬─────┘
       │ 1:N
       ├──────────┬──────────┬──────────┬──────────┬──────────┐
       ▼          ▼          ▼          ▼          ▼          ▼
  ┌────────┐ ┌────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐ ┌──────────┐
  │workflow│ │  job   │ │data_source│ │kb_entry│ │audit_log │ │  user_   │
  └───┬────┘ └───┬────┘ └──────────┘ └───┬────┘ │          │ │ session  │
      │ 1:N      │ 1:N                   │       └──────────┘ └────┬─────┘
      │          │                       │ self-ref                 │
      │          │ depends_on: UUID[]     │ (parent_id,              │
      │          │ (self-referencing)     │  superseded_by)          │
      ▼          ▼                                                │
  ┌──────────┐                                              ┌─────┴─────┐
  │ workflow │                                              │ incident  │
  │ _version │                                              │           │
  └──────────┘                                              │ linked_   │
                                                            │ workflow  │
  ┌──────────────────────────────────────────────────────┐  │ linked_job│
  │ NOTE: audit_log references all entities by UUID but  │  │ assigned  │
  │ uses NO FK constraints (immutable log independence)  │  │ _to       │
  └──────────────────────────────────────────────────────┘  └───────────┘
```

---


> 📄 Source Location: [../03-architecture.md §18](../03-architecture.md)
