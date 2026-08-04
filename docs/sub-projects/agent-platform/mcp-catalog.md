# MCP Server Catalog

> **Origin**: §22C of [`docs/03-architecture.md`](../../03-architecture.md) (with BRD-pipeline MCPs MCP-20/21/22 from §23.8.2) | **Sub-project**: [agent-platform](README.md)

## Purpose

This module covers the **MCP Server Catalog** (§22C). MCP (Model Context Protocol) is the standard protocol layer for Agent interaction with external systems. Each MCP server exposes a set of Tool/Resource endpoints, communicating via gRPC (internal service-to-service) or REST (external/cross-network). All MCP calls must carry tenant context and authentication credentials.

This module owns:
- **Core MCP Servers** (§22C) — MCP-01 through MCP-17 plus MCP-23, the agent-facing MCP endpoints invoked by Skills and the Agent runtime.
- **MCP Deployment Architecture** (§22C) — the MCP Gateway as the unified, mandatory entry point (auth validation, rate limiting, request logging, circuit breaking) and the gRPC/REST MCP Pod layout.
- **BRD-pipeline MCP servers MCP-20/21/22** (§23.8.2) — referenced here for catalog completeness; these are detailed in the [`brd-adr-lifecycle`](../brd-adr-lifecycle/) sub-project.

## Boundaries

**In-scope:**
- §22C — the MCP protocol contract (gRPC vs REST, tenant context, authentication), the per-server catalog (exposed tools/resources, protocol, authentication, rate limit, timeout), and the MCP Gateway deployment architecture with its mandatory behaviors.
- The 18 core agent-facing MCP servers: MCP-01 (vector-search), MCP-02 (graph-traverse), MCP-03 (graph-query / Code Graph), MCP-04 (pg-query), MCP-05 (log-search), MCP-06 (git-diff), MCP-07 (template-search), MCP-08 (data-profile), MCP-09 (incident-query), MCP-10 (user-activity-stream), MCP-11 (email-parser), MCP-12 (ocr), MCP-13 (static-analysis), MCP-14 (notification-send), MCP-15 (data-source-test), MCP-16 (excel-parser), MCP-17 (external-ticketing), MCP-23 (code-knowledge-search).
- Reference entries for the BRD-pipeline MCPs MCP-20 (jira-sync), MCP-21 (confluence-export), MCP-22 (compliance-mapper) from §23.8.2.

**Delegated / out-of-scope:**
- The Skills that consume these MCP endpoints → [`skill-catalog.md`](skill-catalog.md) (§22B).
- The Agent runtime's Parallel Tool Executor and how it calls MCPs → [`dual-mode-orchestration.md`](dual-mode-orchestration.md) (§22A.1 Step 4 / §22A.2 Step 4).
- The Permission Gate and Output Sanitizer that wrap every MCP call → [`agent-security.md`](agent-security.md) (§22D Layer 2 / Layer 3).
- Full detail and ownership of MCP-20/21/22 (BRD↔Jira sync, Confluence/Notion export, compliance mapping) → [`brd-adr-lifecycle`](../brd-adr-lifecycle/).
- Underlying data stores (KB vector index, Code Graph, PostgreSQL, log store) → [`knowledge-services`](../knowledge-services/) and [`platform-core`](../platform-core/).
- External system credentials / Vault injection (referenced by MCP-17, MCP-20, MCP-21) → [`platform-core`](../platform-core/).

**Upstream/downstream neighbors:**
- *Input*: tool-call requests from the Agent runtime (via the MCP Gateway), each carrying API Key + `X-Tenant-ID` (+ mTLS / RBAC context as required).
- *Output*: tool results returned to the Output Sanitizer (§22A.1 Step 5) before entering the LLM context.

## Interfaces

> MCP (Model Context Protocol) is the standard protocol layer for Agent interaction with external systems. Each MCP server exposes a set of Tool/Resource endpoints, communicating via gRPC (internal service-to-service) or REST (external/cross-network). All MCP calls must carry tenant context and authentication credentials.

### Core MCP Servers

