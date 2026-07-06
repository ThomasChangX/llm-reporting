# Contributing to llm-reporting

This project is currently in the **design phase**. Contributions to the architecture documentation, requirements, and design decisions are welcome.

## Current Contribution Scope

This repository contains design documentation only (pre-implementation). Acceptable contributions include:

- Corrections to architectural descriptions
- New Architecture Decision Records (ADRs) proposing design changes
- Improvements to cross-reference accuracy
- Glossary additions and corrections
- Diagram improvements (Mermaid source files)

## Document Structure

The documentation follows a numbered pipeline:

```
docs/01-facts.md → docs/02-requirement.md → docs/03-architecture.md → docs/04-timeline.md → docs/05-cost.md
```

Plus:
- `adr/` — Architecture Decision Records (MADR format)
- `docs/` — Supplementary documentation (glossary, threat model, SLO/SLI, diagrams, etc.)

## ADR Process

### Creating a New ADR

1. Check `adr/README.md` for the current ADR index
2. Copy the MADR template from `adr/README.md` (or an existing ADR (e.g., `0001-<title>.md`))
3. Fill in all sections: Context, Options Considered, Decision, Rationale, Consequences, Linked Modules
4. Use the next sequential 4-digit number (e.g., `0012-`)
5. Update `adr/README.md` status table
6. Add a summary entry in `docs/01-facts.md` Key Design Decisions

### ADR Format (MADR)

```markdown
# ADR-NNNN: Title

- **Status**: Accepted | Proposed | Deprecated | Superseded | Rejected
- **Date**: YYYY-MM-DD
- **Deciders**: [names]

## Context
## Options Considered
### Option A: ... (Chosen/Rejected)
### Option B: ...
## Decision
## Rationale
## Consequences
## Linked Modules
```

## Cross-Reference Rules

When editing any document, you MUST update all cross-references:

1. References to other documents use the format: `docs/03-architecture.md` (Section N)
2. References to ADRs use the format: `adr/NNNN-title.md`
3. References to FR (Functional Requirements) use the format: `FR15b`
4. References to NFR (Non-Functional Requirements) use the format: `NFR9.2`
5. After any structural change, review the `docs/cross-reference-checklist.md` verification checklist

## AI-Assisted Contributions

This project uses AI-assisted design (Design Plane philosophy). If you use AI tools to draft contributions:

1. Disclose that AI was used in your PR description
2. Verify all AI-generated content for accuracy
3. Ensure all cross-references resolve correctly
4. Human review is required before merge — AI-assisted content is a draft, not final

## Future: Implementation Phase

When the project enters the implementation phase (Phase 1+ of the timeline), code contribution guidelines will be added to this document, including:

- Development environment setup
- Testing requirements
- CI/CD pipeline expectations
- Coding standards (Python/Go/Rust)

## Review Process

1. Open a Pull Request with your changes
2. Ensure all cross-references are updated
3. Request review from at least one maintainer
4. Merge after approval

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
