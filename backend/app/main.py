from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.dependencies import Container
from app.api.routes import router
from app.application.orchestrator import WorkflowOrchestrator
from app.infrastructure.generation import OllamaGenerator, TemplateGenerator
from app.infrastructure.logging import configure_logging
from app.infrastructure.settings import Settings, get_settings
from app.infrastructure.source_control import HandoffSourceControl
from app.infrastructure.sqlite_repository import SQLiteWorkflowRepository


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()
    configure_logging(resolved.log_level)
    repository = SQLiteWorkflowRepository(resolved.database_url)
    generator = (
        OllamaGenerator(
            resolved.ollama_base_url,
            resolved.ollama_model,
            resolved.ollama_timeout_seconds,
        )
        if resolved.generation_provider == "ollama"
        else TemplateGenerator()
    )
    orchestrator = WorkflowOrchestrator(
        repository, generator, HandoffSourceControl()
    )
    container = Container(repository, orchestrator, generator.name)

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        repository.initialize()
        resolved.artifact_dir.mkdir(parents=True, exist_ok=True)
        application.state.container = container
        yield

    app = FastAPI(
        title=resolved.app_name,
        version="0.1.0",
        description="Human-controlled, traceable SDLC agent orchestration",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Request-ID"],
    )

    @app.middleware("http")
    async def correlation_id(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    app.include_router(router, prefix="/api/v1")
    return app
