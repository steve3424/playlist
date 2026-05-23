"""
HTTP server.
"""
import logging
import logging.config
from .configs.logging_conf import LOGGING_CONFIG
logging.config.dictConfig(LOGGING_CONFIG)
import argparse
import fastapi
import uvicorn
import os
from fastapi.responses import PlainTextResponse
from pathlib import Path
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from common import tickets
from .middlewares import authentication
from .routers import bands, users, sessions
from .data import db, files

LOGGER = logging.getLogger("playlist")

class StartupException(Exception):
    pass

@asynccontextmanager
async def appLife(app: fastapi.FastAPI, *args, **kwargs):
    LOGGER.info("Starting server...")

    env_file_name = f"{kwargs["environment"]}.env"
    env_file_path = Path(os.path.dirname(__file__), os.pardir, "common", env_file_name)
    LOGGER.info(f"Loading configs from '{env_file_path}'...")
    env_loaded = load_dotenv(dotenv_path=env_file_path)
    if not env_loaded:
        LOGGER.warning("Failed to load environment file!")
    await tickets.init(kwargs["redis_host"], kwargs["redis_port"])
    db_init = await db.init()
    if not db_init:
        raise StartupException("DB failed to initialize!")
    auth_init = await authentication.init(kwargs["redis_host"], kwargs["redis_port"])
    if not auth_init:
        raise StartupException("Auth failed to initialize!")
    await files.init()

    yield

    LOGGER.info("Shutting down server...")
    await tickets.shutdown()
    await authentication.shutdown()

def health() -> PlainTextResponse:
    # TODO: real health check
    return PlainTextResponse("healthy")

def createApp(redis_host: str, redis_port: int, environment: str) -> fastapi.FastAPI:
    app = fastapi.FastAPI(
        lifespan=lambda app: appLife(
            app,
            redis_host=redis_host,
            redis_port=redis_port,
            environment=environment
        )
    )

    # NOTE: Middlewares are run in reverse order of how they are added.
    app.add_middleware(authentication.Authenticate)

    app.add_api_route("/health", health)
    app.include_router(users.router)
    app.include_router(sessions.router)
    app.include_router(bands.router)
    return app

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--host",        type=str, default="0.0.0.0")
    arg_parser.add_argument("--port",        type=int, default=80)
    arg_parser.add_argument("--redis-host",  type=str, default="localhost")
    arg_parser.add_argument("--redis-port",  type=int, default=6379)
    arg_parser.add_argument("--environment", type=str, default="dev", choices=["dev", "prod"])
    args = arg_parser.parse_args()

    app = createApp(args.redis_host, args.redis_port, args.environment)

    uvicorn.run(app, host=args.host, port=args.port, log_config=LOGGING_CONFIG)
