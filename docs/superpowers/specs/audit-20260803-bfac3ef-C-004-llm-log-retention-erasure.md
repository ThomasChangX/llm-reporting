# Audit Fix Spec · LLM 日志全量留存 + 删除级联遗漏（GDPR 冲突）

## 元数据
- **Source Finding(s)**：C-004
- **Severity**：Critical
- **Source Dimensions**：D3, B1
- **Created From Audit**：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- **Status**：open

## 证据

### C-004 · LLM 交互日志全量留存 7 年，删除级联表遗漏
- **位置**：`docs/03-architecture.md:1093`、`docs/03-architecture.md:6306`、`docs/03-architecture.md:6362-6368`、`docs/operations/gdpr-compliance.md:50-57`、`docs/03-architecture.md:441`
- **证据**：
  > docs/03-architecture.md:1093 — "LLM Interaction Log ... Cold: Glacier 7 years (full prompt + response text for debugging)"
  > docs/03-architecture.md:6362-6368 — 抹除级联表列 `user_session`/`tenant`/`kb_entry`/`audit_log`/Backups，**无 `llm_interaction_log`**
  > docs/03-architecture.md:441 — "Log system redacts T3 fields before writing"（§5.2 规则）
  > docs/security/threat-model.md:79 — "[WARN] LLM Interaction Log stores complete prompt/response (§8) → ... consider auto-redacting T3 data before LLM"
  > docs/operations/gdpr-compliance.md:55 — audit_log "No deletion ... PII redaction via masking at query time"
- **问题**：LLM 日志含全量 prompt/response（按定义含 T3/PII），留存 7 年 Glacier。但：(a) §5.2 规则要求"T3 写入前脱敏"，LLM 日志设计未展示脱敏已应用；(b) §25.2 抹除级联表完全遗漏 LLM 日志；(c) §25.1 DSAR 数据发现（"PG + Vector + Graph + S3"）未列 Glacier 冷存。
- **影响**：直接冲突 GDPR Art.5(1)(c) 最小化 + Art.17 抹除权。用户行使抹除权时，其在 LLM 日志的全量 prompt 历史既不被发现也不被删除。法规级缺陷。

## 问题分析（根因）

设计时优先了"可调试性"（全量 prompt/response 留存）与"审计可追溯"，但未与 GDPR 最小化/抹除权原则交叉校验。§5.2 的"T3 写入前脱敏"规则未被 LLM 日志管线吸收（规则存在但应用点未对齐）。抹除级联表与 DSAR 发现范围是早于 LLM 日志设计的产物，扩展时未同步。这是 D3（数据保护）与 B1（数据最小化）的交叉缺陷。

## 修复方案（Fix Plan）

1. **脱敏**：在 LLM 交互日志写入前强制 T3 字段脱敏（实现 §5.2 规则），仅保留 prompt_hash + 元数据 + 脱敏后的 prompt 片段。全量 prompt 仅在短期热存（如 7d ES）保留用于调试，冷存（Glacier）只留脱敏版。
2. **抹除级联**：在 `docs/03-architecture.md:6362-6368` + `docs/operations/gdpr-compliance.md:50-57` 的级联表增加 `llm_interaction_log` 行（如 "脱敏版保留；全量 prompt 在 grace 期后从热存删除；冷存仅脱敏版"）。
3. **DSAR 发现**：在 §25.1 + gdpr-compliance.md §1 第 2 阶段数据发现显式加入 "LLM Interaction Log (ES hot + S3 warm + Glacier cold)"。
4. **重新评估留存期**：评估 7 年全量留存的必要性——若 prompt_hash + 元数据足够审计，全量可缩短至 90d。

## 验收标准（Acceptance Criteria）

- [ ] `docs/03-architecture.md` §8 LLM 日志设计明确"T3 写入前脱敏"
- [ ] §25.2 抹除级联表含 `llm_interaction_log` 行
- [ ] §25.1 + gdpr-compliance.md DSAR 数据发现含 LLM 日志/Glacier
- [ ] threat-model.md LLM06 [WARN] 标记为已解决（脱敏实施）
- [ ] 法规审查能证明 LLM 日志符合 GDPR Art.5(1)(c) 最小化

## Audit Trail
- 来源审核 run：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- 来源报告：`docs/superpowers/specs/audit-20260803-bfac3ef-report.md`
