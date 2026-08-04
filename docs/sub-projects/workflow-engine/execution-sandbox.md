# Execution Sandbox

> **Origin**: §7 of [`docs/03-architecture.md`](../../03-architecture.md) | **Sub-project**: [workflow-engine](README.md)

## Purpose

This module covers the **Execution Sandbox** — the isolated runtime container in which every Job executes. Per §7, each Job executes in an independent Sandbox that provides resource isolation, a security boundary, a warm pool for sub-100ms acquisition, multi-tenant isolation tiers, and a lightweight Exploration-Environment variant for sampled-data execution.

The Sandbox owns three core mechanisms that the rest of the engine depends on:
- **§7.1 State-Passing Mechanism** — reference-based / shared-volume passing between Jobs (no data copying).
- **§7.2 Python Execution Constraints** — import whitelist, AST static analysis, mandatory code review, seccomp runtime enforcement, and timeouts.
- **§7.3 SQL Injection Defense** — parameterized queries, SQL AST validation, variable-injection sanitization, sandbox enforcement, and audit.

## Boundaries

**In-scope:**
- §7 Sandbox dimensions: Resource Isolation (CPU/Memory/Disk/Network), Security Boundary (FS layout `/workspace/` `/input/` `/output/` `/secrets/`, network whitelist, seccomp), Warm Pool (<100ms acquisition), Multi-Tenant Isolation (L1/L2/L3), Exploration Environment lightweight Sandbox.
- §7.1 State-Passing Mechanism — same-group symlink passing, cross-group Object Store (S3/MinIO) mediation, >1GB auto-degrade, immutability (`chmod 555`), cleanup.
- §7.2 Python Execution Constraints — Import Whitelist, AST Static Analysis (commit-time), Mandatory Code Review, Sandbox Enforcement (seccomp), Timeout (30min Design / 4h Runtime).
- §7.3 SQL Injection Defense — Parameterized Queries, SQL AST Validation, Variable Injection Sanitization, Sandbox Enforcement, Audit.

**Delegated / out-of-scope:**
- The Compute Spec language, Job Types, dependency rules → [`compute-spec.md`](compute-spec.md) (§6).
- `freeze()` operation and fuzzy-node resolution → [`freeze-pipeline.md`](freeze-pipeline.md) (§4). The Freeze Pipeline's Test Runner *uses* the Sandbox (§7) for dry-runs but does not own it.
- MCP servers/Tools invoked by `llm_reasoning` → [`agent-platform`](../agent-platform/).
- Tenant identity, RBAC, audit-trail storage, Incident Manager → [`platform-core`](../platform-core/). The Sandbox enforces isolation but does not own identity.

**Upstream/downstream neighbors:**
- *Provisioning*: Warm Pool pre-creates Sandboxes; Executor acquires one per Job (<100ms).
- *Data flow*: upstream Job writes to `/output/<job_id>/` → downstream reads via `/input/<upstream_job_id>/` symlink (same group) or via Object Store presigned URL/IAM role (cross-group / >1GB).
- *Enforcement*: AST scans run at commit time (Freeze Pipeline); seccomp + DB-user permissions run at execution time (Sandbox runtime).

## Interfaces

### §7 Sandbox — design dimensions

Each Job executes in an independent Sandbox.

| Dimension        | Design                                                                      |
| ---------------- | --------------------------------------------------------------------------- |
| **Resource Isolation** | CPU / Memory / Disk (ephemeral) / Network (egress-only)               |
| **Security Boundary**  | FS (`/workspace/` `/input/` `/output/` `/secrets/`), Network whitelist, seccomp |
| **Warm Pool**          | Pre-created Sandboxes, <100ms acquisition                            |
| **Multi-Tenant Isolation** | L1: Process isolation (SaaS) → L2: Node isolation → L3: Cluster isolation (Finance/Government) |
| **Exploration Environment** | Lightweight Sandbox (DuckDB/Polars), sampled data                           |

### §7.1 State-Passing Mechanism

State passing between Jobs uses a **Reference-Based / Shared Volume** model — no data copying, only reference passing:

```
Job A (transform)                Job B (transform, depends_on: A)
  │                                │
  ├─ Write to: /output/job_a/      │
  │  (Parquet, partitioned)        │
  │                                │
  └──────── reference ────────────►│
           /output/job_a/          ├─ Read from: /input/job_a/ → symlink → /output/job_a/
                                   │  (zero-copy, same volume)
```

