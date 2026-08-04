# Experience Typology Tree & BRD Product Quality Assessment

> **Origin**: §23.11 and §23.12 of [`docs/03-architecture.md`](../../03-architecture.md) | **Sub-project**: [brd-adr-lifecycle](README.md)

## Purpose

This module covers two tightly coupled mechanisms that govern BRD *quality*:

1. **Experience Typology Tree** (§23.11) — the core data structure of BRD-VaguenessResolver (one of the six BRD generation sub-agents). It automatically induces a requirements dimension hierarchy tree from the tenant's own artifacts, guiding precise questioning and dimension pruning during BRD elicitation. Based on TypoAgent/OntoAgent (RE 2026).
2. **BRD Product Quality Assessment** (§23.12) — a four-dimension human-reviewer scoring rubric applied at approval time. This is *product* quality (the BRD itself), deliberately distinct from ADR-0018's six-dimension agent *trajectory* scoring.

Together they form a closed loop: the Typology Tree guides generation toward high-quality BRDs, and the four-dimension scores feed back into Typology Tree confidence and Golden Dataset expansion.

## Boundaries

**In-scope:**
- Typology Tree concept and its role as VaguenessResolver's core data structure (§23.11.1).
- The three-layer progressive construction: Schema-Driven Bootstrap (Layer 0) → BRD-Driven Refinement (Layer 1) → Cross-BRD Pattern Mining (Layer 2), including coverage and accuracy expectations (§23.11.2).
- Strict tenant isolation rules for the Typology Tree (§23.11.2).
- Typology Tree storage in `agent_semantic_memory` (§23.11.3).
- Degradation mechanism when tenant naming is irregular (§23.11.4).
- Distinction between product quality assessment and ADR-0018 agent trajectory scoring (§23.12.1).
- Four-dimension human reviewer scoring rubric — Clarity, Completeness, Feasibility, Compliance (§23.12.2) — and its downstream uses.

**Out of scope (delegated):**
- VaguenessResolver's questioning/pruning algorithms themselves → [`generation-pipeline.md`](generation-pipeline.md) (§23.5.1).
- Agent trajectory scoring (ADR-0018 six dimensions) → Agent Platform / evaluation framework ([`../../../adr/0018-agent-evaluation-framework.md`](../../../adr/0018-agent-evaluation-framework.md)).
- BRD lifecycle approval state transitions that host the scoring → [`lifecycle-state-machine.md`](lifecycle-state-machine.md).

## Interfaces

| Interface | Consumer | Contract |
|-----------|----------|----------|
| Typology Tree (read) — `typology_tree` facts in `agent_semantic_memory` | BRD-VaguenessResolver (S15 sub-agent) | Dimension hierarchy for a `brd_type`, used to guide precise questioning and dimension gating/pruning |
| Typology Tree (write) — Layer 0/1/2 construction | Onboarding, BRD close, pattern-mining batch | Inserts/updates `agent_semantic_memory` rows with `fact_type='typology_tree'` |
| Four-dimension scores (input) | Human approvers in Workbench | Approvers score 1–5 on Clarity, Completeness, Feasibility, Compliance at BRD approval |
| Four-dimension scores (output) | Typology Tree confidence updater, Golden Dataset curator | Drives Tree evolution weight and Golden Dataset failure-mode analysis |

## Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| **BRD-VaguenessResolver** (S15 sub-agent) | Hard | The Typology Tree exists to serve this agent's elicitation; defined in [`generation-pipeline.md`](generation-pipeline.md). |
| **`agent_semantic_memory` store** | Hard | Persistence target for Typology Tree facts; isolated by `tenant_id`. |
| **Data Source Schema** (table/column/DDL) | Hard (Layer 0) | Source for Schema-Driven Bootstrap at tenant onboarding. |
| **Approved BRDs** | Hard (Layer 1, Layer 2) | Layer 1 refines from each closed BRD; Layer 2 mines patterns across ≥3 BRDs of the same type. |
| **ADR-0022** | Hard | Redesigned the generation pipeline, including VaguenessResolver's use of the Typology Tree ([`../../../adr/0022-brd-generation-agent-pipeline.md`](../../../adr/0022-brd-generation-agent-pipeline.md)). |
| **ADR-0018** | Reference | Agent trajectory scoring framework; this module is deliberately distinct from it (§23.12.1) ([`../../../adr/0018-agent-evaluation-framework.md`](../../../adr/0018-agent-evaluation-framework.md)). |

## Data Model

### §23.11 Experience Typology Tree

> **Related**: → §23.5.4 (BRD-VaguenessResolver), → [`../../../adr/0022-brd-generation-agent-pipeline.md`](../../../adr/0022-brd-generation-agent-pipeline.md)

#### §23.11.1 Concept

Experience Typology Tree mechanism based on TypoAgent/OntoAgent (RE 2026). Typology Tree is VaguenessResolver's core data structure — automatically inducing a requirements dimension hierarchy tree from the tenant's own artifacts, guiding precise questioning and dimension pruning.

