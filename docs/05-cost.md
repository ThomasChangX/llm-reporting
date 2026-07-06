# 05 - Cost Analysis

> Full lifecycle cost assessment for system development and operations.
>
> Covers: development phase costs, runtime operational costs, different scale scenarios, pricing model reference, cost optimization strategies.

---

## 1. Cost Model Overview

System costs are divided into three major categories:

| Category | Description | Billing Method |
| -------------------- | --------------------- | ----------------------------- |
| **A. Development Cost** | One-time investment, 8-month cycle | Fixed (personnel + LLM + infrastructure) |
| **B. Runtime Infrastructure** | Monthly fixed + elastic | Usage-based (tenant count / data volume / compute) |
| **C. Runtime LLM Cost** | Per invocation | Per-token / Per-request |

Core cost advantage: **Zero LLM execution cost after Freezing**. Design Plane uses AI for exploration, Runtime Plane uses deterministic scripts — this is the fundamental difference from traditional "AI-driven BI" products.

---

## 2. A: Development Phase Costs

### 2.1 Personnel Costs

**Option 1: US/Global Team**

| Role | FTE | Monthly Cost (USD, prorated) | 8-Month Cost |
| ------------------------------------------ | --------- | ---------- | ------------ |
| Senior Full-Stack Developer (AI-Assisted) | 2.0 | $14,000 | $224,000 |
| Senior Backend/Data Engineer (AI-Assisted) | 1.0 | $13,500 | $108,000 |
| Domain Expert (Finance/BI, Part-time) | 0.5 | $6,000 | $48,000 |
| DevOps Engineer (Part-time) | 0.5 | $6,500 | $52,000 |
| **Subtotal** | **4.0 FTE** | | **$432,000** |

