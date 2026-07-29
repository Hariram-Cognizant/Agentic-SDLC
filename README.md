# Agentic SDLC

Production-oriented reference implementation of the **SDLC Agentic Framework**. Eleven
specialized agents turn a feature request into a traceable delivery package while
pausing at architect-controlled approval gates.

## What is included

- FastAPI API with a domain/application/infrastructure split
- Resumable, persisted workflow with clarification, BRD, and code-plan gates
- Eleven explicit agents: Intake, Context, Clarification, BRD, Story, Plan, Code,
  Git, Review, Sanity, and Release
- Deterministic generation by default and an optional local Ollama provider
- SQLite artifact and lineage persistence; integration ports for Git and graph stores
- React + TypeScript operator console
- Structured logging, health/readiness probes, request correlation IDs, tests, and
  container deployment assets

## Quick start

Prerequisites: Python 3.11+ and Node.js 20+.

```powershell
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:create_app --factory --app-dir backend --reload
```

In another terminal:

```powershell
Set-Location frontend
npm install
npm run dev
```

Open `http://localhost:5173`. API documentation is at `http://localhost:8000/docs`.

The default `GENERATION_PROVIDER=template` needs no model or API key. To use Ollama,
set `GENERATION_PROVIDER=ollama`, start Ollama, and make the configured model available.
If Ollama cannot answer, generation falls back to deterministic templates.

## Workflow

```text
Intake → Context → Clarification ⏸
BRD → Story → Plan ⏸
Code plan ⏸ → Code implementation → Git → Review → Sanity → Release
```

Every output is stored as a versioned artifact and linked to its upstream inputs.
See [docs/architecture.md](docs/architecture.md) and [docs/api.md](docs/api.md) for
the design and API contract.

## Quality commands

```powershell
ruff check .
mypy backend/app
pytest
Set-Location frontend
npm run lint
npm run build
```
