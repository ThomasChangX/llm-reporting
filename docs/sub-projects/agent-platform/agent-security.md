# Agent Security — 7-Layer Anti-Exploitation Defense

> **Origin**: §22D of [`docs/03-architecture.md`](../../03-architecture.md) | **Sub-project**: [agent-platform](README.md)

## Purpose

This module covers the **Agent Security Architecture — 7-Layer Anti-Exploitation Defense** (§22D).

The core security challenge of AI Agents: Agents have the authority to invoke tools, access data, and generate content — making them high-value attack targets. The attack surface includes: **Prompt Injection** (making the Agent execute unintended tool calls), **Data Exfiltration** (bypassing permissions to access data through the Agent), **Instruction Injection** (making the Agent output malicious instructions to users), **Denial of Wallet** (infinite loops consuming LLM budget).

The following seven-layer defense system interconnects from input to output, from invocation to response. **Each layer is a necessary condition; no single layer alone provides sufficient protection.**

This module owns all 7 layers plus supply-chain security:
- **Layer 1: Input Sanitization & Prompt Injection Defense** — the Agent's "immune system first line of defense" (inherits and strengthens §3.2's pipeline).
- **Layer 2: Tool-Call Permission Gating** — the most critical boundary; four-dimensional pre-execution check (Role / Tenant / Resource / Parameter).
- **Layer 3: Tool Output Sanitization** — PII redaction, truncation, schema validation, reflection-injection detection.
- **Layer 4: Response Guard (Output)** — data-leakage / prompt-leakage / instruction-injection / confidence scans.
- **Layer 5: Agent Action Authorization (Tiered)** — the five-tier action system (L0 Read → L1 Suggest → L2 Draft → L3 Execute → L4 Admin).
- **Layer 6: Audit & Monitoring** — immutable interaction log, guard trigger log, audit retention, real-time anomaly detection.
- **Layer 7: Sandbox Isolation (Execution Boundary)** — network egress whitelist, filesystem isolation, mem/CPU/timeout/concurrency limits, process and container isolation.
- **Supply Chain Security** — SLSA v1.0 + OpenSSF Scorecard practices, plus LLM-specific supply-chain risks.

## Boundaries

**In-scope:**
- §22D overview — the four attack classes (Prompt Injection, Data Exfiltration, Instruction Injection, Denial of Wallet) and the "each layer is a necessary condition" principle.
- §22D Layer 1 — Structured Input Wrapping, System Prompt Immutability (SHA-256), Injection Pattern Detection (regex + classifier), Input Length Limit, Unicode Normalization, Nested Delimiter Detection.
- §22D Layer 2 — the per-tool-call Permission Gate, its four checks (Role / Tenant / Resource ACL / Parameter Anomaly), the worked example, and the Decision Matrix; **rejection occurs before execution (Pre-Execution Deny)**.
- §22D Layer 3 — PII/Sensitive Data Redaction, Output Truncation, Schema Validation, Reflection Injection Detection.
- §22D Layer 4 — Data Leakage Scan, Prompt Leakage Scan, Instruction Injection Scan, Confidence Check.
- §22D Layer 5 — the five-tier action system (L0–L4) and the Action Authorization Flow.
- §22D Layer 6 — Interaction Log, Guard Trigger Log, Audit Retention (Hot/Warm/Cold), and the six Real-Time Anomaly Detection Rules.
- §22D Layer 7 — Network Egress Whitelist, Filesystem Isolation, Memory/CPU/Timeout/Concurrency limits, Process Isolation, Container-Level Isolation.
- §22D Supply Chain Security — SLSA Level 3 requirements (Source Integrity, Build Provenance, Artifact Signing, SBOM, CVE Scanning, MCP/Skill Verification, Hermetic Builds) and LLM-specific risks (Model Provenance, Prompt Template Integrity, Vector DB Integrity).

**Delegated / out-of-scope:**
- The §3.2 input-side guard pipeline that Layer 1 inherits and strengthens → [`exploration-runtime.md`](exploration-runtime.md) (§3.2).
- The runtime steps that host Layers 2/3/4 (Permission Gate = Step 3, Output Sanitizer = Step 5, Response Guard = Step 7) → [`dual-mode-orchestration.md`](dual-mode-orchestration.md) (§22A.1 / §22A.2).
- The MCP endpoints gated by Layer 2 and sanitized by Layer 3 → [`mcp-catalog.md`](mcp-catalog.md) (§22C).
- RBAC/entitlement policy source (column/row ACL, role→tool mapping) and the Audit Trail sink → [`platform-core`](../platform-core/).
- The Sandbox execution internals beyond the isolation envelope (Python AST, SQL AST, resource limits inside a Job) → [`workflow-engine` `execution-sandbox.md`](../workflow-engine/execution-sandbox.md) (§7).
- KB embeddings integrity watermark cross-check → [`knowledge-services`](../knowledge-services/) (§10.1).

**Upstream/downstream neighbors:**
- *Input*: user natural language (entering Layer 1); LLM tool-call decisions (entering Layer 2); raw tool results (entering Layer 3); synthesized responses (entering Layer 4); proposed actions (entering Layer 5).
- *Output*: sanitized/guarded responses to the user; SECURITY-level events to the Audit Trail; Incidents to the Incident Manager; telemetry to real-time anomaly detection.

