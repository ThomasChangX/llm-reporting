# ADR-0006: Freeze Bridge Independence

- **Status**: Accepted
- **Date**: 2026-07-04
- **Deciders**: Project Sponsor

## Context

AI-assisted artifacts need to be converted into deterministic scripts, but this conversion process is not simply "compilation" — disambiguation of fuzzy nodes requires human judgment, while testing/validation/approval/canary rollout requires a complete CI/CD process.

The architectural positioning of the Freeze Bridge must be clarified: is it a feature of the Design Plane? A pre-processing step of the Runtime Plane? Or an independent plane?

## Options Considered

### Option A: As Design Plane Export Feature (Rejected)
Freeze Bridge as an "Export" button within the Design Plane.
- **Pro**: Simple implementation, short user operation path
- **Con**: Confuses the responsibility boundary between AI exploration and deterministic conversion; cannot execute independent CI/CD processes (testing, approval, canary rollout); the semantics of "export" imply a single-step operation, when in reality multiple rounds of review are needed

### Option B: As Runtime Plane Pre-Processing Step (Rejected)
Freeze Bridge as a pre-processing step of the Runtime Plane.
- **Pro**: Close to the execution environment; testing and validation can use production-grade infrastructure directly
- **Con**: Makes Runtime Plane dependent on the AI-assisted Spec Refinement Assistant, blurring the "Runtime Zero AI Side Effects" boundary; Runtime Plane deployment and scaling strategies are unsuitable for Freeze Bridge's interactive review process

### Option C: As Independent Plane (Chosen)
Freeze Bridge as an independent plane between Design Plane and Runtime Plane.
- **Pro**: Clear architectural boundaries; independent CI/CD process; all disambiguation decisions for fuzzy nodes are immutably recorded
- **Con**: Adds an architectural layer — four layers rather than three

## Decision

Adopt **Option C**: Freeze Bridge as an independent plane. Core principle: **No automatic compilation** — instead, scan fuzzy nodes → propose deterministic solutions (1–3 alternatives, with confidence scores and impact analysis) → **mandatory human Sign-off** (no automatic compilation path exists) → validation (Schema check + DQ Gate) → testing (Sandbox Snapshot comparison) → generate Impact Report → approval → canary rollout.

The MVP phase adopts a simplified process (human Sign-off → validation → testing → direct rollout); canary gradual rollout (1%→10%→50%→100%) goes live in Post-MVP alongside the Heavy Engine.

Freezing is reversible: at any time one can "unfreeze" to return to exploration mode, modify, and re-freeze.

## Rationale

1. **"No automatic compilation path exists"** is the most critical safety constraint — any fuzzy node in AI artifacts (e.g., "appropriate aggregation function," "reasonable JOIN path") must have the final decision made by a human.
2. CI/CD processes (testing, approval, canary rollout) are hard requirements for production-grade systems — if Freeze Bridge is not an independent plane, these processes have nowhere to reside.
3. Immutable approval records are the foundation of SOX compliance — Freeze Bridge as an independent plane ensures all approval decisions are completely recorded and tamper-proof.

## Consequences

- **Positive**: Clearly defines the responsibility boundary for AI→deterministic conversion; immutable approval records support auditing; independent CI/CD process can reuse standard DevOps toolchains.
- **Negative**: Adds an architectural layer (the Freeze Bridge as a separate layer between Design and Runtime); human approval may become a bottleneck — mitigated by parallel processing of multiple Freeze requests and automatic routing to the appropriate Approver.
- **Neutral**: Canary gradual rollout is not enabled in the MVP phase — this simplifies initial implementation but means MVP users must accept the risk of "full rollout."

## Linked Modules

- `docs/03-architecture.md` → §4 (Freeze Bridge)
- `docs/02-requirement.md` → FR2 (Workflow Freeze), FR28 (Change Intelligence)
- `adr/0005-four-layer-architecture.md` → Decision #2 (Four-Layer Architecture / Separation of Concerns)
