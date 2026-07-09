---
id: ADR-0002
title: "LLM Role Positioning"
status: accepted
date: 2026-07-04
deciders: "Project Sponsor"
domain: Architecture
---

# ADR-0002: LLM Role Positioning

- **Status**: Accepted
- **Date**: 2026-07-04
- **Deciders**: Project Sponsor

## Context

LLMs suffer from drift/distortion problems (unreliable reasoning). Invoking an LLM for every task leads to cost explosions, and LLM success rates for guessing/inferring structured data are limited (accuracy approximately 60–70%, dropping below 50% for complex business definitions).

At the same time, users clearly need AI-assisted efficiency — purely manual operations do not align with the "AI-Era BI" product vision. A balance must be found between AI efficiency and deterministic reliability.

## Options Considered

### Option A: Human-Only (Rejected)
All operations performed entirely by humans.
- **Pro**: 100% determinism, no compliance risk
- **Con**: Low efficiency, cannot realize the "AI-Era BI" vision

### Option B: AI-Only / Full Auto (Rejected)
All operations performed automatically by AI.
- **Pro**: Extreme efficiency
- **Con**: AI hallucinations lead to erroneous decisions; unacceptable compliance risk in industries such as finance and healthcare; invoking an LLM for every execution causes cost explosion

### Option C: Hybrid with Human Gate (Chosen)
AI assists during the exploration/design phase, with human approval retained at key decision points; Runtime Plane has zero AI side effects (production execution does not invoke LLMs; Intelligence Plane provides read-only AI analysis, temporary answers do not cross the bridge).
- **Pro**: AI efficiency + human controllability, balancing speed and reliability
- **Con**: Requires building a complete approval workflow and Freeze Bridge; improper design of the human-machine boundary can lead to a fragmented user experience

## Decision

Adopt **Option C** (Hybrid Mode): Daily operations completed automatically by Agents; key decision points (definition of business metrics, Adjustment approval, Workflow freezing) retain human approval. LLMs assist exploration in the Design Plane; Runtime Plane has zero AI side effects (Intelligence Plane provides read-only AI analysis).

## Rationale

1. **"LLMs are suited for exploration, not production"** is the core insight of the entire design — the exploration phase requires flexibility and breadth, while the production phase requires determinism and reliability.
2. The human-machine hybrid model has been validated in domains such as autonomous driving (L2/L3 levels) and medical diagnosis (AI-assisted + physician confirmation).
3. Building the approval workflow is a one-time cost that provides a safety guardrail for all subsequent AI features.

## Consequences

- **Positive**: Clear AI responsibility boundaries, auditable (can prove to auditors that "AI did not participate in production decisions"); controllable costs (zero LLM invocations after freezing).
- **Negative**: Requires building a complete approval workflow and Freeze Bridge; users need to understand and trust the human-machine boundary.
- **Neutral**: Over-reliance on human approval may create bottlenecks — mitigate by automating mechanical steps in the approval process via Skill chains (e.g., Schema validation, DQ Gate), leaving only decision points that truly require judgment to humans.

## Linked Modules

- `docs/02-requirement.md` → FR2 (Workflow Freeze), FR29 (AI Agent Architecture)
- `docs/03-architecture.md` → §1 (Core Design Philosophy)
- `adr/0005-four-layer-architecture.md` → Decision #2 (Four-Layer Architecture / Separation of Concerns)
