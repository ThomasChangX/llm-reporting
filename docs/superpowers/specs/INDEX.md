# Spec 执行索引

> **最后更新**：2026-08-04（首批 spec 修复：7 done / 1 in-progress，见下）
> **活跃 spec 数**：24（覆盖 25 findings；M-020+M-021 同根因合并）| **已归档**：0
> **进度**：7 done（C-001, C-002, I-019, M-020+M-021, M-022, M-023, M-025）· 1 in-progress（M-024 机械项已修，re-verification 待 I-008）· 16 open
> **审核报告**：[`audit-20260803-bfac3ef-report.md`](audit-20260803-bfac3ef-report.md)
> **finding↔spec 追溯索引**：[`audit-20260803-bfac3ef-index.md`](audit-20260803-bfac3ef-index.md)

本项目的 spec 当前全部来自 **2026-08-03 全量设计审核**（`design-audit-prompt.md` v4）。审核覆盖 4 大类 20 维度（机械/架构/可行性/安全合规），产出 25 findings，每个由独立 spec 追踪。spec 的 `## 元数据` 段含 Source Finding(s) / Severity / Source Dimensions / Created From Audit / Status 五字段。

**执行顺序 = 优先级**（见下方分组）。`#编号`为 finding ID（`C-NNN`/`I-NNN`/`M-NNN`），其中字母编码严重程度（🔴 Critical / 🟡 Important / 🟢 Minor）。`Status` 生命周期：`open` → 修复开始置 `in-progress` → 验收通过置 `done`。

---

## 执行队列

### 🔴 P0 — Critical（7 个，最高优先）

> **排序理由**：C-001/C-002 是机械可快速修（跨文档数值/ID 一致性）；C-003/C-004/C-005 涉及安全/合规需设计补全；C-006/C-007 涉及 timeline/cost 重算。建议优先 C-001/C-002（快赢），再处理安全/合规类。

| # | 标题 | 维度 | spec |
|---|------|------|------|
| C-001 | NL→Preview SLO 跨文档 5× 矛盾（3s vs 15s） | A4, B1 | [audit-20260803-bfac3ef-C-001-nl-preview-slo-conflict.md](audit-20260803-bfac3ef-C-001-nl-preview-slo-conflict.md) |
| C-002 | MCP-ID 同文件双映射（MCP-17/18/19 vs MCP-20/21/22） | A8, A4 | [audit-20260803-bfac3ef-C-002-mcp-id-dual-mapping.md](audit-20260803-bfac3ef-C-002-mcp-id-dual-mapping.md) |
| C-003 | STRIDE 矩阵覆盖 10/20 组件，MCP Gateway（生产 LLM 咽喉点）无威胁行 | D1 | [audit-20260803-bfac3ef-C-003-stride-coverage-gap.md](audit-20260803-bfac3ef-C-003-stride-coverage-gap.md) |
| C-004 | LLM 日志全量留存 7 年 + 删除级联遗漏（GDPR Art.5/17 冲突） | D3, B1 | [audit-20260803-bfac3ef-C-004-llm-log-retention-erasure.md](audit-20260803-bfac3ef-C-004-llm-log-retention-erasure.md) |
| C-005 | 生产 LLM egress 三层防御论证强，但无 CI 一致性测试证明 NetworkPolicy 生效 | D6, B5 | [audit-20260803-bfac3ef-C-005-networkpolicy-conformance-test.md](audit-20260803-bfac3ef-C-005-networkpolicy-conformance-test.md) |
| C-006 | 监控/告警全部集中在 Phase 8，Phase 3-7 系统无定义的可观测性 | B4 | [audit-20260803-bfac3ef-C-006-monitoring-phase8-only.md](audit-20260803-bfac3ef-C-006-monitoring-phase8-only.md) |
| C-007 | FX 汇率未声明，中美成本对比（~1:2.5 核心论点）不可复现 | C4 | [audit-20260803-bfac3ef-C-007-fx-rate-undeclared.md](audit-20260803-bfac3ef-C-007-fx-rate-undeclared.md) |

