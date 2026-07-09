# 02 - Requirements

> Functional requirements, non-functional requirements, and constraints extracted from discussions. This document should be continuously refined throughout the design process.
>
> **Document Version:** v1.0 | **Last Updated:** 2026-07-04 | **Status:** Stable

---

## Functional Requirements

### Priority Definitions

| Priority | Meaning | Description |
|----------|--------|-------------|
| P0 | Must Have | Core capabilities the product cannot function without; must be delivered in MVP |
| P1 | Should Have | Important but not blocking; delivered in late MVP or V1.0 |
| P2 | Could Have | Nice-to-have; delivered when resources and time permit |
| P3 | Won't Have Now | On the long-term roadmap; not delivered in the current version |

### Requirements Writing Standards (INVEST Principles)

> ⚠️ Most current FRs lack testable acceptance criteria and need to be supplemented before entering the development phase.

Each functional requirement should include: User Story (As a [role], I want [capability], so that [value]), Acceptance Criteria (Given/When/Then testable conditions), Boundary Conditions (exception scenarios, degradation behavior), Related Requirements (upstream/downstream FR/NFR dependencies).

### FR1: AI-Assisted Exploration
| ID | Requirement | Priority |
|----|------------|----------|
| FR1.1 | Users can describe desired analysis results in natural language | P0 |
| FR1.2 | System can automatically locate relevant data sources, infer schema, and suggest visualizations | P0 |
| FR1.3 | AI-assisted generation of transform logic, metric definitions, and report layouts | P0 |
| FR1.4 | Users can manually correct any AI output at any time | P0 |

> 🔗 FR1 → FR29: AI-assisted exploration capabilities depend on the AI Agent technical architecture

### FR2: Workflow Freeze & Script
| ID | Requirement | Priority |
|----|------------|----------|
| FR2.1 | Users can one-click freeze a validated complete task flow into a deterministic script | P0 |
| FR2.2 | Frozen scripts no longer depend on LLMs, ensuring deterministic output and low-cost execution | P0 |
| FR2.3 | Scripts must support parameterization and reusability (version control see FR8.1) | P0 |
| FR2.4 | Scripts exportable as standard file formats (e.g., YAML, Python, SQL) | P1 |

### FR3: Observation & Suggestion
| ID | Requirement | Priority |
|----|------------|----------|
| FR3.1 | System continuously observes user operation patterns and identifies repetitive tasks | P1 |
| FR3.2 | When repeatable patterns are detected, proactively suggests creating reusable workflows | P1 |
| FR3.3 | Analyzes potential requirements based on user behavior and recommends workflow templates | P2 |

> 🔗 FR3 → FR32.6: User behavior patterns are persistently stored in the KB's User Behavior Pattern Store

### FR4: Knowledge Base
| ID | Requirement | Priority |
|----|------------|----------|
| FR4.1 | System maintains long-term memory: business semantics, data dictionary, metric definitions | P0 |
| FR4.2 | Users can explicitly provide: data source mapping relationships, table relationships, business rules | P0 |
| FR4.3 | Stores historical adjustment reasons, workflow templates, user preferences | P1 |
| FR4.4 | New requests first retrieve relevant KB context before reasoning, improving accuracy | P0 |
| FR4.5 | Technical foundation: PostgreSQL + pgvector (Vector/Graph/Relational unified) + S3/MinIO (Object Store). Dedicated engines reserved via interface abstraction, introduced on-demand (see adr/0013) | P0 |

### FR5: Reporting
| ID | Requirement | Priority |
|----|------------|----------|
| FR5.1 | Supports multi-data-source access and mixed queries | P0 |
| FR5.2 | AI-assisted chart recommendation and auto-generation | P0 |
| FR5.3 | Supports report templating, parameterization, and scheduled publishing | P1 |
| FR5.4 | AI proactively pushes anomaly/insight notifications | P2 |
| FR5.5 | Reports exportable in multiple formats (PDF, Excel, CSV) | P1 |

### FR5b: Dashboard
| ID | Requirement | Priority |
|----|------------|----------|
| FR5b.1 | Supports drag-and-drop Dashboard construction: Widget adding, layout adjustment, size scaling | P0 |
| FR5b.2 | Widget types: KPI cards, trend charts, bar/line/pie charts, heatmaps, tables, text | P0 |
| FR5b.3 | Cross-Widget linking: clicking a data point in one Widget auto-filters other Widgets to the relevant dimension | P1 |
| FR5b.4 | Supports parameterization (date range, department filter), parameters can be global or local | P1 |
| FR5b.5 | Dashboard can be scheduled for publishing (Email/Slack) and embedded in external systems (iframe/API) | P2 |
| FR5b.6 | Supports data Drill-down and Roll-up within the Dashboard | P2 |

> 🔗 FR5b → FR24.4: Dashboard Widget formats are defined by the Format System's Dashboard format

### FR6: ETL Workflow
| ID | Requirement | Priority |
|----|------------|----------|
| FR6.1 | Supports multiple data source types (DB, API, File, Stream) | P0 |
| FR6.2 | AI-assisted data source discovery, schema inference, and intelligent mapping | P0 |
| FR6.3 | Visual transform logic editing + AI-assisted generation | P0 |
| FR6.4 | Data quality validation and anomaly alerting | P1 |
| FR6.5 | Frozen ETL pipelines execute independently of AI | P0 |

> 🔗 FR6 → FR15: ETL data source connectivity is provided by the unified Integration Framework

### FR7: Adjustment
| ID | Requirement | Priority |
|----|------------|----------|
| FR7.1 | Dev/Admin can define Adjustment Forms (column definitions, validation rules, approval chain), producing Form Definition YAML | P0 |
| FR7.2 | Business Users can submit via Web UI, Excel download-upload, or API — all three go through the same pipeline | P0 |
| FR7.3 | Submission pipeline: Permission → Validation → Approval → Trigger ETL. Any operation modifying financial data, regardless of amount, must pass this pipeline — there is no Auto-write-off | P0 |
| FR7.4 | Approval rules configurable: four-eyes principle / amount-threshold dual approval / no approval (to meet different Team needs) | P0 |
| FR7.5 | Repeat Adjustment: scheduled pre-set Adjustments (amounts pre-populated), approval path simplified (within historical range auto-approve) | P1 |
| FR7.6 | Daily Manual Adjustment: event-driven blank form, complete approval chain | P1 |
| FR7.7 | AI reasons adjustment causes with KB context (metric differences/data entry errors/exchange rate fluctuations) → suggests Adjustment drafts → human approval → execution | P2 |
| FR7.8 | Complete audit trail: pre-adjustment value, post-adjustment value, adjustment reason, approval chain | P0 |
| FR7.9 | Historical adjustments auto-ingested into KB (Adjustment History domain), improving future reasoning accuracy | P2 |

