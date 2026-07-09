---
id: ADR-0020
title: "Agent Cost Governance & Model Degradation Detection"
status: accepted
date: 2026-07-04
deciders: "Architecture Team"
domain: Architecture / Operations
---

# ADR-0020: Agent Cost Governance & Model Degradation Detection

- **Status**: Accepted
- **Date**: 2026-07-04
- **Deciders**: Architecture Team
- **Domain**: Architecture / Operations

## Context

LLM Agent costs are fundamentally different from traditional APIs: costs are unpredictable. A user asking "help me look at this month's PnL anomalies" could consume 500 tokens or 50,000 tokens. Exploration Mode's ReAct Loop could trigger runaway cycles.

Additionally, LLM providers upgrade models and outputs for the same Prompt may change after upgrade, affecting Agent reasoning quality. A 2024 FinTech case: model upgrade caused Recon classification to systematically shift from "TIMING" to "MISSING," triggering massive unnecessary Adjustments.

Real industry incidents exist: $47K LangChain loop (4 Agent ping-pong over 11 days), 2.3M call retry storm, 442K tokens single burst. Layered cost governance and model upgrade verification mechanisms must be established.

## Options Considered

### Option A: Hard Token Cap (Rejected)
Single fixed token limit per request/tenant — exceeding the cap immediately denies service.
- **Pro**: Simple to implement and reason about; predictable worst-case cost.
- **Con**: Denies legitimate complex explorations; poor user experience when cap is hit mid-task; no graceful degradation path.

### Option B: Post-Hoc Cost Reporting (Rejected)
No real-time governance — log all costs and report periodically for manual review.
- **Pro**: Zero runtime overhead; simplest possible implementation.
- **Con**: Cannot prevent runaway costs before they occur; $47K LangChain loop would not be caught; reactive rather than proactive.

### Option C: Hierarchical Quotas + Tiered Enforcement + Loop Detection (Chosen)
Layered token budgets with progressive throttling (DEGRADE not DENY), circuit breakers for runaway loops, and CI-based model upgrade validation.
- **Pro**: Graceful degradation preserves availability; loop detectors catch runaway patterns; model validation prevents silent regressions.
- **Con**: More complex to implement and tune; requires ongoing quota administration.

## Decision

Adopt **Option C**: hierarchical Token quotas with tiered enforcement (DEGRADE not DENY), three loop detectors with Circuit Breaker, four-stage model deployment funnel with auto-rollback triggers, and CI Regression Gate validating model upgrades on Golden Dataset.

### Hierarchical Token Quota
Organization → Tenant → User → VP/Exploration nested budgets, Admin-configured.

### Tiered Enforcement
50% WARN → 75% THROTTLE → 85% DEGRADE (auto-downgrade to cheaper model) → 90% CRITICAL → 100% KILL. Core principle: DEGRADE rather than DENY.

### Three Loop Detectors
- Identical-Call: repeated identical inputs
- Ping-Pong: mutual invocation between agents
- Context-Growth: context window bloat
Any trigger → Circuit Breaker.

### Four-Stage Model Deployment Funnel
Shadow (0% users) → Canary (1-5%) → Percentage (10→50%) → Full (100%). Each stage armed with auto-rollback triggers.

### Auto-Rollback Triggers
- guardrail_trip_rate > 1.5x baseline
- rubric_regression > -0.5pt
- p99_latency > 1.3x baseline
- new_error_cluster detected

### CI Regression Gate
Model upgrade validated on Golden Dataset before deployment; blocked on any dimension degradation.

## Rationale

1. **Cost unpredictability is the #1 operational risk for LLM agents**: Without hierarchical quotas, a single exploration could consume the monthly budget.
2. **Model upgrades are silent breaking changes**: Provider-side changes need systematic detection, not post-hoc debugging.
3. **DEGRADE not DENY ensures availability**: Users get degraded but functional service instead of hard failures.

## Consequences

- **Positive**: Cost predictability via hierarchical quotas; systematic model upgrade validation; graceful degradation preserves user experience.
- **Negative**: Quota management adds operational complexity; model deployment funnel extends upgrade cycle time.
- **Neutral**: Loop detectors may produce false positives — logged and reviewed, not auto-punitive.

## Linked Modules

- `docs/03-architecture.md` → §22K (Agent Cost Governance & Model Degradation Detection)
- `adr/0018-agent-evaluation-framework.md` → Golden Dataset used by CI Regression Gate
- `docs/glossary.md` → Tiered Enforcement, Loop Detection, Four-Stage Rollout Funnel, Auto-Rollback
