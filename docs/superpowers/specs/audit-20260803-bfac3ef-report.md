# 设计审核报告 · llm-reporting

**RUN_ID**：20260803-bfac3ef
**审核范围**：全量（`$AUDIT_SCOPE` 为空）—— `docs/` 全部设计文档 + `adr/` 全部 25 ADR + 图表 + `docs/security|operations|architecture|api` 子目录
**审核日期**：2026-08-03
**仓库 HEAD**：bfac3efd8515f983338a9f39d658e26f792e936e
**基线 ADR**：ADR-0025 统一工作流引擎（2026-07-30）
**审核执行**：单 agent 逐维度自查（design-audit-prompt v4）

## 汇总统计

| 严重程度 | 数量 | 已分配 spec |
|---------|------|-----------|
| 🔴 Critical | 7 | 7 |
| 🟡 Important | 12 | 12 |
| 🟢 Minor | 6 | 6 |
| **合计** | **25** | **25** |

## 维度执行记录

> 每个审过的维度一行，记录执行动作与 finding 数。finding 数 = 0 的维度也列出（证明该维度已审）。

| 维度 | 执行动作（grep 命令/读过的文件/矩阵） | findings 数 |
|------|--------------------------------------|------------|
| A1 完整性 | `grep -rniE 'TODO\|TBD\|FIXME\|占位\|待定\|placeholder'`；读 `docs/api/README.md`；核对 01-facts 版本历史 | 1 |
| A2 术语一致性 | `grep -rniE 'design[ -]plane\|runtime[ -]plane\|intelligence[ -]plane\|freeze[ -]bridge'` 全仓（排除 superpowers/.zcode）；逐文件分类豁免 | 1（合并大组） |
| A3 交叉引用完整性 | `python3 scripts/check_adr_semantics.py`（PASS）+ `python3 scripts/gen_adr_index.py --check`（PASS）；抽检 narrative | 0 |
| A4 计数对等 | `grep` Skills/MCP/Job Types/glossary 行数；交叉对比 01-facts/glossary/03-arch/04-timeline/05-cost；`wc -l 03-architecture.md` | 2 |
| A5 图表-正文同步 | 读全部 4 个 `.mmd` + `c4-model.md` 标签，回正文核对计数/术语 | 1（并入 A2 大组） |
| A6 可验证性 | 深读 01-facts/02-requirement/03-arch/04-timeline/05-cost 数值论断；逐条查出处 | 2（合并大组） |
| A7 无歧义性 | grep 模糊词；深读 "零 AI 副作用" 边界定义 | 1（并入 B5） |
| A8 可追溯性 | 抽样 FR→ADR 链；核对 Decision #N 编号；MCP-ID 一致性 | 2 |
| B1 可靠性（含 LLM 镜像） | 读 03-arch §4/§8/§15-§16 + threat-model + slo-sli；查 agent loop budget/工具幻觉/模型回归 | 2 |
| B2 性能可扩展性 | 读 03-arch §6/§10/§13 容量预估/瓶颈/扩展 | 1 |
| B3 模块边界 | 读 03-arch §13 选型表 + §12.3 DR 表 + Common Compute Subset | 1 |
| B4 可运维性（含 LLM 镜像） | 读 04-timeline Phase 部署/监控计划 + 03-arch §8 日志 | 1 |
| B5 核心约束可执行性 | 读 03-arch §4/§7/§9.3/§17.3.1 + ADR-0005/0006/0025；核对 NetworkPolicy/Sandbox/capability gate 三层 | 1 |
| C1 ADR 质量 | 扫读 25 ADR 的 Context/Options/Decision/Rationale/Consequences | 0 |
| C2 显式权衡 | 抽检关键 ADR tradeoff 论述 | 0 |
| C3 技术选型可行性 | 读 03-arch §13 + 关键假设标注 | 0（并入 B3） |
| C4 成本可行性（含 LLM 镜像） | 深读 05-cost 全 + 04-timeline §D；核对 FX/burden/TCO 完整性/预算熔断建模 | 1（合并大组） |
| C5 风险登记 | 读 04-timeline §B R01-R10 + 查 05-cost 风险册 | 1 |
| D1 STRIDE 威胁建模 | 读 threat-model.md 全 + c4-model.md 组件清单；构造组件×STRIDE 矩阵（见附录 A） | 1（合并大组） |
| D2 身份访问控制 | 读 03-arch §11 + entity-erd.md RBAC/extra_permissions/isolation_level | 1（合并大组） |
| D3 数据保护隐私 | 读 03-arch §5.2/§25 + gdpr-compliance.md；核 LLM 日志留存/删除级联 | 1 |
| D4 合规映射 | 构造法规×控制点矩阵（见附录 B）；查 DPIA/HIPAA/SoD | 1（合并大组） |
| D5 可审计性（含 LLM 镜像） | 读 03-arch §8 + entity-erd.md audit_log；核 append-only/Evidence Packet/LLM 决策链 | 1 |
| D6 LLM 特定危害 | 读 03-arch §17.3.1/§22D + ADR-0025；核 egress 物理阻断论证/HITL/熔断 | 1（并入 B5） |

## Findings 详情

### 🔴 C-001 · NL→Preview SLO 跨文档 5× 矛盾（需求不可达）

- **维度**：A4 计数对等 + B1 可靠性
- **位置**：`docs/02-requirement.md:175`、`docs/operations/slo-sli.md:20-21`
- **证据**：
  > docs/02-requirement.md:175 — "NFR3.1 | Interaction latency in AI Exploration Mode must meet usability requirements (NL→Preview P95 ≤ 3s, follow-up context refresh ≤ 2s) | P1"
  > docs/operations/slo-sli.md:20-21 — "SLI ... Includes: Intent Parsing (~200ms), KB Retrieval (~300ms), LLM Inference (~2-8s), Artifact Build (~500ms), Light Engine Preview (~1-5s). ... SLO Target | p95 ≤ 15 seconds over a 28-day rolling window"
- **问题**：同一关键旅程（NL→Preview），需求文档说 P95 ≤3s，SLO 文档说 P95 ≤15s。按 SLO 文档自带的延迟分解（200+300+2000~8000+500+1000~5000ms = 4-13s 下限），3s 在物理上不可达。两份"当前状态文档"对核心契约给出冲突值。
- **影响**：SLO 是与干系人的核心契约。读者（开发/运维/审计）无法判断真实目标。若按 3s 验收则必然失败；若按 15s 则与需求 P1 冲突。
- **建议**：统一为单一权威值。建议以 slo-sli.md 的 15s 为准（有推导链），将 02-requirement NFR3.1 改为 ≤15s，或在 02-requirement 标注 "see SLO doc for authoritative target"。
- **追踪 spec**：`docs/superpowers/specs/audit-20260803-bfac3ef-C-001-nl-preview-slo-conflict.md`

