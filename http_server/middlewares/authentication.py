import logging
import json
from typing import Callable, Awaitable
from fastapi import Request, Response, HTTPException
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
        if request.url.path == "/users/session":
            response = await call_next(request)
            # if response == 200:
            #   delete any user session
            #   create new
            return response
        elif request.url.path == "/users" and request.method.upper() == "POST":
            response = await call_next(request)
            # if response == 200:
            #   create new
            return response
        else:
            user_info = self.sessionValidate(request)
            logging_conf.USER_NAME.set(f"{user_info.name}:{user_info.id}")
            request.state.user_info = user_info
            return await call_next(request)

    def sessionValidate(self, request: Request) -> User:
        session_id = request.headers.get("Authorization", None)
        if not session_id:
            session_id = request.cookies.get("Authorization", None)
        if not session_id:
            raise HTTPException(401, "Missing session id!")
        # TODO: check session in redis and return user

    def sessionCreate(self, user_info: User) -> str:
        pass

    def sessionGetById(self, session_id: str) -> bool:
        pass

    def sessionGetByUser(self, user_id: int) -> bool:
        pass

    def sessionRefresh(self, session_id: str) -> None:
        pass
