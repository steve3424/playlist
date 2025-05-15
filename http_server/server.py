"""
Websocket server.
"""
import logging
import logging.config
from .logging_conf import LOGGING_CONFIG
logging.config.dictConfig(LOGGING_CONFIG)
import argparse
import fastapi
import uvicorn
from contextlib import asynccontextmanager
from .routers import gig
from .services import redis_service

LOGGER = logging.getLogger("playlist")

@asynccontextmanager
async def appLife(app: fastapi.FastAPI, *args, **kwargs):
    LOGGER.info("Starting server...")
    redis_service.init(kwargs["redis_host"], kwargs["redis_port"])
    yield
    LOGGER.info("Shutting down server...")
    await redis_service.shutdown()

def health() -> dict:
    return {"detail": "healthy"}
    
if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--host", type=str, default="0.0.0.0")
    arg_parser.add_argument("--port", type=int, default=80)
    arg_parser.add_argument("--redis-host", type=str, default="localhost")
    arg_parser.add_argument("--redis-port", type=int, default=6379)
    args = arg_parser.parse_args()

    app = fastapi.FastAPI(
        lifespan=lambda app: appLife(
            app,
            redis_host=args.redis_host,
            redis_port=args.redis_port,
        )
    )
    app.include_router(gig.router)
    app.add_api_route("/health", health)

    uvicorn.run(app, host=args.host, port=args.port)