| MCP ID     | Server Name              | Exposed Tools/Resources                                                                                                                                                                                                                                                                                                                | Protocol        | Authentication                                                                                                    | Rate Limit              | Timeout |
| ---------- | ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- | ----------------------------------------------------------------------------------------------------------------- | ----------------------- | ------- |
| **MCP-01** | vector-search            | `search(query: str, top_k: int, filters: dict) → SearchResults` — Semantic search over KB vector index; `embed(text: str\|list[str]) → Vector\|list[Vector]` — Text to vector; `hybrid_search(semantic_weight: float, keyword: str, top_k: int, filters: dict) → SearchResults` — Hybrid search                                        | gRPC (protobuf) | API Key + `X-Tenant-ID` Header + mTLS                                                                             | 100 req/min per tenant  | 5s      |
| **MCP-02** | graph-traverse           | `traverse(node_id: str, relation: str, depth: int, direction: "IN"\|"OUT"\|"BOTH") → Subgraph` — KB relationship graph traversal; `expand_context(kb_ids: list[str], hop: int) → RelatedNodes` — Expand related context                                                                                                                 | gRPC            | API Key + `X-Tenant-ID` + mTLS                                                                                    | 50 req/min per tenant   | 3s      |
| **MCP-03** | graph-query (Code Graph) | `query(cypher: str, params: dict) → QueryResults` — Parameterized Cypher query; `nl_query(question: str) → { cypher, results, explanation }` — NL→Cypher→results; `get_lineage(entity_id: str, direction: "upstream"\|"downstream"\|"both", depth: int) → LineageDAG` — Lineage tracking; `get_subgraph(root_id: str, radius: int) → Subgraph` — Subgraph export | gRPC            | API Key + `X-Tenant-ID` + RBAC Filter (query-level injection: `WHERE node.tenant_id = $tenant_id` auto-appended) | 100 req/min per tenant  | 10s     |
| **MCP-04** | pg-query                 | `sql(query: str, params: dict) → ResultSet` — **Read-only** parameterized SQL query; `get_schema(table_pattern: str) → SchemaInfo` — Table schema discovery                                                                                                                                                                             | gRPC            | API Key + `X-Tenant-ID` + Column-Level ACL (query rewriter injects column-level redaction and row-level filtering at DB Proxy layer) | 200 req/min per tenant  | 15s     |
| **MCP-05** | log-search               | `search_logs(filters: dict, time_range: {start, end}, level?: str, limit?: int) → LogEntries` — Structured log query; `get_trace(trace_id: str) → TraceSpans` — Distributed trace reconstruction; `get_execution_context(execution_id: str) → ExecutionContext` — Execution context aggregation                                          | gRPC            | API Key + `X-Tenant-ID` + Role filtering (Dev→full technical logs; Business→business-layer logs only, error stack truncated) | 50 req/min per tenant   | 10s     |
| **MCP-06** | git-diff                 | `diff(branch_a: str, branch_b: str, path?: str) → UnifiedDiff` — Branch/commit diff; `blame(file: str, line: int) → BlameInfo` — Line-level change history; `log(path: str, limit?: int) → CommitHistory` — Commit history                                                                                                              | gRPC            | API Key + `X-Tenant-ID` + Git Repo-level permission (only Agent service account has read access)                  | 30 req/min per tenant   | 10s     |
| **MCP-07** | template-search          | `search_templates(query: str, category?: str, tags?: list[str]) → TemplateList` — Template search; `render(template_id: str, variables: dict, format: "md"\|"pdf") → RenderedOutput` — Template rendering; `validate_template(template_yaml: str) → ValidationResult` — Template validation                                              | REST (JSON)     | API Key + `X-Tenant-ID` Header                                                                                    | 100 req/min per tenant  | 15s     |
| **MCP-08** | data-profile             | `profile(source_id: str, sample_size?: int, columns?: list[str]) → ProfileStats` — Data Profile (distribution/statistics/patterns); `detect_anomalies(source_id: str, baseline_profile_id?: str) → AnomalyList` — Anomaly detection; `compare_profiles(profile_a: str, profile_b: str) → ProfileDiff` — Profile comparison            | gRPC            | API Key + `X-Tenant-ID` + Source ACL (only data sources the user is authorized to access can be Profiled; T3 columns auto-redacted before Profiling) | 20 req/min per tenant   | 60s     |
| **MCP-09** | incident-query           | `get_incident(id: str) → IncidentDetail` — Incident detail; `list_incidents(filters: dict, page: int) → IncidentList` — Incident list; `correlate(incident_id: str) → RelatedIncidents` — Similar Incident correlation; `get_timeline(incident_id: str) → IncidentTimeline` — Event timeline                                              | gRPC            | API Key + `X-Tenant-ID`                                                                                           | 50 req/min per tenant   | 5s      |
| **MCP-10** | user-activity-stream     | `get_actions(user_id: str, time_range: {start, end}, limit?: int) → ActionSequence` — User action sequence; `detect_patterns(user_id: str, min_frequency?: int) → PatternList` — Pattern detection (triggers S11)                                                                                                                         | gRPC            | API Key + `X-Tenant-ID` (enforced same-tenant — user_id must belong to requesting tenant)                         | 30 req/min per tenant   | 10s     |
| **MCP-11** | email-parser             | `parse_eml(bytes: bytes) → EmailRecord` — .eml parsing; `parse_msg(bytes: bytes) → EmailRecord` — .msg parsing; `extract_facts(email_id: str) → ExtractedFactList` — Fact extraction (triggers S10); `get_attachment(email_id: str, attachment_index: int) → AttachmentData` — Attachment retrieval                                      | gRPC            | API Key + `X-Tenant-ID`                                                                                           | 30 req/min per tenant   | 30s     |
| **MCP-12** | ocr                      | `extract_text(image_bytes: bytes, language?: str) → OcrResult` — Image OCR; `extract_tables(pdf_bytes: bytes, pages?: list[int]) → TableList` — PDF table extraction; `extract_structured(document_bytes: bytes, type: "invoice"\|"receipt"\|"statement") → StructuredData` — Structured document extraction                             | gRPC            | API Key + `X-Tenant-ID`                                                                                           | 10 req/min per tenant   | 60s     |
| **MCP-13** | static-analysis          | `analyze_spec(spec_yaml: str) → SpecIssues` — Compute Spec static analysis (anti-patterns/security/performance); `analyze_python(code: str) → PythonIssues` — Python AST security analysis (detects eval/exec/forbidden imports/network calls etc. — see Section 7.2)                                                                      | gRPC            | API Key + `X-Tenant-ID`                                                                                           | 30 req/min per tenant   | 30s     |
| **MCP-14** | notification-send        | `send(channel: "email"\|"slack"\|"teams"\|"in-app"\|"webhook"\|"sms", template_id: str, variables: dict, recipients: list[str]) → SendResult` — Templated notification sending; `send_raw(channel: str, content: { subject?, body, ... }, recipients: list[str]) → SendResult` — Custom notification                                      | gRPC            | API Key + `X-Tenant-ID` + RBAC (who can notify whom: only same-tenant users; Critical-level notifications require additional elevated permission) | 200 req/min per tenant  | 10s     |
| **MCP-15** | data-source-test         | `test_connection(config: DataSourceConfig) → ConnectionTestResult` — Connection test; `discover_schema(config: DataSourceConfig) → SchemaInfo` — Schema discovery; `sample_data(config: DataSourceConfig, table: str, limit?: int) → SampleData` — Sample data                                                                             | gRPC            | API Key + `X-Tenant-ID`                                                                                           | 20 req/min per tenant   | 30s     |
| **MCP-16** | excel-parser             | `parse(file_bytes: bytes) → ParsedWorkbook { sheets: [{ name, tables: [...], formulas: [...], charts: [...] }] }` — Excel workbook parsing; `extract_logic(file_bytes: bytes) → LogicModel` — Formula logic extraction (attempts to recover computation intent)                                                                           | gRPC            | API Key + `X-Tenant-ID`                                                                                           | 20 req/min per tenant   | 30s     |
| **MCP-17** | external-ticketing       | `create_ticket(system: "jira"\|"rally"\|"servicenow"\|"azure_devops", project: str, issue_type: str, fields: dict) → TicketResult` — Create external ticket; `link_brd(ticket_id: str, brd_id: str) → LinkResult` — BRD↔Ticket bidirectional link; `get_status(ticket_id: str) → TicketStatus` — Query ticket status                                                                          | gRPC            | API Key + `X-Tenant-ID` + External System Credential (Vault injection)                                            | 50 req/min per tenant   | 15s     |
| **MCP-23** | code-knowledge-search    | `semantic_search_code(query: str, language?: str, top_k?: int) → CodeResults` — Semantic search over the Code Knowledge index (find functions by meaning, not name); `get_function(function_id: str) → FunctionDetail` — Full function source + Docstring + caller/callee list; `get_call_graph(root_function: str, depth?: int) → CallGraph` — Call-graph subgraph export; `find_similar_code(function_id: str, top_k?: int) → SimilarFunctions` — Find structurally/semantically similar functions | gRPC            | API Key + `X-Tenant-ID` + RBAC (Dev→full code access; Business User→no code access, only Spec-level)              | 50 req/min per tenant   | 10s     |