#### §23.11.2 Three-Layer Progressive Construction

| Layer | Trigger Condition | Data Source | Coverage | Accuracy |
|----|---------|----------|--------|--------|
| **Layer 0: Schema-Driven Bootstrap** | Tenant onboarding (immediate) | Data Source Schema (table names/column names/DDL comments) | 60-70% dimensions | Medium (depends on column name quality) |
| **Layer 1: BRD-Driven Refinement** | Each BRD closed | Dimension structure extracted from that BRD YAML | +10-15% / BRD | High (from approved BRD) |
| **Layer 2: Cross-BRD Pattern Mining** | ≥3 BRDs of the same type | Cross-BRD pattern induction | Standardized template | Highest (validated commonality) |

**Strict Tenant Isolation**:
- Typology Tree stored in `agent_semantic_memory`, isolated by `tenant_id`
- All dimensions sourced from tenant's own Schema + own BRDs
- No cross-tenant Tree sharing exists; no global "industry template" containing tenant data
- System built-in "bare skeleton" (type names + generic dimension names only) can be shared across tenants, containing no tenant data

#### §23.11.3 Storage

```sql
-- Use existing agent_semantic_memory table structure
INSERT INTO agent_semantic_memory (tenant_id, user_id, fact_type, fact_key, fact_value, provenance, confidence)
VALUES (
    'tenant_acme', '00000000-0000-0000-0000-000000000000' /* system */, 
    'typology_tree', 
    'brd_type:reconciliation',
    '{"dimensions": [...], "version": 3, "source_brds": ["BRD-0001", "BRD-0007"]}',
    'tool_output',  -- Auto-extracted from BRD YAML, not LLM reasoning
    0.95
);
```

Note the `provenance = 'tool_output'`: the Typology Tree is auto-extracted from BRD YAML and schema, **not** from LLM reasoning, which is why it can be trusted as a high-accuracy dimension source.

#### §23.11.4 Degradation Mechanism

When tenant tables are all `table_a / col_1 / col_2` with meaningless naming → Layer 0 inference coverage < 30% → trigger proactive guided interaction: "It looks like your data source structure is quite irregular. Let me ask you a few core questions to understand your business first." Bare skeleton dimensions serve as the fallback questioning framework.

### §23.12 BRD Product Quality Assessment

> **Related**: → [`../../../adr/0018-agent-evaluation-framework.md`](../../../adr/0018-agent-evaluation-framework.md) (Agent Evaluation Framework), → [`../../../adr/0022-brd-generation-agent-pipeline.md`](../../../adr/0022-brd-generation-agent-pipeline.md)

#### §23.12.1 Distinction from Agent Trajectory Scoring

ADR-0018's six-dimension trajectory scoring evaluates the quality of Agent **execution process** (tool selection, argument accuracy, etc.). BRD as a **product** needs independent product quality assessment — two Agents could both have high trajectory scores, yet the BRDs they produce could differ dramatically in quality.

#### §23.12.2 Four-Dimension Human Reviewer Scoring

Approvers score BRDs on four dimensions during approval (1-5):

| Dimension | Assessment Criteria | Example |
|------|---------|------|
| **Clarity** | Are requirements unambiguous? Are Given/When/Then precise? | "Amount variance < $0.01" is clear; "Report should be correct" is not |
| **Completeness** | Are all necessary scenarios covered? Are edge cases considered? | Does it include exception handling and fallback strategies? |
| **Feasibility** | Is it achievable under current system constraints? Are data sources reachable? | Are referenced data sources in the Data Catalog and available? |
| **Compliance** | Are all applicable regulations correctly mapped? Is compliance coverage complete? | Are SOX §302/§404 both mapped to specific Requirements? |

The four-dimension scores serve as ground truth for BRD quality, driving:
- Typology Tree confidence updates (higher quality BRDs → higher Tree evolution weight)
- Golden Dataset expansion (lower quality BRDs → analyze failure modes → improve Prompts and Agent strategies)

## Failure Modes & Recovery

| Failure Mode | Detection | Recovery |
|--------------|-----------|----------|
| **Layer 0 low coverage** — tenant schema uses meaningless names (`table_a`/`col_1`), inference covers < 30% of dimensions. | Coverage check after Schema-Driven Bootstrap. | Trigger proactive guided interaction using the bare-skeleton questioning framework (§23.11.4). |
| **Stale Typology Tree** — schema changed but Tree not yet refined (Layer 1 only fires on BRD close). | Dimension mismatch detected by VaguenessResolver during elicitation. | Fall back to Schema-Driven dimensions + guided questioning; Tree refreshes on next BRD close. |
| **Cross-tenant leakage risk** — a global "industry template" would mix tenant data. | Design-time invariant: no such template exists; only the bare skeleton (no tenant data) is shareable. | Enforced by storage isolation in `agent_semantic_memory` keyed by `tenant_id`; no recovery needed if invariant holds. |
| **Low BRD quality scores** — approvers score low on Clarity/Completeness/Feasibility/Compliance. | Four-dimension scores below threshold at approval. | Block approval; route BRD back to draft with reviewer feedback; the low-quality BRD feeds Golden Dataset failure-mode analysis. |
| **Trajectory-vs-product mismatch** — high agent trajectory score but low product quality (or vice versa). | Comparison of ADR-0018 trajectory scores against §23.12.2 product scores. | Expected by design (§23.12.1); use the divergence to improve Agent prompts/strategies via the Golden Dataset. |
| **`agent_semantic_memory` corruption/loss. | Store-level health check. | Recover from WAL-G backups; Typology Tree is reconstructable from tenant Schema + approved BRDs (re-running Layers 0–2). |

