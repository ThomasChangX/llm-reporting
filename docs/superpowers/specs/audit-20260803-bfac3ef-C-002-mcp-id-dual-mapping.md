# Audit Fix Spec · MCP-ID 同文件双映射

## 元数据
- **Source Finding(s)**：C-002
- **Severity**：Critical
- **Source Dimensions**：A8, A4
- **Created From Audit**：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- **Status**：done（2026-08-04。`01-facts.md:362` 叙事改为 MCP-20/21/22 + 重编号说明；`adr/0010:60` 加非内容 HTML 注释指向 §23.8.2/glossary（决策内容不动，ADR-0010 未被 supersede——它承载的"BRD/ADR 一等公民"决策仍活跃）。AC 中"§22C MCP-17 非 jira-sync"已核实：MCP-17 = `external-ticketing`）

## 证据

### C-002 · MCP-ID 同文件双映射（jira-sync/confluence-export/compliance-mapper）
- **位置**：`docs/01-facts.md:298`、`docs/01-facts.md:362`
- **证据**：
  > docs/01-facts.md:298 — "21 MCP Servers planned (18 in §22C Core Catalog: MCP-01..17 + MCP-23; plus 3 BRD-pipeline MCPs in §23.8.2: MCP-20 jira-sync, MCP-21 confluence-export, MCP-22 compliance-mapper)."
  > docs/01-facts.md:362 — "New MCPs: MCP-17 (jira-sync), MCP-18 (confluence-export), MCP-19 (compliance-mapper)."
- **问题**：同一文件内三个工具被分配两组不同 ID（MCP-20/21/22 vs MCP-17/18/19）。行 298 "MCP-01..17 Core Catalog" 若 jira-sync=MCP-17（行 362），则同时属 Core 与 BRD 两组，违反互斥。
- **影响**：MCP 编号是 ADR-0022/0024 硬引用点。ID 冲突导致 §22C 目录、§23.8.2 BRD 集成、glossary 条目可追溯性断裂。

## 问题分析（根因）

ADR-0010（2026-07-04）首次引入 BRD-pipeline MCPs 时编号为 MCP-17/18/19（01-facts:362 是该 ADR 的叙事记录）。后 ADR-0024（2026-07-08）扩展 MCP 目录，将 MCP-17 重新分配给 Core Catalog 中的另一个工具，BRD-pipeline 三工具改编号为 MCP-20/21/22（01-facts:298 + glossary:54 反映此更新）。但 01-facts:362 的旧叙事未被同步更新。根因 = 重编号后未做跨文档一致性扫描。

## 修复方案（Fix Plan）

1. 确立权威编号：**MCP-20 (jira-sync), MCP-21 (confluence-export), MCP-22 (compliance-mapper)**（与 glossary:54 一致，反映 ADR-0024 后状态）。
2. 编辑 `docs/01-facts.md:362`：将 "MCP-17 (jira-sync), MCP-18 (confluence-export), MCP-19 (compliance-mapper)" 改为 "MCP-20 (jira-sync), MCP-21 (confluence-export), MCP-22 (compliance-mapper)"。
3. 验证 §22C（03-architecture.md）Core Catalog 中 MCP-01..17 + MCP-23 的 MCP-17 是另一个工具（非 jira-sync），若混淆则一并校正。
4. 全仓 grep "MCP-17\|MCP-18\|MCP-19" 确认无其他残留误引。
5. 注意：01-facts:362 位于 Decision #N 叙事（准 ADR 引用），编辑需谨慎——但 Decision #N 是叙事序号非 ADR 正文，可编辑。

## 验收标准（Acceptance Criteria）

- [ ] `grep -rn "MCP-17 (jira-sync)\|MCP-18 (confluence\|MCP-19 (compliance" docs/ adr/` 无返回
- [ ] `docs/01-facts.md` 行 298 与行 362 的 BRD-pipeline MCP 编号一致（MCP-20/21/22）
- [ ] glossary.md:54 与 01-facts.md 的 MCP 编号一致
- [ ] §22C Core Catalog 的 MCP-17 明确为非 jira-sync 的工具

## Audit Trail
- 来源审核 run：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- 来源报告：`docs/superpowers/specs/audit-20260803-bfac3ef-report.md`
