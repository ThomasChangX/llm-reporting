# LLM Reporting — Next-Gen BI for the LLM Era

> An AI-assisted design and deterministic execution platform for Reporting, ETL, Adjustment, and Reconciliation — replacing Excel and PowerBI.

**Status**: Design Phase (pre-implementation) | **Version**: 1.4 | **Last Updated**: 2026-07-04

## Philosophy

**"Explore with AI in the Design Plane, Execute without AI Side Effects in the Runtime Plane."**

AI assists in exploration and authoring. Once workflows are validated, they are "frozen" into deterministic scripts requiring zero LLM calls during production execution. The Intelligence Plane provides AI-powered read-only analysis (ad-hoc Q&A, attribution) without writing to any system state.

## Documentation Map

### Core Design Documents (read in order)

| # | Document | Contents |
|---|----------|----------|
| 01 | [docs/01-facts.md](docs/01-facts.md) | Project background, design philosophy, 22 Architecture Decision Records (summarized in facts doc) |
| 02 | [docs/02-requirement.md](docs/02-requirement.md) | 44 functional requirement groups + 9 NFR groups (ISO 25010) |
| 03 | [docs/03-architecture.md](docs/03-architecture.md) | Full architecture design (~6200 lines): dual-plane, Compute Spec, KB, Agents, BRD/ADR, and more |
| 04 | [docs/04-timeline.md](docs/04-timeline.md) | Development roadmap with Token-Speed estimation methodology |
| 05 | [docs/05-cost.md](docs/05-cost.md) | Full lifecycle cost analysis: development, infrastructure, LLM, pricing model |

### Architecture Decision Records

| Directory | Contents |
|-----------|----------|
| [adr/](adr/) | 22 complete ADRs in MADR format |

### Supplementary Documentation

| Document | Contents |
|----------|----------|
| [docs/glossary.md](docs/glossary.md) | 102 domain and technical terms |
| [docs/security/threat-model.md](docs/security/threat-model.md) | STRIDE threat matrix + OWASP Top 10 for LLM Applications assessment |
| [docs/operations/slo-sli.md](docs/operations/slo-sli.md) | Service Level Objectives for 5 critical user journeys with error budgets |
| [docs/architecture/c4-model.md](docs/architecture/c4-model.md) | C4 Model diagrams (System Context, Container, Component) |
| [docs/architecture/entity-erd.md](docs/architecture/entity-erd.md) | Core entity relationship diagram |
| [docs/diagrams/](docs/diagrams/) | Architecture diagram source files (Mermaid) |
| [docs/cross-reference-checklist.md](docs/cross-reference-checklist.md) | Manual consistency verification checklist |

## Key Architecture Decisions

1. **Four-Layer Architecture**: Design Plane (AI-assisted) + Freeze Bridge + Runtime Plane (zero AI side effects) + Intelligence Plane (AI read-only, answers don't cross the bridge)
2. **Compute Spec (YAML)**: Unified IR for Reporting/ETL/Adjustment/Reconciliation — 9 Job Types
3. **Knowledge Base**: 7 domains, PG-First storage (PostgreSQL + pgvector + S3), dedicated engines on-demand via interface abstraction
4. **BRD/ADR as First-Class Entities**: Full lifecycle management with AI-assisted generation and 6-round verification
5. **Dual-Model Strategy**: DeepSeek V4 Pro (China, cost-optimized) + Claude Sonnet 5 (US, capability-optimized)

> **Note**: DeepSeek V4 Pro and Claude Sonnet 5 are projected/planned model tiers for forward-looking cost estimation, not currently shipping products.

## Quick Start

1. Start with [docs/01-facts.md](docs/01-facts.md) for project background
2. Read the [adr/](adr/) directory for architectural rationale
3. Dive into [docs/03-architecture.md](docs/03-architecture.md) for full technical design
4. Check [docs/glossary.md](docs/glossary.md) for unfamiliar terms

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for documentation contribution guidelines.

## License

MIT — see [LICENSE](LICENSE)