| Mechanism | Description |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **Same-Group Jobs** | Share ephemeral volume; references passed via symlink. Upstream Job writes to `/output/<job_id>/`, downstream Job reads via `/input/<upstream_job_id>/`. |
| **Cross-Group Jobs** | Intermediated via Object Store (S3/MinIO); upstream writes to Object Store, downstream reads via presigned URL or IAM role. |
| **Large Payloads (>1GB)** | Auto-degrade to Object Store passing to avoid volume overflow. |
| **Immutability** | Upstream output directory `chmod 555` before downstream begins reading; downstream cannot write to upstream output. |
| **Cleanup** | Ephemeral volume destroyed immediately upon Workflow completion; Object Store intermediate data cleaned per retention policy. |

## Dependencies

- **Warm Pool**: pre-created Sandboxes (process/container instances) kept hot so acquisition is <100ms.
- **Filesystem layout**: per-Job `/workspace/`, `/input/`, `/output/`, `/secrets/` directories; `/output/<job_id>/` is the canonical write location for same-group handoff.
- **Object Store (S3/MinIO)**: used for cross-group handoff and for >1GB payloads (auto-degrade). Presigned URLs or IAM roles grant downstream read access.
- **seccomp profile**: runtime enforcement layer that blocks network egress (except whitelisted endpoints), filesystem writes (except allowed directories), and process creation — even when static analysis passed.
- **AST analyzer (commit-time)**: parses Python and SQL at commit time; rejecting code cannot enter the Freeze Pipeline (see [`freeze-pipeline.md`](freeze-pipeline.md) §4).
- **Database user permissions**: defense-in-depth for SQL — SELECT-only on source schemas, limited INSERT/UPDATE on designated output schemas.
- **Audit Trail** ([`platform-core`](../platform-core/)): receives every Python code-review approval record and every SQL block (original + rewritten) with execution trace.
- **Incident Manager** ([`platform-core`](../platform-core/)): receives timeout-triggered incidents (Python Job SIGKILL, `wait` 72h timeout).

## Data Model

- **Sandbox descriptor** — acquired from the Warm Pool; carries resource quotas (CPU/Memory/Disk), an egress-only Network policy, the FS layout, and the seccomp profile.
- **Same-group handoff artifact** — Parquet partitioned dataset at `/output/<job_id>/`, exposed to downstream as a symlink at `/input/<upstream_job_id>/` (zero-copy, same ephemeral volume).
- **Cross-group handoff artifact** — Object Store object (S3/MinIO) addressed by presigned URL or IAM role; used for cross-Group Jobs and for payloads >1GB.
- **Immutability marker** — upstream `/output/` set to `chmod 555` before downstream reads begin.
- **Python code block** — parsed into an AST at commit time; carries import-whitelist compliance, forbidden-call absence (`eval`/`exec`/`compile`/`__import__`), and review-approval record.
- **SQL block** — paired original + rewritten forms, both logged to the Audit Trail with execution trace; carries AST validation result (allowed statements only).

## Failure Modes & Recovery

| Failure | Impact | Recovery |
| --- | --- | --- |
| Same-group ephemeral volume overflow (payload >1GB) | Volume full, write fails | Auto-degrade to Object Store passing (S3/MinIO) — upstream writes to Object Store, downstream reads via presigned URL/IAM role. |
| Downstream attempts to write upstream `/output/` | Data corruption risk | Prevented by immutability — upstream `/output/` is `chmod 555` before downstream begins reading. |
| Python code with forbidden import / `eval`/`exec`/`compile`/`__import__` / FS write outside `/output/` / network access | Code rejected | AST Static Analysis at commit time rejects the code; it cannot enter the Freeze Pipeline. |
| Python code with non-standard imports (no approval) | Blocked | Mandatory Code Review by Data Engineering Lead; approval record linked to Audit Trail before execution. |
| Python code passes static analysis but violates at runtime | Sandbox escape attempt | seccomp profile blocks network egress (except whitelist), FS writes (except allowed dirs), and process creation at runtime. |
| Python Job exceeds 30min (Design) / 4h (Runtime) | Hung Job | Timeout → SIGKILL → Incident created. |
| SQL block with non-parameterized user input | Injection risk | Rejected at Spec validation — inline string concatenation with user-supplied values is rejected; parameterized queries (`$1`, `$2`, `:param_name`) mandatory. |
| SQL with DROP/ALTER/TRUNCATE/GRANT or system-catalog subquery or non-allowlist UDF | Dangerous SQL | SQL AST Validation rejects; only SELECT/INSERT/UPDATE/MERGE allowed. |
| Anomalous SQL pattern (deep JOIN, cartesian product, excessive row estimates) | Performance/data risk | Audit layer flags for automatic review. |

