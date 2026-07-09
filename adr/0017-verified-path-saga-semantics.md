---
id: ADR-0017
title: "Verified Path — Saga Semantics & Durable Execution"
status: accepted
date: 2026-07-04
deciders: "Project Sponsor"
domain: Architecture
---

# ADR-0017: Verified Path — Saga Semantics & Durable Execution

- **Status**: Accepted
- **Date**: 2026-07-04
- **Deciders**: Project Sponsor

## Context

ADR-0016 defined Dual-Mode Agent orchestration — Exploration Mode (LLM free orchestration) and Verified Path Mode (fixed step sequence). However, Verified Path only defined the success path, not system behavior on failure:

1. If a 5-step Path times out at Step 3 — what happens to the completed outputs of Steps 1-2?
2. After the user fixes the issue, should execution resume from Step 3 or restart from Step 1? Resuming may have stale upstream inputs; restarting may produce duplicate side effects
3. SOX audit asks "Why wasn't this Path completed?" — the system needs to provide a deterministic, immutable answer

Industry best practice (Stripe/PayPal-grade architecture, 2025) answers with three pillars: **Saga compensation + idempotency + durable execution**. No need for heavy engines like Temporal/Cadence — achievable with existing PostgreSQL + Redis.

## Options Considered

### Option A: Best-Effort Cleanup (Rejected)
Best-effort cleanup of side effects on failure, no guarantees.
- **Pro**: Simplest implementation
- **Con**: Orphaned state (drafts, uncleaned locks) causes data pollution; audit cannot trace

### Option B: Saga + Idempotency + Durable Execution (Chosen)
Each Step has a forward action + compensating action. Compensation executes in reverse order. Idempotency Key guarantees safe re-execution. Durable storage ensures crash recovery.

### Option C: Full Temporal/Cadence Engine (Rejected for MVP)
Introduce a dedicated workflow engine.
- **Pro**: Most complete state management and observability
- **Con**: Operational complexity — adds a stateful distributed system. MVP-stage Path count (6) and invocation frequency (tens per day) don't justify it

## Decision

Adopt **Option B** (Saga + Idempotency + Durable Execution), based on existing infrastructure.

### Saga Semantics (Reverse-Order Compensation)

Each Verified Path Step registers compensation **before** executing the forward action:

```
Step N executes:
  1. register_compensation(step_N, comp_fn)    # register before forward
  2. execute_forward(step_N)                    # execute
  3. persist_result(step_N, output_hash)        # persist result

Step N+1 fails:
  for i = N down to 1:                          # reverse order
    execute_compensation(step_i)
    # compensation is idempotent — safe to retry
```

**Compensation Operations Declaration** (carried by each Skill):

| Skill | Forward Effect | Compensation | Idempotency Check |
|---|---|---|---|
| S09 ReconBreakAnalyzer | Read-only | noop | — |
| S02 KBRetriever (Exploration) | Read-only | noop | — |
| S02 KBRetriever (Verified Path) | Write KB draft | `delete_draft(kb_entry_id)` | `SELECT status FROM kb_entries WHERE id = ? → already deleted?` |
| S04 ImpactAnalyzer | Read-only | noop | — |
| S05 SpecGenerator | Write draft Spec / Form | `delete_draft(artifact_id)` | `SELECT status FROM design_artifacts WHERE id = ? → already deleted?` |
| GATE L3_REMEDIATION | Write approval_request | `mark_voided(approval_id, reason)` | `SELECT status FROM approvals WHERE id = ? → already voided?` |

**Key Constraint**: GATE compensation does not delete approval records — marks as voided. Approval records are part of the immutable audit trail.

### Idempotency

Each Path execution instance carries a deterministic idempotency key:

```
idempotency_key = "{path_id}_{date}_{entity_id}"

Examples:
  VP-001_20260706_recon_042        # Create Adjustment from Recon #42
  VP-002_20260706_rule_017         # Modify DQ Rule #17
  VP-004_20260706_glossary_003     # Modify Glossary #3
```

**Idempotency Guarantee Levels**:

| Level | Mechanism | Storage |
|---|---|---|
| Path Level | Same key Path instance executes only once. Replay → return cached result | Redis `SET NX {key} {status} EX 86400` |
| Step Level | Before each step, check if `{key}_step{N}` already completed. Completed → skip, return cached output_hash | Redis + PG dual-write |
| Skill Level | Each Skill's mutation carries idempotency token; Skill internally checks if already executed | PG `INSERT ... ON CONFLICT (idempotency_token) DO NOTHING` |

**Significance of Deterministic Key Generation** (non-random UUID): System crash replay — same Path + same entity + same day → same key → idempotent recovery.

### Durable Execution

Path execution state persisted in PostgreSQL `verified_path_executions` table:

