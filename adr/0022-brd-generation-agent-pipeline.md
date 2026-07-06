# ADR-0022: BRD Generation Agent Pipeline Redesign

- **Status**: Accepted
- **Date**: 2026-07-04
- **Deciders**: Project Sponsor

## Context

ADR-0010 established BRD as a system first-class citizen with the core direction — AI-assisted generation + 6-round LLM deep verification + human approval. However, in that ADR, S15 BRDGenerator was modeled as a monolithic Skill with a 6-step serial pipeline (Intent Parsing → KB Retrieval → Draft Generation → Impact Analysis → User Review → Publication).

After a deep-dive architecture grilling session focused on BRD generation, the following gaps were identified in the monolithic model:
1. **Insufficient vague requirement disambiguation**: S01 IntentParser only does intent classification, lacking structured requirement elicitation (Five Whys)
2. **LLM confident hallucinations undetectable**: fuzzy_nodes relies on LLM self-reporting uncertainty, but 2025 research (INS-S1, Moody's) shows LLM confidence and actual accuracy have weak correlation
3. **Hallucination Snowballing**: Post-hoc verification cannot prevent early errors from contaminating subsequent chapters (SHARS, ICLR 2025)
4. **Coarse context retrieval**: Missing historical Jira/Rally and GitHub code implementations as context sources
5. **Ambiguous external sync direction**: Jira/Rally bidirectional sync causes state conflicts

## Options Considered

### Option A: Keep Monolithic S15 with Minor Tweaks
- **Pro**: Lowest implementation cost, no changes to existing documentation structure
- **Con**: Cannot resolve the five structural gaps above

### Option B: Split into 6 Prefix-Named Agents, Serial Pipeline (Chosen)
- **Pro**: Each Agent has a single responsibility, independently renderable output, focused context (ReqInOne proves modular > monolithic by 20%+ accuracy improvement); serial execution avoids LLM Gateway concurrency bottleneck; prefix naming (BRD-xxx) clearly expresses ownership
- **Con**: Adds 5 Agent definitions; Web UI needs progressive rendering support

## Decision

Adopt **Option B**: S15 BRDGenerator refined into 6 prefix-named Agents in a serial pipeline.

### 1. Agent Naming and Responsibilities

| Agent | Role | Input | Output |
|-------|------|-------|--------|
| **BRD-IntentDeepener** | Five Whys requirement elicitation + business objective distillation | User natural language input | `intent_profile.json` (core objective, success criteria, scope, confidence) |
| **BRD-ContextGatherer** | Parallel RAG (KB + Jira/Rally + GitHub) + gap identification | intent_profile | `context_dossier.json` (KB entries, historical artifacts, existing code, gaps) |
| **BRD-VaguenessResolver** | Experience Typology Tree missing dimension detection + precise questioning | context_dossier + intent_profile | `resolved_dimensions.json` (auto-filled dimensions + targeted multiple-choice questions, ≤3) |
| **BRD-DraftWriter** | Chapter-by-chapter BRD YAML generation + Inline AssumptionCheck + soft lock / bounded backtracking | First three step outputs + user confirmations | Streaming incremental BRD YAML (per-Section rendering) |
| **BRD-Verifier** | 6-round deep verification (Structure/References/Impact/Gaps/Approval Chain/Testability) | Complete BRD Draft | `verification_report.json` (per-round scores + issues + recommended_actions) |
| **BRD-Assembler** | Three-format aggregation (YAML/Markdown/Jira Payload) + Pre-Sync Gate | BRD Draft + verification_report | `brd_package.json` (three output formats + confidence_summary + export_formats) |

### 2. Serial Pipeline (LLM Gateway Concurrency Constraint)

BRD-IntentDeepener → BRD-ContextGatherer → BRD-VaguenessResolver → [User Confirmation] → BRD-DraftWriter (with Inline AssumptionCheck) → BRD-Verifier → BRD-Assembler (with Pre-Sync Gate)

Only one Agent calls the LLM at any time. Each step outputs independent JSON; the Web UI progressively renders cards.

### 3. BRD-IntentDeepener: Five Whys Stopping Conditions

- **Semantic gating**: Answer is mappable to ≥1 Given/When/Then or success_criteria → stop
- **Diminishing returns**: Current answer contains no new information vs. previous → stop
- **Hard depth cap**: 3 layers (O'Hara 2025 data: 99% of actionable requirements appear within 3 layers)

### 4. BRD-ContextGatherer: Three-Source RAG + Cold-Start Fallback

- Primary path: KB (Business Glossary + Data Catalog + Mapping Registry) + Jira/Rally history + GitHub code implementations
- Fallback path (new tenant / new domain): Single-source KB, empty results → Schema-Driven Bootstrap (scan tenant Data Source Schema, infer business domain and requirement dimensions from table/column names)
- Basis: LLMs4OL 2025 proves domain ontology extraction from plain text is feasible, GPT-4 structured extraction accuracy 84.76%

### 5. BRD-VaguenessResolver: Experience Typology Tree

- Based on TypoAgent/OntoAgent (RE 2026) Gating/Pruning mechanism
- Typology Tree three-layer progressive construction (strict tenant isolation):
  - Layer 0: Schema-Driven Bootstrap (at tenant onboarding, inferred from Data Source Schema, covering 60-70% dimensions)
  - Layer 1: BRD-Driven Refinement (per completed BRD write-back, updating confidence and observation count)
  - Layer 2: Cross-BRD Pattern Mining (same type ≥3 BRDs, distill standard template)
- Tree stored in `agent_semantic_memory`, `tenant_id` isolated
- System built-in "bare skeleton" (type names + generic dimension names only) shareable across tenants, contains no tenant data
- Questioning strategy: Typology Tree covered dimensions auto-fill → remaining missing dimensions get precise questions (≤3) → irrelevant dimensions pruned/skipped

### 6. BRD-DraftWriter: Chapter-by-Chapter Generation + Inline AssumptionCheck

**Chapter order**: `business_context → requirements → data_flows → stakeholders → traceability`

**Soft Lock + Bounded Backtracking** (ReAgent, ACL 2025 / CARE, 2026):
- Each chapter soft-locked after generation (not immutable)
- Downstream discovery of upstream defects → localized rollback following dependency graph (max 2 times)
- Supplementary conflicts (e.g., new Stakeholder needed) → write `pending_revision` marker, no rollback
- Blocking conflicts (e.g., core data source missing) → trigger rollback
- Rollback infinite loop protection: same section max 2 times → escalate to P0 blocking issue for user

**Inline AssumptionCheck** (SHARS, ICLR 2025 / FGL, 2025):
- Execute immediately after each chapter generation (not Post-hoc), preventing Hallucination Snowballing
- Process: Atomic Claim Decomposition → NLI Verification (Natural Language Inference, checking whether KB source actually supports the claim, not just checking citation existence)
- Each claim tagged as `directly_supported` / `inferred_assumption` / `business_assumption`
- Unconfirmed assumption two-tier routing:
  - **Blocker**: impacts ≥2 Sections or ≥1 P0 Requirement → halt subsequent generation, present to user
  - **Non-blocker**: impacts only current Section minor fields → allow continuation, mark conditional

### 7. BRD-Verifier: 6-Round Verification + Conflict Detection

Retains ADR-0010's 6-Round verification pipeline (Structural Completeness / KB Cross-Reference / Impact Analysis / Gap Analysis / Approval Chain Validation / Testability).

**Conflict detection strategy**: Option C2 — Agent detects conflicts, marks `conflict`, does not adjudicate, returns to human resolution.

### 8. BRD-Assembler: Three-Format Output + Pre-Sync Gate

- YAML: System internal storage (Git versioned, Compute Spec subtype)
- Markdown: Text export
- Jira Payload: Epic + Stories (with Given/When/Then AC)

**Pre-Sync Gate**: Unresolved blockers present → block Jira/Rally creation. Markdown/PDF export unaffected — fuzzy content annotated with `[To Be Confirmed: ...]`.

### 9. Revision Mode: Incremental Patch + Cascade Refresh

- User revision feedback arrives → only modify the marked Section
- Post-modification auto cascade refresh: traverse dependency graph, refresh affected downstream Sections, leave unrelated sections untouched
- Revision conflict detection: Agent detects conflicts (e.g., two parties propose different values for same field) → mark `conflict` → return to human adjudication
- Slot-machine effect prevention: cascade refresh only affects dependency-related chapters

### 10. Jira/Rally: Unidirectional Sync

- Direction: BRD → Jira (BRD is single Source of Truth)
- Jira content does not write back to BRD
- MCP-17 via Jira Webhook **read-only pull** Story status → update BRD `implementation_progress` field (e.g., 3/5 Stories Done)
- BRD state transitions (`in_progress` → `implemented`) require manual human triggering

### 11. Compliance Mapping: Tenant Compliance Profile

- One-time Admin configuration at tenant onboarding: jurisdiction / industry / company type / data regions / data types
- System activates corresponding regulation library based on Profile (SOX / HIPAA / GDPR / Basel III / …)
- MCP-19 only performs RAG semantic matching within activated regulation libraries (referencing Drata 93% accuracy approach, Sprinto context-aware mapping)
- Each mapping requires human Accept/Reject

### 12. Multi-BRD Conflict Detection: Event-Driven Suspect Flag

- Entity change (BRD approved / KB entry modified / Data Source Schema change) → publish `entity.changed` event
- Consumer traverses Code Graph dependency graph to find all BRDs referencing the entity → mark as `needs_update` (Suspect Flag)
- Granularity: precise to Requirement level (referencing CRSensor Precision 0.95 / Recall 0.98)
- Adjudication: human confirms impact / confirms no impact / creates revision BRD
- Basis: AroTrace Suspect Link Management + ARTIAS 99% detection accuracy (but adjudication still Roadmap)

### 13. BRD Product Quality Assessment

Independent product quality dimension (distinct from ADR-0018's Agent trajectory scoring):
- Human reviewer four dimensions: Clarity / Completeness / Feasibility / Compliance
- Approver scores during BRD approval, serving as ground truth for BRD quality

### 14. Phase 2 Reservation

- BRD `approved` publishes `brd.approved` event
- Phase 2 mounts SDD Pipeline (Specify → Plan → Implement), referencing code_minions / GitHub Spec Kit / SYNTACT (EMNLP 2025)
- Phase 1 does not auto-generate code — BRD value boundary: generate document → approve → (optional) create Jira/Rally

## Rationale

1. **Modular > Monolithic**: ReqInOne (RE 2025) proves decomposing SRS generation into independent tasks improves accuracy by 20%+. Each Agent has focused context, precise prompts, lower hallucination.
2. **Inline > Post-hoc Verification**: SHARS (ICLR 2025) and HALC (2025) prove Post-hoc verification cannot prevent Hallucination Snowballing — early errors are "over-committed to" by subsequent chapters during generation. Inline AssumptionCheck executes immediately after each chapter, blocking the snowball effect.
3. **Claim-Level > Document-Level**: FGL (2025) proves Atomic Claim Decomposition + NLI verification (90-91.8% accuracy) is far more effective than fuzzy full-document verification. Distinguishing directly_supported / inferred_assumption / business_assumption solves LLM "correct citation, wrong inference" confident hallucinations.
4. **Typology Tree Solves Blank Canvas**: TypoAgent (RE 2026)'s core innovation — structured domain knowledge guides precise questioning. Three-layer progressive construction (Schema → BRD → Pattern Mining) ensures even new tenant cold start achieves 60-70% inferred coverage.
5. **Unidirectional Sync Eliminates Conflicts**: Bidirectional sync inevitably produces conflicts when BRD↔Jira state models are inconsistent. BRD as single Source of Truth eliminates all state conflict scenarios.

## Consequences

- **Positive**: 6-Agent pipeline produces higher quality BRDs; Inline AssumptionCheck blocks hallucination snowballing; Typology Tree reduces redundant questions; Suspect Flag proactively discovers multi-BRD conflicts.
- **Negative**: From 1 Skill to 6 Agents increases system complexity; serial pipeline adds end-to-end latency (but each step remains acceptable); Typology Tree cold-start effectiveness is limited.
- **Neutral**: BRD generation no longer includes automatic code/Workflow generation — deferred to Phase 2 (SDD Pipeline); Jira/Rally unidirectional sync simplifies integration but reduces automation.

## Industry References

| Reference | Year | Key Insight |
|-----------|------|-------------|
| TypoAgent / OntoAgent (RE 2026) | 2026 | Experience Typology Tree auto-construction + Gating/Pruning precise questioning |
| ReqInOne (RE 2025) | 2025 | Modular Agent decomposition (Summary→Extraction→Classification) > holistic by 20%+ |
| SHARS (ICLR 2025) | 2025 | Sentence-by-sentence generation + detection, blocking Hallucination Snowballing |
| HALC (2025) | 2025 | Closed-loop architecture: step-level semantic entropy detection + multi-source RAG verification, >85% unsafe acceptance risk reduction |
| FGL (2025) | 2025 | Atomic Claim Decomposition + NLI verification, 90-91.8% accuracy |
| O'Hara (IEEE DataPort 2025) | 2025 | Five Whys multi-agent workflow + deterministic evaluation engine, $0.01/session |
| ProReFiCIA (Oct 2025) | 2025 | LLM change impact analysis, 93.3% recall, human only needs to review 2.1-8.5% |
| AroTrace (2025) | 2025 | Suspect Link Management — auto-mark, human adjudicate |
| CRSensor (Oct 2025) | 2025 | Real-time auto Trace Link, Precision 0.95 / Recall 0.98 |
| Drata / Sprinto (2025) | 2025 | Tenant Compliance Profile + RAG compliance mapping, 93% accuracy |
| ClarifySTL (arXiv 2026) | 2026 | Vagueness→Clarification→Ambiguity→Disambiguation→Formalization staged pipeline |
| FSE Companion '25 (ACM) | 2025 | Coarse-to-Fine Skeletal Refinement preventing slot-machine effect |
| LLMs4OL (2025) | 2025 | Prompt-driven ontology construction, cold-start from plain text, GPT-4 84.76% accuracy |

## Linked Modules

- `adr/0010-brd-adr-first-class.md` → This ADR refines its AI-assisted generation component
- `adr/0018-agent-evaluation-framework.md` → BRD product quality assessment distinct from Agent trajectory scoring
- `adr/0019-agent-memory-architecture.md` → Typology Tree stored in agent_semantic_memory
- `docs/03-architecture.md` → §23.5-§23.12 (BRD Generation Pipeline + Typology Tree + Multi-BRD Conflict)
- `docs/01-facts.md` → Decision #21
- `docs/glossary.md` → Added 10 BRD generation-related terms
