# Audit Fix Spec · pushdown 单位不统一 + CP5 负载测试排序

## 元数据
- **Source Finding(s)**：M-025
- **Severity**：Minor
- **Source Dimensions**：B2, B1
- **Created From Audit**：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- **Status**：open

## 证据

### M-025 · pushdown 单位不统一 + CP5 测试排序
- **位置**：`docs/03-architecture.md:614` vs `:936-937`、`docs/04-timeline.md:447` vs `:405`
- **证据**：
  > docs/03-architecture.md:614 — "max_rows_transferred: 10_000_000"（行） vs :936-937 "≤10GB transfer"（字节）
  > docs/04-timeline.md:447 — "CP5 ... 100 concurrent workflows" 但 100 并发负载测试仅在 M8.7（Phase 8, :405）
- **问题**：(a) 单位不统一可能冲突（10M 窄行≪10GB 双过；10M 宽行≫10GB 单过）；(b) CP5 gate 引用的负载测试排在其后的 Phase 8。
- **影响**：轻微——边界 case 行为不清；gate 顺序不严格。

## 问题分析（根因）

(a) pushdown 策略（§5.4）用行数限流，联邦查询决策树（§6.3）用字节数限流，两套单位未换算。(b) timeline 的 CP5（Phase 5 末）要求 100 并发，但 100 并发负载测试在 M8.7（Phase 8），时序倒挂。

## 修复方案（Fix Plan）

1. **单位统一**：在 `docs/03-architecture.md` §5.4 或 §6.3 加换算说明，如 "max_rows_transferred 与 max_bytes_transferred 双重限制：取先达者；假定平均行宽 X bytes 推算"。
2. **测试前移**：将 100 并发负载测试从 M8.7（Phase 8）前移至 CP5（Phase 5 末）或 Phase 5 内的某里程碑，使 gate 验证在 gate 声明前完成。

## 验收标准（Acceptance Criteria）

- [ ] `docs/03-architecture.md` pushdown 行数与字节限制有换算/双重说明
- [ ] `docs/04-timeline.md` 100 并发负载测试在 CP5 之前或同时

## Audit Trail
- 来源审核 run：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- 来源报告：`docs/superpowers/specs/audit-20260803-bfac3ef-report.md`
