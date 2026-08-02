# Design Audit Prompt v3（全方位设计审核 · 单 agent 逐维度自查 + 全量追踪 + 零遗留）

> **用途**：在需要对 llm-reporting 设计仓库做全方位深度审核时，将本文件作为 prompt 反复调用。
> 它不是被动运行的 skill，而是一份操作指令：定义审核维度（rubric）、执行流程、判断标准、输出格式与反偷懒守则。
>
> **调用方式**：将本文件全文 + `$REPO_PATH` 喂给 AI agent，令其按本文件执行。
>
> **变更历史**：
> - **v3**：产物分层 + 零遗留。临时文件（工作笔记/矩阵草稿）在审核结束时清理，仓库只留持久层（报告 + 索引 + 追踪 spec）。
> - **v2**：全量追踪。每个 finding（C/I/M 无例外）由独立 superpowers spec 追踪，零孤儿方可声称完成。

---

## Variables

| 变量 | 值 |
|------|----|
| `$REPO_PATH` | `<填入 llm-reporting 仓库绝对路径>` |
| `$AUDIT_SCOPE` | `<可选：限定审核范围，如 "ADR-0025 迁移完整性" / "安全合规" / 空=全量>` |

---

## 适用对象与审核目标

**审核对象**：llm-reporting 设计仓库（纯文档：6410 行架构主文档、25 个 ADR、46 个 FR 组、102 个术语、4 个 Mermaid 图表）。

**核心特征**：这是一个 **design-phase、documentation-only** 仓库 —— 无应用代码、无运行系统。"正确性"在这里的含义是：
1. **内部一致性**（交叉引用、计数、术语、图表同步）
2. **架构合理性**（设计本身站不站得住）
3. **可行性**（方案能否落地、代价是否被接受）
4. **安全合规充分性**（设计是否充分覆盖了安全/法规要求）

机械部分由 `scripts/check_adr_semantics.py` + CI（markdownlint/lychee/Vale）部分覆盖，但本审核覆盖**语义级、架构级、可行性级**的判断，这些是机器脚本无法完成的。

**审核输出（三部分，缺一不可）**：
1. **A 直接消息**：对话中的汇总（计数/维度覆盖/Top Critical/spec 清单/孤儿检查/下一步）
2. **B findings 报告**：`docs/superpowers/specs/audit-<run-date>-report.md`（C/I/M 分级 + 证据）
3. **C 追踪 spec 文件集**：每个 finding 对应的 superpowers spec + 追溯索引（`audit-<run-date>-index.md`）

**审核输出（三部分，缺一不可 · 详见"输出"段）**：
1. **A 直接消息**：对话中的汇总（计数/维度覆盖/Top Critical/spec 清单/孤儿检查/零遗留确认/下一步）
2. **B findings 报告**：`docs/superpowers/specs/audit-<run-date>-report.md`（C/I/M 分级 + 证据）
3. **C 追踪 spec 文件集**：每个 finding 对应的 superpowers spec + 追溯索引（`audit-<run-date>-index.md`）

审核阶段**仅报告不修复被审文件**（核心原则 6）；追踪 spec 记录修复方案，修复执行是后续独立流程。审核产生的临时文件（工作笔记/矩阵草稿）在结束时清理，仓库**零遗留**（核心原则 8）。

---

## 核心原则（Iron Laws · 每条 finding 级，非阶段级）

### 1. 证据强制（Evidence Iron Law）

**每个 finding 必须引用具体 `文件:行号` + 原文片段作为证据。** 禁止"文档似乎不一致""可能缺少""大体覆盖"这种无锚点的断言。

- 无证据 = 不报告。若无法定位证据，则该问题不值得报告。
- 跨文档一致性 finding，**必须同时引用两处**（矛盾的两份文件各自的行号）。
- 数值类 finding，必须给出文档中的数字 + 推导链断裂点。

### 2. 原文核对，不轻信记忆（No Memory-Based Judgment）

判断前**必须打开/读取真实文件核对**。禁止基于"我之前读到过""印象中""按理说应该"下结论。

- 审核跨文档一致性时，必须同时打开两份文件对照。
- 引用 ADR/§N 时，必须确认目标真实存在（不得假设编号连续）。
- 计数类判断，必须实际 grep 并列出命中行，不允许"grep 过了没问题"而无输出。

### 3. 历史快照 vs 当前状态 区分（Snapshot Exemption）

Accepted ADR 正文中的历史计数/术语是**决策时刻的合法快照**，不算缺陷。只有"当前应反映的状态"不一致才算 finding。

**豁免条件**（满足任一即豁免）：
- 该论断位于某 Accepted ADR 的 Context/Options/Decision/Rationale/Consequences 正文内（不可变决策内容）。
- 该论断显式标注了时间语境（"当时""v1.0 时""from N to M"）。

**非豁免**：架构主文档、timeline、cost、glossary、图表中的过时数字/术语 —— 这些是"当前状态文档"，必须保持最新。

> 实例：ADR-0011 正文说"第 9 个 Job Type"（决策时是第 9 个）= 豁免；
> 但 `component-exploration-env.mmd` 写"14 Skills"而 glossary 说 18 Skills = **finding**（图表应反映当前状态）。

### 4. LLM 镜像强制（LLM Lens Mandatory）

本系统有"零 AI 副作用"核心约束 + 大量 LLM 使用。在以下维度的子检查项中，**必须**检查 LLM 特有失败模式，不得跳过：

| 挂载维度 | 必查的 LLM 镜像 |
|---------|---------------|
| B1 可靠性 | 幻觉 / 工具幻觉 / 安全漂移 / 死循环 的缓解设计 |
| B4 可观测性 | prompt 版本 / 模型版本 / 决策链日志（支撑可审计性） |
| C4 成本可行性 | token 成本护栏 / 模型退化检测 / 预算熔断 |
| D5 可审计性 | LLM 决策链入日志 / 防篡改 |
| D6 LLM 危害 | 生产环境 LLM egress 物理阻断的论证（非仅叙述） |

### 5. 运行时 → 设计时转化（Runtime-to-Design Reframe）

这是纯文档仓库。所有"系统实际表现"类维度（性能 QPS、实际 MTTR、真实成本曲线）转为审**"文档是否充分论证了该维度"**。

