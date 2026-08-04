# Key Sequence Diagrams (Cross-Sub-Project)

> **Origin**: §21 of [`docs/03-architecture.md`](../../../03-architecture.md)
> **Scope**: Three end-to-end sequences that span multiple sub-projects. Each is referenced from the relevant sub-project's "Key Flows" section.

These diagrams illustrate how the sub-projects collaborate at runtime. They are maintained here as a single shared reference to avoid duplication, because each sequence traverses 3+ sub-projects.

---

## 21.1 Freeze Flow: Full End-to-End

**Primary sub-project**: [workflow-engine](../workflow-engine/freeze-pipeline.md)
**Also involves**: [agent-platform](../agent-platform/) (Spec Refinement Assistant uses LLM), [knowledge-services](../knowledge-services/) (Code Graph for impact), [platform-core](../platform-core/) (Notification, Audit Trail)

```
Participants:
  USER        = Analyst/Developer in Workbench UI
  WB          = Workbench (React SPA)
  API         = API Gateway (Kong)
  FB          = Freeze Pipeline Service
  SRA         = Spec Refinement Assistant
  VE          = Validation Engine
  TR          = Test Runner (Sandbox)
  IR          = Impact Report Generator
  GIT         = Git Platform (GitHub/GitLab)
  REVIEWER    = Peer Reviewer / Business Approver
  RM          = Release Manager
  MON         = Monitoring (Prometheus + Alertmanager)
  NOTIF       = Notification Service

Flow:
  1.  USER     →  WB       :  Clicks "Freeze" on Workflow draft
  2.  WB       →  API      :  POST /freeze { workflow_id, artifact_id }
  3.  API      →  FB       :  Forward (JWT: user_id, tenant_id, role)
  4.  FB       →  FB       :  Validate: workflow.status == 'draft' AND
                               all fuzzy_nodes.user_confirmed == true
  5.  FB       →  SRA      :  gRPC: ScanFuzzyNodes(artifact)
  6.  SRA      →  SRA      :  Parse Design Artifact → identify fuzzy_nodes
                               → for each, generate 1-3 proposals with
                               confidence scores and trade-off explanations
  7.  SRA      →  FB       :  return: List<FuzzyNodeProposal> (grouped by risk)
  8.  FB       →  WB       :  PUSH (WebSocket): render proposals in Workbench
  9.  USER     →  WB       :  For each fuzzy node: (a) accept proposal, or
                               (b) edit & accept, or (c) provide custom resolution,
                               or (d) escalate to Data Owner
  10. WB       →  API      :  POST /freeze/resolve { resolutions: [...] }
  11. API      →  FB       :  Forward resolutions
  12. FB       →  FB       :  Record all resolutions (who, when, proposal,
                               edits) → Audit Trail; mark nodes confirmed
  13. FB       →  VE       :  gRPC: ValidateSpec(frozen_spec)
  14. VE       →  VE       :  Schema validation (YAML schema)
                               + DQ Gate: run pre-freeze quality checks
                               + Logic integrity: cycle detection, type checking,
                                 timeout validation, Python AST scan (§7.2),
                                 SQL AST scan (§7.3)
                               + Engine compatibility check (§6.1)
  15. VE       →  FB       :  return: ValidationReport { pass, warnings, errors }
  16. [IF FAIL] → WB       :  Render validation errors; loop back to step 9
  17. FB       →  TR       :  gRPC: RunTest(frozen_spec, sandbox_config={
                                engine: light, sample_pct: 5, timeout: 600s })
  18. TR       →  TR       :  Acquire Sandbox from warm pool (<100ms)
                               → Execute workflow with 5% sample data on Light Engine
                               → Capture: output snapshot, execution trace, row counts
  19. TR       →  FB       :  return: TestResult { passed, snapshot_ref, trace_id }
  20. [IF FAIL] → WB       :  Render test failure with diff; loop back to step 9
  21. FB       →  IR       :  gRPC: GenerateImpactReport(frozen_spec, base_branch)
  22. IR       →  IR       :  Compute diff (Spec vs base)
                               → Query Code Graph for upstream/downstream impact
                               → Simulate data impact (old logic vs new on historical data)
                               → Aggregate test results + approval requirements
  23. IR       →  FB       :  return: ImpactReport (Markdown + JSON)
  24. FB       →  GIT      :  HTTPS: Create PR on freeze/{workflow_id} branch
                               PR body = ImpactReport Markdown
  25. FB       →  WB       :  PUSH: PR link + Impact Report + review checklist
  26. FB       →  NOTIF    :  Kafka: events.freeze.pr_created { pr_url, reviewer_ids }
  27. NOTIF    →  REVIEWER :  Slack/Email: "Freeze PR ready for review"
  28. REVIEWER →  GIT      :  HTTPS: Review diff, approve PR (or request changes)
  29. [IF CHANGES REQUESTED] → loop back to Exploration Environment (user edits → step 1)
  30. GIT      →  FB       :  Webhook: PR approved + CI checks passed
  31. FB       →  RM       :  gRPC: StartCanary(workflow_id, version)
  32. RM       →  RM       :  Stage: CANARY_1% — §4.2 Canary Gating
                               → Deploy to 1% of scheduled runs
                               → Monitor for 2 cycles or 4h
  33. RM       →  MON      :  Query: gate criteria metrics (error rate, row count ±5%,
                               quality checks, schema drift)
  34. MON      →  RM       :  return: GatePassed { true/false, metric_values }
  35. [IF GATE FAIL] →     :  Auto-rollback: redeploy previous version;
                               create P2 incident; notify Business Approver;
                               return artifact to 'draft' status
  36. RM       →  RM       :  Stage: CANARY_10% (6 cycles / 24h) → same gate logic
  37. RM       →  RM       :  Stage: 50% (12 cycles / 72h) → same gate logic
  38. RM       →  RM       :  Stage: 100% cutover → mark workflow as 'active'
  39. RM       →  FB       :  return: DeployResult { success, canary_log }
  40. FB       →  NOTIF    :  Kafka: events.freeze.completed
  41. NOTIF    →  USER     :  "Workflow deployed successfully"
  42. FB       →  FB       :  Generate Post-Change Summary (§9.2):
                               Design vs Actual consistency check,
                               Updated Code Graph DAG, Cost & Performance Profile
  43. FB       →  GIT      :  HTTPS: Merge PR to main (squash merge)
  44. FB       →  WB       :  PUSH: Post-Change Summary + Deployment confirmation
```

