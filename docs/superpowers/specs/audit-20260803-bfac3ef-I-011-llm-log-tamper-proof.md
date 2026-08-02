# Audit Fix Spec · LLM 交互日志无防篡改保证

## 元数据
- **Source Finding(s)**：I-011
- **Severity**：Important
- **Source Dimensions**：D5
- **Created From Audit**：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- **Status**：open

## 证据

### I-011 · append-only 仅 audit_log，LLM 日志无防篡改
- **位置**：`docs/architecture/entity-erd.md:91`、`docs/03-architecture.md:1093,6306`、`docs/03-architecture.md:3576`
- **证据**：
  > docs/architecture/entity-erd.md:91 — "`audit_log` is Strictly append-only: no UPDATE or DELETE allowed (enforced by table-level trigger + restricted DB user)."
  > docs/03-architecture.md:1093 — LLM 交互日志流向 "ES 7d → S3 Parquet → Glacier 7yr"，**无 append-only 声明**
- **问题**：防篡改仅 audit_log 表级 trigger 保证。LLM 交互日志（承载决策链）流经 ES→S3→Glacier，无任何层级声明 append-only/WORM/哈希链。即便 audit_log，DBA 持 `DISABLE TRIGGER` 可绕过——无外部篡改证据。
- **影响**：D5 LLM 镜像要求"LLM 决策链防篡改"。当前决策链日志无防篡改，"零 AI 副作用可证"在日志层断裂。

## 问题分析（根因）

设计优先了 audit_log（SOX 核心审计日志）的 append-only，但未将同等保护延伸到 LLM 交互日志——后者承载 LLM 决策链（prompt+model+output+tools），是证明"零 AI 副作用"的关键证据。原则 4（D5 LLM 镜像）强制要求 LLM 决策链防篡改。audit_log 的 trigger 防护也不够（DBA 可 DISABLE）——需外部篡改证据。

## 修复方案（Fix Plan）

1. **LLM 日志全层级 append-only**：在 `docs/03-architecture.md` §8 + §24.4 明确：
   - ES 层：索引设为 read-only（写入期除外）+ ILM 策略禁止删除。
   - S3 Parquet：启用 S3 Object Lock（WORM 模式）。
   - Glacier：Vault Lock policy（合规模式，不可改）。
2. **哈希链/Merkle 树**：每条 LLM 日志含 prev_hash（链式），定期（如每日）将根哈希外存（独立审计服务或公开日志），提供外部篡改证据。
3. **audit_log 加固**：限制 DBA 的 DISABLE TRIGGER 权限；引入同样的哈希链。
4. 同步更新 `docs/architecture/entity-erd.md` audit_log + LLM 日志的不可变性声明。

## 验收标准（Acceptance Criteria）

- [ ] `docs/03-architecture.md` §8/§24.4 LLM 日志全层级声明 append-only（ES/S3/Glacier）
- [ ] 哈希链或 Merkle 树设计存在，根哈希外存
- [ ] DBA DISABLE TRIGGER 权限受限或哈希链提供外部证据
- [ ] `docs/architecture/entity-erd.md` 不可变性声明覆盖 audit_log + LLM 日志

## Audit Trail
- 来源审核 run：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- 来源报告：`docs/superpowers/specs/audit-20260803-bfac3ef-report.md`
