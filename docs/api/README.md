# API Specifications

This directory will contain API specifications for the llm-reporting system.

## Planned Contents

| File | Format | Description |
|------|--------|-------------|
| `rest-api.openapi.yaml` | OpenAPI 3.1 | REST API specification |
| `grpc-api.proto` | Protobuf | gRPC service definitions |
| `mcp-api.yaml` | YAML | MCP (Model Context Protocol) server interfaces |

## Current Status

The project is in the design phase. API specifications will be created when:
1. The Compute Spec YAML schema is finalized (see [docs/03-architecture.md §6](../03-architecture.md))
2. The Agent SDK interface is stabilized (see [docs/03-architecture.md §22A](../03-architecture.md))
3. The MCP Server catalog is complete (see [docs/03-architecture.md §22C](../03-architecture.md))

## Related

- [docs/03-architecture.md](../03-architecture.md) — Full architecture (API Gateway in §2, Agent SDK in §22A-22G)
- [adr/](../../adr/) — Architecture Decision Records
