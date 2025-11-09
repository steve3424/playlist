"""
This middleware does it all! Authentication, trace logging, api timing, security headers, exception handling!
"""
import logging
import redis.asyncio as redis
import uuid
import time
from typing import Callable, Awaitable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.concurrency import iterate_in_threadpool
from .authorization.models import User
from .authorization.main import AuthorizationError
from ..configs import logging_conf

LOGGER = logging.getLogger(f"playlist.{__name__}")
SESSION_COOKIE_NAME = "SESSION"
SESSION_TTL = 60 * 60 * 24 * 7 # seconds per week
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
            time_start_request = time.perf_counter()
            logging_conf.IP_ADDRESS.set(request.client.host)
            logging_conf.ENDPOINT.set(f"{request.method}:{request.url.path}")
            logging_conf.REQUEST_ID.set(uuid.uuid4().hex)
            LOGGER.info("Request...")

            open_endpoints = {
                "GET:/docs",
                "GET:/openapi.json",
                "GET:/health",
            }
            login_endpoint = "POST:/sessions"
            register_endpoint = "POST:/users"

            requested_endpoint = f"{request.method}:{request.url.path}"
            if requested_endpoint in open_endpoints:
                response = await call_next(request)
            elif requested_endpoint == login_endpoint:
                response = await call_next(request)
                if response.status_code == 200:
                    user_info = await self.userFromResponseBody(response)
                    logging_conf.USER_NAME.set(user_info.name)
                    await sessionDelete(user_info.name)
                    await sessionCreate(user_info, response)
            elif requested_endpoint == register_endpoint:
                response = await call_next(request)
                if response.status_code == 200:
                    user_info = await self.userFromResponseBody(response)
                    logging_conf.USER_NAME.set(user_info.name)
                    await sessionDelete(user_info.name)
                    await sessionCreate(user_info, response)
            else:
                user_info = await sessionValidate(request)
                logging_conf.USER_NAME.set(user_info.name)
                request.state.user_info = user_info
                response = await call_next(request)
        except AuthenticationError as ex:
            response = JSONResponse({"message": str(ex)}, status_code=401)
            logging_conf.STATUS_CODE.set(response.status_code)
            LOGGER.info(ex)
        except AuthorizationError as ex:
            response = JSONResponse({"message": str(ex)}, status_code=403)
            logging_conf.STATUS_CODE.set(response.status_code)
            LOGGER.info(ex)
        except Exception as ex:
            # Unhandled exceptions
            response = JSONResponse({"message": "Something went wrong"}, status_code=500)
            logging_conf.STATUS_CODE.set(response.status_code)
            LOGGER.exception(ex)
        finally:
            logging_conf.STATUS_CODE.set(response.status_code)
            self.addSecurityHeaders(response)
            LOGGER.info(f"{(time.perf_counter() - time_start_request):.6f}s")
            return response
    
    def addSecurityHeaders(self, response: Response):
        # csp
        response.headers.append(
            "content-security-policy",
            "object-src 'none';"
        )

    async def userFromResponseBody(self, response: Response) -> User:
        response_body = [chunk async for chunk in response.body_iterator]
        response.body_iterator = iterate_in_threadpool(iter(response_body))
        return User.model_validate_json(b''.join(response_body))

async def sessionCreate(user_info: User, response: Response) -> None:
    global SESSION_CLIENT
    global SESSION_COOKIE_NAME

    session_id = str(uuid.uuid4())
    user_info.session_id = session_id
    session_user_key = f"{SESSION_COOKIE_NAME}:{session_id}"
    user_session_key = f"{SESSION_COOKIE_NAME}:{user_info.name}"

    transaction = SESSION_CLIENT.pipeline(transaction=True)
    await transaction.set(session_user_key, user_info.model_dump_json())
    await transaction.expire(session_user_key, SESSION_TTL)
    await transaction.set(user_session_key, user_info.model_dump_json())
    await transaction.expire(user_session_key, SESSION_TTL)
    await transaction.execute()

    response.set_cookie(SESSION_COOKIE_NAME, session_id, secure=True, httponly=True, samesite="strict", max_age=SESSION_TTL)

async def sessionGet(session_id_or_name: str) -> User | None:
    global SESSION_CLIENT
    global SESSION_COOKIE_NAME

    user_info = await SESSION_CLIENT.get(f"{SESSION_COOKIE_NAME}:{session_id_or_name}")
    if user_info:
        user_info = User.model_validate_json(user_info)
    return user_info

async def sessionDelete(session_id_or_name: str) -> None:
    global SESSION_CLIENT
    global SESSION_COOKIE_NAME

    user_info = await sessionGet(session_id_or_name)
    if user_info:
        transaction = SESSION_CLIENT.pipeline(transaction=True)
        await transaction.delete(f"{SESSION_COOKIE_NAME}:{user_info.session_id}")
        await transaction.delete(f"{SESSION_COOKIE_NAME}:{user_info.name}")
        await transaction.execute()

async def sessionAll() -> list[User]:
    global SESSION_CLIENT

    all_sessions = set()
    cursor = '0'
    while cursor != 0:
        cursor, keys = await SESSION_CLIENT.scan(cursor=cursor, count=10000)
        values = await SESSION_CLIENT.mget(*keys)
        for i,val in enumerate(values):
            all_sessions.add(User.model_validate_json(val))
    return list(all_sessions)

async def sessionValidate(request: Request) -> User:
    global SESSION_COOKIE_NAME

    session_id = request.headers.get("Authorization", None)
    if not session_id:
        session_id = request.cookies.get(SESSION_COOKIE_NAME, None)
    if not session_id:
        raise AuthenticationError("Session id not found in request!")

    user_info = await sessionGet(session_id)
    if not user_info:
        raise AuthenticationError("Invalid session id!")
    return user_info
