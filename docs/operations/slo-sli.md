# SLO / SLI Definitions with Error Budgets

> Extracted from [docs/03-architecture.md §19](../03-architecture.md) | Sync Date: 2026-07-04
>
> SLO/SLI definitions and error budget strategies for 5 critical user journeys.

## 19. SLO / SLI Definitions with Error Budgets

### 19.1 Critical User Journey SLOs

#### Journey 1: "User Creates a Report via Natural Language" (NL → Spec → Preview)

| Attribute | Definition |
|-----------|------------|
| **User Journey** | Analyst types a natural-language request → AI interprets intent → Plan generated → Artifact built → Light Engine preview renders within Workbench |
| **SLI (Indicator)** | **p95 End-to-End Latency**: Time from user message submission to rendered preview in Workbench, measured at API Gateway. Includes: Intent Parsing (~200ms), KB Retrieval (~300ms), LLM Inference (~2-8s), Artifact Build (~500ms), Light Engine Preview (~1-5s). |
| **SLI Measurement** | Prometheus histogram metric `report_nl_to_preview_duration_seconds` with buckets [0.5, 1, 2, 5, 10, 15, 30, 60]. 5-minute rolling windows. |
| **SLO Target** | **p95 ≤ 15 seconds** over a 28-day rolling window |
| **Error Budget** | **5% failure allowance** = ~33.6 hours/month of violations allowed (based on 28d×24h×5%). Tracked as `(violations / total_valid_requests)` over the window. |
| **Budget Exhaustion Action** | (1) Freeze all non-critical AI Copilot model upgrades; (2) Degrade to Fast Path: skip KB Graph expansion, use keyword-only retrieval; (3) Display latency warning banner in Workbench; (4) Notify Platform Engineering Lead. |
| **Measurement Window** | 28-day rolling |
| **Exclusions** | LLM Provider outage (tracked separately as dependency SLO); Workbench client-side rendering time; user idle time between plan confirmation and artifact build trigger. |

#### Journey 2: "User Freezes and Deploys a Workflow" (Freeze → Test → Canary → 100%)

| Attribute | Definition |
|-----------|------------|
| **User Journey** | User clicks Freeze → Spec Refinement resolves fuzzy nodes → User signs off → Validation passes → Test Runner executes in Sandbox → Impact Report generated → PR created → Reviewer approves → Canary 1% → Canary 10% → 50% → 100% (automated gating at each stage per docs/03-architecture.md §4.2). |
| **SLI (Indicator)** | **p95 Time-to-Production (TTP)**: Time from "Freeze button clicked" to "100% cutover complete" for standard-risk changes (overall confidence ≥ 0.8, no Data Owner escalation required). Measured at Freeze Bridge Service. |
| **SLI Measurement** | Prometheus histogram `freeze_ttp_duration_seconds` with buckets [300, 600, 1800, 3600, 7200, 14400, 28800, 86400]. Starts at `freeze.initiated` event, ends at `canary.100pct.complete` event. |
| **SLO Target** | **p95 ≤ 4 hours** for standard-risk changes. High-risk (confidence <0.8 or escalated) tracked separately with p95 ≤ 24 hours. |
| **Error Budget** | **10% failure allowance** for standard-risk (~67.2 hours/month). Budget consumed by: (a) TTP exceeding 4h, (b) canary gate failure causing rollback. |
| **Budget Exhaustion Action** | (1) Mandatory manual gate review replaces auto-advancement at all canary stages; (2) All Freeze operations require 2× peer review instead of 1×; (3) Canary stages extend from 4h→8h (1%), 24h→48h (10%); (4) Root cause analysis mandatory for last 10 freezes. |
| **Measurement Window** | 28-day rolling |
| **Exclusions** | PR review waiting time (external human dependency — measured separately as `freeze_review_wait_duration_seconds`); Data Owner escalation resolution time. |

#### Journey 3: "Scheduled Workflow Executes Successfully"

| Attribute | Definition |
|-----------|------------|
| **User Journey** | Scheduler triggers Workflow at cron time → Runtime Executor acquires Sandbox → All Jobs execute in DAG order → Output rendered → Delivery to destination (email/S3/dashboard). |
| **SLI (Indicator)** | **(a) Success Rate**: `successful_executions / total_scheduled_executions` over the window. Success = all Jobs completed with status `SUCCESS` (not `FAILED`, `TIMED_OUT`, `BLOCKED`). **(b) p95 Execution Duration**: Time from Scheduler trigger to final Output delivery, per Workflow type. |
| **SLI Measurement** | **(a)** Prometheus counter `workflow_execution_total{status="success|failed|timeout"}`. **(b)** Histogram `workflow_execution_duration_seconds` with buckets [60, 300, 600, 1800, 3600, 7200, 14400]. Segmented by `workflow_type`. |
| **SLO Target** | **(a) Success Rate ≥ 99.5%** over 28-day window. **(b) p95 Duration ≤ 2× baseline** (baseline = 7-day moving average of p50 for that workflow). |
| **Error Budget** | **0.5% failure allowance** = ~3.36 hours/month of failures (28d×24h×0.5%). Each failed execution counts as ~(scheduled_interval) of budget consumed. |
| **Budget Exhaustion Action** | **Graduated Response**: 50% budget consumed → notification + voluntary slowdown; 80% budget consumed → all new deployments require additional approval; 100% budget consumed → freeze all non-critical feature releases \| Workflow (P2+) deployments (P0/P1 critical Workflows may continue deploying but require Tech Lead approval) |
| **Measurement Window** | 28-day rolling |
| **Exclusions** | Upstream data source unavailability (tracked as dependency health, not execution failure — Circuit Breaker open state fires a separate SLO); Force Majeure (cloud AZ outage) — tracked via separate DR SLO. |