### 🔴 C-002 · MCP-ID 同文件双映射（jira-sync/confluence-export/compliance-mapper）

- **维度**：A8 可追溯性 + A4 计数对等
- **位置**：`docs/01-facts.md:298`、`docs/01-facts.md:362`
- **证据**：
  > docs/01-facts.md:298 — "21 MCP Servers planned (18 in §22C Core Catalog: MCP-01..17 + MCP-23; plus 3 BRD-pipeline MCPs in §23.8.2: MCP-20 jira-sync, MCP-21 confluence-export, MCP-22 compliance-mapper)."
  > docs/01-facts.md:362 — "New MCPs: MCP-17 (jira-sync), MCP-18 (confluence-export), MCP-19 (compliance-mapper)."
- **问题**：同一文件内，三个工具被分配了两组不同的 ID（MCP-20/21/22 vs MCP-17/18/19）。更严重的是，行 298 同时声称 "MCP-01..17" 为 Core Catalog —— 若 jira-sync 是 MCP-17（行 362），则它同时属于 Core Catalog 与 BRD-pipeline 两组，违反互斥。
- **影响**：MCP 编号是 ADR-0022/0024 引用的硬引用点。ID 冲突导致 §22C MCP 目录、§23.8.2 BRD 集成、glossary 条目全部可追溯性断裂。21 个 MCP 的"完整目录"声明无法自洽。
- **建议**：确立单一权威编号方案。建议保留行 298 的 MCP-20/21/22（与 glossary.md:54 一致），将行 362 改为 MCP-20/21/22，并确认 "Core Catalog = MCP-01..17 + MCP-23" 中的 MCP-17 是另一个工具（需在 §22C 落实）。
- **追踪 spec**：`docs/superpowers/specs/audit-20260803-bfac3ef-C-002-mcp-id-dual-mapping.md`

### 🔴 C-003 · STRIDE 矩阵覆盖 10/20 组件，MCP Gateway（生产 LLM 唯一出口）无威胁行

- **维度**：D1 STRIDE 威胁建模
- **位置**：`docs/security/threat-model.md:14-53`、`docs/architecture/c4-model.md:84-148`、`docs/03-architecture.md:2155`
- **证据**：
  > docs/security/threat-model.md:5 — "STRIDE threat matrix (10 components × 6 dimensions) = 38 threat entries"
  > docs/architecture/c4-model.md:139-148 — 列出 Log Ingestion Svc、Message Bus (Kafka) 等容器，但 threat-model 未覆盖
  > docs/03-architecture.md:2155 — "MCP Gateway is the sole allowed external endpoint" for Production LLM egress
- **问题**：C4 容器图描绘约 20 个容器，STRIDE 仅覆盖 10 个。**未覆盖的关键组件**：MCP Gateway（生产环境 LLM 唯一合法出口，是攻击者必须攻克的咽喉点）、Agent Runtime、Auth Service、Model Registry、Sandbox Pool Manager、Scheduler、Log Ingestion Svc、Message Bus (Kafka)、Object Store、Cloud KMS/Vault、Incident Manager。矩阵 ~22/60 格为空，Repudiation 覆盖仅 3/10。
- **影响**：未建模的威胁 = 未缓解的威胁。MCP Gateway 作为零 AI 副作用的最后执行点，若被攻破（如 namespaceSelector 标签伪造），整个核心约束失效。STRIDE 是 D1 的强制穷举工具，此处穷举失败。
- **建议**：补全 STRIDE 矩阵至覆盖全部 C4 容器，特别是 MCP Gateway（S/T/R/I/D/E 六格全填）+ Agent Runtime。在 C4 图中显式画信任边界（虚线）。
- **追踪 spec**：`docs/superpowers/specs/audit-20260803-bfac3ef-C-003-stride-coverage-gap.md`

### 🔴 C-004 · LLM 交互日志留存全量 prompt/response 7 年，但删除级联表遗漏它（GDPR 抹除权 + 最小化冲突）

- **维度**：D3 数据保护与隐私 + B1 可靠性（数据最小化）
- **位置**：`docs/03-architecture.md:1093`、`docs/03-architecture.md:6306`、`docs/03-architecture.md:6362-6368`、`docs/operations/gdpr-compliance.md:50-57`
- **证据**：
  > docs/03-architecture.md:1093 — "LLM Interaction Log ... Cold: Glacier 7 years (full prompt + response text for debugging)"
  > docs/03-architecture.md:6362-6368 — 抹除级联表仅列 `user_session`/`tenant`/`kb_entry`/`audit_log`/Backups，**无 `llm_interaction_log`**
  > docs/03-architecture.md:441 — "Log system redacts T3 fields before writing"（§5.2 规则）
  > docs/security/threat-model.md:79 — "[WARN] LLM Interaction Log stores complete prompt/response (§8) → ... consider auto-redacting T3 data before LLM"
- **问题**：LLM 交互日志含全量 prompt/response（按定义含 T3 用户数据/PII，threat-model.md:42 已标 P0 风险），留存 7 年 Glacier。但：(a) §5.2 规则要求"日志写入前脱敏 T3"，可 LLM 日志设计未展示脱敏已应用；(b) §25.2 抹除级联表完全遗漏 LLM 日志，DSAR 数据发现（§25.1）也未列 Glacier 冷存。
- **影响**：直接与 GDPR Art.5(1)(c) 最小化原则 + Art.17 抹除权冲突。用户行使抹除权时，其在 LLM 日志中的全量 prompt 历史既不被发现、也不被删除。这是法规级缺陷，非风格问题。
- **建议**：(1) 在 LLM 日志写入前强制 T3 脱敏（实现 §5.2 规则）；(2) 将 LLM 日志加入 §25.2 抹除级联表 + §25.1 DSAR 发现范围；(3) 重新评估 7 年全量留存的必要性（prompt_hash + 元数据可能足够调试）。
- **追踪 spec**：`docs/superpowers/specs/audit-20260803-bfac3ef-C-004-llm-log-retention-erasure.md`

### 🔴 C-005 · 生产 LLM egress 三层防御论证强，但无 CI 一致性测试证明 NetworkPolicy 实际生效

- **维度**：D6 LLM 特定危害 + B5 核心约束可执行性
- **位置**：`docs/03-architecture.md:2096-2158`、`adr/0025-unified-workflow-engine.md:139-165,183`、`docs/03-architecture.md:2108-2151`
- **证据**：
  > docs/03-architecture.md:2158 — "even if the Engine-level check is misconfigured, the NetworkPolicy still blocks LLM API egress ... Auditors can independently verify each layer."
  > adr/0025-unified-workflow-engine.md:183 — 负面后果："NetworkPolicy complexity ... Misconfiguration could accidentally block legitimate traffic or leave unintended LLM API paths open"
  > docs/03-architecture.md:2108-2151 — NetworkPolicy YAML 使用 `namespaceSelector: matchLabels: name: mcp-gateway`