```sql
CREATE TABLE verified_path_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    path_id VARCHAR(64) NOT NULL,          -- "VP-001"
    idempotency_key VARCHAR(256) UNIQUE NOT NULL,
    status VARCHAR(32) NOT NULL,            -- running | compensating | completed | rejected | aborted | dlq
    current_step INT DEFAULT 1,
    context JSONB NOT NULL,                 -- tenant, user, input parameters
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE verified_path_step_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID REFERENCES verified_path_executions(id),
    step_number INT NOT NULL,
    skill_id VARCHAR(16) NOT NULL,
    event_type VARCHAR(32) NOT NULL,        -- forward_started | forward_completed | forward_failed | compensation_started | compensation_completed | compensation_failed
    output_hash VARCHAR(64),                -- SHA-256 of step output
    error_details JSONB,
    event_at TIMESTAMPTZ DEFAULT now()
);
```

**Crash Recovery**: After Agent Runtime restart, scan Paths with `status = running` → resume from `current_step` → check idempotency key before each step → skip if already completed.

### DLQ (Dead Letter Queue)

Compensation failure (after 3 retries) → enters DLQ:

```
Compensation failed after 3 retries:
  1. Write to dlq_entries table
  2. Create Incident → PagerDuty "Verified Path compensation failed"
  3. Escalate to Data Owner (manual cleanup of residual state)
  4. Path status → dlq

DLQ Handling:
  - Data Owner manually cleans up residuals (e.g., delete orphaned draft)
  - After confirming cleanup → manually mark DLQ entry resolved
  - Periodic scan of unresolved DLQ → weekly summary report
```

### Verified Path State Machine (Complete)

```
┌─────────┐  step-by-step  ┌──────────┐  Step N fails  ┌──────────────┐
│ running │───────────────→│ running  │───────────────→│ compensating │
└─────────┘                └──────────┘                └──────┬───────┘
                                  │                          │
                                  │                          ▼
                                  │                  Reverse-order compensation
                                  │                  3 retries/step, exponential backoff
                                  │                          │
                                  │                   ┌──────┴──────┐
                                  │                   │ All comp OK? │
                                  │                   └──────┬──────┘
                                  │                     │        │
                                  │                    Yes      No
                                  │                     │        │
                         All steps done                 ▼        ▼
                                  │               ┌────────┐ ┌──────┐
                                  ▼               │aborted │ │ DLQ  │
                        ┌─────────────────┐       └────────┘ └──────┘
                        │ awaiting_gate   │              ↑
                        └────────┬────────┘      After manual cleanup
                                 │                manually resolve
                        ┌────────┴────────┐
                        │                 │
                        ▼                 ▼
                  ┌───────────┐    ┌───────────┐
                  │ completed │    │ rejected  │
                  └───────────┘    └───────────┘
```

**Audit Event Stream Example** (VP-001 Step 3 timeout):

```
path_execution_id: vp-001_20260706_0042
events:
  - { step: 1, skill: S09, event: forward_completed, output_hash: "a1b2...", ts: 10:00:01 }
  - { step: 2, skill: S02, event: forward_completed, output_hash: "c3d4...", ts: 10:00:15 }
  - { step: 3, skill: S04, event: forward_failed, error: "timeout_30s", ts: 10:00:45 }
  - { step: 2, skill: S02, event: compensation_completed, status: noop, ts: 10:00:46 }
  - { step: 1, skill: S09, event: compensation_completed, status: noop, ts: 10:00:46 }
  - { path_status: aborted, reason: "Step 3 (S04 ImpactAnalyzer) timeout after 30s", ts: 10:00:46 }
```

SOX audit value: Can prove "After Step 3 timed out, the system cleaned up Step 2 and Step 1 side effects in reverse order. No residual state."

## Rationale

1. **Saga is the industry standard for financial systems**: Stripe, PayPal, Square all use Saga + idempotency for distributed transactions. Compensation rather than 2PC — because 2PC is unreliable across services
2. **Idempotency is the safety net**: Network packet loss, timeout retries, crash recovery — without idempotency, every failure is a data pollution risk
3. **No need for heavy engines**: MVP has 6 Paths, tens of invocations daily — PG + Redis is sufficient. Temporal's operational cost is not justified. Reassess migration when Path count exceeds 50 and daily invocation exceeds thousands (Phase 7+)
4. **Reverse compensation cannot be simplified**: If Step 5 fails and only Step 5 is cleaned up without Step 4 — the system leaves an orphaned draft. Reverse-order compensation ensures complete rollback

## Consequences

- **Positive**: Failure paths are auditable, recoverable, with no residual state; idempotency eliminates duplicate execution risk; audit event streams satisfy SOX compliance
- **Negative**: Each Skill needs to declare compensation operations (increases development cost); Path execution adds idempotency check latency (~5ms Redis query per step)
- **Neutral**: DLQ requires manual intervention for cleanup — this is by design, not a defect. Auto-cleaning residual state is unsafe in financial systems

## Linked Modules

- `docs/03-architecture.md` → §22H (Verified Path Catalog — Saga state machine + compensation table)
- `docs/03-architecture.md` → §22A (Agent SDK — durable execution + idempotency layer)
- `adr/0016-dual-mode-agent-orchestration.md` → Dual-Mode Orchestration (this ADR supplements its failure semantics)
- `adr/0015-agent-triage-remediation-gateway.md` → L0-L3 Remediation Gateway (GATE compensation approval record handling)
