from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[..., Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        hsts = "max-age=63072000; includeSubDomains; preload"
        response.headers["Strict-Transport-Security"] = hsts
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, max_requests: int = 1000, window_seconds: int = 60) -> None:
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: dict[str, list[float]] = {}

    async def dispatch(
        self, request: Request, call_next: Callable[..., Awaitable[Response]]
    ) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        now_ts = time.time()
        window_start = now_ts - self.window_seconds

        if client_ip not in self._buckets:
            self._buckets[client_ip] = []

        self._buckets[client_ip] = [
            ts for ts in self._buckets[client_ip] if ts > window_start
        ]

        if len(self._buckets[client_ip]) >= self.max_requests:
            body = '{"errors":[{"code":"rate_limit_exceeded","message":"Too many requests."}]}'
            response = Response(content=body, status_code=429, media_type="application/json")
            response.headers["Retry-After"] = str(self.window_seconds)
            response.headers["X-RateLimit-Limit"] = str(self.max_requests)
            response.headers["X-RateLimit-Remaining"] = "0"
            return response

        self._buckets[client_ip].append(now_ts)
        response = await call_next(request)
        remaining = max(0, self.max_requests - len(self._buckets[client_ip]))
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response


def setup_middleware(app: FastAPI) -> None:
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware, max_requests=1000, window_seconds=60)  # type: ignore[arg-type]
