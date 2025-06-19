import logging
import redis.asyncio as redis
import uuid
import json
from typing import Callable, Awaitable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.concurrency import iterate_in_threadpool
from ..authorization.models import User, AppRoles
from ..configs import logging_conf

LOGGER = logging.getLogger(f"playlist.{__name__}")
SESSION_COOKIE_NAME = "SESSIONID"
SESSION_PREFIX = "session"
SESSION_TTL = 60 * 60 # * 24 * 7 # seconds per week
SESSION_CLIENT: redis.Redis = None

async def init(host: str, port: int):
    try:
        global SESSION_CLIENT
        if not SESSION_CLIENT:
            LOGGER.info(f"Starting session client on '{host}:{port}'...")
            SESSION_CLIENT = redis.Redis(
                host=host,
                port=port,
                decode_responses=True,
            )
        await SESSION_CLIENT.ping()
        return True
    except Exception as ex:
        LOGGER.error(ex)
        return False

async def shutdown() -> None:
    global SESSION_CLIENT
    if SESSION_CLIENT:
        LOGGER.info("Shutting down auth client...")
        await SESSION_CLIENT.aclose()
        SESSION_CLIENT = None

class AuthenticationError(Exception):
    pass

class Authenticate(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        try:
            if (
                (request.url.path == "/docs" and request.method.upper() == "GET") or
                (request.url.path == "/openapi.json" and request.method.upper() == "GET")
            ):
                return await call_next(request)
            elif request.url.path == "/users/sessions" and request.method.upper() == "POST":
                response = await call_next(request)
                if response.status_code == 200:
                    user_info = await self.userFromResponseBody(response)
                    await sessionDelete(user_info=user_info)
                    session_id = await sessionCreate(user_info)
                    self.setSessionCookie(response, session_id)
                return response
            elif request.url.path == "/users" and request.method.upper() == "POST":
                response = await call_next(request)
                if response.status_code == 200:
                    user_info = await self.userFromResponseBody(response)
                    session_id = await sessionCreate(user_info)
                    self.setSessionCookie(response, session_id)
                return response
            else:
                user_info = await sessionValidate(request)
                logging_conf.USER_NAME.set(f"{user_info.name}:{user_info.id}")
                request.state.user_info = user_info
                return await call_next(request)
        except AuthenticationError as ex:
            LOGGER.exception(ex)
            return JSONResponse({"message": str(ex)}, status_code=401)

    async def userFromResponseBody(self, response: Response) -> User:
        response_body = [chunk async for chunk in response.body_iterator]
        response.body_iterator = iterate_in_threadpool(iter(response_body))
        user_info = json.loads(b''.join(response_body))
        user_info["role"] = AppRoles[user_info["role"]]
        return User.model_validate(user_info)

    def setSessionCookie(self, response: Response, session_id: str):
        global SESSION_COOKIE_NAME
        response.set_cookie(SESSION_COOKIE_NAME, session_id, secure=True, httponly=True, samesite="strict")

async def sessionCreate(user_info: User) -> str:
    global SESSION_CLIENT
    global SESSION_PREFIX
    session_id = str(uuid.uuid4())
    session_user_key = f"{SESSION_PREFIX}:{session_id}"
    user_session_key = f"{SESSION_PREFIX}:{user_info.id}"
    # TODO: transactions
    await SESSION_CLIENT.set(session_user_key, user_info.model_dump_json())
    await SESSION_CLIENT.expire(session_user_key, SESSION_TTL)
    await SESSION_CLIENT.set(user_session_key, session_id)
    await SESSION_CLIENT.expire(user_session_key, SESSION_TTL)
    return session_id

async def sessionDelete(user_info: User | None=None, session_id: str | None=None) -> None:
    global SESSION_CLIENT
    global SESSION_PREFIX
    user_info, session_id = await sessionGet(user_info, session_id)
    session_user_key = f"{SESSION_PREFIX}:{session_id}"
    user_session_key = f"{SESSION_PREFIX}:{user_info.id}"
    # TODO: transactions
    await SESSION_CLIENT.delete(session_user_key)
    await SESSION_CLIENT.delete(user_session_key)

async def sessionGet(user_info: User | None=None, session_id: str | None=None) -> tuple[User, str]:
    global SESSION_CLIENT
    global SESSION_PREFIX
    if not user_info and not session_id:
        raise ValueError("I need user_info or session_id!")
    elif not user_info:
        user_info = await SESSION_CLIENT.get(f"{SESSION_PREFIX}:{session_id}")
        if user_info:
            user_info = User.model_validate_json(user_info)
        return user_info, session_id
    elif not session_id:
        session_id = await SESSION_CLIENT.get(f"{SESSION_PREFIX}:{user_info.id}")
        return user_info, session_id
    else:
        return user_info, session_id

async def sessionValidate(request: Request) -> User:
    global SESSION_COOKIE_NAME
    session_id = request.headers.get("Authorization", None)
    if not session_id:
        session_id = request.cookies.get(SESSION_COOKIE_NAME, None)
    if not session_id:
        raise AuthenticationError("Session id not found in request!")

    user_info, session_id = await sessionGet(session_id=session_id)
    if not user_info:
        raise AuthenticationError("Invalid session id!")
    return user_info
