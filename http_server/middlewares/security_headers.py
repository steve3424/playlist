import logging
from typing import Callable, Awaitable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

LOGGER = logging.getLogger(f"playlist.{__name__}")

class Headers(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        contentSecurityPolicy(response)
        return response

def contentSecurityPolicy(response: Response) -> None:
    response.headers.append(
        "content-security-policy",
        "object-src 'none';"
    )
