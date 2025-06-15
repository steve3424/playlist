"""
Entry point for every request. Handles general exceptions, logs api timings, sets up request logging.
"""
import logging
import time
from uuid import uuid4
from typing import Callable, Awaitable
from fastapi import Request, HTTPException
from fastapi.responses import Response, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from ..configs import logging_conf

LOGGER = logging.getLogger(f"playlist.{__name__}")

class InitMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        try:
            time_start_request = time.perf_counter()
            logging_conf.IP_ADDRESS.set(request.client.host)
            logging_conf.ENDPOINT.set(request.url.path)
            logging_conf.REQUEST_ID.set(uuid4().hex)
            LOGGER.info("Requesting...")
            result = await call_next(request)
            LOGGER.info(f"[{result.status_code}] {(time.perf_counter() - time_start_request):.6f}s")
            return result
        except HTTPException as ex:
            # NOTE: we may want to raise this from our application code.
            #       we don't want to wrap this in 500 error as we do with
            #       other unhandled exceptions.
            LOGGER.exception(ex)
            return JSONResponse(ex.detail, ex.status_code) 
        except Exception as ex:
            LOGGER.exception(ex)
            return JSONResponse({"message": "Something went wrong"}, status_code=500)