判断的是**设计论述的充分性**，不是运行数据：
- 性能 → 文档是否给出容量预估、瓶颈分析、扩展策略，且数值自洽？
- 可靠性 → 文档是否识别故障域、定义 SLO、设计降级路径？
- 成本 → 文档是否估算 TCO 并给出推导？

### 6. 只报告，不修复（Report-Only · 限于审核阶段）

**审核阶段**（步骤 1-6）只产出 findings 报告，不修改任何被审文件。

- 这避免了"审核者自己审、自己修、再自己审"的循环（既当裁判又当运动员）。
- 明显的机械错误（术语残留、计数偏差）同样只报告；修复由后续单独流程（fix spec）处理。
- 审核者可在 finding 的"建议"字段给出修复方向，但不得在审核阶段执行修复。
- **不与原则 7 冲突**：原则 7 要求为每个 finding **创建追踪 spec 文件**（写入 `docs/superpowers/specs/`），这是"创建新文件"而非"修改被审文件" —— 追踪是审核产物，不是修复动作。

### 7. 全量追踪，无孤儿（Universal Tracking · No Orphan Finding）

**每一个 finding —— 不论 Critical / Important / Minor —— 都必须被一个独立的 superpowers spec 追踪。**

- 审核结束时，`findings → specs` 追溯索引中，**finding 总数 == 已分配 spec ID 总数 == 0 孤儿**。
- 一个 spec 可追踪多个同源 findings（见下方分组规则），但**禁止把不同优先级混进同一 spec**（C/I/M 各自独立 spec，便于分级排期）。
- spec 文件命名：`docs/superpowers/specs/audit-<run-date>-<severity>-<seq>-<short-slug>.md`（如 `audit-2026-08-02-I-003-glossary-term-migration.md`）。
- 每个 spec 必须含：finding ID 引用、证据原文、问题分析、修复方案、验收标准（修复如何验证）、追溯回原 finding。
- Minor 不例外：Minor 也要建 spec。批量性 Minor（如多处 typo）可合并为单个 Minor spec，但 ID 必须全部列出。

**spec 分组规则**（决定哪些 findings 合并进同一 spec）：

| 维度 | 同源 → 合并 | 不同源 → 拆分 |
|------|------------|-------------|
| 严重程度 | 同 C / 同 I / 同 M 可合并（若同根因） | **C 与 I 与 M 永不合并**（分级排期需要） |
| 根因 | 同根因（如同一术语迁移残留散落多文件）→ 合并为 1 spec | 不同根因 → 各自 spec |
| 维度 | 同维度同区域可合并 | 跨大类的 findings 即便同根因也建议拆分（修复路径不同） |

### 8. 零遗留，产物分层（No Residue · Tiered Artifacts）

审核产生的所有文件分为两层，**临时层在审核结束时清理，仓库只留下持久层**。

**持久层（保留）** —— 审核结束后仓库存在的全部文件：

| 文件 | 角色 |
|------|------|
| `docs/superpowers/specs/audit-<date>-report.md` | 全局视图：计数 / 维度覆盖 / 所有 findings 汇总 / 维度总结 |
| `docs/superpowers/specs/audit-<date>-index.md` | 追溯索引：finding ↔ spec 双向映射 |
| `docs/superpowers/specs/audit-<date>-<sev>-<seq>-*.md` | N 个追踪 spec（每个含完整证据 + 修复方案 + 验收标准） |

**临时层（审核结束时必须删除）** —— 这些是审核过程的脚手架，其价值已被沉淀进持久层：

- 工作笔记（grep 命令 + 命中行号草稿）
- STRIDE×组件、法规×控制点 矩阵草稿
- 步骤 1 的文件清单 / 术语 grep 列表草稿
- 任何散落的中间 `.md` / `.txt` 草稿

**沉淀规则**（临时层删除前，关键信息必须已进入持久层）：

- 矩阵的每个**空洞** → 已转为 finding → 已进入某 spec 的 `Source Finding(s)` + `Evidence`。完整矩阵不保留，但其结论（哪些格未覆盖）已固化进 spec。
- grep 命中行 → 已进入对应 finding 的 `位置` + `证据` 字段。grep 命令本身不保留。
- 维度总结（每个维度的整体评价）→ 进入报告 `report.md` 的"维度总结"段。

**完成判据**：审核结束时，`docs/superpowers/specs/` 下**只存在**上述持久层三类文件。任何其他文件 = 违规。

---

## 反合理化守则（Anti-Rationalization）

| 模型可能说 | 回应 |
|-----------|------|
| "这个维度文档大体覆盖了，应该没问题" | 必须指出具体章节:行号证明"覆盖了"，并按该维度的子检查项逐条过。笼统覆盖 ≠ 充分论证。 |
| "术语大体一致" | 必须实际 grep 每个关键术语，列出所有出现位置与命中行号。发现冲突才算审过。 |
| "这个数值看起来合理" | 数值类论断（SLA、成本、容量、token）必须找到出处或推导链。无出处 = finding（可验证性缺陷）。 |
| "这是历史快照可以忽略" | 必须验证该论断满足豁免条件（原则 3）。正文叙述中的过时数字不算快照豁免。 |
| "安全设计很全面" | 必须按 STRIDE × 组件 / 法规 × 控制点 矩阵逐格过。"全面"是结论不是证据。 |
| "LLM 相关风险已在别处覆盖" | LLM 镜像是独立检查项（原则 4），必须在每个挂载维度下显式过，不得"已在 X 维度查过"推诿。 |
| "我跳过这个维度因为文档没提" | 文档没提本身就是 finding（完整性缺陷，A1），不是跳过理由。记录为 finding 后继续其他维度。 |
| "Minor 可以不报" | 全报。严重程度由你判断，但报告完整性不打折。 |
| "Minor 不必建 spec，太琐碎" | 禁止。原则 7：所有 finding 不论优先级都要 spec 追踪。批量 Minor 可合并为单个 spec，但 ID 全列。 |
| "这几个 finding 我合并成一个 spec 了" | 必须验证：①同严重程度 ②同根因 ③所有 finding ID 都在 spec 内列出。跨严重程度合并 = 违规。 |
| "这个 finding 和那个差不多，共用一个 spec 就行" | 若根因不同则必须拆分。共用 spec 必须显式列出每个 finding ID + 各自证据，否则 = 孤儿。 |
| "工作笔记/矩阵草稿留着以后参考" | 禁止。原则 8：临时文件必须清理。其价值已沉淀进 spec（证据/空洞）和报告（维度总结）。留着 = 遗留垃圾 = 审核未完成。 |
| "这个中间文件有信息，删了可惜" | 若信息有价值，它必须已进入持久层（spec/报告）。若没进入 = 沉淀失败，应补进 spec 后再删，而非保留草稿。 |
| "我已经整体读过架构文档" | 禁止通读后凭印象。必须按"执行流程"的分批策略读取并记录。 |
| "grep 过了没发现问题" | 必须把 grep 命令 + 命中行号列入工作笔记。无输出的 grep 也要记录命令本身。 |
| "矩阵这一格应该是安全的" | 矩阵每格必须显式填（有对策/无对策-残余风险接受/未覆盖-finding），不得留空或"应该"。 |

