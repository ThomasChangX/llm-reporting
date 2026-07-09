# STRIDE Threat Model & OWASP LLM Top 10 Assessment

> Extracted from [docs/03-architecture.md §16](../03-architecture.md) | Sync Date: 2026-07-04
>
> STRIDE threat matrix (10 components × 6 dimensions) + OWASP Top 10 for LLM Applications (v1.0, 2023) item-by-item assessment.
> Bare `§N` references below point to [docs/03-architecture.md](../03-architecture.md); consult that document for full context.

## 16.1 Threat Matrix

> Risk Levels: **H** = High (requires immediate mitigation), **M** = Medium (planned mitigation), **L** = Low (acceptable risk)
>
> "—" indicates the STRIDE dimension has no significant threat to the component or existing architecture has fully mitigated it.

| # | Component | STRIDE Category | Threat | Existing Mitigation | Residual Risk |
|---|-----------|-----------------|--------|---------------------|---------------|
| 1 | **Conversation Interface** | Spoofing | Attacker impersonates legitimate user via OAuth and launches prompt injection | Auth Gateway JWT validation + RBAC Context Injection (§3.1); per-request token signature + expiry verification | M |
| 1 | Conversation Interface | Tampering | User tampers with WebSocket messages to inject malicious instructions bypassing input sanitization | Input Sanitization (§3.1 Layer 1) + Instruction Boundary wrapping (§3.1 Layer 2) | M |
| 1 | Conversation Interface | Information Disclosure | LLM response leaks other tenants' KB data | Output Guard scanning (§3.1 Layer 4) + RBAC Context limiting retrieval scope (§2.1) | M |
| 1 | Conversation Interface | Denial of Service | Malicious user sends excessively long prompt exhausting LLM token quota | Input 32KB cap (§3.1 Layer 1); Rate Limiting per tenant on API Gateway | L |
| 1 | Conversation Interface | Elevation of Privilege | User induces LLM via prompt to execute admin operations | LLM never directly calls APIs; all operations authenticated via Design Plane; AI output is suggestion not command (§3) | L |
| 2 | **AI Copilot Engine** | Spoofing | Malicious LLM Provider returns tampered Spec suggestions | Only pre-approved Provider plugins supported (§3.4); all LLM outputs carry confidence score (§3.2) | M |
| 2 | AI Copilot Engine | Tampering | Attacker poisons KB Vector index causing compromised retrieval results | KB Write Pipeline enforces human confirmation Gate (§10); CDC sync version watermark verification (§10.1) | M |
| 2 | AI Copilot Engine | Repudiation | AI generates incorrect suggestion causing business loss with untraceable responsibility | LLM Interaction Log (§8 Layer 3) records prompt_hash, kb_retrieved, outcome; immutable audit | L |
| 2 | AI Copilot Engine | Information Disclosure | LLM Provider-side logs record sensitive data from user prompts | Pre-send PII masking (Query Rewriter pattern reuse); Provider contract includes data residency clauses | H |
| 2 | AI Copilot Engine | Denial of Service | LLM API quota exhaustion causing Design Plane unavailability | Provider plugin architecture supports multi-model switching; Fallback to open-source local models (e.g., Llama via vLLM) | M |
| 3 | **Spec Refinement Assistant** | Tampering | Attacker bypasses human Sign-off to auto-resolve fuzzy nodes | Spec Refinement Step 4 "Decide" enforces human confirmation (§4.1); code-level enforcement cannot be skipped | L |
| 3 | Spec Refinement Assistant | Repudiation | Approver denies having signed off on fuzzy node resolution | Each resolution records who/when/proposal/edits, immutably linked to Audit Trail (§4.1 Step 5) | L |
| 3 | Spec Refinement Assistant | Elevation of Privilege | Low-privilege user approves high-risk fuzzy nodes belonging to Data Owner | Fuzzy nodes grouped by risk level (§4.1 Step 3); high-risk nodes require Data Owner approval | M |
| 4 | **Workflow Executor** | Spoofing | Malicious Data Connector impersonates legitimate data source injecting false data | Data Connector Adapter five-level framework unified authentication (§5); Connector registration requires Admin approval | M |
| 4 | Workflow Executor | Tampering | Runtime SQL transform injected with malicious SQL (DROP/ALTER) | SQL AST Validation (§7.3 Layer 2) + Sandbox DB user minimal privileges (§7.3 Layer 4) | L |
| 4 | Workflow Executor | Information Disclosure | Sandbox logs leak T3-level sensitive field values | Log System auto-masks T3 fields before writing (§5.2 Classification Flow); structured log Schema pre-defines mask rules | M |
| 4 | Workflow Executor | Denial of Service | Single Workflow exhausts Sandbox pool starving other tenants | Bulkhead pattern: Per-tenant Sandbox pool isolation + cgroups limits (§5.1); Circuit Breaker per data source | L |
| 4 | Workflow Executor | Elevation of Privilege | User Workflow accesses data sources beyond their permissions | Query Rewriter injects row-level security predicates + column-level masking functions (§5); all queries compile-time permission checked | L |
| 5 | **Query Rewriter** | Tampering | Attacker injects predicates bypassing RLS filtering | Query Rewriter uses parameterized AST rewriting, rejects raw string concatenation; rewritten Query Plan recorded to Audit Trail (§5) | L |
| 5 | Query Rewriter | Information Disclosure | Column-level masking functions bypassed (e.g., via UDF indirect access) | Masking injected at query compilation stage in outermost projection, cannot be bypassed via subquery; UDF whitelist mechanism | M |
| 5 | Query Rewriter | Denial of Service | Rewriting engine itself becomes bottleneck causing all queries to timeout | Query Rewriter stateless design, horizontally scalable; rewrite result caching (Redis, 60s TTL per query fingerprint) | L |
| 6 | **Code Graph** | Spoofing | Malicious service forges Domain Events writing false graph edges | Event-sourced writes: only accepts messages from verified domain event bus (§2.1 Write Triggers); event signature verification | M |
| 6 | Code Graph | Information Disclosure | Graph traversal leaks cross-tenant relationship chains | RBAC Filter transparently filters row/column/edge three levels (§2.1); cross-tenant edges denied by default | M |
| 6 | Code Graph | Denial of Service | Deep recursive Cypher queries exhaust Graph DB resources | Query depth limit (max 10 hops) + query timeout (30s) + read replica separation (§2.1 Cache Strategy) | L |
| 7 | **KB Write Pipeline** | Tampering | Unconfirmed AI-extracted facts bypass Human Confirmation Gate entering KB directly | Write Pipeline code-level enforcement: Fact status `confirmed` is write precondition (§12.1); cannot be skipped | L |
| 7 | KB Write Pipeline | Repudiation | KB entry modified without traceable change history | All KB entries versioned (§10 Write Path); Git version control + Audit Trail dual recording | L |
| 7 | KB Write Pipeline | Information Disclosure | Customer PII in email originals leaked to LLM Provider during AI extraction | Pre-AI Fact Extraction PII pre-scan and masking on email body; Confidence Scoring does not carry original text | H |
| 7 | KB Write Pipeline | Elevation of Privilege | Non-Data Owner user confirms critical Business Glossary definitions | KB Entry approval policies by domain; Business Glossary entries require Data Owner approval (§11.3 PR Workflow) | M |
| 8 | **Email Ingest Gateway** | Spoofing | Attacker forges internal user email sending malicious attachments | SMTP SPF/DKIM/DMARC verification; Spam/Phishing Filter → Quarantine (§12.1 Ingestion Gateway) | M |
| 8 | Email Ingest Gateway | Tampering | Malicious attachments (.xlsx macro, .pdf exploit) trigger parser vulnerabilities | Attachments parsed in isolated Sandbox; 25MB size limit; executable file types blocked (.exe/.bat/.ps1) | M |
| 8 | Email Ingest Gateway | Denial of Service | Single tenant mailbox bombed exhausting parsing resources | Rate Limiting: 100 emails/hr per tenant (§12.1); exceeding rate enters Quarantine queue | L |
| 9 | **Notification Service** | Spoofing | Attacker forges system alerts inducing users to perform dangerous operations | All notifications carry digital signatures; In-App Inbox is trusted channel; external channels (Email/Slack) marked "Please verify internally" | M |
| 9 | Notification Service | Information Disclosure | Notification content (e.g., Incident details) leaked to unauthorized recipients | Notification Template pre-render RBAC filtering: recipient only sees Incident fields they are authorized to view | M |
| 9 | Notification Service | Denial of Service | Slack/Teams Webhook rate-limited causing critical alert loss | Failure degradation chain: Slack → Email → SMS → Incident; DLQ retry (§5.1 Dead Letter Queue) | L |
| 10 | **API Gateway** | Spoofing | Attacker uses stolen JWT Token to impersonate legitimate user | JWT short validity (15min access + 1h refresh); Token Binding (bind client IP/User-Agent fingerprint) | M |
| 10 | API Gateway | Tampering | Man-in-the-middle attack tampering API requests/responses | TLS 1.3 full-path enforcement; Certificate Pinning for critical upstreams; mTLS inside mesh | L |
| 10 | API Gateway | Denial of Service | DDoS attack exhausting Gateway connection pool | CDN (CloudFront/Cloudflare) + WAF (AWS WAF/ModSecurity) fronting; API Gateway Rate Limiting per tenant+IP | M |
| 10 | API Gateway | Elevation of Privilege | Attacker exploits API Gateway routing misconfiguration to access internal services | Gateway routing table only points to public API endpoints; internal services not exposed to Gateway; periodic route auditing | L |

