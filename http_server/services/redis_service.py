import logging
import redis.asyncio as redis

client: redis.Redis = None

LOGGER = logging.getLogger(f"playlist.{__name__}")

class RedisError(Exception):
    pass

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

async def addKey(key: str, val: str, ttl: int):
    try:
        global client
        await client.set(key, val)
        await client.expire(key, ttl)
    except Exception as ex:
        raise RedisError(ex) from ex