---

## 维度 Rubric（主体）

4 大类、20 个维度。每个维度含：**审视问题 / 判断标准 / 常见失败模式**。

> 调用时可设 `$AUDIT_SCOPE` 限定只跑某一类或某几个维度；为空则全量审核。

### 类 A：机械 / 文档卫生（Mechanical & Documentation Hygiene）

纯文档仓库的地基。最高 ROI，大量 findings 产自此处。优先用 grep 工具化处理。

#### A1 · 完整性（Completeness）

- **审视**：所有应有章节/FR/ADR/术语是否齐全？有无 TBD/占位/空引用？占位区是否有说明？
- **标准**：无 TODO/FIXME/TBD 残留于非归档文档（CI 的 `NoTbdTodo` 规则已覆盖部分，但本审核查更广）；占位区明确标注"待定 + 原因 + 依赖"；编号连续无缺漏；`docs/api/` 等空占位有状态说明。
- **失败模式**：占位无说明；§N 引用指向空章节；FR 组声明了但正文无内容；图表引用了不存在的节点。

#### A2 · 术语一致性（Terminology Consistency）

- **审视**：102 个术语在全文用法是否统一？重大架构迁移（如 ADR-0025：Design/Runtime/Intelligence Plane → Exploration/Freeze/Production 三环境）后的新术语是否全文落地？旧术语是否仅残留于豁免处？
- **标准**：grep 每个关键术语，旧术语仅出现在合法豁免处（不可变 ADR 正文 / 历史快照标注 / 不同概念同名如"four-layer memory"）。
- **失败模式**：**迁移残留**（`05-cost.md`/`04-timeline.md`/`system-context.mmd` 仍用"Design Plane"）；同一概念多名混用；术语使用先于 glossary 定义。

#### A3 · 交叉引用完整性（Cross-Reference Integrity）

- **审视**：每个 ADR/FR/§N/术语引用是否都指向存在且正确的目标？双向 supersede 是否一致？narrative 中的"见 ADR-XXXX §Y""如 §Z 所述"是否真实存在？
- **标准**：`check_adr_semantics.py` 全绿（已覆盖 ADR 间引用 + §N 解析）+ 人工抽检 narrative 引用。
- **失败模式**：指向已废弃 ADR（如引用 0004 而非 0012）；supersede 单向；§N 编号因文档编辑偏移；抽取章节后主文档指针未更新。

#### A4 · 计数对等（Count Parity）

- **审视**：跨文件计数是否一致？ADR 数、术语数、Job Type 数、Skill 数、FR 数、MCP 数、数据域数等。
- **标准**：每个"当前状态计数"在所有提及处一致；历史快照豁免（原则 3）。
- **失败模式**：图表"14 Skills" vs glossary/01-facts 的"18 Skills (S01-S18)"；"10 Job Types"在图/正文/glossary 不一致；行数标注过时（README "~6200" vs 实际 6410）。

#### A5 · 图表-正文同步（Diagram-Text Sync）

- **审视**：4 个 `.mmd` 图表的节点标签/计数/命名是否与正文一致？图表是否反映最新架构叙事（ADR-0025 后）？
- **标准**：每个图表元素都能在正文找到对应描述；图表标签用当前术语；图表计数 = 正文计数；架构变更已同步图。
- **失败模式**：图表仍标旧术语（如 `system-context.mmd` 的 "Design Plane"）；图表写 N 个组件但正文说 M 个；新增 ADR-0025 后未更新 `four-plane-arch.mmd`（已删除但替代图是否完整）。

#### A6 · 可验证性（论断可核验，Verifiability）

- **审视**：文档中的数值论断（SLA、延迟、成本、容量、token 数）是否有出处或推导链？每条 FR 是否有验收标准？
- **标准**：数值有"来自 X""基于 Y 推导"；FR 有可测 AC；`02-requirement.md` 自述"多数 FR 缺 AC"本身是 finding。
- **失败模式**：裸数值无来源；FR 只有描述无 AC；成本/token 数字无推导链。

#### A7 · 无歧义性（Unambiguity）

- **审视**：每条需求/决策是否只有一种解读？是否避免"适当""合理""必要时"等模糊词？
- **标准**：关键约束用可量化表述；模糊词要么定义阈值要么替换。
- **失败模式**："适当的安全措施""合理延迟""必要时人工审核"无定义；"零 AI 副作用"无精确边界（什么算副作用）。

#### A8 · 可追溯性（Traceability）

- **审视**：FR→ADR→设计组件→glossary 是否形成可追溯链？每条 FR 能否追溯到干系人需求？每个 ADR 能否追溯到它解决的 FR/约束？
- **标准**：抽样 N 条 FR，每条能正向（FR→设计）和反向（设计→FR）追溯。
- **失败模式**：FR 无对应 ADR；ADR 未关联它解决的 FR/约束；术语使用先于定义。

---

### 类 B：架构 / 设计合理性（Architecture & Design Soundness）

设计本身站不站得住。对应云 Well-Architected 支柱 + ATAM，但审的是文档的**论证充分性**（原则 5）。

#### B1 · 可靠性与故障设计（Reliability & Failure Design）