- **问题**：ADR-0025 的三层防御论证本身是**真正的论证**（C-5 正面证据，非仅叙述）。但：(a) ADR-0025 自己列出"误配置"为负面后果，却无对应的 CI 一致性测试证明 NetworkPolicy 实际被应用（§22F.5:4213 仅测跨租户隔离，未测生产 egress 阻断）；(b) YAML 用 `namespaceSelector` 标签选择 mcp-gateway 命名空间——若该标签被误标到恶意命名空间，deny 被绕过，无补充的 podSelector/FQDN 校验。
- **影响**：核心约束"零 AI 副作用"的第二层防御（NetworkPolicy）依赖手工配置正确性，但无自动化验证。误配置可能在审计间隙静默失效。
- **建议**：(1) 增加 CI 测试：部署后尝试从 Production Pod 直连外部 LLM API，断言被 DENY；(2) NetworkPolicy 增补 podSelector 或 Cilium FQDN-based egress；(3) 将 NetworkPolicy 配置纳入 GitOps 版本化 + 审计。
- **追踪 spec**：`docs/superpowers/specs/audit-20260803-bfac3ef-C-005-networkpolicy-conformance-test.md`

### 🔴 C-006 · 监控/告警全部集中在 Phase 8，Phase 3-7 系统无定义的可观测性

- **维度**：B4 可运维性与可观测性
- **位置**：`docs/04-timeline.md:407`、`docs/04-timeline.md:264`（M5.1）、`docs/04-timeline.md:228`（M4.5）
- **证据**：
  > docs/04-timeline.md:407 — "M8.9: Feedback Loop & Telemetry | W36 | Usage analytics, Error rate dashboards, Cost-per-workflow tracking, Model quality monitoring (CI Regression Gate from ADR-0020)"
  > docs/04-timeline.md:228 — Canary/回滚仅在 Phase 4（Freeze Bridge）定义
- **问题**：监控/告警/反馈环**全部**集中在最后一个阶段（Phase 8, W36）。Phase 3（W13-18 设计平面）、Phase 5（W24-28 运行时）、Phase 6（W29-32 企业）、Phase 7（W33-35 高级）部署的组件，在 W14-W35 期间运行**无定义的监控/告警**。Canary/回滚/蓝绿仅描述产品 freeze→canary 管线（Phase 4），组件级部署策略未定义。
- **影响**：Phase 3-7 的故障无法被检测/告警。SLO（C-001 中的 NL→Preview）即使定义了，在 W13-W35 也无 SLI 采集。这是严重的可运维性缺陷——系统在大部分构建期"盲目运行"。
- **建议**：(1) 在 Phase 3 引入基础监控（结构化事件日志 + 错误率仪表板）；(2) 每阶段交付物加"可观测性"验收项；(3) 组件级部署补蓝绿/金丝雀策略。
- **追踪 spec**：`docs/superpowers/specs/audit-20260803-bfac3ef-C-006-monitoring-phase8-only.md`

### 🔴 C-007 · FX 汇率未声明，中美成本对比（核心可行性论点）不可复现

- **维度**：C4 成本与资源可行性
- **位置**：`docs/05-cost.md:46`、`docs/05-cost.md:445`、`docs/05-cost.md:37`、`docs/05-cost.md:179,181`
- **证据**：
  > docs/05-cost.md:46 — "China team ... Subtotal ¥1,072,000 (~$149,000)"（隐含 ~7.19 CNY/USD，未声明）
  > docs/05-cost.md:443-451 — 中美对比表 "Total 3-yr Small ~1:2.5"
  > docs/05-cost.md:37 — "China: ~84-91% total burden"（组件列出但未求和到总数）
  > docs/05-cost.md:179 — "China cloud (Alibaba Cloud) ~$1,454/mo ... (~50% of AWS)"（无逐项推导）
- **问题**：中美成本对比是 cost 文档的核心可行性论点（"~1:2.5 中国优势"），但：(a) CNY→USD 汇率（~7.19）全文未声明、无日期、无来源；(b) 中国负担率 84-91% 列出组件但未求和；(c) 阿里云 ~50% AWS 是断言，无逐资源比价。整个对比不可复现。
- **影响**：成本可行性论点无法验证。若汇率变动或负担率算错，TCO 结论可能反转。决策（如区域选址）建立在不可审计的数字上。
- **建议**：(1) 显式声明汇率 + 日期 + 来源；(2) 负担率给出求和推导；(3) 阿里云 vs AWS 给逐项资源比价或引用第三方对比。
- **追踪 spec**：`docs/superpowers/specs/audit-20260803-bfac3ef-C-007-fx-rate-undeclared.md`

### 🟡 I-008 · ADR-0025 术语迁移残留：当前状态文档大量使用旧 plane 名（A2/A5 大组）

- **维度**：A2 术语一致性 + A5 图表-正文同步
- **位置**：`docs/glossary.md:16,17,86,90,123,135,152`、`docs/03-architecture.md`（22 处）、`docs/02-requirement.md:313,374,431,547`、`docs/04-timeline.md`（12 处，含 Phase 3/4/5 标题）、`docs/05-cost.md`（多处，含成本表行标签）、`docs/architecture/c4-model.md:97,157,158`、`docs/security/threat-model.md:20,25`、`docs/diagrams/system-context.mmd:10-13`、`CONTRIBUTING.md:69`、`docs/operations/slo-sli.md`、`docs/01-facts.md:583`
- **证据**（代表性）：
  > docs/glossary.md:16 — "Light Engine | Lightweight compute engine for the **Design Plane**"（无 legacy 标注）
  > docs/glossary.md:135 — "Query Service ... **Design Plane** assists NL→SQL; **Runtime Plane** executes"（无 legacy 标注）
  > docs/diagrams/system-context.mmd:10-13 — 四个 box 全用旧名：DP["Design Plane"], FB["Freeze Bridge"], RP["Runtime Plane"], IP["Intelligence Plane"]
  > docs/04-timeline.md:176 — "### Phase 3: **Design Plane** (Weeks 13–18)"
  > docs/05-cost.md:63 — 成本表行 "| 3: **Design Plane** | 7.9M ..."
  > docs/cross-reference-checklist.md:6 — 自标 "⚠️ Pending re-verification after ADR-0025"
- **问题**：ADR-0025（2026-07-30）将 Design/Runtime/Intelligence Plane + Freeze Bridge 重命名为 Exploration/Production/Cross-Env Read-Only Mode + Freeze Pipeline。但大量**当前状态文档**（非豁免）仍用旧名作为当前定义：glossary 7 个词条（无 legacy 标注）、03-arch 22 处、04-timeline 12 处（含 Phase 标题）、05-cost 多处（含成本行）、system-context.mmd 四个 box 全旧名。豁免项：ADR 正文（E1）、glossary "Formerly called" 注明（E3）、superseded ADR 列表（E3）。
- **影响**：读者（尤其新成员）无法确定哪个是当前术语。迁移未完成削弱 ADR-0025 的权威性。system-context.mmd 是系统入门图，全旧名造成第一印象错误。
- **建议**：批量替换非豁免处。glossary 7 词条补 legacy 标注或改用新名；system-context.mmd 四个 box 改新名（参考已迁移的 component-exploration-env.mmd）；04-timeline Phase 标题、05-cost 成本行标签、03-arch 正文逐处替换。
- **追踪 spec**：`docs/superpowers/specs/audit-20260803-bfac3ef-I-008-term-migration-residual.md`