### BRD-Pipeline MCP Servers (reference — detailed in brd-adr-lifecycle)

> The following MCP servers are part of the BRD/ADR lifecycle pipeline (§23.8.2). They are listed here for catalog completeness; full definitions, ownership, and flows live in the [`brd-adr-lifecycle`](../brd-adr-lifecycle/) sub-project.

| MCP ID | Server Name | Purpose (summary) | Protocol | Auth | Rate Limit | Timeout |
| --- | --- | --- | --- | --- | --- | --- |
| **MCP-20** | jira-sync | Jira one-way sync: create Epic/Story from BRD, link BRD↔Epic, push BRD status to Jira, read-only Story status via webhook, Jira→Spec→PR→Deploy traceability. BRD is the sole Source of Truth — Jira content does not write back to BRD. | REST (JSON) over TLS 1.3 | OAuth 2.0 (Jira Cloud) / PAT (Jira Server) + `X-Tenant-ID` | 30 req/min per tenant (limited by Jira API) | 15s |
| **MCP-21** | confluence-export | Export BRD/ADR to Confluence page or Notion database (single + batch); render BRD/ADR YAML → Confluence Storage Format (XHTML) / Notion Blocks including all traceability links auto-converted to hyperlinks. | REST (JSON) | OAuth 2.0 (Confluence Cloud) / API Token (Confluence Server/Notion) | 10 req/min per tenant | 30s |
| **MCP-22** | compliance-mapper | Map BRD requirements to compliance framework controls (SOX 302/404, HIPAA, GDPR Art.5/25/32, ASC606 5-step, Basel III, …); validate coverage; AI-suggest missing controls. Pre-loaded library + tenant custom framework extensions. | gRPC | API Key + `X-Tenant-ID` + mTLS | 20 req/min per tenant | 10s |