- **审视**：是否识别故障域、定义 SLO/SLA、设计自动恢复/降级/容灾？故障场景是否枚举？
- **标准**：有 SLO 数值 + 错误预算 + 降级路径 + 容灾 RTO/RPO；关键故障路径有分析。
- **失败模式**：SLO 无错误预算；降级未设计；单点故障未识别。
- **LLM 镜像（强制）**：幻觉 / 工具幻觉（调用不存在的 tool）/ 安全漂移 / 死循环 的缓解设计是否存在？

#### B2 · 性能与可扩展性论证（Performance & Scalability）

- **审视**：是否给出容量预估、瓶颈识别、扩展策略（水平/垂直/缓存/分片/materialize）？数值是否自洽？
- **标准**：容量有推导（用户 × QPS × …）；瓶颈指明组件；扩展策略与瓶颈对应。
- **失败模式**：裸容量无推导；扩展策略与实际瓶颈不对应；数值内部矛盾（如某层吞吐 < 上层需求）。

#### B3 · 模块边界与可演进性（Module Boundary & Evolvability）

- **审视**：模块边界是否清晰？接口是否稳定？扩展点是否显式？改动是否局部化？
- **标准**：每个模块单一职责；接口有版本化/稳定性声明；扩展点（如 Compute Spec 10 Job Type）显式枚举。
- **失败模式**：职责重叠；隐式跨模块依赖；接口无版本策略；"上帝模块"；循环依赖。

#### B4 · 可运维性与可观测性（Operability & Observability）

- **审视**：是否设计监控/告警/日志/追踪/部署/回滚？SLO 是否有对应 SLI？
- **标准**：SLO 有对应 SLI + 告警；日志覆盖审计 + 调试；部署有蓝绿/金丝雀；回滚路径明确。
- **失败模式**：SLO 无对应 SLI；部署无回滚；日志不足以调试。
- **LLM 镜像（强制）**：prompt 版本 / 模型版本 / 决策链日志是否设计？这直接支撑可审计性。

#### B5 · 核心约束的可执行性（Core Constraint Enforceability）

- **审视**："零 AI 副作用""冻结强制性""可逆冻结""BRD/ADR 不可变"等核心约束是否有**机制化保障**而非仅靠文档约定？
- **标准**：约束有强制点（Engine capability gate / NetworkPolicy / Sandbox seccomp / 人工 sign-off gate），非靠叙述约定；防御纵深（多层而非单点）。
- **失败模式**：核心约束只在叙述层声明，无代码/配置级强制；防御层单点（非纵深）；强制点可被绕过。

---

### 类 C：可行性与权衡（Feasibility & Tradeoffs）

方案能否落地、代价是否被接受。ATAM 的 tradeoff/sensitivity/risk 核心。

#### C1 · 备选方案与决策准则（ADR Quality）

- **审视**：每个 ADR 是否列 ≥2 备选？准则是否 MECE（互斥穷尽）？冲突准则是否排序？所选方案理由是否成立？
- **标准**：每 ADR 有 Context/Options/Decision/Rationale/Consequences（MADR 4.0.0）；备选含被拒理由；准则可比较。
- **失败模式**：备选是"稻草人"（明显劣、为衬托所选方案）；准则含糊；决策理由与准则不对应；Options 缺关键候选。

#### C2 · 显式权衡分析（Explicit Tradeoff Analysis）

- **审视**：关键决策是否标出 tradeoff（利好 A 损害 B）？sensitivity point（参数敏感）？
- **标准**：重要决策有"牺牲 X 换 Y"的显式论述；敏感参数标注。
- **失败模式**：决策只谈好处不谈代价；质量属性冲突未识别（如安全 vs 性能、灵活 vs 可审计）。

#### C3 · 技术选型可行性（Tech Selection Feasibility）

- **审视**：所选技术/模型/集成方式是否在当前能力范围内？关键假设是否成立且标注？
- **标准**：选型有成熟度评估；关键假设（如"DeepSeek V4 Pro 在中国可用""PG 可支撑 KB 规模"）标注且可验证；集成有 PoC 或论证。
- **失败模式**：选型无成熟度评估；关键假设隐含且未标注；依赖未发布/不稳定的外部能力。

#### C4 · 成本与资源可行性（Cost & Resource Feasibility）

- **审视**：TCO 估算是否完整（token + 人力 + 许可 + 基础设施 + 存储增长）？是否在预算内？成本护栏是否设计？
- **标准**：TCO 含三类成本（开发一次性 / 运行基础设施 / 运行 LLM）；有 Breakeven 分析；数值有推导。
- **失败模式**：TCO 漏项（如遗漏许可费/存储增长/冗余成本）；成本数字无推导；中美成本对比的汇率/定价假设未标注。
- **LLM 镜像（强制）**：token 成本护栏 / 模型退化检测 / 预算熔断 是否设计？（ADR-0020 相关）

#### C5 · 风险登记与缓解（Risk Register & Mitigation）

- **审视**：是否维护风险登记册？每风险有等级/责任人/缓解或接受决策？
- **标准**：risk register 存在；风险可追溯；缓解措施具体（非口号）。
- **失败模式**：无风险登记；风险描述无等级；"缓解"是口号非措施；风险未关联到具体设计点。

---

### 类 D：安全与合规（Security & Compliance）

独立大类。用**矩阵法**（STRIDE × 组件 / 法规 × 控制点）强迫穷举。矩阵空洞即 finding。

#### D1 · 威胁建模（STRIDE Threat Modeling）

- **审视**：数据流图（C4 Container/Component 图）每个组件 × S/T/R/I/D/E 是否都有对策记录？信任边界是否标注？
- **标准**：构造"组件 × STRIDE"矩阵，每格有对策或"残余风险已接受（附理由）"；信任边界在图中明确。
- **方法**：从 `docs/diagrams/*.mmd` 提取组件清单 → 构造矩阵 → 逐格问"这个组件针对此威胁有对策吗？对策在哪份文档:行号？"。
- **失败模式**：矩阵有空洞；信任边界未画；对策只在部分组件；未覆盖 LLM 引入的新威胁（如 prompt 注入）。

#### D2 · 身份与访问控制（Identity & Access Control）

