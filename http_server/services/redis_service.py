import logging
import redis.asyncio as redis

client: redis.Redis = None

LOGGER = logging.getLogger(f"playlist.{__name__}")

def init(host: str, port: int) -> None:
    # TODO: should use TLS if going over network.
    global client
    if not client:
        LOGGER.info(f"Starting redis client on '{host}:{port}'...")
        client = redis.Redis(
            host=host,
            port=port,
            decode_responses=True,
        )

async def shutdown() -> None:
    global client
    if client:
        LOGGER.info("Killing redis client...")
        await client.close()
