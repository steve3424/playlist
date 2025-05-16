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
import os
from pathlib import Path
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from .routers import band
from .services import redis_service

LOGGER = logging.getLogger("playlist")

@asynccontextmanager
async def appLife(app: fastapi.FastAPI, *args, **kwargs):
    LOGGER.info("Starting server...")

    env_file_name = f"{kwargs["environment"]}.env"
    env_file_path = Path(os.path.dirname(__file__), "configs", env_file_name)
    LOGGER.info(f"Loading configs from '{env_file_name}'...")
    env_loaded = load_dotenv(dotenv_path=env_file_path)
    if not env_loaded:
        LOGGER.error(f"Failed to load environment!")

    redis_service.init(kwargs["redis_host"], kwargs["redis_port"])
    yield
    LOGGER.info("Shutting down server...")
    await redis_service.shutdown()

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
    app.include_router(band.router)
    app.add_api_route("/health", health)

    uvicorn.run(app, host=args.host, port=args.port)
