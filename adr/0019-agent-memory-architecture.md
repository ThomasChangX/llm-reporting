# ADR-0019: Agent Memory Architecture

- **Status**: Accepted
- **Date**: 2026-07-04
- **Deciders**: Architecture Team
- **Domain**: Architecture

## Context

Each Agent interaction is independent in the current architecture. But financial analysis has a natural rhythm spanning multiple days — discover anomaly, wait for data, come back to continue investigation. When a user says "continue last time's Recon investigation," the Agent needs to restore previous state.

Industry 2025-2026 consensus (LangGraph Store, Mem0, ENGRAM, Letta/MemGPT): Agent memory is not a single database but a four-layer cognitive architecture, corresponding to human cognitive psychology models.

Financial scenarios have additional constraints: memory data is subject to SOX audit requirements, needing bitemporal validity tracking and provenance tags.

## Options Considered

### Option A: Stateless Agent (Rejected)
Each interaction is independent, no memory.
- **Pro**: Simplest architecture, no storage or privacy concerns
- **Con**: Cannot support multi-turn financial analysis workflows

### Option B: Single Flat Memory Store (Rejected)
All memory in one flat table with simple key-value retrieval.
- **Pro**: Simple implementation
- **Con**: Cannot distinguish session context from permanent facts; no cognitive structure for different memory types

### Option C: Four-Layer Memory Architecture (Chosen)
L1 Working Memory (within-session), L2 Episodic Memory (cross-session), L3 Semantic Memory (permanent facts), L4 Procedural Memory (Skills/VPs, already exists). Each layer has independent storage strategy and promotion rules.

## Decision

Adopt a four-layer memory architecture using existing PostgreSQL + pgvector as storage, adding agent_episodic_memory and agent_semantic_memory tables. Strict tenant isolation. model_inferred facts require human confirmation before promotion to L3.

### L1: Working Memory
Within-session context: Context Window + LangGraph Checkpointer. In-memory, not persisted across sessions.

### L2: Episodic Memory
Cross-session episodic storage: PostgreSQL + pgvector semantic retrieval. Records session summaries with continuation_point for resuming multi-session workflows. TTL: 90 days.

```sql
CREATE TABLE agent_episodic_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    user_id UUID NOT NULL,
    session_id UUID NOT NULL,
    session_type VARCHAR(32) NOT NULL,
    vp_id VARCHAR(16),
    summary TEXT NOT NULL,
    key_findings JSONB,
    continuation_point JSONB,
    status VARCHAR(16) DEFAULT 'open',
    created_at TIMESTAMPTZ DEFAULT now(),
    expires_at TIMESTAMPTZ,
    embedding VECTOR(1536)
);
```

### L3: Semantic Memory
Permanent user-level facts (preferences, relationships, learned patterns). Stored with provenance tags (user_stated / model_inferred / tool_output) and bitemporal validity (valid_from / valid_to / superseded_by).

```sql
CREATE TABLE agent_semantic_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    user_id UUID NOT NULL,
    fact_type VARCHAR(32) NOT NULL,
    fact_key VARCHAR(256) NOT NULL,
    fact_value JSONB NOT NULL,
    provenance VARCHAR(16) NOT NULL,
    confidence FLOAT DEFAULT 1.0,
    observation_count INT DEFAULT 1,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ,
    superseded_by UUID,
    UNIQUE (tenant_id, user_id, fact_key)
);
```

### L4: Procedural Memory
VP Catalog + Skill Registry (already exists in ADR-0016 and ADR-0017).

### Promotion Rules
Same fact observed 3 independent times + confidence ≥0.7 → candidate extracted by LLM → user confirms → written to L3. All model_inferred facts must pass human confirmation. user_stated facts auto-promoted (confidence 1.0).

### Bitemporal Validity
Each fact carries valid_from / valid_to / superseded_by. Changes do not overwrite old facts, forming a traceable evolution chain for SOX audit.

## Rationale

1. **Multi-session continuity is essential for financial analysis**: Month-end close, reconciliation, and adjustment workflows naturally span days.
2. **Four-layer model maps to cognitive science**: Working (short-term), Episodic (experiential), Semantic (factual), Procedural (skill-based) — well-validated in both human cognition and AI memory research.
3. **Strict tenant isolation**: All memory tables include tenant_id; no cross-tenant memory sharing.
4. **Provenance and bitemporal validity satisfy SOX**: Auditors can trace when facts were learned, from what source, and how they evolved.

## Consequences

- **Positive**: Multi-session continuity enables natural financial analysis workflows; provenance tracking supports SOX audit; four-layer structure prevents context pollution.
- **Negative**: Additional storage for episodic and semantic memory tables; promotion rules require user interaction overhead.
- **Neutral**: L2 episodic memory has 90-day TTL — long-running investigations beyond this window lose session context.

## Industry References

| Reference | Year | Key Insight |
|-----------|------|-------------|
| LangGraph Store | 2025 | Checkpointer-based working memory + persistent long-term store |
| Mem0 | 2025 | Multi-layer memory with autonomous fact extraction |
| ENGRAM | 2025 | Episodic memory for agent session continuity |
| Letta/MemGPT | 2025 | OS-inspired memory hierarchy for LLM agents |

## Linked Modules

- `docs/03-architecture.md` → §22J (Agent Memory Architecture)
- `adr/0022-brd-generation-agent-pipeline.md` → Typology Tree stored in agent_semantic_memory
- `docs/glossary.md` → Four-Layer Memory, Provenance Tag, Bitemporal Validity