### 16.2 Risk Remediation Priority

Priority items sorted by residual risk level:

| Priority | Component | Threat | Recommended Action |
|----------|-----------|--------|--------------------|
| **P0** | AI Copilot Engine | Provider-side log leakage of sensitive data | Deploy PII scanner before all prompts sent to LLM; sign DPA with vendor |
| **P0** | KB Write Pipeline | Email PII leakage to LLM | Enforce PII detection Pipeline before AI Fact Extraction; prohibit T3 data from being passed to external LLMs |
| **P1** | API Gateway | JWT theft leading to account takeover | Implement Token Binding + Anomaly Detection (abnormal IP/time/behavior pattern triggers re-auth) |
| **P1** | Conversation Interface | Prompt injection leaking cross-tenant data | Introduce LLM Firewall (e.g., GuardRails AI / Lakera Guard); semantic similarity detection on output side |
| **P2** | Code Graph | Cross-tenant relationship leakage | Periodic penetration testing: Graph traversal with cross-tenant edge cases |
| **P2** | Notification Service | Alert content leakage | Secondary receiver permission verification at Dispatch stage |

### 16.3 OWASP Top 10 for LLM Applications Assessment

STRIDE covers traditional security threats but does not fully cover LLM-specific attack surfaces. Item-by-item assessment per OWASP Top 10 for LLM Applications (v1.0, 2023):