### 🟡 P1 — Important（12 个）

> **排序理由**：I-008 是大批量机械替换（术语迁移），可单独排期一次扫清；I-009 是设计→开发的最大鸿沟（FR 验收标准）；I-013 是合规准入硬门槛（DPIA/HIPAA/SoD）；I-010/I-011/I-012 涉及核心约束"零 AI 副作用"的可证性链；I-015 是 LLM 可靠性镜像；I-014/I-016/I-017/I-018 是可行性论证补强；I-019 是文档卫生。

| # | 标题 | 维度 | spec |
|---|------|------|------|
| I-008 | ADR-0025 术语迁移残留（旧 plane 名散落当前状态文档） | A2, A5 | [audit-20260803-bfac3ef-I-008-term-migration-residual.md](audit-20260803-bfac3ef-I-008-term-migration-residual.md) |
| I-009 | 246 条 FR 中 0 条有 Given/When/Then 验收标准（文档自承认） | A6 | [audit-20260803-bfac3ef-I-009-fr-acceptance-criteria-missing.md](audit-20260803-bfac3ef-I-009-fr-acceptance-criteria-missing.md) |
| I-010 | "零 AI 副作用" 边界无精确定义 + glossary Production 定义自相矛盾 | A7, B5 | [audit-20260803-bfac3ef-I-010-zero-ai-side-effect-ambiguity.md](audit-20260803-bfac3ef-I-010-zero-ai-side-effect-ambiguity.md) |
| I-011 | append-only 仅 audit_log，LLM 交互日志（携带决策链）无防篡改保证 | D5 | [audit-20260803-bfac3ef-I-011-llm-log-tamper-proof.md](audit-20260803-bfac3ef-I-011-llm-log-tamper-proof.md) |
| I-012 | Evidence Packet 仅捕获 Verified Path，Exploration 模式 Agent 查询无结构化决策记录 | D5 | [audit-20260803-bfac3ef-I-012-exploration-evidence-packet.md](audit-20260803-bfac3ef-I-012-exploration-evidence-packet.md) |
| I-013 | 无 DPIA 工件；HIPAA 映射薄弱（无 Breach Notification Rule）；SoD 未显式强制 | D4 | [audit-20260803-bfac3ef-I-013-dpia-hipaa-sod.md](audit-20260803-bfac3ef-I-013-dpia-hipaa-sod.md) |
| I-014 | 多个无源数值论断（A6 大组：推理准确率/Anthropic 引用/$47K/5 次每天） | A6 | [audit-20260803-bfac3ef-I-014-unsourced-numerics.md](audit-20260803-bfac3ef-I-014-unsourced-numerics.md) |
| I-015 | LLM 镜像缺失：Agent 编排循环无 max-iter/max-token/wall-clock 预算；工具幻觉未防护 | B1 | [audit-20260803-bfac3ef-I-015-agent-loop-tool-hallucination.md](audit-20260803-bfac3ef-I-015-agent-loop-tool-hallucination.md) |
| I-016 | TCO 完整性缺陷：无存储增长模型 + 无生产许可/支持成本 | C4 | [audit-20260803-bfac3ef-I-016-tco-completeness.md](audit-20260803-bfac3ef-I-016-tco-completeness.md) |
| I-017 | IAM：extra_permissions JSONB 无最大范围/审批流；权限缓存 60s 失效完整性未述；双密钥方案未调和 | D2 | [audit-20260803-bfac3ef-I-017-iam-extra-permissions-keys.md](audit-20260803-bfac3ef-I-017-iam-extra-permissions-keys.md) |
| I-018 | ADR-0020 预算熔断/降级未在运行时 LLM 成本模型中体现（C4 LLM 镜像） | C4 | [audit-20260803-bfac3ef-I-018-cost-circuit-breaker-modeling.md](audit-20260803-bfac3ef-I-018-cost-circuit-breaker-modeling.md) |
| I-019 | 01-facts "## Supplemental Decisions (ADR #7-#21)" 标题与正文（Decision #8-#25）不符；版本 v1.4→v1.6 跳号 | A8, A1 | [audit-20260803-bfac3ef-I-019-01facts-header-version.md](audit-20260803-bfac3ef-I-019-01facts-header-version.md) |