## Non-Functional Requirements

### §7.2 Python Execution Constraints

Python transforms executing in the Sandbox are subject to the following mandatory constraints:

| Constraint                | Mechanism                                                                                                                                                                                                                                                                                          |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Import Whitelist**      | Only pre-vetted modules allowed: `polars`, `pandas`, `numpy`, `scipy`, `scikit-learn` (prediction/inference only, training forbidden), `statsmodels`, `datetime`, `python-dateutil`, `pytz`, `json`, `math`, `re`, `collections`, `itertools`, `functools`, `typing`. Tenant Data Owners may apply for additional modules via whitelist extension (requires audit approval) |
| **AST Static Analysis**   | All Python code is parsed via AST at commit time: detects (a) forbidden imports, (b) `eval`/`exec`/`compile`/`__import__` calls, (c) filesystem writes (outside `/output/`), (d) network access (`socket`, `requests`, `urllib`). Violating code is rejected and cannot enter the Freeze Pipeline. |
| **Mandatory Code Review** | Any Python code block containing non-standard imports requires manual approval by the Data Engineering Lead. Approval records are linked to the Audit Trail. |
| **Sandbox Enforcement**   | Even if code passes static analysis, the Sandbox runtime blocks via seccomp profile: network egress (except whitelisted endpoints), filesystem writes (except allowed directories), and process creation. |
| **Timeout**               | Python Job maximum execution time = 30min (Exploration Environment) / 4h (Production Environment). Timeout → SIGKILL → Incident. |

### §7.3 SQL Injection Defense

SQL transform blocks in Compute Spec YAML are a potential injection vector. All SQL blocks pass through mandatory defenses:

| Defense Layer                       | Mechanism                                                                                                                                                                                                                                                       |
| ----------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Parameterized Queries**           | All `source` and `transform` SQL blocks must use parameterized queries (`$1`, `$2` or `:param_name`). Inline string concatenation with user-supplied values is rejected at Spec validation.                                                                     |
| **SQL AST Validation**              | SQL is parsed into an AST (using sqlparser-rs or equivalent). The AST is validated: (a) only SELECT/INSERT/UPDATE/MERGE statements allowed (no DROP/ALTER/TRUNCATE/GRANT), (b) no subqueries accessing system catalogs, (c) no UDF calls except from allowlist. |
| **Variable Injection Sanitization** | Variables and Parameters injected into SQL are type-checked and escaped according to their declared type. String variables are automatically quoted and escaped. Table/column names from Variables are validated against an allowlist of known identifiers.     |
| **Sandbox Enforcement**             | Even if SQL passes all above checks, the Sandbox's seccomp profile and database user permissions provide defense-in-depth: the DB user has SELECT-only on source schemas and limited INSERT/UPDATE on designated output schemas.                                |
| **Audit**                           | All SQL blocks (both original and rewritten) are logged with the execution trace. Anomalous SQL patterns (unusual JOIN depth, cartesian products, excessive row estimates) trigger automatic review flags.                                                      |

### §7 Sandbox — quantitative targets

- Warm Pool acquisition: **<100ms**.
- Multi-tenant isolation tiers: **L1** Process (SaaS) → **L2** Node → **L3** Cluster (Finance/Government).
- Python Job timeout: **30min** (Exploration Environment) / **4h** (Production Environment); timeout → SIGKILL → Incident.
- Large-payload auto-degrade threshold: **>1GB** → Object Store.
- Network policy: **egress-only** (whitelist enforced by seccomp).

## Key Flows

### §7.1 Same-Group Job state passing

```
Job A (transform)                       Job B (transform, depends_on: A)
  │                                       │
  ├─ Sandbox FS: /workspace/, /input/,    │
  │   /output/, /secrets/                 │
  │                                       │
  ├─ Write result → /output/job_a/        │
  │   (Parquet, partitioned)              │
  │                                       │
  ├─ chmod 555 /output/job_a/  ──┐        │
  │   (immutability before read) │        │
  └──────── reference ───────────┼──────► │
           /output/job_a/        │        ├─ /input/job_a/ → symlink → /output/job_a/
                                 │        │  (zero-copy, same ephemeral volume)
                                 │        │
                                 │        ├─ Read-only access (chmod 555 enforced)
                                 │        │
                                 └────────┴─ On Workflow completion:
                                              ephemeral volume destroyed
```

