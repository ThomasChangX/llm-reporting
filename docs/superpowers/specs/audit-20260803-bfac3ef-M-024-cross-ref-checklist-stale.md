# Audit Fix Spec · cross-reference-checklist 日期不一致 + glossary 计数过时

## 元数据
- **Source Finding(s)**：M-024
- **Severity**：Minor
- **Source Dimensions**：A1
- **Created From Audit**：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- **Status**：in-progress（2026-08-04。机械项已修：glossary 计数 101→102；L6/L80 日期语义明确区分（Last Verified Run vs last updated）；L80 更新到 2026-08-04。**未完成**：L6 的"⚠️ Pending re-verification after ADR-0025"——逐项 re-verification 属 I-008 术语迁移的工作范围，待 I-008 完成后执行）

## 证据

### M-024 · cross-ref-checklist 自标 stale + 日期 + 计数
- **位置**：`docs/cross-reference-checklist.md:6`、`docs/cross-reference-checklist.md:80`、`docs/cross-reference-checklist.md:58`
- **证据**：
  > docs/cross-reference-checklist.md:6 — "**Last Run**: 2026-07-30 ... ⚠️ Pending re-verification after ADR-0025"
  > docs/cross-reference-checklist.md:80 — "*This checklist last updated: 2026-07-09*"（同一文档两个"最后"日期）
  > docs/cross-reference-checklist.md:58 — "Glossary: ... 101 entries"（glossary 当前 102）
- **问题**：自标 stale；日期不一致；glossary 计数滞后。
- **影响**：轻微——清单可信度受损。

## 问题分析（根因）

cross-reference-checklist.md 是人工验证清单，在 ADR-0025（2026-07-30）后自标"待 re-verification"但未执行。"Last Run"（L6）与"last updated"（L80）是两个不同语义字段但读者混淆。§3 的 glossary 计数（101）早于 ADR-0024 加入的第 102 词。

## 修复方案（Fix Plan）

1. 完成 ADR-0025 后的 re-verification：逐项核对 §1-§5，更新 ⚠️ 为 ✅。
2. 统一日期：L6 "Last Run" 与 L80 "last updated" 改为一致日期（或明确区分"Last Run"=上次执行验证/"Last Updated"=清单内容上次编辑）。
3. `docs/cross-reference-checklist.md:58` glossary 计数 101 → 102。
4. 同步 §3 其他计数（如 §15/§16/§18/§19 行数）与实际。

## 验收标准（Acceptance Criteria）

- [ ] `docs/cross-reference-checklist.md:6` ⚠️ 移除（re-verification 完成）
- [ ] L6 与 L80 日期一致或语义明确区分
- [ ] `docs/cross-reference-checklist.md:58` glossary 计数 == 102
- [ ] §3 各项行数与实际一致

## Audit Trail
- 来源审核 run：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- 来源报告：`docs/superpowers/specs/audit-20260803-bfac3ef-report.md`