### 🟡 I-009 · 246 条 FR 中 0 条有 Given/When/Then 验收标准（文档自承认）

- **维度**：A6 可验证性
- **位置**：`docs/02-requirement.md:22,24`、`docs/02-requirement.md:5`
- **证据**：
  > docs/02-requirement.md:22 — "⚠️ Most current FRs lack testable acceptance criteria and need to be supplemented before entering the development phase."
  > docs/02-requirement.md:24 — "Each functional requirement should include: ... Acceptance Criteria (Given/When/Then testable conditions) ..."
  > docs/02-requirement.md:5 — "Status: Stable"（与 L22 自承认矛盾）
- **问题**：文档自定的写作标准（L24）要求每条 FR 含 Given/When/Then AC，但 L22 自承认"多数 FR 缺 AC"，实测 246 条 FR 中仅 1 条含 AC 关键词。同时 header 标 "Status: Stable" 与"缺 AC"矛盾。
- **影响**：FR 不可测试 = 进入开发阶段无法验收。这是设计阶段→开发阶段的最大鸿沟。
- **建议**：将 "Status" 改为 "Draft" 或补全全部 FR 的 AC。优先为 P0 FR 补 AC。
- **追踪 spec**：`docs/superpowers/specs/audit-20260803-bfac3ef-I-009-fr-acceptance-criteria-missing.md`

### 🟡 I-010 · "零 AI 副作用" 边界无精确定义 + glossary Production 定义自相矛盾

- **维度**：A7 无歧义性 + B5 核心约束可执行性
- **位置**：`docs/glossary.md:13`、`adr/0025-unified-workflow-engine.md:97-100`、`docs/03-architecture.md:1153`
- **证据**：
  > docs/glossary.md:13 — "Production Environment | The deterministic, **zero AI side-effect** production execution environment ... **LLM API egress is physically blocked at NetworkPolicy level**; `llm_reasoning` capabilities beyond `read_analyze`/`suggest_plan` are rejected at Engine submission time."
  > adr/0025-unified-workflow-engine.md:97-100 — Production YAML: `llm.enabled: true`, `allow_llm_api: true`, `allowed_capabilities: [read_analyze, suggest_plan]`
  > docs/03-architecture.md:1153 — "Production Environment may invoke LLMs via `llm_reasoning` Jobs with `read_analyze` or `suggest_plan` capabilities"
- **问题**：(a) glossary 同一定义内自相矛盾——说"egress 物理阻断"又说"超出 read_analyze/suggest_plan 被拒"（暗示这两个能力可触发，需 egress 开放）；(b) ADR-0025 + §9.3 确认生产可调 LLM；(c) 无任何文档定义"什么算副作用"（变异？任何 LLM 调用？仅不可逆？）。"零 AI 副作用"是核心约束却无精确边界。
- **影响**：核心约束歧义 → 防御层设计（C-005）的验收标准不清 → 审计无法判定合规。
- **建议**：(1) glossary Production 定义消除自相矛盾（如改为"LLM egress 仅允许经 MCP Gateway 的 read_analyze/suggest_plan"）；(2) 增"AI side effect"词条精确定义边界（如"任何不可逆的生产状态变更，包括数据写入/配置变更/外部副作用；只读 LLM 推理不算副作用"）。
- **追踪 spec**：`docs/superpowers/specs/audit-20260803-bfac3ef-I-010-zero-ai-side-effect-ambiguity.md`

### 🟡 I-011 · append-only 仅保证 audit_log，LLM 交互日志（携带决策链）无防篡改保证

- **维度**：D5 可审计性与不可否认（含 LLM 镜像）
- **位置**：`docs/architecture/entity-erd.md:91`、`docs/03-architecture.md:1093,6306`、`docs/03-architecture.md:3576`
- **证据**：
  > docs/architecture/entity-erd.md:91 — "`audit_log` is Strictly append-only: no UPDATE or DELETE allowed (enforced by table-level trigger + restricted DB user)."
  > docs/03-architecture.md:1093 — LLM 交互日志流向 "ES 7d → S3 Parquet → Glacier 7yr"，**无 append-only 声明**
- **问题**：防篡改仅由 audit_log 的表级 trigger 保证。但承载 LLM 决策链（prompt+model+output+tool calls）的 LLM 交互日志流经 ES→S3→Glacier，无任何层级声明 append-only/WORM/哈希链。即便 audit_log，DBA 持 `DISABLE TRIGGER` 权限可绕过——无外部篡改证据（如 Merkle 链 + 外存根哈希）。
- **影响**：D5 LLM 镜像强制要求"LLM 决策链入日志/防篡改"。当前决策链日志无防篡改，"零 AI 副作用可证"（C-005 论证的终极目标）在日志层断裂。
- **建议**：(1) LLM 交互日志全层级声明 append-only（S3 Object Lock、Glacier WORM）；(2) 引入哈希链或 Merkle 树，根哈希外存（如独立审计服务）；(3) 限制 DBA 的 DISABLE TRIGGER 权限。
- **追踪 spec**：`docs/superpowers/specs/audit-20260803-bfac3ef-I-011-llm-log-tamper-proof.md`

### 🟡 I-012 · Evidence Packet 仅捕获 Verified Path 决策，Exploration 模式 Agent 查询无结构化决策记录

- **维度**：D5 可审计性（含 LLM 镜像）
- **位置**：`docs/03-architecture.md:2970-2988`
- **证据**：
  > docs/03-architecture.md:2970 — Evidence Packet 捕获 `query/context_snapshot/decision/confidence/alternatives/human_reviewed` —— **仅 Verified Path**（§22A.4）
- **问题**：Evidence Packet（决策理由快照）只为 Verified Path 生成。Exploration 模式下大量 Agent 查询（NL→SQL、归因分析、影响分析）只进 LLM 交互日志（prompt_hash + 元数据），无结构化决策理由记录。多数 LLM 决策缺决策理由。
- **影响**：D5 LLM 镜像要求"LLM 决策链入日志支撑可审计性"。Exploration 决策（虽非生产决策）仍可能影响用户判断，无决策理由则事后无法审计"为何 Agent 这么建议"。
- **建议**：为 Exploration 模式 Agent 查询引入轻量 Evidence Packet（至少捕获 query/retrieved_context/decision/confidence）。
- **追踪 spec**：`docs/superpowers/specs/audit-20260803-bfac3ef-I-012-exploration-evidence-packet.md`

