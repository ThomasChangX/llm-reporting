# Audit Fix Spec · STRIDE 矩阵覆盖 10/20 组件，MCP Gateway 无威胁行

## 元数据
- **Source Finding(s)**：C-003
- **Severity**：Critical
- **Source Dimensions**：D1
- **Created From Audit**：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- **Status**：open

## 证据

### C-003 · STRIDE 矩阵覆盖 10/20 组件
- **位置**：`docs/security/threat-model.md:14-53`、`docs/architecture/c4-model.md:84-148`、`docs/03-architecture.md:2155`
- **证据**：
  > docs/security/threat-model.md:5 — "STRIDE threat matrix (10 components × 6 dimensions) = 38 threat entries"
  > docs/architecture/c4-model.md:84-148 — C4 容器图描绘约 20 容器（含 Auth Service、MCP Gateway、Agent Runtime、Kafka、Scheduler、Log Ingestion 等）
  > docs/03-architecture.md:2155 — "MCP Gateway is the sole allowed external endpoint" for Production LLM egress
- **问题**：STRIDE 仅覆盖 10/20 组件。未覆盖的关键组件：**MCP Gateway**（生产 LLM 唯一出口，咽喉点）、Agent Runtime、Auth Service、Model Registry、Sandbox Pool Manager、Scheduler、Log Ingestion Svc、Message Bus (Kafka)、Object Store、Cloud KMS/Vault、Incident Manager。已建模的 ~22/60 格为空，Repudiation 覆盖仅 3/10。信任边界未在 C4 图画出。
- **影响**：未建模 = 未缓解。MCP Gateway 若被攻破（如 namespaceSelector 标签伪造），核心约束"零 AI 副作用"失效。

## 问题分析（根因）

STRIDE 威胁建模（threat-model.md，Sync Date 2026-07-04）早于 ADR-0025（2026-07-30）引入的 MCP Gateway 作为生产 LLM 咽喉点。ADR-0025 重构后未回头补全 STRIDE。C4 容器图（c4-model.md）与 STRIDE 矩阵未对齐——STRIDE 仍按早期 10 组件视图。原则 4（D1 矩阵法）要求"组件 × STRIDE 每格显式填"，此处穷举失败。

## 修复方案（Fix Plan）

1. 从 `docs/architecture/c4-model.md` 提取完整组件清单（~20 容器）。
2. 在 `docs/security/threat-model.md` §16.1 补全 STRIDE 矩阵至覆盖全部 C4 容器，**优先 MCP Gateway**（六格全填，引用 §17.3.1 NetworkPolicy + §22D Layer 2 权限门）+ Agent Runtime（§22D Layer 7 Sandbox）。
3. 对现有 10 组件的 ~22 空格逐格补"有对策（引 doc:line）/ 残余风险接受（附理由）/ 未覆盖（本 finding）"。
4. 在 C4 图（c4-model.md）用虚线标信任边界：User→DMZ、DMZ→App Mesh、App→Data、App→MCP Gateway/Internet。
5. 同步更新 `docs/03-architecture.md §16`（STRIDE 章节源）。

## 验收标准（Acceptance Criteria）

- [ ] `docs/security/threat-model.md` STRIDE 矩阵组件数 == C4 容器图容器数
- [ ] MCP Gateway 有独立的 STRIDE 行，六格非空
- [ ] Agent Runtime 有独立的 STRIDE 行
- [ ] C4 图（c4-model.md）含显式信任边界线
- [ ] 矩阵无空格（每格为 ✅/⚡/⚠️ 之一）

## Audit Trail
- 来源审核 run：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- 来源报告：`docs/superpowers/specs/audit-20260803-bfac3ef-report.md`
