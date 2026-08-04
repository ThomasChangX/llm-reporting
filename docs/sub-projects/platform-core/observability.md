# Observability & Log System

> **Origin**: §8 Log System + §12.6 Observation Engine of [`docs/03-architecture.md`](../../03-architecture.md) | **Sub-project**: [platform-core](README.md)

## Purpose

This module provides the platform's observability backbone: a three-layer log system (§8) aligned with the OpenTelemetry (CNCF graduated) standard for distributed tracing and metrics export, plus an AI-driven Observation Engine (§12.6) that detects recurring user-behavior patterns and suggests Workflow automations. Together they give every plane (Design, Freeze, Runtime) and every sub-project a uniform way to emit structured events, traces, metrics, and LLM-interaction records, and they feed AI-powered consumers (real-time anomaly detection, incident diagnosis assistant, cost tracking dashboard). This document is the detailed companion to the Observability pillar summarized in §11.4 of [cross-cutting-layer.md](cross-cutting-layer.md).

## Boundaries

**In-scope:**
- Three-layer log system: Structured Event Log, Execution Trace, LLM Interaction Log (§8).
- OpenTelemetry alignment: trace context, span semantics, metrics export, log correlation, collector (§8.1).
- Pattern-detection pipeline and Suggestion Engine for user-behavior observation (§12.6 / FR3).
- Pattern storage to the KB Behavior Patterns domain (→ FR32.6) and confidence decay.

**Delegated / out-of-scope:**
- The **metrics/traces/logs/alerting pillar summary** (RED metrics, Prometheus + Grafana, Alertmanager rules) is in [cross-cutting-layer.md](cross-cutting-layer.md) §11.4; this document holds the deeper §8/§12.6 detail.
- **KB Behavior Patterns domain storage** → knowledge-services sub-project (FR32.6).
- **Incident Manager** and incident diagnosis assistant → workflow-engine / agent-platform.
- **Cost Tracking Dashboard** data sourcing → shared with [operational-architecture.md](operational-architecture.md) capacity planning.

**Upstream/downstream neighbors:**
- *Producers*: API Gateway, Design Plane, Freeze Bridge, Workflow Executor, Sandbox, DB queries, LLM calls, Workbench user actions, all sub-projects.
- *Consumers*: Elasticsearch/Kibana (logs), Prometheus/Grafana (metrics), Tempo/Jaeger (traces), S3/Glacier (cold LLM transcripts), the Observation Engine's Suggestion Engine, and AI-powered consumers.

## Interfaces

### §8 Three-Layer Log System

| Layer | Content | Storage |
| --- | --- | --- |
| **Structured Event Log** | All system events, unified Schema (event_id/type/tenant/workflow/job/actor/data/result/error) | Hot: ES 7 days |
| **Execution Trace** | OpenTelemetry-style, complete call chain for each Workflow | Warm: S3+Parquet 90 days |
| **LLM Interaction Log** | Each AI call: prompt_hash, **full prompt + response text** (Cold storage for debugging), kb_retrieved, tokens, cost, latency, outcome, guard_trigger_events | Hot: ES 7 days (metadata) + Cold: Glacier 7 years (full prompt/response) |

AI-Powered consumers: Real-time anomaly detection, Incident Diagnosis Assistant, Cost Tracking Dashboard.

### §8.1 OpenTelemetry Alignment (Observability Standard Alignment)

The system aligns with the **OpenTelemetry** (CNCF graduated project) standard for distributed tracing and metrics export:

| OTel Component | Implementation | Details |
| --- | --- | --- |
| **Trace Context** | W3C Trace Context (`traceparent` header) | `trace_id UUID` propagates across audit_log, LLM Interaction Log, Workflow Executor spans; crosses service boundaries (API Gateway → Design Plane → Freeze Bridge → Runtime Plane) via gRPC metadata |
| **Span Semantics** | OTel Semantic Conventions v1.27 | `service.name`, `span.kind` (CLIENT/SERVER/INTERNAL), `http.method`, `db.system`, `gen_ai.request.model` (LLM GenAI conventions) |
| **Metrics Export** | OTLP (gRPC) → Prometheus | Histogram metrics (p95 latency, duration) follow OTel Metrics Data Model; Exemplar supports trace-metric correlation |
| **Log Correlation** | `trace_id` + `span_id` in structured logs | Each log entry in ES carries trace context; Kibana one-click jump to corresponding trace |
| **Collector** | OpenTelemetry Collector (Gateway mode) | Deployed as DaemonSet, receives OTLP/jaeger/zipkin, exports to Prometheus + Tempo/Jaeger |

