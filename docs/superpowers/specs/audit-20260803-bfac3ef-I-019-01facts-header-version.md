# Audit Fix Spec · 01-facts 标题与正文不符 + 版本跳号

## 元数据
- **Source Finding(s)**：I-019
- **Severity**：Important
- **Source Dimensions**：A8, A1
- **Created From Audit**：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- **Status**：done（2026-08-04。`01-facts.md:470` 标题改为 "Supplemental Decisions (Decision #8–#25)" + 补 Decision#N 为叙事序号的说明；Version History 补 v1.5 "folded into v1.6" 条目消除跳号）

## 证据

### I-019 · 01-facts 标题不符 + 版本跳号
- **位置**：`docs/01-facts.md:470`、`docs/01-facts.md:595-599`
- **证据**：
  > docs/01-facts.md:470 — "## 2026-07-04 Supplemental Decisions (ADR **#7-#21**)"
  > docs/01-facts.md:472-581 — 正文从 "### Decision **#8**" 到 "### Decision **#25**"
  > docs/01-facts.md:595→599 — Version History 从 v1.4 跳到 v1.6，无 v1.5 条目
- **问题**：标题声称覆盖 ADR #7-#21，正文实际是 Decision #8-#25（且 Decision #N 是叙事序号非 ADR 号）。版本历史跳号。
- **影响**：读者按标题定位内容失败。可追溯性断裂。

## 问题分析（根因）

01-facts 的"## Supplemental Decisions"标题在历次 ADR 添加后未同步更新（标题停留在某次中间状态 #7-#21）。Decision #N 是叙事序号（docs/AGENTS.md 明确"非 1:1 与 ADR 号"），标题却用 "ADR #7-#21" 暗示 ADR 号映射，混淆两个概念。版本跳号 v1.4→v1.6 可能是 v1.5 漏记或合并提交。

## 修复方案（Fix Plan）

1. **标题校正**：将 `docs/01-facts.md:470` 改为反映实际内容，如 "## 2026-07-04 Supplemental Decisions (Decision #8-#25)" 或 "## Supplemental Decisions (Decisions recorded 2026-07-04)"。避免用 "ADR #N" 暗示 ADR 号映射。
2. **版本跳号**：在 Version History 补 v1.5 条目（若回忆得起变更），或注明"v1.5 合并至 v1.6"。
3. **Decision #N vs ADR 号**：在文档开头补一句说明"Decision #N 是叙事序号，与 ADR 号的关系见各 Decision 的 Status/Background 字段引用的具体 ADR"。

## 验收标准（Acceptance Criteria）

- [ ] `docs/01-facts.md:470` 标题与正文 Decision 范围一致
- [ ] 标题不再用误导性的 "ADR #N" 暗示
- [ ] Version History 无跳号或跳号有说明
- [ ] 文档含 Decision #N vs ADR 号关系说明

## Audit Trail
- 来源审核 run：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- 来源报告：`docs/superpowers/specs/audit-20260803-bfac3ef-report.md`