- **审视**：认证/授权（RBAC/ABAC）/最小权限/密钥凭证管理是否设计？多租户隔离是否充分？
- **标准**：有认证方案；授权模型可审计；密钥轮换；租户隔离有机制（逻辑/物理）+ 论证。
- **失败模式**：授权模型含糊；密钥管理缺失；多租户隔离仅靠逻辑隔离无论证；权限粒度过粗。

#### D3 · 数据保护与隐私（Data Protection & Privacy）

- **审视**：静态/传输加密？数据分级（T0-T3）是否落实对应控制？脱敏/最小化/留存删除策略？DSAR 流程？
- **标准**：加密覆盖静态 + 传输；分级有对应控制矩阵；留存有策略；DSAR（数据主体访问请求）流程设计。
- **失败模式**：分级定义了但无对应控制；留存策略缺失；DSAR 流程空洞；PII 检测未设计。

#### D4 · 合规映射（SOX/HIPAA/GDPR Compliance Mapping）

- **审视**：是否逐条映射法规要求到设计控制？DPIA？RoPA？ITGC（访问管理/变更管理/职责分离/审计留痕）？
- **标准**：构造"法规条目 × 设计控制"矩阵；关键控制（ITGC）逐项有设计；DPIA 有证据。
- **失败模式**：矩阵空洞；ITGC 缺项（如职责分离 SoD 未设计）；无 DPIA 证据；合规声明是口号非映射。

#### D5 · 可审计性与不可否认（Auditability & Non-Repudiation）

- **审视**：操作/变更/决策日志是否完整且防篡改？是否满足抵赖对抗？
- **标准**：三类日志（操作/变更/决策）覆盖；日志写入只追加（append-only）；审计日志与操作日志分离。
- **失败模式**：日志可篡改；审计日志与操作日志未分离；日志留存期不足。
- **LLM 镜像（强制）**：LLM 决策链（prompt + 模型版本 + 输出 + tool calls）是否入日志？这决定"零 AI 副作用"是否可证。

#### D6 · LLM 特定危害（LLM-Specific Harms）

- **审视**：是否定义禁止输出类别？越狱/prompt 注入/PII 泄漏防护？内容过滤？人在环路（HITL）关键点？降级/熔断？
- **标准**：禁止类别定义；过滤层设计；HITL 关键点标注（冻结/发布/写回/KB 写入）；**生产环境 LLM egress 物理阻断（NetworkPolicy）的论证**。
- **失败模式**：无内容过滤；HITL 点含糊；"零 AI 副作用"无物理强制论证（仅叙述层声明，见 B5）。

---

## 执行流程（7 步 · 单 agent 逐维度自查）

### 步骤 1 · 范围界定与索引

- 读 `AGENTS.md`（根 + `docs/AGENTS.md` + `adr/AGENTS.md`）—— 这些定义"什么算正确"。
- 读 `glossary.md`（102 术语）+ `docs/adr-index.md`（25 ADR 概览）+ `docs/README.md`（阅读顺序）+ `adr/README.md`。
- 读 `cross-reference-checklist.md` —— 注意它若自标记"待对齐"，这本身就是线索。
- **产出**：审核文件清单（明确每个要读的文件）+ 关键术语 grep 列表（用于步骤 2）。**这些是临时产物**（原则 8），在步骤 7 清理；其价值会被消耗在后续步骤的 grep 执行和 findings 里。
- 若设了 `$AUDIT_SCOPE`，在此裁剪范围（如只审"ADR-0025 迁移"则聚焦 A2/A3/A4/A5）。

### 步骤 2 · 机械类批量扫描（A1-A8）

最高 ROI 步骤。大量 findings 产自此处。**优先用 grep 工具化**。

- **术语迁移完整性**：对 ADR-0025 定义的每个新/旧术语对（Design Plane→Exploration Environment 等），grep 全仓，列出旧术语所有出现位置，逐个判断是否豁免（原则 3）。
- **计数对等**：grep "N ADRs / N terms / N Job Types / N Skills / N FRs / N MCP"，交叉对比所有提及处。
- **引用完整性**：除 `check_adr_semantics.py` 覆盖的，查 narrative 引用（"见 §X.Y""如 ADR-ZZZZ 所述"）。
- **图表-正文同步**：读每个 `.mmd` 的标签，回正文核对。
- **占位/TBD 扫描**：grep `TODO|TBD|FIXME|占位|待定`。
- **规则**：每个 grep 必须记录命令 + 命中行号到工作笔记。"grep 过了没问题"无输出 = 未执行。**工作笔记是临时产物**（原则 8）：命中行号在步骤 6 进入对应 finding 的 `位置`+`证据` 字段（持久化），笔记草稿在步骤 7 删除。

### 步骤 3 · 按模块分批深读（B/C 类）

B/C 类（架构/可行性）主战场。**不能一次读 6410 行，必须切块**。

推荐切分（按文档自然结构）：

| 批次 | 读取内容 | 配套 ADR |
|------|---------|---------|
| 批 1 | `01-facts.md`（全）+ `02-requirement.md`（全）—— 建立需求基线 | 全 ADR 扫读摘要 |
| 批 2 | `03-architecture.md` §1-§6（哲学/全景/引擎/Compute Spec） | 0005, 0006, 0007, 0008, 0011, 0025 |
| 批 3 | `03-architecture.md` §7-§14（Sandbox/Log/Change Intel/KB/跨层/领域组件/选型） | 0013, 0014, 0015, 0023, 0024 |
| 批 4 | `03-architecture.md` §15-§25（C4/STRIDE/部署/ERD/SLO/CDC/时序/Agent/BRD-ADR/运维合规）+ `docs/security/`+`docs/operations/`+`docs/architecture/` | 0010, 0016-0022, 安全合规相关 |
| 批 5 | `04-timeline.md` + `05-cost.md` | 0009, 0020 |

- 每批读完，**立即记录**该批覆盖维度产生的 findings（趁热打铁，避免上下文丢失）。
- 读某章节引用 ADR 时，同时打开该 ADR 对照。

### 步骤 4 · 矩阵构造（D1/D4）

