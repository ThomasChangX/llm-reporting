# Plan: Accept ADR-0025 and Align All Documentation

> **状态**：🟠 **部分执行**
> - ✅ Phase 1（ADR-0025 接受 + 0005/0006 加 `refined_by` 注记）—— ADR-0025 已 `accepted`（2026-07-30）
> - ✅ Phase 3.1（glossary 4 个新词条带 "Formerly called"）
> - ✅ Phase 5（图表重命名：`four-plane-arch.mmd`/`component-design-plane.mmd`/`freeze-bridge-flow.mmd` → `unified-engine-arch.mmd`/`component-exploration-env.mmd`/`freeze-pipeline-flow.mmd`）
> - ⚠️ **Phase 2/3.2/4/6/7 未完成**：当前状态文档（`03-architecture.md`、`02-requirement.md`、`04-timeline.md`、`05-cost.md`、`glossary.md` 7 词条、`system-context.mmd` 四个 box、`c4-model.md`、`threat-model.md` 等）仍残留旧 plane 名 —— 见审计 finding **I-008**（`docs/superpowers/specs/audit-20260803-bfac3ef-I-008-term-migration-residual.md`）
> - **后续**：术语迁移的剩余修复由 I-008 spec 驱动（修复执行时另起 plan）

## Overview
Accept ADR-0025 ("Unified Workflow Engine — One Engine, Three Environments") and systematically update 16+ files to eliminate the "four independent planes" narrative in favor of "one engine, three environments + one cross-environment read-only mode."

## Core Terminology Migration

| Old Term | New Term |
|---|---|
| Design Plane | Exploration Environment |
| Freeze Bridge (noun) | Freeze Pipeline (`freeze()` operation) |
| Runtime Plane | Production Environment |
| Intelligence Plane | Cross-Environment Read-Only Mode |
| "four planes" / "four layers" | "three environments + cross-environment read-only mode" |
| "cross-plane" | "cross-environment" |
| 9 Job Types | 10 Job Types (add `llm_reasoning`) |

---

## Phase 1: Accept ADR-0025 + Update ADR Metadata (4 files)

### 1.1 `adr/0025-unified-workflow-engine.md`
- Change `status: proposed` → `status: accepted` in YAML frontmatter
- Update `date: 2026-07-30` (keep)
- Change body `- **Status**: Proposed` → `- **Status**: Accepted`

### 1.2 `adr/README.md`
- Line 36: Change `📋 Proposed` → `✅ Accepted` for ADR-0025

### 1.3 `adr/0005-four-layer-architecture.md` (Accepted — body text is immutable per AGENTS.md)
- Frontmatter already has `refined_by: "ADR-0025"` ✅
- Add a refinement note after the header: *"> **Refined by ADR-0025** (2026-07-30): The 'four independent planes' are now understood as three environments of a unified Workflow Engine + one cross-environment read-only mode. The core decisions (separation of exploration from production, zero AI side effects) are preserved. See ADR-0025 for the refined framing."*
- Update line 82 Linked Modules to reference ADR-0025

### 1.4 `adr/0006-freeze-bridge-independence.md` (Accepted — body text is immutable)
- Frontmatter already has `refined_by: "ADR-0025"` ✅
- Add a refinement note after the header: *"> **Refined by ADR-0025** (2026-07-30): Freeze Bridge is repositioned from an independent plane to a built-in `freeze()` pipeline operation on the unified Workflow Engine. The core guarantees (mandatory human sign-off, no auto-compilation) are preserved. See ADR-0025 for the refined framing."*

---

## Phase 2: Update Core Architecture Document (1 file, ~15 edits)

### 2.1 `docs/03-architecture.md`

**§2 Panoramic Architecture (lines 22-86):**
- Redesign the ASCII diagram to show one Workflow Engine at the center with:
  - Exploration Environment (left, LLM APIs reachable, sampled data)
  - Freeze Pipeline (center, as a horizontal flow: `Design Artifact → freeze() → Frozen Spec`)
  - Production Environment (right, LLM API egress blocked by NetworkPolicy, full data)
  - Cross-Environment Read-Only Mode (horizontal bar spanning both environments)