> **Salary Note**: "Monthly Cost" is the effective monthly cost for the stated FTE fraction (already prorated for part-time roles — e.g., the Domain Expert at 0.5 FTE costs $6,000/mo, equivalent to a $12,000/mo full-time rate). Figures are pre-tax. Actual enterprise employment costs must include employer burdens (US: FICA 7.65%, Health Insurance ~$500-1,200/mo/person, 401k match 3-6%, Workers' Comp, PTO etc. ≈ +25-35%; China: ~84-91% total burden — Five Insurances + Housing Fund ~35%, plus supplementary benefits, office space, equipment, management overhead, and other indirect costs). With burdens: US ~$540,000-583,000, China ~¥1,971,000-2,044,000 (~$274,000-284,000). Operations personnel costs in TCO calculations below should be proportionally adjusted upward.

**Option 2: China Team**
| Role | FTE | Monthly Cost (CNY, prorated) | 8-Month Cost |
| ------------------------------------------ | --------- | ---------- | ------------ |
| Senior Full-Stack Developer (AI-Assisted) | 2.0 | ¥35,000 | ¥560,000 |
| Senior Backend/Data Engineer (AI-Assisted) | 1.0 | ¥33,000 | ¥264,000 |
| Domain Expert (Finance/BI, Part-time) | 0.5 | ¥15,000 | ¥120,000 |
| DevOps Engineer (Part-time) | 0.5 | ¥16,000 | ¥128,000 |
| **Subtotal** | **4.0 FTE** | | **¥1,072,000 (~$149,000)** |

### 2.2 LLM API Costs (Development Phase)

> **Status**: Cost model defined; actual token volume estimates pending Phase 0-2 velocity calibration. See docs/04-timeline.md §D for per-phase token budget placeholders.

**Purpose**: Estimate LLM API costs incurred during the 8-month development cycle. Development-phase LLM usage falls into two categories: (a) Sub-Agent parallel code generation (the Token-Speed development methodology in docs/04-timeline.md §A-B), and (b) Architecture/design exploration by human engineers interacting with AI Copilot tools. Both are priced per ADR-0009 (Dual-Model Strategy).

#### 2.2.1 Development Code Generation Costs (Sub-Agent Parallelism)

**Model**: Costs are estimated for both the China team (DeepSeek V4 Pro) and US team (Claude Sonnet 5) baselines, per ADR-0009.

| Phase | Est. Total Tokens (DeepSeek) | Input Cost (DeepSeek, $0.50/M) | Output Cost (DeepSeek, $2.00/M) | Total LLM Cost (DeepSeek) | Est. Total Tokens (Claude) | Input Cost (Claude, $3.00/M) | Output Cost (Claude, $15.00/M) | Total LLM Cost (Claude) |
|-------|------------------------------|-------------------------------|--------------------------------|--------------------------|----------------------------|------------------------------|-------------------------------|-------------------------|
| 0: Foundation | 1.0M (0.7M in / 0.3M out) | $0.35 | $0.60 | $0.95 | 1.0M (0.7M in / 0.3M out) | $2.10 | $4.50 | $6.60 |
| 1: Core Compute | 8.3M (5.5M in / 2.8M out) | $2.75 | $5.60 | $8.35 | 8.3M (5.5M in / 2.8M out) | $16.50 | $42.00 | $58.50 |
| 2: KB | 4.1M (2.7M in / 1.4M out) | $1.35 | $2.80 | $4.15 | 4.1M (2.7M in / 1.4M out) | $8.10 | $21.00 | $29.10 |
| 3: Design Plane | 7.9M (5.3M in / 2.6M out) | $2.65 | $5.20 | $7.85 | 7.9M (5.3M in / 2.6M out) | $15.90 | $39.00 | $54.90 |
| 4: Freeze Bridge | 7.8M (5.2M in / 2.6M out) | $2.60 | $5.20 | $7.80 | 7.8M (5.2M in / 2.6M out) | $15.60 | $39.00 | $54.60 |
| 5: Runtime | 12.2M (8.1M in / 4.1M out) | $4.05 | $8.20 | $12.25 | 12.2M (8.1M in / 4.1M out) | $24.30 | $61.50 | $85.80 |
| 6: Enterprise | 14.7M (9.8M in / 4.9M out) | $4.90 | $9.80 | $14.70 | 14.7M (9.8M in / 4.9M out) | $29.40 | $73.50 | $102.90 |
| 7: Advanced | 18.4M (12.3M in / 6.1M out) | $6.15 | $12.20 | $18.35 | 18.4M (12.3M in / 6.1M out) | $36.90 | $91.50 | $128.40 |
| 8: Polish & Launch | 3.9M (2.6M in / 1.3M out) | $1.30 | $2.60 | $3.90 | 3.9M (2.6M in / 1.3M out) | $7.80 | $19.50 | $27.30 |
| **Subtotal (Code Gen)** | **78.3M (52.2M in / 26.1M out)** | **$26.10** | **$52.20** | **$78.30** | **78.3M (52.2M in / 26.1M out)** | **$156.60** | **$391.50** | **$548.10** |

**Assumptions**:
- Input/Output token ratio: ~2:1 averaged across all task tiers (T1 tasks skew high-input; T4 tasks skew high-output due to multi-iteration generation)
- Agent scheduling tax (+27.5%: Orchestrator ~17.5% + Reviewer ~10%) included in all token estimates (docs/04-timeline.md §B.1)
- Parallelism factors per phase as defined in docs/04-timeline.md §B.2.5
- Token estimates assume median iteration counts per Tier (T1=1, T2=2.5, T3=4, T4=6.5)

**Pricing Reference** (ADR-0009):
- DeepSeek V4 Pro (China region): Input $0.50/M tokens, Output $2.00/M tokens
- Claude Sonnet 5 (US region): Input $3.00/M tokens, Output $15.00/M tokens

#### 2.2.2 Design/Architecture Exploration LLM Costs

Human engineers interact with AI Copilot tools (ChatGPT, Claude, Cursor, Copilot) during architecture design, code review, and debugging. These are separate from the Sub-Agent code generation pipeline.

| Activity | Model(s) | Est. Monthly Tokens per Engineer | Est. Monthly Cost per Engineer | Engineers | Monthly Cost | 8-Month Cost |
|----------|----------|--------------------------------|-------------------------------|-----------|-------------|-------------|
| Architecture Design (BRD/ADR drafting) | Claude Sonnet 5 | ~2M | ~$36 | 3 | $108 | $864 |
| Code Review & Debugging | Claude Sonnet 5 / GPT-4 | ~3M | ~$54 | 4 | $216 | $1,728 |
| KB Entry Authoring & Validation | DeepSeek V4 Pro | ~1M | ~$1.25 | 2 | $3 | $20 |
| Documentation & Diagram Generation | Claude Sonnet 5 | ~1.5M | ~$27 | 2 | $54 | $432 |
| **Subtotal (Design Exploration)** | — | — | — | — | **~$381/mo** | **~$3,044** |

#### 2.2.3 Agent Evaluation & CI Regression Costs (ADR-0018, ADR-0020)

CI regression gates run model evaluation on a Golden Dataset before every model upgrade deployment. These are recurring operational costs, not one-time development costs.

| Evaluation Activity | Model | Est. Tokens per Run | Cost per Run | Runs per Month | Monthly Cost |
|---------------------|-------|---------------------|-------------|----------------|-------------|
| Golden Dataset validation (full) | Both models | ~2M | ~$16 | 4 | ~$64 |
| Shadow mode comparison (new vs. current) | Both models | ~1M | ~$8 | 4 | ~$32 |
| Rubric scoring (per ADR-0018) | Claude Sonnet 5 | ~1M | ~$15 | 4 | ~$60 |
| **Subtotal (Evaluation)** | — | — | — | — | **~$156/mo** |

#### 2.2.4 Development Phase LLM Cost Summary

| Cost Category | DeepSeek V4 Pro (China) | Claude Sonnet 5 (US) | Notes |
|---------------|------------------------|---------------------|-------|
| Code Generation (Sub-Agent) | $78.30 | $548.10 | Per-phase breakdown in §2.2.1 |
| Design Exploration (Human) | $3,044 | $3,044 | Per-activity breakdown in §2.2.2 |
| Agent Evaluation (CI) | $100 | $1,100 | Recurring monthly during development (8 mo) |
| **Total Development LLM Cost** | **$3,222** | **$4,692** | China ~69% of US cost per ADR-0009 |

> **Key Insight per ADR-0009**: Using DeepSeek V4 Pro for bulk Sub-Agent parallel tasks and reserving Claude Sonnet 5 for Tier 3-4 complex reasoning tasks is the recommended cost-optimization strategy. A blended approach (DeepSeek for T1-T2, Claude for T3-T4) may reduce total LLM cost by 40-60% vs. all-Claude, while preserving quality on complex tasks.

---

### 2.3 Development Infrastructure Costs

> **Status**: Cost model defined; resource sizing and provider selection pending Phase 0 environment setup.

**Purpose**: Estimate cloud infrastructure costs consumed during the 8-month development cycle — development VMs/containers, CI/CD runners, sandbox environments, monitoring, and collaboration tools.

#### 2.3.1 Compute Resources (Development & CI/CD)

| Resource | Spec | Quantity | Unit Cost (Monthly) | Monthly Cost | 8-Month Cost | Provider Options |
|----------|------|----------|---------------------|-------------|-------------|-----------------|
| Developer VMs / Cloud Workstations | 8 vCPU, 32 GB RAM, 256 GB SSD | 4 (1 per engineer) | $274 | $1,096 | $8,768 | AWS EC2 / Alibaba Cloud ECS / GCP Compute |
| CI/CD Runner Instances | 4 vCPU, 16 GB RAM (spot/preemptible) | 3 (concurrent PR capacity) | $82 (spot, ~60% off) | $246 | $1,968 | GitHub Actions / GitLab CI / Jenkins |
| Per-PR Sandbox Environments | 2 vCPU, 8 GB RAM (ephemeral) | 5 (avg. concurrent PRs) | $68 (prorated, short-lived) | $340 | $2,720 | Kubernetes (namespace-isolated) |
| Test Runner Sandbox Pool | 4 vCPU, 16 GB RAM (pre-warmed) | 4 | $137 | $548 | $4,384 | Kubernetes / Docker Compose |
| **Subtotal Compute** | — | — | — | **$2,230/mo** | **$17,840** | — |

> **Sandbox Policy**: Per-PR sandboxes are auto-created on PR open and auto-destroyed on PR merge/close (FR20.2). Estimated lifespan: 2-5 days average.

#### 2.3.2 Storage & Data (Development)

| Resource | Spec | Quantity | Unit Cost | Monthly Cost | 8-Month Cost |
|----------|------|----------|-----------|-------------|-------------|
| PostgreSQL (KB Dev) | db.r6g.large equivalent, 100 GB | 1 instance (shared dev) | $187 | $187 | $1,496 |
| pgvector Extension | Included in PG instance | — | $0 (built-in) | $0 | $0 |
| S3/MinIO (Object Store Dev) | 500 GB, infrequent access | 1 bucket | ~$0.03/GB (IA tier) | ~$15 | $120 |
| Redis (Cache Dev) | cache.t4g.small equivalent | 1 instance | $20 | $20 | $160 |
| Git Repository Storage | GitHub/GitLab (private repo) | 1 org/repo | $4/user/mo (4 users) | $16 | $128 |
| Container Registry | Docker/OCI images | ~100 GB | ~$0.10/GB | ~$10 | $80 |
| **Subtotal Storage** | — | — | — | **$248/mo** | **$1,984** |

#### 2.3.3 Networking (Development)

| Resource | Spec | Monthly Cost | 8-Month Cost |
|----------|------|-------------|-------------|
| VPC / VNet | Private network for dev resources | $0 (free tier) | $0 |
| NAT Gateway / Egress | Outbound internet for package downloads, API calls | $37 (~$32 base + ~1 GB egress) | $296 |
| Load Balancer (Dev) | For API Gateway dev testing | $25 | $200 |
| Data Transfer | Inter-AZ and egress for dev workloads | ~$20 | $160 |
| **Subtotal Networking** | — | **$82/mo** | **$656** |

#### 2.3.4 Tooling & Services (Development)

| Tool / Service | Purpose | Pricing Model | Monthly Cost | 8-Month Cost |
|---------------|---------|---------------|-------------|-------------|
| GitHub / GitLab (Team plan) | Source control, CI/CD, PR workflow | Per-user/month ($4/user) | $16 | $128 |
| Docker Hub / ECR | Container registry | Free tier (Docker Hub) | $0 | $0 |
| Monitoring (Grafana/Prometheus/Datadog) | Dev environment observability | Free tier (Grafana Cloud, 10K series) | $0 | $0 |
| Log Aggregation (Elasticsearch/Loki) | Centralized dev logging | Free tier (Grafana Loki, 50 GB) | $0 | $0 |
| Incident / Ticket System (Jira/Linear) | Task tracking, issue management | Per-user/month ($8/user) | $32 | $256 |
| Documentation (Notion/Confluence) | Design docs, meeting notes | Per-user/month ($10/user) | $40 | $320 |
| Communication (Slack/Teams) | Team communication | Per-user/month ($7.25/user) | $29 | $232 |
| API Development Tools (Postman/Bruno) | API testing, documentation | Per-user/month ($19/user, 3 users) | $57 | $456 |
| **Subtotal Tooling** | — | — | **$174/mo** | **$1,392** |

#### 2.3.5 Development Infrastructure Cost Summary

| Category | Monthly Cost | 8-Month Cost | Notes |
|----------|-------------|-------------|-------|
| Compute (VMs + CI/CD + Sandboxes) | $2,230 | $17,840 | Sandboxes are ephemeral; estimate avg. concurrency, not peak |
| Storage (PG + S3 + Redis + Git + Registry) | $248 | $1,984 | Dev data sizes are small; costs dominated by compute |
| Networking | $82 | $656 | Egress for LLM API calls is negligible vs. compute |
| Tooling & Services | $174 | $1,392 | Per-user SaaS costs scale with team size |
| **Total Development Infrastructure** | **$2,734/mo** | **$21,872** | China cloud (Alibaba Cloud) ~$1,454/mo, 8-mo ~$11,632 (~50% of AWS) |

> **China Team Note**: Alibaba Cloud / Tencent Cloud pricing is approximately 40-60% of AWS US list prices for equivalent compute and storage resources. Both provider options should be evaluated.

---

## 3. B: Runtime Infrastructure Costs

> **Status**: Cost model defined; sizing estimated based on three reference scenarios (Small/Medium/Large). Actual sizing will be calibrated during customer discovery.

**Purpose**: Estimate ongoing operational infrastructure costs for the Runtime Plane (deterministic, zero-AI-side-effect execution). Costs scale primarily with tenant count, data volume, and workflow execution frequency — not with LLM invocation volume (which is zero in Runtime Plane per architecture §2).

**Reference Architecture**: docs/03-architecture.md §5 (Runtime Plane), §5.1 (Resilience Patterns), §5.2 (Data Classification Tiers).

### 3.1 Compute Resources (Runtime)

| Resource | Spec | Scaling Model | Small (≤ 10 tenants) | Medium (≤ 100 tenants) | Large (≤ 1000 tenants) |
|----------|------|--------------|----------------------|------------------------|------------------------|
| Workflow Executor Nodes | 8 vCPU, 32 GB RAM per node | Horizontal (per tenant concurrency) | 2 nodes × $274 = $548 | 5 nodes × $274 = $1,370 | 15 nodes × $274 = $4,110 |
| Job Sandbox Pool | 2-4 vCPU, 8-16 GB RAM per sandbox | Pre-warmed pool, elastic | 10 sandboxes × ~$50 = $500 | 30 sandboxes × ~$50 = $1,500 | 100 sandboxes × ~$50 = $5,000 |
| Scheduler Nodes | 4 vCPU, 16 GB RAM | 2 nodes (HA pair) | 2 × $137 = $274 | 2 × $137 = $274 | 3 × $137 = $411 |
| API Gateway Nodes | 4 vCPU, 16 GB RAM | Horizontal (per request rate) | 2 nodes × $137 = $274 | 4 nodes × $137 = $548 | 10 nodes × $137 = $1,370 |
| Query Service Nodes | 4 vCPU, 16 GB RAM | Horizontal (per query volume) | 2 nodes × $137 = $274 | 4 nodes × $137 = $548 | 8 nodes × $137 = $1,096 |
| Heavy Engine (Spark) | Per-job cluster (post-MVP) | Elastic (per job, auto-terminate) | N/A (post-MVP) | $500 (spot, occasional) | $2,000 (spot, regular) |
| **Subtotal Compute** | — | — | **$1,870/mo** | **$4,740/mo** | **$13,987/mo** |

> **Kubernetes Assumption**: All Runtime components deployed on Kubernetes (AWS EKS / Azure AKS / GCP GKE / Alibaba ACK). Node costs above assume Kubernetes worker node pricing. Control plane cost included.

### 3.2 Storage Resources (Runtime)

| Resource | Spec | Scaling Model | Small | Medium | Large |
|----------|------|--------------|-------|--------|-------|
| PostgreSQL (KB Prod) | db.r6g.xlarge, 500 GB — 5 TB | Vertical + read replicas | $374/mo | $748/mo | $1,870/mo |
| pgvector (KB Prod) | Included in PG instance | — | $0 | $0 | $0 |
| S3/MinIO (Object Store) | 1 TB — 100+ TB, tiered (Hot/Warm/Cold) | Per GB stored + API calls | ~$30/mo | ~$250/mo | ~$2,000/mo |
| Redis / ElastiCache | cache.t4g.medium — r6g.large | Vertical + cluster mode | $47/mo | $137/mo | $467/mo |
| Log Storage (Elasticsearch) | Hot 7d (SSD) + Warm 90d (S3) + Cold 7yr (Glacier) | Per GB ingested, tiered retention (FR27.5) | ~$150/mo | ~$600/mo | ~$3,500/mo |
| Audit Log Storage | Immutable, WORM-compliant | Per GB, 7-year retention (FR10, NFR9.1) | ~$15/mo | ~$100/mo | ~$800/mo |
| Backup Storage | Offsite multi-copy, cross-region (FR41.4) | Per GB, daily snapshots | ~$30/mo | ~$200/mo | ~$1,500/mo |
| Container Registry (Prod) | Docker/OCI images for deployment | Per GB stored | ~$5/mo | ~$20/mo | ~$80/mo |
| **Subtotal Storage** | — | — | **$651/mo** | **$2,055/mo** | **$10,217/mo** |

### 3.3 Networking (Runtime)

| Resource | Scaling Model | Small | Medium | Large |
|----------|--------------|-------|--------|-------|
| VPC / VNet | Fixed per region | $0/mo | $0/mo | $0/mo |
| Load Balancer (ALB/NLB) | Per 1M requests | $30/mo | $60/mo | $150/mo |
| NAT Gateway | Per GB egress | $50/mo | $100/mo | $250/mo |
| Cross-AZ Data Transfer | Per GB | $50/mo | $150/mo | $500/mo |
| Internet Egress (API responses, file delivery) | Per GB | $50/mo | $200/mo | $800/mo |
| CDN (CloudFront/CloudFlare) | Per GB served | $30/mo | $150/mo | $600/mo |
| Private Link / VPC Endpoints | Per endpoint | $30/mo | $60/mo | $120/mo |
| **Subtotal Networking** | — | **$240/mo** | **$720/mo** | **$2,420/mo** |

### 3.4 Multi-Tenant Isolation Premium

Per FR12 and architecture §5.1 (Bulkhead pattern), tenants can select isolation levels. Higher isolation = higher cost.

| Isolation Level | Mechanism | Cost Premium vs. Shared | Applicable Tenant Types |
|----------------|-----------|------------------------|------------------------|
| **Process Isolation** | cgroups + namespace per Job | 1.0× (baseline) | Individual, small Team |
| **Node Isolation** | Dedicated Kubernetes nodes per tenant | 1.3-1.5× | SMB, privacy-sensitive |
| **Cluster Isolation** | Separate K8s cluster per tenant | 2.0-3.0× | Large Enterprise, regulated industry |

### 3.5 Runtime Infrastructure Cost Summary

| Category | Small (≤ 10 tenants) | Medium (≤ 100 tenants) | Large (≤ 1000 tenants) |
|----------|---------------------|------------------------|------------------------|
| Compute | $1,870/mo | $4,740/mo | $13,987/mo |
| Storage | $651/mo | $2,055/mo | $10,217/mo |
| Networking | $240/mo | $720/mo | $2,420/mo |
| Isolation Premium | $150/mo | $500/mo | $2,000/mo |
| **Total Runtime Infrastructure** | **$2,911/mo** | **$8,015/mo** | **$28,624/mo** |
| **Annual Runtime Infrastructure** | **$34,932/yr** | **$96,180/yr** | **$343,488/yr** |

---

## 4. C: Runtime LLM Costs

> **Status**: Cost model defined; invocation volumes estimated across three reference scenarios (Small/Medium/Large). Actual volumes will be validated during customer discovery.

**Purpose**: Estimate ongoing LLM API costs during system operation. Per architecture §2, **Runtime Plane has zero LLM cost** (deterministic execution). LLM costs accrue only in the Design Plane (AI-assisted exploration) and Intelligence Plane (read-only AI analysis).

**Reference Architecture**: docs/03-architecture.md §3 (Design Plane), §3.4 (AI Copilot Engine); §2 (Panoramic Architecture — Intelligence Plane).

### 4.1 Design Plane LLM Costs (Per-User Exploration)

Each user interaction in the Design Plane (NL→report, NL→ETL, NL→adjustment suggestion) invokes the AI Copilot Engine pipeline: Intent Parser → Context Resolver → Plan Generator → Artifact Builder.

| Agent/Skill | Model | Est. Input Tokens per Invocation | Est. Output Tokens per Invocation | Cost per Invocation (DeepSeek) | Cost per Invocation (Claude) |
|-------------|-------|----------------------------------|-----------------------------------|-------------------------------|------------------------------|
| Intent Parser (classification) | DeepSeek V4 Pro | 2,000 | 200 | $0.0014 | $0.0090 |
| Context Resolver (KB hybrid search) | Embedding model | 1,500 (embedding tokens) | — | $0.0002 | $0.0002 |
| Plan Generator (structured plan) | DeepSeek V4 Pro / Claude Sonnet 5 | 8,000 | 2,000 | $0.0080 | $0.0540 |
| Artifact Builder (Spec generation) | DeepSeek V4 Pro / Claude Sonnet 5 | 12,000 | 5,000 | $0.0160 | $0.1110 |
| BRD Generation (ADR-0022 pipeline) | Claude Sonnet 5 | 25,000 | 10,000 | — | $0.2250 |
| Fuzzy Node Resolution (Freeze Bridge) | Claude Sonnet 5 | 15,000 | 4,000 | — | $0.1050 |
| Pre/Post-Change Impact Report | Claude Sonnet 5 | 20,000 | 8,000 | — | $0.1800 |
| **Average per Exploration Session** | — | **20,000** | **6,000** | **~$0.022** | **~$0.150** |

### 4.2 Design Plane Usage Scenarios

| Tenant Size | Active Analysts | Avg. Explorations per Analyst per Day | Daily Invocations | Monthly Invocations (22 workdays) | Monthly LLM Cost (DeepSeek) | Monthly LLM Cost (Claude) |
|-------------|-----------------|---------------------------------------|-------------------|----------------------------------|----------------------------|---------------------------|
| Small (≤ 10 tenants) | 15 | 5 | 75 | 1,650 | ~$36 | ~$248 |
| Medium (≤ 100 tenants) | 150 | 5 | 750 | 16,500 | ~$363 | ~$2,475 |
| Large (≤ 1000 tenants) | 1,500 | 5 | 7,500 | 165,000 | ~$3,630 | ~$24,750 |

### 4.3 Intelligence Plane LLM Costs (Read-Only AI Analysis)

The Intelligence Plane provides cross-plane read-only AI analysis — ad-hoc NL Q&A, attribution analysis, log analysis — without crossing the Freeze Bridge (architecture §2). These are on-demand, user-initiated queries.

| Query Type | Model | Est. Input/Output Tokens | Cost per Query (DeepSeek) | Cost per Query (Claude) | Estimated Queries per User per Day |
|-----------|-------|--------------------------|---------------------------|-------------------------|-----------------------------------|
| "Why is gross margin down this month?" (attribution) | Claude Sonnet 5 | 15K / 5K | $0.0175 | $0.120 | 2 |
| "Show me data lineage for this number" (trace) | Claude Sonnet 5 | 10K / 3K | $0.0110 | $0.075 | 1 |
| "What changed in this workflow last week?" (change query) | DeepSeek V4 Pro | 8K / 2K | $0.0080 | $0.054 | 3 |
| "Explain this anomaly" (root cause) | Claude Sonnet 5 | 20K / 8K | $0.0260 | $0.180 | 1 |
| Log Analysis (AI-powered, FR27.4) | DeepSeek V4 Pro | 12K / 4K | $0.0140 | $0.096 | 0.5 |
| **Average per Intelligence Query** | — | **~13K / ~4.4K** | **~$0.015** | **~$0.105** | **~7.5** |

### 4.4 Runtime LLM Cost Summary

| Cost Category | DeepSeek V4 Pro (China, monthly) | Claude Sonnet 5 (US, monthly) | Annual Cost (China) | Annual Cost (US) |
|---------------|----------------------------------|-------------------------------|---------------------|------------------|
| Design Plane — Exploration | $36 / $363 / $3,630 (S/M/L) | $248 / $2,475 / $24,750 (S/M/L) | $432 / $4,356 / $43,560 | $2,976 / $29,700 / $297,000 |
| Design Plane — BRD/ADR Generation | $0 / $50 / $300 (S/M/L) | $30 / $300 / $1,800 (S/M/L) | $0 / $600 / $3,600 | $360 / $3,600 / $21,600 |
| Design Plane — Freeze Bridge Resolution | $0 / $30 / $200 (S/M/L) | $15 / $200 / $1,200 (S/M/L) | $0 / $360 / $2,400 | $180 / $2,400 / $14,400 |
| Intelligence Plane — Q&A | $8 / $80 / $800 (S/M/L) | $50 / $500 / $5,000 (S/M/L) | $96 / $960 / $9,600 | $600 / $6,000 / $60,000 |
| Agent Evaluation (CI Regression) | $45 / $45 / $45 | $111 / $111 / $111 | $540 / $540 / $540 | $1,332 / $1,332 / $1,332 |
| Agent Cost Governance Overhead | $5 / $30 / $150 (S/M/L) | $5 / $30 / $150 (S/M/L) | $60 / $360 / $1,800 | $60 / $360 / $1,800 |
| **Total Runtime LLM Cost** | **$94 / $598 / $5,125/mo** | **$459 / $3,616 / $33,011/mo** | **$1,128 / $7,176 / $61,500/yr** | **$5,508 / $43,392 / $396,132/yr** |

> **Key Insight**: Runtime LLM costs are entirely variable (per-use) and directly proportional to user activity. A tenant with 0 active analysts incurs $0 runtime LLM cost. This is fundamentally different from traditional SaaS where infrastructure cost is the dominant factor — here, LLM costs can exceed infrastructure costs for heavy-use tenants.

---

## 5. Cost Optimization Strategies

> **Status**: Strategy catalog defined; implementation priority assigned per Phase 0-8 roadmap. Projected savings ranges provided; actual savings pending baseline cost measurement.

**Purpose**: Catalog of cost optimization levers available throughout the system lifecycle. Each strategy references the architecture decision or mechanism that enables it, the projected savings range, and the implementation complexity.

### 5.1 Architectural Cost Advantages (Inherent)

These advantages are inherent in the architecture and require no additional implementation — they are the direct result of ADR decisions.

| Advantage | Architecture Basis | Mechanism | Savings vs. Traditional AI-BI |
|-----------|-------------------|-----------|-------------------------------|
| **Zero Runtime AI Cost** | ADR-0005 (Four-Layer Architecture), ADR-0006 (Freeze Bridge) | Frozen scripts execute deterministically; zero LLM tokens consumed after freezing | 100% of runtime AI invocation cost eliminated |
| **Design-Time AI Only** | Architecture §2 (Core Design Philosophy) | AI costs accrue only during exploration/authoring, not during recurring execution | Eliminates per-report/per-run LLM costs |
| **Dual-Model Cost Arbitrage** | ADR-0009 (Dual-Model Pricing) | Route T1-T2 tasks to DeepSeek V4 Pro ($0.50/$2.00 per M) vs. Claude ($3.00/$15.00 per M) | 40-60% on bulk generation tasks |
| **KB-Driven Reduces Iterations** | Architecture §3.4 (AI Copilot Engine → KB Retriever) | High-quality KB context improves first-pass generation accuracy, reducing iteration count per task | 20-30% fewer tokens per exploration session |

### 5.2 Operational Cost Optimization Levers

| Lever | Mechanism | Estimated Savings | Implementation Complexity | Status | Reference |
|-------|-----------|-------------------|---------------------------|--------|-----------|
| **Prompt Caching** | Cache common system prompts, KB context blocks, and schema definitions; avoid re-sending identical prefixes | 15-30% on input tokens | Low (built into most LLM APIs) | To Deploy (Phase 0) | LLM Provider docs |
| **Result Caching** | Cache NL→SQL translations, KB retrieval results, and plan generations for semantically identical queries (FR15b.7) | 10-25% on exploration tokens | Medium | To Deploy (Phase 3) | FR15b.7, ADR-0007 |
| **Model Routing** | Auto-select cheaper model for simple queries (intent classification, schema lookup) and reserve expensive model for complex reasoning (multi-step analysis, attribution) | 20-40% on mixed workloads | Medium-High | To Deploy (Phase 7) | ADR-0009, FR30.5 |
| **Tiered Enforcement (DEGRADE not DENY)** | At 85% quota, auto-downgrade to cheaper model instead of denying service (ADR-0020) | Prevents cost overruns; preserves availability | Medium | To Deploy (Phase 6) | ADR-0020 |
| **Token Budgets & Quotas** | Hierarchical quotas: Organization → Tenant → User → VP/Exploration nested budgets (ADR-0020) | Prevents runaway costs; adds cost predictability | Medium | To Deploy (Phase 6) | ADR-0020 |
| **Loop Detection & Circuit Breaker** | Three detectors (identical-call, ping-pong, context-growth) with automatic circuit breaking (ADR-0020) | Prevents $47K+ runaway loops | Medium | To Deploy (Phase 6) | ADR-0020 |
| **KB Embedding Caching** | Pre-compute and cache KB domain embeddings; incremental update on KB changes only | 30-50% on KB retrieval embedding costs | Low | To Deploy (Phase 2) | ADR-0013 (PG-First), FR33.1 |
| **Batch Intelligence Queries** | Queue non-urgent Intelligence Plane queries and process in batch windows for lower-priority model access | 10-20% on Intelligence Plane costs | Low-Medium | To Deploy (Phase 5) | Architecture §2 (Intelligence Plane) |
| **Tenant Model Tiering** | Charge premium for Claude Sonnet 5 access; default tenants to DeepSeek V4 Pro (FR30.3-30.5, FR12.3) | Revenue-aligned cost; 14% cost for default-tier tenants | Low | To Deploy (Phase 8) | ADR-0009, FR12.3 |

### 5.3 Development-Phase Cost Optimization

| Lever | Mechanism | Estimated Savings | Reference |
|-------|-----------|-------------------|-----------|
| **Sub-Agent Parallelism Tuning** | Optimize N per phase based on B.2 efficiency matrix; avoid over-parallelizing tightly-coupled tasks | 10-20% on orchestration overhead | docs/04-timeline.md §B.2 |
| **Model Selection by Task Tier** | Generate T1-T2 tasks with DeepSeek, T3-T4 tasks with Claude (blended approach) | 40-60% vs. all-Claude development | ADR-0009 |
| **Prompt Reuse Library** | Build and reuse validated prompts for common code generation patterns (CRUD, connector, test) | 15-25% on input tokens | docs/04-timeline.md §A.2 |
| **Incremental Regeneration** | On review-fix cycles, regenerate only the changed code block, not the entire file | 30-50% on iteration tokens | — |

### 5.4 Cost Optimization Implementation Roadmap

| Phase | Optimization to Implement | Priority | Dependencies |
|-------|--------------------------|----------|-------------|
| Phase 0-2 | Prompt Caching, KB Embedding Caching (low-hanging fruit) | High | None |
| Phase 3 | Result Caching (NL→SQL), Model Selection by Task Tier | High | AI Copilot Engine operational |
| Phase 4 | Incremental Regeneration (Freeze Bridge review cycles) | Medium | Freeze Bridge operational |
| Phase 5 | Batch Intelligence Queries | Low | Scheduler operational |
| Phase 6 | Token Budgets & Quotas, Tiered Enforcement, Loop Detection (ADR-0020) | High | Multi-tenancy, RBAC |
| Phase 7 | Model Routing (auto-select based on complexity) | Medium | Agent Customization (FR30) |
| Phase 8 | Tenant Model Tiering (pricing model) | Medium | Tiered pricing model (FR12.3) |

---

## 6. TCO Summary & Scenarios

> **Status**: Scenario framework defined; all values estimated based on reference architecture sizing and ADR-0009 pricing model. Calibration pending Phase 0-2 velocity measurement and customer discovery.

**Purpose**: Provide Total Cost of Ownership (TCO) projections across three deployment scenarios. TCO = Development Costs (one-time, amortized) + Annual Runtime Costs (infrastructure + LLM + operations).

### 6.1 Scenario Definitions

| Parameter | Small | Medium | Large |
|-----------|-------|--------|-------|
| **Tenants** | ≤ 10 | ≤ 100 | ≤ 1000 |
| **Active Users (Analysts + Approvers + Admins)** | 25 | 250 | 2,500 |
| **Workflows per Tenant (avg.)** | 15 | 25 | 40 |
| **Daily Workflow Executions (total)** | 150 | 2,500 | 40,000 |
| **Daily Design Plane Explorations (total)** | 75 | 750 | 7,500 |
| **Daily Intelligence Plane Queries (total)** | 40 | 400 | 4,000 |
| **Data Volume (KB + Audit + Logs)** | 0.5 TB | 5 TB | 50 TB |
| **Isolation Level (typical)** | Process | Node | Cluster (for enterprise) |
| **Model Tier (typical)** | DeepSeek V4 Pro | Mixed (DeepSeek + Claude) | Mixed (DeepSeek + Claude) |
| **Region** | Single (China or US) | Single + DR | Multi-region + DR |

### 6.2 TCO Breakdown — Small Scenario (≤ 10 tenants)

| Cost Category | Annual Cost (China, DeepSeek) | Annual Cost (US, Claude) | Notes |
|---------------|-------------------------------|--------------------------|-------|
| **A. Development (one-time, amortized over 3 years)** | | | |
| Personnel (8 months ÷ 3) | $49,667/yr | $144,000/yr | See §2.1 |
| LLM — Code Generation (÷ 3) | $26/yr | $183/yr | See §2.2.1 |
| LLM — Design Exploration (÷ 3) | $1,015/yr | $1,015/yr | See §2.2.2 |
| Infrastructure (÷ 3) | $3,877/yr | $7,291/yr | See §2.3 |
| **Subtotal A (Amortized Dev)** | **$54,585/yr** | **$152,489/yr** | — |
| **B. Runtime Infrastructure (annual)** | | | |
| Compute | $11,220/yr | $22,440/yr | See §3.1 |
| Storage | $3,906/yr | $7,812/yr | See §3.2 |
| Networking | $1,440/yr | $2,880/yr | See §3.3 |
| **Subtotal B** | **$17,466/yr** | **$34,932/yr** | Includes isolation premium |
| **C. Runtime LLM (annual)** | | | |
| Design Plane Exploration | $432/yr | $2,976/yr | See §4.1-4.2 |
| Intelligence Plane Q&A | $96/yr | $600/yr | See §4.3 |
| Agent Evaluation (CI) | $540/yr | $1,332/yr | See §2.2.3 |
| **Subtotal C** | **$1,128/yr** | **$5,508/yr** | Includes BRD/ADR, Freeze Bridge, Governance |
| **D. Operations Personnel (annual)** | | | |
| DevOps/SRE (part-time) | $20,000/yr | $40,000/yr | 0.25 FTE for small |
| Support (part-time) | $10,000/yr | $20,000/yr | 0.25 FTE |
| **Subtotal D** | **$30,000/yr** | **$60,000/yr** | — |
| **TOTAL TCO (Annual)** | **~$103,179/yr** | **~$252,928/yr** | — |
| **Per-Tenant Annual TCO** | **~$10,318/tenant/yr** | **~$25,293/tenant/yr** | Based on 10 tenants |

### 6.3 TCO Breakdown — Medium Scenario (≤ 100 tenants)

| Cost Category | Annual Cost (China, DeepSeek) | Annual Cost (US, Claude) | Notes |
|---------------|-------------------------------|--------------------------|-------|
| **A. Development (amortized over 3 years)** | $54,585/yr | $152,489/yr | Same as Small |
| **B. Runtime Infrastructure** | $48,090/yr | $96,180/yr | 3-5× Small due to scale |
| **C. Runtime LLM** | $7,176/yr | $43,392/yr | 6-8× Small due to user growth |
| **D. Operations Personnel** | $80,000/yr | $180,000/yr | 1.0 FTE SRE + 0.5 support |
| **TOTAL TCO (Annual)** | **~$189,851/yr** | **~$472,061/yr** | — |
| **Per-Tenant Annual TCO** | **~$1,899/tenant/yr** | **~$4,721/tenant/yr** | Expected lower than Small (economies of scale) |

### 6.4 TCO Breakdown — Large Scenario (≤ 1000 tenants)

| Cost Category | Annual Cost (China, DeepSeek) | Annual Cost (US, Claude) | Notes |
|---------------|-------------------------------|--------------------------|-------|
| **A. Development (amortized over 3 years)** | $54,585/yr | $152,489/yr | Same as Small |
| **B. Runtime Infrastructure** | $171,744/yr | $343,488/yr | 8-15× Small; cluster isolation premium |
| **C. Runtime LLM** | $61,500/yr | $396,132/yr | 50-100× Small; volume discounts possible |
| **D. Operations Personnel** | $140,000/yr | $350,000/yr | 2.0 FTE SRE + 1.0 support + 0.5 compliance |
| **TOTAL TCO (Annual)** | **~$427,829/yr** | **~$1,242,109/yr** | — |
| **Per-Tenant Annual TCO** | **~$428/tenant/yr** | **~$1,242/tenant/yr** | Significant economies of scale expected |

### 6.5 TCO Comparison — China vs. US Team

| Factor | China Team (DeepSeek) | US Team (Claude) | Ratio (CN:US) |
|--------|----------------------|------------------|---------------|
| Development Personnel (8-month) | ¥1,072,000 (~$149,000) | $432,000 | ~1:2.9 |
| Development LLM — Code Gen | $78.30 | $548.10 | ~1:7.0 (per ADR-0009 pricing ratio) |
| Development Infrastructure | $11,632 | $21,872 | ~1:1.9 (Alibaba vs. AWS) |
| Runtime Infrastructure (annual, Small) | $17,466/yr | $34,932/yr | ~1:2.0 |
| Runtime LLM (annual, Small) | $1,128/yr | $5,508/yr | ~1:4.9 |
| Operations Personnel (annual, Small) | ~$30,000/yr | ~$60,000/yr | ~1:2.0 |
| **Total TCO (3-year, Small)** | **~$310K** | **~$759K** | **~1:2.5** |

### 6.6 Key Cost Ratios

| Ratio | Small | Medium | Large | Trend |
|-------|-------|--------|-------|-------|
| Runtime LLM : Runtime Infrastructure | 0.06 : 1 | 0.15 : 1 | 0.36 : 1 | LLM costs grow faster than infra |
| Development Amortization : Annual Runtime | 1.1 : 1 | 0.40 : 1 | 0.15 : 1 | Dev becomes negligible at scale |
| Per-Tenant Cost (China) | ~$10,318 | ~$1,899 | ~$428 | Declines sharply with scale |
| Operations : Total TCO | ~29% | ~42% | ~33% | Roughly constant % |
| China TCO : US TCO | ~1:2.5 | ~1:2.5 | ~1:2.9 | Consistent ~1:2.5 to 1:3 advantage |

### 6.7 Breakeven Analysis

> **Purpose**: Determine minimum tenant count and pricing tier to recover development costs within target payback period.

| Parameter | Value | Notes |
|-----------|-------|-------|
| Total Development Cost (one-time) | $163,854 (China) / $458,564 (US) | §2.1 + §2.2 + §2.3 |
| Target Payback Period | 24 months | Typical: 18-24 months |
| Monthly Revenue per Tenant (avg.) | $2,000 (Small), $1,500 (Medium), $1,000 (Large) | Per FR12.3 tiered pricing |
| Gross Margin (after Runtime costs) | 70% (China) / 60% (US) | Revenue − (Infrastructure + LLM + Ops) |
| Breakeven Tenant Count (China, 24mo) | ~5 tenants | $163,854 ÷ ($2,000 × 0.70 × 24) |
| Breakeven Tenant Count (US, 24mo) | ~16 tenants | $457,464 ÷ ($2,000 × 0.60 × 24) |

---

*Last Updated: 2026-07-04*
