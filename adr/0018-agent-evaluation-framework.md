---
id: ADR-0018
title: "Agent Evaluation Framework"
status: accepted
date: 2026-07-04
deciders: "Architecture Team"
domain: Architecture
---

# ADR-0018: Agent Evaluation Framework

- **Status**: Accepted
- **Date**: 2026-07-04
- **Deciders**: Architecture Team
- **Domain**: Architecture

## Context

The current architecture has clearly defined Agent capability boundaries (Dual-Mode, Saga, Evidence Packet, Triage), but lacks a systematic evaluation framework to answer the fundamental question: **Is the Agent getting better or worse?**

Industry 2025-2026 consensus: evaluating Agents means evaluating the **entire execution trajectory** — every step from intent recognition to task completion. 78% of enterprises have AI Agent pilots, but fewer than 15% reach production scale, primarily because evaluation pipelines haven't kept pace.

In financial compliance scenarios, "users feel it works" is not sufficient — measurable, auditable quality metrics are required.

## Options Considered

### Option A: User Feedback Only (CSAT/NPS)
- User satisfaction ≠ result correctness (user may be satisfied with a wrong answer)
- No objective measurement, not audit-usable
- **Rejected**

### Option B: Single LLM Output Evaluation (Traditional Benchmark)
- Static tests like MMLU/GAIA cannot cover multi-step Agent trajectories
- Cannot evaluate Agent-specific behaviors like tool selection, error recovery
- **Rejected**

### Option C: Six-Dimension Trajectory Scoring + Evaluation Flywheel (Amazon/Future AGI/NVIDIA 2025-2026 pattern)
- Six dimensions covering full Agent behavior
- Evaluation flywheel closing the production feedback → test set loop
- **Chosen**

## Decision

### Six-Dimension Trajectory Scoring System

Each Agent execution (VP or Exploration) is scored across six dimensions:

| Dimension | What It Measures | Scoring Method |
|-----------|-----------------|----------------|
| **1. Task Completion** | Was the user's intent ultimately resolved? | LLM-as-Judge + human-annotated ground truth |
| **2. Tool Selection** | Were the right tools selected? Was "none" selected when appropriate? | Comparison against optimal tool invocation sequence |
| **3. Argument Accuracy** | Are tool parameters schema-valid and semantically correct? | Deterministic checks + LLM semantic judgment |
| **4. Result Utilization** | Was tool-returned data used, or was it fabricated? | Cross-validate Evidence Packet supporting_evidence against tool output |
| **5. Plan Coherence** | No loops, no dead ends, reasonable step depth? | Loop detector + step efficiency ratio (optimal steps / actual steps) |
| **6. Error Recovery** | On tool failure: retry/degrade/escalate rather than crash? | Saga compensation success rate + degradation path coverage |

### Scoring Pipeline

```
Execution Trace → Deterministic Checks (dimensions 3, 5 partial) → LLM-as-Judge (dimensions 1, 2, 4, 6) → Six-Dimension Score Report
```

**Principle: Deterministic checks first, LLM-as-Judge supplementary.** Schema validation, parameter type checking, and loop detection are faster and cheaper than LLM Judge — run first. LLM Judge is only used for semantic correctness. The Judge model must be from a different model family than the Agent model (e.g., Agent uses DeepSeek, Judge uses Claude Haiku).

### Compound Error Tracking

```
Single-step 95% success rate → 8-step chain end-to-end ≈ 0.95^8 ≈ 66%
```

Per-step scoring + end-to-end scoring cross-analysis. per-step all-green but end-to-end red → compound error alert. This is the most common production Agent failure pattern.

### Evaluation Flywheel

```
Offline Eval → Deploy → Online Monitoring → Failure Analysis → Expand Golden Dataset → Agent Optimization → Repeat
                    ↑
            Every production failure permanently converted into a regression test
```

**Core principle: The same error should never happen twice.**

### Golden Dataset Management

- **Sources**: Production Execution Traces (especially cases with compensation/rejected by Gateway) + hand-crafted boundary cases
- **Annotation**: Human-annotated ground truth (optimal Skill sequence + expected output)
- **Versioning**: Immutable; each new case produces a new version
- **Per-VP Organization**: Each VP has its own Golden Dataset subset
- **CI Gate**: On Model upgrade/Agent code change, auto-run full Golden Dataset; any dimension degradation > threshold → block release

### Three-Layer Monitoring Dashboard

| Layer | What to Watch | Audience |
|-------|--------------|----------|
| **L1 Business KPIs** | Task Success Rate, User Satisfaction, Per-Task Cost | PM, Business Leads |
| **L2 System Health** | Per-VP/Exploration success rates, tool failure rates, hallucination rates, compound error rates | SRE, Engineering Team |
| **L3 Cost & Resources** | Daily consumption, model distribution, Token efficiency | FinOps, Admin |

### Evaluation Frequency

| Trigger | Evaluation Scope | Action |
|---------|-----------------|--------|
| **Every CI/CD** | Golden Dataset full | Degradation → block release |
| **Daily** | Past 24h production Executions sampled at 10% | Trend report |
| **Weekly** | Past 7 days full Executions | Six-dimension score trends + degradation alert |
| **Before Model Upgrade** | Golden Dataset full × old vs. new model comparison | Degradation → block upgrade |

## Rationale

1. **Six-Dimension Scoring covers full Agent behavior** — not just "did it answer correctly" but also "how did it answer." Financial compliance requires auditable reasoning chains.
2. **Deterministic checks first** — reduces Judge cost (~70% of checks don't need LLM), improves reproducibility.
3. **Compound Error Tracking** — this is the industry-recognized #1 killer of production Agents, must be made explicit.
4. **Evaluation Flywheel** — converts production incidents into permanent tests, gradually eliminating known failure modes.
5. **VP Catalog naturally fits** — fixed steps make per-VP Golden Dataset construction very precise.

## Consequences

- Need to develop Six-Dimension Scoring Engine (offline Job, Go/Rust implementation)
- Need to establish Golden Dataset annotation process (human + AI-assisted)
- LLM-as-Judge cost: ~$0.05-0.20 per evaluation (using low-cost Judge like Haiku)
- CI/CD adds ~5-10 minutes evaluation time (parallelizable)
- S08 Closed-Loop Learning signals feed into evaluation flywheel: false_positive marked cases directly added to Golden Dataset

## Linked Modules

- → docs/03-architecture.md §22I
- → docs/03-architecture.md §22A (Dual-Mode)
- → docs/03-architecture.md §22B S08 (Closed-Loop Learning)
- → adr/0016 (Dual-Mode Orchestration)
