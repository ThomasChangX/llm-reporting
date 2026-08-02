# Audit Fix Spec · ADR-0025 术语迁移残留（旧 plane 名）

## 元数据
- **Source Finding(s)**：I-008
- **Severity**：Important
- **Source Dimensions**：A2, A5
- **Created From Audit**：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- **Status**：open

## 证据

### I-008 · ADR-0025 术语迁移残留（当前状态文档）
- **位置**（代表性，详见报告）：
  - `docs/glossary.md:16,17,86,90,123,135,152`（7 词条用旧名作当前定义，无 legacy 标注）
  - `docs/03-architecture.md`（22 处：L14,159,551,650,884,1034,1069,1102,1800,1866,2066,2479,2617,2777,4788,4936,6324,6336 等）
  - `docs/02-requirement.md:313,374,431,547`（FR15c.6/FR20.5/FR26.5/FR38.3）
  - `docs/04-timeline.md`（12 处，含 L176 Phase 3 标题"Design Plane"、L216 Phase 4"Freeze Bridge"、L256 Phase 5"Runtime Plane"）
  - `docs/05-cost.md`（多处，含 L63 成本表行"3: Design Plane"、L261,265,280,305-308,345）
  - `docs/architecture/c4-model.md:97,157,158`
  - `docs/security/threat-model.md:20,25`
  - `docs/diagrams/system-context.mmd:10-13`（四个 box 全旧名）
  - `CONTRIBUTING.md:69`
  - `docs/operations/slo-sli.md`
- **证据**（代表性）：
  > docs/glossary.md:16 — "Light Engine | Lightweight compute engine for the **Design Plane**"（无 legacy 标注）
  > docs/diagrams/system-context.mmd:10-13 — DP["Design Plane"], FB["Freeze Bridge"], RP["Runtime Plane"], IP["Intelligence Plane"]
  > docs/04-timeline.md:176 — "### Phase 3: **Design Plane** (Weeks 13–18)"
  > docs/05-cost.md:63 — "| 3: **Design Plane** | 7.9M ..."
- **问题**：ADR-0025（2026-07-30）将四 plane 重命名为 Exploration/Production/Cross-Env Read-Only Mode + Freeze Pipeline。但大量当前状态文档仍用旧名作当前定义。豁免：ADR 正文（E1）、glossary "Formerly called"（E3）、superseded ADR 列表（E3）。
- **影响**：读者无法确定当前术语。迁移未完成削弱 ADR-0025 权威性。system-context.mmd 是入门图，全旧名造成第一印象错误。

## 问题分析（根因）

ADR-0025 完成了术语**定义**迁移（glossary 4 个新词条带"Formerly called"），但未完成术语**使用**迁移（全文替换）。旧名作为当前定义散落在 glossary 7 词条、03-arch 22 处、04-timeline Phase 标题、05-cost 成本行、system-context.mmd。原则 3（历史快照豁免）只保护 ADR 正文与标注 legacy 的词条，不保护当前状态文档。这是 A2（术语一致性）的批量机械缺陷。

## 修复方案（Fix Plan）

机械类批量替换（按文件分批）：

1. **glossary.md**（7 词条）：对 L16/L17/L86/L90/L123/L135/L152，要么将旧名替换为新名，要么补 legacy 标注（如 "Light Engine ... for the Exploration Environment (formerly Design Plane)"）。
2. **system-context.mmd**（4 box）：参考已迁移的 component-exploration-env.mmd/unified-engine-arch.mmd/freeze-pipeline-flow.mmd，将 DP/FB/RP/IP 改为 EXPLORATION ENVIRONMENT/FREEZE PIPELINE/PRODUCTION ENVIRONMENT/CROSS-ENV READ-ONLY MODE。
3. **03-architecture.md**（22 处）：逐处替换，注意 §3 章节标题（如"§3 Design Plane"→"§3 Exploration Environment"）需同步 §N 引用。
4. **04-timeline.md**（12 处）：Phase 3/4/5 标题 + 正文 + 里程碑引用。
5. **05-cost.md**（多处）：成本表行标签 + §4/§5 正文。
6. **02-requirement.md**（4 FR）：FR15c.6/FR20.5/FR26.5/FR38.3。
7. **c4-model.md / threat-model.md / CONTRIBUTING.md / slo-sli.md**：逐处替换。
8. **不替换**：ADR 正文（0002-0008, 0011, 0015 等）、glossary "Formerly called" 注明、superseded ADR 列表（E1/E3 豁免）。
9. 替换后跑 `python3 scripts/check_adr_semantics.py` 确保无破坏。

## 验收标准（Acceptance Criteria）

- [ ] `grep -rn 'Design Plane' docs/ adr/ --include='*.md' --include='*.mmd'` 仅返回 ADR 正文豁免处（adr/0002-0008,0011,0015 等）+ glossary "Formerly called" 标注处
- [ ] `grep -rn 'Runtime Plane\|Intelligence Plane\|Freeze Bridge' docs/ adr/` 同上（豁免处除外）
- [ ] `docs/diagrams/system-context.mmd` 四个 box 全用新名
- [ ] `docs/04-timeline.md` Phase 3/4/5 标题用新名
- [ ] `docs/05-cost.md` 成本表行标签用新名
- [ ] `python3 scripts/check_adr_semantics.py` PASS

## Audit Trail
- 来源审核 run：20260803-bfac3ef（HEAD bfac3efd8515f983338a9f39d658e26f792e936e）
- 来源报告：`docs/superpowers/specs/audit-20260803-bfac3ef-report.md`