### 🟢 P2 — Minor（6 findings / 5 specs，低优先批量处理）

> M-020+M-021 同根因（计数过时）已合并为单个 spec。

| # | 标题 | 维度 | spec |
|---|------|------|------|
| M-020, M-021 | README 行数过时（~6200 vs 6410）+ component-exploration-env.mmd 标"14 Skills"（实际 18） | A4, A5 | [audit-20260803-bfac3ef-M-020-doc-hygiene-minor.md](audit-20260803-bfac3ef-M-020-doc-hygiene-minor.md) |
| M-022 | cost 文档算术不一致（盈亏分子 $457,464 vs $458,564；Intelligence Small $8 vs 推导 $13.20） | A6 | [audit-20260803-bfac3ef-M-022-cost-arithmetic.md](audit-20260803-bfac3ef-M-022-cost-arithmetic.md) |
| M-023 | §13 技术选型表 TigerGraph 单次出现无论证 | B3, A7 | [audit-20260803-bfac3ef-M-023-tech-selection-minor.md](audit-20260803-bfac3ef-M-023-tech-selection-minor.md) |
| M-024 | cross-reference-checklist 日期不一致 + glossary 计数过时（101 vs 102） | A1 | [audit-20260803-bfac3ef-M-024-cross-ref-checklist-stale.md](audit-20260803-bfac3ef-M-024-cross-ref-checklist-stale.md) |
| M-025 | pushdown 10M rows vs 联邦查询 10GB 单位不统一 + CP5 100 并发测试排在 Phase 8 | B2, B1 | [audit-20260803-bfac3ef-M-025-perf-unit-test-order.md](audit-20260803-bfac3ef-M-025-perf-unit-test-order.md) |

---

## 依赖关系图

```
─── 设计审核 run 20260803-bfac3ef（HEAD bfac3efd）───

[审核完成] 25 findings, 24 specs, 0 孤儿 ✅
  │
  ├─► 🔴 C-001 SLO 矛盾 ─── 独立（机械修，可立即执行）
  ├─► 🔴 C-002 MCP-ID 冲突 ─── 独立（机械修，需校验 §22C MCP-17）
  │
  ├─► 🔴 安全/合规链（涉及核心约束"零 AI 副作用"可证性）───
  │     ├─► C-003 STRIDE 覆盖（补 MCP Gateway/Agent Runtime 行 + 信任边界）
  │     │     └─ 影响 C-005（NetworkPolicy 验收依赖完整威胁模型）
  │     ├─► C-004 LLM 日志留存/抹除（GDPR 硬伤）
  │     │     └─ 关联 I-011（同日志管线的防篡改）+ I-012（同决策链的 Evidence Packet）
  │     ├─► C-005 NetworkPolicy CI 测试（依赖 I-010 边界定义清晰）
  │     │     └─ 依赖 I-010（"零 AI 副作用"边界明确后才能写验收断言）
  │     └─► I-010 "零 AI 副作用" 边界定义 ─── 阻塞 C-005 验收
  │
  ├─► 🔴 可行性/可运维链 ───
  │     ├─► C-006 监控 Phase 8 ─── 关联 C-001（SLI 采集需随阶段交付）
  │     └─► C-007 FX 汇率 ─── 关联 I-016（TCO 完整性）+ I-018（成本熔断建模）
  │
  ├─► 🟡 术语迁移（大批量机械）───
  │     └─► I-008 ADR-0025 残留 ─── 对应 plan: 2026-07-30-adr-0025-document-alignment.md（已部分执行，剩余由本 spec 驱动）
  │
  ├─► 🟡 可验证性/可追溯性 ───
  │     ├─► I-009 FR AC 缺失（工作量大，建议分批 P0→P1→P2）
  │     ├─► I-014 无源数值（承重型补出处/推导）
  │     ├─► I-019 01-facts 标题/版本（机械修）
  │     └─► I-013 DPIA/HIPAA/SoD（合规准入硬门槛，若目标客户含医疗/上市公司优先）
  │
  ├─► 🟡 LLM 镜像（原则 4 强制）───
  │     ├─► I-015 Agent 循环预算 + 工具幻觉（B1）
  │     ├─► I-011 LLM 日志防篡改（D5，关联 C-004）
  │     └─► I-012 Exploration Evidence Packet（D5）
  │
  ├─► 🟡 可行性补强 ───
  │     ├─► I-016 TCO 完整性（存储增长/许可/支持）
  │     ├─► I-018 成本熔断建模（关联 C-007）
  │     └─► I-017 IAM（extra_permissions/缓存/密钥）
  │
  └─► 🟢 Minor 批量（低优先，M-020+M-021 已合并）
```