### 🟡 I-013 · 无 DPIA 工件；HIPAA 映射薄弱（无 Breach Notification Rule）；SoD 未显式强制

- **维度**：D4 合规映射
- **位置**：`docs/03-architecture.md:6389-6393`、`docs/operations/gdpr-compliance.md:107`、`docs/03-architecture.md:6343-6345`
- **证据**：
  > docs/03-architecture.md:6389-6393 — Breach Notification 仅引 GDPR Art.33/34（72h），**未提 HIPAA Breach Notification Rule**（向个人 60 天 + HHS/OCR）
  > docs/operations/gdpr-compliance.md:107 — DPO "Advise on Data Protection Impact Assessments (DPIA)" —— **无实际 DPIA 工件**
  > docs/03-architecture.md:6345 — "Designed based on GDPR/CCPA/HIPAA/CSL/DSL/PIPL" 但无逐条映射
- **问题**：(a) 声称 HIPAA 范围但 Breach Notification 仅 GDPR，HIPAA 164.308/310/312/316 各子条款未逐项映射；(b) GDPR Art.35 高风险处理（AI 处理客户财务数据明显属高风险）要求 DPIA，但无 DPIA 工件，仅 DPO 职责提及；(c) SOX ITGC 职责分离（SoD）未显式强制——REVIEWER 是独立 actor 但无硬规则"开发某 Workflow 者不能批准其 Freeze PR"。
- **影响**：合规映射是法规审查的入口。DPIA 缺失 = GDPR 合规硬伤；HIPAA 薄弱 = 医疗客户准入受阻；SoD 未强制 = SOX 审计发现。
- **建议**：(1) 制作 DPIA 工件（gdpr-compliance.md 或独立文件）；(2) 补 HIPAA 逐条映射（含 Breach Notification Rule）；(3) 显式声明 Freeze 审批的 SoD 规则。
- **追踪 spec**：`docs/superpowers/specs/audit-20260803-bfac3ef-I-013-dpia-hipaa-sod.md`

### 🟡 I-014 · 多个无源数值论断（A6 大组）

- **维度**：A6 可验证性
- **位置**：`docs/01-facts.md:22,463-465,546,565`、`docs/03-architecture.md:1118,1264`、`docs/04-timeline.md:49-50`、`docs/05-cost.md:271-278,284-286,343,471-472`
- **证据**（代表性）：
  > docs/01-facts.md:22 — "structured data inference accuracy ~60-70%, complex business metric inference below 50%, based on industry experience estimates, not rigorous experimental data"（"LLM 仅用于探索"哲学的承重前提，自承认无据）
  > docs/01-facts.md:565 — "(Anthropic 2024: -35% retrieval failure alone, -67% with reranking)"（仅年份+机构，无标题/URL/DOI）
  > docs/05-cost.md:343 — "Loop Detection ... Prevents $47K+ runaway loops"（裸数字，无推导）
  > docs/05-cost.md:284 — "Avg. Explorations per Analyst per Day | 5"（运行时 LLM 成本最承重假设，无用户研究来源）
  > docs/03-architecture.md:1118 — "alert volume reduced by 30-40%, MTTR reduced by 50-70% (known patterns)"（"(known patterns)" 模糊手势）
- **问题**：大量数值论断无出处或推导链。承重型数字（如 60-70% 推理准确率支撑"LLM 仅探索"决策；5 次/天 假设乘进全部运行时 LLM TCO；$47K 支撑 ADR-0020 熔断）尤其危险。
- **影响**：设计决策建立在不可审计的数字上。审计/评审无法验证前提。
- **建议**：承重型数字补出处或推导链；无法溯源的标注为"假设"并加入风险登记（C5）。
- **追踪 spec**：`docs/superpowers/specs/audit-20260803-bfac3ef-I-014-unsourced-numerics.md`

### 🟡 I-015 · LLM 镜像缺失：Agent 编排循环无 max-iter/max-token/wall-clock 预算；工具幻觉未防护

- **维度**：B1 可靠性（含 LLM 镜像）
- **位置**：`docs/03-architecture.md:974,1069`（仅 wait=72h, python=30min/4h）、`docs/03-architecture.md:976,154`
- **证据**：
  > docs/03-architecture.md:974 — "`wait` Job: max 72h"
  > docs/03-architecture.md:1069 — "Python Job ... 30min (Design Plane) / 4h (Runtime Plane)"
  > docs/03-architecture.md:976 — `llm_reasoning` "Invoke LLM capabilities through registered MCP Servers and Tools" —— 无工具调用幻觉校验
- **问题**：原则 4 强制要求 B1 查 LLM 失败模式（幻觉/工具幻觉/安全漂移/死循环）。当前：wait/python Job 有超时，但 LLM Agent 编排循环（Skill+MCP，§22A）无 max_rounds/max_tokens/wall-clock 预算（注：§22K.3 有 Loop Detection 三检测器，但那是 Exploration 模式的回路检测，非 Agent 步骤预算）。工具幻觉——LLM 可调用注册表外的工具——无校验（Output Guard §3.2:154 扫"沙箱外代码"，不扫幻觉 MCP 调用）。
- **影响**：LLM 卡在工具调用死循环无定义的熔断；幻觉工具调用可能产生不可追溯的动作。
- **建议**：(1) Agent 编排补 max_rounds（如 10）+ max_tokens + wall-clock；(2) MCP 调用前校验工具名在注册表中。
- **追踪 spec**：`docs/superpowers/specs/audit-20260803-bfac3ef-I-015-agent-loop-tool-hallucination.md`

### 🟡 I-016 · TCO 完整性缺陷：无存储增长模型 + 无生产许可/支持成本

- **维度**：C4 成本可行性
- **位置**：`docs/05-cost.md:215,252-253`、`docs/05-cost.md:6.2-6.4`
- **证据**：
  > docs/05-cost.md:215 — "Log Storage ... Cold 7yr (Glacier)" —— 7 年审计日志累积是重大 TCO 驱动因素
  > docs/05-cost.md:252-253 — "Total Runtime Infra ... $2,911/mo ($34,932/yr)" —— 年度 = 月度×12，**假设零数据增长**
- **问题**：(a) 存储成本无增长模型——7 年审计日志 + KB 增长 + 行为模式积累，年度成本被低估；(b) 生产许可成本缺失（Datadog/New Relic 生产级可观测、SIEM、企业 GitHub、Spark 商业支持）；(c) 厂商支持/维护成本缺失。
- **影响**：TCO 低估，盈亏平衡（§6.7）结论失真。
- **建议**：(1) 加存储增长曲线（如年增 X%）；(2) 补生产许可 + 支持成本项。
- **追踪 spec**：`docs/superpowers/specs/audit-20260803-bfac3ef-I-016-tco-completeness.md`

