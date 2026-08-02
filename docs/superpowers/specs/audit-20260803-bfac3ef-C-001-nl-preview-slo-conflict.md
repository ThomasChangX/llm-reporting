# Audit Fix Spec · NL→Preview SLO 跨文档 5× 矛盾

## 元数据
- **Source Finding(s)**：C-001
- **Severity**：Critical
- **Source Dimensions**：A4, B1
- **Created From Audit**：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- **Status**：open（生命周期：`open` → 修复开始置 `in-progress` → 验收通过置 `done`；由后续修复流程更新，非审核阶段）

## 证据（从 findings 报告复制）

### C-001 · NL→Preview SLO 跨文档 5× 矛盾
- **位置**：`docs/02-requirement.md:175`、`docs/operations/slo-sli.md:20-21`
- **证据**：
  > docs/02-requirement.md:175 — "NFR3.1 | Interaction latency in AI Exploration Mode must meet usability requirements (NL→Preview P95 ≤ 3s, follow-up context refresh ≤ 2s) | P1"
  > docs/operations/slo-sli.md:20-21 — "SLI ... Includes: Intent Parsing (~200ms), KB Retrieval (~300ms), LLM Inference (~2-8s), Artifact Build (~500ms), Light Engine Preview (~1-5s). ... SLO Target | p95 ≤ 15 seconds over a 28-day rolling window"
- **问题**：同一关键旅程（NL→Preview），需求文档说 P95 ≤3s，SLO 文档说 P95 ≤15s。按 SLO 文档自带的延迟分解（4-13s 下限），3s 物理不可达。
- **影响**：SLO 是核心契约。读者无法判断真实目标。3s 必然验收失败；15s 与需求 P1 冲突。

## 问题分析（根因）

SLO 数值在两份"当前状态文档"中不一致，违反原则 2（原文核对）与 A4（计数对等）/B1（可靠性）。根因是 SLO 在 slo-sli.md（2026-07-09 更新）细化时引入了推导链（200+300+2000~8000+500+1000~5000ms），但未回写同步 02-requirement.md（2026-07-04，更早）。3s 是早期未分解的乐观值，15s 是分解后的现实值。冲突未被任何 CI 检查捕获（机械检查不覆盖跨文档数值一致性）。

## 修复方案（Fix Plan）

1. 确立单一权威值：建议 **15s**（有推导链，物理可达）。
2. 编辑 `docs/02-requirement.md:175` NFR3.1：将 "NL→Preview P95 ≤ 3s" 改为 "NL→Preview P95 ≤ 15s（权威值见 docs/operations/slo-sli.md Journey 1）"。
3. 或在 02-requirement 加注："本表为概要目标，精确 SLO/SLI 见 docs/operations/slo-sli.md"。
4. 此为内容修改，按 AGENTS.md 需评估是否触及 NFR 的"决策内容"——NFR 非 ADR，可直接编辑（无 immutability 约束）。

## 验收标准（Acceptance Criteria）

- [ ] `grep -rn "NL.*Preview.*3s\|NL.*Preview.*≤ 3" docs/` 仅返回历史快照豁免处（如 ADR 正文）或无返回
- [ ] `docs/02-requirement.md` NFR3.1 与 `docs/operations/slo-sli.md` Journey 1 的 NL→Preview P95 值一致
- [ ] 若改 02-requirement，commit message 说明"同步 SLO 权威值"

## Audit Trail
- 来源审核 run：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- 来源报告：`docs/superpowers/specs/audit-20260803-bfac3ef-report.md`
