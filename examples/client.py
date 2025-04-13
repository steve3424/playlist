"""
Sample client for connecting to local websocket host
and sending messages from console.
"""
import logging
import logging.config
from logging_conf import LOGGING_CONFIG
logging.config.dictConfig(LOGGING_CONFIG)
import asyncio
import aioconsole
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError, ConnectionClosed
from websockets.asyncio.client import connect, ClientConnection

LOGGER = logging.getLogger(f"__main__.{__name__}")

async def process_message_from_server(msg: str):
    pass

async def ws_listener(websocket: ClientConnection):
    LOGGER.info(f"Listening to {websocket.remote_address} for messages...")
    try:
        while True:
            incoming_msg = await websocket.recv()
            LOGGER.info(f"Received message '{incoming_msg}' from {websocket.remote_address}!")
    except ConnectionClosedOK as ex:
        LOGGER.info(f"ConnectionClosedOk from server: {ex}")
    except ConnectionClosedError as ex:
        LOGGER.info(f"ConnectionClosedError from server: {ex}")
    except ConnectionClosed as ex:
        LOGGER.info(f"ConnectionClosed from server: {ex}")

async def input_listener(websocket: ClientConnection):
    LOGGER.info("Listening to console for messages...")
    try:
        while True:
            msg_to_send = await aioconsole.ainput()
            LOGGER.info(f"Sending '{msg_to_send}' to {websocket.remote_address}...")
            await websocket.send(msg_to_send)
            LOGGER.info("Message sent!")
    except EOFError as ex:
        LOGGER.info("EOFError stopping input listener...")

async def start_client(host: str, port: int):
    async with connect(f"ws://{host}:{port}") as websocket:
        LOGGER.info(f"Connected to {host}:{port} on local port {websocket.local_address[1]}!")
        in_task = asyncio.create_task(input_listener(websocket))
        rec_task = asyncio.create_task(ws_listener(websocket))
        _, pending = await asyncio.wait(
            [
                in_task,
                rec_task,
            ],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()

def main(host: str, port: int):
    try:
        asyncio.run(start_client(host, port))
    except KeyboardInterrupt:
        LOGGER.info("ctrl+c stopped client!")

if __name__ == "__main__":
    host = "localhost"
    port = 8080
    main(host, port)
