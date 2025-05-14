import logging
import redis

client: redis.Redis = None

LOGGER = logging.getLogger(f"__main__.{__name__}")

def init(host: str, port: int) -> None:
    # TODO: should use TLS if going over network.
    global client
    if not client:
        LOGGER.info("Starting redis client...")
        client = redis.Redis(
            host=host,
            port=port,
            decode_responses=True
        )
        LOGGER.info("Done!")

def shutdown() -> None:
    global client
    if client:
        LOGGER.info("Killing redis cliend...")
        client.close()
        LOGGER.info("Dead!")
