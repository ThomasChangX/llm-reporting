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

| Role | Headcount | Monthly Salary (USD) | 8-Month Cost |
| ------------------------------------------ | --------- | ---------- | ------------ |
| Senior Full-Stack Developer (AI-Assisted) | 2 | $14,000 | $224,000 |
| Senior Backend/Data Engineer (AI-Assisted) | 1 | $13,500 | $108,000 |
| Domain Expert (Finance/BI, Part-time) | 0.5 | $6,000 | $48,000 |
| DevOps Engineer (Part-time) | 0.5 | $6,500 | $52,000 |
| **Subtotal** | **4 FTE** | | **$432,000** |

> **Salary Note**: Above are pre-tax base salaries. Actual enterprise employment costs must include employer burdens (US: FICA 7.65%, Health Insurance ~$500-1,200/mo/person, 401k match 3-6%, Workers' Comp, PTO etc. ≈ +25-35%; China: ~84-91% total burden — Five Insurances + Housing Fund ~35%, plus supplementary benefits, office space, equipment, management overhead, and other indirect costs). With burdens: US ~$540,000-583,000, China ~¥1,971,000-2,044,000 (~$274,000-284,000). Operations personnel costs in TCO calculations below should be proportionally adjusted upward.

**Option 2: China Team**
| Role | Headcount | Monthly Salary (CNY) | 8-Month Cost |
| ------------------------------------------ | --------- | ---------- | ------------ |
| Senior Full-Stack Developer (AI-Assisted) | 2 | ¥35,000 | ¥560,000 |
| Senior Backend/Data Engineer (AI-Assisted) | 1 | ¥33,000 | ¥264,000 |
| Domain Expert (Finance/BI, Part-time) | 0.5 | ¥15,000 | ¥120,000 |
| DevOps Engineer (Part-time) | 0.5 | ¥16,000 | ¥128,000 |
| **Subtotal** | **4 FTE** | | **¥1,072,000 (~$149,000)** |

> **⚠️ Status**: Sections below are outlined but detailed content is pending. See the section headers for planned scope.

### 2.2 LLM API Costs (Development Phase)
*(Token cost estimates per phase using DeepSeek V4 Pro and Claude Sonnet 5 pricing — to be completed)*

### 2.3 Development Infrastructure Costs
*(Cloud VMs, CI/CD, monitoring, and tooling costs during the 8-month development cycle — to be completed)*

### 3. B: Runtime Infrastructure Costs
*(Monthly fixed + elastic costs: compute, storage, networking, multi-tenant isolation — to be completed)*

### 4. C: Runtime LLM Costs
*(Per-invocation token costs for the Design Plane exploration layer — to be completed)*

### 5. Cost Optimization Strategies
*(Freezing strategy, caching, prompt optimization, model routing — to be completed)*

### 6. TCO Summary & Scenarios
*(Total Cost of Ownership across small/medium/large deployment scenarios — to be completed)*
