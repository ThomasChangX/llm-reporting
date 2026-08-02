# Audit Fix Spec · 246 条 FR 缺验收标准（文档自承认）

## 元数据
- **Source Finding(s)**：I-009
- **Severity**：Important
- **Source Dimensions**：A6
- **Created From Audit**：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- **Status**：open

## 证据

### I-009 · FR 普遍缺验收标准
- **位置**：`docs/02-requirement.md:22,24`、`docs/02-requirement.md:5`
- **证据**：
  > docs/02-requirement.md:22 — "⚠️ Most current FRs lack testable acceptance criteria and need to be supplemented before entering the development phase."
  > docs/02-requirement.md:24 — "Each functional requirement should include: ... Acceptance Criteria (Given/When/Then testable conditions) ..."
  > docs/02-requirement.md:5 — "Status: Stable"（与 L22 自承认矛盾）
- **问题**：文档自定标准（L24）要求每条 FR 含 Given/When/Then AC，但 L22 自承认"多数 FR 缺 AC"，实测 246 条 FR 仅 1 条含 AC 关键词。header "Status: Stable" 与"缺 AC"矛盾。
- **影响**：FR 不可测试 = 进入开发阶段无法验收。设计→开发的最大鸿沟。

## 问题分析（根因）

02-requirement.md（2026-07-04）在"Status: Stable"声明时高估了成熟度。L22 的 ⚠️ 是诚实自承认，但未触发将 Status 降级或补全 AC 的行动。违反 A6（可验证性：每条 FR 需可测 AC）。

## 修复方案（Fix Plan）

1. **优先 P0 FR**：为 P0 FR（约 N 条）补 Given/When/Then AC。
2. **降级或补全**：要么将 header "Status: Stable" 改为 "Status: Draft (AC pending)"，要么补全全部 FR 的 AC 后保持 Stable。
3. **模板**：建立 FR AC 模板（Given [前置] / When [动作] / Then [可测结果]），统一格式。
4. 工作量大，建议分批（如先 P0，再 P1，最后 P2）。

## 验收标准（Acceptance Criteria）

- [ ] `docs/02-requirement.md` 所有 P0 FR 含 Given/When/Then AC
- [ ] header "Status" 与 AC 完整度一致（要么 Stable + 全 AC，要么 Draft）
- [ ] L22 ⚠️ 标记移除（AC 补全后）或更新为具体剩余数

## Audit Trail
- 来源审核 run：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- 来源报告：`docs/superpowers/specs/audit-20260803-bfac3ef-report.md`