### FR8: Enterprise SDLC & Governance
| ID | Requirement | Priority |
|----|------------|----------|
| FR8.1 | Version Control: Git-like versioning for Workflow Scripts | P0 |
| FR8.2 | Code Review mechanism (workflow changes require peer review) | P1 |
| FR8.3 | Automated testing (workflow test cases, data snapshot comparison) | P1 |
| FR8.4 | Canary Deployment: supports multi-stage canary percentages (1%→10%→50%→100%). Each stage must meet gating conditions (P95 + DQ <1.5x baseline) before advancing; anomalies trigger auto-rollback | P0 |
| FR8.5 | Rollback mechanism | P0 |

### FR9: Entitlement Control
| ID | Requirement | Priority |
|----|------------|----------|
| FR9.1 | Fine-grained data access control (row-level / column-level / table-level) | P0 |
| FR9.2 | Operation permission control (who can modify metrics, who can approve adjustments, who can freeze scripts) | P0 |
| FR9.3 | Role-permission model with support for custom roles | P1 |
| FR9.4 | Integration with mainstream authentication systems (OAuth 2.0, Kerberos, SAML/SSO) | P1 |

### FR10: Audit & Compliance
| ID | Requirement | Priority |
|----|------------|----------|
| FR10.1 | Complete operation audit log (who, when, what, data changes) | P0 |
| FR10.2 | Data lineage tracking (where data came from → what transforms were applied → where it went) | P0 |
| FR10.3 | Audit logs exportable as files | P1 |
| FR10.4 | Meets industry compliance requirements (SOX, HIPAA, GDPR) | P0 |

### FR10b: Privacy & Data Subject Rights
| ID | Requirement | Priority |
|----|------------|----------|
| FR10b.1 | Supports data subject "Right to Erasure": cascade-delete all associated data (KB entries, vector embeddings, audit logs, backups) per user/tenant request, providing deletion proof | P1 |
| FR10b.2 | Supports Data Portability: users/tenants can request full data export in structured machine-readable format (JSON/Parquet) | P1 |
| FR10b.3 | Consent Management: records the lawful basis for data processing (consent/contract/legal obligation), supports consent withdrawal and audit | P1 |
| FR10b.4 | Data Residency Enforcement: after tenant configures data storage regions, the system enforces no cross-region transfer/storage | P1 |

> 🔗 FR10b → NFR9: Privacy and Data Subject Rights implementation depends on data governance and compliance NFRs

### FR11: Integration & Extensibility
| ID | Requirement | Priority |
|----|------------|----------|
| FR11.1 | Integration/interaction with existing legacy systems (ERP, financial systems, data warehouses, etc.) | P0 |
| FR11.2 | Open API supporting third-party extensions | P1 |
| FR11.3 | Template marketplace / plugin ecosystem (future) | P3 |

### FR12: Multi-tenancy & Tiered Model
| ID | Requirement | Priority |
|----|------------|----------|
| FR12.1 | Supports three tenant types: Individual, Team/SMB, Large Enterprise | P1 |
| FR12.2 | Differentiated interfaces and capabilities by role | P1 |
| FR12.3 | Supports tiered feature/compute/storage pricing model | P2 |

---

## Non-Functional Requirements

### NFR1: Reliability
| ID | Requirement | Priority |
|----|------------|----------|
| NFR1.1 | Frozen workflow scripts must execute deterministically with zero AI side effects (no LLM invocation; Intelligence Plane provides AI read-only analysis but does not cross the bridge) | P0 |
| NFR1.2 | System must handle LLM output drift/hallucination issues; critical paths must not depend on LLMs | P0 |

### NFR2: Cost
| ID | Requirement | Priority |
|----|------------|----------|
| NFR2.1 | Avoid invoking LLMs for every task; after freezing, execution incurs no AI invocation cost | P0 |
| NFR2.2 | LLM invocations require budget controls, priority queues, and caching strategies | P1 |

### NFR3: Performance
| ID | Requirement | Priority |
|----|------------|----------|
| NFR3.1 | Interaction latency in AI Exploration Mode must meet usability requirements (NL→Preview P95 ≤ 3s, follow-up context refresh ≤ 2s) | P1 |
| NFR3.2 | Frozen script execution must meet enterprise batch processing requirements: 1M rows end-to-end P95 < 5min | P0 |

### NFR4: Security
| ID | Requirement | Priority |
|----|------------|----------|
| NFR4.1 | Data encryption in transit and at rest | P0 |
| NFR4.2 | Support for enterprise security policies (data residency, network isolation, etc.) | P1 |

### NFR5: Scalability
| ID | Requirement | Priority |
|----|------------|----------|
| NFR5.1 | Architecture must support elastic scaling from individual to large enterprise | P1 |
| NFR5.2 | Plugin architecture supporting customization and extension for different industries/scenarios | P2 |

### NFR6: Usability & Accessibility
| ID | Requirement | Priority |
|----|------------|----------|
| NFR6.1 | Web interface conforms to WCAG 2.1 Level AA accessibility standards | P1 |
| NFR6.2 | Average time for new users to complete their first report creation < 15 minutes (without training) | P0 |
| NFR6.3 | System supports bilingual interface (Chinese/English) via i18n framework, extensible to additional languages | P2 |
| NFR6.4 | Core task operation paths ≤ 3 clicks/inputs (e.g., creating reports, approving adjustments) | P1 |

### NFR7: Availability & Resilience
| ID | Requirement | Priority |
|----|------------|----------|
| NFR7.1 | Design Plane service availability ≥ 99.9% (monthly), planned maintenance windows ≤ 4 hours/month | P1 |
| NFR7.2 | Runtime Plane critical Workflow execution availability ≥ 99.95% (quarterly) | P0 |
| NFR7.3 | Disaster Recovery (RPO/RTO see FR41) | P1 |

### NFR8: Maintainability & Portability
| ID | Requirement | Priority |
|----|------------|----------|
| NFR8.1 | Modular architecture: core modules communicate through well-defined APIs; any module can be independently replaced | P1 |
| NFR8.2 | System supports deployment on major cloud platforms (AWS/Azure/GCP) and private Kubernetes clusters | P1 |
| NFR8.3 | Data exportable in standard open formats (JSON/Parquet), supporting system migration and data portability | P1 |
| NFR8.4 | Plugin/Skill hot-loading without restarting core services | P2 |

