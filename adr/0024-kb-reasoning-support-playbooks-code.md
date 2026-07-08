# ADR-0024: KB Reasoning Support — Diagnostic Playbooks & Code Knowledge Domains

- **Status**: Accepted
- **Date**: 2026-07-08
- **Deciders**: Architecture Team
- **Domain**: Architecture

## Context

Two gaps in the current KB design directly undermine the AI Knowledge Agent's ability to answer the highest-value, most complex user questions: cross-content diagnostic queries such as *"Why did this report generate this value instead of that one?"*

### Gap 1: No explicit diagnostic knowledge — the Agent improvises

Scenario 6 (`docs/03-architecture.md` §22E — *"Why did Line 3 jump 30%?"*) demonstrates that the architecture *can* execute a complex multi-source diagnostic: parallel calls to S03 (lineage), S02 (business definition), MCP-05 (logs), MCP-13 (data profile), fused into an attribution analysis. But how the Agent *knows* to compose that particular sequence rests on three implicit mechanisms, each insufficient on its own:

1. **S01 IntentParser** classifies intent (`explain_anomaly`) and routes to one Skill — but only the *first* hop. It does not encode the full investigation path.
2. **Skill Orchestration Metadata** (`prerequisites`, `compatible_with`, `incompatible_with` — §22B) constrains which Skills may combine — but this *prevents* bad combinations; it does not *prescribe* good ones.
3. **The ReAct loop** (§22A.3) lets the LLM reason act-by-act — but for high-stakes financial diagnostics, free-form ReAct produces unstable quality: the same question may follow an expert-grade path on one run and a shallow path (e.g., "only checked lineage, forgot to diff the data snapshot") on another.

