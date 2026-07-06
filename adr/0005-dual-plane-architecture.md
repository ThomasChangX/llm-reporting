# ADR-0005: Four-Layer Architecture (Zero AI Side Effects)

- **Status**: Accepted (Refined 2026-07-05)
- **Date**: 2026-07-04
- **Deciders**: Project Sponsor

## Context

The core insight — "LLMs are suited for exploration, not production." Architecture-level physical isolation is needed to guarantee this principle, not merely process norms.

Specific challenges:
1. If AI and deterministic execution are mixed in the same plane, it is impossible to prove to auditors that "AI did not participate in production decisions."
2. If LLMs are invoked for every execution, costs are uncontrollable (even at $0.50/M input tokens, terabyte-scale data processing scenarios are infeasible).
3. The exploration phase requires AI's flexibility and breadth; the production phase requires determinism and reliability — the two have fundamentally different infrastructure requirements.
4. **(Added 2026-07-05)** Ad-hoc analysis needs (e.g., "Why did East China gross margin drop by 2 percentage points?") inherently require AI assistance to understand the data, but such AI invocations must not enter the production execution path. The correct boundary between "zero AI" and "AI-assisted analysis" must be found.

## Options Considered

### Option A: Single Plane + AI On/Off Switch (Rejected)
A single plane, controlling whether AI is invoked via a switch.
- **Pro**: Simple architecture, low development cost
- **Con**: Incomplete isolation — the AI switch could be accidentally turned on or bypassed; cannot prove to auditors that "AI did not participate in production decisions"; the switch state itself becomes a new attack surface

### Option B: AI Always-On + Human Approval Every Step (Rejected)
AI participates throughout but requires human approval at every step.
- **Pro**: Audit-controllable
- **Con**: Cost explosion — LLM invoked for every execution; approval fatigue — approval loses meaning under high-frequency operations; human approval becomes a bottleneck

### Option C: Four-Layer Architecture (Chosen)
Divided into four layers by **mutability**:

| Layer | AI Present? | Output | Mutability |
|---|---|---|---|
| **Design Plane** | Heavy AI | Persistent Artifacts (Compute Spec, BRD, ADR) | High — exploration, iteration |
| **Freeze Bridge** | AI-assisted validation | Signed deterministic Spec | Zero — freeze point |
| **Runtime Plane** | **Zero AI side effects** | Scheduled execution, materialized refresh, Pipeline output | Zero — deterministically executes Spec |
| **Intelligence Plane** | **Read-only AI** | Temporary answers (NL explanations, attribution analysis) | High — but **does not cross the bridge** |

- **Pro**: Clear separation of concerns; auditable AI boundaries; independent cost optimization and scaling; ad-hoc analysis needs satisfied by Intelligence Plane without compromising Runtime determinism.
- **Con**: Increased system complexity; inter-plane communication requires explicit protocols and boundaries.

## Decision

Adopt **Option C** (Four-Layer Architecture):

1. **Design Plane**: AI-assisted exploration; all operations are "design drafts" that produce no production side effects. Includes Conversation UI, Visual Designer, Workbench, AI Copilot Engine.
2. **Freeze Bridge**: An independent plane connecting Design Plane and Runtime Plane, responsible for converting AI exploration artifacts into deterministic scripts — scanning ambiguous nodes → proposing deterministic solutions → **mandatory human Sign-off**.
3. **Runtime Plane**: Deterministic execution, **zero AI side effects**. Includes Workflow Executor, Data Connectors, Output Renderer, Scheduler, Incident Manager. Executes frozen Compute Specs, does not invoke LLMs, all operations are reproducible and auditable.
4. **Intelligence Plane**: AI read-only analysis, **temporary answers do not cross the bridge**. Includes AI Knowledge Agent (ad-hoc NL Q&A, attribution analysis), Pre/Post-Change Impact Report, Observability & Log Analysis. Read-only queries, writes no state to any Plane — worst case is an incorrect answer, without polluting data or Pipelines.

**Core Principle Refinement**: From "Runtime Zero AI" → **"Runtime Zero AI Side Effects"**:
- AI may participate in read-only analysis (Intelligence Plane) but must not produce side effects.
- Ad-hoc questions → Intelligence Plane (AI query, temporary answer, zero side effects).
- User decides to freeze → Design Plane → Freeze Bridge → Runtime Plane (deterministic execution).

## Rationale

1. **Auditability**: Physical isolation between planes makes "AI did not participate in production decisions" a provable architectural property (rather than relying on process norms).
2. **Cost Isolation**: Design Plane LLM costs are billed per exploration count; Runtime Plane engine costs are billed per data volume — independently optimized without mutual interference.
3. **Fault Isolation**: Design Plane AI hallucinations do not affect Runtime Plane production data; Runtime Plane performance issues do not block Design Plane exploration; Intelligence Plane incorrect answers do not pollute any system state.
4. **Independent Scaling**: Design Plane requires low-latency AI inference; Runtime Plane requires high-throughput computation — the two have completely different scaling strategies.
5. **Ad-hoc Friendly**: Intelligence Plane resolves the tension between the "zero AI" principle and "users need AI assistance to understand data" — AI reads only, does not write, answers do not cross the bridge.

## Consequences

- **Positive**: Clear AI boundaries, auditable, independently optimizable costs; ad-hoc analysis needs satisfied by Intelligence Plane without compromising Runtime determinism.
- **Negative**: The four-layer architecture increases system complexity and operational costs (requires maintaining four different sets of infrastructure and monitoring).
- **Neutral**: As a read-only analysis layer, Intelligence Plane's data freshness depends on log push latency from the Design/Runtime Planes; AI-generated temporary answers are not persisted unless the user explicitly confirms and goes through the Design Plane process.

## Linked Modules

- `docs/03-architecture.md` → §2 (Panoramic Architecture), §3 (Four-Layer Model Details), §9 (Change Intelligence)
- `docs/02-requirement.md` → FR1-2, FR15b, FR15c, NFR1-2
- `adr/0006-freeze-bridge-independence.md` → Decision #6 (Freeze Bridge Independence)
