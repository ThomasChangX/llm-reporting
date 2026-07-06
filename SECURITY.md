# Security Policy

## Reporting a Vulnerability

This project is currently in the **design phase** (pre-implementation). If you discover a security vulnerability in the architecture design or documentation, please report it privately.

**Do not open a public issue.**

Email the project maintainer at **security@llm-reporting.dev** with:
- A description of the vulnerability
- The affected document(s) and section(s)
- Any suggested mitigations

You will receive a response within 72 hours.

## Supported Versions

| Version | Status |
|---------|--------|
| Design docs v1.4 (2026-07-04) | Current |

## Security Architecture

The full technical threat model (STRIDE + OWASP Top 10 for LLM Applications) is available at:
- [docs/security/threat-model.md](docs/security/threat-model.md)

Security design principles are embedded in the architecture at:
- [docs/03-architecture.md](docs/03-architecture.md) §16
- [docs/03-architecture.md](docs/03-architecture.md) §22D (AI Agent 7-Layer Anti-Exploitation Defense)