---

## 21.2 Runtime Execution with Failure

**Primary sub-project**: [workflow-engine](../workflow-engine/) (Executor, Sandbox)
**Also involves**: [query-serving](../query-serving/) (Query Rewriter, Resilience Patterns), [knowledge-services](../knowledge-services/) (Code Graph, KB), [platform-core](../platform-core/) (Incident Manager, Notification)

```
Participants:
  SCHED     = Scheduler
  EXEC      = Workflow Executor (Production Environment)
  SANDBOX   = Sandbox Pool Manager
  DS        = Data Source (external, e.g., Snowflake)
  REWRITER  = Query Rewriter
  IM        = Incident Manager
  NOTIF     = Notification Service
  KB        = Knowledge Base (PostgreSQL)
  CG        = Code Graph (Neo4j)

Flow:
  1.  SCHED    →  SCHED    :  Cron trigger fires: "monthly_revenue_report" @ 06:00 UTC
  2.  SCHED    →  EXEC     :  gRPC: ExecuteWorkflow(workflow_id, trigger=cron,
                                params={}, trace_id)
  3.  EXEC     →  EXEC     :  Load frozen spec_yaml → parse DAG (jobs + depends_on)
                               → Topological sort → determine execution waves
  4.  EXEC     →  SANDBOX  :  gRPC: AcquireSandbox(tenant_id, workflow_id,
                                requirements={cpu:2, mem:4Gi, timeout:3600s})
  5.  SANDBOX  →  SANDBOX  :  Allocate from pre-warmed pool → assign ephemeral volume
  6.  SANDBOX  →  EXEC     :  return: SandboxLease { sandbox_id, /workspace/, /secrets/,
                                /input/, /output/, lease_timeout: 3600s }

  -- Wave 1: source jobs (no dependencies) --
  7.  EXEC     →  SANDBOX  :  gRPC: RunJob(job_id="source_revenue", type=source,
                                config={connector: snowflake, query: "SELECT ..."})
  8.  SANDBOX  →  REWRITER :  gRPC: RewriteQuery(original_sql, user_context={
                                tenant_id, role, permissions})
  9.  REWRITER →  REWRITER :  Inject: RLS predicate (tenant_id = $tenant_id) +
                                column masking (PII redaction)
  10. REWRITER →  SANDBOX  :  return: rewritten_sql, query_plan_fingerprint
  11. SANDBOX  →  DS       :  Execute rewritten_sql via Snowflake connector (TLS)
  12. DS       →  SANDBOX  :  ResultSet streamed to /output/source_revenue/ (Parquet)
  13. SANDBOX  →  EXEC     :  return: JobResult { status: SUCCESS, output_ref,
                                row_count: 1500000, duration_ms: 3200 }

  -- Wave 2: transform jobs (depend on source_revenue) --
  14. EXEC     →  SANDBOX  :  RunJob(job_id="transform_revenue", type=transform,
                                dependencies=[source_revenue])
  15. SANDBOX  →  SANDBOX  :  Mount /input/source_revenue → symlink to /output/source_revenue/
  16. SANDBOX  →  SANDBOX  :  Execute transform (SQL/Python) → write /output/transform_revenue/
  17. SANDBOX  →  EXEC     :  return: JobResult { status: SUCCESS, ... }

  18. EXEC     →  SANDBOX  :  RunJob(job_id="transform_forecast", type=transform,
                                dependencies=[transform_revenue])
  19. SANDBOX  →  SANDBOX  :  Execute Python transform: ML forecast using numpy/polars
  20. SANDBOX  →  EXEC     :  return: JobResult { status: SUCCESS, ... }

  -- FAILURE POINT --
  21. EXEC     →  SANDBOX  :  RunJob(job_id="join_crm", type=transform,
                                dependencies=[transform_forecast])
  22. SANDBOX  →  DS       :  Execute query against CRM data source
  23. DS       →  SANDBOX  :  ERROR: Connection timeout (CRM DB unresponsive)

  24. SANDBOX  →  EXEC     :  return: JobResult {
                                status: FAILED,
                                error: "ConnectionTimeout: CRM DB unresponsive after 30s",
                                attempt: 1/3
                              }

  25. EXEC     →  EXEC     :  Retry logic (§5.1): error is transient (network timeout)
                               → exponential backoff: wait 2s → retry
  26. EXEC     →  SANDBOX  :  RunJob(job_id="join_crm", attempt=2)

  27. SANDBOX  →  DS       :  Execute query against CRM data source
  28. DS       →  SANDBOX  :  ERROR: Connection timeout (CRM DB still unresponsive)
  29. SANDBOX  →  EXEC     :  return: JobResult { status: FAILED, attempt: 2/3 }

  30. EXEC     →  EXEC     :  wait 4s → retry final attempt
  31. EXEC     →  SANDBOX  :  RunJob(job_id="join_crm", attempt=3)
  32. DS       →  SANDBOX  :  ERROR: Connection timeout
  33. SANDBOX  →  EXEC     :  return: JobResult { status: FAILED, attempt: 3/3,
                                exhausted: true }

  34. EXEC     →  EXEC     :  Max retries exhausted → mark job as TERMINAL_FAILURE
                               → Propagate failure to dependent jobs:
                               all downstream jobs (output_render, email_distribute)
                               → set status: BLOCKED (dependency failed)

  35. EXEC     →  IM       :  gRPC: CreateIncident({
                                title: "Workflow 'monthly_revenue_report' failed: join_crm",
                                severity: P1_high,
                                source: workflow_failure,
                                context: { workflow_id, job_id, trace_id, error_stack,
                                          attempt_log, sandbox_id },
                                linked_workflow_id, linked_job_id
                              })
  36. IM       →  IM       :  Create incident record (§18.1 (incident entity))
                               → Calculate SLA deadline (P1 = 4h from now)
                               → Route to on-call: query user_session for admin role
  37. IM       →  NOTIF    :  Kafka: events.incident.created { incident_id, severity }
  38. NOTIF    →  USER     :  Slack + Email (Critical priority): "P1 Incident: monthly
                               revenue report failed at join_crm job. CRM DB unresponsive.
                               SLA: resolve within 4h. [View Incident #INC-042]"

  39. EXEC     →  CG       :  gRPC: UpdateNodeStatus(workflow_id,
                                status: FAILED, failed_job: join_crm)
  40. EXEC     →  KB       :  SQL: INSERT INTO audit_log (event_type='workflow.execute.failed',
                                ...)

  41. EXEC     →  SANDBOX  :  gRPC: ReleaseSandbox(sandbox_id)
  42. SANDBOX  →  SANDBOX  :  Quarantine /output/ (flag for review, not immediate delete)
                               → Destroy ephemeral volume after quarantine period (24h)
```

