# Audit Fix Spec · "零 AI 副作用" 边界无精确定义 + glossary 自相矛盾

## 元数据
- **Source Finding(s)**：I-010
- **Severity**：Important
- **Source Dimensions**：A7, B5
- **Created From Audit**：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- **Status**：open

## 证据

### I-010 · "零 AI 副作用" 边界无精确定义
- **位置**：`docs/glossary.md:13`、`adr/0025-unified-workflow-engine.md:97-100`、`docs/03-architecture.md:1153`
- **证据**：
  > docs/glossary.md:13 — "Production Environment | The deterministic, **zero AI side-effect** production execution environment ... **LLM API egress is physically blocked at NetworkPolicy level**; `llm_reasoning` capabilities beyond `read_analyze`/`suggest_plan` are rejected at Engine submission time."
  > adr/0025-unified-workflow-engine.md:97-100 — Production YAML: `llm.enabled: true`, `allow_llm_api: true`, `allowed_capabilities: [read_analyze, suggest_plan]`
  > docs/03-architecture.md:1153 — "Production Environment may invoke LLMs via `llm_reasoning` Jobs with `read_analyze` or `suggest_plan` capabilities"
- **问题**：(a) glossary 同一定义自相矛盾——说"egress 物理阻断"又说"超出 read_analyze/suggest_plan 被拒"（暗示这两个可触发，需 egress 开放）；(b) ADR-0025 + §9.3 确认生产可调 LLM；(c) 无文档定义"什么算副作用"。
- **影响**：核心约束歧义 → 防御层设计验收标准不清 → 审计无法判定合规。

## 问题分析（根因）

"零 AI 副作用"是 ADR-0005 提出的核心约束，但从未精确定义"副作用"的边界。ADR-0025 实质上放宽了它（生产允许 read_analyze/suggest_plan 只读 LLM），但 glossary 仍用 ADR-0005 时代的绝对化表述（"physically blocked"）。这是 A7（无歧义性："零 AI 副作用"无精确边界）+ B5（核心约束可执行性）的交叉缺陷。

## 修复方案（Fix Plan）

1. **glossary Production 定义消除矛盾**：改为 "Production Environment | ... LLM API egress is **restricted via NetworkPolicy** to only the MCP Gateway; `llm_reasoning` capabilities beyond `read_analyze`/`suggest_plan` are rejected at Engine submission time. Read-only LLM calls (read_analyze/suggest_plan) are permitted; all mutating/irreversible operations remain deterministic."（移除"physically blocked"的绝对化表述）。
2. **新增 "AI Side Effect" 词条**：精确定义边界，如："AI Side Effect | Any irreversible or state-mutating consequence of LLM invocation on production data, configuration, or external systems. Includes: data writes, config changes, external API mutations. Excludes: read-only LLM inference (read_analyze, suggest_plan) whose outputs are presented to users as suggestions and never directly executed. The 'zero AI side effects' constraint prohibits the former; the latter is permitted under capability governance."
3. **同步 ADR-0005/ADR-0025 叙事**：若需改 ADR 决策内容，用新 superseding ADR；若仅澄清，在 glossary + 03-arch §9.3 补注。
4. 全仓 grep "zero AI side" 确保表述一致。

## 验收标准（Acceptance Criteria）

- [ ] `docs/glossary.md` Production Environment 定义无内部矛盾（egress 描述与 capability 描述一致）
- [ ] `docs/glossary.md` 新增 "AI Side Effect" 词条，精确定义边界
- [ ] "零 AI 副作用" 边界可量化（变异 vs 只读）
- [ ] `grep -rn 'zero AI side\|physically blocked' docs/ adr/` 表述一致

## Audit Trail
- 来源审核 run：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- 来源报告：`docs/superpowers/specs/audit-20260803-bfac3ef-report.md`
