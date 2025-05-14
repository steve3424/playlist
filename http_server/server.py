"""
Websocket server.
"""
import logging
import logging.config
from .logging_conf import LOGGING_CONFIG
logging.config.dictConfig(LOGGING_CONFIG)
import argparse
import asyncio
import fastapi
import uvicorn
from .routers import gig
from .services import redis_service

app = fastapi.FastAPI()
app.include_router(gig.router)

@app.get("/health")
def health() -> dict:
    return {"detail": "healthy"}

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--host", type=str, default="0.0.0.0")
    arg_parser.add_argument("--port", type=int, default=80)
    arg_parser.add_argument("--redis-host", type=str, default="localhost")
    arg_parser.add_argument("--redis-port", type=int, default=6379)
    args = arg_parser.parse_args()

    # Startup code
    redis_service.init(args.redis_host, args.redis_port)

    uvicorn.run(app, host=args.host, port=args.port)

    # Shutdown code
    asyncio.run(redis_service.shutdown())
