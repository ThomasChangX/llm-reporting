# Architecture Diagrams

This directory contains architecture diagram source files in [Mermaid](https://mermaid.js.org/) format. Diagrams are version-controlled alongside documentation.

## Diagram Index

| File | Type | Description |
|------|------|-------------|
| [`system-context.mmd`](system-context.mmd) | C4 System Context | External actors and system boundaries |
| [`four-plane-arch.mmd`](four-plane-arch.mmd) | C4 Container | Four-Layer Architecture: Design Plane / Freeze Bridge / Runtime Plane (Zero AI Side Effects) / Intelligence Plane (AI Read-Only) |
| [`freeze-bridge-flow.mmd`](freeze-bridge-flow.mmd) | Sequence | Freeze Bridge workflow: AI artifact → deterministic script |
| [`component-design-plane.mmd`](component-design-plane.mmd) | C4 Component | Design Plane detail: UI, AI Copilot Engine, Artifact Store, external integrations |

## Conventions

- Use [C4 Model](https://c4model.com/) for structural diagrams
- Use [Mermaid](https://mermaid.js.org/) syntax (natively rendered by GitHub)
- File naming: `kebab-case.mmd`
- Keep diagrams focused — one concern per diagram
- Update diagrams when architecture changes (they are part of the design, not an afterthought)

## Rendering

These `.mmd` files render natively in:
- GitHub (in Markdown files via ` ```mermaid ` blocks)
- VS Code (with Mermaid extension)
- Any Mermaid-compatible renderer

To embed a diagram in a Markdown document, copy the `.mmd` source into a ```` ```mermaid ```` fenced block:

````markdown
```mermaid
graph TB
    A --> B
```
````

Alternatively, use the [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli) (`@mermaid-js/mermaid-cli`) as a preprocessor to render `.mmd` files to SVG/PNG, or a build-time preprocessor that inlines `.mmd` content into ```` ```mermaid ```` blocks at publish time. Note: `%%!include` directives are not part of the Mermaid spec and are not rendered by GitHub or standard Mermaid renderers.

## Related

- [docs/architecture/c4-model.md](../architecture/c4-model.md) — C4 Model textual description (docs/03-architecture.md §15)
- [docs/03-architecture.md](../03-architecture.md) §2 — Full architecture diagram (ASCII)