### NFR9: Data Governance & Compliance
| ID | Requirement | Priority |
|----|------------|----------|
| NFR9.1 | Supports differentiated retention policies by data classification (audit logs 7 years, behavior logs 90 days) | P1 |
| NFR9.2 | Supports "Right to Erasure": user/tenant data can be completely erased including all backups, logs, KB entries, vector embeddings | P1 |
| NFR9.3 | Supports Data Portability: tenants can request export of all data in machine-readable format | P1 |
| NFR9.4 | Data Residency: tenants can specify geographic regions for data storage and computation; system enforces no cross-border movement | P1 |

## Constraints
- **Unreliability**: Core execution paths must not depend on LLM reasoning
- **Enterprise Environment**: Must support SDLC, permission, and compliance requirements
- **Legacy System Coexistence**: Cannot require enterprises to replace existing systems; smooth integration is required
- **File Export**: All core artifacts (scripts, reports, audit logs) must be exportable as standard file formats
- **Authentication Diversity**: Must integrate OAuth, Kerberos, SAML/SSO

## User Roles (Preliminary)

| Role | Description |
|------|-------------|
| Viewer | View reports, Dashboards |
| Analyst | Create analyses, explore data, configure workflows |
| Approver | Approve adjustments, review workflow changes |
| Admin | Manage permissions, configure system, manage KB |
| Developer | Develop/modify frozen scripts, manage data pipelines |

## Glossary

> The complete glossary (102 core concepts covering architecture concepts, KB, Jobs, AI Agent, BRD/ADR, data compliance, development operations, regulatory standards) has been moved to [glossary.md](glossary.md). Below is a quick reference for core terms.

### Core Terms Quick Reference

| Term | Definition |
|------|------------|
| Design Plane | AI-assisted exploration and authoring layer. All artifacts are design drafts with no production side effects. |
| Freeze Bridge | The independent transition plane that converts AI artifacts into deterministic scripts with mandatory human sign-off — not auto-compilation. |
| Runtime Plane | Deterministic, zero AI side-effect production execution layer. The Intelligence Plane provides AI read-only analysis (ad-hoc Q&A) without crossing the bridge. |
| Intelligence Plane | Cross-plane AI read-only analysis layer (ad-hoc NL Q&A, attribution analysis). Core constraint: read-only, never writes; temporary answers do not cross the bridge. |
| Compute Spec | Unified YAML-based computation definition. 9 Job Types. |
| Knowledge Base (KB) | 9 knowledge domains. PG-First storage strategy: PostgreSQL + pgvector unified + S3/MinIO. Dedicated engines introduced on-demand. Unified Content Processing Pipeline (ADR-0023) + Diagnostic Playbooks & Code Knowledge domains (ADR-0024). |
| ADR (Architecture Decision Record) | MADR format. 12 lifecycle states, first-class entity in the system. |

> See [glossary.md](glossary.md) for the complete glossary (101 terms).

---

## 2026-07-04 Supplemental Requirements: Compute Spec / Query Service / Data Masking

### FR13: Compute Spec (Unified Compute Definition)
| ID | Requirement | Priority |
|----|------------|----------|
| FR13.1 | Supports defining computation tasks in YAML format: variables, data_sources, transforms, output, schedule | P0 |
| FR13.2 | Covers four scenarios: Reporting, ETL, Adjustment, Reconciliation | P0 |
| FR13.3 | Engine-independent design: the same spec can execute on different compute engines | P0 |
| FR13.4 | The Spec itself forms a complete DAG, naturally traceable for data lineage | P0 |
| FR13.5 | Supports embedding Python/Polars/SQL code blocks as transform logic | P0 |
| FR13.6 | Supports 9 Job types: source, transform, output, quality, workflow_ref, data_writer, decision, wait, materialize | P0 |
| FR13.7 | Distinguishes Variables (runtime-injected, e.g., date ranges — cannot change DAG topology) from Parameters (config-level, e.g., connection strings) | P0 |
| FR13.8 | Supports Group-level default policies: concurrency limits, retry policy, timeout, failure strategy | P1 |

### FR14: Dual Engine Strategy
| ID | Requirement | Priority |
|----|------------|----------|
| FR14.1 | Light Engine (Design Plane): DuckDB + Polars for interactive exploration, data preview, dev/testing | P0 |
| FR14.2 | Heavy Engine (Runtime Plane): Spark (Post-MVP), Trino/Ray (Phase 7+) for production execution, large-scale data, multi-source federation | P1 |
| FR14.3 | The same Compute Spec can specify a target execution engine for seamless switching | P1 |

### FR15: Integration Framework
| ID | Requirement | Priority |
|----|------------|----------|
| FR15.1 | Level 1: File-Based (SFTP/S3/HDFS/Shared Folder), formats: CSV/JSON/Parquet/Avro/Excel/XML | P0 |
| FR15.2 | Level 2: DB Protocol (JDBC/ODBC/Native Driver), targets: MySQL/PG/Oracle/SQL Server/DB2/Hive | P0 |
| FR15.3 | Level 3: API/Service (REST/GraphQL/gRPC/SOAP) with multiple authentication methods | P0 |
| FR15.4 | Level 4: Message/Stream (Kafka/RabbitMQ/MQ/Pulsar) | P1 |
| FR15.5 | Level 5: Custom Plugin SDK — users implement the unified DataSource Interface and upload as custom Connectors | P2 |
| FR15.6 | Unified DataSource Interface: connect → discover → query → write → capabilities | P0 |

> FR15 → FR6: The Integration Framework provides standardized data source connectivity for ETL Workflows

### FR15b: Query Service
| ID | Requirement | Priority |
|----|------------|----------|
| FR15b.1 | IT administrators can register database connection info; system auto-scans database Schema structure (tables, columns, types, indexes) | P0 |
| FR15b.2 | System auto-detects PK/FK relationships (DDL declarations + naming convention inference + data distribution inference); IT can manually declare and correct table relationships (including cross-database, JOIN types, cardinality) | P0 |
| FR15b.3 | When users request data via NL, system auto-retrieves Schema info from Data Catalog and generates optimal queries (correct JOIN paths, aggregation, filtering) | P0 |
| FR15b.4 | Queries auto-execute Pushdown optimization: WHERE/JOIN/AGGREGATION executed at the data source where possible, only necessary result sets transferred to Compute Engine | P0 |
| FR15b.5 | Pushdown Plan visualization (which operations execute at data source vs. Compute Engine, estimated row transfers) | P1 |
| FR15b.6 | Cross-source queries auto-select optimal JOIN strategy (small table broadcast to data source local JOIN vs. Compute Engine federated JOIN) | P1 |
| FR15b.7 | Query result caching: same SQL + parameters + Schema version → reuse cached result, configurable TTL | P1 |
| FR15b.8 | Schema change auto-detection → invalidate related caches → notify affected Workflow Owners | P1 |

> FR15b → FR6, FR15, FR5: The Query Service provides a unified, optimized data access layer for all data consumption scenarios

