import logging
from typing import Callable, Awaitable
from fastapi import Request
from fastapi.responses import Response, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

LOGGER = logging.getLogger(f"playlist.{__name__}")

class ExceptionHandlerGeneral(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        try:
            return await call_next(request)
        except Exception as ex:
            LOGGER.exception(ex)
            return JSONResponse({"message": "Something went wrong"}, status_code=500)