### 🟡 I-017 · extra_permissions JSONB 无最大范围/审批流；权限缓存 60s 失效完整性未述；双密钥方案未调和

- **维度**：D2 身份与访问控制
- **位置**：`docs/architecture/entity-erd.md:100`、`docs/03-architecture.md:1351`、`docs/architecture/entity-erd.md:63`、`docs/03-architecture.md:1341`
- **证据**：
  > docs/architecture/entity-erd.md:100 — "`user_session.extra_permissions JSONB` allows time-bound ABAC grants `[{"action":"approve_freeze","scope":"workflow:uuid-abc","expires_at":"..."}]`" —— 无最大范围/授权审批流
  > docs/03-architecture.md:1351 — "Permission decisions cached in Redis 60s TTL ... invalidation on role change" —— 失效完整性未述（Kafka 事件丢失则 60s 陈旧权限）
  > docs/architecture/entity-erd.md:63 — "`data_source.connector_config` encrypted at application layer"（Vault 路径引用）vs docs/03-architecture.md:1341 "KMS-managed DEKs" —— 两套并行的密钥方案未调和
- **问题**：(a) extra_permissions 若授权 API 不严，自授=提权向量；(b) 60s 陈旧权限窗口是 EoP 风险，失效机制无完整性保证；(c) Vault 应用层加密 vs KMS DEK 两套密钥管理并存，边界不清。
- **影响**：D2 访问控制多个提权/越权向量。
- **建议**：(1) extra_permissions 授权加审批流 + 最大范围；(2) 权限缓存失效补完整性（如周期性全量同步）；(3) 统一密钥方案或明确边界。
- **追踪 spec**：`docs/superpowers/specs/audit-20260803-bfac3ef-I-017-iam-extra-permissions-keys.md`

### 🟡 I-018 · ADR-0020 预算熔断/降级未在运行时 LLM 成本模型中体现（C4 LLM 镜像）

- **维度**：C4 成本可行性（含 LLM 镜像）
- **位置**：`docs/05-cost.md:269-311`、`docs/05-cost.md:341-343`
- **证据**：
  > docs/05-cost.md:284-286 — "Avg. Explorations per Analyst per Day | 5" —— 运行时 LLM 成本模型假设**无界**使用（5/天、7.5/天扁平）
  > docs/05-cost.md:341 — "Tiered Enforcement; Token Budgets; Loop Detection" —— 引用 ADR-0020 但未成本建模
- **问题**：原则 4 要求 C4 查 token 成本护栏/模型退化检测/预算熔断。ADR-0020 定义 WARN→THROTTLE→DEGRADE→KILL（01-facts:547），但 §4 成本投影假设无界使用，DEGRADE/KILL 激活时的成本场景未建模——成本投影不反映其声称的控制。
- **影响**：成本可行性论证与设计的成本控制机制脱节。
- **建议**：补"熔断激活"成本场景（如 75% 预算时 THROTTLE 对使用率的影响）。
- **追踪 spec**：`docs/superpowers/specs/audit-20260803-bfac3ef-I-018-cost-circuit-breaker-modeling.md`

### 🟡 I-019 · 01-facts "## Supplemental Decisions (ADR #7-#21)" 标题与正文（Decision #8-#25）不符；版本 v1.4→v1.6 跳号

- **维度**：A8 可追溯性 + A1 完整性
- **位置**：`docs/01-facts.md:470`、`docs/01-facts.md:595-599`
- **证据**：
  > docs/01-facts.md:470 — "## 2026-07-04 Supplemental Decisions (ADR **#7-#21**)"
  > docs/01-facts.md:472-581 — 正文从 "### Decision **#8**" 到 "### Decision **#25**"
  > docs/01-facts.md:595→599 — Version History 从 v1.4 跳到 v1.6，无 v1.5 条目
- **问题**：标题声称覆盖 ADR #7-#21，正文实际是 Decision #8-#25（且 Decision #N 是叙事序号非 ADR 号）。版本历史跳号。
- **影响**：读者按标题定位内容会失败。可追溯性断裂。
- **建议**：标题改为"## Supplemental Decisions (Decision #8-#25 / ADR-0008..0025)"或按实际内容校正；补 v1.5 版本条目或说明跳号原因。
- **追踪 spec**：`docs/superpowers/specs/audit-20260803-bfac3ef-I-019-01facts-header-version.md`

### 🟢 M-020 · README 行数标注过时（~6200 vs 实际 6410）

- **维度**：A4 计数对等
- **位置**：`README.md:21`
- **证据**：
  > README.md:21 — "Full architecture design (~6200 lines)" | 实际 `wc -l docs/03-architecture.md` = 6410
- **问题**：行数标注滞后实际 ~210 行。
- **影响**：轻微——读者对文档规模印象偏差。
- **建议**：改为 ~6400 lines 或移除具体数字（避免再次过时）。
- **追踪 spec**：`docs/superpowers/specs/audit-20260803-bfac3ef-M-020-doc-hygiene-minor.md`

### 🟢 M-021 · component-exploration-env.mmd 标"14 Skills"（实际 18）

- **维度**：A5 图表-正文同步
- **位置**：`docs/diagrams/component-exploration-env.mmd:15`
- **证据**：
  > docs/diagrams/component-exploration-env.mmd:15 — "Skill["Skill Engine<br/>**14 Skills**<br/>Skill Chaining"]"
  > docs/glossary.md:55 + 01-facts.md:297 + 03-architecture.md:3072 —— 均为 "**18** composable Skills (S01-S18)"
- **问题**：图表计数滞后（S15-18 在 ADR-0022/0024 后加入）。图表应反映当前状态，无豁免。
- **影响**：轻微——图表与正文计数不一致。
- **建议**：14 Skills → 18 Skills。
- **追踪 spec**：`docs/superpowers/specs/audit-20260803-bfac3ef-M-020-doc-hygiene-minor.md`（与 M-020 同根因"计数过时"合并）

### 🟢 M-022 · cost 文档算术不一致：盈亏平衡分子 $457,464 vs 开发成本 $458,564；Intelligence Plane Small $8 vs 推导 $13.20

- **维度**：A6 可验证性
- **位置**：`docs/05-cost.md:474` vs `:469`、`docs/05-cost.md:308`
- **证据**：
  > docs/05-cost.md:474 — "$457,464 ÷ ($2,000 × 0.60 × 24)" | docs/05-cost.md:469 — "Total Development Cost ... $458,564 (US)"（差 $1,100）
  > docs/05-cost.md:308 — Small Intelligence Plane "$8/mo" | 但 $0.015/query × 40/day × 22d = $13.20/mo
- **问题**：两处算术/转录不一致。
- **影响**：轻微——盈亏平衡结论 ~$1,100 误差；Intelligence 成本低估 ~40%。
- **建议**：校正分子为 $458,564；重算 Small Intelligence 成本。
- **追踪 spec**：`docs/superpowers/specs/audit-20260803-bfac3ef-M-022-cost-arithmetic.md`