---

## 快速参考

| 想做什么 | 看哪个 spec |
|----------|------------|
| 修 SLO 跨文档矛盾（NL→Preview 3s vs 15s） | C-001（P0，机械修） |
| 修 MCP 编号冲突（jira-sync 是 MCP-17 还是 20） | C-002（P0，机械修） |
| 补 STRIDE 威胁模型（MCP Gateway 缺失） | C-003（P0，安全设计补全） |
| 修 LLM 日志 GDPR 抹除冲突 | C-004（P0，法规级） |
| 加 NetworkPolicy CI 一致性测试 | C-005（P0，依赖 I-010 先定义边界） |
| 把监控从 Phase 8 前移 | C-006（P0，可运维性） |
| 声明 FX 汇率让中美对比可复现 | C-007（P0，成本可行性） |
| 完成术语迁移（旧 plane 名） | I-008（P1，大批量机械；对应 plan 已部分执行） |
| 给 FR 补验收标准 | I-009（P1，工作量大分批） |
| 定义"零 AI 副作用"边界 | I-010（P1，阻塞 C-005 验收） |
| 让 LLM 决策链日志防篡改 | I-011（P1，关联 C-004） |
| 给 Exploration 决策加 Evidence Packet | I-012（P1） |
| 做 DPIA / 补 HIPAA / 强制 SoD | I-013（P1，合规准入） |
| 给承重型数字补出处 | I-014（P1） |
| 给 Agent 循环加预算 + 防工具幻觉 | I-015（P1，LLM 镜像） |
| 补 TCO 存储增长/许可/支持 | I-016（P1） |
| 修 IAM extra_permissions/缓存/密钥 | I-017（P1） |
| 把成本熔断场景建模进 TCO | I-018（P1） |
| 修 01-facts 标题/版本跳号 | I-019（P1，机械修） |
| 修 README 行数 + 图表 Skills 计数 | M-020+M-021（P2，已合并） |
| 修 cost 算术错误 | M-022（P2） |
| 处理 TigerGraph 无论证 | M-023（P2） |
| 修 cross-ref-checklist 自标 stale | M-024（P2） |
| 统一 pushdown 单位 + 前移 CP5 测试 | M-025（P2） |

---

## 归档说明

当前无归档 spec（首次设计审核）。后续完成的 spec 移至 `archive/specs/`（待建立），按完成日期排序。审核 run 级产物（report / finding↔spec 追溯 index）保留在 `specs/` 根，不归档——它们是审核 run 的持久记录，供历史趋势对比。

> **审核 run 历史**：
> - `20260803-bfac3ef`（HEAD bfac3efd，全量，25 findings）—— 当前唯一 run

---

## Spec → Plan 映射

| spec | 对应 plan | 状态 |
|------|----------|------|
| I-008（术语迁移残留） | [`../plans/2026-07-30-adr-0025-document-alignment.md`](../plans/2026-07-30-adr-0025-document-alignment.md) | 🟠 plan 已部分执行（ADR-0025 接受 + glossary 4 词条 + 图表重命名已完成；当前状态文档术语残留由 I-008 spec 驱动，修复时另起 plan） |
| 其余 23 spec | ❌ 未写 | spec 进入实施阶段时再创建 plan（避免过早规划） |