Full detail for MCP-20/21/22 (tool signatures, sync direction, render format, compliance framework library) → [`brd-adr-lifecycle`](../brd-adr-lifecycle/) (§23.8.2).

### MCP Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        MCP GATEWAY                                      │
│  • Unified entry point for all MCP calls                                │
│  • Auth validation: API Key + Tenant Header + mTLS cert                 │
│  • Rate limit enforcement (per tenant per MCP)                          │
│  • Request logging (all MCP calls → Audit Trail)                        │
│  • Circuit breaker per MCP server                                       │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │
     ┌─────────────────────┼─────────────────────┐
     ▼                     ▼                     ▼
┌──────────┐        ┌──────────┐          ┌──────────┐
│ MCP Pod  │        │ MCP Pod  │          │ MCP Pod  │
│ (gRPC)   │        │ (gRPC)   │   ...    │ (REST)   │
│          │        │          │          │          │
│ MCP-01   │        │ MCP-03   │          │ MCP-07   │
│ MCP-02   │        │ MCP-04   │          │          │
│ MCP-05   │        │ MCP-06   │          │          │
│ MCP-08   │        │ MCP-09   │          │          │
│ ...      │        │ ...      │          │          │
└──────────┘        └──────────┘          └──────────┘
```

**MCP Gateway Key Behaviors**:
- All MCP calls **must** go through the Gateway — Agent Runtime must not connect directly to MCP backends
- Gateway injects before forwarding: `X-Internal-Caller: "agent-runtime"`, `X-Trace-ID: <trace_id>`
- Gateway enforces rate limiting — exceeding limit returns `429 Too Many Requests` + `Retry-After` header
- MCP backend unavailable → Gateway returns `503 Service Unavailable` + automatic failover to standby instance

## Dependencies

- **Agent runtime** ([`dual-mode-orchestration.md`](dual-mode-orchestration.md), §22A.1 Step 4) — the Parallel Tool Executor is the sole legitimate caller; it must route every call through the MCP Gateway, never directly to a backend.
- **Skills** ([`skill-catalog.md`](skill-catalog.md), §22B) — each Skill's `Tools` field references specific MCP endpoints (e.g., S02 → MCP-01/02/04; S07 → MCP-05/09; S12 → MCP-06/13; S14 → MCP-16; S18 → S02→MCP-01/02/04).
- **Agent security** ([`agent-security.md`](agent-security.md), §22D) — Layer 2 (Permission Gate) performs the 4-dim check before the call; Layer 3 (Output Sanitizer) sanitizes MCP results before they enter LLM context; several MCPs carry their own auth/RBAC (mTLS, RBAC Filter, Column-Level ACL, Source ACL, role filtering).
- **Knowledge services** ([`knowledge-services`](../knowledge-services/)) — the backends behind MCP-01 (KB vector index), MCP-02 (KB graph), MCP-03 (Code Graph), MCP-23 (Code Knowledge index).
- **Platform core** ([`platform-core`](../platform-core/)) — PostgreSQL/DB Proxy behind MCP-04 (Column-Level/Row-Level ACL rewriter), Log Store behind MCP-05, Audit Trail sink for the Gateway, Incident Manager behind MCP-09, Notification service behind MCP-14, Vault for external credentials (MCP-17/20/21).
- **Workflow engine** ([`workflow-engine`](../workflow-engine/)) — MCP-06 (git-diff over Spec branches), MCP-07 (template library for Compute Spec), MCP-13 (Spec static analysis).
- **External systems** — Jira (MCP-17/20), Confluence/Notion (MCP-21), Rally/ServiceNow/Azure DevOps (MCP-17), email servers / .eml/.msg stores (MCP-11), OCR document sources (MCP-12), Excel/PowerBI (MCP-16).

## Data Model

- **MCP tool-call request** — `{ tool: "<MCP-ID>.<method>", params: {...} }` issued by the Agent runtime; must carry API Key + `X-Tenant-ID` (+ mTLS / RBAC context as per the server's `Authentication`).
- **Gateway-injected headers** — `X-Internal-Caller: "agent-runtime"`, `X-Trace-ID: <trace_id>` added before forwarding (§22C Gateway behaviors).
- **Per-tenant rate-limit counters** — enforced per tenant per MCP at the Gateway (values in the catalog table: 10–200 req/min per tenant).
- **Tenant-isolation query injection** — MCP-03 appends `WHERE node.tenant_id = $tenant_id`; MCP-04 rewriter injects column-level redaction and row-level filtering at the DB Proxy.
- **MCP-16 ParsedWorkbook** — `{ sheets: [{ name, tables: [...], formulas: [...], charts: [...] }] }`; MCP-16 `LogicModel` (recovered computation intent).
- **MCP-20/21/22 BRD-side artifacts** (reference) — Jira Epic/Story links, Confluence/Notion page mappings, compliance-framework control mappings; the BRD YAML remains the single Source of Truth.

## Failure Modes & Recovery

| Failure | Impact | Detection | Recovery |
| ------- | ------ | --------- | -------- |
| **Rate limit exceeded (per tenant per MCP)** | Request rejected | Gateway rate-limit enforcement | `429 Too Many Requests` + `Retry-After` header; caller backs off and retries |
| **MCP backend unavailable** | Tool call fails | Gateway health check / circuit breaker | Gateway returns `503 Service Unavailable` + automatic failover to standby instance; circuit breaker trips per MCP server |
| **Agent Runtime bypasses Gateway** | Direct backend access (security violation) | "All MCP calls must go through the Gateway" rule; Network Policy / iptables block non-Gateway egress (see [`agent-security.md`](agent-security.md) §22D Layer 7) | Connection blocked at network layer; flagged as security event |
| **Cross-tenant access attempt via MCP** | Tenant boundary breach | MCP-03 `tenant_id` injection; MCP-04 ACL rewriter; MCP-10 same-tenant enforcement | Query rejected / filtered; cross-tenant access requires explicit recorded opt-in; SECURITY-level alert |
| **Unauthorized column/row access (MCP-04/MCP-08)** | PII/restricted data leak | Column-Level ACL rewriter; Source ACL; T3 auto-redaction | Query rewritten (T3 → REDACT, T2 → HASH) or denied; redaction irreversible |
| **MCP-05 log role leakage** | Business User sees technical stack | Role filtering at MCP-05 (Dev→full; Business→business-layer only, stack truncated) | Error stack truncated before return |
| **External system credential failure (MCP-17/20/21)** | Ticket/page creation fails | Vault injection failure / OAuth expiry | Credential refresh via Vault; caller retry with backoff |
| **Tool output exceeds 100KB / 1M rows** | LLM context overflow / cost spike | Output Sanitizer truncation rules (§22D Layer 3) | Truncate to first 20KB + small-model summary; very large sets → schema + row count + 10 sample rows + stats |
| **Reflection injection in tool output** | Malicious MCP data steers LLM | Output Sanitizer reflection-injection scan | Hard block — fragment removed/replaced with `[FILTERED: potential injection detected]`; SECURITY-level log |

## Non-Functional Requirements

- **Gateway-mandated** — all MCP calls go through the MCP Gateway; the Agent Runtime must never connect directly to MCP backends (§22C).
- **Tenant context on every call** — every MCP call must carry tenant context and authentication credentials (API Key + `X-Tenant-ID`, plus mTLS / RBAC / External Credential as specified per server) (§22C).
- **Per-tenant rate limiting** — each MCP enforces a per-tenant rate limit (10–200 req/min); the Gateway returns `429` + `Retry-After` on excess (§22C catalog + Gateway behaviors).
- **Per-call timeouts** — each MCP declares a timeout (3s–60s); MCP-08 (data-profile) and MCP-12 (ocr) are the longest at 60s (§22C catalog).
- **Circuit breaking & failover** — the Gateway runs a circuit breaker per MCP server and fails over to a standby instance on `503` (§22C Gateway behaviors).
- **Tenant isolation by construction** — MCP-03 injects `WHERE node.tenant_id = $tenant_id`; MCP-04 rewrites with column-level/row-level ACL; MCP-10 enforces same-tenant `user_id`; MCP-23 RBAC filters Dev vs Business User code access (§22C catalog).
- **Full audit** — all MCP calls are logged to the Audit Trail by the Gateway (§22C Gateway behaviors; aligns with §22D Layer 6).
- **Read-only where stated** — MCP-04 `sql` is explicitly read-only; MCP-20 Jira sync is one-way (System → Jira) with BRD as sole Source of Truth (§22C, §23.8.2).
- **PII / sensitivity handling** — MCP-08 auto-redacts T3 columns before profiling; MCP-04 redacts at the DB Proxy; aligns with §22D Layer 3 irreversible redaction.

## Key Flows

### MCP tool-call (Gateway-mediated, §22C)

```
Agent Runtime (Step 4 Parallel Tool Executor)
  → builds tool-call request { tool: "MCP-ID.method", params }
  → MCP Gateway:
      • Auth validation (API Key + X-Tenant-ID + mTLS)
      • Rate-limit check (per tenant per MCP) → 429 + Retry-After on excess
      • Inject X-Internal-Caller: "agent-runtime", X-Trace-ID
      • Circuit breaker per MCP server
  → MCP Pod (gRPC or REST)
      • Tenant isolation (MCP-03 tenant_id injection / MCP-04 ACL rewriter / MCP-10 same-tenant)
      • Role filtering (MCP-05 Dev vs Business; MCP-23 Dev vs Business code access)
      • Sensitivity handling (MCP-08 T3 redaction; MCP-04 column/row ACL)
  → result → Output Sanitizer (§22D Layer 3: PII redaction, truncation, reflection-injection block)
  → Response Synthesizer (LLM context)
