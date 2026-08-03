# Plan 执行索引

> **最后更新**：2026-08-03
> **活跃 plan 数**：1（部分执行）| **已归档**：0（见 `archive/plans/`，待建立）

Plan 文件在 spec 进入实施阶段后才创建。Plan 是 spec 的执行细化（具体到改哪些文件、怎么改、验收门禁）。

---

## 活跃 Plan

### `2026-07-30-adr-0025-document-alignment.md` · ADR-0025 文档对齐
- **状态**：🟠 **部分执行**
- **对应 spec**：[`../specs/audit-20260803-bfac3ef-I-008-term-migration-residual.md`](../specs/audit-20260803-bfac3ef-I-008-term-migration-residual.md)（I-008，术语迁移残留）
- **已完成**：
  - ✅ Phase 1：ADR-0025 接受（`status: accepted`，2026-07-30）；ADR-0005/0006 加 `refined_by: ADR-0025` 注记
  - ✅ Phase 3.1：glossary 4 个新词条（Exploration Environment / Freeze Pipeline / Production Environment / Cross-Environment Read-Only Mode）带 "Formerly called" legacy 标注
  - ✅ Phase 5：图表重命名 —— `four-plane-arch.mmd` → `unified-engine-arch.mmd`、`component-design-plane.mmd` → `component-exploration-env.mmd`、`freeze-bridge-flow.mmd` → `freeze-pipeline-flow.mmd`
- **未完成**（由 I-008 spec 驱动）：
  - ⚠️ Phase 2/3.2/4/6/7：当前状态文档仍残留旧 plane 名 —— `03-architecture.md`（22 处）、`02-requirement.md`（4 FR）、`04-timeline.md`（含 Phase 标题）、`05-cost.md`（含成本行）、`glossary.md`（7 词条无 legacy 标注）、`system-context.mmd`（四个 box 全旧名）、`c4-model.md`、`threat-model.md` 等
- **后续**：剩余修复执行时另起 plan（基于 I-008 spec 的 Fix Plan + Acceptance Criteria）

---

## 待执行的 spec → plan 映射

活跃 spec 的执行队列、优先级、依赖关系见 [`../specs/INDEX.md`](../specs/INDEX.md)。每个 spec 的「对应 plan」字段标记了 plan 是否已创建：

- `❌ 未写` → 该 spec 进入实施阶段时再创建 plan（避免过早规划）
- `✅ ready` → plan 已创建并位于本目录
- `🟠 部分执行` → plan 已创建并部分执行，剩余由 spec 驱动

当前 24 个 spec 中：
- 1 个（I-008）对应 plan 已部分执行（上方）
- 23 个对应 plan 未写（spec ready，进入实施时创建）

---

## 归档说明

当前无归档 plan。后续完成的 plan 移至 `archive/plans/`（待建立），按完成日期排序，保留作历史记录。
