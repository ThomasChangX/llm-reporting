# Audit Fix Spec · 无 DPIA + HIPAA 薄弱 + SoD 未强制

## 元数据
- **Source Finding(s)**：I-013
- **Severity**：Important
- **Source Dimensions**：D4
- **Created From Audit**：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- **Status**：open

## 证据

### I-013 · 无 DPIA + HIPAA 薄弱 + SoD 未强制
- **位置**：`docs/03-architecture.md:6389-6393`、`docs/operations/gdpr-compliance.md:107`、`docs/03-architecture.md:6343-6345`
- **证据**：
  > docs/03-architecture.md:6389-6393 — Breach Notification 仅引 GDPR Art.33/34（72h），**未提 HIPAA Breach Notification Rule**（向个人 60 天 + HHS/OCR）
  > docs/operations/gdpr-compliance.md:107 — DPO "Advise on Data Protection Impact Assessments (DPIA)" —— **无实际 DPIA 工件**
  > docs/03-architecture.md:6345 — "Designed based on GDPR/CCPA/HIPAA/CSL/DSL/PIPL" 但无逐条映射
- **问题**：(a) 声称 HIPAA 但 Breach Notification 仅 GDPR，HIPAA 164.308/310/312/316 未逐项映射；(b) GDPR Art.35 高风险处理要求 DPIA，无工件；(c) SOX ITGC SoD 未显式强制（REVIEWER 独立但无硬规则 dev≠approver）。
- **影响**：DPIA 缺失 = GDPR 硬伤；HIPAA 薄弱 = 医疗客户准入受阻；SoD 未强制 = SOX 审计发现。

## 问题分析（根因）

§25 合规章节以 GDPR 为主线（gdpr-compliance.md 详尽），HIPAA/CCPA/CSL 仅在数据驻留 + 分类层提及，未做逐条控制映射。DPIA 是 GDPR Art.35 对"高风险处理"（AI 处理客户财务数据明显属此）的强制要求，但设计仅列 DPO 职责。SoD 在 §21.1 REVIEWER 角色隐含，但未声明为硬规则。这是 D4（合规映射：法规 × 控制点矩阵）的空洞——见报告附录 B 矩阵的 ⚠️/⚡ 格。

## 修复方案（Fix Plan）

1. **DPIA 工件**：在 `docs/operations/` 新建 `dpia.md`（或在 gdpr-compliance.md 补章节），覆盖 GDPR Art.35 要求：处理描述、必要性评估、风险识别、缓解措施、残余风险、相关方咨询。
2. **HIPAA 逐条映射**：在 `docs/03-architecture.md` §25 或新建 `docs/operations/hipaa-compliance.md`，逐条映射：
   - 164.308 行政保障（含 workforce security、incident response、 contingency planning）
   - 164.310 物理保障（facility access、workstation security）
   - 164.312 技术保障（access control、audit、integrity、transmission security）
   - 164.316 文档化
   - **Breach Notification Rule**（45 CFR §§164.400-414：向个人 ≤60 天 + HHS + 媒体若 >500 人）
3. **SoD 显式强制**：在 §21.1 或 §11.2 声明硬规则："Workflow 的开发者（author）不能是该 Workflow Freeze PR 的 REVIEWER；系统在 Freeze 提交时校验 author ≠ reviewer。"
4. **更新报告附录 B 矩阵**：修复后，DPIA/HIPAA/SoD 格从 ⚠️/⚡ 改为 ✅。

## 验收标准（Acceptance Criteria）

- [ ] `docs/operations/` 存在 DPIA 工件（或 gdpr-compliance.md 含 DPIA 章节）
- [ ] `docs/03-architecture.md` 或新文件含 HIPAA 逐条映射（含 Breach Notification Rule 60d）
- [ ] §21.1 或 §11.2 含 SoD 硬规则（author ≠ reviewer）
- [ ] 附录 B 矩阵 DPIA/HIPAA-308-316/SoD 格标 ✅

## Audit Trail
- 来源审核 run：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- 来源报告：`docs/superpowers/specs/audit-20260803-bfac3ef-report.md`
