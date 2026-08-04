# Audit Fix Spec · Exploration 模式 Agent 查询无 Evidence Packet

## 元数据
- **Source Finding(s)**：I-012
- **Severity**：Important
- **Source Dimensions**：D5
- **Created From Audit**：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- **Status**：open

## 证据

### I-012 · Evidence Packet 仅 Verified Path，Exploration 决策无结构化记录
- **位置**：`docs/03-architecture.md:2970-2988`
- **证据**：
  > docs/03-architecture.md:2970 — Evidence Packet 捕获 `query/context_snapshot/decision/confidence/alternatives/human_reviewed` —— **仅 Verified Path**（§22A.4）
- **问题**：Evidence Packet（决策理由快照）只为 Verified Path 生成。Exploration 模式大量 Agent 查询（NL→SQL、归因分析、影响分析）只进 LLM 交互日志（prompt_hash + 元数据），无结构化决策理由。多数 LLM 决策缺决策理由。
- **影响**：D5 LLM 镜像要求 LLM 决策链支撑可审计性。Exploration 决策仍可能影响用户判断，无决策理由则事后无法审计"为何 Agent 这么建议"。

## 问题分析（根因）

Evidence Packet 设计绑定 Verified Path（ mutating 操作的 SOX 合规需求），未扩展到 Exploration（read-only）。但 Exploration 的 Agent 建议（如归因分析、调整建议）虽不直接 mutate，却影响用户决策，事后审计同样需要"为何"。原则 4（D5 LLM 镜像）要求 LLM 决策链入日志——结构化决策理由是关键。

## 修复方案（Fix Plan）

1. **轻量 Exploration Evidence Packet**：在 `docs/03-architecture.md` §22A.4 或 §3.4 定义 Exploration 模式的轻量 Evidence Packet，至少捕获：
   - `query`（用户意图）
   - `retrieved_context`（KB/Code Graph 检索片段引用）
   - `decision`（Agent 输出摘要）
   - `confidence`（置信度）
   - `tools_called`（MCP/Skill 调用链）
2. **与 LLM 交互日志关联**：轻量 Evidence Packet 的 ID 关联到 LLM 交互日志的 prompt_hash，避免重复存储全量 prompt。
3. **保留策略**：Exploration Evidence Packet 留存期可与 LLM 日志一致（见 C-004 修复）。
4. 不必为每条 Exploration 查询生成完整 VP 级 Evidence Packet（成本过高），轻量版即可。

## 验收标准（Acceptance Criteria）

- [ ] `docs/03-architecture.md` 定义 Exploration 模式轻量 Evidence Packet（5 字段）
- [ ] 轻量 Evidence Packet 与 LLM 交互日志关联（ID → prompt_hash）
- [ ] §22A.4 Evidence Packet 章节覆盖 Verified Path + Exploration 两类

## Audit Trail
- 来源审核 run：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- 来源报告：`docs/superpowers/specs/audit-20260803-bfac3ef-report.md`