- Change box labels: `DESIGN PLANE`→`EXPLORATION ENVIRONMENT`, `FREEZE BRIDGE`→`FREEZE PIPELINE`, `RUNTIME PLANE`→`PRODUCTION ENVIRONMENT`, `INTELLIGENCE PLANE`→`CROSS-ENVIRONMENT READ-ONLY MODE`
- Change `(Cross-Plane)` label → `(Cross-Environment)`

**§3 Four-Layer Model (lines 102-111):**
- Line 102: Add subtitle "Environments of the Unified Workflow Engine"
- Line 104: Rewrite from "four layers by Mutability" to "single Workflow Engine operating in distinct environments"
- Lines 106-111: Restructure the table — rename columns, add Network Isolation column, reframe Freeze Bridge row as pipeline, reframe Intelligence Plane as cross-environment mode
- Line 113: `### 3.1 Design Plane in Detail` → `### 3.1 Exploration Environment in Detail`
- Line 115: Update terminology throughout subsection

**§4 Freeze Bridge (lines 240-371):**
- Line 240: `## 4. Freeze Bridge` → `## 4. Freeze Pipeline`
- Line 242: Rewrite opening sentence to describe `freeze()` as built-in engine operation
- Line 247: Add `llm_reasoning` Job scanning to Spec Refinement Assistant description
- Lines 261-262: Add `llm_reasoning` to Step 1 Scan description
- Lines 284+: Add note that `llm_reasoning` Jobs with capabilities beyond `read_analyze`/`suggest_plan` are flagged alongside fuzzy_nodes

**§5 Runtime Plane (lines 372-386):**
- Update heading narrative: "Deterministic, high-performance production execution" → add "(Production Environment of the Unified Workflow Engine)"
- No structural changes needed; component responsibilities are unchanged

**§6 Compute Spec (lines 909-987):**
- Line 921: Add `| llm_reasoning` to the concept hierarchy type list
- Lines 931-943: Add `llm_reasoning` row to Job Type Complete Enumeration table with capability taxonomy
- Lines 964-987: Add `llm_reasoning` row to Common Compute Subset table (noted as "routes through MCP, orthogonal to Light/Heavy Engine")
- Line 2081: Update `job` entity description from "9 types" to "10 types"

**§9.3 Intelligence Plane (lines 1110-1129):**
- Line 1110: Heading → "Cross-Environment Read-Only Mode"
- Line 1112: Rewrite positioning statement
- Line 1115: Update "Intelligence Plane AI output" → "Cross-environment mode output"
- Line 1117: Update transition path terminology
- Line 1121: Update "Runtime Plane never calls an LLM" to reflect configurable `read_analyze`/`suggest_plan` in Production

**§17.3 Network Security Group Rules (lines 2050-2067):**
- Add environment-specific egress rules for LLM API access
- Add Production Environment `default-deny` internet egress with explicit allow to MCP Gateway
- Add new subsection `### 17.3.1 Environment-Level NetworkPolicy (Kubernetes)` describing K8s NetworkPolicy resources

---

## Phase 3: Update Glossary and Requirements (2 files)

### 3.1 `docs/glossary.md`
- Lines 11-14: Rewrite Design Plane/Freeze Bridge/Runtime Plane/Intelligence Plane definitions
- Line 12: Remove "independent transition plane" language for Freeze Bridge
- Line 15: Change "9 Job Types" → "10 Job Types", add `llm_reasoning` to list
- Lines 45-46: Remove "The 9th Job Type" ordinal for Materialize; replace with plain description
- Add new entries: `llm_reasoning`, `Exploration Environment`, `Freeze Pipeline`, `Production Environment`, `Cross-Environment Read-Only Mode`
- Line 155: Update "Total Terms" count (101 → ~106 after additions)

### 3.2 `docs/02-requirement.md`
- Lines 246-250: Update Core Terms Quick Reference table with new terminology
- Line 250: "9 Job Types" → "10 Job Types"
- Line 268 (FR13.6): "9 Job types" → "10 Job types", add `llm_reasoning`
- Lines 163, 201-202, 275-276, 325: Update scattered plane references
- Lines 633-682: Update phase traceability matrix column headers to new terminology

---

## Phase 4: Update Facts & Supporting Docs (4 files)