## Interfaces

### §22D Seven-Layer Agent Defense Architecture (overview)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    SEVEN-LAYER AGENT DEFENSE ARCHITECTURE                     │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │ LAYER 1: INPUT SANITIZATION & PROMPT INJECTION DEFENSE              │     │
│  │ • Delimited blocks, immutable system prompt, injection pattern scan │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │ LAYER 2: TOOL-CALL PERMISSION GATING  ◄── THE CRITICAL BOUNDARY     │     │
│  │ • 4-dimension check (Role/Tenant/Resource/Parameter) per tool-call  │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │ LAYER 3: TOOL OUTPUT SANITIZATION                                   │     │
│  │ • PII redaction, truncation, reflective injection detection        │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │ LAYER 4: RESPONSE GUARD (OUTPUT)                                    │     │
│  │ • Data leakage scan, prompt leakage scan, instruction injection scan│     │
│  └─────────────────────────────────────────────────────────────────────┘     │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │ LAYER 5: AGENT ACTION AUTHORIZATION (TIERED)                        │     │
│  │ • Read(auto)→Suggest(auto)→Draft(confirm)→Execute(confirm)→Admin(MFA)│     │
│  └─────────────────────────────────────────────────────────────────────┘     │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │ LAYER 6: AUDIT & MONITORING (EVERYTHING LOGGED)                     │     │
│  │ • Full interaction log, anomaly detection, real-time alerting      │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │ LAYER 7: SANDBOX ISOLATION (EXECUTION BOUNDARY)                     │     │
│  │ • Network allowlist, no FS access, mem limit, timeout, concur limit │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Layer 1: Input Sanitization & Prompt Injection Defense

> Inherits and strengthens §3.2's defense pipeline. This layer is the Agent's "immune system first line of defense."

| Mechanism | Implementation | Block Level |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------ |
| **Structured Input Wrapping** | All user input is wrapped in `<user_input>` XML tag blocks; system instructions are in a separate, SHA-256 hash-verified `<system_instruction>` block. The LLM is trained/prompted to treat `<user_input>` content as data, never as instructions. | Architectural (cannot bypass) |
| **System Prompt Immutability** | The Agent's system prompt is stored in Git, loaded at startup, and SHA-256 computed. Hash is verified before every LLM call. Hash mismatch → Agent refuses service + security alert. | Hard block |
| **Injection Pattern Detection** | Two-layer detection: (a) **Regex Engine**: detects known patterns like "ignore previous instructions", "you are now DAN", "pretend you are", "as a developer", "system prompt:", "forget all", "new instructions:", "you must", "roleplay as"; (b) **Classifier Model** (small model, <50ms): detects role-playing language, instruction-following language, boundary-breaking attempts. Either hit → input rejected, generic error returned (does not reveal specific detection rules). | Hard block |
| **Input Length Limit** | Single user message max 32KB. Exceeding → truncated with user notification. Attachments/files via dedicated upload endpoints (not inlined in Prompts). | Hard block |
| **Unicode Normalization** | NFC normalization + strip control characters (except `\n`, `\t`, `\r`) + detect homoglyph attacks (e.g., Cyrillic 'а' substituting Latin 'a'). | Hard block |
| **Nested Delimiter Detection** | Detect whether user input contains `</user_input>` closing tags (attempts to prematurely close user input block). Found → reject input. | Hard block |

### Layer 2: Tool-Call Permission Gating (Most Critical Security Boundary)