### 🟢 M-023 · §13 技术选型表 TigerGraph 单次出现无论证

- **维度**：B3 模块边界 + A7 无歧义性
- **位置**：`docs/03-architecture.md:1831`
- **证据**：
  > docs/03-architecture.md:1831 — "Graph DB | Neo4j / **TigerGraph**" —— TigerGraph 全仓仅此一处出现，无论证、无其他引用
- **问题**：备选技术单次裸出现，无成熟度评估/选型论证。
- **影响**：轻微——读者困惑该选项是否真实候选。
- **建议**：移除 TigerGraph 或补论证。
- **追踪 spec**：`docs/superpowers/specs/audit-20260803-bfac3ef-M-023-tech-selection-minor.md`

### 🟢 M-024 · cross-reference-checklist.md 日期不一致（Last Run 2026-07-30 vs Last Updated 2026-07-09）；§3 glossary 计数过时（101 vs 102）

- **维度**：A1 完整性
- **位置**：`docs/cross-reference-checklist.md:6`、`docs/cross-reference-checklist.md:80`、`docs/cross-reference-checklist.md:58`
- **证据**：
  > docs/cross-reference-checklist.md:6 — "**Last Run**: 2026-07-30"
  > docs/cross-reference-checklist.md:80 — "*This checklist last updated: 2026-07-09*"（同一文档两个"最后"日期）
  > docs/cross-reference-checklist.md:58 — "Glossary: ... 101 entries"（glossary 当前 102）
- **问题**：自标"⚠️ Pending re-verification"；日期不一致；glossary 计数滞后。
- **影响**：轻微——清单可信度受损（自标 stale）。
- **建议**：统一日期；glossary 计数改 102；完成 ADR-0025 后的 re-verification。
- **追踪 spec**：`docs/superpowers/specs/audit-20260803-bfac3ef-M-024-cross-ref-checklist-stale.md`

### 🟢 M-025 · pushdown 10M rows vs 联邦查询 10GB 单位不统一可能冲突；CP5 100 并发测试排在 Phase 8

- **维度**：B2 性能 + B1 可靠性（小问题）
- **位置**：`docs/03-architecture.md:614` vs `:936-937`、`docs/04-timeline.md:447` vs `:405`
- **证据**：
  > docs/03-architecture.md:614 — "max_rows_transferred: 10_000_000"（行） vs :936-937 "≤10GB transfer"（字节）
  > docs/04-timeline.md:447 — "CP5 ... 100 concurrent workflows" 但 100 并发负载测试仅在 M8.7（Phase 8, :405）
- **问题**：(a) 单位不统一可能冲突（10M 窄行≪10GB 双过；10M 宽行≫10GB 单过）；(b) CP5 gate 引用的负载测试排在其后的 Phase 8。
- **影响**：轻微——边界 case 行为不清；gate 顺序不严格。
- **建议**：统一单位或加换算；将 100 并发测试前移至 CP5 前。
- **追踪 spec**：`docs/superpowers/specs/audit-20260803-bfac3ef-M-025-perf-unit-test-order.md`

## 维度总结

- **A1 完整性**：TBD/占位清洁；docs/api/ 有状态说明（正面）。小问题：cross-ref-checklist 自标 stale + 日期不一致（M-024）。
- **A2 术语一致性**：**ADR-0025 迁移未完成**。旧术语残留集中于 glossary（7 词条无 legacy 标注）、03-arch（22 处）、04-timeline（Phase 标题）、05-cost（成本行）、system-context.mmd（四个 box 全旧名）。豁免项已正确识别（ADR 正文 E1、glossary "Formerly called" E3）。
- **A3 交叉引用**：机械检查全绿（check_adr_semantics + gen_adr_index）。无 finding。
- **A4 计数对等**：glossary 102 ✅；Skills 18 一致（除图表 14，M-021）；MCP 21 一致（除 ID 冲突 C-002）；Job Types 10 一致；KB domains 9 一致。SLO 计数矛盾（C-001）。
- **A5 图表同步**：system-context.mmd 全旧名（并入 I-008）；component-exploration-env.mmd Skills=14（M-021）；其余两图已迁移。
- **A6 可验证性**：**FR 普遍缺 AC**（I-009）；大量无源数值（I-014）；算术小错（M-022）。
- **A7 无歧义性**："零 AI 副作用"边界不清（I-010）；TigerGraph 无论证（M-023）。
- **A8 可追溯性**：**MCP-ID 同文件双映射**（C-002）；01-facts 标题不符（I-019）；FR→ADR 追溯普遍缺失（多处 FR1/2/4/5/13 无 ADR）。
- **B1 可靠性（LLM 镜像）**：**SLO 跨文档矛盾**（C-001）；**Agent 循环无预算 + 工具幻觉未防护**（I-015）；其余 SLO 有 SLI 支撑（正面）；Loop Detection 设计存在（正面，仅 Exploration）。
- **B2 性能**：KB 720K records vs 1M embeddings 头寸紧（潜在风险）；无生产容量预估；单位不统一（M-025）。
- **B3 模块边界**：§13 选型表与 PG-First 矛盾；DR 表列 post-MVP 组件如已部署；Common Compute Subset 对 Trino/Ray 歧义（并入 M-023 周边）。
- **B4 可运维性**：**监控全在 Phase 8**（C-006）；Canary 仅产品管线，组件部署无策略。
- **B5 核心约束**：**"零 AI 副作用"边界 + glossary 自相矛盾**（I-010）；**NetworkPolicy 论证强但无 CI 测试**（C-005）；confidence<0.8 与 llm_reasoning 未决无 freeze 拒绝机制（机制化不足）。
- **C1 ADR 质量**：25 ADR 的 Context/Options/Decision/Rationale/Consequences 结构完整（正面）。
- **C2 显式权衡**：抽检 ADR tradeoff 论述充分（正面）。
- **C3 技术选型**：并入 B3。
- **C4 成本（LLM 镜像）**：**FX 未声明**（C-007）；**TCO 缺增长/许可/支持**（I-016）；**熔断未成本建模**（I-018）；无源数字（I-014）。
- **C5 风险登记**：04-timeline R01-R10 存在（正面）；部分缓解是口号；05-cost 无成本风险册。
- **D1 STRIDE**：**矩阵覆盖 10/20，MCP Gateway 缺失**（C-003）；~22 空格；信任边界未画。
- **D2 身份访问**：extra_permissions 无审批流 + 缓存失效完整性 + 双密钥（I-017）。
- **D3 数据保护**：**LLM 日志全量留存 + 删除级联遗漏**（C-004）；T0-T3 分级与控制矩阵完整（正面）。
- **D4 合规映射**：**无 DPIA + HIPAA 薄弱 + SoD 未强制**（I-013）。
- **D5 可审计性（LLM 镜像）**：**LLM 日志无防篡改**（I-011）；**Exploration 决策无 Evidence Packet**（I-012）；audit_log append-only 强（正面）。
- **D6 LLM 特定危害**：**egress 论证强但无 CI 测试**（C-005）；HITL 检查点完整（正面）；熔断设计强（正面）；无禁止输出类别清单；NetworkPolicy namespaceSelector 标签伪造风险。

