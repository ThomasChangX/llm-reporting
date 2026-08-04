# Audit Spec 追溯索引 · 20260803-bfac3ef

**审核 run**：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
**报告**：`audit-20260803-bfac3ef-report.md`
**孤儿检查**：0 孤儿（25 findings 全部映射到 24 specs，M-020+M-021 同根因合并）

## Finding → Spec 映射

| Finding ID | Severity | 标题 | 追踪 spec |
|-----------|---------|------|----------|
| C-001 | 🔴 | NL→Preview SLO 跨文档 5× 矛盾 | audit-20260803-bfac3ef-C-001-nl-preview-slo-conflict.md |
| C-002 | 🔴 | MCP-ID 同文件双映射 | audit-20260803-bfac3ef-C-002-mcp-id-dual-mapping.md |
| C-003 | 🔴 | STRIDE 矩阵覆盖 10/20 组件，MCP Gateway 缺失 | audit-20260803-bfac3ef-C-003-stride-coverage-gap.md |
| C-004 | 🔴 | LLM 日志全量留存 + 删除级联遗漏（GDPR） | audit-20260803-bfac3ef-C-004-llm-log-retention-erasure.md |
| C-005 | 🔴 | 生产 LLM egress 三层防御无 CI 一致性测试 | audit-20260803-bfac3ef-C-005-networkpolicy-conformance-test.md |
| C-006 | 🔴 | 监控/告警全部集中在 Phase 8 | audit-20260803-bfac3ef-C-006-monitoring-phase8-only.md |
| C-007 | 🔴 | FX 汇率未声明，中美成本对比不可复现 | audit-20260803-bfac3ef-C-007-fx-rate-undeclared.md |
| I-008 | 🟡 | ADR-0025 术语迁移残留（旧 plane 名） | audit-20260803-bfac3ef-I-008-term-migration-residual.md |
| I-009 | 🟡 | 246 条 FR 缺验收标准（文档自承认） | audit-20260803-bfac3ef-I-009-fr-acceptance-criteria-missing.md |
| I-010 | 🟡 | "零 AI 副作用" 边界无精确定义 + glossary 自相矛盾 | audit-20260803-bfac3ef-I-010-zero-ai-side-effect-ambiguity.md |
| I-011 | 🟡 | LLM 交互日志无防篡改保证 | audit-20260803-bfac3ef-I-011-llm-log-tamper-proof.md |
| I-012 | 🟡 | Exploration 模式 Agent 查询无 Evidence Packet | audit-20260803-bfac3ef-I-012-exploration-evidence-packet.md |
| I-013 | 🟡 | 无 DPIA + HIPAA 薄弱 + SoD 未强制 | audit-20260803-bfac3ef-I-013-dpia-hipaa-sod.md |
| I-014 | 🟡 | 多个无源数值论断（A6 大组） | audit-20260803-bfac3ef-I-014-unsourced-numerics.md |
| I-015 | 🟡 | Agent 编排循环无预算 + 工具幻觉未防护（LLM 镜像） | audit-20260803-bfac3ef-I-015-agent-loop-tool-hallucination.md |
| I-016 | 🟡 | TCO 完整性缺陷（无存储增长/许可/支持） | audit-20260803-bfac3ef-I-016-tco-completeness.md |
| I-017 | 🟡 | IAM：extra_permissions 无审批 + 缓存失效 + 双密钥 | audit-20260803-bfac3ef-I-017-iam-extra-permissions-keys.md |
| I-018 | 🟡 | 预算熔断/降级未在运行时 LLM 成本模型体现 | audit-20260803-bfac3ef-I-018-cost-circuit-breaker-modeling.md |
| I-019 | 🟡 | 01-facts 标题与正文不符 + 版本跳号 | audit-20260803-bfac3ef-I-019-01facts-header-version.md |
| M-020 | 🟢 | README 行数标注过时（~6200 vs 6410） | audit-20260803-bfac3ef-M-020-doc-hygiene-minor.md（与 M-021 合并） |
| M-021 | 🟢 | component-exploration-env.mmd 标"14 Skills"（实际 18） | audit-20260803-bfac3ef-M-020-doc-hygiene-minor.md（与 M-020 合并） |
| M-022 | 🟢 | cost 文档算术不一致（盈亏分子 + Intelligence Small） | audit-20260803-bfac3ef-M-022-cost-arithmetic.md |
| M-023 | 🟢 | §13 技术选型 TigerGraph 单次出现无论证 | audit-20260803-bfac3ef-M-023-tech-selection-minor.md |
| M-024 | 🟢 | cross-reference-checklist 日期不一致 + glossary 计数过时 | audit-20260803-bfac3ef-M-024-cross-ref-checklist-stale.md |
| M-025 | 🟢 | pushdown 单位不统一 + CP5 负载测试排序 | audit-20260803-bfac3ef-M-025-perf-unit-test-order.md |

## Spec → Finding 映射（反向）

| 追踪 spec | 覆盖 findings | 状态 |
|----------|-------------|------|
| audit-20260803-bfac3ef-C-001-nl-preview-slo-conflict.md | C-001 | open |
| audit-20260803-bfac3ef-C-002-mcp-id-dual-mapping.md | C-002 | open |
| audit-20260803-bfac3ef-C-003-stride-coverage-gap.md | C-003 | open |
| audit-20260803-bfac3ef-C-004-llm-log-retention-erasure.md | C-004 | open |
| audit-20260803-bfac3ef-C-005-networkpolicy-conformance-test.md | C-005 | open |
| audit-20260803-bfac3ef-C-006-monitoring-phase8-only.md | C-006 | open |
| audit-20260803-bfac3ef-C-007-fx-rate-undeclared.md | C-007 | open |
| audit-20260803-bfac3ef-I-008-term-migration-residual.md | I-008 | open |
| audit-20260803-bfac3ef-I-009-fr-acceptance-criteria-missing.md | I-009 | open |
| audit-20260803-bfac3ef-I-010-zero-ai-side-effect-ambiguity.md | I-010 | open |
| audit-20260803-bfac3ef-I-011-llm-log-tamper-proof.md | I-011 | open |
| audit-20260803-bfac3ef-I-012-exploration-evidence-packet.md | I-012 | open |
| audit-20260803-bfac3ef-I-013-dpia-hipaa-sod.md | I-013 | open |
| audit-20260803-bfac3ef-I-014-unsourced-numerics.md | I-014 | open |
| audit-20260803-bfac3ef-I-015-agent-loop-tool-hallucination.md | I-015 | open |
| audit-20260803-bfac3ef-I-016-tco-completeness.md | I-016 | open |
| audit-20260803-bfac3ef-I-017-iam-extra-permissions-keys.md | I-017 | open |
| audit-20260803-bfac3ef-I-018-cost-circuit-breaker-modeling.md | I-018 | open |
| audit-20260803-bfac3ef-I-019-01facts-header-version.md | I-019 | open |
| audit-20260803-bfac3ef-M-020-doc-hygiene-minor.md | M-020, M-021 | open |
| audit-20260803-bfac3ef-M-022-cost-arithmetic.md | M-022 | open |
| audit-20260803-bfac3ef-M-023-tech-selection-minor.md | M-023 | open |
| audit-20260803-bfac3ef-M-024-cross-ref-checklist-stale.md | M-024 | open |
| audit-20260803-bfac3ef-M-025-perf-unit-test-order.md | M-025 | open |

## 统计核验
- findings 总数：25
- spec 总数：24（M-020+M-021 同根因"计数过时"合并为单 spec，两 ID 全列）
- 孤儿 findings：0
- 覆盖率：100%
