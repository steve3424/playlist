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
from .routers import gig

app = fastapi.FastAPI()
app.include_router(gig.router)

@app.get("/health")
def health() -> dict:
    return {"detail": "healthy"}

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--host", type=str, default="0.0.0.0")
    arg_parser.add_argument("--port", type=int, default=80)
    args = arg_parser.parse_args()

    uvicorn.run(app, host=args.host, port=args.port)
