# Audit Fix Spec · TCO 完整性缺陷（无存储增长/许可/支持）

## 元数据
- **Source Finding(s)**：I-016
- **Severity**：Important
- **Source Dimensions**：C4
- **Created From Audit**：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- **Status**：open

## 证据

### I-016 · TCO 完整性缺陷
- **位置**：`docs/05-cost.md:215,252-253`、`docs/05-cost.md` §6.2-6.4
- **证据**：
  > docs/05-cost.md:215 — "Log Storage ... Cold 7yr (Glacier)" —— 7 年审计日志累积是重大 TCO 驱动
  > docs/05-cost.md:252-253 — "Total Runtime Infra ... $2,911/mo ($34,932/yr)" —— 年度 = 月度×12，**假设零数据增长**
- **问题**：(a) 存储成本无增长模型——7 年审计日志 + KB 增长 + 行为模式积累，年度成本被低估；(b) 生产许可成本缺失（Datadog/New Relic 生产级、SIEM、企业 GitHub、Spark 商业支持）；(c) 厂商支持/维护成本缺失。
- **影响**：TCO 低估，盈亏平衡（§6.7）结论失真。

## 问题分析（根因）

cost 文档的 TCO（§6）把运行时基础设施按"月度×12"算年度，隐含零增长假设。但系统有 7 年审计日志留存（C-004）+ KB 累积 + 行为模式存储，存储是增长型成本。生产许可（可观测、SIEM、企业工具）与厂商支持（Spark/ES/PG 商业支持）是生产 TCO 的常规项，此处缺。违反 C4（TCO 完整性：token+人力+许可+基础设施+存储增长）。

## 修复方案（Fix Plan）

1. **存储增长模型**：在 §3.2 或 §6 加存储增长曲线，如：
   - 审计日志：年增 X%（基于 transaction 量）
   - KB：年增 Y%（基于 tenant/conent）
   - 行为模式：年增 Z%
   - 重算 3 年/5 年 TCO 含增长。
2. **生产许可**：在 §3 加"Production Licensing"项：
   - 可观测（Datadog/New Relic 生产级，~$X/host/mo）
   - SIEM（审计日志分析，~$Y/mo）
   - 企业 GitHub / 工具链
3. **厂商支持**：Spark 商业支持（Databricks）、ES 支持、PG 企业支持（如 Crunchy）。
4. **更新盈亏平衡**：§6.7 用新 TCO 重算盈亏 tenant 数。

## 验收标准（Acceptance Criteria）

- [ ] `docs/05-cost.md` 含存储增长模型（年增率 + 多年 TCO）
- [ ] §3 含生产许可成本项
- [ ] §3 含厂商支持成本项
- [ ] §6.7 盈亏平衡用新 TCO 重算

## Audit Trail
- 来源审核 run：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- 来源报告：`docs/superpowers/specs/audit-20260803-bfac3ef-report.md`
