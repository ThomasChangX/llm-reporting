# Audit Fix Spec · FX 汇率未声明，中美成本对比不可复现

## 元数据
- **Source Finding(s)**：C-007
- **Severity**：Critical
- **Source Dimensions**：C4
- **Created From Audit**：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- **Status**：open

## 证据

### C-007 · FX 汇率未声明，中美成本对比不可复现
- **位置**：`docs/05-cost.md:46`、`docs/05-cost.md:445`、`docs/05-cost.md:37`、`docs/05-cost.md:179,181`
- **证据**：
  > docs/05-cost.md:46 — "China team ... Subtotal ¥1,072,000 (~$149,000)"（隐含 ~7.19 CNY/USD，未声明）
  > docs/05-cost.md:443-451 — 中美对比表 "Total 3-yr Small ~1:2.5"
  > docs/05-cost.md:37 — "China: ~84-91% total burden"（组件列出未求和）
  > docs/05-cost.md:179 — "China cloud (Alibaba Cloud) ~$1,454/mo ... (~50% of AWS)"（无逐项推导）
- **问题**：中美成本对比是核心可行性论点（"~1:2.5 中国优势"），但：(a) CNY→USD 汇率（~7.19）全文未声明、无日期、无来源；(b) 中国负担率 84-91% 组件未求和；(c) 阿里云 ~50% AWS 无逐项比价。整个对比不可复现。
- **影响**：成本可行性论点无法验证。汇率/负担率变动可能反转 TCO 结论。决策（区域选址）建立在不可审计数字上。

## 问题分析（根因）

cost 文档的"中国成本"部分用"~"估算（如 ~$149,000、~50% AWS），但未把这些估算的输入（汇率、负担率组件、云比价）显式化。违反 A6（可验证性）+ C4（成本可行性要求推导链）。承重型论点尤其需要可复现——审计/评审无法验证则决策无基础。

## 修复方案（Fix Plan）

1. **显式声明汇率**：在 `docs/05-cost.md` 开头加"假设"段，声明 "FX rate: 1 USD = 7.19 CNY（来源：[央行中间价/XE.com]，日期：YYYY-MM-DD）"。
2. **负担率求和**：将 §2.1 的中国负担组件（Five Insurances + Housing Fund ~35% + 补充福利 + 办公空间 + 设备 + 管理摊销）显式求和到 84-91%，列公式。
3. **阿里云 vs AWS 逐项**：§2.3 给 AWS 逐资源单价，对阿里云给对应资源单价或引用第三方对比（如 Stratoscale/Forrester），证明 ~50% 因子。
4. **敏感性分析**：补汇率±10%、负担率±5% 对 TCO 的影响（破除"1:2.5"的虚假精确）。
5. 将 FX/负担率/云比价假设加入风险登记（04-timeline §B 或 05-cost 新增成本风险册，见 C5/I-018）。

## 验收标准（Acceptance Criteria）

- [ ] `docs/05-cost.md` 显式声明 FX 汇率 + 日期 + 来源
- [ ] 中国负担率给出求和公式（组件 → 总数）
- [ ] 阿里云 vs AWS 给逐项比价或引用第三方
- [ ] TCO 含汇率/负担率敏感性分析
- [ ] FX 假设加入风险登记

## Audit Trail
- 来源审核 run：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- 来源报告：`docs/superpowers/specs/audit-20260803-bfac3ef-report.md`
