# ADR-0021: Verified Path Promotion & Multi-Agent Concurrency Control

- **Status**: Accepted
- **Date**: 2026-07-04
- **Deciders**: Architecture Team
- **Domain**: Architecture

## Context

Two independent but related problems:

**Problem 1 — VP Promotion**: The current VP Catalog has only 6 manually-defined Verified Paths. Skill sequences repeatedly validated as effective by users in Exploration Mode should be promotable to Verified Paths. But financial compliance (SOX) requires all change paths affecting financial data to follow SDLC.

**Problem 2 — Multi-Agent Concurrency**: Two users/Agents may simultaneously launch conflicting operations on the same resource. For example: User A creates an Adjustment for GL Account X (VP-001 awaiting L3 approval), User B simultaneously creates another Adjustment for the same account (VP-003). Both approved → double adjustment. Also, semantic conflicts: Agent A relaxes DQ Rule threshold, Agent B simultaneously marks reports passing that rule as "reviewed."

## Options Considered

### Option A: All Paths Manually Defined (Rejected)
Every Verified Path must be manually authored, reviewed, and approved — no automated promotion from Exploration Mode.
- **Pro**: Maximum control; every path has explicit human sign-off; simplest from a compliance standpoint.
- **Con**: Does not scale — user-validated patterns never become reusable paths; high maintenance burden; discourages exploration-to-production flow.

### Option B: Auto-Promote All Validated Paths (Rejected)
Any Skill sequence validated as effective in Exploration Mode is automatically promoted to a Verified Path.
- **Pro**: Fastest path from exploration to production; zero manual overhead.
- **Con**: Unacceptable compliance risk — SOX requires SDLC for financial data changes; no production validation before promotion; could propagate flawed sequences.

### Option C: Risk-Graded Promotion + Shadow Period + Multi-Layer Concurrency (Chosen)
Promotion gated by risk level (Read-Only auto, Config-Modify admin, Data-Modify full SDLC), 30-day shadow validation, and three-layer concurrency control with priority preemption.
- **Pro**: Balances agility with compliance; shadow period catches real-world issues; three-layer concurrency prevents both double-adjustment and semantic conflicts.
- **Con**: Shadow period adds 30-day latency; priority preemption may starve low-priority operations.

## Decision

Adopt **Option C**: risk-graded VP promotion (Read-Only auto / Config-Modify Admin / Data-Modify full BRD+Jira SDLC) with Shadow Promotion (30-day silent production run), three-layer concurrency control (optimistic → pessimistic → semantic), priority preemption (Recon > Month-End Close > Ad-hoc), and VP non-diversion during execution.

### VP Risk-Graded Promotion
- Read-Only: auto-promote
- Config-Modify: Admin approval within platform
- Data-Modify: full BRD → Jira/Rally → dual approval SDLC

### Shadow Promotion
Candidate VP runs silently in production for 30 days. Success rate >95%, compensation rate <5%, rejection rate <10% → auto-generate Promotion Proposal.

### Three-Layer Concurrency Control
- L1: Optimistic lock (version CAS, default)
- L2: Pessimistic lock (PG Advisory Lock, hot resources)
- L3: Semantic conflict detection (Gateway pre-approval ResourceConflictCheck)

### Priority Preemption
Recon > Month-End Close > Ad-hoc. Higher-priority operations can preempt locks held by lower-priority ones.

### VP Non-Diversion
Follow-up questions during VP execution saved as Pending Questions. VP cannot be paused or forked. After completion, Agent proactively reminds user of unanswered questions.

## Rationale

1. **Risk-graded promotion balances agility and compliance**: Read-Only paths auto-promote for speed; Data-Modify paths follow full SDLC for safety.
2. **Shadow Promotion provides production validation**: 30-day silent run catches real-world issues before formal promotion.
3. **Three-layer concurrency covers the spectrum**: Optimistic for low-contention, pessimistic for hot resources, semantic for intent-level conflicts.

## Consequences

- **Positive**: Clear promotion path encourages Exploration-to-VP flow; three-layer concurrency prevents double-adjustment and semantic conflicts.
- **Negative**: Shadow Promotion adds 30-day latency to VP promotion; priority preemption may cause lower-priority operations to wait.
- **Neutral**: VP non-diversion ensures audit trail integrity but requires users to manage pending questions separately.

## Linked Modules

- `docs/03-architecture.md` → §22K (VP Promotion & Multi-Agent Concurrency)
- `adr/0016-dual-mode-agent-orchestration.md` → Verified Path Catalog
- `adr/0017-verified-path-saga-semantics.md` → Saga & Idempotency