**Aligned with Data Classification**: T3-level span attributes (such as PII field names) are automatically redacted by the OTel Collector's `redactionprocessor` before export.

### §12.6 Observation Engine (FR3) — Suggestion Engine surface

| Surface | Behavior |
| --- | --- |
| Suggestion prompt | "Detected you repeat the following operations ... Create an automated Workflow?" with actions `[Create Workflow] [Dismiss] [Snooze 7 days]` |
| Pattern emission | Patterns flow to the KB Behavior Patterns domain (→ FR32.6) |
| Confidence decay | Pattern not seen for 30 days → `confidence *= 0.8` |
| Privacy boundary | All pattern detection within single tenant boundary (no cross-tenant learning in SaaS multi-tenant mode) |

## Dependencies

- **OpenTelemetry Collector** (Gateway mode, DaemonSet) — receives OTLP/jaeger/zipkin.
- **Prometheus + Grafana** — metrics sink (OTLP gRPC → Prometheus).
- **Tempo / Jaeger** — distributed trace backend.
- **Elasticsearch + Kibana** — structured event log hot store (7 days); one-click trace jump.
- **S3 + Parquet** — warm execution traces (90 days).
- **S3 Glacier** — cold LLM prompt/response transcripts (7 years, compliance).
- **W3C Trace Context** propagation across service boundaries via gRPC metadata.
- **KB (Behavior Patterns domain)** — downstream store for detected patterns (FR32.6).
- **Workbench + API Gateway** — user-action stream source for pattern detection.
- **OTel `redactionprocessor`** — enforces T3 data-classification redaction before export.

## Data Model

- **Structured Event Log record**: `event_id, type, tenant, workflow, job, actor, data, result, error`. Unified schema for all system events.
- **Execution Trace**: OpenTelemetry-style spans forming the complete call chain per Workflow.
- **LLM Interaction Log record**: `prompt_hash`, full prompt + response text (cold), `kb_retrieved`, `tokens`, `cost`, `latency`, `outcome`, `guard_trigger_events`.
- **Trace context**: W3C `traceparent` carrying `trace_id` (UUID) + `span_id`, propagated through audit_log, LLM Interaction Log, and Workflow Executor spans.
- **Span attributes** (OTel Semantic Conventions v1.27): `service.name`, `span.kind`, `http.method`, `db.system`, `gen_ai.request.model`. T3 attributes (e.g. PII field names) redacted by the collector.
- **Behavior pattern** (Observation Engine): detected sequence / frequency / temporal pattern with a decaying confidence score; stored in the KB Behavior Patterns domain.

## Failure Modes & Recovery

| Failure | Impact | Recovery |
| --- | --- | --- |
| OTel Collector down | Trace/metric/log export stalls; in-process SDKs buffer/batch until collector returns (bounded retry). | DaemonSet restart resumes collection; gaps in trace coverage possible but services unaffected. |
| Elasticsearch hot store unavailable | Structured Event Log + LLM metadata queries fail; ingestion can be queued/retried. | ES snapshot restore (daily snapshot to S3, RPO 24h, RTO <8h — see [operational-architecture.md](operational-architecture.md) §24.1/§12.3). |
| Prometheus scrape gap | Metrics missing for window; exemplars/trace-metric correlation degraded. | Self-healing Prometheus; long-term metrics persisted to object storage per retention policy. |
| S3/Glacier cold tier unavailable | LLM transcript cold retrieval blocked; hot metadata (7d) still queryable. | S3 cross-region replication (async); Glacier restore on demand. |
| Pattern pipeline lag | Automation suggestions delayed; no functional impact on executed workflows. | Confidence decay (`*= 0.8` after 30d) keeps suggestions from going stale. |
| Cross-tenant leakage risk | Privacy boundary violation. | Mitigated by design: no cross-tenant learning in SaaS multi-tenant mode; pattern detection is within a single tenant boundary. |

Cross-ref: full backup/DR coverage for ES, S3, and logs is in [operational-architecture.md](operational-architecture.md) §24.1 and §12.3 ([domain-services.md](domain-services.md)).

## Non-Functional Requirements

