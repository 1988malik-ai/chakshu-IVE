"""HTTP request logging middleware."""

from __future__ import annotations

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_HTTP = logging.getLogger("aive.http")


class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        path = request.url.path
        try:
            response = await call_next(request)
            ms = (time.perf_counter() - start) * 1000
            if path.startswith("/api/"):
                _HTTP.info("%s %s → %s (%.0fms)", request.method, path, response.status_code, ms)
            return response
        except Exception:
            ms = (time.perf_counter() - start) * 1000
            _HTTP.exception("%s %s → ERROR (%.0fms)", request.method, path, ms)
            raise