```

### Read-only KB / Code Graph query (S02/S03 → MCP-01/02/03/04)

```
Skill (e.g., S02 KBRetriever / S03 CodeGraphQuery)
  → MCP-01 vector-search / MCP-02 graph-traverse / MCP-03 graph-query / MCP-04 pg-query
  → tenant_id auto-injected (MCP-03 WHERE node.tenant_id = $tenant_id)
  → column/row ACL rewritten at DB Proxy (MCP-04)
  → results → Output Sanitizer → LLM
```

### Notification / external write (MCP-14 / MCP-17)

```
Skill (e.g., S06 DocGenerator or Verified Path step)
  → MCP-14 notification-send (RBAC: same-tenant recipients; Critical needs elevated perm)
  → MCP-17 external-ticketing (Vault-injected external credential)
  → Gateway → MCP Pod → external system
  → result (SendResult / TicketResult / LinkResult) → audit logged
```

### BRD-pipeline MCP reference flow (MCP-20/21/22)

```
BRD/ADR lifecycle stage (brd-adr-lifecycle sub-project)
  → MCP-20 jira-sync: create_epic / link_to_epic / push_status (one-way; BRD = SoT)
  → MCP-21 confluence-export: export_to_page / export_to_notion / batch_export
  → MCP-22 compliance-mapper: map_brd_to_framework / validate_coverage / suggest_missing_controls
  → Gateway → MCP Pod → external system / compliance library