- **Sampling**: Traces sampled at 100% for failures, 10% for successes (§11.4).
- **Log retention**: Hot ES 7 days; Warm S3+Parquet 90 days; Cold Glacier 7 years (LLM prompt/response) — see [operational-architecture.md](operational-architecture.md) §24.4 for the full retention matrix.
- **Log-level control**: Structured JSON logs; log-level dynamically adjustable per tenant without restart (§11.4).
- **Standardization**: W3C Trace Context; OTel Semantic Conventions v1.27; OTLP gRPC export; OTel Metrics Data Model with Exemplars.
- **PII protection**: T3-level span attributes auto-redacted by `redactionprocessor` before export.
- **Privacy**: Single-tenant boundary for pattern detection in SaaS multi-tenant mode.
- **SLOs**: Observability pipeline lag tracked as a platform SLO — see [docs/operations/slo-sli.md](../../operations/slo-sli.md). Alert: KB sync lag >60s (§11.4).
- **Security**: cold LLM transcripts at rest AES-256; access governed by [docs/security/threat-model.md](../../security/threat-model.md).

## Key Flows

### §8 Log ingestion tiers

Hot (ES, 7d, structured events + LLM metadata) → Warm (S3+Parquet, 90d, execution traces) → Cold (Glacier, 7yr, full LLM prompt/response). Trace context (`trace_id`/`span_id`) is carried in each structured log entry, enabling Kibana one-click jump to the corresponding trace.

### §8.1 Cross-service trace propagation

`trace_id` (UUID) propagates across audit_log → LLM Interaction Log → Workflow Executor spans, crossing service boundaries (API Gateway → Design Plane → Freeze Bridge → Runtime Plane) via gRPC metadata (W3C `traceparent`). Metrics use OTel Exemplars to correlate back to traces.

### §12.6 Pattern Detection Pipeline (FR3)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     PATTERN DETECTION PIPELINE                            │
│                                                                          │
│  USER ACTIONS STREAM (from Workbench + API Gateway)                      │
│       │                                                                  │
│       ▼                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐   │
│  │ SEQUENCE MINER    │  │ FREQUENCY TRACKER│  │ TEMPORAL ANALYZER    │   │
│  │ Repeated action   │  │ "User runs same  │  │ "Every Monday 9am    │   │
│  │ sequences >3      │  │  filter 5x/week" │  │  user opens report X"│   │
│  │ → Workflow cand.  │  │ → Automation sug.│  │ → Schedule suggestion│   │
│  └────────┬──────────┘  └────────┬─────────┘  └───────────┬──────────┘   │
│           └──────────────────────┼────────────────────────┘              │
│                                  ▼                                        │
│                     SUGGESTION ENGINE                                     │
│  ┌───────────────────────────────────────────────────────────┐          │
│  │ "Detected you repeat the following operations every Monday morning: Open ERP report → Filter region  │          │
│  │  → Export Excel → Send email to CFO. Create an automated Workflow?"   │          │
│  │ [Create Workflow] [Dismiss] [Snooze 7 days]               │          │
│  └───────────────────────────────────────────────────────────┘          │
│                                                                          │
│  Pattern storage → KB Behavior Patterns domain (→ FR32.6)               │
│  Confidence decay: pattern not seen for 30 days → confidence *= 0.8     │
│  Privacy: all pattern detection within single tenant boundary            │
│           (no cross-tenant learning in SaaS multi-tenant mode)           │
└─────────────────────────────────────────────────────────────────────────┘
```

## Design References

- **Original sections**: §8 Log System + §8.1 OpenTelemetry Alignment, §12.6 Observation Engine (FR3) of [`docs/03-architecture.md`](../../03-architecture.md).
- **Pillar summary**: [cross-cutting-layer.md](cross-cutting-layer.md) §11.4 (Metrics / Traces / Logs / Alerting / Dashboards).
- **Retention & backup**: [operational-architecture.md](operational-architecture.md) §24.1 (Backup & Recovery), §24.4 (Data Retention Policies).
- **ADRs** ([index](../../adr-index.md)): [ADR-0020 Agent Cost Governance & Model Degradation Detection](../../../adr/0020-agent-cost-governance.md) (cost tracking), [ADR-0018 Agent Evaluation Framework](../../../adr/0018-agent-evaluation-framework.md).
- **Glossary** ([../../glossary.md](../../glossary.md)): Compute Spec, Production Environment, Cross-Environment Read-Only Mode.
- **External procedures**: [docs/operations/slo-sli.md](../../operations/slo-sli.md), [docs/operations/backup-dr.md](../../operations/backup-dr.md), [docs/security/threat-model.md](../../security/threat-model.md).