| OWASP LLM Threat | Risk Level | Existing Defense | Residual Risk | Recommendation |
|----------------|---------|---------|---------|------|
| **LLM01: Prompt Injection** | [CRITICAL] | §3.1 Five-Layer Defense (Input Sanitization + Instruction Boundary + RBAC Context + Output Guard + Audit) + §3.1 KB Content Sanitization | Medium | Add Lakera Guard or equivalent dedicated injection detection; require explicit secondary confirmation for high-sensitivity operations |
| **LLM02: Insecure Output Handling** | [HIGH] | §22D Layer 4 Response Guard + Layer 5 Action Authorization (L0-L4 five-level classification) | Low | Adequately defended |
| **LLM03: Training Data Poisoning** | [HIGH] | KB three-path write (user explicit > AI confirmed > system auto) + human confirmation gate; FR34 five-gate write | Medium | Add §3.1 KB Content Sanitization (already supplemented); periodically audit instruction patterns in KB entries |
| **LLM04: Model Denial of Service** | [HIGH] | §22D Layer 7 Sandbox (5min timeout, 4GB/instance, 3 concurrent/tenant); §5.1 Rate Limiting | Low | Adequately defended |
| **LLM05: Supply Chain Vulnerabilities** | [HIGH] | §22A Model Registry only supports pre-approved Provider plugins; Python import whitelist (§7.2) | Medium-High | **Needs Enhancement**: Add signature verification for MCP Servers/Skills; regular CVE scanning of AI/ML dependencies; record SBOM for all models/Skills/MCPs |
| **LLM06: Sensitive Information Disclosure** | [CRITICAL] | §5.2 Data Classification T0-T3 + §11.1 Encryption + §22D Layer 3 Output Sanitization + Query Rewriter RLS/CLS | Low-Medium | [WARN] LLM Interaction Log stores complete prompt/response (§8) → ensure Cold storage encryption + access auditing; consider auto-redacting T3 data before LLM |
| **LLM07: Insecure Plugin Design** | [HIGH] | §22D Layer 2 Permission Gate (four-dimensional check) + Layer 5 Action Authorization + Sandbox isolation | Medium | **Needs Enhancement**: Add input parameter schema validation for MCP calls; sanitize inter-Skill data passing |
| **LLM08: Excessive Agency** | [HIGH] | §22D Layer 5 Five-Level Classification (Read→Suggest→Draft→Execute→Admin) + Pre-Execution Permission Gate | Low | Adequately defended. L3+ operations require explicit human confirmation; L4 operations require MFA |
| **LLM09: Overreliance** | [MEDIUM] | All AI output marked with confidence score + fuzzy_nodes; human approval at key decision points | Medium | **Needs Enhancement**: Add "AI-Assisted" watermark to AI-generated reports; quarterly Accuracy Audit; FR28.3 AI Agent responses must cite sources |
| **LLM10: Model Theft** | [MEDIUM] | Model Registry unified API Key management (Vault); Tenant-level private model deployment isolation | Medium | **Needs Enhancement**: API Key access frequency anomaly detection; encrypted storage for local model weights; periodic audit of model access logs |

> **Note**: The OWASP LLM Top 10 (v1.0, 2023) list has exactly 10 items (LLM01-LLM10). Vector/Embedding Weaknesses is covered under the 2025 list as a separate item but is not part of the v1.0 standard used here; it is addressed in the architecture via KB entry version control and embedding model configurability (§10.1).

> **Comprehensive Conclusion**: This architecture provides adequate defense on LLM01/02/04/08. LLM05 (Supply Chain), LLM07 (Insecure Plugins), LLM09 (Overreliance), LLM10 (Model Theft) have residual risks requiring enhancement in Phase 6-7. All enhancement items have been added to the Phase 6-7 development roadmap.

---

> 📄 Original Location: [../03-architecture.md §16](../03-architecture.md)
