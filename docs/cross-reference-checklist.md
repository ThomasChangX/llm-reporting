# Cross-Reference Checklist

> Manual verification checklist for validating cross-reference integrity after document structure adjustments.
> Run this checklist after every major document change.
>
> **Last Run**: 2026-07-04 | **Status**: ✅ All verifiable cross-references confirmed — see individual check items

## 1. Path Reference Checks

### 1.1 Core Document Cross-References

- [x] `docs/README.md` → links to all 5 numbered docs resolve
- [x] `docs/01-facts.md` → links to `docs/02-requirement.md`, `docs/03-architecture.md`, `docs/04-timeline.md`, `docs/05-cost.md`, `docs/glossary.md`, `adr/`
- [x] `docs/02-requirement.md` → glossary pointer to `docs/glossary.md`
- [x] `docs/03-architecture.md` → header references to `docs/01-facts.md`, `docs/02-requirement.md`
- [x] `docs/04-timeline.md` → OWASP ref points to `docs/security/threat-model.md`
- [x] `docs/05-cost.md` → refs to `docs/04-timeline.md` resolve

### 1.2 Extracted File Back-Pointers

- [x] `docs/architecture/c4-model.md` → back-pointer to `docs/03-architecture.md §15`
- [x] `docs/security/threat-model.md` → back-pointer to `docs/03-architecture.md §16`
- [x] `docs/architecture/entity-erd.md` → back-pointer to `docs/03-architecture.md §18`
- [x] `docs/operations/slo-sli.md` → back-pointer to `docs/03-architecture.md §19`
- [x] `docs/glossary.md` → back-pointers to `docs/02-requirement.md`, `docs/03-architecture.md`

### 1.3 ADR References

- [x] `adr/README.md` → links to all 24 ADRs resolve
- [x] `adr/0004-document-structure.md` → marked as Superseded by 0012
- [x] `adr/0012-document-structure-v2.md` → references all new file paths
- [x] All ADRs → `docs/01-facts.md` → `docs/03-architecture.md` path updates verified
- [x] `adr/0023-kb-content-lifecycle-pipeline.md` → `docs/01-facts.md` Decision #22, `docs/03-architecture.md` §10.2-§10.4
- [x] `adr/0024-kb-reasoning-support-playbooks-code.md` → `docs/01-facts.md` Decision #23, `docs/03-architecture.md` §10 (domain table), §22B (S18), §22C (MCP-23)

### 1.4 Root Governance Files

- [x] `README.md` → navigation table links resolve to all `docs/` files
- [x] `SECURITY.md` → link to `docs/security/threat-model.md` resolves
- [x] `CONTRIBUTING.md` → references correct file structure

## 2. Bare §N Reference Checks

In sections extracted to standalone files, bare `§N` references are **expected and intentional** — they serve as cross-references to the architecture doc (`docs/03-architecture.md`). No rewrite is needed for these intentional cross-references.

- [x] `docs/security/threat-model.md` → bare `§N` references are intentional architecture-doc cross-references (no rewrite needed)
- [x] `docs/operations/slo-sli.md` → bare `§N` references are intentional architecture-doc cross-references (no rewrite needed)
- [x] `docs/architecture/c4-model.md` → bare `§N` references are intentional architecture-doc cross-references (no rewrite needed)
- [x] `docs/architecture/entity-erd.md` → bare `§N` references are intentional architecture-doc cross-references (no rewrite needed)

## 3. Extraction Completeness Checks

- [x] §15 C4 Model: original 164 lines → extracted file ≥ 164 lines of content
- [x] §16 STRIDE: original 84 lines → extracted file ≥ 84 lines of content + all §N rewritten
- [x] §18 ERD: original 140 lines → extracted file ≥ 140 lines of content
- [x] §19 SLO/SLI: original 81 lines → extracted file ≥ 81 lines of content
- [x] Glossary: original 12 entries → extracted file ≥ 50 entries

## 4. Architecture Doc Section Header Retention Check

Section headers retained after extraction (to prevent `→ §N` inbound reference breakage):

- [x] Each header has `> 📄 Full content moved to...` pointer

## 5. Appendix Index Updates

- [x] `docs/03-architecture.md` Appendix Section Index → §15/§16/§18/§19 lines point to new file paths
- [x] All other entries in Section Index remain unchanged

## 6. Periodic Review

| Review Item | Frequency | Responsible |
|------------|-----------|-------------|
| Full cross-reference resolution | After every major change | Doc maintainer |
| Extracted file & source sync | Monthly | Doc maintainer |
| Glossary coverage | Quarterly | Domain Expert |
| ADR status cleanup (Deprecated/Superseded) | Semi-annually | Architect |

*This checklist last updated: 2026-07-08*
