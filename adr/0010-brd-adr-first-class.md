---
id: ADR-0010
title: "BRD/ADR as First-Class Entities"
status: accepted
date: 2026-07-04
deciders: "Project Sponsor"
domain: Product
---

# ADR-0010: BRD/ADR as First-Class Entities

- **Status**: Accepted
- **Date**: 2026-07-04
- **Deciders**: Project Sponsor

## Context

In traditional BI/software development, BRDs (Business Requirements Documents) and ADRs (Architecture Decision Records) are standalone Word/Wiki documents disconnected from actual Workflows, code, and data pipelines. This leads to:
- Inability to automatically trace impact scope when requirements change
- Architecture decision rationale being lost over time
- Broken traceability chains from business requirements to technical implementation

The user explicitly requested: "BRD, ADR, and other content generation should also be provided by this system."

## Options Considered

### Option A: External Document + Manual Linking (Rejected)
BRD/ADR continues as external documents (Confluence/SharePoint) with manual links added in the system.
- **Pro**: Lowest implementation cost
- **Con**: Links easily break; no automatic impact analysis; cannot leverage AI-assisted generation and verification

### Option B: Simple CRUD Entities in System (Rejected)
BRD/ADR as simple CRUD entities within the system.
- **Pro**: One step better than external documents, can have bidirectional links
- **Con**: Missing lifecycle management; missing AI-assisted generation and verification; no integration with external tools like Jira/Rally

### Option C: First-Class Entities with Full Lifecycle (Chosen)
BRD/ADR as first-class citizens at parity with Workflows, with complete lifecycle management, AI-assisted generation, and bidirectional traceability.

## Decision

Adopt **Option C**: BRD/ADR as system first-class citizens.

### BRD Lifecycle (16 states)
- **Core 9 states**: `draft` → `in_review` → `pending_fix` → `revised` → `approved` → `in_progress` → `implemented` → `verified` → `closed`
- **Extension flags**: `needs_revision`, `impact_pending`, `stale`, `on_hold`, `fast_track`, `requires_compliance_review`, `discussion_active`

### ADR Lifecycle (12 states)
- **Core 7 states**: `proposed` → `challenged` → `pending_validation` → `needs_revision` → `accepted` → `deprecated` → `superseded`
- Content is immutable after `accepted`

### AI-Assisted Generation
- **BRD Generation**: S15 BRDGenerator Skill → 6-round LLM deep verification (completeness/consistency/compliance/feasibility/impact/security) → human approval
  - **Refined**: S15 internal pipeline has been refined by ADR-0022 into a 6-Agent serial pipeline (BRD-IntentDeepener / ContextGatherer / VaguenessResolver / DraftWriter / Verifier / Assembler), introducing Inline AssumptionCheck, Experience Typology Tree, Suspect Flag, and other mechanisms. The AI-assisted generation + 6-round verification + human approval direction established by this ADR remains unchanged.
- **ADR Generation**: S16 ADRGenerator Skill → auto-draft ADRs from design discussions and architecture changes → human Review
- Verification does not block generation — Drafts are presented to the user first; verification results serve as auxiliary decision information

### External Tool Integration
- Jira/Rally multi-layer mapping: BRD→Epic/Feature, requirement→Story/US, AC→Sub-task/Task
- New MCPs: MCP-17 (jira-sync), MCP-18 (confluence-export), MCP-19 (compliance-mapper)
- Import capability: Legacy BRDs from Confluence/SharePoint/Word

### Full Traceability Chain
```
BRD → (justifies) → ADR
BRD → (decomposes_to) → Epic → Story → Compute Spec
ADR → (constrains) → Module → Compute Spec
Compute Spec → (implements) → Story → Epic → BRD
```

## Rationale

1. **Automated Impact Analysis**: BRD changes → auto-flag all affected Workflows → auto-generate Impact Report. This is impossible with traditional document systems.
2. **AI Verification Closed Loop**: LLM-assisted generated BRDs need to be verified — the 6-round verification pipeline covers comprehensive checks from syntax to security. Verification not blocking generation ensures user experience is not blocked.
3. **Jira/Rally Unidirectional Sync**: BRDs are not isolated documents — they sync to Jira Epic/Story. PR commits auto-update Jira Story status to Done.
4. **Intermediate States Support Real Workflows**: Intermediate states like `pending_fix`, `challenged`, `pending_validation` reflect real team collaboration processes — requirements often need multiple rounds of discussion and revision.

## Consequences

- **Positive**: Complete BRD→Workflow→Deployment traceability chain; AI-assisted generation + verification improves quality and efficiency; external tool integration (Jira/Rally/Confluence) reduces migration costs.
- **Negative**: The 16/12 state machine increases system complexity — state transition matrices must be carefully designed to prevent illegal transitions.
- **Neutral**: Added 3 Skills (S15 internally refined by ADR-0022 into 6 BRD Agents, S16, S17) and 3 MCPs (MCP-17-19), increasing AI Agent invocation complexity.

## Linked Modules

- `docs/02-requirement.md` → FR23 (BRD & ADR as First-Class Entities)
- `docs/03-architecture.md` → §23 (BRD & ADR as First-Class Entities, 10 sub-sections)
- `docs/01-facts.md` → BRD/ADR as First-Class Entities (summary)
- `adr/0022-brd-generation-agent-pipeline.md` → S15 Internal Pipeline Refinement (6-Agent Serial Pipeline)