- **STRIDE × 组件矩阵**：从 `docs/diagrams/*.mmd`（C4 图）提取组件列表 → 构造 6 列（S/T/R/I/D/E）矩阵 → 逐格问"对策？对策在哪份文档:行号？" → 空格 = finding。
- **法规 × 控制点矩阵**：列 SOX(ITGC)/HIPAA/GDPR 关键条目 → 逐条问"设计文档映射了控制？" → 空格 = finding。
- **规则**：矩阵每格必须显式填（有对策 / 无对策-残余风险接受 / 未覆盖-finding），不得留空。
- **矩阵是临时草稿**（原则 8）：矩阵本身在步骤 7 清理，但其**每个空洞**必须先转为带 ID 的 finding，进入步骤 6 汇总 → 最终沉淀进 spec 的 `Evidence`。矩阵的"已覆盖"格若产生有价值的整体评价，记入步骤 6 的维度总结（进报告）。

### 步骤 5 · 交叉维度核对

- 抽样 N 条 FR，追"FR → ADR → 架构章节 → 成本/timeline 体现"全链，断链即 finding（A8）。
- 检查跨文档同一论断是否一致（如某 SLO 在架构、operations、timeline 三处是否同值）。
- 检查 ADR 间的依赖/冲突是否被显式记录（如 ADR-0025 重新定义了 0005/0006 的叙事但未取代决策内容 —— 这种关系是否清晰）。

### 步骤 6 · 汇总与分级

- 所有候选 findings 去重（不同维度可能发现同一问题，合并为一条，标注涉及的维度）。
- 按 C/I/M 分级（见下方"输出格式"）。
- 写 findings 报告（输出 B）。
- **本步骤结束时，每个 finding 有唯一稳定 ID**（C-NNN / I-NNN / M-NNN）。ID 一旦分配，后续步骤不得重排或丢弃。

### 步骤 7 · 为所有 findings 创建追踪 spec（Track Everything）

**本步骤是审核闭环的强制环节，不得跳过。** 原则 7 要求：每个 finding 都有 superpowers spec 追踪。

**输入**：步骤 6 产出的、已分级且已分配 ID 的全部 findings（C + I + M，无例外）。

**执行**：

1. **分组**：按"严重程度 + 根因 + 区域"对 findings 聚合（见核心原则 7 的分组规则）。同严重程度、同根因的可合并为一个 spec；**跨严重程度绝不合并**。
2. **创建 spec 文件**：为每个分组写一个 spec 到 `docs/superpowers/specs/`，命名 `audit-<run-date>-<severity>-<seq>-<short-slug>.md`（如 `audit-2026-08-02-I-003-glossary-term-migration.md`）。`<seq>` 取该 spec 覆盖的最小 finding ID 的数字部分。
3. **每个 spec 必含字段**：
   - `Source Finding(s)`：覆盖的 finding ID 列表（全部列出，无一遗漏）
   - `Severity`：C / I / M
   - `Evidence`：从 findings 报告复制对应原文证据（文件:行号 + 引用）
   - `Problem`：问题分析（为什么是缺陷，引用的判断标准/维度）
   - `Fix Plan`：修复方案（具体到改哪些文件、怎么改；机械类给批量替换策略，架构类给论证补充方向）
   - `Acceptance Criteria`：修复如何验证（如"grep 'Design Plane' 仅返回豁免处""SLO 在三处文档同值""矩阵空洞填满"）
   - `Audit Trail`：来源审核 run（日期 + HEAD SHA + spec 路径）
4. **构造追溯索引**：在 `docs/superpowers/specs/audit-<run-date>-index.md` 写一张映射表，保证 `finding ID → spec 文件` 双向可查。
5. **孤儿检查**：遍历全部 finding ID，确认每个都出现在某 spec 的 `Source Finding(s)` 中。**孤儿 finding = 审核未完成。**
6. **临时文件清理（强制 · 原则 8）**：删除本审核过程中产生的所有临时层文件（工作笔记草稿、矩阵草稿、文件清单/grep 列表草稿、任何散落中间文件）。删除前确认其关键信息已按"沉淀规则"进入持久层（spec / 报告）。清理后核验：`docs/superpowers/specs/` 下**只存在**持久层三类文件（report.md / index.md / 追踪 spec）。

**与原则 6 的关系**：本步骤创建的是**新文件**（追踪 spec），不修改任何被审文件。这是审核产物，不是修复动作 —— 修复动作（按 spec 的 Fix Plan 执行）是后续独立流程。

**与原则 8 的关系**：前 6 步用临时文件（笔记/矩阵）做脚手架，本步骤把脚手架的价值沉淀进 spec/报告后，删除脚手架本身。仓库不留审核过程的中间垃圾。

---

## 输出（三部分 · 缺一不可）

审核完成后，必须产出**三部分**输出。三者均为完成判据（见下方），缺任一 = 审核未完成。

| 部分 | 形式 | 交付位置 | 内容 |
|------|------|---------|------|
| **A. 直接消息** | 对话消息（非文件） | 调用方收到的最终回复 | 汇总信息：范围/计数/维度覆盖/最严重问题/已创建 spec 清单/下一步建议 |
| **B. Findings 报告** | Markdown 文件 | `docs/superpowers/specs/audit-<run-date>-report.md` | 完整 findings 详情（C/I/M 分级 + 证据） |
| **C. 追踪 spec 文件集** | 多个 Markdown 文件 + 1 个索引 | `docs/superpowers/specs/audit-<run-date>-<severity>-<seq>-*.md` + `audit-<run-date>-index.md` | 每个 finding 一个或一组 spec，全部可追溯 |

---

### 输出 A · 直接消息（对话汇总）

审核结束的**最终对话回复**。简洁，让调用方一眼掌握全局。结构：

```
## 设计审核完成 · llm-reporting

**范围**：<全量 / $AUDIT_SCOPE 摘要>
**仓库 HEAD**：<SHA>
**审核日期**：YYYY-MM-DD

### 计数
| 严重程度 | findings | 已建 spec |
|---------|---------|----------|
| 🔴 Critical | N | n |
| 🟡 Important | N | n |
| 🟢 Minor | N | n |
| **合计** | **N** | **n** |

### 维度覆盖
<一行总结：审了 X/20 维度，跳过 Y（原因）>

### 最值得关注（Top 3 Critical）
1. C-001 <标题> — <一句话>
2. C-002 <标题> — <一句话>
3. C-003 <标题> — <一句话>
（若无 Critical，写"无 Critical"；若 Top 不足 3，据实列）

### 产物
- Findings 报告：docs/superpowers/specs/audit-<date>-report.md
- 追踪 spec：<n> 个，见索引 docs/superpowers/specs/audit-<date>-index.md
- 孤儿 finding 检查：<0 / N（审核未完成）>
- 零遗留确认：docs/superpowers/specs/ 下仅持久层三类文件，临时草稿已清理 ✅

### 建议下一步
<如"优先处理 3 个 Critical spec""Minor 批量合并为 2 个 spec 可低优先排期">
```