### 4.1 `docs/01-facts.md`
- Line 7: Update term count if glossary count changes
- Lines 62-65 (Decision #1): Add refinement note referencing ADR-0025
- Lines 68-72 (Decision #2): Rewrite to acknowledge "one engine, three environments" refinement; preserve original decision content, add note that ADR-0025 refines the framing
- Line 85 (Decision #4): Update plane references
- Line 229: "9 Job Types" → "10 Job Types", add `llm_reasoning`
- Line 601: Update footer date and version

### 4.2 `docs/README.md`
- Line 14: Update term count if changed
- Line 21: Update "Four-Layer Architecture" description
- Lines 45-46: Update key concepts summary

### 4.3 `docs/cross-reference-checklist.md`
- Line 25: Update glossary entry count reference if changed
- Update "Last Run" date

### 4.4 `README.md` (root)
- Lines 21, 45-46: Update "Four-Layer Architecture" and "9 Job Types" references

---

## Phase 5: Update Diagrams (4 files)

### 5.1 `docs/diagrams/four-plane-arch.mmd`
- Rename file to `unified-engine-arch.mmd`
- Update comment "C4 Container Diagram — llm-reporting Four-Layer Architecture" → "llm-reporting Unified Workflow Engine Architecture"
- Restructure subgraphs: `DESIGN PLANE`→`EXPLORATION ENVIRONMENT`, `FREEZE BRIDGE`→`FREEZE PIPELINE`, `RUNTIME PLANE`→`PRODUCTION ENVIRONMENT`, `INTELLIGENCE PLANE`→`CROSS-ENVIRONMENT READ-ONLY MODE`
- Update classDef labels: `plane`→`environment`

### 5.2 `docs/diagrams/component-design-plane.mmd`
- Update subgraph label `DESIGN PLANE`→`EXPLORATION ENVIRONMENT`

### 5.3 `docs/diagrams/freeze-bridge-flow.mmd`
- Rename to `freeze-pipeline-flow.mmd`
- Update participant names and note labels

### 5.4 `docs/diagrams/README.md`
- Line 10: Update diagram descriptions with new file names and terminology

---

## Phase 6: Update Timeline and Cost Docs (2 files)

### 6.1 `docs/04-timeline.md`
- Line 220: "independent transition plane" → "Freeze Pipeline"
- Line 443: "all 9 Job types" → "all 10 Job types"

### 6.2 `docs/05-cost.md`
- Line 329: Update "ADR-0005 (Four-Layer Architecture)" reference

---

## Phase 7: Update Other ADRs with Passing References (4 files)

### 7.1 `adr/0003-design-order.md`
- Line 41: "four layers" → update with refinement note

### 7.2 `adr/0011-materialize-job-type.md`
- Line 83: "9 Job Types" → "10 Job Types" reference

### 7.3 `adr/0016-dual-mode-agent-orchestration.md`
- Line 23: "ADR-0005 Four-Layer Architecture" → add refinement note

### 7.4 `adr/0002-llm-role-positioning.md`
- Line 59: Update linked module reference (optional)

---

## Phase 8: Regenerate ADR Index + Validate

### 8.1 Regenerate ADR index
```bash
python3 scripts/gen_adr_index.py && git add docs/adr-index.md
```

### 8.2 Run consistency checks
```bash
python3 scripts/check_adr_semantics.py
python3 scripts/gen_adr_index.py --check
```

### 8.3 Verify all cross-references
- Ensure all internal links resolve
- Ensure counts are consistent (10 Job Types everywhere, term count current)

---

## Files NOT Changed (Rationale)
- **ADR-0005, ADR-0006 body text**: Immutable per AGENTS.md ("Decision content is immutable once Accepted"). Only refinement notes added above body.
- **All other Accepted ADRs**: Body text preserved; only Linked Modules sections updated where they reference 9 Job Types.
- **`docs/security/threat-model.md`**: Uses component names not plane names (e.g., "Workflow Executor"), unaffected.
- **`docs/operations/slo-sli.md`**: Uses component names, unaffected.
- **`docs/architecture/c4-model.md`**: References components, would need review but labeling changes only if it references "planes".
- **`docs/api/README.md`**: Placeholder, unaffected.

## Total: ~16 files touched, ~40+ individual edits