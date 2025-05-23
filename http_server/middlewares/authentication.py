import logging
import json
from typing import Callable, Awaitable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from ..authorization.models import User, AppRoles
from ..configs import logging_conf

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
                user_info: User = self.validateToken(request.headers["Authorization"])
            elif request.cookies.get("Authorization", None):
                user_info: User = self.validateToken(request.cookies["Authorization"])
            else:
                return JSONResponse({"message": "No authentication token found!"}, status_code=401)
            logging_conf.USER_NAME.set(user_info.name)
            request.state.user_info = user_info
            return await call_next(request)
        except AuthenticationError as ex:
            LOGGER.exception(ex)
            return JSONResponse({"message": "Unable to authenticate request!"}, status_code=401)

    # TODO: finalize permission model and actually do auth
    def validateToken(self, token: str) -> dict:
        try:
            return json.loads(token)
        except Exception as ex:
            raise AuthenticationError(ex) from ex
