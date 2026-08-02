# Audit Fix Spec · 预算熔断/降级未在运行时 LLM 成本模型体现（C4 LLM 镜像）

## 元数据
- **Source Finding(s)**：I-018
- **Severity**：Important
- **Source Dimensions**：C4
- **Created From Audit**：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- **Status**：open

## 证据

### I-018 · ADR-0020 预算熔断未成本建模
- **位置**：`docs/05-cost.md:269-311`、`docs/05-cost.md:341-343`
- **证据**：
  > docs/05-cost.md:284-286 — "Avg. Explorations per Analyst per Day | 5" —— 运行时 LLM 成本模型假设**无界**使用
  > docs/05-cost.md:341 — "Tiered Enforcement; Token Budgets; Loop Detection" —— 引用 ADR-0020 但未成本建模
- **问题**：原则 4 要求 C4 查 token 护栏/退化检测/预算熔断。ADR-0020 定义 WARN→THROTTLE→DEGRADE→KILL（01-facts:547），但 §4 成本投影假设无界使用（5/天、7.5/天扁平），DEGRADE/KILL 激活时的成本场景未建模——成本投影不反映其声称的控制。
- **影响**：成本可行性论证与设计的成本控制机制脱节。

## 问题分析（根因）

cost 文档 §4 的运行时 LLM 成本按"扁平使用率"（5 explorations/day、7.5 queries/day）线性外推，未考虑 ADR-0020 的 Tiered Enforcement 会在预算触达时降级/熔断。这使成本既是"乐观估计"（假设无超额使用）又"未反映控制"（DEGRADE 激活时实际成本应低于无界投影）。违反原则 4（C4 LLM 镜像）+ C4（成本可行性）。

## 修复方案（Fix Plan）

1. **补"熔断激活"成本场景**：在 §4 加场景，如：
   - 基线：5 explorations/day（无熔断）
   - 压力：10 explorations/day（75% 预算触发 THROTTLE，实际吞吐降）
   - 极端：20 explorations/day（85% 触发 DEGRADE，模型降级到更便宜，单价变）
   展示 DEGRADE 激活时成本 vs 无界投影的差异。
2. **模型退化成本**：DEGRADE 降级到更便宜模型（如 Claude→DeepSeek）的单价变化反映在场景。
3. **预算上限**：明确每 tenant 的 token 预算上限对月度成本的封顶效应。
4. 可与 I-016（TCO 完整性）一起修订。

## 验收标准（Acceptance Criteria）

- [ ] `docs/05-cost.md` §4 含"熔断激活"成本场景（基线/压力/极端）
- [ ] DEGRADE 模型降级的单价变化反映
- [ ] 每 tenant token 预算上限的封顶效应展示

## Audit Trail
- 来源审核 run：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- 来源报告：`docs/superpowers/specs/audit-20260803-bfac3ef-report.md`