The 2025-2026 industry consensus (Devin, Monte Carlo's RCA Agent, Cursor's agent, Google's diagnostic agents) converges on the same answer: **pure LLM ReAct is too unstable for complex diagnostics; encode expert investigation paths as explicit "playbooks" that act as a soft skeleton the LLM reasons within.** The project has no such knowledge type — the seven KB domains contain *what* and *how the system is built*, but not *how to investigate*.

### Gap 2: No code-knowledge ingestion path — the Agent cannot reason about code logic

When a user asks *"Is there a bug in the `revenue_transform` logic?"*, the Agent currently has no tool to retrieve and reason about code *content*:

- **Code Graph** (§2.1) models structural relationships (Workflow → Job → DataSource) but its nodes are *system artifacts*, not the source code itself.
- **MCP-06 git-diff** does diff/blame/log — it answers *what changed and when*, not *what the code does*.
- **MCP-13 static-analysis** does security/anti-pattern analysis on Compute Specs and Python — it does not support semantic code search ("find all functions that compute gross margin").
- **ADR-0022** BRD-ContextGatherer references "GitHub code implementations" as a context source, but *how code is ingested, indexed, and correlated is undefined*.

Consequently the Agent cannot fulfill a core diagnostic step — *"check the code logic for bugs"* — because it has no indexed, searchable representation of the code's semantics. This is the weakest link in the end-to-end diagnostic loop.

## Options Considered

### Option A: Pure LLM ReAct for Diagnostics (Rejected)

Rely entirely on S01 routing + Skill metadata + ReAct improvisation for all diagnostic queries.

- **Pro**: Zero new KB machinery; maximum flexibility.
- **Con**: Quality variance is unacceptable for financial diagnostics. Expert investigation paths (check lineage → check job status → diff data snapshot → check upstream commits → check related reports) are domain knowledge that the LLM may or may not reproduce on any given run. This is precisely the instability Monte Carlo and Devin's 2025 post-mortems identify as the top failure mode of diagnostic agents.

### Option B: Verified-Path-ify All Diagnostics (Rejected)

Encode every diagnostic as a fixed-step Verified Path (ADR-0016 / ADR-0017).

- **Pro**: Fully auditable, deterministic, reproducible.
- **Con**: Diagnostics are inherently exploratory — the right next step depends on what the previous step found (data volume anomalous? → check upstream; spec changed? → diff code). Forcing every diagnostic into a fixed graph either over-constrains exploration or requires a combinatorial explosion of paths to cover every branch. This misuses the Verified Path mechanism, which ADR-0016 explicitly reserves for *mutation* scenarios (data/config changes requiring compliance audit), not for read-only investigation.

### Option C: Diagnostic Playbooks + Code Knowledge Domain (Chosen)

Introduce two new KB domains: **Diagnostic Playbooks** (8th domain — expert-encoded investigation trees acting as a *soft skeleton* for Exploration Mode) and **Code Knowledge** (9th domain — a three-layer code index enabling semantic code search and logic reasoning). Together they close both gaps while respecting the existing Dual-Mode Orchestration (ADR-0016): Playbooks are the Exploration-Mode counterpart to Verified Paths, and Code Knowledge extends the existing Code Graph + PG-First storage.

## Decision

Adopt **Option C**. Add two KB domains (bringing the total from seven to nine) and one new Skill and one new MCP to support them.

### 1. KB Domain 8 — Diagnostic Playbooks

**Definition.** A Playbook is an IF/THEN diagnostic decision tree that encodes *expert investigation methodology* — the sequence and branching of tool calls a senior analyst would follow for a given diagnostic intent. It is metadata that *guides* the Agent, not code that *controls* it: the LLM reasons within the playbook's skeleton and may adapt based on observations.

**Example Playbook** (`explain_unexpected_metric_value`):

```yaml
playbook: explain_unexpected_metric_value
  trigger:
    intent: [explain_anomaly, explain_lineage, audit_query]
    entities: {metric, report, time_range}
  steps:
    - step: 1
      skill: S03                          # CodeGraphQuery
      action: "Full lineage of the metric (upstream + downstream)"
      goal: "Locate which Jobs and DataSources produce this value"
    - step: 2
      parallel:
        - skill: MCP-05                   # log-search
          action: "Execution history of related Jobs (last 7 days)"
        - skill: MCP-04                   # pg-query
          action: "Actual persisted value for the metric in the time window"
        - skill: S02                      # KBRetriever
          action: "Business definition of the metric (rule out definition drift)"
    - step: 3
      condition: "Job failed OR data volume anomalous"
      then:
        - skill: MCP-06                   # git-diff
          action: "Recent Spec changes affecting the Job"
        - skill: MCP-08                   # data-profile
          action: "Compare anomaly-period vs baseline-period data distribution"
    - step: 4
      skill: S02
      action: "Query related reports via SIMILAR_TO / DERIVED_FROM edges"
      goal: "Confirm whether this is a single-point issue or a cascade"
    - step: 5
      condition: "root cause not yet located"
      then:
        - skill: MCP-09                   # incident-query
          action: "Search historical similar incidents"
        - skill: S07                      # IncidentDiagnostician
          action: "Parallel sub-agents (Pipeline / Data / Infra / Historical)"
  confidence_thresholds:
    job_failed: 0.95              # Job failure = high-confidence root cause
    data_volume_anomaly: 0.85     # Data-volume anomaly = medium-high
    spec_changed_recently: 0.70   # Recent Spec change = medium
```

**Three Playbook sources** (confidence-tagged, aligning with ADR-0019 provenance):

| Source | Provenance | Confidence | Example |
|---|---|---|---|
| System-builtin | `system_builtin` | 1.0 | Industry-standard diagnostic patterns (e.g., "for unexpected metric values, always check lineage + job status first") shipped with the platform |
| Incident-distilled | `model_inferred` | 0.7–0.9 | After S07 successfully diagnoses an incident, the LLM distills the successful trajectory into a Playbook candidate; human confirms before promotion (mirrors ADR-0019 promotion rules) |
| User-defined | `user_stated` | 1.0 | A team codifies its own investigation SOP into a Playbook via the Workbench |

**Two routing paths** — how the Agent "knows" to use a Playbook:

| Path | Mechanism | When |
|---|---|---|
| **Explicit routing** | S01 IntentParser matches a Playbook `trigger`; the matched Playbook is injected into the Skill Planner as a guided plan | High-frequency known scenarios (explain metric, diagnose anomaly) |
| **Implicit retrieval** | S01 does not match a Playbook; mid-ReAct, the LLM retrieves a relevant Playbook via S02 as reference | Novel questions that resemble a known pattern |

**Closed-loop learning.** Successful diagnostic trajectories are stored in L2 Episodic Memory (ADR-0019). When the same diagnostic pattern recurs ≥3 times (ADR-0019 promotion threshold), the LLM proposes distilling it into a new Playbook; user confirms; the Playbook is promoted to the domain. This reuses the S08 closed-loop learning pattern (ADR-0015) and ADR-0019's promotion rules — no new mechanism invented.

**Relationship to Verified Paths (ADR-0016).** Playbooks are the Exploration-Mode counterpart to Verified Paths: Verified Paths are *hard skeletons* (fixed steps, non-skippable, for mutation scenarios requiring compliance audit); Playbooks are *soft skeletons* (suggested steps, LLM-adaptable, for read-only investigation). A diagnostic that concludes with a recommended mutation hands off to the appropriate Verified Path (e.g., `create_adjustment_from_recon`).

### 2. KB Domain 9 — Code Knowledge

**Definition.** A three-layer index over code artifacts (Compute Spec YAML, Python transforms executed in the Sandbox per §7, Git history, external repos via GitHub/GitLab sync) that enables the Agent to retrieve and reason about code *semantics*, not just structure or diffs.

**Three-layer index**:

| Layer | Store | Content | Query it answers |
|---|---|---|---|
| **Structure** | Code Graph (existing, §2.1) | Functions/classes → nodes; call relationships → edges (`CALLS`, `READS`) | "What does `revenue_transform` call? What reads `erp_gl`?" |
| **Semantic** | pgvector (new, via ADR-0023 Stage 4) | Each function/Spec chunked + Contextual Retrieval + embedding | "Find all functions that compute gross margin" (semantic, not keyword) |
| **Change** | Git (existing, MCP-06) | Commit messages, PR descriptions, blame, diff | "When and why was this logic last changed?" |

**Why three layers (industry basis).** 2025-2026 production code-RAG systems (Cursor, Sourcegraph Cody, GitHub Copilot Workspace, Google Code Search) converge on the finding that *pure vector retrieval over code underperforms* — code semantics and natural-language semantics misalign. The consensus is a dual index: structural (AST / call graph) + semantic (embedding). This ADR adds the semantic layer over the existing structural Code Graph and the existing Git change layer, completing the trio.

**Event-driven ingestion** (keeps the index correlated, not batch-rebuilt):

| Event | Triggered Index Update | Correlation Maintained |
|---|---|---|
| Freeze Bridge `merge` (Spec frozen) | Re-parse Spec YAML → update Code Graph nodes + semantic embedding | Automatic (ACID, via ADR-0023 Stage 4 single-transaction write) |
| Sandbox Python execution | Static analysis of the code → function-level nodes + `CALLS` edges | Automatic |
| Git push (repo webhook) | Diff → update changed function nodes + embeddings; commit → blame edges | Automatic |
| PR merge | PR description → LLM extracts "what changed and why" → linked to Spec change | Semi-automatic (LLM proposes; enters version chain) |

**Bridge edges to existing graphs** (extends §2.1 and ADR-0023 §10.3):

```
CodeKnowledge.Function  —IMPLEMENTS→   CodeGraph.Job
CodeKnowledge.Function  —REFERENCES→   KB.GlossaryEntry   (via comments / naming)
CodeKnowledge.Commit    —MODIFIES→     CodeGraph.Spec
```

These edges are what let the Agent, in a single diagnostic, join *"the function that computes revenue"* + *"the Job it implements"* + *"the business definition of revenue"* + *"the last commit that changed it"* into one causal chain.

**New Skill S18 — PlaybookRouter** and **new MCP-23 — code-knowledge-search** (defined in `docs/03-architecture.md` §22B and §22C respectively) provide the Agent's interface to these two domains.

### 3. End-to-end diagnostic loop (how Q1+Q2+Q3 compose)

With both domains in place, the *"why is this report value X not Y"* scenario runs as:

```
User: "Why did report_R show revenue = 1.2M instead of 1.5M?"
  │
  ▼
S01 → intent: explain_metric_discrepancy
  → PlaybookRouter (S18) → matches playbook explain_unexpected_metric_value
  │
  ▼ Playbook guides the Agent (soft skeleton):
  │
  ├─ Step 1: S03 lineage (Code Graph structural layer)
  ├─ Step 2: parallel — MCP-05 logs + MCP-04 data + S02 definition (KB)
  ├─ Step 3: MCP-06 git-diff + MCP-08 data-profile (if anomaly detected)
  ├─ Step 4: S02 related reports (via ADR-0023 SIMILAR_TO / DERIVED_FROM edges)
  ├─ Step 5 (if unresolved): MCP-09 incidents + S07 sub-agents
  │   └─ Code-logic check: MCP-23 semantic code search (Code Knowledge semantic layer)
  │       → retrieves revenue_transform source → LLM verifies logic vs definition
  │
  ▼
Response Synthesizer → root cause + confidence + citations + suggested actions
  │
  ▼ (optional)
Successful trajectory → L2 Episodic Memory → ≥3 recurrences → Playbook candidate (closed loop)
```

## Rationale

1. **Playbooks are the Exploration-Mode counterpart to Verified Paths.** ADR-0016 established that mutation scenarios need *hard* skeletons (Verified Paths) for compliance; this ADR establishes that complex read-only diagnostics need *soft* skeletons (Playbooks) for quality stability. Both exist because both modes exist — symmetry with the Dual-Mode architecture.
2. **Soft skeleton beats both extremes.** Pure ReAct (Option A) is unstable; full Verified-Path-ification (Option B) over-constrains exploration. A soft skeleton — suggested steps the LLM adapts within — is the Goldilocks solution, matching what Devin and Monte Carlo independently converged on in 2025.
3. **Code Knowledge closes the weakest diagnostic link.** Without semantic code search, *"check the code logic for bugs"* is impossible — the Agent can diff code but not read it. The three-layer index (structure + semantic + change) is the 2025 industry consensus for production code-RAG.
4. **Reuses existing mechanisms, invents nothing new for governance.** Playbook promotion reuses ADR-0019's promotion rules; playbook confidence tagging reuses ADR-0019 provenance; closed-loop learning reuses the S08 pattern (ADR-0015); linkage weaving reuses ADR-0023's edge-generation strategies; storage reuses ADR-0013's PG-First stack. The decision is *compositional*, not *inventive* — consistent with the project's Boring-Technology discipline.
5. **Extends, does not replace.** Code Knowledge's structural layer *is* the existing Code Graph; its change layer *is* the existing Git/MCP-06; only the semantic layer is new, and it rides on ADR-0023's Stage 4 write pipeline. No existing component is displaced.

## Consequences

- **Positive**: Complex cross-content diagnostics gain quality stability (Playbooks) and completeness (Code Knowledge). The Agent can now fulfill the full diagnostic loop — including the code-logic check that was previously impossible. KB grows from seven to nine domains, all on the existing PG-First stack. Closed-loop learning means the Playbook library improves with use.
- **Negative**: Two new KB domains increase conceptual surface area; Playbook authoring (system-builtin aside) requires human effort; the Code Knowledge semantic index adds embedding storage proportional to the codebase size (estimated ~50K functions over 5 years — well within pgvector's 1M threshold). MCP-23 adds one MCP server to operate.
- **Neutral**: Playbook routing introduces a new decision point in S01 (explicit-match vs implicit-retrieval); the fallback (no Playbook matched → pure ReAct) preserves backward compatibility, so existing behavior is a strict subset of the new behavior. The Playbook library starts small (system-builtin set) and grows organically — cold-start effectiveness depends on how many system-builtin playbooks ship at launch.

## Industry References

| Reference | Year | Key Insight |
|-----------|------|-------------|
| Devin (Cognition) — Diagnostic Agents | 2025 | Production autonomous-coding agents converge on playbook/skeleton-guided reasoning over pure ReAct for complex multi-step investigation; quality stability is the primary driver |
| Monte Carlo — RCA Agent | 2025-2026 | Data-incident root-cause-analysis agents encode expert investigation paths as explicit runbooks; reported 50-70% MTTR reduction, mirroring ADR-0015's Triage Layer results |
| Cursor / Sourcegraph Cody — Code RAG | 2025 | Production code search/retrieval uses dual indexing (structural AST/call-graph + semantic embedding); pure vector retrieval over code underperforms due to code/natural-language semantic mismatch |
| GitHub Copilot Workspace / Spec Kit / SYNTACT (EMNLP 2025) | 2025 | Spec-driven development pipelines treat code, specs, and change history as one correlated knowledge graph; bridge edges between specs and code are foundational |
| ADR-0016 (this project) | 2026 | Established Dual-Mode Orchestration — Verified Paths for mutation, Exploration for read-only. This ADR adds the Exploration-Mode counterpart (Playbooks as soft skeletons) |
| ADR-0019 (this project) | 2026 | Four-layer memory + provenance + promotion rules — directly reused for Playbook confidence tagging and closed-loop learning |

## Linked Modules

- `docs/03-architecture.md` → §10 (Knowledge Base — adds domains 8 & 9 to the domain table)
- `docs/03-architecture.md` → §22B (Skill Catalog — new S18 PlaybookRouter)
- `docs/03-architecture.md` → §22C (MCP Catalog — new MCP-23 code-knowledge-search)
- `docs/03-architecture.md` → §22E Scenario 6 (diagnostic flow now guided by `explain_unexpected_metric_value` playbook)
- `adr/0016-dual-mode-agent-orchestration.md` → Playbooks are the Exploration-Mode counterpart to Verified Paths
- `adr/0019-agent-memory-architecture.md` → Playbook confidence tagging (provenance) + closed-loop promotion rules reused
- `adr/0015-agent-triage-remediation-gateway.md` → S08 closed-loop learning pattern reused for Playbook distillation
- `adr/0013-kb-storage-strategy.md` → Code Knowledge semantic layer rides on pgvector (within the 1M threshold)
- `adr/0023-kb-content-lifecycle-pipeline.md` → Code Knowledge ingestion reuses the Stage 1–5 funnel; linkage weaving reuses §10.3 edge strategies
- `docs/01-facts.md` → Decision #23
- `docs/glossary.md` → Diagnostic Playbooks, Code Knowledge, Playbook Router
- `docs/02-requirement.md` → FR45 (Diagnostic Playbooks), FR46 (Code Knowledge Index)