#### Journey 4: "AI Knowledge Agent Answers a Question"

| Attribute | Definition |
|-----------|------------|
| **User Journey** | User asks a question in Conversation Interface → Agent parses intent → Injects RBAC context → Queries Code Graph (filtered) → Queries KB (filtered) → Queries Log Store (if relevant) → Fuses results → Checks output against permission boundaries → Returns answer with citations. |
| **SLI (Indicator)** | **(a) p95 Response Time**: Time from user question submission to AI answer rendered. **(b) Answer Accuracy Rate**: Percentage of answers where user does NOT click "This answer is incorrect" or "Report inaccuracy" within 7 days, sampled weekly. |
| **SLI Measurement** | **(a)** Histogram `agent_query_duration_seconds` with buckets [1, 2, 5, 10, 20, 30, 60]. **(b)** Counter `agent_answer_feedback_total{outcome="accurate|inaccurate|partial"}` — weekly sample of 100 random queries rated by human review panel. |
| **SLO Target** | **(a) p95 ≤ 20 seconds**. **(b) Accuracy Rate ≥ 85%** (human-rated sample). |
| **Error Budget** | **(a)** 5% latency budget. **(b)** 15% inaccuracy allowance. Combined budget: when either exhausts, actions triggered. |
| **Budget Exhaustion Action** | (1) Agent enters "High-Accuracy Mode": disables Log Store queries, reduces retrieved KB context window to top-3 results only; (2) Displays explicit "AI answer may be incomplete — verify against source" watermark on all answers; (3) Increases citation strictness: every claim must have an inline source link; (4) Triggers KB quality audit (check for stale/deprecated entries). |
| **Measurement Window** | 28-day rolling for latency; weekly sampling for accuracy. |
| **Exclusions** | Questions outside KB coverage (agent responds "I don't have enough information" — not counted as inaccurate); Code Graph or KB store unavailability (degraded mode tracked separately). |

#### Journey 5: "Reconciliation Run Completes"

| Attribute | Definition |
|-----------|------------|
| **User Journey** | Recon Rule triggers (scheduled or ad-hoc) → Match Execution Engine loads Source A and Source B → Hash match keys → Full outer join → Compare fields → Classify (Matched/Unmatched/Partial) → Break Analysis (AI-assisted) → Recon Report generated. |
| **SLI (Indicator)** | **p95 Execution Time for 1M rows** (combined Source A + Source B = 1,000,000 rows). Measured from Recon job start to Recon Report available. |
| **SLI Measurement** | Histogram `recon_duration_seconds` with buckets [30, 60, 120, 300, 600, 1800, 3600], filtered to executions with `total_rows` between 900K and 1.1M. |
| **SLO Target** | **p95 ≤ 5 minutes per 1M rows**. For larger volumes: linear scaling up to 10M rows (p95 ≤ 30 minutes). |
| **Error Budget** | **5% latency allowance**. Budget consumed per execution exceeding target. |
| **Budget Exhaustion Action** | (1) Recon auto-escalates from Light Engine to Heavy Engine (Spark/Trino) for all runs regardless of volume; (2) Disable AI-assisted Break Analysis (fall back to rule-based classification only); (3) Recon schedule reduced: high-frequency recons (sub-hourly) downgraded to hourly; (4) Notify Data Platform Team to provision additional compute. |
| **Measurement Window** | 28-day rolling |
| **Exclusions** | Source A or Source B data unavailability (Circuit Breaker open → Recon skipped with incident created, not counted as latency violation); Schema changes requiring manual Match Key reconfiguration. |

### 19.2 Error Budget Policy Summary

| Journey | SLI | SLO | Monthly Error Budget | Budget Exhaustion Gates |
|---------|-----|-----|----------------------|------------------------|
| NL → Preview | p95 latency | ≤15s | 5% (~33.6h) | → Fast Path degradation |
| Freeze → Deploy | p95 TTP | ≤4h (standard) | 10% (~67.2h) | → Manual gates + extended canary |
| Scheduled Execution | Success rate | ≥99.5% | 0.5% (~3.36h) | → Freeze new deploys |
| AI Agent QA | p95 latency + accuracy | ≤20s + ≥85% | 5% latency / 15% inaccuracy | → High-Accuracy Mode |
| Recon Run (1M rows) | p95 duration | ≤5min | 5% | → Heavy Engine escalation |

---


> 📄 Original Location: [../03-architecture.md §19](../03-architecture.md)
