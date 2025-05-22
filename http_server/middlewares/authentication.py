import os
import logging
import time
import json
from typing import Callable, Awaitable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from ..services.authorization import User, AppRoles

LOGGER = logging.getLogger(f"playlist.{__name__}")

class AuthenticationError(Exception):
    pass

class Authenticate(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        try:
            if request.headers.get("Authorization", None):
                user_info = self.validateToken(request.headers["Authorization"])
            elif request.cookies.get("Authorization", None):
                user_info = self.validateToken(request.cookies["Authorization"])
            else:
                user_info = User(
                    id=0,
                    name="steve",
                    role=AppRoles.admin
                )
                # return JSONResponse({"message": "No auth token found!"}, status_code=401)
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
