# docs/ — Supplementary Documentation

> This directory contains supplementary documentation extracted from or supporting the core design documents.

## Directory Map

| Directory / File | Contents |
|------------------|----------|
| `01-facts.md` | Project background, design philosophy, 25 ADRs (summary) |
| `02-requirement.md` | Functional and non-functional requirements |
| `03-architecture.md` | Architecture overview (~1300 lines): Core philosophy, panoramic architecture, deployment topology, and §N anchor stubs pointing to detailed module design in `sub-projects/` |
| `04-timeline.md` | Development roadmap and resource estimation |
| `05-cost.md` | Lifecycle cost analysis and pricing model |
| [`glossary.md`](glossary.md) | 102 domain and technical terms |
| [`cross-reference-checklist.md`](cross-reference-checklist.md) | Manual consistency verification checklist |
| [`sub-projects/`](sub-projects/) | **7 sub-project directories** with detailed per-module design docs (comprehensive 9-section format): workflow-engine, agent-platform, knowledge-services, query-serving, data-health, brd-adr-lifecycle, platform-core |
| [`security/`](security/) | Threat model (STRIDE + OWASP LLM Top 10) |
| [`operations/`](operations/) | SLO/SLI definitions with error budgets, backup/DR, GDPR compliance |
| [`architecture/`](architecture/) | C4 Model diagrams, entity ERD |
| [`diagrams/`](diagrams/) | Architecture diagram source files (Mermaid) |
| [`api/`](api/) | API specification placeholder |

## Relationship to Root Documents

The root-level `README.md` serves as the project entry point. All detailed design documentation lives under `docs/`. The ADR directory (`adr/`) is peer to `docs/` per standard GitHub project conventions.

## Reading Order

For first-time readers:
1. Start with `../README.md` for the project overview
2. Read `01-facts.md` → `02-requirement.md` → `03-architecture.md` (the numbered pipeline)
3. Reference `04-timeline.md` and `05-cost.md` for planning context
4. Browse `../adr/` for architectural decision rationale
5. Use `glossary.md` to decode unfamiliar terminology