### §7.1 Cross-Group / large-payload handoff

```
Job A (Group 1)                        Job B (Group 2, depends_on Group 1)
  │                                       │
  ├─ payload > 1GB  OR  cross-Group       │
  │                                       │
  ├─ Write → Object Store (S3/MinIO)      │
  │                                       │
  └─ Issue presigned URL / IAM role ─────►├─ Read via presigned URL / IAM role
                                            (cross-volume, no shared ephemeral)

Cleanup: Object Store intermediate data cleaned per retention policy
         (ephemeral volume destroyed immediately on Workflow completion)
```

### §7.2 + §7.3 Code admission flow (commit-time → runtime)

```
Python / SQL code block (in Compute Spec YAML)
    │
    ▼
┌─────────────────────────────────────────────┐
│ COMMIT-TIME (Freeze Pipeline, §4)              │
│  • Python AST Static Analysis                │
│    – forbidden imports?                      │
│    – eval/exec/compile/__import__?           │
│    – FS write outside /output/?              │
│    – network access (socket/requests/urllib)?│
│  • SQL AST Validation                        │
│    – only SELECT/INSERT/UPDATE/MERGE?        │
│    – parameterized ($1/:param_name)?         │
│  • Mandatory Code Review (non-standard       │
│    imports → Data Eng Lead approval → Audit) │
│  REJECTED code cannot enter Freeze Pipeline    │
└──────────────────────┬──────────────────────┘
                       │ passes
                       ▼
┌─────────────────────────────────────────────┐
│ RUNTIME (Sandbox, §7)                        │
│  • Acquire Sandbox from Warm Pool (<100ms)   │
│  • seccomp profile:                          │
│    – network egress (whitelist only)         │
│    – FS writes (allowed dirs only)           │
│    – process creation blocked                │
│  • DB user: SELECT-only on source schemas,   │
│    limited INSERT/UPDATE on output schemas   │
│  • Timeout: Python 30min (Design) / 4h (Run) │
│    → SIGKILL → Incident                      │
│  • Audit: SQL original + rewritten logged    │
└─────────────────────────────────────────────┘
```

### Shared runtime sequence

The Sandbox is the execution substrate shown end-to-end in [`../_shared/sequence-diagrams.md`](../_shared/sequence-diagrams.md): the Freeze Pipeline's Test Runner acquires a Sandbox from the Warm Pool (step 17–18 of **§21.1 Freeze Flow: Full End-to-End**), and the Runtime Executor dispatches each Job to a Sandbox under failure in **§21.2 Runtime Execution with Failure**.

## Design References

- **Original sections**: §7 (Execution Sandbox), §7.1 (State-Passing Mechanism), §7.2 (Python Execution Constraints), §7.3 (SQL Injection Defense) of [`docs/03-architecture.md`](../../03-architecture.md).
- **Related workflow-engine docs**: [`compute-spec.md`](compute-spec.md) (§6 — the Job Types that execute inside the Sandbox), [`freeze-pipeline.md`](freeze-pipeline.md) (§4 — the Test Runner uses the Sandbox for dry-runs), [`design-artifact.md`](design-artifact.md) (§3.3 — the artifact whose Python/SQL blocks are scanned).
- **Shared sequence diagram**: [`../_shared/sequence-diagrams.md`](../_shared/sequence-diagrams.md) §21.1 Freeze Flow (Test Runner → Warm Pool) / §21.2 Runtime Execution with Failure.
- **ADRs** ([index](../../adr-index.md)): [ADR-0025 Unified Workflow Engine](../../../adr/0025-unified-workflow-engine.md) (one engine, three environments — Sandbox serves all), [ADR-0005 Four-Layer Architecture](../../../adr/0005-four-layer-architecture.md) (Zero AI Side Effects — the security boundary enforces it).
- **Glossary** ([../../glossary.md](../../glossary.md)): Execution Sandbox, Warm Pool, Multi-Tenant Isolation (L1/L2/L3), seccomp, State-Passing Mechanism, Import Whitelist, AST Static Analysis, SQL AST Validation.
- **Cross-references retained from source**: §22 (MCP infrastructure — `llm_reasoning` Jobs route through MCP, orthogonal to Sandbox compute); §6.2 (Common Compute Subset — Python transform portability that the Sandbox runtime enforces).