> **This is the most important boundary in the Agent security architecture.** After the LLM decides to invoke a tool, before the tool actually executes, the Permission Gate performs a four-dimensional check. **Rejection occurs before execution (Pre-Execution Deny)**, not as post-hoc audit.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PERMISSION GATE (per tool-call)                   │
│                                                                      │
│  Tool Call Request (from LLM):                                       │
│  { tool: "MCP-04.sql", params: { query: "SELECT name, salary        │
│    FROM employees WHERE dept = $1", params: ["Engineering"] } }     │
│                                                                      │
│                         │                                            │
│                         ▼                                            │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ CHECK 1: ROLE CHECK                                           │  │
│  │ Does the user's role permit calling this tool?                     │  │
│  │ • Dev role → can call MCP-03 (code_graph), MCP-05 (logs)      │  │
│  │ • Dev role → CANNOT call MCP-04 (pg-query) on business tables │  │
│  │ • Business User → CANNOT call MCP-06 (git-diff)               │  │
│  │ Result: ✅ User is Business User, role allows pg-query on      │  │
│  │         sample data with masking                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                         │                                            │
│                         ▼                                            │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ CHECK 2: TENANT CHECK                                          │  │
│  │ Does the target resource belong to user's tenant?              │  │
│  │ • Every MCP server extracts tenant_id from request metadata    │  │
│  │ • Query-level enforcement: WHERE tenant_id = $injected_tenant  │  │
│  │ • Cross-tenant access requires explicit opt-in (recorded)      │  │
│  │ Result: ✅ Query targets tenant's own data                     │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                         │                                            │
│                         ▼                                            │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ CHECK 3: RESOURCE-LEVEL CHECK (Column/Row ACL)                 │  │
│  │ • Is query accessing columns user has permission to see?       │  │
│  │ • Column "salary" is T3 (Restricted) → masked or denied        │  │
│  │ • Row-level: only rows where department = user's dept          │  │
│  │ Result: ⚠️ Column "salary" is T3 → query rewritten to redact  │  │
│  │         (Query Rewriter injects: SELECT name, '***' AS salary) │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                         │                                            │
│                         ▼                                            │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ CHECK 4: PARAMETER ANOMALY DETECTION                           │  │
│  │ • Are parameters reasonable?                                   │  │
│  │ • Pattern check: unusually broad query? (no WHERE clause)      │  │
│  │ • Pattern check: parameter contains injection patterns?        │  │
│  │ • Pattern check: query returns too many columns/rows?           │  │
│  │ Result: ✅ Query has WHERE clause, params are safe              │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                         │                                            │
│                         ▼                                            │
│  ✅ PERMIT (with salary column masked)                               │
│  OR                                                                  │
│  ❌ DENY → Audit Log Entry (SECURITY level) + Alert                  │
└─────────────────────────────────────────────────────────────────────┘
```

**Permission Gate Decision Matrix**:

| Check Dimension        | Check Dimension                                      | Failure Behavior                                                               |
| --------------------- | ---------------------------------------------------- | ------------------------------------------------------------------------------ |
| **Role Check**        | Session Context (user_id → roles → permitted_tools) | DENY + `role_violation` log + do not reveal specific denial reason to user (only "This operation is not permitted") |
| **Tenant Check**      | Session Context (tenant_id) + MCP-side auto-injection | DENY + `cross_tenant_attempt` log + security alert (possible attack)           |
| **Resource ACL**      | Entitlement Service (column-level/row-level policy)  | DENY (hard violation) or REWRITE (maskable) — T3 columns masked as REDACT, T2 columns masked as HASH |
| **Parameter Anomaly** | Rule engine + ML anomaly detection model             | DENY or FLAG — overly broad queries rejected; minor anomalies flagged but allowed (recorded in audit log) |

### Layer 3: Tool Output Sanitization

> Tool-returned data must be sanitized before entering the LLM reasoning context. Prevents: (a) sensitive data leakage to the LLM (especially critical when LLM is a SaaS model), (b) reflection injection (malicious data inducing the LLM to perform unexpected operations).

| Mechanism                         | Implementation                                                                                                                                                                                                                                                                                                                                                      |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **PII/Sensitive Data Redaction**  | Based on `permitted_columns` and `column_sensitivity_map` in Session Context, redact all T2/T3 column data: T3 → replace with `[RESTRICTED]`; T2 → replace with `SHA256_first8(data)`. Redaction is completed before tool output enters LLM context; irreversible.                                                                                                   |
| **Output Truncation**             | Single tool output > 100KB → truncate to first 20KB + summary (summary generated by small model: "This dataset contains 15,432 rows, key statistics: ..."). Very large result sets (>1M rows) → return only schema + row count + 10 sample rows + statistical summary.                                                                                                |
| **Schema Validation**             | Verify that tool output structure matches expected Schema. Mismatch → tool call marked as failed, output not fed into LLM (prevent LLM from being confused by malformed data).                                                                                                                                                                                       |
| **Reflection Injection Detection**| Scan tool output for: (a) Prompt injection patterns ("ignore previous", "you are now"...), (b) Directive language ("you should", "you must", "tell the user to"...), (c) Code blocks containing `eval`/`exec`/`__import__`. Hit → the output fragment is removed, replaced with `[FILTERED: potential injection detected]`, event logged at SECURITY level. |

### Layer 4: Response Guard (Output)

> After Agent reasoning completes and before the final response is sent to the user, a three-layer scan is performed:

| Scan Type               | Detection Content                                                                                                                                                                                                                           | Hit Behavior                                                                                       |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| **Data Leakage Scan** | Does the response contain data from tool calls that the user is not authorized to view? Compare: values/entities appearing in the response vs. restricted columns in the user's permission matrix. Uses fuzzy matching (allowing format variations and restatements) and exact matching. | Hard block: response withheld, replaced with "This response contains data you are not authorized to access and has been filtered. Please narrow your query." + security log |
| **Prompt Leakage Scan** | Does the response contain system Prompt fragments? (Detected via N-gram overlap detection, comparing against known system Prompt content) | Hard block: response withheld + security alert (possible Prompt extraction attack) |
| **Instruction Injection Scan** | Is the response attempting to guide the user toward executing dangerous operations? Detect patterns: "you should run", "execute this command", "disable the firewall", "grant admin access", etc. Combined with user role context (Admin receiving "grant access" suggestion may be normal; Viewer receiving it is anomalous). | Hard block or soft warning (depending on severity) |
| **Confidence Check** | Each claim in the response with confidence < 0.7 → prepend `[Confidence: {score}]` marker before the claim; overall response average confidence < 0.6 → prepend `⚠️ The following response has low confidence, manual verification recommended.` at the top. | Soft marking (does not block, but transparently informs user) |

### Layer 5: Agent Action Authorization (Tiered)

> The Agent may **suggest** actions, but execution requires different levels of authorization. Five-tier action system:

| Level           | Name    | Example Actions                                                            | Authorization Requirement                                       | Implementation                                 |
| --------------- | ------- | ------------------------------------------------------------------------- | --------------------------------------------------------------- | ---------------------------------------------- |
| **L0: Read**    | Read    | Query KB, query Code Graph, query logs, query data Profile                | Auto-execute (Session Context permissions already cover)        | No additional confirmation                     |
| **L1: Suggest** | Suggest | Suggest DQ rules, suggest Workflow templates, suggest KB entries, suggest Impact Report | Auto-execute (marked as "AI Suggestion")                        | Output carries `suggestion` tag                |
| **L2: Draft**   | Draft   | Create Spec draft, create KB entry draft, create Adjustment draft         | Auto-execute (write as draft status, no production impact)      | Write `status: draft`; user must Confirm to publish |
| **L3: Execute** | Execute | Finalize Workflow, trigger production execution, publish KB entry, create Ticket, send notification | **Explicit user confirmation** (UI button / API confirm param)  | Confirmation recorded in Audit Trail           |
| **L4: Admin**   | Admin   | Modify tenant config, modify permissions, delete KB entry, modify Model policy, rollback Workflow | **Explicit confirmation + MFA (Multi-Factor Authentication)**   | Requires TOTP/WebAuthn verification in addition to confirmation |

**Action Authorization Flow**:
```
Agent suggests action → Action Router classifies tier →
  L0/L1 → auto-execute, response includes action result
  L2    → auto-execute as draft, response includes "Draft created: [link]. Click to review and confirm."
  L3    → response includes "Proposed action: [description]. [Confirm] [Dismiss]"
           User must click Confirm → Action executed → Audit logged
  L4    → response includes "Proposed action: [description]. MFA required. [Confirm with MFA] [Dismiss]"
           User must complete MFA → Action executed → Audit logged
```

### Layer 6: Audit & Monitoring

> The complete lifecycle of every Agent interaction is recorded in an immutable audit log. Abnormal behavior patterns are monitored in real time.

| Audit Dimension              | Recorded Content                                                                                                                                                                                                                                                                                                                                                                                                                |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Interaction Log**          | `{ session_id, timestamp, user_id, tenant_id, query_text, intent, routed_skill, all_tool_calls: [{ tool, params_hash, params_summary, result_summary, latency_ms, permission_gate: { checks_passed, checks_failed } }], final_response_hash, response_guard: { leakage_hits, prompt_leak_hits, injection_hits }, confidence_scores, tokens: { input, output, total }, cost: { estimated_usd }, model_used, latency_total_ms }` |
| **Guard Trigger Log**        | Any Guard layer trigger event (injection detection, permission denial, redaction operation, output interception) → independent log stream, SECURITY level                                                                                                                                                                                                                                                                        |
| **Audit Retention**          | Hot 30 days (ES) → Warm 1 year (S3+Parquet) → Cold 7 years (Glacier, compliance retention). Tenants can request export of their own audit logs (machine-readable JSON).                                                                                                                                                                                                                                                          |

**Real-Time Anomaly Detection Rules**:

| Rule                              | Condition                                                                    | Action                                                                                          |
| --------------------------------- | ---------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| **Permission Denial Storm**       | Same user/tenant ≥5 Permission Gate DENY events within 1 minute              | Agent session throttled (503) + SECURITY Incident auto-created + notify Security Admin          |
| **Abnormal Tool Calls**           | Single query tool calls > 20 (exceeds budget)                                | Agent session terminated + WARNING log                                                          |
| **Cross-Tenant Access Attempt**   | Any Tenant Check failure                                                     | Immediate SECURITY Incident + notify both tenant Admins                                         |
| **Abnormal Time Pattern**         | Large volume of Agent queries during 2-5 AM (outside normal working hours)   | Elevate Guard sensitivity for that session + INFO log                                           |
| **Abnormal Token Consumption**    | Single query consumption > 50K tokens                                        | FLAG + notify tenant Admin (possible DoW attack — Denial of Wallet)                             |
| **Pattern Probing**               | Same user sends structurally similar incremental queries in short time (probing Guard boundaries) | User session throttled + SECURITY Incident                                                      |

### Layer 7: Sandbox Isolation (Execution Boundary)

> Agent Runtime executes in a dedicated sandbox, physically isolated from the rest of the system.

| Isolation Dimension               | Implementation                                                                                                                                                                                                                                              |
| --------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Network Egress Whitelist**      | Agent Runtime may only access registered MCP endpoints (via MCP Gateway). Any other network requests (external internet, direct internal service connections) are blocked at the iptables/NetworkPolicy layer. DNS resolution restricted to internal DNS only. |
| **Filesystem Isolation**          | Agent Runtime may only write to `/workspace/` (temporary tool output cache, max 500MB, cleared after session ends). No access to system files, Git repos, secret stores. `/workspace/` mounted with `noexec`.                                               |
| **Memory Limit**                  | Per Agent instance: 4GB RAM (cgroup hard limit). Exceeded → OOM Kill → session terminated + Incident.                                                                                                                                                       |
| **CPU Limit**                     | Per Agent instance: 2 vCPU (cgroup `cpu.max`). Prevents a single query from consuming all compute resources.                                                                                                                                                 |
| **Timeout**                       | Single Agent query max 5 minutes (`loop_timeout_seconds`). Timeout → SIGKILL → partial results returned (if any) + timeout notification.                                                                                                                     |
| **Concurrency Limit**             | Per tenant per user max 3 concurrent Agent sessions. Exceeded → queued (max 30s) or 429 Too Many Requests.                                                                                                                                                   |
| **Process Isolation**             | Agent Runtime runs as non-root user (UID 10000+), no `CAP_SYS_ADMIN`, seccomp profile allows only ~50 safe syscalls.                                                                                                                                        |
| **Container-Level Isolation**     | Each tenant's Agent Runtime runs in an independent Kubernetes Namespace; L3 (Finance/Government) tenants run in a dedicated Node Group.                                                                                                                      |

### Supply Chain Security

> Based on [SLSA (Supply-chain Levels for Software Artifacts) v1.0](https://slsa.dev/) and [OpenSSF Scorecard](https://securityscorecards.dev/) best practices.

| SLSA Requirement            | Implementation                                                                                                                                                                 | Target Level          |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------- |
| **Source Integrity**        | Git signed commits (SSH/GPG); branch protection rules; 2FA required for all committers                                                                                         | SLSA Level 3          |
| **Build Provenance**        | Build pipeline generates in-toto attestations; provenance published to Sigstore transparency log (Rekor)                                                                       | SLSA Level 3          |
| **Artifact Signing**        | All deployable artifacts signed via Cosign (keyless, OIDC-based); container images signed + attested                                                                           | SLSA Level 3          |
| **SBOM Generation**         | CycloneDX SBOM generated at build time for all services (Python: `pip-audit` + `cyclonedx-py`; Container: Syft); SBOM ingested into Dependency-Track for continuous monitoring | SLSA Level 3          |
| **Dependency CVE Scanning** | Daily CVE scan via Trivy (containers) + Safety (Python); Critical CVEs block deploy; High CVEs require waiver                                                                  | SLSA Level 3          |
| **MCP/Skill Verification**  | All MCP Servers and Skills distributed with Sigstore-signed manifests; Agent Runtime verifies signature before loading                                                         | SLSA Level 3          |
| **Hermetic Builds**         | All builds run in isolated, ephemeral environments; no network access except to declared dependencies (vendored or proxy)                                                      | SLSA Level 3 (target) |

**LLM-Specific Supply Chain Risks** (aligned with OWASP LLM05 assessment in `docs/security/threat-model.md`):
- **Model Provenance**: Model weights and tokenizers stored with SHA-256 hash verification; registry records model source, version, and training date
- **Prompt Template Integrity**: System prompts and Skill templates version-controlled in Git with signed commits; Agent Runtime verifies template hash before injection
- **Vector DB Integrity**: KB embeddings validated against PG source data via version watermark cross-check (see §10.1)

## Dependencies

- **Exploration runtime** ([`exploration-runtime.md`](exploration-runtime.md), §3.2) — Layer 1 inherits and strengthens the §3.2 six-layer input-side pipeline.
- **Dual-mode orchestration** ([`dual-mode-orchestration.md`](dual-mode-orchestration.md), §22A.1/§22A.2) — hosts Layers 2/3/4 as runtime Steps 3/5/7; Layer 5 (Action Authorization) routes through the Action Router; Layer 7 Sandbox hosts the entire runtime.
- **MCP catalog** ([`mcp-catalog.md`](mcp-catalog.md), §22C) — Layer 2 gates the tool calls; Layer 3 sanitizes the tool results; Layer 7 Network Egress Whitelist permits only the MCP Gateway.
- **Platform core** ([`platform-core`](../platform-core/)) — Entitlement Service (column/row ACL for Layer 2 Check 3); Audit Trail (Layer 6 Interaction/Guard logs); Incident Manager (Layer 6 anomaly-rule escalation); Auth/MFA for Layer 5 L4; Vault for supply-chain signing keys.
- **Workflow engine** ([`workflow-engine` `execution-sandbox.md`](../workflow-engine/execution-sandbox.md), §7) — the inner Sandbox (Python AST / SQL AST / resource limits inside a Job) that complements the Layer 7 outer Sandbox.
- **Knowledge services** ([`knowledge-services`](../knowledge-services/)) — KB embeddings integrity watermark cross-check (LLM-specific supply chain risk, §10.1).
- **Build/release infrastructure** — Sigstore/Rekor, Cosign, CycloneDX/Syft, Dependency-Track, Trivy/Safety, in-toto attestations (Supply Chain Security).

## Data Model

- **Session Context (immutable)** — `{ tenant_id, user_id, role, permissions, caps }`, includes `permitted_columns` and `column_sensitivity_map` consumed by Layer 3 redaction (§22A.1, Layer 3).
- **Permission Gate decision record** — `PERMIT` (possibly with masking rewrite) or `DENY { reason, evidence }`; on DENY an Audit Log Entry at SECURITY level (Layer 2 Decision Matrix).
- **Query Rewriter output** — e.g., `SELECT name, '***' AS salary` (T3 redaction at Layer 2 Check 3).
- **Layer 6 Interaction Log entry** — `{ session_id, timestamp, user_id, tenant_id, query_text, intent, routed_skill, all_tool_calls: [{ tool, params_hash, params_summary, result_summary, latency_ms, permission_gate: { checks_passed, checks_failed } }], final_response_hash, response_guard: { leakage_hits, prompt_leak_hits, injection_hits }, confidence_scores, tokens: { input, output, total }, cost: { estimated_usd }, model_used, latency_total_ms }`.
- **Layer 6 Guard Trigger Log** — any Guard trigger (injection detection, permission denial, redaction, output interception) at SECURITY level.
- **Audit Retention tiers** — Hot 30 days (ES) → Warm 1 year (S3 + Parquet) → Cold 7 years (Glacier); tenant-exportable as machine-readable JSON.
- **Layer 5 tiering** — L0 Read / L1 Suggest (`suggestion` tag) / L2 Draft (`status: draft`) / L3 Execute (Audit-logged confirm) / L4 Admin (TOTP/WebAuthn + confirm).
- **Supply-chain artifacts** — signed commits (SSH/GPG), in-toto attestations, Sigstore/Rekor provenance, Cosign-signed images, CycloneDX SBOMs (Dependency-Track), Trivy/Safety CVE reports, Sigstore-signed MCP/Skill manifests.

## Failure Modes & Recovery

| Failure | Impact | Detection | Recovery |
| ------- | ------ | --------- | -------- |
| **Prompt injection attempt** | Agent executes unintended tool calls | Layer 1 (Structured Input Wrapping, Injection Pattern Detection regex + classifier, Nested Delimiter Detection) | Hard block — generic error returned (rules not revealed); security alert; logged |
| **System prompt tampering** | Immutable system prompt altered | Layer 1 SHA-256 hash mismatch before every LLM call | Agent refuses service + security alert |
| **Homoglyph / Unicode / control-char attack** | Encoding-based bypass | Layer 1 Unicode Normalization (NFC, control-char strip, homoglyph detection) | Hard block — input rejected |
| **Unauthorized tool call (role/tenant/resource/param)** | Unauthorized data access or action | Layer 2 four-dimensional check, **Pre-Execution Deny** | `DENY { reason, evidence }` + SECURITY-level audit + alert; do not reveal specific reason to user |
| **PII leakage into LLM context (esp. SaaS model)** | Sensitive data sent to external LLM | Layer 3 PII/Sensitive Data Redaction (T3 → `[RESTRICTED]`, T2 → `SHA256_first8`) | Irreversible redaction before LLM context |
| **Reflection injection via tool output** | Malicious data steers LLM | Layer 3 Reflection Injection Detection (injection patterns, directive language, `eval`/`exec`/`__import__`) | Hard block — fragment replaced with `[FILTERED: potential injection detected]`; SECURITY-level log |
| **Data leakage in final response** | Restricted data exfiltrated to user | Layer 4 Data Leakage Scan (fuzzy + exact match vs. permission matrix) | Hard block — response withheld + filtering notice + security log |
| **System prompt leakage in response** | Prompt extraction attack | Layer 4 Prompt Leakage Scan (N-gram overlap) | Hard block — response withheld + security alert |
| **Instruction injection in response** | User guided to dangerous operations | Layer 4 Instruction Injection Scan (role-context aware) | Hard block or soft warning by severity |
| **Unauthorized action execution** | State mutation without authorization | Layer 5 tiering — L3 requires explicit confirm, L4 requires MFA | Action withheld pending confirmation/MFA; confirmation recorded in Audit Trail |
| **Permission denial storm / probing** | Brute-force boundary probing | Layer 6 anomaly rules (≥5 DENY/min; structurally similar incremental queries) | Session throttled (503) + SECURITY Incident + notify Security Admin |
| **DoW (Denial of Wallet)** | LLM budget exhaustion | Layer 6 (>50K tokens/query) + Layer 7 caps; Layer 1/§22A.3 loop limits | FLAG + notify tenant Admin; session terminated if > 20 tool calls |
| **Cross-tenant access attempt** | Tenant boundary breach | Layer 2 Tenant Check + Layer 6 anomaly rule | Immediate SECURITY Incident + notify both tenant Admins |
| **Sandbox escape attempt** | Agent reaches non-MCP network/FS | Layer 7 iptables/NetworkPolicy; `noexec` `/workspace/`; non-root UID 10000+; seccomp (~50 syscalls); no `CAP_SYS_ADMIN` | Connection/operation blocked at kernel layer; Incident |
| **OOM / CPU hog / runaway query** | Resource exhaustion | Layer 7 cgroup hard limits (4GB RAM, 2 vCPU); 5-min timeout → SIGKILL | OOM Kill / SIGKILL → session terminated + Incident; partial results returned (if any) |
| **Critical CVE in dependency** | Known-vulnerable artifact deployed | Supply Chain CVE Scanning (Trivy/Safety, daily) | Critical CVE blocks deploy; High CVE requires waiver |
| **Tampered MCP/Skill manifest** | Malicious capability loaded | Supply Chain MCP/Skill Verification (Sigstore-signed; Runtime verifies before load) | Load refused on signature mismatch |

## Non-Functional Requirements

- **Defense in depth (necessary, not sufficient)** — each of the 7 layers is a necessary condition; no single layer alone provides sufficient protection (§22D principle).
- **Pre-Execution Deny** — Layer 2 rejects unauthorized tool calls *before* execution, not as post-hoc audit (§22D Layer 2).
- **Non-revealing rejections** — denial messages do not disclose specific detection rules or reasons to the user ("This operation is not permitted") to avoid aiding probing (Layer 1 Injection Pattern Detection, Layer 2 Role Check).
- **Irreversible redaction** — Layer 3 PII redaction is one-way before data enters LLM context; reflection-injection detection is a hard block (§22D Layer 3).
- **Hard vs soft blocks** — leakage/prompt-leakage/reflection-injection are hard blocks; low-confidence marking and some instruction-injection hits are soft warnings (Layers 3, 4).
- **Immutable & retained audit** — every interaction is logged immutably with full tool-call detail; Hot 30d / Warm 1y / Cold 7y retention; tenant-exportable JSON (Layer 6).
- **Real-time anomaly detection** — six rules (denial storm, >20 tool calls, cross-tenant, 2–5 AM pattern, >50K tokens, pattern probing) drive throttling/Incidents in real time (Layer 6).
- **Sandbox hard limits** — 4GB RAM, 2 vCPU, 5-min timeout, max 3 concurrent sessions per tenant per user, `/workspace/` 500MB + `noexec`, non-root UID 10000+, seccomp ~50 syscalls, no `CAP_SYS_ADMIN` (Layer 7).
- **Network egress locked** — Agent Runtime may only reach registered MCP endpoints via the Gateway; all other egress blocked at iptables/NetworkPolicy; internal DNS only (Layer 7).
- **Per-tenant container isolation** — each tenant runs in its own K8s Namespace; L3 (Finance/Government) tenants get a dedicated Node Group (Layer 7).
- **SLSA Level 3 supply chain** — signed commits, build provenance (in-toto/Rekor), Cosign artifact signing, CycloneDX SBOM + Dependency-Track, daily Trivy/Safety CVE scans, Sigstore-signed MCP/Skill manifests verified at load, hermetic builds (Supply Chain Security).
- **LLM supply-chain integrity** — SHA-256 model-weight verification, signed/templated prompts with hash check before injection, KB-embedding watermark cross-check vs. PG source (LLM-Specific Supply Chain Risks).

## Key Flows

### Per-tool-call Permission Gate flow (Layer 2, §22D)

```
LLM tool-call request { tool, params }
  → CHECK 1 Role    (Session Context: user_id → roles → permitted_tools)
  → CHECK 2 Tenant  (tenant_id auto-injected; WHERE tenant_id = $injected_tenant)
  → CHECK 3 Resource (Entitlement Service: column/row ACL; T3 → REDACT, T2 → HASH)
  → CHECK 4 Parameter (rule engine + ML anomaly: broad query? injection? too many cols/rows?)
  → PERMIT (with rewrite, e.g. SELECT name, '***' AS salary)
  OR DENY → SECURITY-level Audit Log + Alert
```

### End-to-end 7-layer defense flow (per query, §22D)

```
User NL
  → Layer 1 Input Sanitization & Prompt Injection Defense
      (wrap <user_input>; verify system_prompt SHA-256; regex+classifier injection scan;
       32KB cap; NFC + control-char + homoglyph; nested-delimiter detection)
  → [LLM reasoning decides tool-call]
  → Layer 2 Permission Gate (4-dim Pre-Execution Deny)
  → Layer 3 Tool Output Sanitization (PII redaction; truncation >100KB/>1M rows;
       schema validation; reflection-injection hard block)
  → [LLM Response Synthesizer]
  → Layer 4 Response Guard (data-leakage / prompt-leakage / instruction-injection scans;
       confidence < 0.7 per-claim marker; avg < 0.6 top banner)
  → Layer 5 Action Authorization (L0/L1 auto; L2 draft; L3 confirm; L4 confirm+MFA)
  → Layer 6 Audit & Monitoring (Interaction Log + Guard Trigger Log; 6 anomaly rules)
  → all of the above runs inside Layer 7 Sandbox Isolation
       (MCP-Gateway-only egress; /workspace noexec; 4GB/2vCPU/5min/3-concurrency;
        non-root; seccomp; per-tenant Namespace)
```

### Layer 5 Action Authorization flow

```
Agent suggests action → Action Router classifies tier →
  L0/L1 → auto-execute, response includes action result
  L2    → auto-execute as draft, "Draft created: [link]. Click to review and confirm."
  L3    → "Proposed action: [description]. [Confirm] [Dismiss]" → Confirm → Audit logged
  L4    → "Proposed action: [description]. MFA required. [Confirm with MFA] [Dismiss]"
           → TOTP/WebAuthn → Audit logged
```

### Supply-chain verification flow (load time)

```
MCP/Skill manifest delivered → Sigstore signature verified by Agent Runtime before load
Container image → Cosign-signed + attested; build provenance in Rekor
SBOM (CycloneDX) → ingested into Dependency-Track; daily Trivy/Safety CVE scan
System prompt / Skill template → Git signed commits; hash verified before injection
Model weights → SHA-256 verified at registry load
KB embeddings → watermark cross-check vs. PG source (§10.1)
```

### Shared runtime sequence

The end-to-end Agent query — where the Permission Gate (Layer 2) enforces its four-dimensional check before each tool call against Code Graph / KB Vector / KB Relational / Log Store, and the Output Guard (Layer 4) scans the synthesized response — is documented in [`../_shared/sequence-diagrams.md`](../_shared/sequence-diagrams.md) **§21.3 AI Agent Query with Permission Gating**. That sequence is the canonical reference for Layers 2 and 4 in action and is co-owned with [`knowledge-services`](../knowledge-services/) (Code Graph, KB Vector/Relational) and [`platform-core`](../platform-core/) (Auth, Log Store).

## Design References

- **Original sections**: §22D (Agent Security Architecture — 7-Layer Anti-Exploitation Defense), including the overview architecture diagram, Layer 1 (Input Sanitization & Prompt Injection Defense), Layer 2 (Tool-Call Permission Gating — Decision Matrix), Layer 3 (Tool Output Sanitization), Layer 4 (Response Guard), Layer 5 (Agent Action Authorization — Tiered + Action Authorization Flow), Layer 6 (Audit & Monitoring — Interaction Log, Guard Trigger Log, Audit Retention, Real-Time Anomaly Detection Rules), Layer 7 (Sandbox Isolation), and Supply Chain Security (SLSA + LLM-specific risks) of [`docs/03-architecture.md`](../../03-architecture.md).
- **Related agent-platform docs**: [`exploration-runtime.md`](exploration-runtime.md) (§3.2 — Layer 1 inherits/strengthens the input-side pipeline), [`dual-mode-orchestration.md`](dual-mode-orchestration.md) (§22A.1/§22A.2 — Layers 2/3/4 are runtime Steps 3/5/7; Layer 5 Action Router; Layer 7 hosts the runtime), [`mcp-catalog.md`](mcp-catalog.md) (§22C — Layer 2 gate targets; Layer 3 sanitizes their output; Layer 7 permits only the MCP Gateway), [`skill-catalog.md`](skill-catalog.md) (§22B — each Skill's `permissions` enforced by Layer 2).
- **Related sub-project docs**: [`platform-core`](../platform-core/) (Entitlement Service, Audit Trail, Incident Manager, Auth/MFA, Vault), [`workflow-engine` `execution-sandbox.md`](../workflow-engine/execution-sandbox.md) (§7 — inner Sandbox complementing Layer 7), [`knowledge-services`](../knowledge-services/) (§10.1 — KB embedding watermark cross-check).
- **Shared sequence diagram**: [`../_shared/sequence-diagrams.md`](../_shared/sequence-diagrams.md) §21.3 AI Agent Query with Permission Gating (primary sub-project).
- **External standards**: [SLSA v1.0](https://slsa.dev/), [OpenSSF Scorecard](https://securityscorecards.dev/), OWASP LLM05 (referenced in `docs/security/threat-model.md`).
- **ADRs** ([index](../../adr-index.md)): [ADR-0005 Four-Layer Architecture](../../../adr/0005-four-layer-architecture.md) (Zero AI Side Effects — underpinning the defense-in-depth posture), [ADR-0016 Dual-Mode Agent Orchestration](../../../adr/0016-dual-mode-agent-orchestration.md) (Verified Path as a Layer-2-aligned guardrail), [ADR-0017 Verified Path Saga Semantics](../../../adr/0017-verified-path-saga-semantics.md) (durable execution within the sandbox), [ADR-0020 Agent Cost Governance](../../../adr/0020-agent-cost-governance.md) (DoW defense and Layer 6 token-anomaly rules).
- **Glossary** ([../../glossary.md](../../glossary.md)): Prompt Injection, Data Exfiltration, Instruction Injection, Denial of Wallet, Permission Gate, Pre-Execution Deny, Reflection Injection, Response Guard, Action Authorization (L0–L4), Sandbox Isolation, SLSA, SBOM.
- **Cross-references retained from source**: §3.2 (Layer 1 inheritance), §7.2 (Python AST analysis feeding Layer 3 / MCP-13), §10.1 (KB embedding watermark cross-check), §22A.1/§22A.2 (runtime Steps hosting Layers 2/3/4), §22C (MCP endpoints gated by Layer 2), `docs/security/threat-model.md` (OWASP LLM05 alignment).
