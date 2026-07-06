# ADR-0009: Dual-Model Pricing Strategy

- **Status**: Accepted
- **Date**: 2026-07-05
- **Deciders**: Project Sponsor

## Context

LLM costs are a major operational expense for the system. Different regional customers have different price sensitivities (China market is highly cost-sensitive; US market prioritizes capability), and different tasks have different model capability requirements (simple NL→SQL translation vs. complex multi-step reasoning for architecture design).

A single model cannot simultaneously satisfy both the cost-sensitive market (China) and the capability-first market (US).

## Options Considered

### Option A: Single Global Model (Rejected)
Use one model globally.
- **Pro**: Simple operations, only one model integration to maintain
- **Con**: China customers are sensitive to latency and compliance of overseas models (e.g., Claude) due to data residency requirements; US customers have trust and ecosystem acceptance concerns with domestic models (e.g., DeepSeek); cannot differentiate between cost and capability

### Option B: Customer Self-Selection (Rejected)
Allow customers to fully choose and configure models themselves.
- **Pro**: Maximum flexibility
- **Con**: Increases operational complexity — N model integrations to maintain; customers may choose inappropriate models for their scenarios leading to poor experience; initial focus should be on a few high-quality models rather than long-tail support

### Option C: Dual-Model Default + Tiered Override (Chosen)
China region defaults to DeepSeek V4 Pro, US region defaults to Claude Sonnet 5, with Tenant/Group/User three-tier model preference override.

## Decision

Adopt **Option C** (Dual-Model Default + Three-Tier Override):

| Market | Default Model | Decode Speed | Input Price | Output Price |
|--------|--------------|-------------|------------|-------------|
| **China** | DeepSeek V4 Pro | ~80 tps | $0.50/M | $2.00/M |
| **US** | Claude Sonnet 5 | ~80 tps | $3.00/M | $15.00/M |

**Selection Logic**:
- Cost-sensitive scenarios → DeepSeek V4 Pro (~14% of Sonnet 5's price, comparable generation speed)
- Complex multi-step reasoning (Tier 3-4 tasks) → Claude Sonnet 5 (stronger deep reasoning capability, potentially reducing iteration rounds)
- Sensitive data scenarios → configurable to use private deployment models only

**Configuration Hierarchy**:
- Tenant-level (default) → Group-level override → Individual-level override
- LLM SDK unified invocation layer abstracts model differences, pluggable switching

## Rationale

1. **DeepSeek V4 Pro's cost-performance advantage**: At ~14% of Claude Sonnet 5's price with comparable generation speed (~80 tps), suitable for large-scale parallel development (running multiple Sub-Agents simultaneously) and cost-sensitive production calls.
2. **Claude Sonnet 5's deep reasoning capability**: Stronger deep reasoning on complex multi-step tasks (Tier 3-4, such as architecture design, security modules, distributed systems), potentially reducing iteration rounds — even if per-invocation cost is higher, total cost may be lower.
3. **Regional compliance**: China customers may require data to stay within borders (using domestic models); US customers may have concerns about domestic model compliance certifications — dual-model default strategy addresses both compliance needs.
4. **SDK unified abstraction**: Future new models (e.g., GPT-5, Gemini 3) only need a new Adapter at the SDK layer, transparent to business logic.

## Consequences

- **Positive**: Cost flexibility — heavy reasoning tasks use Sonnet 5 (reduce iterations), high-frequency light tasks use DeepSeek V4 Pro (reduce unit cost); regionally compliance-friendly.
- **Negative**: Dual-model maintenance cost (Prompt adaptation, performance monitoring, cost tracking) higher than single-model.
- **Neutral**: A model routing layer may be needed in the future (auto-select model based on task complexity), but this would be over-engineering initially.

## Linked Modules

- `docs/04-timeline.md` (Token-Speed estimation based on dual-model parameters)
- `docs/05-cost.md` (Development and operational costs calculated per dual-model/dual-region)
- `docs/03-architecture.md` → §22A-22G (AI Agent Architecture)