---

## 21.3 AI Agent Query with Permission Gating

**Primary sub-project**: [agent-platform](../agent-platform/) (Agent SDK, Permission Gating)
**Also involves**: [knowledge-services](../knowledge-services/) (Code Graph, KB Vector/Relational), [platform-core](../platform-core/) (Auth, Log Store)

```
Participants:
  USER      = Any authenticated user
  CONV      = Conversation Interface (Exploration Environment)
  AGENT     = AI Knowledge Agent (LLM SDK + Skill + MCP)
  AUTH      = Auth Service
  CG        = Code Graph Service (Neo4j, GraphQL)
  KB_VEC    = KB Vector Search (Milvus)
  KB_REL    = KB Relational (PostgreSQL)
  LOG       = Log Store (Elasticsearch)
  GUARD     = Output Guard (§3.2 Layer 4)
  CITATION  = Citation Builder

Flow:
  1.  USER     →  CONV     :  "What data sources feed the monthly revenue report,
                               and who owns the CRM data mapping?"

  2.  CONV     →  AGENT    :  Forward user query + session context {
                                user_id, tenant_id, role: analyst,
                                permissions: [viewer, analyst]
                              }

  3.  AGENT    →  AGENT    :  Intent Parsing: decompose into sub-questions
                               Q1: "data sources for monthly_revenue_report"
                               Q2: "owner of CRM data mapping"

  4.  AGENT    →  AUTH     :  gRPC: GetPermissionBoundary(user_id, tenant_id)
  5.  AUTH     →  AUTH     :  Lookup role + extra_permissions → compute
                               effective permission set:
                               { read: [workflow, job, data_source, kb_entry],
                                 domains: [business_glossary, data_catalog, mapping_registry],
                                 restrictions: { PII: redact, cross_tenant: deny } }
  6.  AUTH     →  AGENT    :  return: PermissionBoundary

  -- Q1: Query Code Graph for workflow data sources --
  7.  AGENT    →  CG       :  GraphQL (with RBAC filter):
                               query {
                                 workflow(id: "monthly_revenue_report") {
                                   jobs(type: "source") {
                                     name
                                     dataSource { name, type, schema_catalog }
                                   }
                                 }
                               }
                               headers: { X-Tenant-ID, X-User-ID, X-Role }
  8.  CG       →  CG       :  RBAC Filter (§2.1) applied:
                               - Row-level: WHERE tenant_id = $caller_tenant
                               - Column-level: strip PII columns from schema_catalog
                               - Edge-level: deny cross-tenant edges
  9.  CG       →  AGENT    :  return: {
                                workflow: {
                                  jobs: [
                                    { name: "source_revenue",
                                      dataSource: { name: "Snowflake_ERP_Prod",
                                                    type: "snowflake",
                                                    schema_catalog: { tables: [...],
                                                      columns: [{name:"revenue", type:"DECIMAL"},
                                                                {name:"cust_name", type:"VARCHAR", tier:"T3"}]
                                                      // T3 column 'cust_name' REDACTED by RBAC filter
                                                    }
                                                  }
                                    },
                                    { name: "source_crm",
                                      dataSource: { name: "CRM_Salesforce",
                                                    type: "api_rest" }
                                    }
                                  ]
                                }
                              }

  -- Q2: Query KB for CRM mapping owner --
  10. AGENT    →  KB_VEC   :  gRPC: HybridSearch(
                                query: "CRM data mapping owner contact",
                                tenant_id, top_k: 5,
                                domain_filter: [mapping_registry, data_catalog]
                              )
  11. KB_VEC   →  AGENT    :  return: [ { kb_entry_id: "kb_042", score: 0.92,
                                          title: "CRM↔ERP Customer Mapping",
                                          domain: mapping_registry, ... }, ... ]

  12. AGENT    →  KB_REL   :  SQL (via parameterized query):
                               SELECT id, title, metadata, confirmed_by
                               FROM kb_entry
                               WHERE id = 'kb_042' AND tenant_id = $1
  13. KB_REL   →  AGENT    :  return: { id: "kb_042",
                                metadata: {
                                  owner: "Jane Smith (Data Owner)",
                                  contact: "jane.smith@company.com",
                                  last_reviewed: "2026-06-15"
                                },
                                confirmed_by: "user:jane"
                              }

  -- Optional: query Log Store for recent CRM-related incidents --
  14. AGENT    →  LOG      :  ES Query (with tenant filter):
                               { query: { bool: { must: [
                                 { term: { event_type: "incident.created" } },
                                 { match: { "context": "CRM" } },
                                 { range: { event_ts: { gte: "now-30d" } } }
                               ] } } }
  15. LOG      →  AGENT    :  return: [ { incident: "INC-038", title: "CRM API timeout",
                                severity: "P2", resolved_at: "2026-06-20" } ]

  -- Fusion & Synthesis --
  16. AGENT    →  AGENT    :  Fuse results from CG + KB_VEC + KB_REL + LOG:
                               Build structured answer:
                               - Data sources: Snowflake_ERP_Prod, CRM_Salesforce
                               - CRM mapping owner: Jane Smith (jane.smith@company.com)
                               - Recent CRM incident: INC-038 (resolved Jun 20)

  -- Permission Boundary Check on Output --
  17. AGENT    →  AGENT    :  For each fact in answer, verify against PermissionBoundary:
                               - Can user see data source names? → Yes (T1 Internal)
                               - Can user see owner contact? → Yes (T1 Internal)
                               - Can user see incident details? → Yes (own tenant)
                               - Any T3 data exposed? → No (cust_name already redacted in step 9)
                               - Any cross-tenant references? → No

  18. AGENT    →  GUARD    :  Pass draft answer through Output Guard (§3.2 Layer 4):
                               - Scan for system prompt leakage → None detected
                               - Scan for instruction-following language → None detected
                               - Scan for executable code → None detected
  19. GUARD    →  AGENT    :  return: GuardResult { pass: true }

  -- Citation Building --
  20. AGENT    →  CITATION :  Build citations for each claim:
                               Claim 1: "Monthly revenue report uses Snowflake_ERP_Prod as source"
                                 → Citation: "Code Graph: workflow monthly_revenue_report,
                                    job source_revenue [verified at runtime]"
                               Claim 2: "CRM mapping owned by Jane Smith"
                                 → Citation: "KB Entry kb_042: CRM↔ERP Customer Mapping,
                                    confirmed by user:jane on 2026-06-15"

  21. AGENT    →  CONV     :  return: StructuredAnswer {
                                summary: "The monthly revenue report pulls from 2 sources...
                                         The CRM mapping is owned by Jane Smith...",
                                facts: [...],
                                citations: [ { claim_id, source_type, source_ref, verified_at } ],
                                confidence: 0.94,
                                caveats: ["CRM data source has had 1 recent incident (INC-038),
                                          now resolved — verify if data was affected"]
                              }

  22. CONV     →  USER     :  Render answer in Conversation UI:
                               - Summary text with inline citation markers [1], [2]
                               - Expandable citation panel
                               - Caveats highlighted in amber warning box
                               - [👍 Accurate] [👎 Inaccurate] [📋 Copy] feedback buttons

  23. CONV     →  LOG      :  Log LLM Interaction (§8 Layer 3):
                               { prompt_hash, kb_retrieved: [kb_042, ...],
                                 tokens: {in: 1240, out: 380}, cost: $0.0042,
                                 latency_ms: 8200, guard_triggered: false,
                                 user_feedback: null }
```
