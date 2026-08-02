# Audit Fix Spec · Agent 编排循环无预算 + 工具幻觉未防护（LLM 镜像）

## 元数据
- **Source Finding(s)**：I-015
- **Severity**：Important
- **Source Dimensions**：B1
- **Created From Audit**：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- **Status**：open

## 证据

### I-015 · Agent 编排循环无预算 + 工具幻觉未防护
- **位置**：`docs/03-architecture.md:974,1069`、`docs/03-architecture.md:976,154`
- **证据**：
  > docs/03-architecture.md:974 — "`wait` Job: max 72h"（仅 wait Job 有超时）
  > docs/03-architecture.md:1069 — "Python Job ... 30min / 4h"（仅 Python Job 有超时）
  > docs/03-architecture.md:976 — `llm_reasoning` "Invoke LLM capabilities through registered MCP Servers and Tools" —— 无工具调用幻觉校验
- **问题**：原则 4 要求 B1 查 LLM 失败模式。wait/python Job 有超时，但 LLM Agent 编排循环（Skill+MCP）无 max_rounds/max_tokens/wall-clock 预算（§22K.3 Loop Detection 是 Exploration 回路检测，非 Agent 步骤预算）。工具幻觉——LLM 可调用注册表外的工具——无校验。
- **影响**：LLM 卡工具调用死循环无熔断；幻觉工具调用可能产生不可追溯动作。

## 问题分析（根因）

设计为 Job 级（wait/python）设了超时，但 LLM Agent 编排是更高层的"循环"（Skill→MCP→Skill），其步数/Token/墙钟预算未定义。§22K.3 的 Loop Detection（Identical-Call/Ping-Pong/Context-Growth）针对 Exploration 模式的重复调用，不覆盖单次 Agent 任务的步数上限。工具幻觉是 LLM 已知失败模式（OWASP LLM07），Output Guard 不扫幻觉 MCP 调用。违反原则 4（B1 LLM 镜像强制）。

## 修复方案（Fix Plan）

1. **Agent 编排预算**：在 `docs/03-architecture.md` §22A 或 §22K 定义 Agent 编排循环的硬预算：
   - `max_rounds`（如 10 步）
   - `max_tokens`（如 50K/任务）
   - `wall_clock_budget`（如 5min/任务）
   - 触达预算 → Circuit Breaker → 返回部分结果 + 告警。
2. **工具幻觉防护**：MCP 调用前校验工具名在注册表中（§22C）；校验失败 → 拒绝 + 记 LLM 交互日志（标"hallucinated_tool"）。
3. **与 Loop Detection 区分**：明确 §22K.3 Loop Detection（Exploration 跨任务回路）vs 新增 Agent 步数预算（单任务内）是两层。
4. 可在 ADR-0020 或新 ADR 记录此决策（若视为决策内容变更）。

## 验收标准（Acceptance Criteria）

- [ ] `docs/03-architecture.md` 定义 Agent 编排 max_rounds/max_tokens/wall_clock_budget
- [ ] MCP 调用前有工具名校验（注册表查询）
- [ ] 预算触达有 Circuit Breaker + 告警
- [ ] Loop Detection（§22K.3）vs Agent 步数预算的层次关系明确

## Audit Trail
- 来源审核 run：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- 来源报告：`docs/superpowers/specs/audit-20260803-bfac3ef-report.md`
