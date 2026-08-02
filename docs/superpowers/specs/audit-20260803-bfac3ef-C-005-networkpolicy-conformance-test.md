# Audit Fix Spec · 生产 LLM egress 三层防御无 CI 一致性测试

## 元数据
- **Source Finding(s)**：C-005
- **Severity**：Critical
- **Source Dimensions**：D6, B5
- **Created From Audit**：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- **Status**：open

## 证据

### C-005 · 生产 LLM egress 三层防御论证强，但无 CI 一致性测试
- **位置**：`docs/03-architecture.md:2096-2158`、`adr/0025-unified-workflow-engine.md:139-165,183`、`docs/03-architecture.md:2108-2151`
- **证据**：
  > docs/03-architecture.md:2158 — "even if the Engine-level check is misconfigured, the NetworkPolicy still blocks LLM API egress ... Auditors can independently verify each layer."（论证本身强，正面证据）
  > adr/0025-unified-workflow-engine.md:183 — 负面后果："NetworkPolicy complexity ... Misconfiguration could accidentally block legitimate traffic or leave unintended LLM API paths open"
  > docs/03-architecture.md:2108-2151 — NetworkPolicy YAML 用 `namespaceSelector: matchLabels: name: mcp-gateway`（若标签误标可绕过）
- **问题**：ADR-0025 三层防御论证是真正的论证（C-5 正面安全证据）。但：(a) ADR-0025 自列"误配置"为负面后果，却无 CI 测试证明 NetworkPolicy 实际应用（§22F.5:4213 仅测跨租户隔离）；(b) namespaceSelector 标签选择无补充 podSelector/FQDN 校验。
- **影响**：核心约束第二层防御依赖手工配置正确性，无自动化验证。误配置可能在审计间隙静默失效。

## 问题分析（根因）

ADR-0025 论证了三层防御的"设计意图"，但未规定"持续验证"。跨租户隔离有 §22F.5 测试，但生产 egress 阻断无对应测试——这是覆盖不对称。原则 4（D6）要求"生产环境 LLM egress 物理阻断的论证（非仅叙述）"——论证已有，但"持续可验证"缺失。namespaceSelector 的标签伪造风险是 K8s NetworkPolicy 的已知局限。

## 修复方案（Fix Plan）

1. **CI 一致性测试**：在 `docs/03-architecture.md` §17.3.1 或 §22F.5 补充生产 egress 阻断的自动化测试设计：
   - 部署后从 Production Pod 尝试直连外部 LLM API（如 `curl https://api.anthropic.com`），断言被 DENY。
   - 尝试连 MCP Gateway 443，断言 ALLOW。
   - 测试纳入 CI/CD pipeline 或定期（如每日）运行。
2. **NetworkPolicy 加固**：将 `namespaceSelector: name: mcp-gateway` 补充 `podSelector: role: mcp-gateway`（双选择器），或迁移到 Cilium FQDN-based egress（如 `allow api.anthropic.com`）。
3. **GitOps 版本化**：NetworkPolicy 配置纳入 GitOps 版本化，任何变更经 PR 审批 + 自动 diff 告警。
4. 在 ADR-0025 Consequences 补"已设计 CI 一致性测试"（若需改 ADR 决策内容，用新 superseding ADR；若仅补 Consequences 的实现状态，可酌情）。

## 验收标准（Acceptance Criteria）

- [ ] `docs/03-architecture.md` 有生产 egress 阻断的 CI 测试设计（含 DENY/ALLOW 断言）
- [ ] NetworkPolicy YAML 含双选择器（namespaceSelector + podSelector）或 FQDN-based
- [ ] §22F.5（或新章节）含"production-egress-conformance"测试条目
- [ ] 测试可在 CI 环境复现

## Audit Trail
- 来源审核 run：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- 来源报告：`docs/superpowers/specs/audit-20260803-bfac3ef-report.md`