### FR15c: Large-Scale Data Handling
| ID | Requirement | Priority |
|----|------------|----------|
| FR15c.1 | Supports reading/writing Apache Iceberg / Delta Lake / Hudi modern table formats (via Data Connector plugins) | P1 |
| FR15c.2 | Auto-detects and utilizes partition info for Partition Pruning; TB-scale table queries only scan relevant partitions | P1 |
| FR15c.3 | Incremental processing modes: Watermark incremental (by time column), CDC incremental (consume Change Log), Partition incremental (new partitions only) | P1 |
| FR15c.4 | Materialized Aggregation: supports Full Refresh and Incremental Refresh strategies; auto-selects available materialized views to substitute detail queries | P1 |
| FR15c.5 | Table statistics collection (NDV, Min-Max, row count); statistics-driven JOIN strategy selection (Broadcast/Shuffle/Pushdown) | P2 |
| FR15c.6 | Query Plan Guard: estimated scan >100M rows or >10GB → Warning; >30min estimated execution time → reject Design Plane preview | P1 |
| FR15c.7 | Heterogeneous data source federation strategy: small dimension tables broadcast → same-source Pushdown → cross-source materialized copies → federated query engine (auto-selection by transfer cost) | P2 |
| FR15c.8 | Watermark state management: persistent storage, transactional updates, watermark not advanced on execution failure | P1 |

### FR16: Data Masking & Row-Level Security
| ID | Requirement | Priority |
|----|------------|----------|
| FR16.1 | Static Masking: irreversibly mask sensitive columns upon data ingestion | P0 |
| FR16.2 | Dynamic Masking: decide at query time whether to show original values or masks based on role | P0 |
| FR16.3 | Row-Level Security: roles can only see data rows matching their permissions | P0 |
| FR16.4 | Aggregation Restrictions: low-privilege roles see only aggregated results, cannot drill down to detail | P1 |
| FR16.5 | Runtime Plane Query Rewriter injects permission predicates and masking functions | P0 |

---

## 2026-07-04 Supplemental Requirements: Email / Recon / Data Quality / DevOps / Support / Tracking

### FR17: Email Ingestion
| ID | Requirement | Priority |
|----|------------|----------|
| FR17.1 | System provides a dedicated inbox (kb@[tenant].system.com) | P2 |
| FR17.2 | Supports auto-ingestion via mail forwarding rules + manual .eml/.msg uploads + paste body | P2 |
| FR17.3 | Structured email parsing: From/To/CC/Date/Subject/Body + attachment extraction | P2 |
| FR17.4 | AI extracts objective facts (numbers, dates, definitions, decisions); human confirms before KB ingestion | P2 |
| FR17.5 | Every piece of knowledge in KB can be traced back to its original email source | P2 |
| FR17.6 | Intelligent attachment parsing: Excel→tables, PDF→text, images→OCR | P2 |
| FR17.7 | Information not confirmed does not enter KB; explicit Confirm/Edit/Dismiss operations | P2 |

### FR18: Data Health — Reconciliation (see adr/0014)
| ID | Requirement | Priority |
|----|------------|----------|
| FR18.1 | As a type: recon check in the unified Data Health Check Framework, YAML-configuration driven | P0 |
| FR18.2 | Supports defining Match Key + configurable Tolerance Profile for two data sources (by account type, materiality threshold, region — not fixed three-tier) | P0 |
| FR18.3 | Auto-classification after Recon execution: Matched / Unmatched / Partial | P0 |
| FR18.4 | AI + KB reasoning for break causes (TIMING/MISSING/ROUNDING/MAPPING/CURRENCY/DUPLICATE/UNKNOWN) | P1 |
| FR18.5 | All finance-related Resolution suggestions must go through the Adjustment pipeline (Permission→Validation→Approval→Trigger ETL). No Auto-write-off exists. | P0 |
| FR18.6 | Recon Check itself can be frozen as a Compute Spec into a reusable Workflow | P1 |
| FR18.7 | Recon Report exportable + stored in KB (Adjustment History domain) | P1 |
| FR18.8 | type: anomaly check can be bound to Recon checks for cross-period trend detection (e.g., match rate abnormal decline) | P2 |
| FR18.9 | Execution modes: auto (after Recon execution), scheduled (cron), manual, on_recon_complete | P1 |

