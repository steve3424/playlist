"""
Websocket server.
"""
import logging
import logging.config
from logging_conf import LOGGING_CONFIG
logging.config.dictConfig(LOGGING_CONFIG)
import fastapi
import uvicorn
from routers import gig

app = fastapi.FastAPI()
app.include_router(gig.router)

@app.get("/health")
def health() -> dict:
    return {"detail": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
