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
from pathlib import Path
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from .middlewares import exception, authentication
from .routers import bands, users
from .services import db
from common import tickets

LOGGER = logging.getLogger("playlist")

@asynccontextmanager
async def appLife(app: fastapi.FastAPI, *args, **kwargs):
    LOGGER.info("Starting server...")

    env_file_name = f"{kwargs["environment"]}.env"
    env_file_path = Path(os.path.dirname(__file__), "configs", env_file_name)
    LOGGER.info(f"Loading configs from '{env_file_name}'...")
    env_loaded = load_dotenv(dotenv_path=env_file_path)
    if not env_loaded:
        LOGGER.warning("Failed to load environment file!")
    current_env = os.environ.get("ENV", "NONE")
    if current_env in authentication.OPEN_ENVS:
        LOGGER.warning("API authentication turned off!")
    else:
        LOGGER.info("API authentication turned on!")
    await tickets.init(kwargs["redis_host"], kwargs["redis_port"])
    db.init()

    yield

    LOGGER.info("Shutting down server...")
    await tickets.shutdown()

def health() -> dict:
    return {"detail": "healthy"}
    
if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--host",        type=str, default="0.0.0.0")
    arg_parser.add_argument("--port",        type=int, default=80)
    arg_parser.add_argument("--redis-host",  type=str, default="localhost")
    arg_parser.add_argument("--redis-port",  type=int, default=6379)
    arg_parser.add_argument("--environment", type=str, default="dev", choices=["dev", "prod"])
    args = arg_parser.parse_args()

    app = fastapi.FastAPI(
        lifespan=lambda app: appLife(
            app,
            redis_host=args.redis_host,
            redis_port=args.redis_port,
            environment=args.environment
        )
    )
    app.add_middleware(exception.ExceptionHandlerGeneral)
    app.add_middleware(authentication.Authenticate)
    app.add_api_route("/health", health)
    app.include_router(bands.router)
    app.include_router(users.router)

    uvicorn.run(app, host=args.host, port=args.port, log_config=LOGGING_CONFIG)
