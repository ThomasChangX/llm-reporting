# Architecture Decision Records (ADR)

> This directory contains all Architecture Decision Records for the llm-reporting project.
> Using the [MADR](https://adr.github.io/madr/) (Markdown Any Decision Records) format.
>
> **Related Documents**: Summary index → `docs/01-facts.md` §Key Design Decisions | Architecture design → `docs/03-architecture.md`

## ADR Status Overview

| # | ADR | Domain | Status | Date |
|---|-----|--------|------|------|
| 0001 | [Product Evolution Path](./0001-product-evolution-path.md) | Product | ✅ Accepted | 2026-07-04 |
| 0002 | [LLM Role Positioning](./0002-llm-role-positioning.md) | Architecture | ✅ Accepted | 2026-07-04 |
| 0003 | [Design Order](./0003-design-order.md) | Process | ✅ Accepted | 2026-07-04 |
| 0004 | [Document Structure](./0004-document-structure.md) | Process | ⬜ Superseded by [0012](./0012-document-structure-v2.md) | 2026-07-04 |
| 0005 | [Four-Layer Architecture](./0005-four-layer-architecture.md) | Architecture | ✅ Accepted | 2026-07-04 |
| 0006 | [Freeze Bridge Independence](./0006-freeze-bridge-independence.md) | Architecture | ✅ Accepted | 2026-07-04 |
| 0007 | [Query Service Component](./0007-query-service-component.md) | Architecture | ✅ Accepted | 2026-07-04 |
| 0008 | [Large-Scale Data Strategy](./0008-large-scale-data-strategy.md) | Data | ✅ Accepted | 2026-07-04 |
| 0009 | [Dual-Model Pricing](./0009-dual-model-pricing.md) | Operations | ✅ Accepted | 2026-07-04 |
| 0010 | [BRD/ADR as First-Class Entities](./0010-brd-adr-first-class.md) | Product | ✅ Accepted | 2026-07-04 |
| 0011 | [Materialize Job Type](./0011-materialize-job-type.md) | Architecture | ✅ Accepted | 2026-07-04 |
| 0012 | [Document Structure v2](./0012-document-structure-v2.md) | Process | ✅ Accepted | 2026-07-04 |
| 0013 | [KB Storage Strategy](./0013-kb-storage-strategy.md) | Architecture | ✅ Accepted | 2026-07-04 |
| 0014 | [Data Health Check Framework](./0014-data-health-check-framework.md) | Architecture | ✅ Accepted | 2026-07-04 |
| 0015 | [Agent Triage & Remediation Gateway](./0015-agent-triage-remediation-gateway.md) | Architecture | ✅ Accepted | 2026-07-04 |
| 0016 | [Dual-Mode Agent Orchestration](./0016-dual-mode-agent-orchestration.md) | Architecture | ✅ Accepted | 2026-07-04 |
| 0017 | [Verified Path Saga Semantics](./0017-verified-path-saga-semantics.md) | Architecture | ✅ Accepted | 2026-07-04 |
| 0018 | [Agent Evaluation Framework](./0018-agent-evaluation-framework.md) | Architecture | ✅ Accepted | 2026-07-04 |
| 0019 | [Agent Memory Architecture](./0019-agent-memory-architecture.md) | Architecture | ✅ Accepted | 2026-07-04 |
| 0020 | [Agent Cost Governance](./0020-agent-cost-governance.md) | Architecture / Operations | ✅ Accepted | 2026-07-04 |
| 0021 | [VP Promotion & Concurrency](./0021-vp-promotion-concurrency.md) | Architecture | ✅ Accepted | 2026-07-04 |
| 0022 | [BRD Generation Agent Pipeline](./0022-brd-generation-agent-pipeline.md) | Architecture | ✅ Accepted | 2026-07-04 |
| 0023 | [KB Content Lifecycle Pipeline](./0023-kb-content-lifecycle-pipeline.md) | Architecture | ✅ Accepted | 2026-07-08 |
| 0024 | [KB Reasoning Support — Playbooks & Code Knowledge](./0024-kb-reasoning-support-playbooks-code.md) | Architecture | ✅ Accepted | 2026-07-08 |

## Status Meanings

| Status | Description |
|------|------|
| `Proposed` | Proposed, awaiting discussion and approval |
| `Accepted` | Approved, currently in effect |
| `Deprecated` | Deprecated by subsequent ADR, no longer applicable |
| `Superseded` | Superseded by a new ADR (successor noted) |
| `Rejected` | Rejected after discussion (retained for record) |

## Format Description

Each ADR follows the MADR condensed format:

```markdown
# ADR-NNNN: Title

- **Status**: Accepted | Proposed | Deprecated | Superseded | Rejected
- **Date**: YYYY-MM-DD
- **Deciders**: [decision makers]

## Context
## Options Considered
## Decision
## Rationale
## Consequences
## Linked Modules
```

## Creating a New ADR

1. Take the next available number (`ls adr/ | sort`)
2. Copy any existing ADR (e.g., `0001-product-evolution-path.md`) as a template, or use the MADR format skeleton above
3. Fill in each section
4. Update this README's status overview table (including Domain classification)
5. Add a summary Decision entry in `docs/01-facts.md`
