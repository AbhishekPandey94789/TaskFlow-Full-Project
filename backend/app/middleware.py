"""
Custom middleware for TaskFlow.
Logs HTTP method, path, and processing time (ms) for every request.
"""

import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("taskflow.access")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Runs on every request; logs method, path, and elapsed ms."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s  %s  %.2f ms  status=%s",
            request.method,
            request.url.path,
            elapsed_ms,
            response.status_code,
        )
        return response
