# ADR-0001: Product Evolution Path

- **Status**: Accepted
- **Date**: 2026-07-04
- **Deciders**: Project Sponsor (Finance/Accounting Domain Expert)

## Context

The product cannot cover all industries and roles in a single step. A progressive evolution path is needed — one that establishes core capabilities while reserving architectural space for future scaling.

## Options Considered

### Option A: Vertical Start → Horizontal Expansion (Chosen)
Start from financial accounting scenarios (Reporting + ETL + Adjustment), establishing domain depth and core capabilities. Then expand progressively along the path: Three-Tier Differentiation (Individual/Team/Enterprise) → Role Differentiation (Analyst/Operations/Executive) → Open Platform.

### Option B: Horizontal General Start
Start with a general-purpose data analysis tool targeting all industries simultaneously.
- **Pro**: Larger initial TAM
- **Con**: Lack of focus, unable to establish domain depth; difficult to balance feature breadth vs. depth

### Option C: Enterprise-Only
Target only large enterprise customers.
- **Pro**: High per-customer value
- **Con**: Long customer acquisition cycles (6–18 months), making rapid iteration and validation difficult; high cost to verify product-market fit

## Decision

Adopt **Option A**: Phase A (Financial Starting Point) → Phase B (Three-Tier Differentiation) → Phase C (Role Differentiation) → Phase D (Open Platform).

Phase A already embeds the multi-tenant foundation (all entities include `tenant_id`, RBAC framework, three-level isolation model), even though only single-tenant mode is exposed initially — avoiding expensive refactoring at Phase B.

## Rationale

1. **Domain Depth First**: Financial accounting scenarios cover the three core capabilities of Reporting, ETL, and Adjustment — among the most complex use cases for BI tools. Once product capabilities are validated in this scenario, the marginal cost of expanding to other industries is low.
2. **Rapid Iteration and Validation**: Focusing on a single domain allows a small team to quickly close the "develop → release → feedback" loop.
3. **Architectural Embedding**: Phase A embeds multi-tenancy, permission frameworks, and other foundational infrastructure upfront, avoiding the expensive refactoring of "build single-tenant first, retrofit multi-tenant later" — there are numerous failure cases of this pattern in the industry (e.g., Slack's failure to embed the Enterprise Grid architecture early led to years of refactoring).

## Consequences

- **Positive**: Clear early market positioning ("AI BI Tool for Financial Accounting"), well-defined target users, simple and compelling product narrative.
- **Negative**: Phase A total addressable market (TAM) is relatively small; sufficient domain reputation must be accumulated before Phase B.
- **Neutral**: Phases B/C/D require substantial architectural embedding (multi-tenancy, permission framework, plugin system), increasing Phase A's initial development cost but avoiding later refactoring.

## Linked Modules

- `docs/02-requirement.md` → FR12 (Multi-Tenancy)
- `docs/04-timeline.md` → Phase 0-8
- `docs/03-architecture.md` → §11 (RBAC), §7 (Execution Sandbox), §22F (Agent Multi-Tenant Isolation)