## Non-Functional Requirements

| NFR | Target | Rationale |
|-----|--------|-----------|
| Tenant isolation | Strict — Tree facts scoped by `tenant_id`; only the bare skeleton (no tenant data) is shareable | Compliance and confidentiality: a tenant's dimension structure reveals its business. |
| Construction provenance | `provenance = 'tool_output'` for Typology Tree facts (not LLM reasoning) | Auto-extracted from schema/BRD YAML so the Tree is trustworthy and auditable. |
| Progressive coverage growth | Layer 0: 60–70%; Layer 1: +10–15% per BRD; Layer 2: standardized template at ≥3 BRDs | Quantified expectations per §23.11.2. |
| Degradation threshold | < 30% Layer 0 coverage triggers guided interaction | Ensures usable elicitation even with irregular naming. |
| Scoring determinism | Four-dimension scores are human ground truth (1–5) | Used as ground truth for Typology Tree confidence and Golden Dataset expansion; must be stable per approval. |
| Reconstructability | Tree reconstructable from tenant Schema + approved BRDs | Backup/DR robustness; no irreducible LLM-generated state. |

## Key Flows

### Typology Tree construction (progressive)

1. **Onboarding (Layer 0)** — ingest tenant Data Source Schema (table names, column names, DDL comments) → induce initial dimension hierarchy. Expected coverage 60–70% at medium accuracy. If coverage < 30% due to meaningless naming, branch to the degradation flow.
2. **Per-BRD close (Layer 1)** — when a BRD is closed/approved, extract its dimension structure and merge into the Tree. Adds ~10–15% coverage per BRD at high accuracy (sourced from an approved BRD).
3. **Pattern mining (Layer 2)** — once ≥3 BRDs of the same type exist, induce cross-BRD patterns into a standardized template at the highest accuracy (validated commonality).

### Degradation flow (§23.11.4)

Low Layer 0 coverage (< 30%) → VaguenessResolver initiates proactive guided interaction ("It looks like your data source structure is quite irregular. Let me ask you a few core questions to understand your business first.") → uses bare-skeleton dimensions as the fallback questioning framework → dimensions captured during elicitation feed back into Layer 1 refinement once the BRD closes.

### Quality feedback loop (§23.12.2)

1. Approver scores the BRD 1–5 on each of Clarity, Completeness, Feasibility, Compliance at the approval gate.
2. Scores become ground truth for that BRD's product quality.
3. **High-quality BRDs** → increase their weight in Typology Tree evolution (Layer 1/2 confidence).
4. **Low-quality BRDs** → routed into the Golden Dataset for failure-mode analysis → drive improvements to Prompts and Agent strategies (S15 pipeline, per [generation-pipeline.md](generation-pipeline.md)).

This loop is intentionally one-directional with respect to ADR-0018: trajectory scoring informs *how* the Agent ran, while the four-dimension product scoring informs *what* the Agent produced. Both feed improvement, but they measure different things (§23.12.1).

## Design References

- **§23.11, §23.12** of [`docs/03-architecture.md`](../../03-architecture.md) — source sections for this module.
- [`../../../adr/0022-brd-generation-agent-pipeline.md`](../../../adr/0022-brd-generation-agent-pipeline.md) — ADR-0022, which redesigned the BRD generation pipeline and VaguenessResolver's use of the Typology Tree; also referenced by §23.12.
- [`../../../adr/0018-agent-evaluation-framework.md`](../../../adr/0018-agent-evaluation-framework.md) — ADR-0018 Agent Evaluation Framework; the six-dimension trajectory scoring that BRD product quality assessment is deliberately distinct from (§23.12.1).
- [`README.md`](README.md) — sub-project overview and module list.
- [`generation-pipeline.md`](generation-pipeline.md) — VaguenessResolver sub-agent and the elicitation phase that consumes the Typology Tree (§23.5.1, §23.5.4).
- [`lifecycle-state-machine.md`](lifecycle-state-machine.md) — the approval gate at which the four-dimension scoring occurs.
- [`brd-entity-model.md`](brd-entity-model.md) — the BRD YAML that Layer 1 refinement extracts dimensions from.
