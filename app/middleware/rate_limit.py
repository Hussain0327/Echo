"""
Rate Limiting Middleware for Echo Analytics Platform.

Implements a token bucket algorithm to limit request rates per client IP.
Adds X-RateLimit-* headers to responses for client visibility.

Usage:
    Add to FastAPI app:
        app.add_middleware(
            RateLimitMiddleware,
            requests_per_minute=100,
            burst_size=20,
        )
"""

import time
from collections import defaultdict
from typing import Callable, Dict, Tuple

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Token bucket rate limiting middleware.

    Limits requests per client IP using a token bucket algorithm.
    Allows bursts up to burst_size, then enforces rate limit.
    """

    def __init__(
        self,
        app: Callable,
        requests_per_minute: int = 100,
        burst_size: int = 20,
    ):
        """
        Initialize the rate limiter.

        Args:
            app: The FastAPI application
            requests_per_minute: Maximum sustained request rate
            burst_size: Maximum burst capacity
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.rate = requests_per_minute / 60.0  # tokens per second

        # Client state: {ip: (last_request_time, available_tokens)}
        self._clients: Dict[str, Tuple[float, float]] = defaultdict(
            lambda: (time.time(), burst_size)
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and apply rate limiting.

        Args:
            request: The incoming request
            call_next: The next middleware/handler in the chain

        Returns:
            Response from the handler or 429 if rate limited
        """
        # Get client identifier (IP address)
        client_ip = self._get_client_ip(request)

        # Check rate limit
        is_allowed, tokens_remaining, retry_after = self._check_rate_limit(client_ip)

        if not is_allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "detail": f"Rate limit exceeded. Retry after {retry_after} seconds.",
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + retry_after),
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(int(tokens_remaining))
        response.headers["X-RateLimit-Reset"] = str(
            int(time.time() + (self.burst_size - tokens_remaining) / self.rate)
        )

        return response

    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP from request.

        Checks X-Forwarded-For header for proxied requests.
        """
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain (original client)
            return forwarded_for.split(",")[0].strip()

        if request.client:
            return request.client.host

        return "unknown"

    def _check_rate_limit(self, client_ip: str) -> Tuple[bool, float, int]:
        """
        Check if request is allowed under rate limit.

        Uses token bucket algorithm:
        - Tokens regenerate over time at `rate` per second
        - Each request consumes 1 token
        - If no tokens available, request is rejected

        Args:
            client_ip: The client's IP address

        Returns:
            Tuple of (is_allowed, tokens_remaining, retry_after_seconds)
        """
        current_time = time.time()

        # Get client state
        last_request_time, tokens = self._clients[client_ip]

        # Calculate tokens regenerated since last request
        time_passed = current_time - last_request_time
        tokens = min(self.burst_size, tokens + time_passed * self.rate)

        if tokens < 1:
            # Not enough tokens - calculate retry time
            retry_after = int((1 - tokens) / self.rate) + 1
            return False, 0, retry_after

        # Consume a token
        tokens -= 1
        self._clients[client_ip] = (current_time, tokens)

        return True, tokens, 0
