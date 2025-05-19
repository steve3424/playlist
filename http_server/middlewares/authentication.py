import os
import logging
import time
import json
from typing import Callable, Awaitable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

LOGGER = logging.getLogger(f"playlist.{__name__}")

OPEN_ENVS = {
    "dev"
}
OPEN_ENDPOINTS = {
    "/health"
}

class AuthenticationError(Exception):
    pass

class Authenticate(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        try:
            global OPEN_ENVS
            global OPEN_ENDPOINTS
            current_env = os.environ["ENV"]
            if current_env in OPEN_ENVS or request.url.path in OPEN_ENDPOINTS:
                user_info = {}
                LOGGER.debug(f"Auth skipped for endpoint '{request.url.path}' in env '{current_env}'!")
            else:
                time_auth_start = time.perf_counter()
                if request.headers.get("Authorization", None):
                    user_info = self.validateToken(request.headers["Authorization"])
                elif request.cookies.get("Authorization", None):
                    user_info = self.validateToken(request.cookies["Authorization"])
                else:
                    return JSONResponse({"message": "No auth token found!"}, status_code=401)
                LOGGER.info(f"Auth took {time.perf_counter() - time_auth_start}s!")
            request.state.user_info = user_info
            return await call_next(request)
        except AuthenticationError as ex:
            LOGGER.exception(ex)
            return JSONResponse({"message": "Unauthorized"}, status_code=401)

    # TODO: finalize permission model and actually do auth
    def validateToken(self, token: str) -> dict:
        try:
            return json.loads(token)
        except Exception as ex:
            raise AuthenticationError(ex) from ex
