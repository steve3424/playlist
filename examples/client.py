"""
Sample client for connecting to local websocket host
and sending messages from console.
"""
import logging
import logging.config
from logging_conf import LOGGING_CONFIG
logging.config.dictConfig(LOGGING_CONFIG)
import requests
import asyncio
import aioconsole
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError, ConnectionClosed
from websockets.asyncio.client import connect, ClientConnection

LOGGER = logging.getLogger(__name__)

async def wsListener(websocket: ClientConnection):
    LOGGER.info(f"Listening to {websocket.remote_address} for messages...")
    try:
        while True:
            incoming_msg = await websocket.recv()
            LOGGER.info(f"Received message '{incoming_msg}' from {websocket.remote_address}!")
    except ConnectionClosedOK as ex:
        LOGGER.info(f"ConnectionClosedOk from server: {ex}")
    except ConnectionClosedError as ex:
        LOGGER.error(f"ConnectionClosedError from server: {ex}")
    except ConnectionClosed as ex:
        LOGGER.error(f"ConnectionClosed from server: {ex}")

async def inputListener(websocket: ClientConnection):
    LOGGER.info("Listening to console for messages...")
    try:
        while True:
            msg_to_send = await aioconsole.ainput()
            LOGGER.info(f"Sending '{msg_to_send}' to {websocket.remote_address}...")
            await websocket.send(msg_to_send)
            LOGGER.info("Message sent!")
    except EOFError as ex:
        LOGGER.info("EOFError stopping input listener...")

async def startClient(host: str, port: int, ticket: str):
    async with connect(f"ws://{host}:{port}", additional_headers={"sec-websocket-protocol": ticket}) as websocket:
        LOGGER.info(f"Connected to {host}:{port} on local port {websocket.local_address[1]}!")
        in_task = asyncio.create_task(inputListener(websocket))
        rec_task = asyncio.create_task(wsListener(websocket))
        _, pending = await asyncio.wait(
            [
                in_task,
                rec_task,
            ],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()

def getTicket(host: str, port: int, band: str) -> str:
    response = requests.get(f"http://{host}:{port}/gig/ticket?band={band}")
    if response.status_code != 200:
        raise Exception(response.json())
    return response.json()

def main(ws_host: str, ws_port: int, ticket_host: str, ticket_port: int, band: str):
    try:
        asyncio.run(startClient(ws_host, ws_port, getTicket(ticket_host, ticket_port, band)))
    except KeyboardInterrupt:
        LOGGER.info("ctrl+c stopped client!")
    except ConnectionRefusedError as ex:
        LOGGER.error(f"Unable to connect: {ex}")

if __name__ == "__main__":
    ws_host = "localhost"
    ws_port = 8080
    ticket_host = "localhost"
    ticket_port = 80
    band = "The Beatles"
    main(ws_host, ws_port, ticket_host, ticket_port, band)
