# Audit Fix Spec · 监控/告警全部集中在 Phase 8

## 元数据
- **Source Finding(s)**：C-006
- **Severity**：Critical
- **Source Dimensions**：B4
- **Created From Audit**：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- **Status**：open

## 证据

### C-006 · 监控全部集中在 Phase 8，Phase 3-7 无可观测性
- **位置**：`docs/04-timeline.md:407`、`docs/04-timeline.md:228`（M4.5）、`docs/04-timeline.md:264`（M5.1）
- **证据**：
  > docs/04-timeline.md:407 — "M8.9: Feedback Loop & Telemetry | W36 | Usage analytics, Error rate dashboards, Cost-per-workflow tracking, Model quality monitoring (CI Regression Gate from ADR-0020)"
  > docs/04-timeline.md:228 — "M4.5: Canary Gating & Auto-Rollback | W22 | 4-stage canary ..., Gating criteria engine, Auto-rollback mechanism"（Canary 仅产品 freeze 管线）
- **问题**：监控/告警/反馈环全部集中在最后阶段（Phase 8, W36）。Phase 3（W13-18）、Phase 5（W24-28）、Phase 6（W29-32）、Phase 7（W33-35）部署的组件在 W14-W35 运行无定义的监控/告警。Canary/蓝绿仅描述产品 freeze→canary 管线，组件级部署策略未定义。
- **影响**：Phase 3-7 故障无法检测/告警。SLO（如 C-001 的 NL→Preview）即使定义，W13-W35 也无 SLI 采集。严重可运维性缺陷。

## 问题分析（根因）

timeline 文档把"可观测性"当作独立交付物排在最后（M8.9），而非每阶段交付物的横切关注点。这违反 B4（可运维性）原则——监控应随组件同步交付。Canary/回滚同理，仅绑定产品管线（Phase 4 Freeze）而非组件部署。根因 = 可观测性被视为"后期打磨"而非"内置质量属性"。

## 修复方案（Fix Plan）

1. **Phase 3 引入基础监控**：在 M3.x 增加"结构化事件日志 + 错误率仪表板 + 基础告警（如服务宕机）"交付物。
2. **每阶段加可观测性验收项**：在 CP3-CP7（04-timeline:445-449）各加"该阶段组件的 SLI 采集 + 仪表板 + 告警规则"为验收条件。
3. **组件级部署策略**：为 Phase 3（Exploration）、Phase 5（Production）组件部署补蓝绿/金丝雀策略（区别于产品 Freeze 管线）。
4. **SLO 与 SLI 对齐**：将 slo-sli.md 的 5 个 Journey 的 SLI 采集前置到对应阶段（如 Journey 1 NL→Preview 的 SLI 在 Phase 3）。

## 验收标准（Acceptance Criteria）

- [ ] `docs/04-timeline.md` Phase 3-7 各有监控/告警交付物（非仅 Phase 8）
- [ ] CP3-CP7 含可观测性验收项
- [ ] 组件级部署策略（蓝绿/金丝雀）在 Phase 3/5 定义
- [ ] slo-sli.md 每个 Journey 的 SLI 采集 mapped 到对应阶段

## Audit Trail
- 来源审核 run：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- 来源报告：`docs/superpowers/specs/audit-20260803-bfac3ef-report.md`
