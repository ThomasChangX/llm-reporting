# Audit Fix Spec · 多个无源数值论断（A6 大组）

## 元数据
- **Source Finding(s)**：I-014
- **Severity**：Important
- **Source Dimensions**：A6
- **Created From Audit**：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- **Status**：open

## 证据

### I-014 · 无源数值论断（代表性）
- **位置**：`docs/01-facts.md:22,463-465,546,565`、`docs/03-architecture.md:1118,1264`、`docs/04-timeline.md:49-50`、`docs/05-cost.md:271-278,284-286,343,471-472`
- **证据**（代表性）：
  > docs/01-facts.md:22 — "structured data inference accuracy ~60-70%, complex business metric inference below 50%, based on industry experience estimates, not rigorous experimental data"（承重前提，自承认无据）
  > docs/01-facts.md:565 — "(Anthropic 2024: -35% retrieval failure alone, -67% with reranking)"（仅年份+机构，无标题/URL/DOI）
  > docs/05-cost.md:343 — "Loop Detection ... Prevents $47K+ runaway loops"（裸数字，无推导）
  > docs/05-cost.md:284 — "Avg. Explorations per Analyst per Day | 5"（运行时 LLM 成本最承重假设，无来源）
  > docs/03-architecture.md:1118 — "alert volume reduced by 30-40%, MTTR reduced by 50-70% (known patterns)"
- **问题**：大量数值论断无出处或推导链。承重型数字（60-70% 推理准确率、5 次/天、$47K）尤其危险。
- **影响**：设计决策建立在不可审计的数字上。审计/评审无法验证前提。

## 问题分析（根因）

文档混合了"有据数字"（如 SLO 15s 有推导链）与"无据数字"（如 60-70% 推理准确率自承认无据）。承重型无据数字未标注为"假设"也未进风险登记。违反 A6（可验证性：数值需出处或推导链）。注意：ADR 正文内的无据数字属 E1 豁免（决策时刻的合法论断），但 01-facts/03-arch/04-timeline/05-cost 是当前状态文档，不豁免。

## 修复方案（Fix Plan）

1. **承重型数字补出处或推导链**：
   - 01-facts:22 的 60-70%/<50%：若来自某研究，补引用；若无，标注"假设（基于行业经验）"并加入风险登记。
   - 01-facts:565 "Anthropic 2024"：补完整引用（论文标题/URL/DOI，疑为 Anthropic 的 "Contextual Retrieval" 博客，2024-09）。
   - 05-cost:343 "$47K"：补推导（如 X tokens/min × Y min × $Z/M）或引用案例。
   - 05-cost:284 "5 explorations/day"：补来源（用户研究/类比产品）或标注假设。
   - 03-arch:1118 "30-40%/50-70%"：补来源或移除（"(known patterns)" 非证据）。
2. **无法溯源的标"假设"**：统一用"假设（未验证）"标注，加入风险登记（C5/I-018）。
3. **保留 ADR 正文豁免**：不修改 adr/ 下 ADR 正文内的无据数字（E1）。

## 验收标准（Acceptance Criteria）

- [ ] `docs/01-facts.md:22` 的 60-70%/<50% 有引用或标"假设"
- [ ] `docs/01-facts.md:565` "Anthropic 2024" 有完整引用
- [ ] `docs/05-cost.md:343` "$47K" 有推导或案例引用
- [ ] `docs/05-cost.md:284` "5 explorations/day" 有来源或标假设
- [ ] 所有无法溯源的承重数字标"假设"并加入风险登记

## Audit Trail
- 来源审核 run：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- 来源报告：`docs/superpowers/specs/audit-20260803-bfac3ef-report.md`