### FR19: Data Health — Rules & Anomaly Detection (see adr/0014)
| ID | Requirement | Priority |
|----|------------|----------|
| FR19.1 | Unified Data Health Check Framework, YAML-configuration driven. Three check types: rule (rule-driven), anomaly (ML-driven), recon (cross-source). All three share common scope/severity/schedule/output configuration | P0 |
| FR19.2 | type: rule supports 7 dimensions: Completeness, Accuracy, Consistency, Timeliness, Uniqueness, Validity, Temporal_Consistency (e.g., Line 3 vs. Line 12 cumulative validation) | P0 |
| FR19.3 | type: anomaly — ML-driven, no explicit rules. Methods: ratio_change / z_score / seasonal_decomp / distribution_shift / trend_change. Users only specify scope + sensitivity | P1 |
| FR19.4 | Execution modes: auto (after Report generation), scheduled (cron), manual, on_recon_complete (after Recon) | P1 |
| FR19.5 | Three severity levels: Error (blocks Freeze Bridge or Runtime Pre-Exec) / Warning (annotates Report, doesn't block) / Info (log only) | P0 |
| FR19.6 | Output: Annotated Report (row-level anomaly marking + root cause summary + confidence). Does not block Report publication. | P1 |
| FR19.7 | Users can click anomaly annotations in Reports → ask AI Agent (root cause analysis, attribution tracing) → optionally create BRD → push to Jira/Rally/ServiceNow | P2 |
| FR19.8 | Consistency dimension auto-correlates with Recon checks (aggregate vs. detail inconsistency → trigger type: recon) | P2 |
| FR19.9 | Quality trend Dashboard + Data Source Health Score (0-100), 7/30/90-day trends | P2 |

### FR20: DevOps & CI/CD
| ID | Requirement | Priority |
|----|------------|----------|
| FR20.1 | Complete CI/CD Pipeline for Compute Spec / Workflow Scripts (Build → Test → Deploy) | P1 |
| FR20.2 | Sandbox environments auto-created and destroyed (per PR / per Branch) | P1 |
| FR20.3 | Infrastructure as Code: Runtime Plane resources defined and managed through configuration | P2 |
| FR20.4 | Monitoring & Alerting: Workflow execution status, data latency, resource usage, SLA deviations | P1 |
| FR20.5 | Log Aggregation: unified query across Design Plane operation logs + Runtime execution logs | P1 |
| FR20.6 | Incident Management: execution failures auto-create Incidents + rollback + notification | P1 |
| FR20.7 | Environment Management: Dev / Staging / Prod isolation and promotion flow | P1 |

### FR21: Support & Service Ticket
| ID | Requirement | Priority |
|----|------------|----------|
| FR21.1 | Embedded Support Portal: users can submit issues and check status | P1 |
| FR21.2 | Integration with external ticketing systems (Jira Service Management, ServiceNow, Zendesk) | P2 |
| FR21.3 | Execution failures / data anomalies auto-generate Tickets (with context: Workflow ID, error logs, data snapshots) | P1 |
| FR21.4 | Tickets bidirectionally linked with Workflow / Compute Spec (jump from Ticket to related Script) | P1 |
| FR21.5 | Knowledge Base articles: solutions to common issues auto-deposited into KB | P2 |

### FR22: Project Tracking Integration
| ID | Requirement | Priority |
|----|------------|----------|
| FR22.1 | Workflow changes can be linked to Jira / Rally Stories / Epics | P2 |
| FR22.2 | Compute Spec PR / Review / Merge status synced to external Tracking tools | P2 |
| FR22.3 | Traceability chain: BRD → Epic → User Story → Compute Spec | P2 |
| FR22.4 | Deployment status write-back: auto-update Jira/Rally Ticket status upon Prod deployment | P2 |

### FR23: BRD & ADR
| ID | Requirement | Priority |
|----|------------|----------|
| FR23.1 | BRD templating: business requirements linked to Compute Spec / Workflow | P1 |
| FR23.2 | BRD changes auto-flag affected Workflows (traceability matrix) | P2 |
| FR23.3 | ADR built into the system: architecture decisions auto-linked to corresponding modules | P1 |
| FR23.4 | ADR bidirectional linking with Compute Spec / KB entries (view impact from decision, view basis from implementation) | P1 |
| FR23.5 | BRD / ADR exportable as standard document formats | P2 |

### FR24: Format System
| ID | Requirement | Priority |
|----|------------|----------|
| FR24.1 | Global Format definitions, decoupled from Jobs, supporting reuse | P1 |
| FR24.2 | Report format: page layout, header/body/footer templates, conditional_format, sorting, charts | P1 |
| FR24.3 | Excel format: multi-sheet, frozen panes, auto_filter, pivot_table, sparkline | P1 |
| FR24.4 | Dashboard format: kpi_card, heatmap, trend, and other widgets | P1 |
| FR24.5 | Data Export format: parquet/csv/json, compression, partition_by | P1 |
| FR24.6 | Writeback config: destination connector, write_mode (append/upsert/overwrite/merge), transaction | P1 |

### FR25: Writeback Job
| ID | Requirement | Priority |
|----|------------|----------|
| FR25.1 | Supports writing computed results back to data sources (DB/Cache/File) | P1 |
| FR25.2 | write_mode: append / upsert / overwrite / merge | P1 |
| FR25.3 | Transactional writes (all-or-nothing rollback) | P1 |
| FR25.4 | Pre-write validation + post-write verification | P1 |

> Writeback Job targets must be data_sources registered in the Data Catalog. Writing to file systems/message channels uses output Jobs.

### FR26: Execution Sandbox
| ID | Requirement | Priority |
|----|------------|----------|
| FR26.1 | Each Job executes in an isolated Sandbox with resource isolation (CPU/Mem/Disk/Net) | P1 |
| FR26.2 | Sandbox Pool pre-warming to reduce cold start latency | P2 |
| FR26.3 | Security isolation: FS boundaries (read-only/read-write/tmpfs), Network whitelist, seccomp | P1 |
| FR26.4 | Multi-tenant isolation selectable levels: Process isolation / Node isolation / Cluster isolation | P2 |
| FR26.5 | Design Plane uses lightweight Sandboxes (DuckDB/Polars, second-level startup, sampled data) | P1 |

### FR27: Log System
| ID | Requirement | Priority |
|----|------------|----------|
| FR27.1 | Three-layer logging: Structured Event Log + Execution Trace + LLM Interaction Log | P1 |
| FR27.2 | Unified Event Schema: event_id, timestamp, type, tenant, workflow, job, actor, parent, data, result, error | P1 |
| FR27.3 | LLM Interaction Log records every AI invocation: prompt_hash, kb_retrieved, tokens, cost, latency, outcome | P1 |
| FR27.4 | AI-Powered Log Analysis: real-time anomaly detection, auto Incident Diagnosis, Cost Tracking | P2 |
| FR27.5 | Tiered Storage: Hot 7 days (ES) → Warm 90 days (S3+Parquet) → Cold 7 years (Glacier) | P1 |
| FR27.6 | Log cost control: sampling, truncation, aggregation | P2 |

### FR28: Change Intelligence
| ID | Requirement | Priority |
|----|------------|----------|
| FR28.1 | Pre-Change Impact Report auto-generated on Freeze/PR: includes Diff, Why, impact scope graph, data impact preview, test results, Approver list | P1 |
| FR28.2 | Post-Change Summary auto-generated after Merge: includes actual vs. design comparison, DAG diagram (change nodes highlighted), Change Log, linked documentation, Cost Profile | P1 |
| FR28.3 | AI Knowledge Agent answers any system question (business logic, code logic, data flow, dependencies, history, incidents) based on Code Graph + KB + Log | P2 |
| FR28.4 | Code Graph as underlying infrastructure: builds a complete knowledge graph — Nodes (Workflow/Job/DataSource/KB/BRD/ADR/User/Tenant/Jira/Incident) + Edges (DEPENDS_ON/READS_FROM/WRITES_TO/IMPLEMENTS/JUSTIFIED_BY/OWNED_BY/TRIGGERS, etc.) | P1 |
| FR28.5 | Code Graph continuously incrementally updated, supports natural language queries | P2 |
| FR28.6 | Impact Reports must include visualized DAG diff diagrams, human-readable | P1 |
| FR28.7 | Post-Change must detect design deviations and alert | P2 |

### FR29: AI Agent Architecture
| ID | Requirement | Priority |
|----|------------|----------|
| FR29.1 | Agent uses LLM SDK + Skill + MCP three-layer architecture | P1 |
| FR29.2 | LLM SDK is pluggable: supports OpenAI, Anthropic, open-source models, private deployments with unified interface switching | P1 |
| FR29.3 | Skill is modular: Intent Parsing / KB Retrieval / Code Graph Query / Impact Analysis / Doc Generation, etc., composable | P1 |
| FR29.4 | MCP (Model Context Protocol): standard protocol for Agent interaction with external systems (data sources, APIs, file systems) | P1 |
| FR29.5 | Skills can be composed into Agent Workflows (templated Skill combinations + System Prompt) | P2 |

> FR29 → FR1: The AI Agent technical architecture underpins the core AI-assisted exploration capabilities

### FR30: Agent Customization
| ID | Requirement | Priority |
|----|------------|----------|
| FR30.1 | Different Teams/Owners can pre-define multiple sets of Agent Workflows (e.g., Finance Team's "metric inquiry + adjustment suggestion") | P2 |
| FR30.2 | Agent Workflow as a Compute Spec type (meta-workflow), naturally inheriting FR8.1 version control and all FR13 Compute Spec capabilities | P2 |
| FR30.3 | Supports different users/Teams connecting to different AI Models (e.g., GPT-4, Claude) | P1 |
| FR30.4 | Model selection three-layer preference: Tenant-level / Group-level / Individual-level | P1 |
| FR30.5 | Models configurable by scenario: sensitive data uses private models, general Q&A uses SaaS models | P2 |

### FR31: Agent Permission Control
| ID | Requirement | Priority |
|----|------------|----------|
| FR31.1 | Agent capabilities dynamically trimmed based on user role | P0 |
| FR31.2 | Dev role: can query Code Graph + Log + ADR + Incident; cannot query Business Data (sales/customers, etc.) | P0 |
| FR31.3 | Business User role: can query KB metrics + reports + data previews; cannot modify Compute Spec code | P0 |
| FR31.4 | Reviewer role: can view full Impact Report + approve; cannot directly modify | P1 |
| FR31.5 | Agent injects user permission context before each response, filtering invisible content | P0 |
| FR31.6 | Agent actions (create Ticket, trigger Workflow) require operation permission checks | P1 |

### FR32: KB Data Model
| ID | Requirement | Priority |
|----|------------|----------|
| FR32.1 | Business Glossary: terms, aliases, definitions, formulas, business context, data source mappings, owner, approval source, version | P0 |
| FR32.2 | Data Catalog: data asset types (tables/APIs/files/streams), Schema details, column-level business meaning, PII markers, relationships, quality scores | P0 |
| FR32.3 | Mapping Registry: legacy→new system mappings, cross-currency conversion, transform logic (reversible), change history | P0 |
| FR32.4 | Workflow Template Library: template definitions, categorization, prerequisite KB requirements, parameters, usage statistics | P1 |
| FR32.5 | Adjustment History: anomaly details, root cause analysis (primary+secondary+residual), adjustment entries, approval chain, immutable at point-in-time | P1 |
| FR32.6 | User Behavior Pattern Store: operation sequences, temporal patterns, derived suggestions, confidence scores | P2 |
| FR32.7 | Report/Metric Catalog: report definitions, metric formulas, calculation granularity, certification status, relationships with data sources and Workflows | P1 |
| FR32.8 | Email Record: sender/recipient/date/subject, body hash + original storage, extracted fact list, attachment parsing, tags | P2 |

> FR32.6 → FR3: User Behavior Pattern Store provides persistent data support for system observation. FR32.7 → FR5: Report/Metric Catalog elevates reports and metrics to KB first-class citizens, enabling traceability queries. FR32.8 → FR17: Email Record provides persistent storage for email ingestion.

### FR33: KB Storage Architecture
| ID | Requirement | Priority |
|----|------------|----------|
| FR33.1 | Vector DB stores all Embeddings, supports hybrid search (semantic + keyword + metadata filtering) | P0 |
| FR33.2 | Graph DB stores KB internal relationships + KB↔Code Graph bridge edges | P1 |
| FR33.3 | Relational DB stores structured metadata, version history, permissions, approval records | P0 |
| FR33.4 | Object Store stores large objects (email originals, attachments, LLM full text, archived Specs) | P1 |
| FR33.5 | Embedding model configurable (default multilingual model, Tenant can configure private model) | P2 |

### FR34: KB Write Governance
| ID | Requirement | Priority |
|----|------------|----------|
| FR34.1 | User explicit input path: Schema scan, manual addition, AI conversation confirmation | P0 |
| FR34.2 | AI extraction + human confirmation path: Email facts, Data Profiling, Adjustment patterns | P1 |
| FR34.3 | System automatic path: behavior observation, template extraction, quality score updates, usage statistics | P2 |
| FR34.4 | All writes pass five gates: Permission Check → Versioning → Notification → Embedding Update → Graph Update | P1 |
| FR34.5 | KB entry changes auto-notify affected Workflow Owners | P1 |

### FR35: KB Read & Retrieval
| ID | Requirement | Priority |
|----|------------|----------|
| FR35.1 | Hybrid retrieval four steps: Semantic Search → Keyword Filtering → Relationship Expansion (Graph) → Fusion Ranking | P0 |
| FR35.2 | Retrieval results injected as Context into AI Prompts | P0 |
| FR35.3 | Permission-aware retrieval: different roles see different content (Dev cannot query Business Data) | P0 |
| FR35.4 | Supports natural language queries (e.g., "Why was Q3 North China gross margin abnormal?") | P1 |

### FR36: KB Governance
| ID | Requirement | Priority |
|----|------------|----------|
| FR36.1 | Each KB entry has independent version history, fully traceable | P1 |
| FR36.2 | Glossary/Mapping changes require approval + auto-notify affected Owners | P1 |
| FR36.3 | Staleness Detection: overdue detection (6 months without update), Schema change marking, Pattern mismatch confidence reduction | P2 |
| FR36.4 | KB ↔ Code Graph inconsistency auto-alert | P2 |

### FR37: Notification System
| ID | Requirement | Priority |
|----|------------|----------|
| FR37.1 | Multi-channel notifications: Email, Slack/Teams, Webhook, system built-in inbox, SMS (optional) | P1 |
| FR37.2 | Notification templating: supports variable substitution (Workflow name, execution time, status, error details) | P1 |
| FR37.3 | Notification priority & tiering: Critical (instant + multi-channel), Warning (aggregated summary), Info (batched) | P1 |
| FR37.4 | User notification preference configuration: subscribe to which event types, delivery channel, do-not-disturb hours | P2 |
| FR37.5 | Notification delivery guarantee: at-least-once delivery; Critical event delivery failure auto-escalates | P1 |
| FR37.6 | Notification linked with Incident Management: auto-generate Incident Link with alert context | P1 |

### FR38: API Gateway
| ID | Requirement | Priority |
|----|------------|----------|
| FR38.1 | Unified API entry point (RESTful, gRPC) | P1 |
| FR38.2 | Per-tenant/user/role Rate Limiting, supports burst and quota modes | P1 |
| FR38.3 | Request routing & load balancing: forward requests to Design Plane or Runtime Plane corresponding services | P1 |
| FR38.4 | Tenant isolation: each tenant's API calls identified in request path or Header; gateway enforces isolation validation | P0 |
| FR38.5 | API version management: URL-based and Header-based version strategies | P1 |
| FR38.6 | Request/response logging: each API call logged (timestamp, tenant, user, endpoint, latency, status) | P1 |
| FR38.7 | API authentication: integrates OAuth 2.0 / API Key / JWT validation, unified Token verification | P1 |

### FR39: Scheduler
| ID | Requirement | Priority |
|----|------------|----------|
| FR39.1 | Trigger types: Cron/scheduled, dependency-triggered (upstream complete → downstream start), event-triggered (file arrival/Webhook), manual trigger | P1 |
| FR39.2 | Timezone-aware: each Tenant / Workflow can specify independent timezone with correct DST handling | P1 |
| FR39.3 | Concurrency control: same Workflow concurrent instance limit (global/Group/single-Workflow three-tier) | P1 |
| FR39.4 | Missed Execution Catch-up strategies: Alarm & Skip / Immediate Catch-up / Scheduled Catch-up | P2 |
| FR39.5 | Scheduling Calendar: supports holidays/trading calendars, can skip/delay specified dates | P2 |
| FR39.6 | Workflow execution sequencing: supports serial chains, parallel groups, conditional branches | P1 |

### FR40: Runtime Dependency Manager
| ID | Requirement | Priority |
|----|------------|----------|
| FR40.1 | Auto-discovers cross-Workflow data dependency relationships (upstream output → downstream input) | P1 |
| FR40.2 | Dependency topology visualization: DAG diagram showing cross-Workflow data flows and execution order | P2 |
| FR40.3 | Upstream change impact alert: when upstream Workflow/DataSource changes, auto-notify downstream Owners | P1 |
| FR40.4 | Dependency version snapshots: each execution records its dependent Workflow version, DataSource Schema version | P2 |
| FR40.5 | Deprecation marking & migration suggestions: mark outdated dependencies, suggest alternatives | P2 |
| FR40.6 | Integrated with Change Intelligence: Impact Reports show cross-Workflow impact chains | P2 |

### FR41: Backup & Disaster Recovery
| ID | Requirement | Priority |
|----|------------|----------|
| FR41.1 | Backup scope: Compute Spec / Workflow Script / KB full / Audit Log / Configuration | P1 |
| FR41.2 | RPO (Recovery Point Objective): core data (Spec + KB) < 1 hour, audit logs < 24 hours | P1 |
| FR41.3 | RTO (Recovery Time Objective): core services < 4 hours, non-critical services < 24 hours | P1 |
| FR41.4 | Backup storage: offsite multi-copy, cross-region redundancy, immutable backups (ransomware protection) | P1 |
| FR41.5 | Periodic recovery drills: at least one full recovery test per quarter, results auto-recorded | P2 |
| FR41.6 | Backup data encryption: encryption in transit + encryption at rest, keys independently managed | P1 |
| FR41.7 | Tenant-level backup & recovery: supports isolated backup and independent recovery for individual tenant data | P2 |

### FR42: System Configuration Management
| ID | Requirement | Priority |
|----|------------|----------|
| FR42.1 | Feature Flags: feature toggle management supporting per-tenant/Group/user granularity canary release and emergency shutdown | P2 |
| FR42.2 | Tenant Configuration: tenant-level configuration center supporting runtime hot updates (without service restart) | P2 |
| FR42.3 | Environment Variables layered management (Global → Tenant → Group → Workflow), supporting sensitive value encrypted storage | P2 |
| FR42.4 | All configuration changes under version control (Git), supporting change audit, Diff comparison, and rollback | P2 |

### FR43: KB Content Processing Pipeline → adr/0023
| ID | Requirement | Priority |
|----|------------|----------|
| FR43.1 | All heterogeneous content sources (Email, DOCX/XLSX/PDF upload, API push, paste) converge into a single unified processing funnel — no per-channel ad-hoc pipelines | P1 |
| FR43.2 | Structure-aware semantic chunking (split on headings/paragraphs/table boundaries; tables stay intact as single chunks); not fixed-length chunking | P1 |
| FR43.3 | Contextual Retrieval enhancement: each chunk is prepended with an LLM-generated context summary before embedding; the same summary is indexed into the BM25 keyword index | P1 |
| FR43.4 | Four indexes (pgvector HNSW + tsvector GIN + native tables + edge tables) written in a single ACID transaction; original blob stored in S3 with PG object key | P1 |
| FR43.5 | Immutable provenance tagging per chunk: source_doc_id, source_span, ingest_time, ingest_channel, extractor, confidence — satisfying FR17.5 traceability and SOX audit | P1 |

### FR44: KB Linkage & Quality → adr/0023
| ID | Requirement | Priority |
|----|------------|----------|
| FR44.1 | Linkage Weaving: automatic generation of MENTIONS_ENTITY (entity co-reference) and SIMILAR_TO (semantic similarity > 0.85 + NLI non-contradiction) edges on ingest; DERIVED_FROM (structural lineage) edges require L2 human confirmation | P1 |
| FR44.2 | Near-duplicate detection across channels (SimHash/MinHash); forwarded email chains merge into one canonical record + reference list | P2 |
| FR44.3 | Conflict detection: new fact vs existing KB fact → NLI contradiction → marked `conflict`, frozen, human adjudication (never auto-overwrite) | P1 |
| FR44.4 | Freshness decay: each chunk carries a configurable half_life by content type (definitions 2yr / snapshots 30d / email 180d); stale chunks are down-ranked at retrieval, not deleted (bitemporal retention) | P2 |
| FR44.5 | Offline retrieval-quality evaluation (RAGAS-family metrics: context_precision/recall/faithfulness) on ADR-0018 Golden Dataset; quality regression triggers re-embedding or re-chunking of affected domain | P2 |

### FR45: Diagnostic Playbooks → adr/0024
| ID | Requirement | Priority |
|----|------------|----------|
| FR45.1 | Diagnostic Playbooks KB domain: stores expert-encoded IF/THEN diagnostic decision trees that guide Agent reasoning in Exploration Mode (soft skeleton) | P1 |
| FR45.2 | Three playbook sources with confidence tagging (align ADR-0019): system-builtin (conf 1.0), incident-distilled (model_inferred, promoted after ≥3 recurrences + human confirm), user-defined (user_stated, conf 1.0) | P1 |
| FR45.3 | Two routing paths: explicit (S01 IntentParser matches playbook trigger → inject as guided plan) and implicit (S02 retrieval mid-ReAct as reference); no-match → pure ReAct fallback (backward compatible) | P1 |
| FR45.4 | Closed-loop learning: successful diagnostic trajectories stored in L2 Episodic Memory; ≥3 recurrences → LLM proposes distillation into new playbook candidate → user confirms → promoted (reuses S08 pattern + ADR-0019 promotion rules) | P2 |

### FR46: Code Knowledge Index → adr/0024
| ID | Requirement | Priority |
|----|------------|----------|
| FR46.1 | Code Knowledge KB domain: three-layer index over code artifacts (Compute Spec YAML, Sandbox Python, Git history, external repos) — structural (Code Graph nodes/edges), semantic (function-level embeddings), change (commits/blame/diffs) | P1 |
| FR46.2 | Event-driven ingestion keeps the index correlated (not batch-rebuilt): Freeze Bridge merge → re-parse Spec; Sandbox exec → static analysis → function nodes + CALLS edges; git push webhook → update changed nodes/embeddings; PR merge → LLM extracts change rationale → linked to Spec | P1 |
| FR46.3 | Bridge edges link Code Knowledge to existing graphs: Function —IMPLEMENTS→ CodeGraph.Job; Function —REFERENCES→ KB.GlossaryEntry; Commit —MODIFIES→ CodeGraph.Spec | P1 |
| FR46.4 | Semantic code search via MCP-23 (code-knowledge-search): find functions by meaning (not name); full function retrieval with caller/callee; call-graph subgraph export; find similar code | P1 |

---

## Requirements-Phase Traceability Matrix

> **Matrix Notes**: This matrix annotates the target delivery phase for each FR group. P0 sub-items within a group may be delivered as "thin slices" in earlier phases (e.g., FR7.4 delivers basic Adjustment capabilities in P0 Foundation, but the complete Adjustment flow is delivered in P7 Advanced; FR9 core RBAC is delivered in P6 Enterprise, but basic authentication integration already has Auth Gateway in P0 Foundation). See per-FR priority annotations within each group for specific sub-item-to-phase mapping.

| FR Group | Requirement Theme | Phase 0: Foundation | Phase 1: Core Compute | Phase 2: KB | Phase 3: Design Plane | Phase 4: Freeze Bridge | Phase 5: Runtime | Phase 6: Enterprise | Phase 7: Advanced | Phase 8: Polish |
|----------|-----------------|---------------|------------------|--------|-----------------|-------------------|-------------|----------------|--------------|------------|
| FR1 | AI-Assisted Exploration | ✅ | — | — | — | — | — | — | — | — |
| FR2 | Workflow Freeze & Script | ✅ | — | — | — | — | — | — | — | — |
| FR3 | Observation & Suggestion | — | — | — | — | — | — | — | ✅ | — |
| FR4 | Knowledge Base | — | — | ✅ | — | — | — | — | — | — |
| FR5 | Reporting | — | — | — | ✅ | — | — | — | — | — |
| FR5b | Dashboard | — | — | — | — | — | — | — | ✅ | — |
| FR6 | ETL Workflow | — | — | — | ✅ | — | — | — | — | — |
| FR7 | Adjustment | ✅ (basic) | — | — | — | — | — | — | ✅ | — |
| FR8 | Enterprise SDLC | — | — | — | — | ✅ | — | — | — | — |
| FR9 | Entitlement Control | — | — | — | — | — | — | ✅ | — | — |
| FR10 | Audit & Compliance | — | — | — | — | — | — | ✅ | — | — |
| FR11 | Integration | — | ✅ | — | — | — | — | — | — | — |
| FR12 | Multi-tenancy | — | — | — | — | — | — | ✅ | — | — |
| FR13 | Compute Spec | ✅ | — | — | — | — | — | — | — | — |
| FR14 | Dual Engine | ✅ | — | — | — | — | — | — | — | — |
| FR15 | Integration Framework | ✅ | — | — | — | — | — | — | — | — |
| FR15b | Query Service | — | ✅ | — | — | — | — | — | — | — |
| FR15c | Large-Scale Data | — | — | — | — | — | ✅ | — | — | — |
| FR16 | Data Masking & RLS | — | — | — | — | — | — | ✅ | — | — |
| FR17 | Email Ingestion | — | — | — | — | — | — | — | ✅ | — |
| FR18 | Reconciliation | — | — | — | — | — | — | ✅ | — | — |
| FR19 | Data Quality Check | — | — | — | — | — | — | ✅ | — | — |
| FR20 | DevOps & CI/CD | — | — | — | — | ✅ | — | — | — | — |
| FR21 | Support & Ticket | — | — | — | — | — | — | ✅ | — | — |
| FR22 | Project Tracking | — | — | — | — | — | — | ✅ | — | — |
| FR23 | BRD & ADR | — | — | — | — | — | — | ✅ | — | — |
| FR24 | Format System | — | ✅ | — | — | — | — | — | — | — |
| FR25 | Writeback Job | — | — | — | — | — | ✅ | — | — | — |
| FR26 | Execution Sandbox | — | — | — | — | — | ✅ | — | — | — |
| FR27 | Log System | — | — | — | — | — | ✅ | — | — | — |
| FR28 | Change Intelligence | — | — | — | — | — | — | — | ✅ | — |
| FR29 | AI Agent Architecture | — | — | — | ✅ | — | — | — | — | — |
| FR30 | Agent Customization | — | — | — | — | — | — | — | ✅ | — |
| FR31 | Agent Permission | — | — | — | — | — | — | ✅ | — | — |
| FR32 | KB Data Model | — | — | ✅ | — | — | — | — | — | — |
| FR33 | KB Storage | — | — | ✅ | — | — | — | — | — | — |
| FR34 | KB Write Governance | — | — | ✅ | — | — | — | — | — | — |
| FR35 | KB Read & Retrieval | — | — | ✅ | — | — | — | — | — | — |
| FR36 | KB Governance | — | — | — | — | — | — | ✅ | — | — |
| FR37 | Notification | — | — | — | — | — | — | ✅ | — | — |
| FR38 | API Gateway | — | — | — | — | — | — | ✅ | — | — |
| FR39 | Scheduler | — | — | — | — | — | ✅ | — | — | — |
| FR40 | Dependency Manager | — | — | — | — | — | — | — | ✅ | — |
| FR41 | Backup & DR | — | — | — | — | — | — | ✅ | — | — |
| FR42 | Config Management | — | — | — | — | — | — | ✅ | — | — |
| FR43 | KB Content Processing Pipeline | — | — | ✅ | — | — | — | — | — | — |
| FR44 | KB Linkage & Quality | — | — | ✅ | — | — | — | — | — | — |
| FR45 | Diagnostic Playbooks | — | — | ✅ | — | — | — | — | ✅ | — |
| FR46 | Code Knowledge Index | — | — | ✅ | — | — | — | — | ✅ | — |

---

*Last Updated: 2026-07-04*
