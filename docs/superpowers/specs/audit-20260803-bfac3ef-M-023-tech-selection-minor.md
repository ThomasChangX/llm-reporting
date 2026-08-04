# Audit Fix Spec · §13 技术选型 TigerGraph 单次出现无论证

## 元数据
- **Source Finding(s)**：M-023
- **Severity**：Minor
- **Source Dimensions**：B3, A7
- **Created From Audit**：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- **Status**：done（2026-08-04。移除 §13 选型表两处 `TigerGraph`（L1831 + L1859），仅留 Neo4j——全仓无任何论证/引用，属早期候选残留）

## 证据

### M-023 · TigerGraph 单次出现无论证
- **位置**：`docs/03-architecture.md:1831`
- **证据**：
  > docs/03-architecture.md:1831 — "Graph DB | Neo4j / **TigerGraph**" | TigerGraph 全仓仅此一处出现
- **问题**：备选技术单次裸出现，无成熟度评估/选型论证。
- **影响**：轻微——读者困惑该选项是否真实候选。

## 问题分析（根因）

§13 技术选型表的 Graph DB 行列了 "Neo4j / TigerGraph" 两选项，但全文未对 TigerGraph 做任何论证（vs Neo4j 的对比、为何列、何时选）。这违反 B3（技术选型需成熟度评估）。疑为早期候选未清理。

## 修复方案（Fix Plan）

1. `docs/03-architecture.md:1831` 移除 TigerGraph（若非真实候选），或补一句对比论证（如 "TigerGraph: 备选，适合超大规模图分析；MVP 选 Neo4j，TigerGraph 保留至 Phase 7+ 评估"）。
2. 同步 §13 表的其他选型确保每选项有简短理由。

## 验收标准（Acceptance Criteria）

- [ ] `docs/03-architecture.md` TigerGraph 要么移除要么有简短论证
- [ ] `grep -rn 'TigerGraph' docs/ adr/` 要么无返回要么有上下文论证

## Audit Trail
- 来源审核 run：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- 来源报告：`docs/superpowers/specs/audit-20260803-bfac3ef-report.md`