---

### 输出 B · Findings 报告（完整详情文件）

写入 `docs/superpowers/specs/audit-<run-date>-report.md`。结构：

```markdown
# 设计审核报告 · llm-reporting

**审核范围**：<文件清单摘要 / 或 $AUDIT_SCOPE>
**审核日期**：YYYY-MM-DD
**仓库 HEAD**：<git SHA，标注审核时的代码状态>
**基线 ADR**：<最新重大 ADR，如 ADR-0025 统一工作流引擎>
**审核执行**：单 agent 逐维度自查（design-audit-prompt v3）

## 汇总统计

| 严重程度 | 数量 | 已分配 spec |
|---------|------|-----------|
| 🔴 Critical | N | n |
| 🟡 Important | N | n |
| 🟢 Minor | N | n |
| **合计** | **N** | **n** |

## 维度覆盖表

| 类别 | 维度 | 已审 | findings 数 |
|------|------|------|------------|
| A 机械 | A1 完整性 | ✅ | n |
| A 机械 | A2 术语一致性 | ✅ | n |
| ... | ... | ... | ... |
| D 安全 | D6 LLM 危害 | ✅ | n |

（未审维度标 ⏭ + 原因）

## Findings 详情

> 以下为**格式示例**（位置/行号/原文仅演示字段结构，非预填结论。实际审核时由 agent 按证据强制原则现场取证）。

### 🔴 C-001 · <简短标题>

- **维度**：A2 术语一致性（+ A5 图表同步）
- **位置**：`docs/<file>:<line>,<line>`、`docs/<file>:<line>`
- **证据**：
  > docs/<file>:<line> — "<引用原文片段>"
  > docs/<file>:<line> — "<引用原文片段>"
- **问题**：<具体描述为什么不合规，引用判断标准>
- **影响**：<如果不修复会导致什么后果>
- **建议**：<修复方向。仅建议，不在本审核中执行 —— 原则 6>
- **追踪 spec**：`docs/superpowers/specs/audit-<date>-C-001-<slug>.md`（步骤 7 创建）

### 🟡 I-003 · <简短标题>
（同结构，含追踪 spec 字段）

### 🟢 M-012 · <简短标题>
（同结构，含追踪 spec 字段）

## 维度总结

（每个审过的维度 1-2 句整体评价）

- **A2 术语一致性**：ADR-0025 迁移未完成，旧术语残留集中于 cost/timeline/图表。
- **B5 核心约束可执行性**：零 AI 副作用有三层防御（Engine/NetworkPolicy/Sandbox），
  论证充分；但生产环境 egress 阻断的具体 NetworkPolicy 规则未规格化。
- ...

## 追溯索引引用

完整 finding → spec 映射见 `docs/superpowers/specs/audit-<date>-index.md`。
```

> **关键**：每条 finding 的"追踪 spec"字段**必须**非空（原则 7）。若该字段为空，说明步骤 7 未对该 finding 创建 spec = 孤儿 = 审核未完成。

---

### 输出 C · 追踪 spec 文件集

#### C-1. 单个 spec 文件模板

文件：`docs/superpowers/specs/audit-<run-date>-<severity>-<seq>-<short-slug>.md`

```markdown
# Audit Fix Spec · <简短标题>

## 元数据
- **Source Finding(s)**：C-001, C-004（列出本 spec 覆盖的全部 finding ID，无一遗漏）
- **Severity**：Critical
- **Source Dimensions**：A2, A5
- **Created From Audit**：audit-<run-date>（HEAD <SHA>）
- **Status**：open

## 证据（从 findings 报告复制）

### C-001 · <标题>
- **位置**：`docs/<file>:<line>,<line>`
- **证据**：
  > "<原文片段>"
- **问题**：<描述>
- **影响**：<描述>

### C-004 · <标题>
（同结构）

## 问题分析（根因）
<为什么这些 findings 是缺陷：引用的判断标准 / 违反的原则 / 维度定义。合并多个 findings 时说明共同根因。>

## 修复方案（Fix Plan）
<具体修复步骤。机械类：批量替换策略（grep pattern → 替换）；架构类：需补充的论证/章节/图表；可行性类：需补的数据/推导。此为方案，不在审核阶段执行（原则 6）。>

## 验收标准（Acceptance Criteria）
<修复如何验证。每条可机械检查。例：>
- [ ] `grep -rn "Design Plane" docs/` 仅返回 ADR 正文内的豁免处
- [ ] glossary / 01-facts / component-exploration-env.mmd 的 Skill 计数一致（=18）
- [ ] SLO 数值在架构 / operations / timeline 三处同值

## Audit Trail
- 来源审核 run：audit-<run-date>（HEAD <SHA>）
- 来源报告：`docs/superpowers/specs/audit-<run-date>-report.md`
```

#### C-2. 追溯索引文件

文件：`docs/superpowers/specs/audit-<run-date>-index.md`

```markdown
# Audit Spec 追溯索引 · <run-date>

**审核 run**：audit-<run-date>（HEAD <SHA>）
**报告**：`audit-<run-date>-report.md`
**孤儿检查**：<0 孤儿 / N 孤儿（审核未完成）>

## Finding → Spec 映射

| Finding ID | Severity | 标题 | 追踪 spec |
|-----------|---------|------|----------|
| C-001 | 🔴 | <标题> | audit-<date>-C-001-<slug>.md |
| C-002 | 🔴 | <标题> | audit-<date>-C-002-<slug>.md |
| I-003 | 🟡 | <标题> | audit-<date>-I-003-<slug>.md |
| I-004 | 🟡 | <标题> | audit-<date>-I-003-<slug>.md（与 I-003 同根因合并） |
| M-012 | 🟢 | <标题> | audit-<date>-M-012-<slug>.md |
| ... | ... | ... | ... |

## Spec → Finding 映射（反向）

| 追踪 spec | 覆盖 findings | 状态 |
|----------|-------------|------|
| audit-<date>-C-001-<slug>.md | C-001 | open |
| audit-<date>-I-003-<slug>.md | I-003, I-004 | open |
| ... | ... | ... |

## 统计核验
- findings 总数：N
- spec 总数：n
- 孤儿 findings：<0 / N>
- 覆盖率：<100% / X%>
```

