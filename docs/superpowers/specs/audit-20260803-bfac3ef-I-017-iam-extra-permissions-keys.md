# Audit Fix Spec · IAM：extra_permissions 无审批 + 缓存失效 + 双密钥

## 元数据
- **Source Finding(s)**：I-017
- **Severity**：Important
- **Source Dimensions**：D2
- **Created From Audit**：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- **Status**：open

## 证据

### I-017 · extra_permissions 无审批 + 缓存失效完整性 + 双密钥
- **位置**：`docs/architecture/entity-erd.md:100`、`docs/03-architecture.md:1351`、`docs/architecture/entity-erd.md:63`、`docs/03-architecture.md:1341`
- **证据**：
  > docs/architecture/entity-erd.md:100 — "`user_session.extra_permissions JSONB` allows time-bound ABAC grants `[{"action":"approve_freeze","scope":"workflow:uuid-abc","expires_at":"..."}]`" —— 无最大范围/授权审批流
  > docs/03-architecture.md:1351 — "Permission decisions cached in Redis 60s TTL ... invalidation on role change" —— 失效完整性未述
  > docs/architecture/entity-erd.md:63 — "`data_source.connector_config` encrypted at application layer" vs docs/03-architecture.md:1341 "KMS-managed DEKs" —— 两套密钥方案未调和
- **问题**：(a) extra_permissions 若授权 API 不严，自授 = 提权向量；(b) 60s 陈旧权限窗口是 EoP 风险，失效机制无完整性保证（Kafka 事件丢失则 60s 陈旧）；(c) Vault 应用层加密 vs KMS DEK 两套密钥管理并存，边界不清。
- **影响**：D2 多个提权/越权向量。

## 问题分析（根因）

IAM 设计分散在 entity-erd（数据模型）+ 03-arch §11（机制），未做统一威胁审视。extra_permissions 是灵活的 ABAC 机制，但缺乏授权治理（谁能授、授多大）。权限缓存为性能妥协，但失效完整性未保证。密钥管理两套方案（Vault 应用层 for connector_config、KMS DEK for 全局）并存未调和，违反 D2（密钥管理一致性）。这些是 D2 的空洞——见报告 §D2。

## 修复方案（Fix Plan）

1. **extra_permissions 授权治理**：在 §11.2 声明：
   - extra_permissions 只能由 Admin 或上级角色授予（不能自授）
   - 最大范围限制（如单 workflow 级，不可全局）
   - 所有授予记 audit_log
2. **缓存失效完整性**：补周期性全量同步（如每 5min 从 PG 重算权限覆盖 Redis），防 Kafka 事件丢失导致的陈旧窗口。
3. **统一密钥方案**：明确 Vault（密钥存储/轮换）与 KMS（DEK 加密）的边界——如 KMS 管根密钥，Vault 管数据密钥，connector_config 由 Vault DEK 加密（KMS 加密 Vault 根）。消除"两套并行"歧义。
4. 同步 entity-erd.md + 03-arch §11 的密钥描述。

## 验收标准（Acceptance Criteria）

- [ ] `docs/03-architecture.md` §11.2 含 extra_permissions 授权治理（Admin 授 + 最大范围 + audit）
- [ ] 权限缓存含周期性全量同步（防事件丢失）
- [ ] Vault vs KMS 边界明确（无"两套并行"歧义）
- [ ] entity-erd.md + 03-arch §11 密钥描述一致

## Audit Trail
- 来源审核 run：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- 来源报告：`docs/superpowers/specs/audit-20260803-bfac3ef-report.md`
