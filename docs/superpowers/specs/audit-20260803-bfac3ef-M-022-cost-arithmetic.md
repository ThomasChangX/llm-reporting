# Audit Fix Spec · cost 文档算术不一致

## 元数据
- **Source Finding(s)**：M-022
- **Severity**：Minor
- **Source Dimensions**：A6
- **Created From Audit**：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- **Status**：open

## 证据

### M-022 · 算术不一致：盈亏分子 + Intelligence Small
- **位置**：`docs/05-cost.md:474` vs `:469`、`docs/05-cost.md:308`
- **证据**：
  > docs/05-cost.md:474 — "$457,464 ÷ ($2,000 × 0.60 × 24)" | docs/05-cost.md:469 — "Total Development Cost ... $458,564 (US)"（差 $1,100）
  > docs/05-cost.md:308 — Small Intelligence Plane "$8/mo" | 但 $0.015/query × 40/day × 22d = $13.20/mo
- **问题**：两处算术/转录不一致。
- **影响**：轻微——盈亏平衡结论 ~$1,100 误差；Intelligence 成本低估 ~40%。

## 问题分析（根因）

M-022 是孤立的算术/转录错误，非系统性缺陷。$457,464 vs $458,564 疑为四舍五入/转录误差；$8 vs $13.20 是 per-query 均价与场景使用量未对齐。

## 修复方案（Fix Plan）

1. `docs/05-cost.md:474` 盈亏分子改为 $458,564（与 :469 一致），重算 tenant 数。
2. `docs/05-cost.md:308` Small Intelligence 重算：$0.015/query × 40/day × 22d = $13.20/mo（或调整使用量假设使 $8 自洽）。

## 验收标准（Acceptance Criteria）

- [ ] `docs/05-cost.md:474` 盈亏分子 == :469 开发成本（$458,564）
- [ ] `docs/05-cost.md:308` Small Intelligence 月成本与 per-query 均价 × 使用量自洽

## Audit Trail
- 来源审核 run：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- 来源报告：`docs/superpowers/specs/audit-20260803-bfac3ef-report.md`