---

### 严重程度定义

| 级别 | 标准 | 示例 |
|------|------|------|
| 🔴 **Critical** | 破坏核心约束 / 架构自洽性 / 安全合规正确性；或会导致读者实质性误解设计 | "零 AI 副作用"无物理强制；核心数据流矛盾；STRIDE 关键威胁无对策；FR↔ADR 断链导致需求无设计支撑 |
| 🟡 **Important** | 影响完整性 / 可验证性 / 可追溯性；不修复会留隐患但不立即致命 | 大量术语迁移残留；FR 缺验收标准；计数跨文件不一致；矩阵局部空洞 |
| 🟢 **Minor** | 文档卫生 / 格式 / 可读性；不影响设计正确性 | 行数标注过时；个别表述模糊；图表标签风格不一；typo |

### Finding 必填字段

每条 finding 必须包含全部 7 字段，缺一不可：

1. **维度**：所属维度编号（可多维度，用 + 连接）
2. **位置**：`文件:行号`（多个用逗号分隔）
3. **证据**：引用原文片段（用 `>` 引用块）
4. **问题**：具体描述为什么不合规
5. **影响**：如果不修复会导致什么后果
6. **建议**：修复方向（仅建议，不执行 —— 原则 6）
7. **追踪 spec**：对应的 spec 文件路径（步骤 7 填写，非空 —— 原则 7）

---

## 审核完成判据

审核"完成"的充要条件（全部满足，缺一即未完成）：

1. **维度覆盖**：范围内所有维度标 ✅（或 ⏭ + 合理原因），每个 ✅ 维度在步骤 2-5 有执行痕迹（grep 命中已进入 finding 证据 / 矩阵空洞已转为 finding / 读过的文件已反映在 findings）。
2. **findings 完整**：所有 findings 满足 7 必填字段 + 证据强制（原则 1），无"待补充""后续再查"遗留。
3. **输出三部分齐全**：
   - A 直接消息已发送（含计数/覆盖/Top Critical/spec 清单/孤儿检查结果/零遗留确认）
   - B findings 报告文件已写入 `docs/superpowers/specs/audit-<run-date>-report.md`
   - C 追踪 spec 文件集已创建（含索引 `audit-<run-date>-index.md`）
4. **零孤儿**：遍历全部 finding ID，每个都出现在某 spec 的 `Source Finding(s)` 中。孤儿数 = 0。
5. **追踪 spec 字段非空**：findings 报告中每条 finding 的"追踪 spec"字段都已填入路径。
6. **零遗留（原则 8）**：`docs/superpowers/specs/` 下**只存在**持久层三类文件 —— `audit-<date>-report.md`、`audit-<date>-index.md`、`audit-<date>-<sev>-<seq>-*.md`。任何其他文件（工作笔记/矩阵草稿/中间 txt）= 违规 = 审核未完成。

不满足以上任一 = 审核未完成，不得声称"审核完成"。

---

## 与现有工具的分工

| 工具/流程 | 覆盖范围 | 与本 spec 的关系 |
|----------|---------|----------------|
| `scripts/check_adr_semantics.py` | ADR 编号/supersede/§N/计数/结构（机械） | 本 spec 的 A3/A4 部分依赖它；先跑它，再补它覆盖不到的（术语迁移/narrative 引用） |
| CI（markdownlint/lychee/Vale） | 格式/链接/prose（机械） | 本 spec 不重复；A1 的 TBD 扫描与之部分重叠 |
| `cross-reference-checklist.md` | 人工交叉引用清单 | 本 spec 的 A3 步骤参考它，但它若过时本身就是 finding |
| **本 spec** | **机械 + 架构 + 可行性 + 安全合规（全语义深度）** | 覆盖机器脚本无法判断的所有维度 |

**调用顺序建议**：先跑 `check_adr_semantics.py` + CI 确保机械基线绿，再用本 spec 做深度审核。

**为何不引入 superpowers skill（如 `requesting-code-review` / `systematic-debugging`）**：那些是**代码工作流** skill，前提假设与本文档审核场景错配 —— 前者依赖 git diff（审核既有文档无 diff 基线）、派 fresh-context 子 agent（本 prompt 明确选单 agent 自查）、调试运行时故障并修复（本 prompt 是文档审核且原则 6 不修复）。本 prompt 的纪律性由 8 条 Iron Laws + 反合理化守则 + 完成判据内化保证，无需外部 skill。"证据强制"与"声称完成前必须验证"的精神已分别内化进原则 1 与完成判据。

---

## 调用示例

```
$REPO_PATH = /Users/xiaotiac/Documents/GitHub/llm-reporting
$AUDIT_SCOPE = （空 = 全量）

[将本文件全文 + 上述变量喂给 AI agent]
→ agent 按执行流程 7 步运行
→ 产出三部分：A 直接消息 + B findings 报告文件 + C 追踪 spec 文件集（含索引）
→ 零孤儿方可声称完成
```

限定范围示例：

```
$AUDIT_SCOPE = "ADR-0025 迁移完整性"
→ agent 聚焦 A2/A3/A4/A5（术语/引用/计数/图表），跳过 B/C/D
```

```
$AUDIT_SCOPE = "安全合规"
→ agent 聚焦 D1-D6 + 相关的 B1/B5，构造 STRIDE/法规矩阵
```

---

*参考框架：AWS/Azure/Google Cloud Well-Architected Framework · SEI ATAM · IEEE Std 830 · ADR Review (ozimmer.ch) · Microsoft STRIDE · OWASP Threat Modeling · SOX/HIPAA/GDPR 合规控制点 · LLM/Agent 可靠性研究。*
