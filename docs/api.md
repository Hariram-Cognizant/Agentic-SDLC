# API

Base path: `/api/v1`

| Method | Path | Purpose |
|---|---|---|
| GET | `/health/live` | Process liveness |
| GET | `/health/ready` | Persistence readiness |
| POST | `/workflows` | Start a workflow from JSON text |
| POST | `/workflows/upload` | Start from TXT, Markdown, JSON, CSV, or DOCX |
| GET | `/workflows` | List recent workflows |
| GET | `/workflows/{id}` | Fetch workflow state and active gate |
| GET | `/workflows/{id}/artifacts` | Fetch all versioned artifacts and lineage |
| POST | `/workflows/{id}/approvals` | Approve the exact active gate |

Interactive OpenAPI documentation is exposed at `/docs`. A gate approval body includes
`gate`, explicit `approved`, optional `answers`, `assumptions`, `out_of_scope`,
`success_metrics`, and `comment`.
