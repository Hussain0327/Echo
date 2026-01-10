"""
API Key Authentication Middleware for Echo Analytics Platform.

Provides simple API key-based authentication via the X-API-Key header.
Can be bypassed in development mode by setting REQUIRE_AUTH=False.

Usage:
    Add to FastAPI app:
        app.add_middleware(APIKeyAuthMiddleware)

    Make requests with header:
        X-API-Key: your-api-key-here
"""

from typing import Callable, Set

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware that validates API key from X-API-Key header.

    Excludes public paths like health checks, docs, and root.
    Can be disabled via REQUIRE_AUTH=False in settings.
    """

    # Paths that don't require authentication
    EXCLUDED_PATHS: Set[str] = {
        "/",
        "/api/v1/health",
        "/api/v1/docs",
        "/api/v1/redoc",
        "/openapi.json",
    }

    # Path prefixes to exclude (e.g., static files, docs)
    EXCLUDED_PREFIXES: tuple[str, ...] = (
        "/api/v1/docs",
        "/api/v1/redoc",
    )

    def __init__(self, app: Callable, api_key: str | None = None):
        """
        Initialize the middleware.

        Args:
            app: The FastAPI application
            api_key: Optional override for API key (defaults to settings)
        """
        super().__init__(app)
        settings = get_settings()
        self._api_key = api_key or settings.API_KEY
        self._require_auth = settings.REQUIRE_AUTH

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and validate API key if required.

        Args:
            request: The incoming request
            call_next: The next middleware/handler in the chain

        Returns:
            Response from the handler or 401/403 error
        """
        # Skip auth if disabled
        if not self._require_auth:
            return await call_next(request)

        # Skip auth for excluded paths
        if self._is_excluded_path(request.url.path):
            return await call_next(request)

        # Validate API key
        api_key = request.headers.get("X-API-Key")

        if not api_key:
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Unauthorized",
                    "detail": "Missing X-API-Key header",
                },
            )

        if api_key != self._api_key:
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Forbidden",
                    "detail": "Invalid API key",
                },
            )

        # API key is valid, proceed
        return await call_next(request)

    def _is_excluded_path(self, path: str) -> bool:
        """Check if the path is excluded from authentication."""
        if path in self.EXCLUDED_PATHS:
            return True

        for prefix in self.EXCLUDED_PREFIXES:
            if path.startswith(prefix):
                return True

        return False
