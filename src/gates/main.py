from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from gates.api.hosted import router as hosted_router
from gates.api.v1.router import router as v1_router
from gates.core.errors import GatesError
from gates.core.middleware import setup_middleware


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    yield


app = FastAPI(
    title="Gates",
    description="Self-hostable authentication platform — Clerk alternative",
    version="0.1.0",
    lifespan=lifespan,
)

setup_middleware(app)


@app.exception_handler(GatesError)
async def gates_error_handler(_request: Request, exc: GatesError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.http_status,
        content={
            "errors": [
                {
                    "code": exc.code,
                    "message": exc.message,
                    "long_message": exc.message,
                    "meta": exc.details,
                }
            ]
        },
    )


app.include_router(v1_router)
app.include_router(hosted_router)


@app.get("/health")
async def root_health() -> dict[str, str]:
    return {"status": "ok", "service": "gates"}