## 附录 A · STRIDE × 组件 矩阵（完整，含已覆盖格的对策引用）

> 完整矩阵，含已覆盖格的对策引用。空洞格标对应 finding ID。✅ = 有对策（附 doc:line）；⚠️`<ID>` = 未覆盖，转 finding；⚡ = 残余风险已接受（附理由）；➖ = 该组件未进 STRIDE（C-003）。

**已建模组件（10）**：

| 组件 | S 伪造 | T 篡改 | R 抵赖 | I 信息泄露 | D 拒绝服务 | E 提权 |
|------|--------|--------|--------|-----------|-----------|--------|
| Conversation Interface | ✅ tm:16 JWT+RBAC | ✅ tm:17 输入消毒 | ⚠️ C-003 | ⚡ tm:18 Output Guard(M) | ✅ tm:19 32KB cap | ✅ tm:20 AI=suggestion |
| AI Copilot Engine | ⚡ tm:21 预批 provider(M) | ⚡ tm:22 KB 写门(M) | ✅ tm:23 LLM 日志 | ⚡ tm:24 provider 日志泄漏(H) | ⚡ tm:25 多模型(M) | ⚠️ C-003 |
| Spec Refinement Assistant | ⚠️ C-003 | ✅ tm:26 人工 sign-off | ✅ tm:27 不可变审计 | ⚠️ C-003 | ⚠️ C-003 | ⚡ tm:28 Data Owner(M) |
| Workflow Executor | ⚡ tm:29 connector auth(M) | ✅ tm:30 SQL AST+sandbox | ⚠️ C-003 | ⚡ tm:31 日志脱敏(M) | ✅ tm:32 bulkhead+CB | ✅ tm:33 RLS+compile |
| Query Rewriter | ⚠️ C-003 | ✅ tm:34 参数 AST | ⚠️ C-003 | ⚡ tm:35 外层投影(M) | ✅ tm:36 无状态+cache | ⚠️ C-003 |
| Code Graph | ⚡ tm:37 事件签名(M) | ⚠️ C-003 | ⚠️ C-003 | ⚡ tm:38 RBAC 过滤(M) | ✅ tm:39 深度/超时/RR | ⚠️ C-003 |
| KB Write Pipeline | ⚠️ C-003 | ✅ tm:40 confirmed 前置 | ✅ tm:41 版本+审计 | ⚡ tm:42 email PII→LLM(H) | ⚠️ C-003 | ⚡ tm:43 Data Owner(M) |
| Email Ingest Gateway | ⚡ tm:44 SPF/DKIM(M) | ⚡ tm:45 sandbox+25MB(M) | ⚠️ C-003 | ⚠️ C-003 | ✅ tm:46 100/hr 限速 | ⚠️ C-003 |
| Notification Service | ⚡ tm:47 数字签名(M) | ⚠️ C-003 | ⚠️ C-003 | ⚡ tm:48 RBAC 预渲染(M) | ✅ tm:49 DLQ 降级链 | ⚠️ C-003 |
| API Gateway | ⚡ tm:50 JWT 15min+Token Binding(M) | ✅ tm:51 TLS1.3+mTLS | ⚠️ C-003 | ⚠️ C-003 | ⚡ tm:52 CDN+WAF(M) | ✅ tm:53 路由审计 |

**未建模组件（C-003，全部六格空洞）**：Auth Service、MCP Gateway（生产 LLM 唯一出口，咽喉点）、Agent Runtime、Model Registry、Sandbox Pool Manager、Scheduler、Log Ingestion Svc、Message Bus (Kafka)、Object Store (S3/MinIO)、Cloud KMS/Vault、Incident Manager。

**统计**：60 已建模格中 ~24 ✅、~14 ⚡、~22 ⚠️（空）。未建模 11 组件 × 6 = 66 格全空。C4 图信任边界未画。

## 附录 B · 法规 × 控制点 矩阵（完整）

| 法规条目 | 设计控制 | 状态 |
|---------|---------|------|
| GDPR Art.12/15-20 DSAR | docs/operations/gdpr-compliance.md §1（4 阶段, 30d SLA） | ✅ 见 gdpr:7-43 |
| GDPR Art.17 抹除 | docs/03-architecture.md:6362-6368 级联表 | ⚠️ C-004（遗漏 LLM 日志） |
| GDPR Art.33/34 违规通知 | gdpr-compliance.md §6（72h 权力机构） | ✅ 见 gdpr:114-119 |
| GDPR Art.28 DPA | gdpr-compliance.md §3.2 | ✅ 见 gdpr:81-87 |
| GDPR Art.30 ROPA | gdpr-compliance.md:110（DPO 职责） | ⚡ 无实际 ROPA 工件（I-013） |
| GDPR Art.35 DPIA | — | ⚠️ I-013（无工件） |
| GDPR Art.5(1)(c) 最小化 | docs/03-architecture.md:1093 LLM 全量留存 7yr | ⚠️ C-004 |
| HIPAA 164.308 行政保障 | 隐含（RBAC workforce） | ⚡ 薄弱（I-013） |
| HIPAA 164.310 物理保障 | 云厂商责任（未细化） | ⚡ 薄弱（I-013） |
| HIPAA 164.312 技术保障 | docs/03-architecture.md §11 加密/审计/RLS | ✅ |
| HIPAA 164.316 文档化 | — | ⚡ 薄弱（I-013） |
| HIPAA Breach Notification Rule | — | ⚠️ I-013（仅 GDPR 72h，无 HIPAA 60d） |
| SOX §302/§404 | docs/03-architecture.md audit_log + Evidence Packet + Freeze | ✅ 见 03-arch:2990,4300 |
| SOX ITGC 访问管理 | docs/03-architecture.md:1349 RBAC+ABAC | ⚡ 无访问再认证（I-013） |
| SOX ITGC 变更管理 | docs/03-architecture.md §4.2 Freeze+canary + §24.3 schema 迁移 | ✅ |
| SOX ITGC 职责分离 | REVIEWER 独立 actor 但无硬规则 | ⚠️ I-013 |
| SOX ITGC 审计留痕 | docs/architecture/entity-erd.md:91 append-only audit_log | ✅ |
| CSL/DSL/PIPL（PRC） | docs/03-architecture.md:6372-6376 数据驻留 | ✅ |

## 追溯索引引用

完整 finding → spec 映射见 `docs/superpowers/specs/audit-20260803-bfac3ef-index.md`。
