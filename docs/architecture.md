# Architecture

## Design goals

The implementation prioritizes traceability, restart safety, deterministic local
operation, explicit human authority, and replaceable integrations. The core domain has
no dependency on FastAPI, SQLite, Ollama, or a Git provider.

## Components

```text
React console
    │ HTTP/JSON
FastAPI boundary ── validation, request IDs, health probes
    │
Workflow orchestrator ── persisted phase transitions and approval gates
    │
11 domain agents ── artifact production and lineage
    │ ports
    ├── SQLite repository (default; durable artifact graph)
    ├── Template / Ollama generator
    └── Source-control handoff adapter
```

Artifacts are append-only and versioned. A child records its parent artifact IDs,
forming a queryable directed acyclic lineage graph. Workflow state is separately
persisted so a process restart cannot skip an approval.

## Human-in-the-loop policy

The orchestrator only accepts an approval when its gate type exactly matches the active
gate and `approved=true` is explicit. Generated source is stored as an artifact. The
default Git adapter returns a proposed branch, commit, pull request, and commands but
does not mutate a repository.

## Production extension points

- Replace `SQLiteWorkflowRepository` with PostgreSQL plus Neo4j without changing agents.
- Replace `HandoffSourceControl` with GitHub/Azure DevOps adapters using workload identity.
- Move `_advance` execution behind a durable queue for horizontal workers.
- Add OIDC at the API gateway and record approver identity in approval payloads.
- Store generated files in object storage and artifact metadata in the database.

SQLite and in-process execution are intentional self-contained defaults, not claims of
multi-node scalability.