```
Full detail and ownership → [`brd-adr-lifecycle`](../brd-adr-lifecycle/) (§23.8.2).

### Shared runtime sequence

The end-to-end Agent query — including the Permission-Gated MCP tool calls (Code Graph via MCP-03, KB Vector via MCP-01, KB Relational via MCP-04, logs via MCP-05) and Output Guard — is documented in [`../_shared/sequence-diagrams.md`](../_shared/sequence-diagrams.md) **§21.3 AI Agent Query with Permission Gating**. That sequence is the canonical reference for MCP invocation at runtime and is co-owned with [`knowledge-services`](../knowledge-services/) (Code Graph, KB Vector/Relational) and [`platform-core`](../platform-core/) (Auth, Log Store).

## Design References

- **Original sections**: §22C (MCP Server Catalog — Core MCP Servers, MCP Deployment Architecture, MCP Gateway Key Behaviors) of [`docs/03-architecture.md`](../../03-architecture.md); §23.8.2 (New MCP Servers — MCP-20 jira-sync, MCP-21 confluence-export, MCP-22 compliance-mapper) for the BRD-pipeline reference entries.
- **Related agent-platform docs**: [`skill-catalog.md`](skill-catalog.md) (§22B — Skills that consume these MCP endpoints), [`dual-mode-orchestration.md`](dual-mode-orchestration.md) (§22A.1/§22A.2 Step 4 — Parallel Tool Executor that calls MCPs via the Gateway), [`agent-security.md`](agent-security.md) (§22D Layer 2 Permission Gate, Layer 3 Output Sanitizer, Layer 7 Sandbox network egress whitelist that enforces Gateway-only access).
- **Related sub-project docs**: [`brd-adr-lifecycle`](../brd-adr-lifecycle/) (§23.8.2 — full ownership of MCP-20/21/22), [`knowledge-services`](../knowledge-services/) (backends for MCP-01/02/03/23), [`platform-core`](../platform-core/) (DB Proxy/ACL for MCP-04, Log Store for MCP-05, Audit Trail, Incident Manager for MCP-09, Notification for MCP-14, Vault for MCP-17/20/21), [`workflow-engine`](../workflow-engine/) (MCP-06 git-diff, MCP-07 template-search, MCP-13 static-analysis).
- **Shared sequence diagram**: [`../_shared/sequence-diagrams.md`](../_shared/sequence-diagrams.md) §21.3 AI Agent Query with Permission Gating (primary sub-project).
- **ADRs** ([index](../../adr-index.md)): [ADR-0016 Dual-Mode Agent Orchestration](../../../adr/0016-dual-mode-agent-orchestration.md) (MCPs are the tool layer in both modes), [ADR-0024 KB Reasoning Support](../../../adr/0024-kb-reasoning-support-playbooks-code.md) (MCP-23 code-knowledge-search backs Code Knowledge), [ADR-0022 BRD Generation Agent Pipeline](../../../adr/0022-brd-generation-agent-pipeline.md) (MCP-20/21/22 BRD-pipeline MCPs).
- **Glossary** ([../../glossary.md](../../glossary.md)): MCP, MCP Gateway, Tool/Resource endpoint, tenant context, Circuit Breaker, Rate Limit.
- **Cross-references retained from source**: §22A (runtime caller), §22B (Skills consuming MCPs), §22D Layer 2/3/7 (gate, output sanitization, network egress whitelist), §7.2 (Python AST analysis exposed by MCP-13), §23.8.2 (BRD-pipeline MCPs detailed in brd-adr-lifecycle).
