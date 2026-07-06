# ADR-0016: Dual-Mode Agent Orchestration

- **Status**: Accepted
- **Date**: 2026-07-04
- **Deciders**: Project Sponsor

## Context

Agent Skill orchestration faces two conflicting requirements:

1. **Flexibility**: Exploration scenarios (ad-hoc Q&A, attribution analysis) require LLM dynamic Skill composition — user questions are unpredictable, fixed paths would constrain Agent reasoning capability
2. **Auditability**: Compliance scenarios (Adjustment, metric changes, Workflow modifications) require the system to prove to auditors that "critical steps were not skipped" — LLM free orchestration cannot provide deterministic guarantees

The current architecture (ADR-0005 Four-Layer Model) has established the separation of exploration and execution — "Explore with AI, Execute without AI Side Effects." But Agent orchestration itself has not yet reflected this separation.

The six major industry Agent frameworks (Claude SDK, LangGraph, OpenAI Agents SDK, etc.) are converging in 2025-2026 — all supporting tool-use dynamic orchestration + MCP + sub-agents. But no framework natively solves the problem of "how a single Agent system can simultaneously satisfy flexible exploration and compliance auditing."

## Options Considered

### Option A: Pure LLM-Driven (Rejected)
All scenarios use LLM dynamic Skill orchestration.
- **Pro**: Most flexible, can discover novel solution paths
- **Con**: Same question may take different paths on different runs; cannot prove to auditors that "critical steps were not skipped"; SOX compliance risk

### Option B: Pure State Graph (Rejected)
All scenarios use explicit state graphs (LangGraph pattern).
- **Pro**: Auditable, reproducible, deterministic paths
- **Con**: New Skills require graph topology updates (high maintenance cost); cannot handle novel user requests; exploration scenarios constrained

### Option C: Dual-Mode — Exploration + Verified Path (Chosen)
Split by operational risk: exploration/read-only → LLM dynamic orchestration; data/configuration mutation → Verified Path fixed steps.

## Decision

Adopt **Option C** (Dual-Mode Orchestration):

### Exploration Mode

Applicable scenarios: ad-hoc Q&A, attribution analysis, data exploration, KB queries. **All operations are read-only, modifying no system state.**

| Attribute | Value |
|---|---|
| Orchestration | LLM dynamically selects Skills and order |
| Guardrails | tool_budget=20, max_rounds=5, Permission Gate |
| Auditability | Complete tool-call trace recorded per execution (reproducible but not guaranteed consistent) |
| Failure Handling | Worst case gives an imperfect answer — does not pollute data |

### Verified Path Mode

Applicable scenarios: Adjustment creation/approval, Workflow changes, DQ Rule modifications, KB definition changes. **Involves modifying data or configuration.**

| Attribute | Value |
|---|---|
| Orchestration | Predefined fixed step sequence — LLM reasons within each step but cannot skip/reorder steps |
| Guardrails | The path itself is the guardrail — architecture guarantees each step executes |
| Auditability | Can prove "Steps A→B→C executed in order, none skipped" |
| Failure Handling | Any step failure → entire Path halts + Incident |

### Verified Path Definition Format

```yaml
verified_paths:
  create_adjustment_from_recon:
    risk_level: L3
    description: "Create Adjustment from Recon break"
    steps:
      - skill: S09   # ReconBreakAnalyzer — classify break
        required: true
        llm_decision: "TIMING/MISSING/ROUNDING/MAPPING/UNKNOWN?"
      - skill: S02   # KBRetriever — retrieve historical adjustment patterns
        required: true
      - skill: S04   # ImpactAnalyzer — affected Reports/Workflows
        required: true
      - skill: S05   # SpecGenerator — generate Adjustment Spec YAML
        required: true
        output: adjustment_spec_draft
      - gate: L3_REMEDIATION  # dual approval
        required: true
    # LLM cannot skip, reorder, or replace these 5 steps

  modify_dq_rule_threshold:
    risk_level: L2
    description: "Modify DQ Rule threshold"
    steps:
      - skill: S08   # DataQualityAdvisor — analyze modification reason
        required: true
      - skill: S04   # ImpactAnalyzer — impact scope
        required: true
      - skill: S05   # SpecGenerator — generate updated Rule YAML
        required: true
      - gate: L2_REMEDIATION  # single approval + DQ Gate
        required: true

  diagnose_anomaly:
    risk_level: L0
    mode: exploration  # ← fall back to LLM free orchestration
    constraints:
      must_include: [S03]   # at minimum query lineage
      max_skills: 6
```

### Skill Metadata Enhancement

To enable correct LLM orchestration in Exploration Mode and provide a basis for Verified Path definitions, each Skill carries orchestration metadata:

```yaml
skill_metadata:
  S08_DataQualityAdvisor:
    prerequisites: [S02]       # Must retrieve from Data Catalog first
    incompatible_with: [S09]   # Cannot run parallel with ReconBreakAnalyzer
    compatible_with: [S03, S04]
    side_effects: [kb_draft_write]
    produces: [dq_rule_draft, anomaly_finding]
    fallback: "schema_only_rules"
    verified_paths: [modify_dq_rule_threshold]

  S09_ReconBreakAnalyzer:
    prerequisites: []
    incompatible_with: [S08]
    compatible_with: [S02, S04]
    side_effects: []           # Read-only analysis
    produces: [break_classification, resolution_suggestion]
    fallback: "manual_review"
    verified_paths: [create_adjustment_from_recon]
```

### Mode Switching Rules

User Request → S01 IntentParser Classification → intent matches Verified Path → force Verified Path Mode → intent involves mutation but no matching Path → reject execution → other → Exploration Mode.

## Rationale

1. **Aligns with core philosophy**: Explore with AI (Exploration Mode), Execute without AI Side Effects (Verified Path Mode + Remediation Gateway)
2. **Auditability is a hard requirement for financial BI**: SOX requires provable change approval paths
3. **No industry standard answer exists**: Six major frameworks don't natively support dual-mode — architectural differentiator
4. **Maintenance cost is controllable**: ~8-12 Verified Paths (critical compliance paths only)
5. **Reject unsafe paths**: Mutation without Verified Path → reject execution — safe default

## Consequences

- **Positive**: Exploration maintains flexibility; compliance paths are auditable and provable; mode switching rules prevent LLM from bypassing compliance steps
- **Negative**: Verified Path definitions require additional maintenance; new compliance operations need Path definitions before Agent can assist
- **Neutral**: Exploration Mode tool-call traces are not deterministic — two identical questions may take different paths. This is a design trade-off, not a bug.

## Linked Modules

- `docs/03-architecture.md` → §22A (Agent SDK — Dual-Mode Orchestration Architecture)
- `docs/03-architecture.md` → §22B (Skill Catalog — Metadata Enhancement)
- `docs/03-architecture.md` → §22G (Verified Path Catalog)
- `adr/0005-four-layer-architecture.md` → Four-Layer Architecture (this ADR refines it at the Agent orchestration level)
- `adr/0015-agent-triage-remediation-gateway.md` → L0-L3 Remediation Gateway (Verified Path Gate step integration)
