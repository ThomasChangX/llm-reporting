# Audit Fix Spec · 文档计数过时（README 行数 + 图表 Skills）

## 元数据
- **Source Finding(s)**：M-020, M-021
- **Severity**：Minor
- **Source Dimensions**：A4, A5
- **Created From Audit**：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- **Status**：done（2026-08-04。`README.md:21` ~6200→~6400；`component-exploration-env.mmd:15` 14→18 Skills）

## 证据

### M-020 · README 行数标注过时（~6200 vs 实际 6410）
- **位置**：`README.md:21`
- **证据**：
  > README.md:21 — "Full architecture design (~6200 lines)" | 实际 `wc -l docs/03-architecture.md` = 6410

### M-021 · component-exploration-env.mmd 标"14 Skills"（实际 18）
- **位置**：`docs/diagrams/component-exploration-env.mmd:15`
- **证据**：
  > docs/diagrams/component-exploration-env.mmd:15 — "Skill["Skill Engine<br/>**14 Skills**<br/>Skill Chaining"]"
  > docs/glossary.md:55 + 01-facts.md:297 + 03-architecture.md:3072 —— 均为 "**18** composable Skills (S01-S18)"

## 问题分析（根因）

两处同根因：**计数过时**。文档/图表在 Skill 数（S15-18 在 ADR-0022/0024 后加入）与架构行数增长后未同步。M-020 是 README 概要数字滞后；M-021 是图表标签滞后（S15-18 加入后 Skills 从 14→18）。均属当前状态文档，无豁免。

## 修复方案（Fix Plan）

1. **M-020**：`README.md:21` 将 "~6200 lines" 改为 "~6400 lines" 或移除具体数字（如 "Full architecture design (6000+ lines)"）避免再次过时。
2. **M-021**：`docs/diagrams/component-exploration-env.mmd:15` 将 "14 Skills" 改为 "18 Skills"。
3. 全仓 grep 其他可能的 Skills 计数残留（已在 Step 2 确认仅此一处非豁免）。

## 验收标准（Acceptance Criteria）

- [ ] `README.md:21` 行数与实际 `wc -l docs/03-architecture.md` 一致或用"6000+"模糊表述
- [ ] `docs/diagrams/component-exploration-env.mmd:15` 标 "18 Skills"
- [ ] `grep -rn '14 Skills' docs/` 无返回（除 superpowers 设计审核 prompt 自身）

## Audit Trail
- 来源审核 run：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- 来源报告：`docs/superpowers/specs/audit-20260803-bfac3ef-report.md`
